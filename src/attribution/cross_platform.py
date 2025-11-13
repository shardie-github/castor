"""
Cross-Platform Attribution

Tracks conversions across web, mobile, and offline channels.
"""

import logging
import hashlib
from datetime import datetime, timezone, date, time
from typing import Dict, List, Optional, Any
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Conversion platforms"""
    WEB = "web"
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"
    OFFLINE = "offline"
    IN_STORE = "in_store"
    PHONE = "phone"
    EMAIL = "email"


@dataclass
class ConversionEvent:
    """Conversion event data structure"""
    conversion_id: str
    tenant_id: str
    campaign_id: str
    timestamp: datetime
    platform: Platform
    conversion_type: str
    conversion_value: Optional[float]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    metadata: Dict[str, Any] = None


class CrossPlatformAttribution:
    """
    Cross-Platform Attribution
    
    Tracks and attributes conversions across:
    - Web (desktop, mobile web)
    - Mobile apps (iOS, Android)
    - Offline (in-store, phone, email)
    - Cross-device matching
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def track_conversion(
        self,
        tenant_id: str,
        campaign_id: str,
        platform: Platform,
        conversion_type: str,
        conversion_value: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer_url: Optional[str] = None,
        landing_page_url: Optional[str] = None,
        conversion_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a conversion event
        
        Returns:
            Conversion ID
        """
        conversion_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO conversion_events (
                conversion_id, tenant_id, campaign_id, timestamp, platform,
                conversion_type, conversion_value, user_id, session_id, device_id,
                ip_address, user_agent, referrer_url, landing_page_url,
                conversion_data, attribution_data, metadata
            )
            VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            conversion_id, tenant_id, campaign_id, platform.value, conversion_type,
            conversion_value, user_id, session_id, device_id, ip_address,
            user_agent, referrer_url, landing_page_url,
            conversion_data or {}, {}, metadata or {}
        )
        
        # Try to match to user journey
        if user_id or device_id or session_id:
            await self._update_user_journey(
                tenant_id, user_id, device_id, session_id, conversion_id
            )
        
        # Record telemetry
        self.metrics.increment_counter(
            "conversion_tracked",
            tags={
                "tenant_id": tenant_id,
                "campaign_id": campaign_id,
                "platform": platform.value,
                "conversion_type": conversion_type
            }
        )
        
        return conversion_id
    
    async def import_offline_conversion(
        self,
        tenant_id: str,
        campaign_id: str,
        conversion_date: date,
        conversion_type: str,
        conversion_value: Optional[float] = None,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        store_location: Optional[str] = None,
        import_source: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Import offline conversion (e.g., in-store purchase)
        
        Returns:
            Offline conversion ID
        """
        offline_conversion_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO offline_conversions (
                offline_conversion_id, tenant_id, campaign_id, conversion_date,
                conversion_time, conversion_type, conversion_value, customer_id,
                order_id, store_location, import_source, import_batch_id, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            offline_conversion_id, tenant_id, campaign_id, conversion_date,
            datetime.now(timezone.utc).time(), conversion_type, conversion_value,
            customer_id, order_id, store_location, import_source, import_batch_id,
            metadata or {}
        )
        
        # Try to match to attribution events
        if customer_id:
            await self._match_offline_to_attribution(
                tenant_id, campaign_id, customer_id, offline_conversion_id
            )
        
        return offline_conversion_id
    
    async def create_device_fingerprint(
        self,
        tenant_id: str,
        device_id: str,
        device_type: Optional[str] = None,
        device_os: Optional[str] = None,
        browser: Optional[str] = None,
        screen_resolution: Optional[str] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create device fingerprint for cross-device matching
        
        Returns:
            Fingerprint ID
        """
        # Generate fingerprint hash
        fingerprint_data = f"{device_type}:{device_os}:{browser}:{screen_resolution}:{timezone}:{language}"
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        # Check if fingerprint exists
        existing = await self.postgres.fetchrow(
            """
            SELECT fingerprint_id, unified_user_id
            FROM device_fingerprints
            WHERE tenant_id = $1 AND fingerprint_hash = $2
            """,
            tenant_id, fingerprint_hash
        )
        
        if existing:
            # Update last seen
            await self.postgres.execute(
                """
                UPDATE device_fingerprints
                SET last_seen_at = NOW()
                WHERE fingerprint_id = $1
                """,
                existing["fingerprint_id"]
            )
            return str(existing["fingerprint_id"])
        
        # Create new fingerprint
        fingerprint_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO device_fingerprints (
                fingerprint_id, tenant_id, device_id, fingerprint_hash,
                device_type, device_os, browser, screen_resolution, timezone,
                language, ip_address, user_agent
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            fingerprint_id, tenant_id, device_id, fingerprint_hash,
            device_type, device_os, browser, screen_resolution, timezone,
            language, ip_address, user_agent
        )
        
        return fingerprint_id
    
    async def match_cross_device(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        device_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Match devices/users to create unified user ID
        
        Returns:
            Unified user ID
        """
        # Check if unified user already exists
        if user_id:
            journey = await self.postgres.fetchrow(
                """
                SELECT unified_user_id
                FROM user_journeys
                WHERE tenant_id = $1 AND user_id = $2
                """,
                tenant_id, user_id
            )
            
            if journey and journey["unified_user_id"]:
                return str(journey["unified_user_id"])
        
        # Check device fingerprints
        if device_ids:
            for device_id in device_ids:
                fingerprint = await self.postgres.fetchrow(
                    """
                    SELECT unified_user_id
                    FROM device_fingerprints
                    WHERE tenant_id = $1 AND device_id = $2 AND unified_user_id IS NOT NULL
                    """,
                    tenant_id, device_id
                )
                
                if fingerprint and fingerprint["unified_user_id"]:
                    return str(fingerprint["unified_user_id"])
        
        # Create new unified user ID
        unified_user_id = uuid4()
        
        # Create user journey
        await self.postgres.execute(
            """
            INSERT INTO user_journeys (
                journey_id, tenant_id, user_id, unified_user_id,
                first_seen_at, last_seen_at, devices, sessions
            )
            VALUES (gen_random_uuid(), $1, $2, $3, NOW(), NOW(), $4, $5)
            """,
            tenant_id, user_id, unified_user_id, device_ids or [], []
        )
        
        # Update device fingerprints
        if device_ids:
            for device_id in device_ids:
                await self.postgres.execute(
                    """
                    UPDATE device_fingerprints
                    SET unified_user_id = $1
                    WHERE tenant_id = $2 AND device_id = $3
                    """,
                    unified_user_id, tenant_id, device_id
                )
        
        return str(unified_user_id)
    
    async def get_unified_journey(
        self,
        tenant_id: str,
        unified_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get unified user journey across all devices"""
        row = await self.postgres.fetchrow(
            """
            SELECT journey_id, user_id, unified_user_id, first_seen_at, last_seen_at,
                   devices, sessions, touchpoints, conversions
            FROM user_journeys
            WHERE tenant_id = $1 AND unified_user_id = $2
            """,
            tenant_id, unified_user_id
        )
        
        if not row:
            return None
        
        return {
            "journey_id": str(row["journey_id"]),
            "user_id": row["user_id"],
            "unified_user_id": str(row["unified_user_id"]),
            "first_seen_at": row["first_seen_at"].isoformat(),
            "last_seen_at": row["last_seen_at"].isoformat(),
            "devices": row["devices"] or [],
            "sessions": row["sessions"] or [],
            "touchpoints": row["touchpoints"] or [],
            "conversions": row["conversions"] or []
        }
    
    async def _update_user_journey(
        self,
        tenant_id: str,
        user_id: Optional[str],
        device_id: Optional[str],
        session_id: Optional[str],
        conversion_id: str
    ):
        """Update user journey with conversion"""
        # Get or create unified user ID
        unified_user_id = await self.match_cross_device(
            tenant_id, user_id, [device_id] if device_id else None
        )
        
        if unified_user_id:
            # Update journey with conversion
            await self.postgres.execute(
                """
                UPDATE user_journeys
                SET conversions = array_append(conversions, $1::text),
                    last_seen_at = NOW(), updated_at = NOW()
                WHERE tenant_id = $2 AND unified_user_id = $3
                """,
                conversion_id, tenant_id, unified_user_id
            )
    
    async def _match_offline_to_attribution(
        self,
        tenant_id: str,
        campaign_id: str,
        customer_id: str,
        offline_conversion_id: str
    ):
        """Match offline conversion to attribution events"""
        # Look for attribution events with matching customer ID
        attribution_events = await self.postgres.fetch(
            """
            SELECT event_id, timestamp
            FROM attribution_events
            WHERE tenant_id = $1 AND campaign_id = $2
            AND attribution_data->>'customer_id' = $3
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            tenant_id, campaign_id, customer_id
        )
        
        if attribution_events:
            # Mark as matched
            await self.postgres.execute(
                """
                UPDATE offline_conversions
                SET matched_to_attribution = TRUE, matched_at = NOW()
                WHERE offline_conversion_id = $1
                """,
                offline_conversion_id
            )

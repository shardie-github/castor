"""
Advanced Attribution Engine

Provides multiple attribution models and attribution calculation.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection
from src.attribution.models import (
    FirstTouchModel,
    LastTouchModel,
    LinearModel,
    TimeDecayModel,
    PositionBasedModel
)

logger = logging.getLogger(__name__)


class AttributionModelType(Enum):
    """Attribution model types"""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"


@dataclass
class Touchpoint:
    """Attribution touchpoint"""
    touchpoint_id: str
    timestamp: datetime
    channel: str
    campaign_id: str
    episode_id: Optional[str] = None
    attribution_method: str = "promo_code"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttributionPath:
    """User attribution path"""
    path_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    device_id: Optional[str]
    touchpoints: List[Touchpoint]
    conversion_value: Optional[float] = None
    conversion_type: Optional[str] = None
    conversion_at: Optional[datetime] = None


@dataclass
class AttributionResult:
    """Attribution calculation result"""
    campaign_id: str
    model_type: AttributionModelType
    total_conversions: int
    total_conversion_value: float
    attributed_conversions: int
    attributed_conversion_value: float
    touchpoint_credits: Dict[str, float]  # touchpoint_id -> credit
    confidence_score: float
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class AttributionEngine:
    """
    Advanced Attribution Engine
    
    Calculates attribution using multiple models:
    - First-touch: 100% credit to first touchpoint
    - Last-touch: 100% credit to last touchpoint
    - Linear: Equal credit to all touchpoints
    - Time-decay: More credit to recent touchpoints
    - Position-based: U-shaped model (more credit to first and last)
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
        
        # Initialize model instances
        self.models = {
            AttributionModelType.FIRST_TOUCH: FirstTouchModel(),
            AttributionModelType.LAST_TOUCH: LastTouchModel(),
            AttributionModelType.LINEAR: LinearModel(),
            AttributionModelType.TIME_DECAY: TimeDecayModel(),
            AttributionModelType.POSITION_BASED: PositionBasedModel()
        }
    
    async def calculate_attribution(
        self,
        campaign_id: str,
        tenant_id: str,
        model_type: AttributionModelType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AttributionResult:
        """
        Calculate attribution for a campaign using specified model
        
        Args:
            campaign_id: Campaign ID
            tenant_id: Tenant ID
            model_type: Attribution model to use
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            AttributionResult with calculated attribution
        """
        # Get attribution paths for campaign
        paths = await self._get_attribution_paths(
            campaign_id, tenant_id, start_date, end_date
        )
        
        if not paths:
            return AttributionResult(
                campaign_id=campaign_id,
                model_type=model_type,
                total_conversions=0,
                total_conversion_value=0.0,
                attributed_conversions=0,
                attributed_conversion_value=0.0,
                touchpoint_credits={},
                confidence_score=0.0
            )
        
        # Get model
        model = self.models.get(model_type)
        if not model:
            raise ValueError(f"Unknown attribution model: {model_type}")
        
        # Calculate attribution
        result = model.calculate(paths)
        
        # Store attribution paths if not already stored
        await self._store_attribution_paths(tenant_id, campaign_id, paths)
        
        # Store attribution result
        await self._store_attribution_result(tenant_id, campaign_id, model_type, result)
        
        # Record telemetry
        self.metrics.increment_counter(
            "attribution_calculated",
            tags={
                "campaign_id": campaign_id,
                "model_type": model_type.value,
                "tenant_id": tenant_id
            }
        )
        
        return result
    
    async def compare_models(
        self,
        campaign_id: str,
        tenant_id: str,
        model_types: Optional[List[AttributionModelType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[AttributionModelType, AttributionResult]:
        """
        Compare multiple attribution models
        
        Returns:
            Dictionary mapping model type to attribution result
        """
        if model_types is None:
            model_types = list(AttributionModelType)
        
        results = {}
        for model_type in model_types:
            result = await self.calculate_attribution(
                campaign_id, tenant_id, model_type, start_date, end_date
            )
            results[model_type] = result
        
        return results
    
    async def _get_attribution_paths(
        self,
        campaign_id: str,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttributionPath]:
        """Get attribution paths from database"""
        # Query attribution events and build paths
        query = """
            SELECT 
                event_id, timestamp, campaign_id, episode_id, attribution_method,
                user_id, session_id, device_id, conversion_data, metadata
            FROM attribution_events
            WHERE campaign_id = $1 AND tenant_id = $2
        """
        
        params = [campaign_id, tenant_id]
        if start_date:
            query += " AND timestamp >= $" + str(len(params) + 1)
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= $" + str(len(params) + 1)
            params.append(end_date)
        
        query += " ORDER BY timestamp ASC"
        
        rows = await self.postgres.fetch(query, *params)
        
        # Group events by user/session/device to build paths
        paths_dict: Dict[str, AttributionPath] = {}
        
        for row in rows:
            # Create unique path identifier
            path_key = row["user_id"] or row["session_id"] or row["device_id"] or str(row["event_id"])
            
            if path_key not in paths_dict:
                paths_dict[path_key] = AttributionPath(
                    path_id=str(uuid4()),
                    user_id=row["user_id"],
                    session_id=row["session_id"],
                    device_id=row["device_id"],
                    touchpoints=[],
                    conversion_value=None,
                    conversion_type=None,
                    conversion_at=None
                )
            
            path = paths_dict[path_key]
            
            # Parse conversion data
            conversion_data = row["conversion_data"] or {}
            if conversion_data.get("conversion_type"):
                path.conversion_type = conversion_data["conversion_type"]
                path.conversion_value = conversion_data.get("conversion_value", 0.0)
                path.conversion_at = row["timestamp"]
            
            # Add touchpoint
            touchpoint = Touchpoint(
                touchpoint_id=str(row["event_id"]),
                timestamp=row["timestamp"],
                channel=row["attribution_method"],
                campaign_id=row["campaign_id"],
                episode_id=row["episode_id"],
                attribution_method=row["attribution_method"],
                metadata=row["metadata"] or {}
            )
            
            path.touchpoints.append(touchpoint)
        
        # Filter to only paths with conversions
        return [path for path in paths_dict.values() if path.conversion_at is not None]
    
    async def _store_attribution_paths(
        self,
        tenant_id: str,
        campaign_id: str,
        paths: List[AttributionPath]
    ):
        """Store attribution paths in database"""
        for path in paths:
            await self.postgres.execute(
                """
                INSERT INTO attribution_paths (
                    path_id, tenant_id, campaign_id, user_id, session_id, device_id,
                    conversion_id, touchpoints, conversion_value, conversion_type,
                    first_touch_at, last_touch_at, conversion_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (path_id) DO NOTHING
                """,
                path.path_id, tenant_id, campaign_id, path.user_id, path.session_id,
                path.device_id, None,  # conversion_id
                [{"touchpoint_id": tp.touchpoint_id, "timestamp": tp.timestamp.isoformat(),
                  "channel": tp.channel, "campaign_id": tp.campaign_id} for tp in path.touchpoints],
                path.conversion_value, path.conversion_type,
                path.touchpoints[0].timestamp if path.touchpoints else None,
                path.touchpoints[-1].timestamp if path.touchpoints else None,
                path.conversion_at, {}
            )
    
    async def _store_attribution_result(
        self,
        tenant_id: str,
        campaign_id: str,
        model_type: AttributionModelType,
        result: AttributionResult
    ):
        """Store attribution result"""
        # Store in attribution_analytics table
        await self.postgres.execute(
            """
            INSERT INTO attribution_analytics (
                analytics_id, tenant_id, campaign_id, model_id, date,
                metric_type, metric_value, breakdown
            )
            VALUES (gen_random_uuid(), $1, $2, NULL, $3, $4, $5, $6)
            """,
            tenant_id, campaign_id, datetime.now(timezone.utc).date(),
            "attributed_conversions", result.attributed_conversions,
            {"model_type": model_type.value, "touchpoint_credits": result.touchpoint_credits}
        )

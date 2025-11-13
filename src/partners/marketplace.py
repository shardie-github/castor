"""
Marketplace Manager

Manages marketplace integrations, listings, and revenue sharing.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import uuid

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class MarketplaceType(str, Enum):
    """Marketplace types"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    BIGCOMMERCE = "bigcommerce"
    SQUARESPACE = "squarespace"
    WIX = "wix"
    GOOGLE_WORKSPACE = "google_workspace"
    ZAPIER = "zapier"


class ListingStatus(str, Enum):
    """Listing status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    LIVE = "live"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


@dataclass
class MarketplaceListing:
    """Marketplace listing data model"""
    listing_id: str
    marketplace_type: MarketplaceType
    app_id: Optional[str]  # Marketplace app ID
    app_name: str
    app_description: str
    status: ListingStatus
    revenue_share_rate: float  # e.g., 0.20 for 20% to marketplace
    total_revenue: float
    total_installs: int
    created_at: datetime
    published_at: Optional[datetime]
    metadata: Dict


class MarketplaceManager:
    """Manages marketplace listings and integrations"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def create_listing(
        self,
        marketplace_type: MarketplaceType,
        app_name: str,
        app_description: str,
        revenue_share_rate: float = 0.20,
        metadata: Optional[Dict] = None
    ) -> MarketplaceListing:
        """Create a new marketplace listing"""
        listing_id = str(uuid.uuid4())
        
        listing = MarketplaceListing(
            listing_id=listing_id,
            marketplace_type=marketplace_type,
            app_id=None,
            app_name=app_name,
            app_description=app_description,
            status=ListingStatus.DRAFT,
            revenue_share_rate=revenue_share_rate,
            total_revenue=0.0,
            total_installs=0,
            created_at=datetime.utcnow(),
            published_at=None,
            metadata=metadata or {}
        )
        
        await self._save_listing(listing)
        
        self.metrics_collector.increment_counter("marketplace_listings_created_total", {
            "marketplace": marketplace_type.value
        })
        self.event_logger.log_event("marketplace_listing_created", {
            "listing_id": listing_id,
            "marketplace": marketplace_type.value
        })
        
        return listing
    
    async def update_listing_status(
        self,
        listing_id: str,
        status: ListingStatus,
        app_id: Optional[str] = None
    ) -> Optional[MarketplaceListing]:
        """Update listing status"""
        listing = await self.get_listing(listing_id)
        if not listing:
            return None
        
        listing.status = status
        if app_id:
            listing.app_id = app_id
        if status == ListingStatus.LIVE and not listing.published_at:
            listing.published_at = datetime.utcnow()
        
        await self._save_listing(listing)
        
        self.event_logger.log_event("marketplace_listing_status_updated", {
            "listing_id": listing_id,
            "status": status.value
        })
        
        return listing
    
    async def track_install(
        self,
        listing_id: str,
        customer_id: str,
        revenue: float
    ):
        """Track a marketplace install and revenue"""
        listing = await self.get_listing(listing_id)
        if not listing:
            logger.warning(f"Listing not found: {listing_id}")
            return
        
        listing.total_installs += 1
        listing.total_revenue += revenue
        
        await self._save_listing(listing)
        
        # Record revenue share
        revenue_share_id = str(uuid.uuid4())
        marketplace_share = revenue * listing.revenue_share_rate
        our_revenue = revenue - marketplace_share
        
        query = """
            INSERT INTO marketplace_revenue (
                revenue_id, listing_id, customer_id, total_revenue,
                marketplace_share, our_revenue, revenue_share_rate, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await self.postgres_conn.execute(
            query,
            revenue_share_id,
            listing_id,
            customer_id,
            revenue,
            marketplace_share,
            our_revenue,
            listing.revenue_share_rate,
            datetime.utcnow()
        )
        
        self.metrics_collector.increment_counter("marketplace_installs_total", {
            "marketplace": listing.marketplace_type.value
        })
        self.event_logger.log_event("marketplace_install_tracked", {
            "listing_id": listing_id,
            "customer_id": customer_id,
            "revenue": revenue
        })
    
    async def get_listing(self, listing_id: str) -> Optional[MarketplaceListing]:
        """Get a listing by ID"""
        query = "SELECT * FROM marketplace_listings WHERE listing_id = $1"
        row = await self.postgres_conn.fetch_one(query, listing_id)
        if not row:
            return None
        return self._row_to_listing(row)
    
    async def list_listings(
        self,
        marketplace_type: Optional[MarketplaceType] = None,
        status: Optional[ListingStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MarketplaceListing]:
        """List marketplace listings"""
        conditions = []
        params = []
        param_idx = 1
        
        if marketplace_type:
            conditions.append(f"marketplace_type = ${param_idx}")
            params.append(marketplace_type.value)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM marketplace_listings
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        params.extend([limit, offset])
        rows = await self.postgres_conn.fetch_all(query, *params)
        return [self._row_to_listing(row) for row in rows]
    
    async def get_marketplace_stats(self) -> Dict:
        """Get marketplace statistics"""
        query = """
            SELECT 
                COUNT(*) as total_listings,
                COUNT(*) FILTER (WHERE status = 'live') as live_listings,
                SUM(total_installs) as total_installs,
                SUM(total_revenue) as total_revenue
            FROM marketplace_listings
        """
        
        row = await self.postgres_conn.fetch_one(query)
        
        return {
            "total_listings": row["total_listings"] or 0,
            "live_listings": row["live_listings"] or 0,
            "total_installs": row["total_installs"] or 0,
            "total_revenue": float(row["total_revenue"] or 0)
        }
    
    async def _save_listing(self, listing: MarketplaceListing):
        """Save listing to database"""
        query = """
            INSERT INTO marketplace_listings (
                listing_id, marketplace_type, app_id, app_name,
                app_description, status, revenue_share_rate,
                total_revenue, total_installs, created_at,
                published_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            ON CONFLICT (listing_id) DO UPDATE SET
                app_id = EXCLUDED.app_id,
                app_name = EXCLUDED.app_name,
                app_description = EXCLUDED.app_description,
                status = EXCLUDED.status,
                revenue_share_rate = EXCLUDED.revenue_share_rate,
                total_revenue = EXCLUDED.total_revenue,
                total_installs = EXCLUDED.total_installs,
                published_at = EXCLUDED.published_at,
                metadata = EXCLUDED.metadata
        """
        
        await self.postgres_conn.execute(
            query,
            listing.listing_id,
            listing.marketplace_type.value,
            listing.app_id,
            listing.app_name,
            listing.app_description,
            listing.status.value,
            listing.revenue_share_rate,
            listing.total_revenue,
            listing.total_installs,
            listing.created_at,
            listing.published_at,
            listing.metadata
        )
    
    def _row_to_listing(self, row: Dict) -> MarketplaceListing:
        """Convert database row to MarketplaceListing object"""
        return MarketplaceListing(
            listing_id=row["listing_id"],
            marketplace_type=MarketplaceType(row["marketplace_type"]),
            app_id=row.get("app_id"),
            app_name=row["app_name"],
            app_description=row["app_description"],
            status=ListingStatus(row["status"]),
            revenue_share_rate=float(row["revenue_share_rate"]),
            total_revenue=float(row["total_revenue"] or 0),
            total_installs=row["total_installs"] or 0,
            created_at=row["created_at"],
            published_at=row.get("published_at"),
            metadata=row.get("metadata", {})
        )

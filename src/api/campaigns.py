"""
Campaign Management API Routes

Provides endpoints for campaign CRUD operations, campaign management, and campaign analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user
from src.campaigns.campaign_manager import CampaignManager, CampaignStatus, AttributionConfig, AttributionMethod
from src.services.campaign_service import CampaignService
from src.utils.error_responses import NotFoundError, ValidationError

router = APIRouter()


# Pydantic Models
class CampaignCreate(BaseModel):
    podcast_id: str
    sponsor_id: str
    name: str
    start_date: datetime
    end_date: datetime
    campaign_value: float
    attribution_method: str = "promo_code"
    promo_code: Optional[str] = None
    episode_ids: Optional[List[str]] = None
    notes: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    campaign_value: Optional[float] = None
    episode_ids: Optional[List[str]] = None
    notes: Optional[str] = None


class CampaignResponse(BaseModel):
    campaign_id: str
    podcast_id: str
    sponsor_id: str
    name: str
    status: str
    start_date: datetime
    end_date: datetime
    campaign_value: float
    created_at: datetime
    updated_at: datetime


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


def get_campaign_manager(
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
) -> CampaignManager:
    """Get campaign manager instance"""
    return CampaignManager(
        metrics_collector=metrics,
        event_logger=event_logger,
        postgres_conn=postgres_conn
    )


def get_campaign_service(
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
) -> CampaignService:
    """Get campaign service instance"""
    return CampaignService(
        postgres_conn=postgres_conn,
        metrics_collector=metrics,
        event_logger=event_logger
    )


# API Endpoints
@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    campaign_service: CampaignService = Depends(get_campaign_service),
    campaign_manager: CampaignManager = Depends(get_campaign_manager),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Create a new campaign"""
    # Get tenant_id from user or request state
    tenant_id = current_user.get('tenant_id') or getattr(request.state, 'tenant_id', None)
    user_id = current_user.get('user_id')
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID required"
        )
    
    # Use service layer
    try:
        campaign = await campaign_service.create_campaign(
            tenant_id=tenant_id,
            user_id=user_id,
            campaign_data=campaign_data.dict()
        )
        return CampaignResponse(**campaign)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Legacy code below (keeping for reference)
    # Verify podcast belongs to user
    podcast = await postgres_conn.fetchrow(
        "SELECT podcast_id FROM podcasts WHERE podcast_id = $1 AND user_id = $2",
        campaign_data.podcast_id,
        current_user['user_id']
    )
    
    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    # Create attribution config
    attribution_config = AttributionConfig(
        method=AttributionMethod(campaign_data.attribution_method),
        promo_code=campaign_data.promo_code
    )
    
    # Create campaign
    campaign = await campaign_manager.create_campaign(
        user_id=str(current_user['user_id']),
        podcast_id=campaign_data.podcast_id,
        sponsor_id=campaign_data.sponsor_id,
        name=campaign_data.name,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        campaign_value=campaign_data.campaign_value,
        attribution_config=attribution_config,
        episode_ids=campaign_data.episode_ids or [],
        notes=campaign_data.notes
    )
    
    # Log event
    await event_logger.log_event(
        event_type='campaign.created',
        user_id=str(current_user['user_id']),
        properties={
            'campaign_id': campaign.campaign_id,
            'podcast_id': campaign.podcast_id,
            'sponsor_id': campaign.sponsor_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    # Calculate TTFV if this is the user's first campaign
    try:
        from src.analytics.analytics_store import AnalyticsStore
        from src.database import TimescaleConnection
        timescale_conn = request.app.state.timescale_conn if request else None
        analytics_store = AnalyticsStore(
            metrics_collector=request.app.state.metrics_collector if request else None,
            timescale_conn=timescale_conn,
            postgres_conn=postgres_conn
        )
        await analytics_store.calculate_ttfv(str(current_user['user_id']))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to calculate TTFV: {e}")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        podcast_id=campaign.podcast_id,
        sponsor_id=campaign.sponsor_id,
        name=campaign.name,
        status=campaign.status.value,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        campaign_value=campaign.campaign_value,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at
    )


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    podcast_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """List campaigns"""
    query = """
        SELECT c.campaign_id, c.podcast_id, c.sponsor_id, c.name, c.status,
               c.start_date, c.end_date, c.campaign_value, c.created_at, c.updated_at
        FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE p.user_id = $1
    """
    params = [current_user['user_id']]
    
    if podcast_id:
        query += " AND c.podcast_id = $" + str(len(params) + 1)
        params.append(podcast_id)
    
    if status:
        query += " AND c.status = $" + str(len(params) + 1)
        params.append(status)
    
    query += " ORDER BY c.created_at DESC"
    
    rows = await postgres_conn.fetch(query, *params)
    
    return [
        CampaignResponse(
            campaign_id=str(row['campaign_id']),
            podcast_id=str(row['podcast_id']),
            sponsor_id=str(row['sponsor_id']),
            name=row['name'],
            status=row['status'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            campaign_value=float(row['campaign_value']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        for row in rows
    ]


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get campaign by ID"""
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.campaign_id, c.podcast_id, c.sponsor_id, c.name, c.status,
               c.start_date, c.end_date, c.campaign_value, c.created_at, c.updated_at
        FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        campaign_id,
        current_user['user_id']
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return CampaignResponse(
        campaign_id=str(campaign['campaign_id']),
        podcast_id=str(campaign['podcast_id']),
        sponsor_id=str(campaign['sponsor_id']),
        name=campaign['name'],
        status=campaign['status'],
        start_date=campaign['start_date'],
        end_date=campaign['end_date'],
        campaign_value=float(campaign['campaign_value']),
        created_at=campaign['created_at'],
        updated_at=campaign['updated_at']
    )


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    campaign_manager: CampaignManager = Depends(get_campaign_manager),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update campaign"""
    # Verify ownership
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.* FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        campaign_id,
        current_user['user_id']
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update campaign
    update_data = campaign_data.dict(exclude_unset=True)
    status_obj = None
    if 'status' in update_data:
        status_obj = CampaignStatus(update_data['status'])
        del update_data['status']
    
    # Prepare update dict
    updates = update_data.copy()
    if status_obj:
        updates['status'] = status_obj
    
    updated_campaign = await campaign_manager.update_campaign(
        user_id=str(current_user['user_id']),
        campaign_id=campaign_id,
        updates=updates
    )
    
    if not updated_campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or update failed"
        )
    
    # Log event
    await event_logger.log_event(
        event_type='campaign.updated',
        user_id=str(current_user['user_id']),
        properties={'campaign_id': campaign_id}
    )
    
    return CampaignResponse(
        campaign_id=updated_campaign.campaign_id,
        podcast_id=updated_campaign.podcast_id,
        sponsor_id=updated_campaign.sponsor_id,
        name=updated_campaign.name,
        status=updated_campaign.status.value,
        start_date=updated_campaign.start_date,
        end_date=updated_campaign.end_date,
        campaign_value=updated_campaign.campaign_value,
        created_at=updated_campaign.created_at,
        updated_at=updated_campaign.updated_at
    )


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    campaign_manager: CampaignManager = Depends(get_campaign_manager),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete campaign"""
    # Verify ownership
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.* FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        campaign_id,
        current_user['user_id']
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Delete campaign
    await campaign_manager.delete_campaign(
        user_id=str(current_user['user_id']),
        campaign_id=campaign_id
    )
    
    # Log event
    await event_logger.log_event(
        event_type='campaign.deleted',
        user_id=str(current_user['user_id']),
        properties={'campaign_id': campaign_id}
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/campaigns/{campaign_id}/duplicate", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    campaign_manager: CampaignManager = Depends(get_campaign_manager),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Duplicate a campaign"""
    # Get original campaign
    original_campaign = await postgres_conn.fetchrow(
        """
        SELECT c.campaign_id, c.podcast_id, c.sponsor_id, c.name, c.status,
               c.start_date, c.end_date, c.campaign_value, c.created_at, c.updated_at
        FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        campaign_id,
        current_user['user_id']
    )
    
    if not original_campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    original = CampaignResponse(
        campaign_id=str(original_campaign['campaign_id']),
        podcast_id=str(original_campaign['podcast_id']),
        sponsor_id=str(original_campaign['sponsor_id']),
        name=original_campaign['name'],
        status=original_campaign['status'],
        start_date=original_campaign['start_date'],
        end_date=original_campaign['end_date'],
        campaign_value=float(original_campaign['campaign_value']),
        created_at=original_campaign['created_at'],
        updated_at=original_campaign['updated_at']
    )
    
    # Create duplicate
    # Create attribution config (use default)
    attribution_config = AttributionConfig(
        method=AttributionMethod.PROMO_CODE
    )
    
    # Create duplicate campaign
    duplicate = await campaign_manager.create_campaign(
        user_id=str(current_user['user_id']),
        podcast_id=original.podcast_id,
        sponsor_id=original.sponsor_id,
        name=f"{original.name} (Copy)",
        start_date=original.start_date,
        end_date=original.end_date,
        campaign_value=original.campaign_value,
        attribution_config=attribution_config,
        episode_ids=[],
        notes=None
    )
    
    # Log event
    await event_logger.log_event(
        event_type='campaign.duplicated',
        user_id=str(current_user['user_id']),
        properties={
            'original_campaign_id': campaign_id,
            'duplicate_campaign_id': duplicate.campaign_id
        }
    )
    
    return CampaignResponse(
        campaign_id=duplicate.campaign_id,
        podcast_id=duplicate.podcast_id,
        sponsor_id=duplicate.sponsor_id,
        name=duplicate.name,
        status=duplicate.status.value,
        start_date=duplicate.start_date,
        end_date=duplicate.end_date,
        campaign_value=duplicate.campaign_value,
        created_at=duplicate.created_at,
        updated_at=duplicate.updated_at
    )


@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store = None
):
    """Get campaign analytics"""
    from src.analytics.analytics_store import AnalyticsStore
    from src.database import TimescaleConnection
    from src.telemetry.metrics import MetricsCollector
    from src.telemetry.events import EventLogger
    
    # Verify ownership
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.* FROM campaigns c
        INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        campaign_id,
        current_user['user_id']
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get analytics store instance
    if analytics_store is None:
        metrics_collector = request.app.state.metrics_collector
        timescale_conn = request.app.state.timescale_conn
        analytics_store = AnalyticsStore(
            metrics_collector=metrics_collector,
            timescale_conn=timescale_conn,
            postgres_conn=postgres_conn
        )
    
    # Check cache first
    from src.cache.cache_manager import CacheManager
    cache_manager = getattr(request.app.state, 'cache_manager', None) if request else None
    cache_key = f"campaign:analytics:{campaign_id}"
    
    if cache_manager:
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
    
    # Get campaign performance from analytics store
    try:
        performance = await analytics_store.calculate_campaign_performance(
            campaign_id=campaign_id,
            podcast_id=str(campaign['podcast_id']),
            start_date=campaign['start_date'],
            end_date=campaign['end_date']
        )
        
        # Calculate ROI if we have campaign value
        roi = None
        if campaign.get('campaign_value') and campaign['campaign_value'] > 0:
            roi = ((performance.conversion_value - campaign['campaign_value']) / campaign['campaign_value']) * 100
        
        result = {
            "campaign_id": campaign_id,
            "impressions": performance.total_downloads + performance.total_streams,
            "clicks": performance.attribution_events,
            "conversions": performance.conversions,
            "revenue": performance.conversion_value,
            "roi": roi,
            "total_downloads": performance.total_downloads,
            "total_streams": performance.total_streams,
            "total_listeners": performance.total_listeners,
            "attribution_events": performance.attribution_events
        }
        
        # Cache result (1 minute TTL for analytics)
        if cache_manager:
            await cache_manager.set(cache_key, result, ttl_seconds=60)
        
        return result
    except Exception as e:
        # Fallback to basic query if analytics store fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Analytics store query failed: {e}, falling back to basic query")
        
        # Get attribution events count
        attribution_count = await postgres_conn.fetchval(
            """
            SELECT COUNT(*) FROM attribution_events
            WHERE campaign_id = $1
            """,
            campaign_id
        ) or 0
        
        # Get conversions count
        conversions_count = await postgres_conn.fetchval(
            """
            SELECT COUNT(*) FROM attribution_events
            WHERE campaign_id = $1 AND conversion_type IS NOT NULL
            """,
            campaign_id
        ) or 0
        
        # Get total conversion value
        conversion_value = await postgres_conn.fetchval(
            """
            SELECT COALESCE(SUM(conversion_value), 0) FROM attribution_events
            WHERE campaign_id = $1 AND conversion_value IS NOT NULL
            """,
            campaign_id
        ) or 0.0
        
        # Calculate ROI
        roi = None
        if campaign.get('campaign_value') and campaign['campaign_value'] > 0:
            roi = ((conversion_value - campaign['campaign_value']) / campaign['campaign_value']) * 100
        
        return {
            "campaign_id": campaign_id,
            "impressions": 0,  # Would need listener metrics
            "clicks": attribution_count,
            "conversions": conversions_count,
            "revenue": float(conversion_value),
            "roi": roi
        }

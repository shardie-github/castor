"""
Attribution API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from src.attribution import AttributionEngine, AttributionModelType
from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.analytics.analytics_store import AnalyticsStore, AttributionEvent
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class AttributionRequest(BaseModel):
    campaign_id: str
    model_type: str  # "first_touch", "last_touch", "linear", "time_decay", "position_based"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AttributionResponse(BaseModel):
    campaign_id: str
    model_type: str
    total_conversions: int
    total_conversion_value: float
    attributed_conversions: int
    attributed_conversion_value: float
    touchpoint_credits: Dict[str, float]
    confidence_score: float
    calculated_at: str


def get_attribution_engine(request: Request) -> AttributionEngine:
    return request.app.state.attribution_engine


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


def get_analytics_store(
    request: Request,
    metrics: MetricsCollector = Depends(get_metrics_collector),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
) -> AnalyticsStore:
    """Get analytics store instance"""
    from src.database import TimescaleConnection
    timescale_conn = request.app.state.timescale_conn if hasattr(request.app.state, 'timescale_conn') else None
    return AnalyticsStore(
        metrics_collector=metrics,
        timescale_conn=timescale_conn,
        postgres_conn=postgres_conn
    )


@router.post("/calculate", response_model=AttributionResponse)
async def calculate_attribution(
    request_data: AttributionRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    attribution_engine: AttributionEngine = Depends(get_attribution_engine)
):
    """Calculate attribution for a campaign"""
    try:
        model_type = AttributionModelType(request_data.model_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type: {request_data.model_type}"
        )
    
    start_date = None
    end_date = None
    
    if request_data.start_date:
        start_date = datetime.fromisoformat(request_data.start_date.replace("Z", "+00:00"))
    if request_data.end_date:
        end_date = datetime.fromisoformat(request_data.end_date.replace("Z", "+00:00"))
    
    result = await attribution_engine.calculate_attribution(
        campaign_id=request_data.campaign_id,
        tenant_id=tenant_id,
        model_type=model_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return AttributionResponse(
        campaign_id=result.campaign_id,
        model_type=result.model_type.value if result.model_type else request_data.model_type,
        total_conversions=result.total_conversions,
        total_conversion_value=result.total_conversion_value,
        attributed_conversions=result.attributed_conversions,
        attributed_conversion_value=result.attributed_conversion_value,
        touchpoint_credits=result.touchpoint_credits,
        confidence_score=result.confidence_score,
        calculated_at=result.calculated_at.isoformat()
    )


@router.post("/compare")
async def compare_models(
    campaign_id: str,
    model_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    attribution_engine: AttributionEngine = Depends(get_attribution_engine)
):
    """Compare multiple attribution models"""
    if model_types is None:
        model_types = [mt.value for mt in AttributionModelType]
    
    model_type_enums = []
    for mt in model_types:
        try:
            model_type_enums.append(AttributionModelType(mt))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model type: {mt}")
    
    start_date_dt = None
    end_date_dt = None
    
    if start_date:
        start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        end_date_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    results = await attribution_engine.compare_models(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        model_types=model_type_enums,
        start_date=start_date_dt,
        end_date=end_date_dt
    )
    
    return {
        "campaign_id": campaign_id,
        "comparisons": {
            mt.value: {
                "total_conversions": r.total_conversions,
                "attributed_conversions": r.attributed_conversions,
                "attributed_conversion_value": r.attributed_conversion_value,
                "confidence_score": r.confidence_score
            }
            for mt, r in results.items()
        }
    }


class AttributionEventRequest(BaseModel):
    """Request model for attribution events from pixel"""
    event_type: str  # impression, click, conversion
    campaign_id: str
    promo_code: Optional[str] = None
    timestamp: Optional[str] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    link_url: Optional[str] = None
    link_text: Optional[str] = None
    conversion_type: Optional[str] = None
    conversion_value: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/events/{campaign_id}", response_model=List[Dict[str, Any]])
async def get_attribution_events(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store),
    limit: int = 100,
    offset: int = 0
):
    """Get attribution events for a campaign"""
    # Verify campaign ownership
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.campaign_id FROM campaigns c
        JOIN podcasts p ON c.podcast_id = p.podcast_id
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
    
    # Get attribution events
    events = await analytics_store.get_attribution_events(campaign_id)
    
    # Convert to dict format for API response
    events_data = []
    for event in events[offset:offset + limit]:
        # Get metadata if available
        metadata = await postgres_conn.fetchrow(
            """
            SELECT page_url, referrer, user_agent, utm_source, utm_medium, utm_campaign
            FROM attribution_event_metadata
            WHERE event_id = $1
            """,
            event.event_id
        )
        
        event_dict = {
            "event_id": str(event.event_id),
            "campaign_id": event.campaign_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "promo_code": event.promo_code,
            "conversion_type": event.conversion_type,
            "conversion_value": event.conversion_value,
            "attribution_method": event.attribution_method,
            "page_url": metadata.get("page_url") if metadata else None,
            "referrer": metadata.get("referrer") if metadata else None,
            "utm_source": metadata.get("utm_source") if metadata else None,
            "utm_medium": metadata.get("utm_medium") if metadata else None,
            "utm_campaign": metadata.get("utm_campaign") if metadata else None,
        }
        events_data.append(event_dict)
    
    return events_data


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def record_attribution_event(
    event_data: AttributionEventRequest,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """
    Record an attribution event from the tracking pixel.
    This endpoint is called by the attribution.js script.
    """
    try:
        # Validate campaign exists
        campaign = await postgres_conn.fetchrow(
            """
            SELECT c.campaign_id, c.podcast_id, c.start_date, c.end_date
            FROM campaigns c
            WHERE c.campaign_id = $1
            """,
            event_data.campaign_id
        )
        
        if not campaign:
            logger.warning(f"Campaign not found: {event_data.campaign_id}")
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        
        # Parse timestamp
        event_timestamp = datetime.utcnow()
        if event_data.timestamp:
            try:
                event_timestamp = datetime.fromisoformat(event_data.timestamp.replace('Z', '+00:00'))
            except Exception:
                pass
        
        # Create attribution event
        attribution_event = AttributionEvent(
            event_id=str(uuid.uuid4()),
            timestamp=event_timestamp,
            campaign_id=event_data.campaign_id,
            podcast_id=str(campaign['podcast_id']),
            episode_id=None,  # Would need to extract from metadata
            attribution_method='promo_code' if event_data.promo_code else 'utm',
            conversion_value=event_data.conversion_value,
            conversion_type=event_data.conversion_type if event_data.event_type == 'conversion' else None,
            user_id=None  # Anonymous tracking
        )
        
        # Store event in analytics store
        await analytics_store.store_attribution_event(attribution_event)
        
        # Store additional metadata in database if needed
        await postgres_conn.execute(
            """
            INSERT INTO attribution_event_metadata 
            (event_id, page_url, referrer, user_agent, utm_source, utm_medium, utm_campaign, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (event_id) DO NOTHING
            """,
            attribution_event.event_id,
            event_data.page_url,
            event_data.referrer,
            event_data.user_agent,
            event_data.utm_source,
            event_data.utm_medium,
            event_data.utm_campaign,
            event_data.metadata or {}
        )
        
        # Log event
        await event_logger.log_event(
            event_type=f'attribution.{event_data.event_type}',
            user_id=None,
            properties={
                'campaign_id': event_data.campaign_id,
                'event_id': attribution_event.event_id,
                'promo_code': event_data.promo_code,
                'conversion_type': event_data.conversion_type,
                'conversion_value': event_data.conversion_value
            }
        )
        
        return {
            "success": True,
            "event_id": attribution_event.event_id,
            "timestamp": event_timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to record attribution event: {e}", exc_info=True)
        # Return 200 to prevent pixel retries, but log the error
        return Response(status_code=status.HTTP_200_OK)

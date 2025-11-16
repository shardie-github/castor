"""
Analytics API Routes

Provides endpoints for analytics data retrieval and analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.database import PostgresConnection, TimescaleConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user
from src.analytics.analytics_store import AnalyticsStore, CampaignPerformance

router = APIRouter()


# Pydantic Models
class AnalyticsQuery(BaseModel):
    campaign_id: Optional[str] = None
    podcast_id: Optional[str] = None
    episode_id: Optional[str] = None
    start_date: datetime
    end_date: datetime
    metric_types: Optional[List[str]] = None
    group_by: Optional[List[str]] = None


class CampaignPerformanceResponse(BaseModel):
    campaign_id: str
    podcast_id: str
    start_date: datetime
    end_date: datetime
    total_downloads: int
    total_streams: int
    total_listeners: int
    attribution_events: int
    conversions: int
    conversion_value: float
    roi: Optional[float]
    roas: Optional[float]


class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float
    platform: Optional[str] = None
    country: Optional[str] = None
    device: Optional[str] = None


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_timescale_conn(request: Request) -> TimescaleConnection:
    """Get TimescaleDB connection from app state"""
    return request.app.state.timescale_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


def get_analytics_store(
    metrics: MetricsCollector = Depends(get_metrics_collector),
    timescale_conn: TimescaleConnection = Depends(get_timescale_conn),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
) -> AnalyticsStore:
    """Get analytics store instance"""
    return AnalyticsStore(
        metrics_collector=metrics,
        timescale_conn=timescale_conn,
        postgres_conn=postgres_conn
    )


# API Endpoints
@router.get("/analytics/campaigns/{campaign_id}/performance", response_model=CampaignPerformanceResponse)
async def get_campaign_performance(
    campaign_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get campaign performance metrics"""
    # Verify campaign belongs to user
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.campaign_id, c.podcast_id, c.start_date, c.end_date
        FROM campaigns c
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
    
    start = start_date or campaign['start_date']
    end = end_date or campaign['end_date']
    
    performance = await analytics_store.get_campaign_performance(
        campaign_id=campaign_id,
        start_date=start,
        end_date=end
    )
    
    return CampaignPerformanceResponse(
        campaign_id=performance.campaign_id,
        podcast_id=performance.podcast_id,
        start_date=performance.start_date,
        end_date=performance.end_date,
        total_downloads=performance.total_downloads,
        total_streams=performance.total_streams,
        total_listeners=performance.total_listeners,
        attribution_events=performance.attribution_events,
        conversions=performance.conversions,
        conversion_value=performance.conversion_value,
        roi=performance.roi,
        roas=performance.roas
    )


@router.post("/analytics/metrics", response_model=List[MetricDataPoint])
async def get_metrics(
    query: AnalyticsQuery,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get time-series metrics"""
    # Verify access to campaign/podcast/episode
    if query.campaign_id:
        campaign = await postgres_conn.fetchrow(
            """
            SELECT c.campaign_id FROM campaigns c
            JOIN podcasts p ON c.podcast_id = p.podcast_id
            WHERE c.campaign_id = $1 AND p.user_id = $2
            """,
            query.campaign_id,
            current_user['user_id']
        )
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
    elif query.podcast_id:
        podcast = await postgres_conn.fetchrow(
            "SELECT podcast_id FROM podcasts WHERE podcast_id = $1 AND user_id = $2",
            query.podcast_id,
            current_user['user_id']
        )
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
    
    # Get metrics from analytics store
    metrics = await analytics_store.get_metrics(
        campaign_id=query.campaign_id,
        podcast_id=query.podcast_id,
        episode_id=query.episode_id,
        start_date=query.start_date,
        end_date=query.end_date,
        metric_types=query.metric_types,
        group_by=query.group_by
    )
    
    return [
        MetricDataPoint(
            timestamp=m.timestamp,
            value=m.value,
            platform=m.platform,
            country=m.country,
            device=m.device
        )
        for m in metrics
    ]


@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get dashboard analytics summary"""
    # Get user's campaigns
    campaigns = await postgres_conn.fetch(
        """
        SELECT c.campaign_id, c.podcast_id, c.start_date, c.end_date
        FROM campaigns c
        JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE p.user_id = $1
        ORDER BY c.created_at DESC
        LIMIT 10
        """,
        current_user['user_id']
    )
    
    dashboard_data = {
        'total_campaigns': len(campaigns),
        'active_campaigns': 0,
        'total_revenue': 0.0,
        'total_conversions': 0,
        'average_roi': 0.0,
        'recent_performance': []
    }
    
    # Calculate aggregate metrics
    roi_sum = 0.0
    roi_count = 0
    
    for campaign in campaigns:
        try:
            performance = await analytics_store.get_campaign_performance(
                campaign_id=str(campaign['campaign_id']),
                start_date=campaign['start_date'],
                end_date=campaign['end_date']
            )
            
            if performance.conversions > 0:
                dashboard_data['active_campaigns'] += 1
            
            dashboard_data['total_revenue'] += performance.conversion_value
            dashboard_data['total_conversions'] += performance.conversions
            
            if performance.roi is not None:
                roi_sum += performance.roi
                roi_count += 1
            
            dashboard_data['recent_performance'].append({
                'campaign_id': str(campaign['campaign_id']),
                'conversions': performance.conversions,
                'revenue': performance.conversion_value,
                'roi': performance.roi
            })
        except Exception:
            continue
    
    if roi_count > 0:
        dashboard_data['average_roi'] = roi_sum / roi_count
    
    return dashboard_data

"""
Sprint Metrics API Routes

Provides endpoints for sprint-specific metrics including TTFV and completion rate.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import PostgresConnection, TimescaleConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user
from src.analytics.analytics_store import AnalyticsStore

router = APIRouter()


# Pydantic Models
class TTFVResponse(BaseModel):
    user_id: str
    ttfv_seconds: Optional[float]
    ttfv_minutes: Optional[float]
    ttfv_hours: Optional[float]


class TTFVDistributionResponse(BaseModel):
    p50: Optional[float]
    p75: Optional[float]
    p90: Optional[float]
    p95: Optional[float]
    mean: Optional[float]
    count: int


class CompletionRateResponse(BaseModel):
    completion_rate: float
    total_campaigns: int
    completed_campaigns: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]


class SprintMetricsResponse(BaseModel):
    ttfv_distribution: TTFVDistributionResponse
    completion_rate: CompletionRateResponse
    error_rate: Optional[float]
    timestamp: datetime


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
@router.get("/sprint-metrics/ttfv/{user_id}", response_model=TTFVResponse)
async def get_user_ttfv(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get TTFV for a specific user"""
    # Only allow users to view their own TTFV or admins
    if str(current_user['user_id']) != user_id and current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's TTFV"
        )
    
    ttfv_seconds = await analytics_store.calculate_ttfv(user_id)
    
    if ttfv_seconds is None:
        return TTFVResponse(
            user_id=user_id,
            ttfv_seconds=None,
            ttfv_minutes=None,
            ttfv_hours=None
        )
    
    return TTFVResponse(
        user_id=user_id,
        ttfv_seconds=ttfv_seconds,
        ttfv_minutes=ttfv_seconds / 60.0,
        ttfv_hours=ttfv_seconds / 3600.0
    )


@router.get("/sprint-metrics/ttfv-distribution", response_model=TTFVDistributionResponse)
async def get_ttfv_distribution(
    current_user: dict = Depends(get_current_user),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get TTFV distribution statistics"""
    # Only admins can view distribution
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    distribution = await analytics_store.get_ttfv_distribution()
    
    return TTFVDistributionResponse(
        p50=distribution.get('p50'),
        p75=distribution.get('p75'),
        p90=distribution.get('p90'),
        p95=distribution.get('p95'),
        mean=distribution.get('mean'),
        count=distribution.get('count', 0)
    )


@router.get("/sprint-metrics/completion-rate", response_model=CompletionRateResponse)
async def get_completion_rate(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    analytics_store: AnalyticsStore = Depends(get_analytics_store)
):
    """Get campaign completion rate"""
    # Only admins can view completion rate
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    completion_rate = await analytics_store.calculate_completion_rate(start_date, end_date)
    
    # Get total and completed counts
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND c.created_at >= $" + str(len(params) + 1)
        params.append(start_date)
    if end_date:
        date_filter += " AND c.created_at <= $" + str(len(params) + 1)
        params.append(end_date)
    
    total_campaigns = await postgres_conn.fetchval(
        f"SELECT COUNT(*) FROM campaigns c WHERE 1=1 {date_filter}",
        *params
    ) or 0
    
    completed_campaigns = await postgres_conn.fetchval(
        f"""
        SELECT COUNT(DISTINCT c.campaign_id) FROM campaigns c
        INNER JOIN reports r ON c.campaign_id = r.campaign_id
        WHERE 1=1 {date_filter}
        """,
        *params
    ) or 0
    
    return CompletionRateResponse(
        completion_rate=completion_rate,
        total_campaigns=total_campaigns,
        completed_campaigns=completed_campaigns,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/sprint-metrics/dashboard", response_model=SprintMetricsResponse)
async def get_sprint_metrics_dashboard(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    analytics_store: AnalyticsStore = Depends(get_analytics_store),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get all sprint metrics for dashboard"""
    # Only admins can view sprint metrics dashboard
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get TTFV distribution
    ttfv_dist = await analytics_store.get_ttfv_distribution()
    ttfv_distribution = TTFVDistributionResponse(
        p50=ttfv_dist.get('p50'),
        p75=ttfv_dist.get('p75'),
        p90=ttfv_dist.get('p90'),
        p95=ttfv_dist.get('p95'),
        mean=ttfv_dist.get('mean'),
        count=ttfv_dist.get('count', 0)
    )
    
    # Get completion rate
    completion_rate = await analytics_store.calculate_completion_rate(start_date, end_date)
    
    # Get total and completed counts
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND c.created_at >= $" + str(len(params) + 1)
        params.append(start_date)
    if end_date:
        date_filter += " AND c.created_at <= $" + str(len(params) + 1)
        params.append(end_date)
    
    total_campaigns = await postgres_conn.fetchval(
        f"SELECT COUNT(*) FROM campaigns c WHERE 1=1 {date_filter}",
        *params
    ) or 0
    
    completed_campaigns = await postgres_conn.fetchval(
        f"""
        SELECT COUNT(DISTINCT c.campaign_id) FROM campaigns c
        INNER JOIN reports r ON c.campaign_id = r.campaign_id
        WHERE 1=1 {date_filter}
        """,
        *params
    ) or 0
    
    completion_rate_response = CompletionRateResponse(
        completion_rate=completion_rate,
        total_campaigns=total_campaigns,
        completed_campaigns=completed_campaigns,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calculate error rate (simplified - would need error tracking)
    error_rate = None
    try:
        # This would come from error tracking system
        # For now, return None
        pass
    except Exception:
        pass
    
    return SprintMetricsResponse(
        ttfv_distribution=ttfv_distribution,
        completion_rate=completion_rate_response,
        error_rate=error_rate,
        timestamp=datetime.utcnow()
    )

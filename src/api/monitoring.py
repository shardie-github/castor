"""
Monitoring API Routes

Provides endpoints for system monitoring and observability.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.database import PostgresConnection
from src.api.auth import get_current_user

router = APIRouter()


class MonitoringMetricsResponse(BaseModel):
    error_rate: float
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_minute: int
    total_requests: int
    active_users: int
    error_breakdown: Dict[str, int]
    timestamp: datetime


@router.get("/monitoring/metrics", response_model=MonitoringMetricsResponse)
async def get_monitoring_metrics(
    time_range: str = "24h",
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """
    Get system monitoring metrics.
    Admin only endpoint.
    """
    # Check admin access
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Calculate time window
    if time_range == "1h":
        start_time = datetime.utcnow() - timedelta(hours=1)
    elif time_range == "24h":
        start_time = datetime.utcnow() - timedelta(hours=24)
    elif time_range == "7d":
        start_time = datetime.utcnow() - timedelta(days=7)
    else:
        start_time = datetime.utcnow() - timedelta(hours=24)
    
    # Get metrics from database (would use metrics store in production)
    try:
        # Total requests
        total_requests = await postgres_conn.fetchval(
            """
            SELECT COUNT(*) FROM events
            WHERE event_type LIKE 'api.%' AND timestamp >= $1
            """,
            start_time
        ) or 0
        
        # Error rate
        error_requests = await postgres_conn.fetchval(
            """
            SELECT COUNT(*) FROM events
            WHERE event_type LIKE 'api.error%' AND timestamp >= $1
            """,
            start_time
        ) or 0
        
        error_rate = error_requests / total_requests if total_requests > 0 else 0.0
        
        # Response times (would come from metrics store)
        # For now, use placeholder values
        avg_response_time = 150.0  # Would calculate from actual metrics
        p50_response_time = 120.0
        p95_response_time = 300.0
        p99_response_time = 500.0
        
        # Requests per minute
        minutes = (datetime.utcnow() - start_time).total_seconds() / 60
        requests_per_minute = int(total_requests / minutes) if minutes > 0 else 0
        
        # Active users
        active_users = await postgres_conn.fetchval(
            """
            SELECT COUNT(DISTINCT user_id) FROM events
            WHERE timestamp >= $1 AND user_id IS NOT NULL
            """,
            start_time
        ) or 0
        
        # Error breakdown
        error_breakdown_rows = await postgres_conn.fetch(
            """
            SELECT 
                CASE 
                    WHEN event_type LIKE 'api.error.4%' THEN '4xx'
                    WHEN event_type LIKE 'api.error.5%' THEN '5xx'
                    ELSE 'other'
                END as error_type,
                COUNT(*) as count
            FROM events
            WHERE event_type LIKE 'api.error%' AND timestamp >= $1
            GROUP BY error_type
            """,
            start_time
        )
        
        error_breakdown = {row['error_type']: row['count'] for row in error_breakdown_rows}
        
        return MonitoringMetricsResponse(
            error_rate=error_rate,
            avg_response_time=avg_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_minute=requests_per_minute,
            total_requests=total_requests,
            active_users=active_users,
            error_breakdown=error_breakdown,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to fetch monitoring metrics: {e}")
        # Return default values
        return MonitoringMetricsResponse(
            error_rate=0.0,
            avg_response_time=0.0,
            p50_response_time=0.0,
            p95_response_time=0.0,
            p99_response_time=0.0,
            requests_per_minute=0,
            total_requests=0,
            active_users=0,
            error_breakdown={},
            timestamp=datetime.utcnow()
        )


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn

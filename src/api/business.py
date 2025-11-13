"""
Business Analytics API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from src.business.analytics import BusinessAnalytics, MetricPeriod

router = APIRouter(prefix="/api/v1/business", tags=["business"])


class BusinessDashboardResponse(BaseModel):
    """Business dashboard response"""
    period: dict
    revenue: dict
    customers: dict
    growth_trends: dict


def get_business_analytics() -> BusinessAnalytics:
    """Get business analytics service"""
    from src.main import app
    # In production, get from app state or dependency injection
    from src.business.analytics import BusinessAnalytics
    from src.database import PostgresConnection
    from src.telemetry.metrics import MetricsCollector
    from src.telemetry.events import EventLogger
    
    # This would be injected properly in production
    return BusinessAnalytics(
        postgres_conn=app.state.postgres_conn,
        metrics_collector=app.state.metrics_collector,
        event_logger=app.state.event_logger
    )


@router.get("/dashboard", response_model=BusinessDashboardResponse)
async def get_business_dashboard(
    tenant_id: Optional[str] = Query(None),
    analytics: BusinessAnalytics = Depends(get_business_analytics)
):
    """Get comprehensive business dashboard"""
    try:
        dashboard = await analytics.get_business_dashboard(tenant_id=tenant_id)
        return BusinessDashboardResponse(**dashboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue")
async def get_revenue_metrics(
    start_date: datetime = Query(default_factory=lambda: datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=datetime.utcnow),
    tenant_id: Optional[str] = Query(None),
    analytics: BusinessAnalytics = Depends(get_business_analytics)
):
    """Get revenue metrics"""
    try:
        metrics = await analytics.get_revenue_metrics(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id
        )
        return {
            "total_revenue": metrics.total_revenue,
            "recurring_revenue": metrics.recurring_revenue,
            "one_time_revenue": metrics.one_time_revenue,
            "revenue_growth_rate": metrics.revenue_growth_rate,
            "average_revenue_per_user": metrics.average_revenue_per_user,
            "lifetime_value": metrics.lifetime_value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers")
async def get_customer_metrics(
    start_date: datetime = Query(default_factory=lambda: datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=datetime.utcnow),
    tenant_id: Optional[str] = Query(None),
    analytics: BusinessAnalytics = Depends(get_business_analytics)
):
    """Get customer metrics"""
    try:
        metrics = await analytics.get_customer_metrics(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id
        )
        return {
            "total_customers": metrics.total_customers,
            "active_customers": metrics.active_customers,
            "new_customers": metrics.new_customers,
            "churned_customers": metrics.churned_customers,
            "churn_rate": metrics.churn_rate,
            "customer_growth_rate": metrics.customer_growth_rate,
            "average_customer_age_days": metrics.average_customer_age_days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/growth")
async def get_growth_metrics(
    period: MetricPeriod = Query(MetricPeriod.MONTHLY),
    months: int = Query(12, ge=1, le=24),
    analytics: BusinessAnalytics = Depends(get_business_analytics)
):
    """Get growth metrics over time"""
    try:
        metrics = await analytics.get_growth_metrics(period=period, months=months)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

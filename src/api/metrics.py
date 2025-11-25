"""
Metrics API Endpoints

Provides endpoints for user metrics, growth metrics, and business metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.database import PostgresConnection
from src.analytics.user_metrics_aggregator import UserMetricsAggregator
from src.business.analytics import BusinessAnalytics, MetricPeriod
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependencies
async def get_postgres_conn() -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    from src.main import app
    return app.state.postgres_conn


async def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector from app state"""
    from src.main import app
    return app.state.metrics_collector


async def get_event_logger() -> EventLogger:
    """Get event logger from app state"""
    from src.main import app
    return app.state.event_logger


# Response Models
class UserMetricsResponse(BaseModel):
    """User metrics response"""
    dau: int
    wau: int
    mau: int
    activation_rate: float
    day_7_retention: float
    day_30_retention: float


class GrowthMetricsResponse(BaseModel):
    """Growth metrics response"""
    period: str
    data: list


class RevenueMetricsResponse(BaseModel):
    """Revenue metrics response"""
    total_revenue: float
    recurring_revenue: float
    one_time_revenue: float
    revenue_growth_rate: float
    average_revenue_per_user: float
    lifetime_value: float


class FunnelResponse(BaseModel):
    """Funnel metrics response"""
    visitors: int
    signups: int
    activated: int
    retained_day_7: int
    paying: int
    conversion_rates: dict


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response"""
    users: UserMetricsResponse
    revenue: RevenueMetricsResponse
    growth: GrowthMetricsResponse


@router.get("/metrics/users/active", response_model=UserMetricsResponse)
async def get_active_users(
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """
    Get active user metrics (DAU/WAU/MAU, activation, retention)
    """
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        metrics = await aggregator.get_all_metrics()
        
        return UserMetricsResponse(
            dau=metrics.dau,
            wau=metrics.wau,
            mau=metrics.mau,
            activation_rate=metrics.activation_rate,
            day_7_retention=metrics.day_7_retention,
            day_30_retention=metrics.day_30_retention
        )
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/users/dau")
async def get_dau(
    date: Optional[datetime] = Query(None, description="Date to calculate DAU for"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get Daily Active Users"""
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        dau = await aggregator.get_dau(date)
        return {"dau": dau, "date": date or datetime.now()}
    except Exception as e:
        logger.error(f"Error getting DAU: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/users/wau")
async def get_wau(
    date: Optional[datetime] = Query(None, description="Date to calculate WAU for"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get Weekly Active Users"""
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        wau = await aggregator.get_wau(date)
        return {"wau": wau, "date": date or datetime.now()}
    except Exception as e:
        logger.error(f"Error getting WAU: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/users/mau")
async def get_mau(
    date: Optional[datetime] = Query(None, description="Date to calculate MAU for"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get Monthly Active Users"""
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        mau = await aggregator.get_mau(date)
        return {"mau": mau, "date": date or datetime.now()}
    except Exception as e:
        logger.error(f"Error getting MAU: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/activation")
async def get_activation_rate(
    days: int = Query(7, description="Days after signup to consider for activation"),
    lookback_days: int = Query(30, description="How far back to look for signups"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get activation rate"""
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        rate = await aggregator.get_activation_rate(days, lookback_days)
        return {
            "activation_rate": rate,
            "days": days,
            "lookback_days": lookback_days
        }
    except Exception as e:
        logger.error(f"Error getting activation rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/retention")
async def get_retention_rate(
    day: int = Query(7, description="Day to calculate retention for"),
    lookback_days: int = Query(60, description="How far back to look for activations"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get retention rate for specific day"""
    try:
        aggregator = UserMetricsAggregator(postgres_conn)
        rate = await aggregator.get_retention_rate(day, lookback_days)
        return {
            "retention_rate": rate,
            "day": day,
            "lookback_days": lookback_days
        }
    except Exception as e:
        logger.error(f"Error getting retention rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/revenue", response_model=RevenueMetricsResponse)
async def get_revenue_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID (optional)"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Get revenue metrics"""
    try:
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        analytics = BusinessAnalytics(postgres_conn, metrics_collector, event_logger)
        revenue_metrics = await analytics.get_revenue_metrics(start_date, end_date, tenant_id)
        
        return RevenueMetricsResponse(
            total_revenue=revenue_metrics.total_revenue,
            recurring_revenue=revenue_metrics.recurring_revenue,
            one_time_revenue=revenue_metrics.one_time_revenue,
            revenue_growth_rate=revenue_metrics.revenue_growth_rate,
            average_revenue_per_user=revenue_metrics.average_revenue_per_user,
            lifetime_value=revenue_metrics.lifetime_value
        )
    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/growth", response_model=GrowthMetricsResponse)
async def get_growth_metrics(
    period: str = Query("monthly", description="Period: daily, weekly, monthly"),
    months: int = Query(12, description="Number of months to look back"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Get growth metrics over time"""
    try:
        period_enum = MetricPeriod.MONTHLY
        if period == "daily":
            period_enum = MetricPeriod.DAILY
        elif period == "weekly":
            period_enum = MetricPeriod.WEEKLY
        
        analytics = BusinessAnalytics(postgres_conn, metrics_collector, event_logger)
        growth_data = await analytics.get_growth_metrics(period_enum, months)
        
        return GrowthMetricsResponse(
            period=growth_data["period"],
            data=growth_data["data"]
        )
    except Exception as e:
        logger.error(f"Error getting growth metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/funnel", response_model=FunnelResponse)
async def get_funnel_metrics(
    days: int = Query(30, description="Number of days to look back"),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get funnel metrics (visitors → signups → activated → retained → paying)"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Note: Visitors would come from frontend analytics (Google Analytics, PostHog, etc.)
        # For now, we'll use signups as proxy
        
        # Signups
        signups_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM events
            WHERE event_type = 'onboarding_started'
              AND timestamp >= $1
              AND timestamp < $2
        """
        signups_row = await postgres_conn.fetch_one(signups_query, start_date, end_date)
        signups = signups_row["count"] or 0 if signups_row else 0
        
        # Activated
        activated_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM events
            WHERE event_type IN (
                'report_generated',
                'campaign_launched',
                'attribution_setup_completed',
                'first_value_delivered'
            )
            AND timestamp >= $1
            AND timestamp < $2
        """
        activated_row = await postgres_conn.fetch_one(activated_query, start_date, end_date)
        activated = activated_row["count"] or 0 if activated_row else 0
        
        # Retained (Day 7)
        aggregator = UserMetricsAggregator(postgres_conn)
        day_7_retention_rate = await aggregator.get_retention_rate(day=7, lookback_days=days)
        retained_day_7 = int(activated * (day_7_retention_rate / 100))
        
        # Paying (users with subscription_tier != FREE)
        paying_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM users
            WHERE subscription_tier != 'FREE'
              AND created_at >= $1
              AND created_at < $2
        """
        paying_row = await postgres_conn.fetch_one(paying_query, start_date, end_date)
        paying = paying_row["count"] or 0 if paying_row else 0
        
        # Visitors (placeholder - would come from frontend analytics)
        visitors = signups * 20  # Assume 5% conversion rate
        
        # Calculate conversion rates
        conversion_rates = {
            "visitor_to_signup": (signups / visitors * 100) if visitors > 0 else 0,
            "signup_to_activated": (activated / signups * 100) if signups > 0 else 0,
            "activated_to_retained": day_7_retention_rate,
            "retained_to_paying": (paying / retained_day_7 * 100) if retained_day_7 > 0 else 0
        }
        
        return FunnelResponse(
            visitors=visitors,
            signups=signups,
            activated=activated,
            retained_day_7=retained_day_7,
            paying=paying,
            conversion_rates=conversion_rates
        )
    except Exception as e:
        logger.error(f"Error getting funnel metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Get comprehensive dashboard metrics"""
    try:
        # User metrics
        aggregator = UserMetricsAggregator(postgres_conn)
        user_metrics = await aggregator.get_all_metrics()
        
        # Revenue metrics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        analytics = BusinessAnalytics(postgres_conn, metrics_collector, event_logger)
        revenue_metrics = await analytics.get_revenue_metrics(start_date, end_date)
        
        # Growth metrics
        growth_data = await analytics.get_growth_metrics(MetricPeriod.MONTHLY, 6)
        
        return DashboardMetricsResponse(
            users=UserMetricsResponse(
                dau=user_metrics.dau,
                wau=user_metrics.wau,
                mau=user_metrics.mau,
                activation_rate=user_metrics.activation_rate,
                day_7_retention=user_metrics.day_7_retention,
                day_30_retention=user_metrics.day_30_retention
            ),
            revenue=RevenueMetricsResponse(
                total_revenue=revenue_metrics.total_revenue,
                recurring_revenue=revenue_metrics.recurring_revenue,
                one_time_revenue=revenue_metrics.one_time_revenue,
                revenue_growth_rate=revenue_metrics.revenue_growth_rate,
                average_revenue_per_user=revenue_metrics.average_revenue_per_user,
                lifetime_value=revenue_metrics.lifetime_value
            ),
            growth=GrowthMetricsResponse(
                period=growth_data["period"],
                data=growth_data["data"]
            )
        )
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

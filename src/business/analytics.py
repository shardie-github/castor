"""
Business Analytics and Reporting

Revenue tracking, customer analytics, growth metrics, and business intelligence.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class MetricPeriod(str, Enum):
    """Metric period"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class RevenueMetrics:
    """Revenue metrics"""
    total_revenue: float
    recurring_revenue: float
    one_time_revenue: float
    revenue_growth_rate: float
    average_revenue_per_user: float
    lifetime_value: float
    churn_revenue: float


@dataclass
class CustomerMetrics:
    """Customer metrics"""
    total_customers: int
    active_customers: int
    new_customers: int
    churned_customers: int
    churn_rate: float
    customer_growth_rate: float
    average_customer_age_days: float


class BusinessAnalytics:
    """Business analytics and reporting"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def get_revenue_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None
    ) -> RevenueMetrics:
        """Get revenue metrics for a period"""
        conditions = []
        params = [start_date, end_date]
        param_idx = 3
        
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                COALESCE(SUM(amount), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN is_recurring THEN amount ELSE 0 END), 0) as recurring_revenue,
                COALESCE(SUM(CASE WHEN NOT is_recurring THEN amount ELSE 0 END), 0) as one_time_revenue,
                COUNT(DISTINCT customer_id) as paying_customers
            FROM payments
            WHERE created_at >= $1 AND created_at <= $2
            AND status = 'completed'
            AND ({where_clause})
        """
        
        row = await self.postgres_conn.fetch_one(query, *params)
        
        total_revenue = float(row["total_revenue"] or 0)
        recurring_revenue = float(row["recurring_revenue"] or 0)
        one_time_revenue = float(row["one_time_revenue"] or 0)
        paying_customers = row["paying_customers"] or 0
        
        # Calculate previous period for growth
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        prev_row = await self.postgres_conn.fetch_one(
            query.replace("$1", f"${param_idx}").replace("$2", f"${param_idx + 1}"),
            prev_start, prev_end, *params[2:]
        )
        prev_revenue = float(prev_row["total_revenue"] or 0) if prev_row else 0
        
        revenue_growth_rate = (
            ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        )
        
        avg_revenue_per_user = (
            total_revenue / paying_customers if paying_customers > 0 else 0
        )
        
        # Calculate LTV (improved - uses actual churn data)
        # Get churn rate from customer metrics
        customer_metrics = await self.get_customer_metrics(start_date, end_date, tenant_id)
        monthly_churn_rate = customer_metrics.churn_rate / 100.0  # Convert to decimal
        
        # Calculate average customer lifetime (in months)
        if monthly_churn_rate > 0:
            avg_customer_lifetime_months = 1 / monthly_churn_rate
        else:
            avg_customer_lifetime_months = 24  # Default if no churn data
        
        # Calculate LTV: ARPU × Average Customer Lifetime
        lifetime_value = avg_revenue_per_user * avg_customer_lifetime_months
        
        return RevenueMetrics(
            total_revenue=total_revenue,
            recurring_revenue=recurring_revenue,
            one_time_revenue=one_time_revenue,
            revenue_growth_rate=revenue_growth_rate,
            average_revenue_per_user=avg_revenue_per_user,
            lifetime_value=lifetime_value,
            churn_revenue=0.0  # Would need churn data
        )
    
    async def get_customer_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None
    ) -> CustomerMetrics:
        """Get customer metrics for a period"""
        conditions = []
        params = [start_date, end_date]
        param_idx = 3
        
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                COUNT(*) as total_customers,
                COUNT(*) FILTER (WHERE status = 'active') as active_customers,
                COUNT(*) FILTER (WHERE created_at >= $1 AND created_at <= $2) as new_customers,
                COUNT(*) FILTER (WHERE status = 'cancelled' AND cancelled_at >= $1 AND cancelled_at <= $2) as churned_customers,
                AVG(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400) as avg_customer_age_days
            FROM tenants
            WHERE ({where_clause})
        """
        
        row = await self.postgres_conn.fetch_one(query, *params)
        
        total_customers = row["total_customers"] or 0
        active_customers = row["active_customers"] or 0
        new_customers = row["new_customers"] or 0
        churned_customers = row["churned_customers"] or 0
        avg_age_days = float(row["avg_customer_age_days"] or 0)
        
        churn_rate = (
            (churned_customers / total_customers * 100) if total_customers > 0 else 0
        )
        
        # Calculate growth rate
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        
        prev_query = f"""
            SELECT COUNT(*) as prev_total
            FROM tenants
            WHERE created_at < ${param_idx}
            AND ({where_clause})
        """
        prev_row = await self.postgres_conn.fetch_one(prev_query, prev_start, *params[2:])
        prev_total = prev_row["prev_total"] or 0 if prev_row else 0
        
        customer_growth_rate = (
            ((total_customers - prev_total) / prev_total * 100) if prev_total > 0 else 0
        )
        
        return CustomerMetrics(
            total_customers=total_customers,
            active_customers=active_customers,
            new_customers=new_customers,
            churned_customers=churned_customers,
            churn_rate=churn_rate,
            customer_growth_rate=customer_growth_rate,
            average_customer_age_days=avg_age_days
        )
    
    async def get_growth_metrics(
        self,
        period: MetricPeriod = MetricPeriod.MONTHLY,
        months: int = 12
    ) -> Dict:
        """Get growth metrics over time"""
        end_date = datetime.utcnow()
        
        if period == MetricPeriod.MONTHLY:
            start_date = end_date - timedelta(days=months * 30)
            group_by = "DATE_TRUNC('month', created_at)"
        elif period == MetricPeriod.WEEKLY:
            start_date = end_date - timedelta(weeks=months * 4)
            group_by = "DATE_TRUNC('week', created_at)"
        else:
            start_date = end_date - timedelta(days=months * 30)
            group_by = "DATE_TRUNC('month', created_at)"
        
        query = f"""
            SELECT 
                {group_by} as period,
                COUNT(*) as new_customers,
                COALESCE(SUM(amount), 0) as revenue
            FROM tenants t
            LEFT JOIN payments p ON p.customer_id = t.tenant_id
            WHERE t.created_at >= $1 AND t.created_at <= $2
            GROUP BY {group_by}
            ORDER BY period ASC
        """
        
        rows = await self.postgres_conn.fetch_all(query, start_date, end_date)
        
        return {
            "period": period.value,
            "data": [
                {
                    "period": row["period"].isoformat() if row["period"] else None,
                    "new_customers": row["new_customers"] or 0,
                    "revenue": float(row["revenue"] or 0)
                }
                for row in rows
            ]
        }
    
    async def get_business_dashboard(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict:
        """Get comprehensive business dashboard"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        revenue_metrics = await self.get_revenue_metrics(start_date, end_date, tenant_id)
        customer_metrics = await self.get_customer_metrics(start_date, end_date, tenant_id)
        growth_metrics = await self.get_growth_metrics(MetricPeriod.MONTHLY, 6)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "revenue": {
                "total": revenue_metrics.total_revenue,
                "recurring": revenue_metrics.recurring_revenue,
                "one_time": revenue_metrics.one_time_revenue,
                "growth_rate": revenue_metrics.revenue_growth_rate,
                "avg_per_user": revenue_metrics.average_revenue_per_user,
                "lifetime_value": revenue_metrics.lifetime_value
            },
            "customers": {
                "total": customer_metrics.total_customers,
                "active": customer_metrics.active_customers,
                "new": customer_metrics.new_customers,
                "churned": customer_metrics.churned_customers,
                "churn_rate": customer_metrics.churn_rate,
                "growth_rate": customer_metrics.customer_growth_rate,
                "avg_age_days": customer_metrics.average_customer_age_days
            },
            "growth_trends": growth_metrics
        }

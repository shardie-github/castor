"""
Analytics Service

Business logic for analytics and reporting.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.database import PostgresConnection, TimescaleConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics business logic"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        timescale_conn: TimescaleConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.timescale_conn = timescale_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def get_dashboard_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get dashboard analytics"""
        # Get campaign counts
        campaign_query = """
            SELECT 
                COUNT(*) as total_campaigns,
                COUNT(*) FILTER (WHERE status = 'active') as active_campaigns
            FROM campaigns
            WHERE tenant_id = $1
        """
        campaign_stats = await self.postgres_conn.fetchrow(campaign_query, tenant_id)
        
        # Get revenue and conversions
        revenue_query = """
            SELECT 
                SUM(revenue) as total_revenue,
                COUNT(*) FILTER (WHERE event_type = 'conversion') as total_conversions
            FROM attribution_events
            WHERE tenant_id = $1
        """
        params = [tenant_id]
        
        if start_date:
            revenue_query += " AND event_time >= $2"
            params.append(start_date)
        
        if end_date:
            revenue_query += " AND event_time <= $" + str(len(params) + 1)
            params.append(end_date)
        
        revenue_stats = await self.postgres_conn.fetchrow(revenue_query, *params)
        
        # Calculate average ROI
        roi_query = """
            SELECT AVG(
                CASE 
                    WHEN c.campaign_value > 0 THEN
                        ((ae.revenue - c.campaign_value) / c.campaign_value * 100)
                    ELSE 0
                END
            ) as average_roi
            FROM campaigns c
            LEFT JOIN attribution_events ae ON c.campaign_id = ae.campaign_id
            WHERE c.tenant_id = $1
        """
        roi_result = await self.postgres_conn.fetchrow(roi_query, tenant_id)
        
        return {
            'total_campaigns': campaign_stats['total_campaigns'] or 0,
            'active_campaigns': campaign_stats['active_campaigns'] or 0,
            'total_revenue': float(revenue_stats['total_revenue'] or 0),
            'total_conversions': revenue_stats['total_conversions'] or 0,
            'average_roi': float(roi_result['average_roi'] or 0)
        }
    
    async def get_time_series_analytics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'day'
    ) -> List[Dict[str, Any]]:
        """Get time-series analytics"""
        # Use TimescaleDB for efficient time-series queries
        query = """
            SELECT 
                time_bucket($1::interval, event_time) as bucket,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as conversions,
                SUM(CASE WHEN event_type = 'conversion' THEN revenue ELSE 0 END) as revenue
            FROM attribution_events
            WHERE tenant_id = $2
                AND event_time >= $3
                AND event_time <= $4
            GROUP BY bucket
            ORDER BY bucket
        """
        
        interval_map = {
            'hour': '1 hour',
            'day': '1 day',
            'week': '1 week',
            'month': '1 month'
        }
        interval = interval_map.get(granularity, '1 day')
        
        results = await self.timescale_conn.fetch(
            query,
            interval,
            tenant_id,
            start_date,
            end_date
        )
        
        return [
            {
                'date': row['bucket'].isoformat(),
                'events': row['events'],
                'unique_users': row['unique_users'],
                'conversions': row['conversions'],
                'revenue': float(row['revenue'] or 0)
            }
            for row in results
        ]

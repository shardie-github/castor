"""
Attribution Analytics

Provides analytics and reporting for attribution data.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, date

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class AttributionAnalytics:
    """
    Attribution Analytics
    
    Provides analytics and insights for attribution data.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def get_attribution_summary(
        self,
        tenant_id: str,
        campaign_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get attribution summary for campaign"""
        query = """
            SELECT 
                SUM(CASE WHEN metric_type = 'attributed_conversions' THEN metric_value ELSE 0 END) as total_conversions,
                SUM(CASE WHEN metric_type = 'attributed_revenue' THEN metric_value ELSE 0 END) as total_revenue
            FROM attribution_analytics
            WHERE tenant_id = $1 AND campaign_id = $2
        """
        
        params = [tenant_id, campaign_id]
        if start_date:
            query += " AND date >= $" + str(len(params) + 1)
            params.append(start_date)
        if end_date:
            query += " AND date <= $" + str(len(params) + 1)
            params.append(end_date)
        
        row = await self.postgres.fetchrow(query, *params)
        
        return {
            "total_conversions": float(row["total_conversions"] or 0),
            "total_revenue": float(row["total_revenue"] or 0)
        }

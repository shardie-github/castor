"""
Cost Monitoring

Monitors cost trends and alerts on budget thresholds.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, date

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class CostMonitor:
    """
    Cost Monitor
    
    Monitors costs and triggers alerts when thresholds are exceeded.
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
    
    async def check_budget_thresholds(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Check if tenant has exceeded budget thresholds"""
        # Query active alerts
        rows = await self.postgres.fetch(
            """
            SELECT alert_id, alert_type, threshold_percentage, threshold_amount,
                   current_amount, status, triggered_at
            FROM cost_alerts
            WHERE tenant_id = $1 AND status IN ('active', 'triggered')
            """,
            tenant_id
        )
        
        return [
            {
                "alert_id": str(row["alert_id"]),
                "alert_type": row["alert_type"],
                "threshold_percentage": float(row["threshold_percentage"] or 0),
                "current_amount": float(row["current_amount"] or 0),
                "status": row["status"]
            }
            for row in rows
        ]

"""
Churn Analyzer

Analyzes churn patterns and segments churned users.
"""

import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, List, Optional, Any

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class ChurnAnalyzer:
    """
    Churn Analyzer
    
    Analyzes churn patterns, reasons, and segments.
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
    
    async def analyze_churn(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Analyze churn for time period"""
        query = """
            SELECT churn_type, churn_reason, COUNT(*) as count
            FROM churn_events
            WHERE tenant_id = $1
        """
        
        params = [tenant_id]
        if start_date:
            query += " AND churn_date >= $" + str(len(params) + 1)
            params.append(start_date)
        if end_date:
            query += " AND churn_date <= $" + str(len(params) + 1)
            params.append(end_date)
        
        query += " GROUP BY churn_type, churn_reason"
        
        rows = await self.postgres.fetch(query, *params)
        
        # Calculate churn rate
        total_users = await self.postgres.fetchval(
            """
            SELECT COUNT(*)
            FROM users
            WHERE tenant_id = $1 AND is_active = TRUE
            """,
            tenant_id
        ) or 0
        
        churned_users = sum(row["count"] for row in rows)
        churn_rate = (churned_users / total_users * 100) if total_users > 0 else 0.0
        
        return {
            "churn_rate": churn_rate,
            "total_churned": churned_users,
            "total_users": total_users,
            "breakdown": [
                {
                    "churn_type": row["churn_type"],
                    "churn_reason": row["churn_reason"],
                    "count": row["count"]
                }
                for row in rows
            ]
        }
    
    async def segment_churned_users(
        self,
        tenant_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Segment churned users by characteristics"""
        # Get churned users with details
        rows = await self.postgres.fetch(
            """
            SELECT ce.user_id, ce.churn_type, ce.churn_reason, ce.churn_date,
                   u.subscription_tier, u.created_at, u.last_login
            FROM churn_events ce
            INNER JOIN users u ON ce.user_id = u.user_id
            WHERE ce.tenant_id = $1
            ORDER BY ce.churn_date DESC
            """,
            tenant_id
        )
        
        segments = {
            "by_tier": {},
            "by_reason": {},
            "by_tenure": {
                "new_users": [],  # < 30 days
                "medium_tenure": [],  # 30-90 days
                "long_tenure": []  # > 90 days
            }
        }
        
        for row in rows:
            user_data = {
                "user_id": str(row["user_id"]),
                "churn_type": row["churn_type"],
                "churn_reason": row["churn_reason"],
                "churn_date": row["churn_date"].isoformat()
            }
            
            # Segment by tier
            tier = row["subscription_tier"]
            if tier not in segments["by_tier"]:
                segments["by_tier"][tier] = []
            segments["by_tier"][tier].append(user_data)
            
            # Segment by reason
            reason = row["churn_reason"] or "unknown"
            if reason not in segments["by_reason"]:
                segments["by_reason"][reason] = []
            segments["by_reason"][reason].append(user_data)
            
            # Segment by tenure
            days_since_signup = (row["churn_date"] - row["created_at"].date()).days
            if days_since_signup < 30:
                segments["by_tenure"]["new_users"].append(user_data)
            elif days_since_signup < 90:
                segments["by_tenure"]["medium_tenure"].append(user_data)
            else:
                segments["by_tenure"]["long_tenure"].append(user_data)
        
        return segments

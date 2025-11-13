"""
Onboarding Analyzer

Analyzes onboarding funnel and identifies drop-off points.
"""

import logging
from typing import Dict, List, Optional, Any

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class OnboardingAnalyzer:
    """
    Onboarding Analyzer
    
    Analyzes onboarding completion rates and drop-off points.
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
    
    async def analyze_onboarding_funnel(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze onboarding funnel completion rates"""
        # Get all onboarding steps
        steps = await self.postgres.fetch(
            """
            SELECT step_id, step_name, step_order
            FROM onboarding_steps
            WHERE tenant_id = $1 AND enabled = TRUE
            ORDER BY step_order ASC
            """,
            tenant_id
        )
        
        funnel_data = []
        total_started = 0
        
        for i, step in enumerate(steps):
            step_id = str(step["step_id"])
            
            # Get users who started this step
            started = await self.postgres.fetchval(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM onboarding_progress
                WHERE tenant_id = $1 AND step_id = $2
                AND status IN ('in_progress', 'completed')
                """,
                tenant_id, step_id
            ) or 0
            
            # Get users who completed this step
            completed = await self.postgres.fetchval(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM onboarding_progress
                WHERE tenant_id = $1 AND step_id = $2
                AND status = 'completed'
                """,
                tenant_id, step_id
            ) or 0
            
            # Get users who dropped off at this step
            dropped = await self.postgres.fetchval(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM onboarding_progress
                WHERE tenant_id = $1 AND step_id = $2
                AND status = 'dropped'
                """,
                tenant_id, step_id
            ) or 0
            
            if i == 0:
                total_started = started
            
            completion_rate = (completed / started * 100) if started > 0 else 0.0
            dropoff_rate = (dropped / started * 100) if started > 0 else 0.0
            
            funnel_data.append({
                "step_id": step_id,
                "step_name": step["step_name"],
                "step_order": step["step_order"],
                "started": started,
                "completed": completed,
                "dropped": dropped,
                "completion_rate": completion_rate,
                "dropoff_rate": dropoff_rate
            })
        
        # Calculate overall completion rate
        if steps:
            final_step_id = str(steps[-1]["step_id"])
            final_completed = await self.postgres.fetchval(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM onboarding_progress
                WHERE tenant_id = $1 AND step_id = $2 AND status = 'completed'
                """,
                tenant_id, final_step_id
            ) or 0
            
            overall_completion_rate = (final_completed / total_started * 100) if total_started > 0 else 0.0
        else:
            overall_completion_rate = 0.0
        
        return {
            "total_started": total_started,
            "overall_completion_rate": overall_completion_rate,
            "funnel": funnel_data
        }
    
    async def identify_dropoff_points(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Identify steps with highest drop-off rates"""
        # Get steps with drop-offs
        rows = await self.postgres.fetch(
            """
            SELECT os.step_id, os.step_name, os.step_order,
                   COUNT(DISTINCT op.user_id) as dropoff_count,
                   COUNT(DISTINCT CASE WHEN op.status = 'completed' THEN op.user_id END) as completed_count
            FROM onboarding_steps os
            LEFT JOIN onboarding_progress op ON os.step_id = op.step_id
            WHERE os.tenant_id = $1 AND os.enabled = TRUE
            AND (op.status = 'dropped' OR op.status = 'completed' OR op.status IS NULL)
            GROUP BY os.step_id, os.step_name, os.step_order
            ORDER BY dropoff_count DESC
            LIMIT 10
            """,
            tenant_id
        )
        
        dropoff_points = []
        
        for row in rows:
            total = row["dropoff_count"] + (row["completed_count"] or 0)
            dropoff_rate = (row["dropoff_count"] / total * 100) if total > 0 else 0.0
            
            dropoff_points.append({
                "step_id": str(row["step_id"]),
                "step_name": row["step_name"],
                "step_order": row["step_order"],
                "dropoff_count": row["dropoff_count"],
                "dropoff_rate": dropoff_rate
            })
        
        return dropoff_points

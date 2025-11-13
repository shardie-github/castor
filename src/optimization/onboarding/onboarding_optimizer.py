"""
Onboarding Optimizer

Optimizes onboarding flow based on analysis.
"""

import logging
from typing import Dict, List, Optional, Any

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class OnboardingOptimizer:
    """
    Onboarding Optimizer
    
    Optimizes onboarding flow and provides recommendations.
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
    
    async def optimize_onboarding(
        self,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Generate onboarding optimization recommendations"""
        # Get funnel analysis
        from src.optimization.onboarding.onboarding_analyzer import OnboardingAnalyzer
        analyzer = OnboardingAnalyzer(self.metrics, self.events, self.postgres)
        
        funnel = await analyzer.analyze_onboarding_funnel(tenant_id)
        dropoff_points = await analyzer.identify_dropoff_points(tenant_id)
        
        recommendations = []
        
        # Recommend removing or simplifying high drop-off steps
        for dropoff in dropoff_points[:3]:  # Top 3 drop-off points
            if dropoff["dropoff_rate"] > 30:
                recommendations.append({
                    "type": "remove_step",
                    "step_id": dropoff["step_id"],
                    "step_name": dropoff["step_name"],
                    "reason": f"High drop-off rate: {dropoff['dropoff_rate']:.1f}%",
                    "impact": "high"
                })
        
        # Recommend making optional steps that have low completion
        for step_data in funnel["funnel"]:
            if step_data["completion_rate"] < 50 and step_data["dropoff_rate"] > 20:
                recommendations.append({
                    "type": "make_optional",
                    "step_id": step_data["step_id"],
                    "step_name": step_data["step_name"],
                    "reason": f"Low completion rate: {step_data['completion_rate']:.1f}%",
                    "impact": "medium"
                })
        
        return {
            "current_completion_rate": funnel["overall_completion_rate"],
            "recommendations": recommendations,
            "estimated_improvement": len(recommendations) * 5  # Estimate 5% improvement per recommendation
        }
    
    async def update_onboarding_step(
        self,
        tenant_id: str,
        step_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update onboarding step configuration"""
        set_clauses = []
        params = []
        param_index = 1
        
        allowed_updates = ["step_name", "required", "completion_criteria", "enabled"]
        
        for key, value in updates.items():
            if key in allowed_updates:
                set_clauses.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = NOW()")
        params.append(tenant_id)
        params.append(step_id)
        
        await self.postgres.execute(
            f"""
            UPDATE onboarding_steps
            SET {', '.join(set_clauses)}
            WHERE tenant_id = ${param_index} AND step_id = ${param_index + 1}
            """,
            *params
        )
        
        return True

"""
Churn Prevention

Automated interventions to prevent churn.
"""

import logging
from typing import Dict, List, Optional, Any

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class ChurnPrevention:
    """
    Churn Prevention
    
    Applies automated interventions to prevent churn.
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
    
    async def apply_intervention(
        self,
        tenant_id: str,
        user_id: str,
        intervention_type: str,
        churn_probability: float
    ) -> bool:
        """
        Apply churn prevention intervention
        
        Intervention types:
        - email_outreach: Send personalized email
        - discount_offer: Offer discount
        - feature_highlight: Highlight unused features
        - support_reachout: Proactive support contact
        """
        # Record intervention
        await self.postgres.execute(
            """
            UPDATE churn_events
            SET intervention_applied = TRUE, intervention_type = $1
            WHERE tenant_id = $2 AND user_id = $3
            """,
            intervention_type, tenant_id, user_id
        )
        
        # Log event
        await self.events.log_event(
            event_type="churn_intervention_applied",
            user_id=user_id,
            properties={
                "tenant_id": tenant_id,
                "intervention_type": intervention_type,
                "churn_probability": churn_probability
            }
        )
        
        # In production, trigger actual intervention (send email, etc.)
        logger.info(f"Applied {intervention_type} intervention for user {user_id}")
        
        return True
    
    async def get_intervention_recommendation(
        self,
        tenant_id: str,
        user_id: str,
        churn_probability: float
    ) -> str:
        """Get recommended intervention based on churn probability and user profile"""
        # Get user profile
        user = await self.postgres.fetchrow(
            """
            SELECT subscription_tier, created_at, last_login
            FROM users
            WHERE tenant_id = $1 AND user_id = $2
            """,
            tenant_id, user_id
        )
        
        if not user:
            return "none"
        
        # Determine intervention based on probability and tier
        if churn_probability >= 0.8:
            if user["subscription_tier"] == "free":
                return "feature_highlight"
            else:
                return "support_reachout"
        elif churn_probability >= 0.6:
            return "email_outreach"
        elif churn_probability >= 0.4:
            return "feature_highlight"
        else:
            return "none"

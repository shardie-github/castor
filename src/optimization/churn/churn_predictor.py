"""
Churn Predictor

Uses ML to predict user churn probability.
"""

import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class ChurnPredictor:
    """
    Churn Predictor
    
    Predicts user churn using ML models and behavioral signals.
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
    
    async def predict_churn_probability(
        self,
        tenant_id: str,
        user_id: str
    ) -> float:
        """
        Predict churn probability for user
        
        Returns:
            Churn probability (0.0 to 1.0)
        """
        # Get user features
        features = await self._get_user_features(tenant_id, user_id)
        
        # Calculate churn score (simplified ML model)
        # In production, use trained ML model
        churn_score = self._calculate_churn_score(features)
        
        # Store prediction
        await self.postgres.execute(
            """
            INSERT INTO churn_events (
                churn_id, tenant_id, user_id, churn_type, churn_date,
                predicted_probability, predicted_at
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
            ON CONFLICT DO NOTHING
            """,
            tenant_id, user_id, "inactive", date.today(), churn_score
        )
        
        return churn_score
    
    async def identify_at_risk_users(
        self,
        tenant_id: str,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Identify users at risk of churning"""
        # Get all active users
        users = await self.postgres.fetch(
            """
            SELECT user_id, email, subscription_tier, last_login, created_at
            FROM users
            WHERE tenant_id = $1 AND is_active = TRUE
            """,
            tenant_id
        )
        
        at_risk_users = []
        
        for user_row in users:
            user_id = str(user_row["user_id"])
            probability = await self.predict_churn_probability(tenant_id, user_id)
            
            if probability >= threshold:
                at_risk_users.append({
                    "user_id": user_id,
                    "email": user_row["email"],
                    "churn_probability": probability,
                    "subscription_tier": user_row["subscription_tier"],
                    "last_login": user_row["last_login"].isoformat() if user_row["last_login"] else None
                })
        
        return at_risk_users
    
    async def _get_user_features(
        self,
        tenant_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user features for churn prediction"""
        # Get user data
        user = await self.postgres.fetchrow(
            """
            SELECT user_id, created_at, last_login, subscription_tier
            FROM users
            WHERE tenant_id = $1 AND user_id = $2
            """,
            tenant_id, user_id
        )
        
        if not user:
            return {}
        
        # Calculate features
        days_since_signup = (datetime.now(timezone.utc) - user["created_at"]).days
        days_since_login = None
        if user["last_login"]:
            days_since_login = (datetime.now(timezone.utc) - user["last_login"]).days
        
        # Get usage metrics
        campaigns_count = await self.postgres.fetchval(
            """
            SELECT COUNT(*)
            FROM campaigns
            WHERE tenant_id = $1 AND user_id = $2
            """,
            tenant_id, user_id
        ) or 0
        
        # Get recent activity
        recent_activity = await self.postgres.fetchval(
            """
            SELECT COUNT(*)
            FROM audit_logs
            WHERE tenant_id = $1 AND user_id = $2
            AND created_at > NOW() - INTERVAL '30 days'
            """,
            tenant_id, user_id
        ) or 0
        
        return {
            "days_since_signup": days_since_signup,
            "days_since_login": days_since_login or 999,
            "subscription_tier": user["subscription_tier"],
            "campaigns_count": campaigns_count,
            "recent_activity": recent_activity
        }
    
    def _calculate_churn_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate churn score from features
        
        Simplified model - in production, use trained ML model
        """
        score = 0.0
        
        # Days since login (higher = more likely to churn)
        days_since_login = features.get("days_since_login", 0)
        if days_since_login > 30:
            score += 0.3
        if days_since_login > 60:
            score += 0.3
        if days_since_login > 90:
            score += 0.2
        
        # Low activity
        recent_activity = features.get("recent_activity", 0)
        if recent_activity == 0:
            score += 0.2
        
        # No campaigns created
        campaigns_count = features.get("campaigns_count", 0)
        if campaigns_count == 0:
            score += 0.1
        
        # Free tier (more likely to churn)
        if features.get("subscription_tier") == "free":
            score += 0.1
        
        return min(score, 1.0)

"""
Monetization & Pricing Module

Handles tiered pricing, conversion logic, and upsell triggers.
Links pricing events to product use and segment signals.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import SubscriptionTier, User

logger = logging.getLogger(__name__)


class ConversionTrigger(Enum):
    """Conversion trigger types"""
    VALUE_REALIZATION = "value_realization"
    ENGAGEMENT = "engagement"
    FEATURE_LIMITATION = "feature_limitation"
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based"


@dataclass
class TierLimits:
    """Tier feature limits"""
    podcasts: int
    campaigns_per_month: int
    reports_per_month: int
    api_calls_per_month: int
    historical_data_days: int
    team_members: int


TIER_LIMITS = {
    SubscriptionTier.FREE: TierLimits(
        podcasts=1,
        campaigns_per_month=1,
        reports_per_month=3,
        api_calls_per_month=0,
        historical_data_days=30,
        team_members=1
    ),
    SubscriptionTier.STARTER: TierLimits(
        podcasts=3,
        campaigns_per_month=-1,  # Unlimited
        reports_per_month=-1,
        api_calls_per_month=0,
        historical_data_days=90,
        team_members=1
    ),
    SubscriptionTier.PROFESSIONAL: TierLimits(
        podcasts=10,
        campaigns_per_month=-1,
        reports_per_month=-1,
        api_calls_per_month=10000,
        historical_data_days=365,
        team_members=5
    ),
    SubscriptionTier.ENTERPRISE: TierLimits(
        podcasts=-1,  # Unlimited
        campaigns_per_month=-1,
        reports_per_month=-1,
        api_calls_per_month=-1,
        historical_data_days=-1,
        team_members=-1
    )
}


class PricingManager:
    """
    Pricing Manager
    
    Manages pricing tiers, conversion logic, and upsell triggers.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        
    def get_tier_limits(self, tier: SubscriptionTier) -> TierLimits:
        """Get limits for a subscription tier"""
        return TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    def check_limit(
        self,
        user: User,
        resource_type: str,
        current_usage: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has reached tier limit
        
        Returns:
            (within_limit, limit_message)
        """
        limits = self.get_tier_limits(user.subscription_tier)
        
        limit_map = {
            "podcasts": limits.podcasts,
            "campaigns": limits.campaigns_per_month,
            "reports": limits.reports_per_month,
            "api_calls": limits.api_calls_per_month,
            "team_members": limits.team_members
        }
        
        limit = limit_map.get(resource_type)
        if limit is None:
            return True, None
        
        # -1 means unlimited
        if limit == -1:
            return True, None
        
        if current_usage >= limit:
            message = f"You've reached your {user.subscription_tier.value} tier limit of {limit} {resource_type}. Upgrade to continue."
            return False, message
        
        return True, None
    
    async def check_freemium_conversion(
        self,
        user_id: str,
        usage_metrics: Dict[str, Any]
    ) -> Optional[ConversionTrigger]:
        """
        Check if free user should be converted to paid
        
        Returns:
            ConversionTrigger if conversion should happen, None otherwise
        """
        signals = {
            "reports_generated": usage_metrics.get("reports_generated", 0),
            "campaigns_created": usage_metrics.get("campaigns_created", 0),
            "dashboard_views": usage_metrics.get("dashboard_views", 0),
            "data_exports": usage_metrics.get("data_exports", 0),
            "days_active": usage_metrics.get("days_active", 0),
            "renewal_rate": usage_metrics.get("renewal_rate", 0)
        }
        
        # Calculate conversion score
        conversion_score = (
            (signals["reports_generated"] >= 3) * 20 +
            (signals["campaigns_created"] >= 2) * 20 +
            (signals["dashboard_views"] >= 10) * 15 +
            (signals["data_exports"] >= 5) * 15 +
            (signals["days_active"] >= 7) * 10 +
            (signals["renewal_rate"] > 0.5) * 20
        )
        
        if conversion_score >= 50:
            # Determine trigger type
            if signals["reports_generated"] >= 3:
                trigger = ConversionTrigger.VALUE_REALIZATION
            elif signals["dashboard_views"] >= 10:
                trigger = ConversionTrigger.ENGAGEMENT
            elif signals["days_active"] >= 7:
                trigger = ConversionTrigger.TIME_BASED
            else:
                trigger = ConversionTrigger.USAGE_BASED
            
            # Log conversion event
            await self.events.log_event(
                event_type="conversion_triggered",
                user_id=user_id,
                properties={
                    "trigger": trigger.value,
                    "conversion_score": conversion_score,
                    "signals": signals
                }
            )
            
            return trigger
        
        return None
    
    async def check_upsell_opportunity(
        self,
        user: User,
        usage_metrics: Dict[str, Any]
    ) -> Optional[SubscriptionTier]:
        """
        Check if user should be upsold to higher tier
        
        Returns:
            Recommended tier if upsell opportunity exists, None otherwise
        """
        current_tier = user.subscription_tier
        
        # Check for upsell signals
        if current_tier == SubscriptionTier.FREE:
            # Check conversion to Starter
            if await self.check_freemium_conversion(user.user_id, usage_metrics):
                return SubscriptionTier.STARTER
        
        elif current_tier == SubscriptionTier.STARTER:
            # Check upsell to Professional
            if (
                usage_metrics.get("active_campaigns", 0) >= 5 or
                usage_metrics.get("monthly_reports", 0) >= 10 or
                usage_metrics.get("api_access_requested", False) or
                usage_metrics.get("podcasts_count", 0) >= 4
            ):
                return SubscriptionTier.PROFESSIONAL
        
        elif current_tier == SubscriptionTier.PROFESSIONAL:
            # Check upsell to Enterprise
            if (
                usage_metrics.get("active_campaigns", 0) >= 15 or
                usage_metrics.get("podcasts_count", 0) >= 10 or
                usage_metrics.get("team_collaboration_requested", False) or
                usage_metrics.get("custom_integrations_requested", False)
            ):
                return SubscriptionTier.ENTERPRISE
        
        return None
    
    async def log_pricing_event(
        self,
        user_id: str,
        event_type: str,
        properties: Dict[str, Any]
    ):
        """Log pricing-related event"""
        await self.events.log_event(
            event_type=f"pricing_{event_type}",
            user_id=user_id,
            properties=properties
        )
        
        # Record metrics
        self.metrics.increment_counter(
            f"pricing_event_{event_type}",
            tags={"user_id": user_id}
        )
    
    async def track_feature_usage(
        self,
        user: User,
        feature: str,
        usage_count: int
    ):
        """Track feature usage for pricing analysis"""
        limits = self.get_tier_limits(user.subscription_tier)
        
        # Check if feature is limited
        feature_limits = {
            "reports": limits.reports_per_month,
            "campaigns": limits.campaigns_per_month,
            "api_calls": limits.api_calls_per_month
        }
        
        limit = feature_limits.get(feature)
        if limit and limit != -1 and usage_count >= limit * 0.8:  # 80% of limit
            # Trigger upsell notification
            await self.events.log_event(
                event_type="usage_limit_approaching",
                user_id=user.user_id,
                properties={
                    "feature": feature,
                    "usage_count": usage_count,
                    "limit": limit,
                    "subscription_tier": user.subscription_tier.value
                }
            )

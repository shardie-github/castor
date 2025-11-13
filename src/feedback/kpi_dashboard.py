"""
KPI Dashboard Aggregator

Aggregates KPIs for:
- Business success (conversion, LTV/CAC, retention, upsell, expansion by persona)
- Operational ease (support case frequency, automation coverage, infra cost/user)
- User success (task completion rate, NPS, feature re-use)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.measurement.continuous_metrics import ContinuousMeasurement
from src.monetization.pricing import PricingManager
from src.users.user_manager import UserManager

logger = logging.getLogger(__name__)


class KPICategory(Enum):
    """KPI categories"""
    BUSINESS_SUCCESS = "business_success"
    OPERATIONAL_EASE = "operational_ease"
    USER_SUCCESS = "user_success"


@dataclass
class BusinessSuccessKPIs:
    """Business success KPIs"""
    conversion_rate: float  # Free to paid conversion
    ltv_cac_ratio: float  # Lifetime value to customer acquisition cost
    retention_rate: float  # Monthly/annual retention
    upsell_rate: float  # Tier upgrade rate
    expansion_rate: float  # Revenue expansion within tier
    by_persona: Dict[str, Dict[str, float]]  # Metrics broken down by persona


@dataclass
class OperationalEaseKPIs:
    """Operational ease KPIs"""
    support_case_frequency: float  # Cases per user per month
    automation_coverage: float  # % of tasks automated
    infra_cost_per_user: float  # Infrastructure cost per user
    support_resolution_time_hours: float  # Average resolution time
    by_persona: Dict[str, Dict[str, float]]  # Metrics broken down by persona


@dataclass
class UserSuccessKPIs:
    """User success KPIs"""
    task_completion_rate: float  # % of tasks completed successfully
    nps_score: float  # Net Promoter Score
    feature_reuse_rate: float  # % of features used more than once
    time_to_value_minutes: float  # Average time to first value
    by_persona: Dict[str, Dict[str, float]]  # Metrics broken down by persona


@dataclass
class KPIDashboard:
    """Complete KPI dashboard"""
    timestamp: datetime
    business_success: BusinessSuccessKPIs
    operational_ease: OperationalEaseKPIs
    user_success: UserSuccessKPIs
    period_days: int


class KPIDashboardAggregator:
    """
    KPI Dashboard Aggregator
    
    Aggregates KPIs across business success, operational ease, and user success.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        measurement: ContinuousMeasurement,
        pricing_manager: PricingManager,
        user_manager: UserManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.measurement = measurement
        self.pricing = pricing_manager
        self.users = user_manager
        
        # Placeholder for infrastructure costs (would come from cloud provider)
        self._infra_cost_per_month = 1000.0  # $1000/month baseline
        
    async def generate_dashboard(
        self,
        days: int = 30,
        persona_segment: Optional[str] = None
    ) -> KPIDashboard:
        """Generate complete KPI dashboard"""
        
        business_success = await self._calculate_business_success_kpis(days, persona_segment)
        operational_ease = await self._calculate_operational_ease_kpis(days, persona_segment)
        user_success = await self._calculate_user_success_kpis(days, persona_segment)
        
        dashboard = KPIDashboard(
            timestamp=datetime.now(timezone.utc),
            business_success=business_success,
            operational_ease=operational_ease,
            user_success=user_success,
            period_days=days
        )
        
        return dashboard
    
    async def _calculate_business_success_kpis(
        self,
        days: int,
        persona_segment: Optional[str]
    ) -> BusinessSuccessKPIs:
        """Calculate business success KPIs"""
        
        # Get all users
        # In production, this would query the database
        # For now, we'll use placeholder logic
        
        # Conversion rate (free to paid)
        conversion_rate = 0.15  # 15% placeholder
        conversion_by_persona = {
            "solo_podcaster": 0.12,
            "producer": 0.25,
            "agency": 0.30,
            "brand": 0.20
        }
        
        # LTV/CAC ratio
        ltv_cac_ratio = 3.5  # 3.5:1 placeholder
        ltv_cac_by_persona = {
            "solo_podcaster": 2.8,
            "producer": 4.2,
            "agency": 5.0,
            "brand": 3.5
        }
        
        # Retention rate
        retention_rate = 0.85  # 85% monthly retention
        retention_by_persona = {
            "solo_podcaster": 0.80,
            "producer": 0.90,
            "agency": 0.92,
            "brand": 0.88
        }
        
        # Upsell rate (tier upgrades)
        upsell_rate = 0.10  # 10% upgrade rate
        upsell_by_persona = {
            "solo_podcaster": 0.08,
            "producer": 0.15,
            "agency": 0.18,
            "brand": 0.12
        }
        
        # Expansion rate (revenue growth within tier)
        expansion_rate = 0.20  # 20% expansion
        expansion_by_persona = {
            "solo_podcaster": 0.15,
            "producer": 0.25,
            "agency": 0.30,
            "brand": 0.22
        }
        
        by_persona = {}
        for persona in ["solo_podcaster", "producer", "agency", "brand"]:
            by_persona[persona] = {
                "conversion_rate": conversion_by_persona.get(persona, 0.0),
                "ltv_cac_ratio": ltv_cac_by_persona.get(persona, 0.0),
                "retention_rate": retention_by_persona.get(persona, 0.0),
                "upsell_rate": upsell_by_persona.get(persona, 0.0),
                "expansion_rate": expansion_by_persona.get(persona, 0.0)
            }
        
        return BusinessSuccessKPIs(
            conversion_rate=conversion_rate,
            ltv_cac_ratio=ltv_cac_ratio,
            retention_rate=retention_rate,
            upsell_rate=upsell_rate,
            expansion_rate=expansion_rate,
            by_persona=by_persona
        )
    
    async def _calculate_operational_ease_kpis(
        self,
        days: int,
        persona_segment: Optional[str]
    ) -> OperationalEaseKPIs:
        """Calculate operational ease KPIs"""
        
        # Support case frequency (cases per user per month)
        # In production, would query support system
        support_case_frequency = 0.15  # 0.15 cases per user per month
        support_by_persona = {
            "solo_podcaster": 0.20,
            "producer": 0.12,
            "agency": 0.10,
            "brand": 0.18
        }
        
        # Automation coverage (% of tasks automated)
        automation_coverage = 0.65  # 65% automated
        automation_by_persona = {
            "solo_podcaster": 0.60,
            "producer": 0.70,
            "agency": 0.75,
            "brand": 0.65
        }
        
        # Infrastructure cost per user
        # In production, would calculate from actual infra costs
        total_users = 1000  # Placeholder
        infra_cost_per_user = self._infra_cost_per_month / total_users if total_users > 0 else 0.0
        
        # Support resolution time (hours)
        support_resolution_time_hours = 4.5  # 4.5 hours average
        resolution_by_persona = {
            "solo_podcaster": 5.0,
            "producer": 3.5,
            "agency": 3.0,
            "brand": 4.8
        }
        
        by_persona = {}
        for persona in ["solo_podcaster", "producer", "agency", "brand"]:
            by_persona[persona] = {
                "support_case_frequency": support_by_persona.get(persona, 0.0),
                "automation_coverage": automation_by_persona.get(persona, 0.0),
                "infra_cost_per_user": infra_cost_per_user,
                "support_resolution_time_hours": resolution_by_persona.get(persona, 0.0)
            }
        
        return OperationalEaseKPIs(
            support_case_frequency=support_case_frequency,
            automation_coverage=automation_coverage,
            infra_cost_per_user=infra_cost_per_user,
            support_resolution_time_hours=support_resolution_time_hours,
            by_persona=by_persona
        )
    
    async def _calculate_user_success_kpis(
        self,
        days: int,
        persona_segment: Optional[str]
    ) -> UserSuccessKPIs:
        """Calculate user success KPIs"""
        
        # Task completion rate
        task_stats = self.measurement.get_task_statistics(days=days)
        task_completion_rate = task_stats.get("success_rate", 0.0)
        
        # NPS score
        nps_score = await self.measurement.calculate_nps(days=days)
        
        # Feature reuse rate (would need to track feature usage)
        feature_reuse_rate = 0.70  # 70% reuse rate placeholder
        
        # Time to value
        # Would integrate with metrics tracker
        time_to_value_minutes = 25.0  # 25 minutes placeholder
        
        # By persona breakdowns
        by_persona = {}
        for persona in ["solo_podcaster", "producer", "agency", "brand"]:
            # In production, would calculate these per persona
            by_persona[persona] = {
                "task_completion_rate": task_completion_rate * (0.9 if persona == "solo_podcaster" else 1.0),
                "nps_score": nps_score + (10 if persona == "agency" else 0),
                "feature_reuse_rate": feature_reuse_rate * (0.95 if persona == "producer" else 1.0),
                "time_to_value_minutes": time_to_value_minutes * (1.2 if persona == "solo_podcaster" else 1.0)
            }
        
        return UserSuccessKPIs(
            task_completion_rate=task_completion_rate,
            nps_score=nps_score,
            feature_reuse_rate=feature_reuse_rate,
            time_to_value_minutes=time_to_value_minutes,
            by_persona=by_persona
        )
    
    async def get_kpi_trends(
        self,
        kpi_name: str,
        days: int = 90,
        persona_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get KPI trends over time"""
        # In production, would query historical data
        # For now, return placeholder trend data
        
        return {
            "kpi_name": kpi_name,
            "trend": "increasing",  # increasing, decreasing, stable
            "change_percentage": 5.2,
            "period_days": days,
            "data_points": []
        }
    
    async def compare_personas(
        self,
        kpi_category: KPICategory,
        days: int = 30
    ) -> Dict[str, Any]:
        """Compare KPIs across personas"""
        dashboard = await self.generate_dashboard(days=days)
        
        if kpi_category == KPICategory.BUSINESS_SUCCESS:
            return {
                "category": "business_success",
                "by_persona": dashboard.business_success.by_persona,
                "overall": {
                    "conversion_rate": dashboard.business_success.conversion_rate,
                    "ltv_cac_ratio": dashboard.business_success.ltv_cac_ratio,
                    "retention_rate": dashboard.business_success.retention_rate,
                    "upsell_rate": dashboard.business_success.upsell_rate,
                    "expansion_rate": dashboard.business_success.expansion_rate
                }
            }
        elif kpi_category == KPICategory.OPERATIONAL_EASE:
            return {
                "category": "operational_ease",
                "by_persona": dashboard.operational_ease.by_persona,
                "overall": {
                    "support_case_frequency": dashboard.operational_ease.support_case_frequency,
                    "automation_coverage": dashboard.operational_ease.automation_coverage,
                    "infra_cost_per_user": dashboard.operational_ease.infra_cost_per_user,
                    "support_resolution_time_hours": dashboard.operational_ease.support_resolution_time_hours
                }
            }
        else:  # USER_SUCCESS
            return {
                "category": "user_success",
                "by_persona": dashboard.user_success.by_persona,
                "overall": {
                    "task_completion_rate": dashboard.user_success.task_completion_rate,
                    "nps_score": dashboard.user_success.nps_score,
                    "feature_reuse_rate": dashboard.user_success.feature_reuse_rate,
                    "time_to_value_minutes": dashboard.user_success.time_to_value_minutes
                }
            }

"""
Longitudinal Health/ROI Studies Module

Tracks and analyzes:
- Sponsor deal renewal rates
- User revenue growth
- Campaign efficiency
- Real-world impact for all personas
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import UserManager
from src.campaigns.campaign_manager import CampaignManager, Campaign, CampaignStatus
from src.analytics.analytics_store import AnalyticsStore, CampaignPerformance
from src.feedback.kpi_dashboard import KPIDashboardAggregator

logger = logging.getLogger(__name__)


class StudyType(Enum):
    """Study types"""
    RENEWAL_RATE = "renewal_rate"
    REVENUE_GROWTH = "revenue_growth"
    CAMPAIGN_EFFICIENCY = "campaign_efficiency"
    PERSONA_IMPACT = "persona_impact"
    LONGITUDINAL_HEALTH = "longitudinal_health"


@dataclass
class RenewalStudy:
    """Sponsor deal renewal rate study"""
    study_id: str
    period_start: datetime
    period_end: datetime
    total_campaigns: int
    renewed_campaigns: int
    renewal_rate: float
    by_persona: Dict[str, Dict[str, float]] = field(default_factory=dict)
    by_sponsor: Dict[str, Dict[str, float]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RevenueGrowthStudy:
    """User revenue growth study"""
    study_id: str
    period_start: datetime
    period_end: datetime
    baseline_revenue: float
    current_revenue: float
    growth_rate: float
    by_persona: Dict[str, Dict[str, float]] = field(default_factory=dict)
    by_tier: Dict[str, Dict[str, float]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CampaignEfficiencyStudy:
    """Campaign efficiency study"""
    study_id: str
    period_start: datetime
    period_end: datetime
    total_campaigns: int
    avg_roi: float
    avg_roas: float
    avg_conversion_rate: float
    by_persona: Dict[str, Dict[str, float]] = field(default_factory=dict)
    by_campaign_type: Dict[str, Dict[str, float]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LongitudinalHealthStudies:
    """
    Longitudinal Health/ROI Studies
    
    Conducts longitudinal studies to measure real-world impact across all personas.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        campaign_manager: CampaignManager,
        analytics_store: AnalyticsStore,
        kpi_dashboard: KPIDashboardAggregator
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.campaigns = campaign_manager
        self.analytics = analytics_store
        self.kpi_dashboard = kpi_dashboard
        self._studies: Dict[str, Any] = {}
        
    async def conduct_renewal_rate_study(
        self,
        period_start: datetime,
        period_end: datetime,
        persona_segment: Optional[str] = None
    ) -> RenewalStudy:
        """
        Conduct sponsor deal renewal rate study
        
        Args:
            period_start: Study period start
            period_end: Study period end
            persona_segment: Optional persona filter
            
        Returns:
            RenewalStudy results
        """
        study_id = str(uuid4())
        
        # Get all campaigns that ended in the period
        all_campaigns = await self.campaigns.list_campaigns(status=CampaignStatus.COMPLETED)
        
        # Filter by period
        period_campaigns = [
            c for c in all_campaigns
            if period_start <= c.end_date <= period_end
        ]
        
        # Check for renewals (campaigns with same sponsor that started after end date)
        renewed_campaigns = []
        renewal_by_sponsor: Dict[str, int] = {}
        
        for campaign in period_campaigns:
            # Check if sponsor created new campaign after this one ended
            future_campaigns = await self.campaigns.list_campaigns(
                sponsor_id=campaign.sponsor_id,
                status=CampaignStatus.ACTIVE
            )
            
            # Check if any future campaign started within 90 days of end date
            renewal_window = campaign.end_date + timedelta(days=90)
            renewed = any(
                c.start_date <= renewal_window and c.start_date > campaign.end_date
                for c in future_campaigns
            )
            
            if renewed:
                renewed_campaigns.append(campaign)
                renewal_by_sponsor[campaign.sponsor_id] = renewal_by_sponsor.get(campaign.sponsor_id, 0) + 1
        
        total_campaigns = len(period_campaigns)
        renewed_count = len(renewed_campaigns)
        renewal_rate = renewed_count / total_campaigns if total_campaigns > 0 else 0.0
        
        # Calculate by persona
        by_persona = {}
        if persona_segment:
            # Filter campaigns by persona
            persona_campaigns = [
                c for c in period_campaigns
                # In production, would check user persona
            ]
            persona_renewed = len([c for c in persona_campaigns if c in renewed_campaigns])
            by_persona[persona_segment] = {
                "total": len(persona_campaigns),
                "renewed": persona_renewed,
                "renewal_rate": persona_renewed / len(persona_campaigns) if persona_campaigns else 0.0
            }
        
        study = RenewalStudy(
            study_id=study_id,
            period_start=period_start,
            period_end=period_end,
            total_campaigns=total_campaigns,
            renewed_campaigns=renewed_count,
            renewal_rate=renewal_rate,
            by_persona=by_persona,
            by_sponsor={
                sponsor_id: {
                    "renewed": count,
                    "total": sum(1 for c in period_campaigns if c.sponsor_id == sponsor_id)
                }
                for sponsor_id, count in renewal_by_sponsor.items()
            }
        )
        
        self._studies[study_id] = study
        
        # Record metrics
        self.metrics.record_gauge(
            "sponsor_renewal_rate",
            renewal_rate,
            tags={"period_days": (period_end - period_start).days}
        )
        
        await self.events.log_event(
            event_type="renewal_rate_study_completed",
            user_id=None,
            properties={
                "study_id": study_id,
                "renewal_rate": renewal_rate,
                "total_campaigns": total_campaigns,
                "renewed_campaigns": renewed_count
            }
        )
        
        return study
    
    async def conduct_revenue_growth_study(
        self,
        period_start: datetime,
        period_end: datetime,
        persona_segment: Optional[str] = None
    ) -> RevenueGrowthStudy:
        """
        Conduct user revenue growth study
        
        Args:
            period_start: Study period start
            period_end: Study period end
            persona_segment: Optional persona filter
            
        Returns:
            RevenueGrowthStudy results
        """
        study_id = str(uuid4())
        
        # Calculate baseline revenue (from period_start)
        baseline_campaigns = await self.campaigns.list_campaigns()
        baseline_revenue = sum(
            c.campaign_value for c in baseline_campaigns
            if c.start_date < period_start and c.status == CampaignStatus.COMPLETED
        )
        
        # Calculate current revenue (from period_end)
        current_campaigns = await self.campaigns.list_campaigns()
        current_revenue = sum(
            c.campaign_value for c in current_campaigns
            if c.start_date <= period_end and c.status == CampaignStatus.COMPLETED
        )
        
        growth_rate = (
            (current_revenue - baseline_revenue) / baseline_revenue
            if baseline_revenue > 0 else 0.0
        )
        
        # Calculate by persona
        by_persona = {}
        # In production, would group by user persona
        
        # Calculate by tier
        by_tier = {}
        # In production, would group by subscription tier
        
        study = RevenueGrowthStudy(
            study_id=study_id,
            period_start=period_start,
            period_end=period_end,
            baseline_revenue=baseline_revenue,
            current_revenue=current_revenue,
            growth_rate=growth_rate,
            by_persona=by_persona,
            by_tier=by_tier
        )
        
        self._studies[study_id] = study
        
        # Record metrics
        self.metrics.record_gauge(
            "revenue_growth_rate",
            growth_rate,
            tags={"period_days": (period_end - period_start).days}
        )
        
        await self.events.log_event(
            event_type="revenue_growth_study_completed",
            user_id=None,
            properties={
                "study_id": study_id,
                "growth_rate": growth_rate,
                "baseline_revenue": baseline_revenue,
                "current_revenue": current_revenue
            }
        )
        
        return study
    
    async def conduct_campaign_efficiency_study(
        self,
        period_start: datetime,
        period_end: datetime,
        persona_segment: Optional[str] = None
    ) -> CampaignEfficiencyStudy:
        """
        Conduct campaign efficiency study
        
        Args:
            period_start: Study period start
            period_end: Study period end
            persona_segment: Optional persona filter
            
        Returns:
            CampaignEfficiencyStudy results
        """
        study_id = str(uuid4())
        
        # Get campaigns in period
        all_campaigns = await self.campaigns.list_campaigns()
        period_campaigns = [
            c for c in all_campaigns
            if period_start <= c.start_date <= period_end
        ]
        
        # Calculate performance metrics for each campaign
        roi_values = []
        roas_values = []
        conversion_rates = []
        
        for campaign in period_campaigns:
            try:
                performance = await self.analytics.calculate_campaign_performance(
                    campaign.campaign_id,
                    campaign.podcast_id,
                    campaign.start_date,
                    campaign.end_date
                )
                
                if performance.roi is not None:
                    roi_values.append(performance.roi)
                if performance.roas is not None:
                    roas_values.append(performance.roas)
                if performance.attribution_events > 0:
                    conversion_rate = performance.conversions / performance.attribution_events
                    conversion_rates.append(conversion_rate)
                    
            except Exception as e:
                logger.warning(f"Error calculating performance for campaign {campaign.campaign_id}: {e}")
        
        avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
        avg_roas = sum(roas_values) / len(roas_values) if roas_values else 0.0
        avg_conversion_rate = sum(conversion_rates) / len(conversion_rates) if conversion_rates else 0.0
        
        # Calculate by persona
        by_persona = {}
        # In production, would group by user persona
        
        # Calculate by campaign type
        by_campaign_type = {}
        # In production, would group by campaign attributes
        
        study = CampaignEfficiencyStudy(
            study_id=study_id,
            period_start=period_start,
            period_end=period_end,
            total_campaigns=len(period_campaigns),
            avg_roi=avg_roi,
            avg_roas=avg_roas,
            avg_conversion_rate=avg_conversion_rate,
            by_persona=by_persona,
            by_campaign_type=by_campaign_type
        )
        
        self._studies[study_id] = study
        
        # Record metrics
        self.metrics.record_gauge(
            "campaign_avg_roi",
            avg_roi,
            tags={"period_days": (period_end - period_start).days}
        )
        
        self.metrics.record_gauge(
            "campaign_avg_roas",
            avg_roas,
            tags={"period_days": (period_end - period_start).days}
        )
        
        await self.events.log_event(
            event_type="campaign_efficiency_study_completed",
            user_id=None,
            properties={
                "study_id": study_id,
                "avg_roi": avg_roi,
                "avg_roas": avg_roas,
                "avg_conversion_rate": avg_conversion_rate,
                "total_campaigns": len(period_campaigns)
            }
        )
        
        return study
    
    async def conduct_persona_impact_study(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive persona impact study
        
        Measures real-world impact for all personas.
        
        Returns:
            Dictionary with impact metrics by persona
        """
        personas = ["solo_podcaster", "producer", "agency", "brand"]
        
        impact_by_persona = {}
        
        for persona in personas:
            # Get KPI dashboard for persona
            dashboard = await self.kpi_dashboard.generate_dashboard(
                days=(period_end - period_start).days,
                persona_segment=persona
            )
            
            # Conduct renewal study
            renewal_study = await self.conduct_renewal_rate_study(
                period_start,
                period_end,
                persona_segment=persona
            )
            
            # Conduct revenue growth study
            revenue_study = await self.conduct_revenue_growth_study(
                period_start,
                period_end,
                persona_segment=persona
            )
            
            # Conduct efficiency study
            efficiency_study = await self.conduct_campaign_efficiency_study(
                period_start,
                period_end,
                persona_segment=persona
            )
            
            impact_by_persona[persona] = {
                "business_success": {
                    "conversion_rate": dashboard.business_success.conversion_rate,
                    "ltv_cac_ratio": dashboard.business_success.ltv_cac_ratio,
                    "retention_rate": dashboard.business_success.retention_rate,
                    "renewal_rate": renewal_study.renewal_rate,
                    "revenue_growth": revenue_study.growth_rate
                },
                "operational_ease": {
                    "support_case_frequency": dashboard.operational_ease.support_case_frequency,
                    "automation_coverage": dashboard.operational_ease.automation_coverage,
                    "support_resolution_time": dashboard.operational_ease.support_resolution_time_hours
                },
                "user_success": {
                    "task_completion_rate": dashboard.user_success.task_completion_rate,
                    "nps_score": dashboard.user_success.nps_score,
                    "time_to_value": dashboard.user_success.time_to_value_minutes
                },
                "campaign_efficiency": {
                    "avg_roi": efficiency_study.avg_roi,
                    "avg_roas": efficiency_study.avg_roas,
                    "avg_conversion_rate": efficiency_study.avg_conversion_rate
                }
            }
        
        await self.events.log_event(
            event_type="persona_impact_study_completed",
            user_id=None,
            properties={
                "personas": personas,
                "impact_by_persona": impact_by_persona
            }
        )
        
        return impact_by_persona
    
    async def get_study(self, study_id: str) -> Optional[Any]:
        """Get study by ID"""
        return self._studies.get(study_id)
    
    async def schedule_longitudinal_studies(
        self,
        study_types: List[StudyType],
        frequency_days: int = 30
    ):
        """
        Schedule recurring longitudinal studies
        
        Args:
            study_types: Types of studies to conduct
            frequency_days: How often to run studies (in days)
        """
        # In production, would use a task scheduler (Celery, etc.)
        # For now, just log the schedule
        
        logger.info(
            f"Scheduled longitudinal studies: {[s.value for s in study_types]} "
            f"every {frequency_days} days"
        )
        
        await self.events.log_event(
            event_type="longitudinal_studies_scheduled",
            user_id=None,
            properties={
                "study_types": [s.value for s in study_types],
                "frequency_days": frequency_days
            }
        )

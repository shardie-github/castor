"""
Feedback Loop Integration

Integrates feedback loops with existing modules:
- Campaigns
- Reporting
- Users
- Analytics
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from src.feedback.journey_surveys import JourneySurveySystem, SurveyTrigger
from src.feedback.metrics_tracker import MetricsTracker, MetricCategory
from src.feedback.kpi_dashboard import KPIDashboardAggregator
from src.feedback.retro_agent import RetroAgent
from src.feedback.ab_testing import ABTestingFramework
from src.feedback.auto_escalation import AutoEscalationSystem
from src.campaigns.campaign_manager import CampaignManager
from src.reporting.report_generator import ReportGenerator
from src.users.user_manager import UserManager
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.measurement.continuous_metrics import ContinuousMeasurement
from src.monetization.pricing import PricingManager

logger = logging.getLogger(__name__)


class FeedbackLoopIntegration:
    """
    Feedback Loop Integration
    
    Integrates feedback systems with existing modules.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        campaign_manager: CampaignManager,
        report_generator: ReportGenerator,
        measurement: ContinuousMeasurement,
        pricing_manager: PricingManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.campaigns = campaign_manager
        self.reports = report_generator
        self.measurement = measurement
        self.pricing = pricing_manager
        
        # Initialize feedback systems
        self.surveys = JourneySurveySystem(metrics_collector, event_logger)
        self.metrics_tracker = MetricsTracker(metrics_collector, event_logger)
        self.kpi_dashboard = KPIDashboardAggregator(
            metrics_collector,
            event_logger,
            measurement,
            pricing_manager,
            user_manager
        )
        self.retro_agent = RetroAgent(
            metrics_collector,
            event_logger,
            self.kpi_dashboard,
            self.metrics_tracker
        )
        self.ab_testing = ABTestingFramework(metrics_collector, event_logger)
        self.auto_escalation = AutoEscalationSystem(
            metrics_collector,
            event_logger,
            self.kpi_dashboard,
            self.metrics_tracker
        )
        
        # Set up event listeners
        self._setup_event_listeners()
        
    def _setup_event_listeners(self):
        """Set up event listeners for automatic feedback triggers"""
        # This would integrate with the event system to automatically trigger
        # surveys, track metrics, etc. when events occur
        pass
    
    async def on_campaign_created(
        self,
        user_id: str,
        campaign_id: str
    ):
        """Handle campaign creation event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        # Track campaign creation time-to-value
        # (would need to track when user started campaign creation)
        
        # Trigger survey if appropriate
        survey = await self.surveys.trigger_survey(
            user=user,
            trigger=SurveyTrigger.FEATURE_COMPLETED,
            context={"feature": "campaign_created"},
            feature="campaign_creation",
            journey_stage="campaign_setup"
        )
        
        if survey:
            logger.info(f"Survey triggered for user {user_id}: {survey.survey_id}")
    
    async def on_report_generated(
        self,
        user_id: str,
        report_id: str,
        campaign_id: str,
        time_to_generate: float
    ):
        """Handle report generation event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        persona_segment = user.persona_segment or "unknown"
        
        # Track time-to-value
        await self.metrics_tracker.track_time_to_value(
            user_id=user_id,
            persona_segment=persona_segment,
            value_type="report_generated",
            time_seconds=time_to_generate,
            feature="report_generation",
            journey_stage="report_delivery"
        )
        
        # Trigger survey
        survey = await self.surveys.trigger_survey(
            user=user,
            trigger=SurveyTrigger.VALUE_DELIVERED,
            context={"value_type": "report_generated"},
            feature="report_generation",
            journey_stage="first_value_delivered"
        )
        
        if survey:
            logger.info(f"Survey triggered for user {user_id}: {survey.survey_id}")
    
    async def on_report_shared(
        self,
        user_id: str,
        report_id: str,
        campaign_id: str
    ):
        """Handle report sharing event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        # Trigger report accuracy survey
        survey = await self.surveys.trigger_survey(
            user=user,
            trigger=SurveyTrigger.FEATURE_COMPLETED,
            context={"feature": "report_shared"},
            feature="report_generation",
            journey_stage="report_delivery"
        )
        
        if survey:
            logger.info(f"Survey triggered for user {user_id}: {survey.survey_id}")
    
    async def on_campaign_completed(
        self,
        user_id: str,
        campaign_id: str
    ):
        """Handle campaign completion event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        # Trigger renewal success survey
        survey = await self.surveys.trigger_survey(
            user=user,
            trigger=SurveyTrigger.JOURNEY_STAGE_COMPLETED,
            context={"journey_stage": "campaign_completed"},
            journey_stage="renewal_discussion",
            feature="renewal_tools"
        )
        
        if survey:
            logger.info(f"Survey triggered for user {user_id}: {survey.survey_id}")
    
    async def on_support_contacted(
        self,
        user_id: str,
        support_type: str,
        issue_category: str
    ):
        """Handle support contact event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        persona_segment = user.persona_segment or "unknown"
        
        # Track support incident
        await self.metrics_tracker.track_support_incident(
            user_id=user_id,
            persona_segment=persona_segment,
            support_type=support_type,
            issue_category=issue_category,
            resolved=False
        )
        
        # Trigger support incident survey
        survey = await self.surveys.trigger_survey(
            user=user,
            trigger=SurveyTrigger.ERROR_ENCOUNTERED,
            context={"error_type": "support_contacted"},
            feature="support",
            journey_stage="support_flow"
        )
        
        if survey:
            logger.info(f"Survey triggered for user {user_id}: {survey.survey_id}")
    
    async def on_renewal_success(
        self,
        user_id: str,
        campaign_id: str,
        renewed: bool,
        rate_increase: Optional[float] = None
    ):
        """Handle renewal success event"""
        user = await self.users.get_user(user_id)
        if not user:
            return
        
        persona_segment = user.persona_segment or "unknown"
        
        # Track renewal success
        await self.metrics_tracker.track_renewal_success(
            user_id=user_id,
            persona_segment=persona_segment,
            campaign_id=campaign_id,
            renewed=renewed,
            rate_increase=rate_increase,
            renewal_tools_used=True  # Would check if tools were actually used
        )
    
    async def run_periodic_checks(self):
        """Run periodic checks for escalations and metrics"""
        # Check for escalations
        escalations = await self.auto_escalation.check_escalations(days=7)
        
        if escalations:
            logger.warning(f"Found {len(escalations)} escalations")
            for escalation in escalations:
                logger.warning(f"Escalation: {escalation.title} - {escalation.description}")
        
        return escalations
    
    async def run_sprint_retro(
        self,
        sprint_id: str,
        sprint_start: datetime,
        sprint_end: datetime
    ):
        """Run sprint retrospective"""
        return await self.retro_agent.run_sprint_retro(
            sprint_id=sprint_id,
            sprint_start=sprint_start,
            sprint_end=sprint_end
        )
    
    async def run_deployment_retro(
        self,
        deployment_id: str,
        deployment_time: datetime
    ):
        """Run deployment retrospective"""
        return await self.retro_agent.run_deployment_retro(
            deployment_id=deployment_id,
            deployment_time=deployment_time
        )
    
    async def get_kpi_dashboard(self, days: int = 30):
        """Get KPI dashboard"""
        return await self.kpi_dashboard.generate_dashboard(days=days)
    
    async def get_metrics_by_persona(
        self,
        metric_category: MetricCategory,
        days: int = 30,
        persona_segment: Optional[str] = None
    ):
        """Get metrics by persona"""
        return await self.metrics_tracker.get_metrics_by_persona(
            metric_category=metric_category,
            persona_segment=persona_segment,
            days=days
        )

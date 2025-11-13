"""
Agent-Driven Retrospective System

Runs retrospective analysis after each sprint/deployment using:
- User journey theory
- Business model canvas
- Behavioral science principles
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.feedback.kpi_dashboard import KPIDashboardAggregator
from src.feedback.metrics_tracker import MetricsTracker

logger = logging.getLogger(__name__)


class RetroAnalysisType(Enum):
    """Retrospective analysis types"""
    SPRINT_RETRO = "sprint_retro"
    DEPLOYMENT_RETRO = "deployment_retro"
    FEATURE_RETRO = "feature_retro"
    MILESTONE_RETRO = "milestone_retro"


class InsightCategory(Enum):
    """Insight categories"""
    JOURNEY_OPTIMIZATION = "journey_optimization"
    BUSINESS_MODEL = "business_model"
    BEHAVIORAL_SCIENCE = "behavioral_science"
    TECHNICAL_DEBT = "technical_debt"
    USER_EXPERIENCE = "user_experience"


@dataclass
class RetroInsight:
    """Retrospective insight"""
    insight_id: str
    category: InsightCategory
    title: str
    description: str
    evidence: List[str]  # Data points supporting the insight
    impact: str  # High, Medium, Low
    recommendations: List[str]
    related_journey_stage: Optional[str] = None
    related_persona: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RetroAnalysis:
    """Retrospective analysis"""
    analysis_id: str
    analysis_type: RetroAnalysisType
    period_start: datetime
    period_end: datetime
    insights: List[RetroInsight]
    what_worked: List[str]
    what_failed: List[str]
    meta_metrics: Dict[str, Any]  # Meta-metrics about the analysis itself
    backlog_items: List[Dict[str, Any]]  # Items to add to backlog
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RetroAgent:
    """
    Agent-Driven Retrospective System
    
    Analyzes what worked/failed using journey theory, business model canvas, and behavioral science.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        kpi_dashboard: KPIDashboardAggregator,
        metrics_tracker: MetricsTracker
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.kpi_dashboard = kpi_dashboard
        self.metrics_tracker = metrics_tracker
        self._analyses: Dict[str, RetroAnalysis] = {}
        
    async def run_sprint_retro(
        self,
        sprint_id: str,
        sprint_start: datetime,
        sprint_end: datetime
    ) -> RetroAnalysis:
        """Run sprint retrospective"""
        return await self._run_retro(
            analysis_type=RetroAnalysisType.SPRINT_RETRO,
            period_start=sprint_start,
            period_end=sprint_end,
            context={"sprint_id": sprint_id}
        )
    
    async def run_deployment_retro(
        self,
        deployment_id: str,
        deployment_time: datetime,
        lookback_days: int = 7
    ) -> RetroAnalysis:
        """Run deployment retrospective"""
        period_start = deployment_time - timedelta(days=lookback_days)
        return await self._run_retro(
            analysis_type=RetroAnalysisType.DEPLOYMENT_RETRO,
            period_start=period_start,
            period_end=deployment_time,
            context={"deployment_id": deployment_id}
        )
    
    async def run_feature_retro(
        self,
        feature_name: str,
        feature_launch_date: datetime,
        lookback_days: int = 30
    ) -> RetroAnalysis:
        """Run feature retrospective"""
        period_start = feature_launch_date
        period_end = feature_launch_date + timedelta(days=lookback_days)
        return await self._run_retro(
            analysis_type=RetroAnalysisType.FEATURE_RETRO,
            period_start=period_start,
            period_end=period_end,
            context={"feature_name": feature_name}
        )
    
    async def _run_retro(
        self,
        analysis_type: RetroAnalysisType,
        period_start: datetime,
        period_end: datetime,
        context: Dict[str, Any]
    ) -> RetroAnalysis:
        """Run retrospective analysis"""
        
        # Get KPI dashboard for the period
        days = (period_end - period_start).days
        dashboard = await self.kpi_dashboard.generate_dashboard(days=days)
        
        # Analyze what worked
        what_worked = await self._analyze_what_worked(dashboard, period_start, period_end)
        
        # Analyze what failed
        what_failed = await self._analyze_what_failed(dashboard, period_start, period_end)
        
        # Generate insights using journey theory
        journey_insights = await self._analyze_journey_optimization(dashboard, period_start, period_end)
        
        # Generate insights using business model canvas
        business_insights = await self._analyze_business_model(dashboard, period_start, period_end)
        
        # Generate insights using behavioral science
        behavioral_insights = await self._analyze_behavioral_science(dashboard, period_start, period_end)
        
        # Combine all insights
        all_insights = journey_insights + business_insights + behavioral_insights
        
        # Generate backlog items
        backlog_items = await self._generate_backlog_items(all_insights, what_failed)
        
        # Calculate meta-metrics
        meta_metrics = {
            "total_insights": len(all_insights),
            "high_impact_insights": len([i for i in all_insights if i.impact == "High"]),
            "backlog_items_generated": len(backlog_items),
            "analysis_duration_seconds": 0  # Would track actual time
        }
        
        analysis = RetroAnalysis(
            analysis_id=str(uuid4()),
            analysis_type=analysis_type,
            period_start=period_start,
            period_end=period_end,
            insights=all_insights,
            what_worked=what_worked,
            what_failed=what_failed,
            meta_metrics=meta_metrics,
            backlog_items=backlog_items
        )
        
        self._analyses[analysis.analysis_id] = analysis
        
        # Log event
        await self.events.log_event(
            event_type="retro_analysis_completed",
            user_id=None,  # System event
            properties={
                "analysis_id": analysis.analysis_id,
                "analysis_type": analysis_type.value,
                "total_insights": len(all_insights),
                "backlog_items": len(backlog_items),
                **context
            }
        )
        
        return analysis
    
    async def _analyze_what_worked(
        self,
        dashboard: Any,
        period_start: datetime,
        period_end: datetime
    ) -> List[str]:
        """Analyze what worked well"""
        what_worked = []
        
        # High retention rate
        if dashboard.business_success.retention_rate > 0.85:
            what_worked.append(f"High retention rate: {dashboard.business_success.retention_rate:.1%}")
        
        # Good LTV/CAC ratio
        if dashboard.business_success.ltv_cac_ratio > 3.0:
            what_worked.append(f"Strong LTV/CAC ratio: {dashboard.business_success.ltv_cac_ratio:.1f}:1")
        
        # High task completion rate
        if dashboard.user_success.task_completion_rate > 0.80:
            what_worked.append(f"High task completion rate: {dashboard.user_success.task_completion_rate:.1%}")
        
        # Positive NPS
        if dashboard.user_success.nps_score > 0:
            what_worked.append(f"Positive NPS score: {dashboard.user_success.nps_score:.1f}")
        
        # Low support case frequency
        if dashboard.operational_ease.support_case_frequency < 0.20:
            what_worked.append(f"Low support case frequency: {dashboard.operational_ease.support_case_frequency:.2f} per user/month")
        
        return what_worked
    
    async def _analyze_what_failed(
        self,
        dashboard: Any,
        period_start: datetime,
        period_end: datetime
    ) -> List[str]:
        """Analyze what failed or needs improvement"""
        what_failed = []
        
        # Low conversion rate
        if dashboard.business_success.conversion_rate < 0.10:
            what_failed.append(f"Low conversion rate: {dashboard.business_success.conversion_rate:.1%} (target: >15%)")
        
        # Low retention rate
        if dashboard.business_success.retention_rate < 0.80:
            what_failed.append(f"Low retention rate: {dashboard.business_success.retention_rate:.1%} (target: >85%)")
        
        # High support case frequency
        if dashboard.operational_ease.support_case_frequency > 0.25:
            what_failed.append(f"High support case frequency: {dashboard.operational_ease.support_case_frequency:.2f} per user/month (target: <0.15)")
        
        # Low task completion rate
        if dashboard.user_success.task_completion_rate < 0.70:
            what_failed.append(f"Low task completion rate: {dashboard.user_success.task_completion_rate:.1%} (target: >80%)")
        
        # Negative or low NPS
        if dashboard.user_success.nps_score < 0:
            what_failed.append(f"Negative NPS score: {dashboard.user_success.nps_score:.1f} (target: >0)")
        
        # Long time to value
        if dashboard.user_success.time_to_value_minutes > 30:
            what_failed.append(f"Long time to value: {dashboard.user_success.time_to_value_minutes:.1f} minutes (target: <30)")
        
        return what_failed
    
    async def _analyze_journey_optimization(
        self,
        dashboard: Any,
        period_start: datetime,
        period_end: datetime
    ) -> List[RetroInsight]:
        """Analyze journey optimization opportunities"""
        insights = []
        
        # Analyze persona-specific journey performance
        for persona, metrics in dashboard.user_success.by_persona.items():
            # Check for journey friction
            if metrics.get("time_to_value_minutes", 0) > 30:
                insights.append(RetroInsight(
                    insight_id=str(uuid4()),
                    category=InsightCategory.JOURNEY_OPTIMIZATION,
                    title=f"Long time-to-value for {persona} persona",
                    description=f"{persona} users take {metrics.get('time_to_value_minutes', 0):.1f} minutes to achieve first value, exceeding 30-minute target.",
                    evidence=[
                        f"Time-to-value: {metrics.get('time_to_value_minutes', 0):.1f} minutes",
                        f"Persona: {persona}"
                    ],
                    impact="High",
                    recommendations=[
                        "Review onboarding flow for this persona",
                        "Identify friction points in first-value journey",
                        "Consider persona-specific onboarding paths",
                        "Add progress indicators and guidance"
                    ],
                    related_persona=persona,
                    related_journey_stage="onboarding"
                ))
            
            # Check task completion rates
            if metrics.get("task_completion_rate", 1.0) < 0.75:
                insights.append(RetroInsight(
                    insight_id=str(uuid4()),
                    category=InsightCategory.JOURNEY_OPTIMIZATION,
                    title=f"Low task completion rate for {persona} persona",
                    description=f"{persona} users have {metrics.get('task_completion_rate', 0):.1%} task completion rate, below 75% target.",
                    evidence=[
                        f"Task completion rate: {metrics.get('task_completion_rate', 0):.1%}",
                        f"Persona: {persona}"
                    ],
                    impact="Medium",
                    recommendations=[
                        "Identify which tasks are failing most often",
                        "Review error messages and guidance",
                        "Consider simplifying complex tasks",
                        "Add contextual help for this persona"
                    ],
                    related_persona=persona
                ))
        
        return insights
    
    async def _analyze_business_model(
        self,
        dashboard: Any,
        period_start: datetime,
        period_end: datetime
    ) -> List[RetroInsight]:
        """Analyze business model opportunities"""
        insights = []
        
        # Analyze conversion rates by persona
        for persona, metrics in dashboard.business_success.by_persona.items():
            conversion_rate = metrics.get("conversion_rate", 0)
            
            if conversion_rate < 0.10:
                insights.append(RetroInsight(
                    insight_id=str(uuid4()),
                    category=InsightCategory.BUSINESS_MODEL,
                    title=f"Low conversion rate for {persona} persona",
                    description=f"{persona} users have {conversion_rate:.1%} conversion rate, below 10% target.",
                    evidence=[
                        f"Conversion rate: {conversion_rate:.1%}",
                        f"Persona: {persona}"
                    ],
                    impact="High",
                    recommendations=[
                        "Review pricing/value proposition for this persona",
                        "Identify conversion barriers",
                        "Test different pricing tiers",
                        "Improve value demonstration in free tier"
                    ],
                    related_persona=persona
                ))
            
            # Analyze LTV/CAC ratio
            ltv_cac = metrics.get("ltv_cac_ratio", 0)
            if ltv_cac < 3.0:
                insights.append(RetroInsight(
                    insight_id=str(uuid4()),
                    category=InsightCategory.BUSINESS_MODEL,
                    title=f"Low LTV/CAC ratio for {persona} persona",
                    description=f"{persona} users have {ltv_cac:.1f}:1 LTV/CAC ratio, below 3:1 target.",
                    evidence=[
                        f"LTV/CAC ratio: {ltv_cac:.1f}:1",
                        f"Persona: {persona}"
                    ],
                    impact="High",
                    recommendations=[
                        "Reduce customer acquisition cost for this persona",
                        "Increase lifetime value through retention/expansion",
                        "Review marketing channels and efficiency",
                        "Consider persona-specific pricing"
                    ],
                    related_persona=persona
                ))
        
        return insights
    
    async def _analyze_behavioral_science(
        self,
        dashboard: Any,
        period_start: datetime,
        period_end: datetime
    ) -> List[RetroInsight]:
        """Analyze behavioral science insights"""
        insights = []
        
        # Analyze NPS by persona
        for persona, metrics in dashboard.user_success.by_persona.items():
            nps = metrics.get("nps_score", 0)
            
            if nps < 0:
                insights.append(RetroInsight(
                    insight_id=str(uuid4()),
                    category=InsightCategory.BEHAVIORAL_SCIENCE,
                    title=f"Negative NPS for {persona} persona indicates dissatisfaction",
                    description=f"{persona} users have negative NPS score of {nps:.1f}, indicating more detractors than promoters.",
                    evidence=[
                        f"NPS score: {nps:.1f}",
                        f"Persona: {persona}"
                    ],
                    impact="High",
                    recommendations=[
                        "Identify root causes of dissatisfaction",
                        "Review user feedback and support tickets",
                        "Address friction points in user experience",
                        "Consider behavioral interventions (nudges, defaults, etc.)",
                        "Improve value delivery for this persona"
                    ],
                    related_persona=persona
                ))
        
        # Analyze support case frequency (indicates friction)
        if dashboard.operational_ease.support_case_frequency > 0.20:
            insights.append(RetroInsight(
                insight_id=str(uuid4()),
                category=InsightCategory.BEHAVIORAL_SCIENCE,
                title="High support case frequency indicates UX friction",
                description=f"Users contact support {dashboard.operational_ease.support_case_frequency:.2f} times per month on average, indicating friction in the user experience.",
                evidence=[
                    f"Support case frequency: {dashboard.operational_ease.support_case_frequency:.2f} per user/month",
                    f"Target: <0.15 per user/month"
                ],
                impact="Medium",
                recommendations=[
                    "Analyze support ticket topics to identify friction points",
                    "Improve in-app guidance and documentation",
                    "Add proactive help and tooltips",
                    "Simplify complex workflows",
                    "Consider behavioral design improvements (progressive disclosure, defaults, etc.)"
                ]
            ))
        
        return insights
    
    async def _generate_backlog_items(
        self,
        insights: List[RetroInsight],
        what_failed: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate backlog items from insights and failures"""
        backlog_items = []
        
        # Create backlog items from high-impact insights
        for insight in insights:
            if insight.impact == "High":
                backlog_items.append({
                    "title": f"Address: {insight.title}",
                    "description": insight.description,
                    "priority": "High",
                    "category": insight.category.value,
                    "recommendations": insight.recommendations,
                    "related_persona": insight.related_persona,
                    "related_journey_stage": insight.related_journey_stage,
                    "source": "retro_analysis",
                    "insight_id": insight.insight_id
                })
        
        # Create backlog items from failures
        for failure in what_failed:
            backlog_items.append({
                "title": f"Fix: {failure}",
                "description": failure,
                "priority": "Medium",
                "category": "improvement",
                "source": "retro_analysis"
            })
        
        return backlog_items
    
    def get_analysis(self, analysis_id: str) -> Optional[RetroAnalysis]:
        """Get retrospective analysis by ID"""
        return self._analyses.get(analysis_id)
    
    def list_analyses(
        self,
        analysis_type: Optional[RetroAnalysisType] = None,
        limit: int = 10
    ) -> List[RetroAnalysis]:
        """List retrospective analyses"""
        analyses = list(self._analyses.values())
        
        if analysis_type:
            analyses = [a for a in analyses if a.analysis_type == analysis_type]
        
        # Sort by creation date (newest first)
        analyses.sort(key=lambda x: x.created_at, reverse=True)
        
        return analyses[:limit]

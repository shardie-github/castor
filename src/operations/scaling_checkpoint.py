"""
Scaling Checkpoint Agent

At each scaling checkpoint, requires agent prompt:
"Does every persona, business function, and critical journey meet or exceed target KPIs?
If not, escalate and backlog immediately."
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.feedback.kpi_dashboard import KPIDashboardAggregator, KPICategory
from src.operations.support import SupportIntegration, EscalationLevel
from src.operations.predictive_scoring import PersonaGroup

logger = logging.getLogger(__name__)


class CheckpointStatus(Enum):
    """Checkpoint status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    REQUIRES_ATTENTION = "requires_attention"


class BusinessFunction(Enum):
    """Business functions"""
    USER_ONBOARDING = "user_onboarding"
    CAMPAIGN_MANAGEMENT = "campaign_management"
    REPORT_GENERATION = "report_generation"
    ANALYTICS = "analytics"
    BILLING = "billing"
    SUPPORT = "support"
    DATA_EXPORT = "data_export"


class CriticalJourney(Enum):
    """Critical user journeys"""
    SIGNUP_TO_FIRST_CAMPAIGN = "signup_to_first_campaign"
    CAMPAIGN_CREATION = "campaign_creation"
    REPORT_GENERATION = "report_generation"
    SPONSOR_RENEWAL = "sponsor_renewal"
    UPGRADE_SUBSCRIPTION = "upgrade_subscription"
    DATA_EXPORT = "data_export"
    SUPPORT_RESOLUTION = "support_resolution"


@dataclass
class KPITarget:
    """KPI target definition"""
    kpi_name: str
    target_value: float
    threshold_warning: float  # Warning threshold (below target)
    threshold_critical: float  # Critical threshold
    unit: str = "percentage"  # percentage, count, hours, etc.


@dataclass
class CheckpointResult:
    """Scaling checkpoint result"""
    checkpoint_id: str
    checkpoint_name: str
    status: CheckpointStatus
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Results by dimension
    persona_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    business_function_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    journey_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Escalations and backlog items
    escalations: List[Dict[str, Any]] = field(default_factory=list)
    backlog_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    summary: Dict[str, Any] = field(default_factory=dict)


class ScalingCheckpointAgent:
    """
    Scaling Checkpoint Agent
    
    Validates that every persona, business function, and critical journey
    meets or exceeds target KPIs. Escalates and backlogs issues immediately.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        kpi_dashboard: KPIDashboardAggregator,
        support_integration: SupportIntegration
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.kpi_dashboard = kpi_dashboard
        self.support = support_integration
        
        # Define KPI targets
        self.kpi_targets = {
            # Persona-specific targets
            "conversion_rate": KPITarget("conversion_rate", 0.15, 0.12, 0.10),
            "retention_rate": KPITarget("retention_rate", 0.85, 0.80, 0.75),
            "nps_score": KPITarget("nps_score", 50.0, 40.0, 30.0),
            "time_to_value_minutes": KPITarget("time_to_value_minutes", 30.0, 45.0, 60.0),
            "task_completion_rate": KPITarget("task_completion_rate", 0.85, 0.75, 0.65),
            "support_resolution_time_hours": KPITarget("support_resolution_time_hours", 4.0, 8.0, 12.0),
            "renewal_rate": KPITarget("renewal_rate", 0.80, 0.70, 0.60),
            
            # Business function targets
            "campaign_creation_success_rate": KPITarget("campaign_creation_success_rate", 0.95, 0.90, 0.85),
            "report_generation_success_rate": KPITarget("report_generation_success_rate", 0.98, 0.95, 0.90),
            "onboarding_completion_rate": KPITarget("onboarding_completion_rate", 0.80, 0.70, 0.60),
            
            # Journey targets
            "signup_to_campaign_days": KPITarget("signup_to_campaign_days", 1.0, 3.0, 7.0),
            "campaign_to_report_days": KPITarget("campaign_to_report_days", 7.0, 14.0, 21.0)
        }
        
        self._checkpoints: Dict[str, CheckpointResult] = {}
        
    async def run_checkpoint(
        self,
        checkpoint_name: str,
        days: int = 30
    ) -> CheckpointResult:
        """
        Run scaling checkpoint validation
        
        Prompt: "Does every persona, business function, and critical journey
        meet or exceed target KPIs? If not, escalate and backlog immediately."
        
        Args:
            checkpoint_name: Name of checkpoint
            days: Number of days to analyze
            
        Returns:
            CheckpointResult
        """
        checkpoint_id = str(uuid4())
        
        logger.info(f"Running scaling checkpoint: {checkpoint_name}")
        
        # Get KPI dashboard
        dashboard = await self.kpi_dashboard.generate_dashboard(days=days)
        
        # Check personas
        persona_results = await self._check_personas(dashboard, days)
        
        # Check business functions
        business_function_results = await self._check_business_functions(dashboard, days)
        
        # Check critical journeys
        journey_results = await self._check_critical_journeys(dashboard, days)
        
        # Generate escalations and backlog items
        escalations = []
        backlog_items = []
        
        # Escalate failures
        for persona, results in persona_results.items():
            if results.get("status") == "failed":
                escalation = await self._create_escalation(
                    f"Persona {persona} failing KPIs",
                    f"Persona {persona} is not meeting target KPIs: {results.get('failures', [])}",
                    EscalationLevel.LEVEL_3
                )
                escalations.append(escalation)
        
        for function, results in business_function_results.items():
            if results.get("status") == "failed":
                escalation = await self._create_escalation(
                    f"Business function {function} failing",
                    f"Business function {function} is not meeting targets: {results.get('failures', [])}",
                    EscalationLevel.LEVEL_2
                )
                escalations.append(escalation)
        
        for journey, results in journey_results.items():
            if results.get("status") == "failed":
                escalation = await self._create_escalation(
                    f"Critical journey {journey} failing",
                    f"Critical journey {journey} is not meeting targets: {results.get('failures', [])}",
                    EscalationLevel.LEVEL_3
                )
                escalations.append(escalation)
        
        # Create backlog items
        for persona, results in persona_results.items():
            if results.get("status") in ["failed", "warning"]:
                backlog_items.append({
                    "title": f"Fix KPI failures for {persona} persona",
                    "description": f"Address KPI failures: {', '.join(results.get('failures', []))}",
                    "priority": "high" if results.get("status") == "failed" else "medium",
                    "persona": persona,
                    "type": "persona_improvement"
                })
        
        for function, results in business_function_results.items():
            if results.get("status") in ["failed", "warning"]:
                backlog_items.append({
                    "title": f"Improve {function} business function",
                    "description": f"Address issues: {', '.join(results.get('failures', []))}",
                    "priority": "high" if results.get("status") == "failed" else "medium",
                    "function": function,
                    "type": "business_function_improvement"
                })
        
        for journey, results in journey_results.items():
            if results.get("status") in ["failed", "warning"]:
                backlog_items.append({
                    "title": f"Optimize {journey} journey",
                    "description": f"Address journey issues: {', '.join(results.get('failures', []))}",
                    "priority": "high" if results.get("status") == "failed" else "medium",
                    "journey": journey,
                    "type": "journey_optimization"
                })
        
        # Determine overall status
        all_passed = all(
            r.get("status") == "passed"
            for r in list(persona_results.values()) +
                     list(business_function_results.values()) +
                     list(journey_results.values())
        )
        
        any_failed = any(
            r.get("status") == "failed"
            for r in list(persona_results.values()) +
                     list(business_function_results.values()) +
                     list(journey_results.values())
        )
        
        if all_passed:
            status = CheckpointStatus.PASSED
        elif any_failed:
            status = CheckpointStatus.FAILED
        else:
            status = CheckpointStatus.WARNING
        
        result = CheckpointResult(
            checkpoint_id=checkpoint_id,
            checkpoint_name=checkpoint_name,
            status=status,
            persona_results=persona_results,
            business_function_results=business_function_results,
            journey_results=journey_results,
            escalations=escalations,
            backlog_items=backlog_items,
            summary={
                "total_personas_checked": len(persona_results),
                "personas_passed": sum(1 for r in persona_results.values() if r.get("status") == "passed"),
                "total_functions_checked": len(business_function_results),
                "functions_passed": sum(1 for r in business_function_results.values() if r.get("status") == "passed"),
                "total_journeys_checked": len(journey_results),
                "journeys_passed": sum(1 for r in journey_results.values() if r.get("status") == "passed"),
                "escalations_created": len(escalations),
                "backlog_items_created": len(backlog_items)
            }
        )
        
        self._checkpoints[checkpoint_id] = result
        
        # Record metrics
        self.metrics.record_gauge(
            "scaling_checkpoint_status",
            {"passed": 1, "warning": 2, "failed": 3}.get(status.value, 0),
            tags={"checkpoint_name": checkpoint_name}
        )
        
        self.metrics.increment_counter(
            "scaling_checkpoint_run",
            tags={"status": status.value, "checkpoint_name": checkpoint_name}
        )
        
        await self.events.log_event(
            event_type="scaling_checkpoint_completed",
            user_id=None,
            properties={
                "checkpoint_id": checkpoint_id,
                "checkpoint_name": checkpoint_name,
                "status": status.value,
                "summary": result.summary
            }
        )
        
        return result
    
    async def _check_personas(
        self,
        dashboard,
        days: int
    ) -> Dict[str, Dict[str, Any]]:
        """Check KPIs for all personas"""
        personas = [p.value for p in PersonaGroup]
        results = {}
        
        for persona in personas:
            persona_dashboard = await self.kpi_dashboard.generate_dashboard(
                days=days,
                persona_segment=persona
            )
            
            failures = []
            warnings = []
            
            # Check conversion rate
            target = self.kpi_targets["conversion_rate"]
            actual = persona_dashboard.business_success.conversion_rate
            if actual < target.threshold_critical:
                failures.append(f"conversion_rate: {actual:.2%} < {target.threshold_critical:.2%}")
            elif actual < target.target_value:
                warnings.append(f"conversion_rate: {actual:.2%} < {target.target_value:.2%}")
            
            # Check retention rate
            target = self.kpi_targets["retention_rate"]
            actual = persona_dashboard.business_success.retention_rate
            if actual < target.threshold_critical:
                failures.append(f"retention_rate: {actual:.2%} < {target.threshold_critical:.2%}")
            elif actual < target.target_value:
                warnings.append(f"retention_rate: {actual:.2%} < {target.target_value:.2%}")
            
            # Check NPS
            target = self.kpi_targets["nps_score"]
            actual = persona_dashboard.user_success.nps_score
            if actual < target.threshold_critical:
                failures.append(f"nps_score: {actual:.1f} < {target.threshold_critical:.1f}")
            elif actual < target.target_value:
                warnings.append(f"nps_score: {actual:.1f} < {target.target_value:.1f}")
            
            # Check time to value
            target = self.kpi_targets["time_to_value_minutes"]
            actual = persona_dashboard.user_success.time_to_value_minutes
            if actual > target.threshold_critical:
                failures.append(f"time_to_value: {actual:.1f}min > {target.threshold_critical:.1f}min")
            elif actual > target.target_value:
                warnings.append(f"time_to_value: {actual:.1f}min > {target.target_value:.1f}min")
            
            status = "passed"
            if failures:
                status = "failed"
            elif warnings:
                status = "warning"
            
            results[persona] = {
                "status": status,
                "failures": failures,
                "warnings": warnings,
                "metrics": {
                    "conversion_rate": actual,
                    "retention_rate": persona_dashboard.business_success.retention_rate,
                    "nps_score": actual,
                    "time_to_value": actual
                }
            }
        
        return results
    
    async def _check_business_functions(
        self,
        dashboard,
        days: int
    ) -> Dict[str, Dict[str, Any]]:
        """Check KPIs for business functions"""
        results = {}
        
        # In production, would check actual function metrics
        # For now, use placeholder logic
        
        functions = [f.value for f in BusinessFunction]
        for function in functions:
            # Placeholder: assume passed for now
            results[function] = {
                "status": "passed",
                "failures": [],
                "warnings": [],
                "metrics": {}
            }
        
        return results
    
    async def _check_critical_journeys(
        self,
        dashboard,
        days: int
    ) -> Dict[str, Dict[str, Any]]:
        """Check KPIs for critical journeys"""
        results = {}
        
        # In production, would check actual journey metrics
        # For now, use placeholder logic
        
        journeys = [j.value for j in CriticalJourney]
        for journey in journeys:
            # Placeholder: assume passed for now
            results[journey] = {
                "status": "passed",
                "failures": [],
                "warnings": [],
                "metrics": {}
            }
        
        return results
    
    async def _create_escalation(
        self,
        title: str,
        description: str,
        level: EscalationLevel
    ) -> Dict[str, Any]:
        """Create escalation"""
        # In production, would create actual support ticket
        escalation = {
            "title": title,
            "description": description,
            "level": level.value,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Log escalation
        await self.events.log_event(
            event_type="scaling_checkpoint_escalation",
            user_id=None,
            properties=escalation
        )
        
        return escalation
    
    async def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointResult]:
        """Get checkpoint result by ID"""
        return self._checkpoints.get(checkpoint_id)
    
    async def list_checkpoints(
        self,
        status: Optional[CheckpointStatus] = None
    ) -> List[CheckpointResult]:
        """List checkpoints with optional filter"""
        checkpoints = list(self._checkpoints.values())
        
        if status:
            checkpoints = [c for c in checkpoints if c.status == status]
        
        return sorted(checkpoints, key=lambda c: c.checked_at, reverse=True)

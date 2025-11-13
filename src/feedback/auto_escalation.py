"""
Auto-Escalation System

Automatically escalates tasks that:
- Degrade LTV (Lifetime Value)
- Increase support load
- Drop user-perceived value
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


class EscalationSeverity(Enum):
    """Escalation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationType(Enum):
    """Escalation types"""
    LTV_DEGRADATION = "ltv_degradation"
    SUPPORT_LOAD_INCREASE = "support_load_increase"
    VALUE_DROP = "value_drop"
    RETENTION_DROP = "retention_drop"
    ERROR_SPIKE = "error_spike"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class EscalationRule:
    """Escalation rule definition"""
    rule_id: str
    escalation_type: EscalationType
    severity: EscalationSeverity
    condition: Dict[str, Any]  # Condition to trigger escalation
    threshold: float  # Threshold value
    comparison: str  # "greater_than", "less_than", "equals"
    action: str  # Action to take
    notification_channels: List[str]  # Email, Slack, PagerDuty, etc.
    enabled: bool = True


@dataclass
class Escalation:
    """Escalation instance"""
    escalation_id: str
    rule_id: str
    escalation_type: EscalationType
    severity: EscalationSeverity
    title: str
    description: str
    current_value: float
    threshold_value: float
    affected_personas: List[str]
    affected_features: List[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AutoEscalationSystem:
    """
    Auto-Escalation System
    
    Monitors KPIs and automatically escalates issues.
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
        self._rules: Dict[str, EscalationRule] = {}
        self._escalations: Dict[str, Escalation] = {}
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default escalation rules"""
        
        # LTV degradation rule
        ltv_rule = EscalationRule(
            rule_id="ltv_degradation",
            escalation_type=EscalationType.LTV_DEGRADATION,
            severity=EscalationSeverity.HIGH,
            condition={"metric": "ltv_cac_ratio", "period_days": 30},
            threshold=2.5,
            comparison="less_than",
            action="notify_product_team",
            notification_channels=["email", "slack"]
        )
        self._rules[ltv_rule.rule_id] = ltv_rule
        
        # Support load increase rule
        support_rule = EscalationRule(
            rule_id="support_load_increase",
            escalation_type=EscalationType.SUPPORT_LOAD_INCREASE,
            severity=EscalationSeverity.MEDIUM,
            condition={"metric": "support_case_frequency", "period_days": 7},
            threshold=0.25,
            comparison="greater_than",
            action="notify_support_team",
            notification_channels=["email", "slack"]
        )
        self._rules[support_rule.rule_id] = support_rule
        
        # Value drop rule (NPS negative)
        value_drop_rule = EscalationRule(
            rule_id="value_drop",
            escalation_type=EscalationType.VALUE_DROP,
            severity=EscalationSeverity.HIGH,
            condition={"metric": "nps_score", "period_days": 7},
            threshold=0.0,
            comparison="less_than",
            action="notify_product_team",
            notification_channels=["email", "slack", "pagerduty"]
        )
        self._rules[value_drop_rule.rule_id] = value_drop_rule
        
        # Retention drop rule
        retention_rule = EscalationRule(
            rule_id="retention_drop",
            escalation_type=EscalationType.RETENTION_DROP,
            severity=EscalationSeverity.CRITICAL,
            condition={"metric": "retention_rate", "period_days": 30},
            threshold=0.75,
            comparison="less_than",
            action="notify_executive_team",
            notification_channels=["email", "slack", "pagerduty"]
        )
        self._rules[retention_rule.rule_id] = retention_rule
        
        # Error spike rule
        error_rule = EscalationRule(
            rule_id="error_spike",
            escalation_type=EscalationType.ERROR_SPIKE,
            severity=EscalationSeverity.MEDIUM,
            condition={"metric": "error_rate", "period_days": 1},
            threshold=0.10,  # 10% error rate
            comparison="greater_than",
            action="notify_engineering_team",
            notification_channels=["email", "slack", "pagerduty"]
        )
        self._rules[error_rule.rule_id] = error_rule
        
    async def check_escalations(
        self,
        days: int = 7,
        persona_segment: Optional[str] = None
    ) -> List[Escalation]:
        """Check for escalations based on current metrics"""
        dashboard = await self.kpi_dashboard.generate_dashboard(days=days, persona_segment=persona_segment)
        new_escalations = []
        
        # Check each rule
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            escalation = await self._check_rule(rule, dashboard, days)
            if escalation:
                new_escalations.append(escalation)
                self._escalations[escalation.escalation_id] = escalation
                
                # Record telemetry
                self.metrics.increment_counter(
                    "escalation_triggered",
                    tags={
                        "escalation_type": rule.escalation_type.value,
                        "severity": rule.severity.value
                    }
                )
                
                # Log event
                await self.events.log_event(
                    event_type="escalation_triggered",
                    user_id=None,
                    properties={
                        "escalation_id": escalation.escalation_id,
                        "escalation_type": rule.escalation_type.value,
                        "severity": rule.severity.value,
                        "current_value": escalation.current_value,
                        "threshold_value": escalation.threshold_value
                    }
                )
                
                # Send notifications (would integrate with notification system)
                await self._send_notifications(escalation, rule)
        
        return new_escalations
    
    async def _check_rule(
        self,
        rule: EscalationRule,
        dashboard: Any,
        days: int
    ) -> Optional[Escalation]:
        """Check if a rule should trigger"""
        condition = rule.condition
        metric_name = condition.get("metric")
        
        # Get metric value based on type
        current_value = None
        affected_personas = []
        affected_features = []
        
        if metric_name == "ltv_cac_ratio":
            current_value = dashboard.business_success.ltv_cac_ratio
            # Check by persona
            for persona, metrics in dashboard.business_success.by_persona.items():
                if metrics.get("ltv_cac_ratio", 0) < rule.threshold:
                    affected_personas.append(persona)
        
        elif metric_name == "support_case_frequency":
            current_value = dashboard.operational_ease.support_case_frequency
            # Check by persona
            for persona, metrics in dashboard.operational_ease.by_persona.items():
                if metrics.get("support_case_frequency", 0) > rule.threshold:
                    affected_personas.append(persona)
        
        elif metric_name == "nps_score":
            current_value = dashboard.user_success.nps_score
            # Check by persona
            for persona, metrics in dashboard.user_success.by_persona.items():
                if metrics.get("nps_score", 0) < rule.threshold:
                    affected_personas.append(persona)
        
        elif metric_name == "retention_rate":
            current_value = dashboard.business_success.retention_rate
            # Check by persona
            for persona, metrics in dashboard.business_success.by_persona.items():
                if metrics.get("retention_rate", 1.0) < rule.threshold:
                    affected_personas.append(persona)
        
        elif metric_name == "error_rate":
            # Would get from metrics tracker
            error_stats = await self.metrics_tracker.get_error_rate_by_persona(days=days)
            current_value = error_stats.get("total_errors", 0) / 1000.0 if error_stats.get("total_errors", 0) > 0 else 0.0
            # Check by persona
            for persona, count in error_stats.get("by_persona", {}).items():
                if count > rule.threshold * 100:  # Convert to count
                    affected_personas.append(persona)
        
        if current_value is None:
            return None
        
        # Check if condition is met
        should_escalate = False
        if rule.comparison == "less_than" and current_value < rule.threshold:
            should_escalate = True
        elif rule.comparison == "greater_than" and current_value > rule.threshold:
            should_escalate = True
        elif rule.comparison == "equals" and abs(current_value - rule.threshold) < 0.01:
            should_escalate = True
        
        if not should_escalate:
            return None
        
        # Check if escalation already exists and is unresolved
        existing_escalations = [
            e for e in self._escalations.values()
            if e.rule_id == rule.rule_id
            and e.resolved_at is None
        ]
        if existing_escalations:
            return None  # Already escalated
        
        # Create escalation
        escalation = Escalation(
            escalation_id=str(uuid4()),
            rule_id=rule.rule_id,
            escalation_type=rule.escalation_type,
            severity=rule.severity,
            title=f"{rule.escalation_type.value.replace('_', ' ').title()} Detected",
            description=f"{metric_name} is {current_value:.2f}, which {'exceeds' if rule.comparison == 'greater_than' else 'falls below'} threshold of {rule.threshold:.2f}",
            current_value=current_value,
            threshold_value=rule.threshold,
            affected_personas=affected_personas or ["all"],
            affected_features=affected_features
        )
        
        return escalation
    
    async def _send_notifications(
        self,
        escalation: Escalation,
        rule: EscalationRule
    ):
        """Send notifications for escalation"""
        # In production, would integrate with:
        # - Email service (SendGrid, AWS SES)
        # - Slack API
        # - PagerDuty API
        # - SMS service
        
        notification_message = f"""
        ESCALATION: {escalation.title}
        
        Severity: {escalation.severity.value.upper()}
        Type: {escalation.escalation_type.value}
        
        {escalation.description}
        
        Current Value: {escalation.current_value:.2f}
        Threshold: {escalation.threshold_value:.2f}
        
        Affected Personas: {', '.join(escalation.affected_personas)}
        
        Action Required: {rule.action}
        """
        
        logger.warning(f"Escalation notification: {notification_message}")
        
        # Log event
        await self.events.log_event(
            event_type="escalation_notification_sent",
            user_id=None,
            properties={
                "escalation_id": escalation.escalation_id,
                "channels": rule.notification_channels
            }
        )
    
    async def resolve_escalation(
        self,
        escalation_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> Escalation:
        """Resolve an escalation"""
        escalation = self._escalations.get(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.resolved_at = datetime.now(timezone.utc)
        escalation.resolved_by = resolved_by
        escalation.resolution_notes = resolution_notes
        
        # Log event
        await self.events.log_event(
            event_type="escalation_resolved",
            user_id=resolved_by,
            properties={
                "escalation_id": escalation_id,
                "resolution_notes": resolution_notes
            }
        )
        
        return escalation
    
    def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        """Get escalation by ID"""
        return self._escalations.get(escalation_id)
    
    def list_escalations(
        self,
        severity: Optional[EscalationSeverity] = None,
        resolved: Optional[bool] = None
    ) -> List[Escalation]:
        """List escalations"""
        escalations = list(self._escalations.values())
        
        if severity:
            escalations = [e for e in escalations if e.severity == severity]
        
        if resolved is not None:
            if resolved:
                escalations = [e for e in escalations if e.resolved_at is not None]
            else:
                escalations = [e for e in escalations if e.resolved_at is None]
        
        # Sort by severity and creation date
        severity_order = {
            EscalationSeverity.CRITICAL: 0,
            EscalationSeverity.HIGH: 1,
            EscalationSeverity.MEDIUM: 2,
            EscalationSeverity.LOW: 3
        }
        escalations.sort(key=lambda x: (severity_order.get(x.severity, 99), x.created_at))
        
        return escalations
    
    def add_rule(self, rule: EscalationRule):
        """Add a new escalation rule"""
        self._rules[rule.rule_id] = rule
    
    def get_rule(self, rule_id: str) -> Optional[EscalationRule]:
        """Get rule by ID"""
        return self._rules.get(rule_id)
    
    def list_rules(self, enabled_only: bool = False) -> List[EscalationRule]:
        """List escalation rules"""
        rules = list(self._rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules

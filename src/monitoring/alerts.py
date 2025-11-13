"""
Alert Management System

Manages alerts for:
- System health issues
- Performance degradation
- Error rate spikes
- SLA violations
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    service: Optional[str] = None
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """
    Alert Manager
    
    Manages alerts:
    - Alert creation
    - Alert routing
    - Alert escalation
    - Alert resolution
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: List[Dict[str, Any]] = []
    
    async def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        service: Optional[str] = None,
        metric_name: Optional[str] = None,
        threshold: Optional[float] = None,
        current_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert"""
        alert_id = f"alert_{datetime.now(timezone.utc).timestamp()}"
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            service=service,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            metadata=metadata or {}
        )
        
        self._alerts[alert_id] = alert
        
        # Send alert notification
        await self._send_alert_notification(alert)
        
        # Log event
        await self.events.log_event(
            event_type="alert_created",
            user_id=None,
            properties={
                "alert_id": alert_id,
                "severity": severity.value,
                "service": service,
                "title": title
            }
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "alerts_created",
            tags={
                "severity": severity.value,
                "service": service or "unknown"
            }
        )
        
        return alert
    
    async def check_metrics_and_alert(self, metrics: Dict[str, float]):
        """Check metrics against thresholds and create alerts"""
        for metric_name, value in metrics.items():
            # Check against alert rules
            for rule in self._alert_rules:
                if rule.get("metric") == metric_name:
                    threshold = rule.get("threshold")
                    severity = AlertSeverity(rule.get("severity", "warning"))
                    
                    if self._should_alert(value, threshold, rule.get("operator", "gt")):
                        await self.create_alert(
                            title=f"{metric_name} threshold exceeded",
                            message=f"{metric_name} is {value}, threshold is {threshold}",
                            severity=severity,
                            metric_name=metric_name,
                            threshold=threshold,
                            current_value=value
                        )
    
    def _should_alert(
        self,
        value: float,
        threshold: float,
        operator: str
    ) -> bool:
        """Check if value should trigger alert"""
        if operator == "gt":
            return value > threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "eq":
            return value == threshold
        else:
            return False
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        # Log event
        await self.events.log_event(
            event_type="alert_acknowledged",
            user_id=user_id,
            properties={"alert_id": alert_id}
        )
        
        return True
    
    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Resolve an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        
        # Log event
        await self.events.log_event(
            event_type="alert_resolved",
            user_id=user_id,
            properties={"alert_id": alert_id}
        )
        
        # Record telemetry
        duration_seconds = (alert.resolved_at - alert.created_at).total_seconds()
        self.metrics.record_histogram(
            "alert_resolution_time_seconds",
            duration_seconds,
            tags={"severity": alert.severity.value}
        )
        
        return True
    
    async def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        service: Optional[str] = None
    ) -> List[Alert]:
        """Get active alerts"""
        alerts = [
            alert for alert in self._alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if service:
            alerts = [a for a in alerts if a.service == service]
        
        return alerts
    
    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification (email, Slack, PagerDuty, etc.)"""
        # In production, this would:
        # - Send email for WARNING and above
        # - Send Slack message for ERROR and above
        # - Page on-call for CRITICAL
        
        logger.info(f"Alert: {alert.severity.value} - {alert.title}: {alert.message}")
        
        # Record telemetry
        self.metrics.increment_counter(
            "alert_notifications_sent",
            tags={"severity": alert.severity.value}
        )
    
    def add_alert_rule(
        self,
        metric: str,
        threshold: float,
        severity: AlertSeverity,
        operator: str = "gt"
    ):
        """Add an alert rule"""
        rule = {
            "metric": metric,
            "threshold": threshold,
            "severity": severity.value,
            "operator": operator
        }
        self._alert_rules.append(rule)

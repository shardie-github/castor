"""
Background Task Agents Module

Handles background tasks including:
- Feed update scheduling
- Analytics aggregation
- Anomaly detection
- Alert generation
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert types"""
    PERFORMANCE_DROP = "performance_drop"
    ANOMALY_DETECTED = "anomaly_detected"
    CAMPAIGN_UNDERPERFORMING = "campaign_underperforming"
    FEED_UPDATE_FAILED = "feed_update_failed"
    SYSTEM_ERROR = "system_error"


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    campaign_id: Optional[str] = None
    podcast_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = None
    acknowledged: bool = False
    metadata: Dict[str, Any] = None


class AnomalyDetector:
    """
    Anomaly Detection Agent
    
    Detects anomalies in campaign performance, feed updates, and system metrics.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._alerts: List[Alert] = []
        
    async def detect_campaign_anomalies(
        self,
        campaign_id: str,
        current_performance: Dict[str, float],
        historical_performance: List[Dict[str, float]]
    ) -> List[Alert]:
        """
        Detect anomalies in campaign performance
        
        Args:
            campaign_id: Campaign ID
            current_performance: Current performance metrics
            historical_performance: Historical performance data
            
        Returns:
            List of alerts
        """
        alerts = []
        
        if not historical_performance:
            return alerts
        
        # Calculate baseline metrics
        baseline_downloads = sum(p.get("downloads", 0) for p in historical_performance) / len(historical_performance)
        baseline_conversions = sum(p.get("conversions", 0) for p in historical_performance) / len(historical_performance)
        
        current_downloads = current_performance.get("downloads", 0)
        current_conversions = current_performance.get("conversions", 0)
        
        # Detect significant drops (>30%)
        if baseline_downloads > 0:
            drop_percentage = (baseline_downloads - current_downloads) / baseline_downloads
            if drop_percentage > 0.3:
                alert = Alert(
                    alert_id=f"alert_{campaign_id}_{datetime.now(timezone.utc).timestamp()}",
                    alert_type=AlertType.PERFORMANCE_DROP,
                    severity=AlertSeverity.HIGH,
                    title="Campaign Performance Drop Detected",
                    message=f"Downloads dropped by {drop_percentage*100:.1f}% compared to baseline",
                    campaign_id=campaign_id,
                    created_at=datetime.now(timezone.utc),
                    metadata={"drop_percentage": drop_percentage, "baseline": baseline_downloads, "current": current_downloads}
                )
                alerts.append(alert)
        
        # Detect conversion anomalies
        if baseline_conversions > 0:
            conversion_drop = (baseline_conversions - current_conversions) / baseline_conversions
            if conversion_drop > 0.5:  # 50% drop
                alert = Alert(
                    alert_id=f"alert_{campaign_id}_conversion_{datetime.now(timezone.utc).timestamp()}",
                    alert_type=AlertType.CAMPAIGN_UNDERPERFORMING,
                    severity=AlertSeverity.MEDIUM,
                    title="Campaign Conversion Drop",
                    message=f"Conversions dropped by {conversion_drop*100:.1f}%",
                    campaign_id=campaign_id,
                    created_at=datetime.now(timezone.utc),
                    metadata={"drop_percentage": conversion_drop}
                )
                alerts.append(alert)
        
        # Record telemetry
        if alerts:
            self.metrics.increment_counter(
                "anomalies_detected",
                tags={"campaign_id": campaign_id, "alert_count": len(alerts)}
            )
        
        return alerts
    
    async def detect_system_anomalies(
        self,
        metrics: Dict[str, float]
    ) -> List[Alert]:
        """Detect system-level anomalies"""
        alerts = []
        
        # Check error rate
        error_rate = metrics.get("error_rate", 0)
        if error_rate > 0.05:  # 5% error rate threshold
            alert = Alert(
                alert_id=f"alert_system_error_{datetime.now(timezone.utc).timestamp()}",
                alert_type=AlertType.SYSTEM_ERROR,
                severity=AlertSeverity.CRITICAL,
                title="High Error Rate Detected",
                message=f"System error rate is {error_rate*100:.1f}%",
                created_at=datetime.now(timezone.utc),
                metadata={"error_rate": error_rate}
            )
            alerts.append(alert)
        
        # Check latency
        p95_latency = metrics.get("p95_latency_ms", 0)
        if p95_latency > 2000:  # 2 second threshold
            alert = Alert(
                alert_id=f"alert_system_latency_{datetime.now(timezone.utc).timestamp()}",
                alert_type=AlertType.SYSTEM_ERROR,
                severity=AlertSeverity.MEDIUM,
                title="High Latency Detected",
                message=f"P95 latency is {p95_latency}ms",
                created_at=datetime.now(timezone.utc),
                metadata={"p95_latency_ms": p95_latency}
            )
            alerts.append(alert)
        
        return alerts


class UpdateAgent:
    """
    Update Agent
    
    Handles scheduled updates including:
    - Feed polling
    - Analytics aggregation
    - Data synchronization
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        update_interval: int = 900  # 15 minutes
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.update_interval = update_interval
        self.running = False
        
    async def start(self):
        """Start update agent"""
        self.running = True
        
        while self.running:
            try:
                # Run update tasks
                await self._run_updates()
                
                # Wait for next interval
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in update agent: {e}")
                self.metrics.increment_counter(
                    "update_agent_errors",
                    tags={"error_type": type(e).__name__}
                )
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop(self):
        """Stop update agent"""
        self.running = False
    
    async def _run_updates(self):
        """Run scheduled update tasks"""
        # In production, this would:
        # 1. Trigger feed polling
        # 2. Aggregate analytics data
        # 3. Sync data across systems
        # 4. Update caches
        # 5. Run feedback loop checks (escalations, metrics)
        
        self.metrics.increment_counter("update_agent_runs")
        logger.debug("Update agent running scheduled tasks")


class AlertAgent:
    """
    Alert Agent
    
    Generates and sends alerts based on anomalies and thresholds.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        anomaly_detector: AnomalyDetector
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.anomaly_detector = anomaly_detector
        self._alerts: List[Alert] = []
        
    async def process_alerts(self, alerts: List[Alert]):
        """Process and send alerts"""
        for alert in alerts:
            # Store alert
            self._alerts.append(alert)
            
            # Record telemetry
            self.metrics.increment_counter(
                "alerts_generated",
                tags={
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value
                }
            )
            
            # Log event
            await self.events.log_event(
                event_type="alert_generated",
                user_id=alert.user_id,
                properties={
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "campaign_id": alert.campaign_id,
                    "podcast_id": alert.podcast_id
                }
            )
            
            # Send notification (email, push, in-app)
            await self._send_notification(alert)
    
    async def _send_notification(self, alert: Alert):
        """Send alert notification"""
        # In production, this would:
        # - Send email notification
        # - Send push notification
        # - Create in-app notification
        # - Post to Slack/webhook
        
        logger.info(f"Sending alert: {alert.title} - {alert.message}")
        
        # Record telemetry
        self.metrics.increment_counter(
            "alert_notifications_sent",
            tags={"alert_type": alert.alert_type.value}
        )


class BackgroundTaskManager:
    """
    Background Task Manager
    
    Coordinates all background tasks and agents.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        
        # Initialize agents
        self.anomaly_detector = AnomalyDetector(metrics_collector, event_logger)
        self.update_agent = UpdateAgent(metrics_collector, event_logger)
        self.alert_agent = AlertAgent(metrics_collector, event_logger, self.anomaly_detector)
        
        self.running = False
        
    async def start(self):
        """Start all background tasks"""
        self.running = True
        
        # Start update agent
        await self.update_agent.start()
        
    async def stop(self):
        """Stop all background tasks"""
        self.running = False
        await self.update_agent.stop()
    
    async def check_campaign_performance(
        self,
        campaign_id: str,
        current_performance: Dict[str, float],
        historical_performance: List[Dict[str, float]]
    ):
        """Check campaign performance and generate alerts if needed"""
        alerts = await self.anomaly_detector.detect_campaign_anomalies(
            campaign_id,
            current_performance,
            historical_performance
        )
        
        if alerts:
            await self.alert_agent.process_alerts(alerts)
        
        return alerts

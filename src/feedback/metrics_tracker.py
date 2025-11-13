"""
Metrics Tracking System

Tracks key metrics broken down by persona:
- Time-to-value
- Report accuracy
- Sponsor renewal success
- Error/support incidents
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Metric categories"""
    TIME_TO_VALUE = "time_to_value"
    REPORT_ACCURACY = "report_accuracy"
    RENEWAL_SUCCESS = "renewal_success"
    ERROR_INCIDENTS = "error_incidents"
    SUPPORT_INCIDENTS = "support_incidents"
    FEATURE_COMPLETION = "feature_completion"


@dataclass
class MetricRecord:
    """Individual metric record"""
    record_id: str
    user_id: str
    persona_segment: str
    metric_category: MetricCategory
    metric_name: str
    value: float
    unit: str  # seconds, percentage, count, etc.
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    feature: Optional[str] = None
    journey_stage: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsTracker:
    """
    Metrics Tracking System
    
    Tracks key metrics by persona for feedback loop analysis.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._records: List[MetricRecord] = []
        
    async def track_time_to_value(
        self,
        user_id: str,
        persona_segment: str,
        value_type: str,
        time_seconds: float,
        feature: Optional[str] = None,
        journey_stage: Optional[str] = None
    ):
        """Track time-to-value metric"""
        record = MetricRecord(
            record_id=str(uuid4()),
            user_id=user_id,
            persona_segment=persona_segment,
            metric_category=MetricCategory.TIME_TO_VALUE,
            metric_name=f"time_to_{value_type}",
            value=time_seconds,
            unit="seconds",
            feature=feature,
            journey_stage=journey_stage,
            metadata={"value_type": value_type}
        )
        
        self._records.append(record)
        
        # Record telemetry
        self.metrics.record_histogram(
            "time_to_value",
            time_seconds,
            tags={
                "persona_segment": persona_segment,
                "value_type": value_type,
                "feature": feature or "none"
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="time_to_value_tracked",
            user_id=user_id,
            properties={
                "value_type": value_type,
                "time_seconds": time_seconds,
                "persona_segment": persona_segment,
                "feature": feature,
                "journey_stage": journey_stage
            }
        )
        
    async def track_report_accuracy(
        self,
        user_id: str,
        persona_segment: str,
        report_id: str,
        accuracy_rating: float,  # 1-5 scale
        sponsor_feedback: Optional[str] = None,
        data_issues: Optional[List[str]] = None
    ):
        """Track report accuracy metric"""
        record = MetricRecord(
            record_id=str(uuid4()),
            user_id=user_id,
            persona_segment=persona_segment,
            metric_category=MetricCategory.REPORT_ACCURACY,
            metric_name="report_accuracy_rating",
            value=accuracy_rating,
            unit="rating_1_5",
            feature="report_generation",
            metadata={
                "report_id": report_id,
                "sponsor_feedback": sponsor_feedback,
                "data_issues": data_issues or []
            }
        )
        
        self._records.append(record)
        
        # Record telemetry
        self.metrics.record_gauge(
            "report_accuracy_rating",
            accuracy_rating,
            tags={
                "persona_segment": persona_segment,
                "report_id": report_id
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="report_accuracy_tracked",
            user_id=user_id,
            properties={
                "report_id": report_id,
                "accuracy_rating": accuracy_rating,
                "persona_segment": persona_segment,
                "has_data_issues": bool(data_issues)
            }
        )
        
    async def track_renewal_success(
        self,
        user_id: str,
        persona_segment: str,
        campaign_id: str,
        renewed: bool,
        rate_increase: Optional[float] = None,
        renewal_tools_used: bool = False
    ):
        """Track sponsor renewal success"""
        record = MetricRecord(
            record_id=str(uuid4()),
            user_id=user_id,
            persona_segment=persona_segment,
            metric_category=MetricCategory.RENEWAL_SUCCESS,
            metric_name="renewal_success",
            value=1.0 if renewed else 0.0,
            unit="boolean",
            feature="renewal_tools",
            journey_stage="renewal_discussion",
            metadata={
                "campaign_id": campaign_id,
                "renewed": renewed,
                "rate_increase": rate_increase,
                "renewal_tools_used": renewal_tools_used
            }
        )
        
        self._records.append(record)
        
        # Record telemetry
        self.metrics.increment_counter(
            "renewal_success" if renewed else "renewal_failure",
            tags={
                "persona_segment": persona_segment,
                "campaign_id": campaign_id,
                "renewal_tools_used": str(renewal_tools_used)
            }
        )
        
        if rate_increase:
            self.metrics.record_gauge(
                "renewal_rate_increase",
                rate_increase,
                tags={
                    "persona_segment": persona_segment,
                    "campaign_id": campaign_id
                }
            )
        
        # Log event
        await self.events.log_event(
            event_type="renewal_success_tracked",
            user_id=user_id,
            properties={
                "campaign_id": campaign_id,
                "renewed": renewed,
                "rate_increase": rate_increase,
                "renewal_tools_used": renewal_tools_used,
                "persona_segment": persona_segment
            }
        )
        
    async def track_error_incident(
        self,
        user_id: str,
        persona_segment: str,
        error_type: str,
        error_message: str,
        feature: Optional[str] = None,
        journey_stage: Optional[str] = None,
        resolved: bool = False
    ):
        """Track error incident"""
        record = MetricRecord(
            record_id=str(uuid4()),
            user_id=user_id,
            persona_segment=persona_segment,
            metric_category=MetricCategory.ERROR_INCIDENTS,
            metric_name="error_incident",
            value=1.0,
            unit="count",
            feature=feature,
            journey_stage=journey_stage,
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "resolved": resolved
            }
        )
        
        self._records.append(record)
        
        # Record telemetry
        self.metrics.increment_counter(
            "error_incident",
            tags={
                "persona_segment": persona_segment,
                "error_type": error_type,
                "feature": feature or "none",
                "resolved": str(resolved)
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="error_incident_tracked",
            user_id=user_id,
            properties={
                "error_type": error_type,
                "error_message": error_message,
                "persona_segment": persona_segment,
                "feature": feature,
                "journey_stage": journey_stage,
                "resolved": resolved
            }
        )
        
    async def track_support_incident(
        self,
        user_id: str,
        persona_segment: str,
        support_type: str,
        issue_category: str,
        resolved: bool = False,
        resolution_time_minutes: Optional[float] = None
    ):
        """Track support incident"""
        record = MetricRecord(
            record_id=str(uuid4()),
            user_id=user_id,
            persona_segment=persona_segment,
            metric_category=MetricCategory.SUPPORT_INCIDENTS,
            metric_name="support_incident",
            value=1.0,
            unit="count",
            metadata={
                "support_type": support_type,
                "issue_category": issue_category,
                "resolved": resolved,
                "resolution_time_minutes": resolution_time_minutes
            }
        )
        
        self._records.append(record)
        
        # Record telemetry
        self.metrics.increment_counter(
            "support_incident",
            tags={
                "persona_segment": persona_segment,
                "support_type": support_type,
                "issue_category": issue_category,
                "resolved": str(resolved)
            }
        )
        
        if resolution_time_minutes:
            self.metrics.record_histogram(
                "support_resolution_time",
                resolution_time_minutes,
                tags={
                    "persona_segment": persona_segment,
                    "issue_category": issue_category
                }
            )
        
        # Log event
        await self.events.log_event(
            event_type="support_incident_tracked",
            user_id=user_id,
            properties={
                "support_type": support_type,
                "issue_category": issue_category,
                "persona_segment": persona_segment,
                "resolved": resolved,
                "resolution_time_minutes": resolution_time_minutes
            }
        )
        
    async def get_metrics_by_persona(
        self,
        metric_category: MetricCategory,
        persona_segment: Optional[str] = None,
        days: int = 30,
        feature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics aggregated by persona"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        records = [
            r for r in self._records
            if r.timestamp >= cutoff_date
            and r.metric_category == metric_category
        ]
        
        if persona_segment:
            records = [r for r in records if r.persona_segment == persona_segment]
        
        if feature:
            records = [r for r in records if r.feature == feature]
        
        # Aggregate by persona
        metrics_by_persona: Dict[str, Dict[str, Any]] = {}
        
        for record in records:
            persona = record.persona_segment
            if persona not in metrics_by_persona:
                metrics_by_persona[persona] = {
                    "total_records": 0,
                    "values": [],
                    "average": 0.0,
                    "median": 0.0,
                    "min": None,
                    "max": None
                }
            
            metrics_by_persona[persona]["total_records"] += 1
            metrics_by_persona[persona]["values"].append(record.value)
        
        # Calculate statistics
        for persona, stats in metrics_by_persona.items():
            if stats["values"]:
                sorted_values = sorted(stats["values"])
                stats["average"] = sum(sorted_values) / len(sorted_values)
                stats["median"] = sorted_values[len(sorted_values) // 2]
                stats["min"] = min(sorted_values)
                stats["max"] = max(sorted_values)
                stats["values"] = sorted_values  # Keep sorted for percentile calculations
        
        return {
            "metric_category": metric_category.value,
            "period_days": days,
            "by_persona": metrics_by_persona,
            "total_records": len(records)
        }
    
    async def get_time_to_value_stats(
        self,
        persona_segment: Optional[str] = None,
        days: int = 30,
        value_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get time-to-value statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        records = [
            r for r in self._records
            if r.timestamp >= cutoff_date
            and r.metric_category == MetricCategory.TIME_TO_VALUE
        ]
        
        if persona_segment:
            records = [r for r in records if r.persona_segment == persona_segment]
        
        if value_type:
            records = [r for r in records if r.metadata.get("value_type") == value_type]
        
        if not records:
            return {
                "total_records": 0,
                "average_seconds": 0.0,
                "median_seconds": 0.0,
                "p90_seconds": 0.0,
                "by_persona": {}
            }
        
        # Calculate overall stats
        values = [r.value for r in records]
        sorted_values = sorted(values)
        
        stats = {
            "total_records": len(records),
            "average_seconds": sum(values) / len(values),
            "median_seconds": sorted_values[len(sorted_values) // 2],
            "p90_seconds": sorted_values[int(len(sorted_values) * 0.9)] if sorted_values else 0.0,
            "min_seconds": min(values),
            "max_seconds": max(values)
        }
        
        # Calculate by persona
        by_persona: Dict[str, Dict[str, float]] = {}
        for record in records:
            persona = record.persona_segment
            if persona not in by_persona:
                by_persona[persona] = []
            by_persona[persona].append(record.value)
        
        for persona, persona_values in by_persona.items():
            sorted_persona_values = sorted(persona_values)
            by_persona[persona] = {
                "count": len(persona_values),
                "average_seconds": sum(persona_values) / len(persona_values),
                "median_seconds": sorted_persona_values[len(sorted_persona_values) // 2],
                "p90_seconds": sorted_persona_values[int(len(sorted_persona_values) * 0.9)] if sorted_persona_values else 0.0
            }
        
        stats["by_persona"] = by_persona
        
        return stats
    
    async def get_renewal_rate_by_persona(
        self,
        days: int = 90,
        persona_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get renewal rate statistics by persona"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        records = [
            r for r in self._records
            if r.timestamp >= cutoff_date
            and r.metric_category == MetricCategory.RENEWAL_SUCCESS
        ]
        
        if persona_segment:
            records = [r for r in records if r.persona_segment == persona_segment]
        
        if not records:
            return {
                "total_campaigns": 0,
                "renewal_rate": 0.0,
                "by_persona": {}
            }
        
        # Calculate overall renewal rate
        renewed = sum(1 for r in records if r.value == 1.0)
        renewal_rate = renewed / len(records) if records else 0.0
        
        # Calculate by persona
        by_persona: Dict[str, Dict[str, Any]] = {}
        for record in records:
            persona = record.persona_segment
            if persona not in by_persona:
                by_persona[persona] = {"total": 0, "renewed": 0}
            by_persona[persona]["total"] += 1
            if record.value == 1.0:
                by_persona[persona]["renewed"] += 1
        
        for persona, stats in by_persona.items():
            stats["renewal_rate"] = stats["renewed"] / stats["total"] if stats["total"] > 0 else 0.0
        
        return {
            "total_campaigns": len(records),
            "renewal_rate": renewal_rate,
            "by_persona": by_persona,
            "period_days": days
        }
    
    async def get_error_rate_by_persona(
        self,
        days: int = 30,
        persona_segment: Optional[str] = None,
        feature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error rate statistics by persona"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        records = [
            r for r in self._records
            if r.timestamp >= cutoff_date
            and r.metric_category == MetricCategory.ERROR_INCIDENTS
        ]
        
        if persona_segment:
            records = [r for r in records if r.persona_segment == persona_segment]
        
        if feature:
            records = [r for r in records if r.feature == feature]
        
        # Count by persona
        by_persona: Dict[str, int] = {}
        for record in records:
            persona = record.persona_segment
            by_persona[persona] = by_persona.get(persona, 0) + 1
        
        return {
            "total_errors": len(records),
            "by_persona": by_persona,
            "period_days": days
        }

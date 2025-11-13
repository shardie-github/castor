"""
MVP Success Tracking System

Tracks MVP-specific success criteria:
- Activation metrics
- Feature adoption
- Customer feedback
- A/B test results
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.feedback.metrics_tracker import MetricsTracker
from src.feedback.ab_testing import ABTestingFramework

logger = logging.getLogger(__name__)


class ActivationEvent(Enum):
    """Activation events"""
    SIGNUP = "signup"
    EMAIL_VERIFIED = "email_verified"
    PODCAST_ADDED = "podcast_added"
    FIRST_CAMPAIGN = "first_campaign"
    FIRST_REPORT = "first_report"
    FIRST_ATTRIBUTION = "first_attribution"
    ACTIVATED = "activated"  # Completed all activation steps


class FeatureAdoptionStatus(Enum):
    """Feature adoption status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ADOPTED = "adopted"
    POWER_USER = "power_user"


@dataclass
class ActivationMetric:
    """Activation metric"""
    user_id: str
    event: ActivationEvent
    timestamp: datetime
    time_from_signup: Optional[float] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureAdoption:
    """Feature adoption tracking"""
    user_id: str
    feature_name: str
    status: FeatureAdoptionStatus
    first_used_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    adoption_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MVPSuccessMetrics:
    """MVP success metrics summary"""
    activation_rate: float  # % of signups who activate
    time_to_activation: float  # Average time to activation (minutes)
    feature_adoption_rates: Dict[str, float]  # Feature -> adoption rate
    customer_feedback_score: float  # Average feedback score
    ab_test_results: Dict[str, Any]  # A/B test results
    activation_funnel: Dict[str, int]  # Event -> user count
    period_days: int


class MVPSuccessTracker:
    """
    MVP Success Tracker
    
    Tracks MVP-specific success criteria and metrics.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        metrics_tracker: MetricsTracker,
        ab_testing: ABTestingFramework
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.metrics_tracker = metrics_tracker
        self.ab_testing = ab_testing
        self._activation_events: List[ActivationMetric] = []
        self._feature_adoptions: Dict[str, Dict[str, FeatureAdoption]] = {}  # user_id -> feature_name -> adoption
        
    async def track_activation_event(
        self,
        user_id: str,
        event: ActivationEvent,
        time_from_signup: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an activation event"""
        activation = ActivationMetric(
            user_id=user_id,
            event=event,
            timestamp=datetime.now(timezone.utc),
            time_from_signup=time_from_signup,
            metadata=metadata or {}
        )
        
        self._activation_events.append(activation)
        
        # Record metrics
        self.metrics.increment_counter(
            "activation_event",
            tags={
                "event": event.value,
                "user_id": user_id
            }
        )
        
        if time_from_signup:
            self.metrics.record_histogram(
                "time_to_activation_event",
                time_from_signup,
                tags={"event": event.value}
            )
        
        # Log event
        await self.events.log_event(
            event_type="activation_event",
            user_id=user_id,
            properties={
                "event": event.value,
                "time_from_signup": time_from_signup,
                "metadata": metadata
            }
        )
    
    async def track_feature_adoption(
        self,
        user_id: str,
        feature_name: str,
        action: str = "used"
    ):
        """Track feature adoption"""
        if user_id not in self._feature_adoptions:
            self._feature_adoptions[user_id] = {}
        
        if feature_name not in self._feature_adoptions[user_id]:
            adoption = FeatureAdoption(
                user_id=user_id,
                feature_name=feature_name,
                status=FeatureAdoptionStatus.NOT_STARTED
            )
            self._feature_adoptions[user_id][feature_name] = adoption
        
        adoption = self._feature_adoptions[user_id][feature_name]
        adoption.usage_count += 1
        adoption.last_used_at = datetime.now(timezone.utc)
        
        # Update status
        if adoption.status == FeatureAdoptionStatus.NOT_STARTED:
            adoption.status = FeatureAdoptionStatus.IN_PROGRESS
            adoption.first_used_at = datetime.now(timezone.utc)
        
        if adoption.usage_count >= 3:
            adoption.status = FeatureAdoptionStatus.ADOPTED
            if not adoption.adoption_date:
                adoption.adoption_date = datetime.now(timezone.utc)
        
        if adoption.usage_count >= 10:
            adoption.status = FeatureAdoptionStatus.POWER_USER
        
        # Record metrics
        self.metrics.increment_counter(
            "feature_adoption",
            tags={
                "feature": feature_name,
                "status": adoption.status.value,
                "user_id": user_id
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="feature_adoption",
            user_id=user_id,
            properties={
                "feature_name": feature_name,
                "action": action,
                "usage_count": adoption.usage_count,
                "status": adoption.status.value
            }
        )
    
    async def calculate_activation_rate(
        self,
        days: int = 30,
        activation_definition: List[ActivationEvent] = None
    ) -> float:
        """Calculate activation rate"""
        if activation_definition is None:
            activation_definition = [
                ActivationEvent.PODCAST_ADDED,
                ActivationEvent.FIRST_CAMPAIGN,
                ActivationEvent.FIRST_REPORT
            ]
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all signups in period
        signups = [
            e for e in self._activation_events
            if e.event == ActivationEvent.SIGNUP
            and e.timestamp >= cutoff_date
        ]
        
        # Get activated users (completed all activation events)
        activated_users = set()
        for event_type in activation_definition:
            event_users = {
                e.user_id for e in self._activation_events
                if e.event == event_type
                and e.timestamp >= cutoff_date
            }
            if not activated_users:
                activated_users = event_users
            else:
                activated_users = activated_users.intersection(event_users)
        
        if not signups:
            return 0.0
        
        activation_rate = len(activated_users) / len(signups) * 100
        
        # Record metric
        self.metrics.record_gauge(
            "activation_rate",
            activation_rate,
            tags={"period_days": str(days)}
        )
        
        return activation_rate
    
    async def calculate_time_to_activation(
        self,
        days: int = 30,
        activation_definition: List[ActivationEvent] = None
    ) -> float:
        """Calculate average time to activation (minutes)"""
        if activation_definition is None:
            activation_definition = [
                ActivationEvent.PODCAST_ADDED,
                ActivationEvent.FIRST_CAMPAIGN,
                ActivationEvent.FIRST_REPORT
            ]
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get signup times
        signups = {
            e.user_id: e.timestamp
            for e in self._activation_events
            if e.event == ActivationEvent.SIGNUP
            and e.timestamp >= cutoff_date
        }
        
        # Get activation times (last event in activation definition)
        activation_times = []
        for user_id, signup_time in signups.items():
            # Find last activation event for this user
            user_events = [
                e for e in self._activation_events
                if e.user_id == user_id
                and e.event in activation_definition
                and e.timestamp >= cutoff_date
            ]
            
            if user_events:
                last_event = max(user_events, key=lambda e: e.timestamp)
                time_diff = (last_event.timestamp - signup_time).total_seconds() / 60
                activation_times.append(time_diff)
        
        if not activation_times:
            return 0.0
        
        avg_time = sum(activation_times) / len(activation_times)
        
        # Record metric
        self.metrics.record_gauge(
            "time_to_activation_minutes",
            avg_time,
            tags={"period_days": str(days)}
        )
        
        return avg_time
    
    async def calculate_feature_adoption_rates(
        self,
        days: int = 30,
        features: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Calculate feature adoption rates"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all users who signed up in period
        signups = {
            e.user_id
            for e in self._activation_events
            if e.event == ActivationEvent.SIGNUP
            and e.timestamp >= cutoff_date
        }
        
        if not signups:
            return {}
        
        # Calculate adoption per feature
        adoption_rates = {}
        
        for user_id, feature_adoptions in self._feature_adoptions.items():
            if user_id not in signups:
                continue
            
            for feature_name, adoption in feature_adoptions.items():
                if features and feature_name not in features:
                    continue
                
                if adoption.first_used_at and adoption.first_used_at >= cutoff_date:
                    if feature_name not in adoption_rates:
                        adoption_rates[feature_name] = {"adopted": 0, "total": 0}
                    
                    adoption_rates[feature_name]["total"] += 1
                    if adoption.status in [
                        FeatureAdoptionStatus.ADOPTED,
                        FeatureAdoptionStatus.POWER_USER
                    ]:
                        adoption_rates[feature_name]["adopted"] += 1
        
        # Calculate rates
        result = {}
        for feature_name, counts in adoption_rates.items():
            if counts["total"] > 0:
                result[feature_name] = (counts["adopted"] / counts["total"]) * 100
        
        return result
    
    async def get_mvp_success_metrics(
        self,
        days: int = 30
    ) -> MVPSuccessMetrics:
        """Get comprehensive MVP success metrics"""
        activation_rate = await self.calculate_activation_rate(days=days)
        time_to_activation = await self.calculate_time_to_activation(days=days)
        feature_adoption_rates = await self.calculate_feature_adoption_rates(days=days)
        
        # Get activation funnel
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        activation_funnel = {}
        for event in ActivationEvent:
            count = len([
                e for e in self._activation_events
                if e.event == event
                and e.timestamp >= cutoff_date
            ])
            activation_funnel[event.value] = count
        
        # Get customer feedback score (would integrate with feedback system)
        customer_feedback_score = 0.0  # Placeholder
        
        # Get A/B test results (would integrate with A/B testing framework)
        ab_test_results = {}  # Placeholder
        
        return MVPSuccessMetrics(
            activation_rate=activation_rate,
            time_to_activation=time_to_activation,
            feature_adoption_rates=feature_adoption_rates,
            customer_feedback_score=customer_feedback_score,
            ab_test_results=ab_test_results,
            activation_funnel=activation_funnel,
            period_days=days
        )

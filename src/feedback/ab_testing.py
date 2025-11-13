"""
A/B Testing Framework

Enables A/B and shadow experiments for:
- Onboarding flows
- Pricing prompts
- Report templates
- Feature variations
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import User

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """Experiment types"""
    ONBOARDING = "onboarding"
    PRICING = "pricing"
    REPORT_TEMPLATE = "report_template"
    FEATURE_VARIATION = "feature_variation"
    UI_ELEMENT = "ui_element"


class ExperimentStatus(Enum):
    """Experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentVariant:
    """Experiment variant"""
    variant_id: str
    name: str
    description: str
    configuration: Dict[str, Any]  # Variant-specific configuration
    traffic_percentage: float  # 0.0 to 1.0


@dataclass
class Experiment:
    """A/B test experiment"""
    experiment_id: str
    name: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    variants: List[ExperimentVariant]
    start_date: datetime
    end_date: Optional[datetime] = None
    target_personas: List[str] = field(default_factory=list)  # Empty = all personas
    target_journey_stage: Optional[str] = None
    success_metrics: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None


@dataclass
class ExperimentAssignment:
    """User assignment to experiment variant"""
    assignment_id: str
    experiment_id: str
    user_id: str
    variant_id: str
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExperimentResults:
    """Experiment results"""
    experiment_id: str
    variant_results: Dict[str, Dict[str, Any]]  # variant_id -> metrics
    winner: Optional[str] = None  # variant_id of winner
    confidence_level: float = 0.0  # Statistical confidence (0-1)
    analysis_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ABTestingFramework:
    """
    A/B Testing Framework
    
    Manages experiments and tracks results.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._experiments: Dict[str, Experiment] = {}
        self._assignments: Dict[str, List[ExperimentAssignment]] = {}  # user_id -> assignments
        self._results: Dict[str, ExperimentResults] = {}
        
    async def create_experiment(
        self,
        name: str,
        experiment_type: ExperimentType,
        variants: List[Dict[str, Any]],
        success_metrics: List[str],
        target_personas: Optional[List[str]] = None,
        target_journey_stage: Optional[str] = None,
        duration_days: int = 14,
        created_by: Optional[str] = None
    ) -> Experiment:
        """Create a new A/B test experiment"""
        
        # Validate variants
        total_traffic = sum(v.get("traffic_percentage", 0) for v in variants)
        if abs(total_traffic - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Variant traffic percentages must sum to 1.0, got {total_traffic}")
        
        # Create variant objects
        variant_objects = []
        for variant_data in variants:
            variant = ExperimentVariant(
                variant_id=str(uuid4()),
                name=variant_data["name"],
                description=variant_data.get("description", ""),
                configuration=variant_data.get("configuration", {}),
                traffic_percentage=variant_data.get("traffic_percentage", 0.0)
            )
            variant_objects.append(variant)
        
        experiment = Experiment(
            experiment_id=str(uuid4()),
            name=name,
            experiment_type=experiment_type,
            status=ExperimentStatus.DRAFT,
            variants=variant_objects,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=duration_days),
            target_personas=target_personas or [],
            target_journey_stage=target_journey_stage,
            success_metrics=success_metrics,
            created_by=created_by
        )
        
        self._experiments[experiment.experiment_id] = experiment
        
        # Log event
        await self.events.log_event(
            event_type="experiment_created",
            user_id=created_by,
            properties={
                "experiment_id": experiment.experiment_id,
                "experiment_type": experiment_type.value,
                "variant_count": len(variant_objects)
            }
        )
        
        return experiment
    
    async def start_experiment(self, experiment_id: str) -> Experiment:
        """Start an experiment"""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Experiment {experiment_id} is not in DRAFT status")
        
        experiment.status = ExperimentStatus.RUNNING
        
        # Log event
        await self.events.log_event(
            event_type="experiment_started",
            user_id=None,
            properties={"experiment_id": experiment_id}
        )
        
        return experiment
    
    async def assign_variant(
        self,
        user: User,
        experiment_id: str
    ) -> Optional[ExperimentAssignment]:
        """
        Assign user to an experiment variant
        
        Returns:
            Assignment if user should be in experiment, None otherwise
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return None
        
        if experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Check if experiment has ended
        if experiment.end_date and datetime.now(timezone.utc) > experiment.end_date:
            experiment.status = ExperimentStatus.COMPLETED
            return None
        
        # Check persona targeting
        if experiment.target_personas:
            user_persona = user.persona_segment or "unknown"
            if user_persona not in experiment.target_personas:
                return None
        
        # Check if user already assigned
        user_assignments = self._assignments.get(user.user_id, [])
        existing_assignment = next(
            (a for a in user_assignments if a.experiment_id == experiment_id),
            None
        )
        if existing_assignment:
            return existing_assignment
        
        # Assign variant based on traffic percentage
        variant = self._select_variant(experiment.variants)
        
        assignment = ExperimentAssignment(
            assignment_id=str(uuid4()),
            experiment_id=experiment_id,
            user_id=user.user_id,
            variant_id=variant.variant_id
        )
        
        if user.user_id not in self._assignments:
            self._assignments[user.user_id] = []
        self._assignments[user.user_id].append(assignment)
        
        # Record telemetry
        self.metrics.increment_counter(
            "experiment_assignment",
            tags={
                "experiment_id": experiment_id,
                "variant_id": variant.variant_id,
                "persona_segment": user.persona_segment or "unknown"
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="experiment_assignment",
            user_id=user.user_id,
            properties={
                "experiment_id": experiment_id,
                "variant_id": variant.variant_id,
                "variant_name": variant.name
            }
        )
        
        return assignment
    
    def _select_variant(self, variants: List[ExperimentVariant]) -> ExperimentVariant:
        """Select variant based on traffic percentages"""
        rand = random.random()
        cumulative = 0.0
        
        for variant in variants:
            cumulative += variant.traffic_percentage
            if rand <= cumulative:
                return variant
        
        # Fallback to last variant
        return variants[-1]
    
    async def get_user_variant(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[str]:
        """Get assigned variant ID for user"""
        user_assignments = self._assignments.get(user_id, [])
        assignment = next(
            (a for a in user_assignments if a.experiment_id == experiment_id),
            None
        )
        return assignment.variant_id if assignment else None
    
    async def track_experiment_event(
        self,
        user_id: str,
        experiment_id: str,
        event_name: str,
        event_properties: Optional[Dict[str, Any]] = None
    ):
        """Track event for experiment analysis"""
        variant_id = await self.get_user_variant(user_id, experiment_id)
        if not variant_id:
            return  # User not in experiment
        
        # Record telemetry
        self.metrics.increment_counter(
            "experiment_event",
            tags={
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "event_name": event_name
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="experiment_event",
            user_id=user_id,
            properties={
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "event_name": event_name,
                **(event_properties or {})
            }
        )
    
    async def analyze_experiment(
        self,
        experiment_id: str
    ) -> ExperimentResults:
        """Analyze experiment results"""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Get all assignments for this experiment
        all_assignments = []
        for assignments in self._assignments.values():
            for assignment in assignments:
                if assignment.experiment_id == experiment_id:
                    all_assignments.append(assignment)
        
        # Calculate metrics per variant
        variant_results: Dict[str, Dict[str, Any]] = {}
        
        for variant in experiment.variants:
            variant_assignments = [
                a for a in all_assignments if a.variant_id == variant.variant_id
            ]
            
            # In production, would query actual metrics from analytics
            # For now, use placeholder calculations
            variant_results[variant.variant_id] = {
                "variant_name": variant.name,
                "users_assigned": len(variant_assignments),
                "metrics": {}
            }
            
            # Calculate success metrics (would be real data in production)
            for metric in experiment.success_metrics:
                # Placeholder: would calculate from actual event data
                variant_results[variant.variant_id]["metrics"][metric] = {
                    "value": random.uniform(0.5, 1.0),  # Placeholder
                    "count": len(variant_assignments)
                }
        
        # Determine winner (simplified - would use statistical significance in production)
        winner = None
        confidence_level = 0.0
        
        if len(variant_results) >= 2:
            # Compare variants (simplified logic)
            # In production, would use statistical tests (t-test, chi-square, etc.)
            variant_ids = list(variant_results.keys())
            if len(variant_ids) >= 2:
                # Placeholder: compare first success metric
                if experiment.success_metrics:
                    metric_name = experiment.success_metrics[0]
                    values = [
                        variant_results[vid]["metrics"].get(metric_name, {}).get("value", 0)
                        for vid in variant_ids
                    ]
                    if values:
                        max_value = max(values)
                        winner_idx = values.index(max_value)
                        winner = variant_ids[winner_idx]
                        confidence_level = 0.85  # Placeholder
        
        results = ExperimentResults(
            experiment_id=experiment_id,
            variant_results=variant_results,
            winner=winner,
            confidence_level=confidence_level
        )
        
        self._results[experiment_id] = results
        
        # Log event
        await self.events.log_event(
            event_type="experiment_analyzed",
            user_id=None,
            properties={
                "experiment_id": experiment_id,
                "winner": winner,
                "confidence_level": confidence_level
            }
        )
        
        return results
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        return self._experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None
    ) -> List[Experiment]:
        """List experiments"""
        experiments = list(self._experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        if experiment_type:
            experiments = [e for e in experiments if e.experiment_type == experiment_type]
        
        return experiments

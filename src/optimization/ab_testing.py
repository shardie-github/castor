"""
A/B Testing Framework

Provides comprehensive A/B testing capabilities with statistical analysis.
"""

import logging
import random
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentType(Enum):
    """Experiment types"""
    ONBOARDING = "onboarding"
    FEATURE = "feature"
    UI = "ui"
    PRICING = "pricing"
    CONTENT = "content"
    CAMPAIGN = "campaign"


@dataclass
class Experiment:
    """Experiment data structure"""
    experiment_id: str
    tenant_id: str
    experiment_name: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    variants: List[Dict[str, Any]]
    traffic_allocation: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime


@dataclass
class ExperimentResult:
    """Experiment result"""
    experiment_id: str
    variant_results: Dict[str, Dict[str, Any]]
    winner: Optional[str]
    statistical_significance: float
    confidence_level: float


class ABTestingFramework:
    """
    A/B Testing Framework
    
    Provides comprehensive A/B testing with:
    - Variant assignment
    - Statistical analysis
    - Significance testing
    - Winner determination
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def create_experiment(
        self,
        tenant_id: str,
        experiment_name: str,
        experiment_type: ExperimentType,
        variants: List[Dict[str, Any]],
        traffic_allocation: float = 100.0,
        hypothesis: Optional[str] = None
    ) -> Experiment:
        """Create a new A/B test experiment"""
        experiment_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO experiments (
                experiment_id, tenant_id, experiment_name, experiment_type,
                status, variants, traffic_allocation, hypothesis
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            experiment_id, tenant_id, experiment_name, experiment_type.value,
            ExperimentStatus.DRAFT.value, variants, traffic_allocation, hypothesis
        )
        
        # Log event
        await self.events.log_event(
            event_type="experiment_created",
            user_id=None,
            properties={
                "experiment_id": experiment_id,
                "experiment_name": experiment_name,
                "tenant_id": tenant_id
            }
        )
        
        return Experiment(
            experiment_id=experiment_id,
            tenant_id=tenant_id,
            experiment_name=experiment_name,
            experiment_type=experiment_type,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            traffic_allocation=traffic_allocation,
            start_date=None,
            end_date=None,
            created_at=datetime.now(timezone.utc)
        )
    
    async def assign_variant(
        self,
        tenant_id: str,
        experiment_id: str,
        user_id: str
    ) -> str:
        """
        Assign user to experiment variant
        
        Uses consistent hashing to ensure same user gets same variant.
        """
        # Check if user already assigned
        existing = await self.postgres.fetchrow(
            """
            SELECT variant
            FROM experiment_assignments
            WHERE tenant_id = $1 AND experiment_id = $2 AND user_id = $3
            """,
            tenant_id, experiment_id, user_id
        )
        
        if existing:
            return existing["variant"]
        
        # Get experiment
        exp_row = await self.postgres.fetchrow(
            """
            SELECT variants, traffic_allocation, status
            FROM experiments
            WHERE tenant_id = $1 AND experiment_id = $2
            """,
            tenant_id, experiment_id
        )
        
        if not exp_row or exp_row["status"] != ExperimentStatus.RUNNING.value:
            # Return control variant if experiment not running
            return "control"
        
        variants = exp_row["variants"]
        traffic_allocation = exp_row["traffic_allocation"]
        
        # Consistent hashing based on user_id
        hash_value = hash(f"{experiment_id}:{user_id}") % 10000
        allocation_threshold = traffic_allocation * 100
        
        if hash_value >= allocation_threshold:
            # User not in experiment
            return "control"
        
        # Assign to variant based on hash
        variant_index = hash_value % len(variants)
        variant = variants[variant_index].get("name", f"variant_{variant_index}")
        
        # Store assignment
        await self.postgres.execute(
            """
            INSERT INTO experiment_assignments (
                assignment_id, tenant_id, experiment_id, user_id, variant
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
            """,
            tenant_id, experiment_id, user_id, variant
        )
        
        return variant
    
    async def track_event(
        self,
        tenant_id: str,
        experiment_id: str,
        user_id: str,
        event_type: str,
        event_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track experiment event"""
        # Get assignment
        assignment = await self.postgres.fetchrow(
            """
            SELECT assignment_id
            FROM experiment_assignments
            WHERE tenant_id = $1 AND experiment_id = $2 AND user_id = $3
            """,
            tenant_id, experiment_id, user_id
        )
        
        if not assignment:
            return
        
        assignment_id = assignment["assignment_id"]
        
        # Record event
        await self.postgres.execute(
            """
            INSERT INTO experiment_events (
                event_id, tenant_id, experiment_id, assignment_id,
                event_type, event_value, metadata
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6)
            """,
            tenant_id, experiment_id, assignment_id, event_type,
            event_value, metadata or {}
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "experiment_event",
            tags={
                "experiment_id": experiment_id,
                "event_type": event_type,
                "tenant_id": tenant_id
            }
        )
    
    async def analyze_experiment(
        self,
        tenant_id: str,
        experiment_id: str
    ) -> ExperimentResult:
        """
        Analyze experiment results with statistical significance
        
        Returns:
            ExperimentResult with variant performance and significance
        """
        # Get experiment
        exp_row = await self.postgres.fetchrow(
            """
            SELECT variants, start_date, end_date
            FROM experiments
            WHERE tenant_id = $1 AND experiment_id = $2
            """,
            tenant_id, experiment_id
        )
        
        if not exp_row:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        variants = exp_row["variants"]
        
        # Get variant results
        variant_results = {}
        
        for variant in variants:
            variant_name = variant.get("name", "control")
            
            # Get assignments for variant
            assignments = await self.postgres.fetch(
                """
                SELECT COUNT(*) as total_users
                FROM experiment_assignments
                WHERE tenant_id = $1 AND experiment_id = $2 AND variant = $3
                """,
                tenant_id, experiment_id, variant_name
            )
            
            total_users = assignments[0]["total_users"] if assignments else 0
            
            # Get conversion events
            conversions = await self.postgres.fetch(
                """
                SELECT COUNT(*) as conversions, AVG(event_value) as avg_value
                FROM experiment_events ee
                INNER JOIN experiment_assignments ea ON ee.assignment_id = ea.assignment_id
                WHERE ee.tenant_id = $1 AND ee.experiment_id = $2
                AND ea.variant = $3 AND ee.event_type = 'conversion'
                """,
                tenant_id, experiment_id, variant_name
            )
            
            conv_count = conversions[0]["conversions"] if conversions else 0
            avg_value = float(conversions[0]["avg_value"] or 0) if conversions else 0.0
            
            conversion_rate = (conv_count / total_users * 100) if total_users > 0 else 0.0
            
            variant_results[variant_name] = {
                "total_users": total_users,
                "conversions": conv_count,
                "conversion_rate": conversion_rate,
                "avg_value": avg_value
            }
        
        # Calculate statistical significance
        significance = self._calculate_significance(variant_results)
        
        # Determine winner
        winner = self._determine_winner(variant_results, significance)
        
        # Update experiment with results
        await self.postgres.execute(
            """
            UPDATE experiments
            SET winner_variant = $1, statistical_significance = $2, updated_at = NOW()
            WHERE tenant_id = $3 AND experiment_id = $4
            """,
            winner, significance, tenant_id, experiment_id
        )
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_results=variant_results,
            winner=winner,
            statistical_significance=significance,
            confidence_level=significance * 100
        )
    
    def _calculate_significance(
        self,
        variant_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate statistical significance using chi-square test
        
        Returns:
            P-value (significance level)
        """
        if len(variant_results) < 2:
            return 0.0
        
        # Get control and variant data
        control = variant_results.get("control", {})
        variants = {k: v for k, v in variant_results.items() if k != "control"}
        
        if not variants:
            return 0.0
        
        # Use first variant for comparison
        variant_name = list(variants.keys())[0]
        variant = variants[variant_name]
        
        # Chi-square test
        control_conversions = control.get("conversions", 0)
        control_non_conversions = control.get("total_users", 0) - control_conversions
        
        variant_conversions = variant.get("conversions", 0)
        variant_non_conversions = variant.get("total_users", 0) - variant_conversions
        
        # Calculate chi-square statistic
        total_conversions = control_conversions + variant_conversions
        total_non_conversions = control_non_conversions + variant_non_conversions
        total_users = total_conversions + total_non_conversions
        
        if total_users == 0:
            return 0.0
        
        expected_control_conversions = (control_conversions + control_non_conversions) * total_conversions / total_users
        expected_variant_conversions = (variant_conversions + variant_non_conversions) * total_conversions / total_users
        
        chi_square = (
            ((control_conversions - expected_control_conversions) ** 2) / expected_control_conversions +
            ((variant_conversions - expected_variant_conversions) ** 2) / expected_variant_conversions
        )
        
        # Convert to p-value (simplified - in production, use proper chi-square distribution)
        # For 1 degree of freedom, p < 0.05 if chi-square > 3.84
        if chi_square > 3.84:
            return 0.95  # 95% confidence
        elif chi_square > 2.71:
            return 0.90  # 90% confidence
        else:
            return 0.0
    
    def _determine_winner(
        self,
        variant_results: Dict[str, Dict[str, Any]],
        significance: float
    ) -> Optional[str]:
        """Determine experiment winner"""
        if significance < 0.95:  # Need 95% confidence
            return None
        
        # Find variant with highest conversion rate
        best_variant = None
        best_rate = 0.0
        
        for variant_name, results in variant_results.items():
            if variant_name == "control":
                continue
            
            rate = results.get("conversion_rate", 0.0)
            if rate > best_rate:
                best_rate = rate
                best_variant = variant_name
        
        # Compare to control
        control_rate = variant_results.get("control", {}).get("conversion_rate", 0.0)
        
        if best_variant and best_rate > control_rate:
            return best_variant
        
        return None
    
    async def start_experiment(
        self,
        tenant_id: str,
        experiment_id: str,
        start_date: Optional[datetime] = None
    ) -> bool:
        """Start experiment"""
        start = start_date or datetime.now(timezone.utc)
        
        await self.postgres.execute(
            """
            UPDATE experiments
            SET status = $1, start_date = $2, updated_at = NOW()
            WHERE tenant_id = $3 AND experiment_id = $4
            """,
            ExperimentStatus.RUNNING.value, start, tenant_id, experiment_id
        )
        
        return True
    
    async def stop_experiment(
        self,
        tenant_id: str,
        experiment_id: str,
        end_date: Optional[datetime] = None
    ) -> ExperimentResult:
        """Stop experiment and analyze results"""
        end = end_date or datetime.now(timezone.utc)
        
        await self.postgres.execute(
            """
            UPDATE experiments
            SET status = $1, end_date = $2, updated_at = NOW()
            WHERE tenant_id = $3 AND experiment_id = $4
            """,
            ExperimentStatus.COMPLETED.value, end, tenant_id, experiment_id
        )
        
        # Analyze results
        return await self.analyze_experiment(tenant_id, experiment_id)

"""
Predictive Agent Scoring Module

Predictive scoring for:
- ROI potential
- Workload impact
- Ease of use
- Value creation

Ensures all user groups are considered, not just a single perspective.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import UserManager
from src.feedback.kpi_dashboard import KPIDashboardAggregator

logger = logging.getLogger(__name__)


class ScoreDimension(Enum):
    """Scoring dimensions"""
    ROI = "roi"
    WORKLOAD = "workload"
    EASE_OF_USE = "ease_of_use"
    VALUE_CREATION = "value_creation"


class PersonaGroup(Enum):
    """Persona groups"""
    SOLO_PODCASTER = "solo_podcaster"
    PRODUCER = "producer"
    AGENCY = "agency"
    BRAND = "brand"
    DATA_MARKETER = "data_marketer"
    PLATFORM_ADMIN = "platform_admin"


@dataclass
class FeatureScore:
    """Feature scoring result"""
    feature_id: str
    feature_name: str
    roi_score: float  # 0-100
    workload_score: float  # 0-100 (lower is better)
    ease_of_use_score: float  # 0-100
    value_creation_score: float  # 0-100
    overall_score: float  # Weighted average
    by_persona: Dict[str, Dict[str, float]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    scored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PersonaScore:
    """Persona-specific scoring"""
    persona: str
    roi_score: float
    workload_score: float
    ease_of_use_score: float
    value_creation_score: float
    overall_score: float
    feature_scores: Dict[str, float] = field(default_factory=dict)


class PredictiveScoringAgent:
    """
    Predictive Scoring Agent
    
    Scores features and changes across multiple dimensions for all personas.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        kpi_dashboard: KPIDashboardAggregator
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.kpi_dashboard = kpi_dashboard
        
        # Scoring weights (can be adjusted)
        self.scoring_weights = {
            ScoreDimension.ROI: 0.30,
            ScoreDimension.WORKLOAD: 0.20,
            ScoreDimension.EASE_OF_USE: 0.25,
            ScoreDimension.VALUE_CREATION: 0.25
        }
        
        # Persona-specific weights (different personas value different things)
        self.persona_weights = {
            PersonaGroup.SOLO_PODCASTER: {
                ScoreDimension.ROI: 0.25,
                ScoreDimension.WORKLOAD: 0.30,  # High weight - time is critical
                ScoreDimension.EASE_OF_USE: 0.30,  # High weight - low technical ability
                ScoreDimension.VALUE_CREATION: 0.15
            },
            PersonaGroup.PRODUCER: {
                ScoreDimension.ROI: 0.30,
                ScoreDimension.WORKLOAD: 0.25,  # Efficiency matters
                ScoreDimension.EASE_OF_USE: 0.20,
                ScoreDimension.VALUE_CREATION: 0.25
            },
            PersonaGroup.AGENCY: {
                ScoreDimension.ROI: 0.35,  # High weight - client retention
                ScoreDimension.WORKLOAD: 0.20,
                ScoreDimension.EASE_OF_USE: 0.15,
                ScoreDimension.VALUE_CREATION: 0.30  # High weight - differentiation
            },
            PersonaGroup.BRAND: {
                ScoreDimension.ROI: 0.40,  # Highest weight - ROI proof critical
                ScoreDimension.WORKLOAD: 0.15,
                ScoreDimension.EASE_OF_USE: 0.20,
                ScoreDimension.VALUE_CREATION: 0.25
            },
            PersonaGroup.DATA_MARKETER: {
                ScoreDimension.ROI: 0.30,
                ScoreDimension.WORKLOAD: 0.15,
                ScoreDimension.EASE_OF_USE: 0.15,  # Lower weight - technical user
                ScoreDimension.VALUE_CREATION: 0.40  # Highest weight - data quality
            },
            PersonaGroup.PLATFORM_ADMIN: {
                ScoreDimension.ROI: 0.25,
                ScoreDimension.WORKLOAD: 0.25,
                ScoreDimension.EASE_OF_USE: 0.20,
                ScoreDimension.VALUE_CREATION: 0.30
            }
        }
        
        self._feature_scores: Dict[str, FeatureScore] = {}
        
    async def score_feature(
        self,
        feature_id: str,
        feature_name: str,
        feature_metadata: Dict[str, Any],
        include_all_personas: bool = True
    ) -> FeatureScore:
        """
        Score a feature across all dimensions and personas
        
        Args:
            feature_id: Feature identifier
            feature_name: Feature name
            feature_metadata: Feature metadata (complexity, estimated_roi, etc.)
            include_all_personas: If True, score for all personas
            
        Returns:
            FeatureScore with comprehensive scoring
        """
        # Score each dimension
        roi_score = await self._score_roi(feature_metadata)
        workload_score = await self._score_workload(feature_metadata)
        ease_of_use_score = await self._score_ease_of_use(feature_metadata)
        value_creation_score = await self._score_value_creation(feature_metadata)
        
        # Calculate overall score using default weights
        overall_score = (
            roi_score * self.scoring_weights[ScoreDimension.ROI] +
            (100 - workload_score) * self.scoring_weights[ScoreDimension.WORKLOAD] +  # Invert workload (lower is better)
            ease_of_use_score * self.scoring_weights[ScoreDimension.EASE_OF_USE] +
            value_creation_score * self.scoring_weights[ScoreDimension.VALUE_CREATION]
        )
        
        # Score by persona
        by_persona = {}
        if include_all_personas:
            for persona in PersonaGroup:
                persona_weights = self.persona_weights.get(persona, self.scoring_weights)
                
                persona_overall = (
                    roi_score * persona_weights[ScoreDimension.ROI] +
                    (100 - workload_score) * persona_weights[ScoreDimension.WORKLOAD] +
                    ease_of_use_score * persona_weights[ScoreDimension.EASE_OF_USE] +
                    value_creation_score * persona_weights[ScoreDimension.VALUE_CREATION]
                )
                
                by_persona[persona.value] = {
                    "roi_score": roi_score,
                    "workload_score": workload_score,
                    "ease_of_use_score": ease_of_use_score,
                    "value_creation_score": value_creation_score,
                    "overall_score": persona_overall
                }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            roi_score,
            workload_score,
            ease_of_use_score,
            value_creation_score,
            by_persona
        )
        
        score = FeatureScore(
            feature_id=feature_id,
            feature_name=feature_name,
            roi_score=roi_score,
            workload_score=workload_score,
            ease_of_use_score=ease_of_use_score,
            value_creation_score=value_creation_score,
            overall_score=overall_score,
            by_persona=by_persona,
            recommendations=recommendations
        )
        
        self._feature_scores[feature_id] = score
        
        # Record metrics
        self.metrics.record_gauge(
            "feature_score_overall",
            overall_score,
            tags={"feature_id": feature_id}
        )
        
        self.metrics.record_gauge(
            "feature_score_roi",
            roi_score,
            tags={"feature_id": feature_id}
        )
        
        await self.events.log_event(
            event_type="feature_scored",
            user_id=None,
            properties={
                "feature_id": feature_id,
                "feature_name": feature_name,
                "overall_score": overall_score,
                "roi_score": roi_score,
                "workload_score": workload_score,
                "ease_of_use_score": ease_of_use_score,
                "value_creation_score": value_creation_score
            }
        )
        
        return score
    
    async def _score_roi(self, metadata: Dict[str, Any]) -> float:
        """Score ROI potential (0-100)"""
        # Factors:
        # - Estimated revenue impact
        # - Conversion potential
        # - Retention impact
        # - Upsell potential
        
        estimated_revenue_impact = metadata.get("estimated_revenue_impact", 0)
        conversion_potential = metadata.get("conversion_potential", 0.5)
        retention_impact = metadata.get("retention_impact", 0.5)
        upsell_potential = metadata.get("upsell_potential", 0.5)
        
        # Normalize revenue impact (0-100 scale)
        revenue_score = min(estimated_revenue_impact / 10000 * 50, 50)  # $10k = 50 points
        
        # Combine factors
        roi_score = (
            revenue_score +
            conversion_potential * 20 +
            retention_impact * 15 +
            upsell_potential * 15
        )
        
        return min(max(roi_score, 0), 100)
    
    async def _score_workload(self, metadata: Dict[str, Any]) -> float:
        """Score workload impact (0-100, lower is better)"""
        # Factors:
        # - Development complexity
        # - Maintenance burden
        # - Support load
        # - Operational overhead
        
        complexity = metadata.get("complexity", 0.5)  # 0-1
        maintenance_burden = metadata.get("maintenance_burden", 0.5)
        support_load = metadata.get("estimated_support_load", 0.5)
        operational_overhead = metadata.get("operational_overhead", 0.5)
        
        workload_score = (
            complexity * 30 +
            maintenance_burden * 25 +
            support_load * 25 +
            operational_overhead * 20
        )
        
        return min(max(workload_score, 0), 100)
    
    async def _score_ease_of_use(self, metadata: Dict[str, Any]) -> float:
        """Score ease of use (0-100)"""
        # Factors:
        # - UI/UX complexity
        # - Learning curve
        # - Documentation quality
        # - Onboarding difficulty
        
        ui_complexity = 1.0 - metadata.get("ui_complexity", 0.5)  # Invert (lower complexity = higher score)
        learning_curve = 1.0 - metadata.get("learning_curve", 0.5)
        documentation_quality = metadata.get("documentation_quality", 0.5)
        onboarding_difficulty = 1.0 - metadata.get("onboarding_difficulty", 0.5)
        
        ease_score = (
            ui_complexity * 30 +
            learning_curve * 30 +
            documentation_quality * 20 +
            onboarding_difficulty * 20
        ) * 100
        
        return min(max(ease_score, 0), 100)
    
    async def _score_value_creation(self, metadata: Dict[str, Any]) -> float:
        """Score value creation (0-100)"""
        # Factors:
        # - User satisfaction impact
        # - Time savings
        # - Problem solving capability
        # - Competitive advantage
        
        satisfaction_impact = metadata.get("satisfaction_impact", 0.5)
        time_savings = metadata.get("time_savings_hours_per_month", 0) / 40  # Normalize to 40 hours/month
        problem_solving = metadata.get("problem_solving_capability", 0.5)
        competitive_advantage = metadata.get("competitive_advantage", 0.5)
        
        value_score = (
            satisfaction_impact * 30 +
            min(time_savings, 1.0) * 30 +
            problem_solving * 20 +
            competitive_advantage * 20
        ) * 100
        
        return min(max(value_score, 0), 100)
    
    def _generate_recommendations(
        self,
        roi_score: float,
        workload_score: float,
        ease_of_use_score: float,
        value_creation_score: float,
        by_persona: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """Generate recommendations based on scores"""
        recommendations = []
        
        if roi_score < 50:
            recommendations.append("Consider ROI optimization - feature may not drive sufficient revenue")
        
        if workload_score > 70:
            recommendations.append("High workload impact - consider simplifying or automating")
        
        if ease_of_use_score < 60:
            recommendations.append("Ease of use concerns - improve UX/onboarding")
        
        if value_creation_score < 50:
            recommendations.append("Low value creation - reconsider feature priority")
        
        # Check persona-specific concerns
        low_scoring_personas = [
            persona for persona, scores in by_persona.items()
            if scores.get("overall_score", 0) < 60
        ]
        
        if low_scoring_personas:
            recommendations.append(
                f"Low scores for personas: {', '.join(low_scoring_personas)} - "
                "consider persona-specific improvements"
            )
        
        return recommendations
    
    async def compare_features(
        self,
        feature_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple features"""
        scores = []
        for feature_id in feature_ids:
            score = self._feature_scores.get(feature_id)
            if score:
                scores.append(score)
        
        if not scores:
            return {"error": "No scores found for provided feature IDs"}
        
        # Rank by overall score
        ranked = sorted(scores, key=lambda s: s.overall_score, reverse=True)
        
        # Find best/worst by persona
        persona_rankings = {}
        for persona in PersonaGroup:
            persona_scores = [
                (s.feature_id, s.by_persona.get(persona.value, {}).get("overall_score", 0))
                for s in scores
                if persona.value in s.by_persona
            ]
            persona_scores.sort(key=lambda x: x[1], reverse=True)
            persona_rankings[persona.value] = persona_scores
        
        return {
            "overall_ranking": [
                {
                    "feature_id": s.feature_id,
                    "feature_name": s.feature_name,
                    "overall_score": s.overall_score
                }
                for s in ranked
            ],
            "by_persona": persona_rankings,
            "summary": {
                "total_features": len(scores),
                "avg_score": sum(s.overall_score for s in scores) / len(scores),
                "highest_score": ranked[0].overall_score if ranked else 0,
                "lowest_score": ranked[-1].overall_score if ranked else 0
            }
        }
    
    async def get_feature_score(self, feature_id: str) -> Optional[FeatureScore]:
        """Get feature score by ID"""
        return self._feature_scores.get(feature_id)
    
    async def score_feature_roadmap(
        self,
        roadmap_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Score entire feature roadmap
        
        Ensures all personas are considered in prioritization.
        """
        scored_features = []
        
        for feature in roadmap_features:
            score = await self.score_feature(
                feature_id=feature.get("feature_id", str(uuid4())),
                feature_name=feature.get("name", "Unknown"),
                feature_metadata=feature.get("metadata", {})
            )
            scored_features.append(score)
        
        # Check if any persona is consistently low-scoring
        persona_concerns = {}
        for persona in PersonaGroup:
            persona_scores = [
                s.by_persona.get(persona.value, {}).get("overall_score", 0)
                for s in scored_features
            ]
            avg_score = sum(persona_scores) / len(persona_scores) if persona_scores else 0
            
            if avg_score < 60:
                persona_concerns[persona.value] = {
                    "avg_score": avg_score,
                    "message": f"Roadmap may not adequately serve {persona.value} persona"
                }
        
        return {
            "scored_features": [
                {
                    "feature_id": s.feature_id,
                    "feature_name": s.feature_name,
                    "overall_score": s.overall_score,
                    "recommendations": s.recommendations
                }
                for s in scored_features
            ],
            "persona_concerns": persona_concerns,
            "recommendations": [
                "Ensure roadmap balances needs across all personas",
                "Prioritize features that score well across multiple personas",
                "Address persona-specific concerns proactively"
            ]
        }

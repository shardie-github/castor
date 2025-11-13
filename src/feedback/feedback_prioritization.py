"""
Feedback Prioritization Engine

Prioritizes and optimizes feedback based on:
- User impact
- Business value
- Implementation effort
- User requests (upvotes, frequency)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.feedback.in_app_feedback import InAppFeedback, FeedbackType, FeedbackPriority
from src.feedback.user_research import ResearchSession

logger = logging.getLogger(__name__)


class PriorityScore(Enum):
    """Priority score levels"""
    CRITICAL = "critical"  # 90-100
    HIGH = "high"  # 70-89
    MEDIUM = "medium"  # 40-69
    LOW = "low"  # 0-39


@dataclass
class PrioritizedFeedback:
    """Prioritized feedback item"""
    feedback_id: str
    feedback_type: FeedbackType
    priority_score: float  # 0-100
    priority_level: PriorityScore
    user_impact: float  # Estimated user impact (0-100)
    business_value: float  # Estimated business value (0-100)
    implementation_effort: float  # Estimated effort (0-100, higher = more effort)
    upvotes: int
    request_frequency: int  # How many times this was requested
    affected_personas: List[str]
    related_features: List[str]
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackPrioritizationEngine:
    """
    Feedback Prioritization Engine
    
    Prioritizes feedback based on multiple factors and generates optimization recommendations.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        
    def calculate_priority_score(
        self,
        feedback: InAppFeedback,
        request_frequency: int = 1,
        affected_personas: Optional[List[str]] = None,
        implementation_effort: Optional[float] = None
    ) -> PrioritizedFeedback:
        """Calculate priority score for feedback"""
        
        # User Impact Score (0-100)
        # Based on: upvotes, request frequency, affected personas
        user_impact = self._calculate_user_impact(
            feedback.upvotes,
            request_frequency,
            affected_personas or []
        )
        
        # Business Value Score (0-100)
        # Based on: feedback type, priority, NPS impact
        business_value = self._calculate_business_value(
            feedback.feedback_type,
            feedback.priority,
            feedback.nps_score
        )
        
        # Implementation Effort (0-100, higher = more effort)
        # If not provided, estimate based on feedback type
        if implementation_effort is None:
            implementation_effort = self._estimate_implementation_effort(
                feedback.feedback_type,
                feedback.content
            )
        
        # Priority Score = (User Impact * 0.4 + Business Value * 0.4) / (Implementation Effort * 0.2 + 1)
        # Higher score = higher priority
        priority_score = (
            (user_impact * 0.4 + business_value * 0.4) /
            (implementation_effort * 0.2 + 1)
        )
        
        # Normalize to 0-100
        priority_score = min(100, max(0, priority_score))
        
        # Determine priority level
        if priority_score >= 90:
            priority_level = PriorityScore.CRITICAL
        elif priority_score >= 70:
            priority_level = PriorityScore.HIGH
        elif priority_score >= 40:
            priority_level = PriorityScore.MEDIUM
        else:
            priority_level = PriorityScore.LOW
        
        return PrioritizedFeedback(
            feedback_id=feedback.feedback_id,
            feedback_type=feedback.feedback_type,
            priority_score=priority_score,
            priority_level=priority_level,
            user_impact=user_impact,
            business_value=business_value,
            implementation_effort=implementation_effort,
            upvotes=feedback.upvotes,
            request_frequency=request_frequency,
            affected_personas=affected_personas or [],
            related_features=[feedback.feature_name] if feedback.feature_name else [],
            created_at=feedback.created_at
        )
    
    def _calculate_user_impact(
        self,
        upvotes: int,
        request_frequency: int,
        affected_personas: List[str]
    ) -> float:
        """Calculate user impact score"""
        # Upvotes contribute up to 40 points
        upvote_score = min(40, upvotes * 2)
        
        # Request frequency contributes up to 30 points
        frequency_score = min(30, request_frequency * 3)
        
        # Affected personas contribute up to 30 points
        # More personas = higher impact
        persona_score = min(30, len(affected_personas) * 10)
        
        return upvote_score + frequency_score + persona_score
    
    def _calculate_business_value(
        self,
        feedback_type: FeedbackType,
        priority: FeedbackPriority,
        nps_score: Optional[int]
    ) -> float:
        """Calculate business value score"""
        # Base value by feedback type
        type_values = {
            FeedbackType.BUG_REPORT: 80,
            FeedbackType.FEATURE_REQUEST: 60,
            FeedbackType.NPS: 50,
            FeedbackType.GENERAL_FEEDBACK: 40,
            FeedbackType.SUPPORT_TICKET: 70
        }
        
        base_value = type_values.get(feedback_type, 50)
        
        # Adjust by priority
        priority_multipliers = {
            FeedbackPriority.CRITICAL: 1.2,
            FeedbackPriority.HIGH: 1.1,
            FeedbackPriority.MEDIUM: 1.0,
            FeedbackPriority.LOW: 0.9
        }
        
        base_value *= priority_multipliers.get(priority, 1.0)
        
        # Adjust by NPS score (low NPS = higher value to fix)
        if nps_score is not None:
            if nps_score <= 3:
                base_value *= 1.3  # High value to address detractors
            elif nps_score <= 6:
                base_value *= 1.1
        
        return min(100, base_value)
    
    def _estimate_implementation_effort(
        self,
        feedback_type: FeedbackType,
        content: str
    ) -> float:
        """Estimate implementation effort (higher = more effort)"""
        content_lower = content.lower()
        
        # Base effort by type
        type_efforts = {
            FeedbackType.BUG_REPORT: 30,  # Usually lower effort
            FeedbackType.FEATURE_REQUEST: 60,  # Usually higher effort
            FeedbackType.NPS: 0,  # No implementation needed
            FeedbackType.GENERAL_FEEDBACK: 40,
            FeedbackType.SUPPORT_TICKET: 20  # Usually documentation/process
        }
        
        base_effort = type_efforts.get(feedback_type, 50)
        
        # Adjust based on keywords
        if any(keyword in content_lower for keyword in ["simple", "easy", "quick", "minor"]):
            base_effort *= 0.7
        
        if any(keyword in content_lower for keyword in ["complex", "major", "rewrite", "redesign"]):
            base_effort *= 1.5
        
        return min(100, base_effort)
    
    async def prioritize_feedback_batch(
        self,
        feedback_list: List[InAppFeedback],
        request_frequencies: Optional[Dict[str, int]] = None
    ) -> List[PrioritizedFeedback]:
        """Prioritize a batch of feedback items"""
        request_frequencies = request_frequencies or {}
        
        prioritized = []
        for feedback in feedback_list:
            request_freq = request_frequencies.get(feedback.feedback_id, 1)
            
            prioritized_item = self.calculate_priority_score(
                feedback,
                request_frequency=request_freq
            )
            
            prioritized.append(prioritized_item)
        
        # Sort by priority score (highest first)
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)
        
        return prioritized
    
    async def generate_optimization_recommendations(
        self,
        prioritized_feedback: List[PrioritizedFeedback],
        research_sessions: Optional[List[ResearchSession]] = None
    ) -> Dict[str, Any]:
        """Generate optimization recommendations based on prioritized feedback"""
        recommendations = {
            "immediate_actions": [],
            "short_term_roadmap": [],
            "long_term_considerations": [],
            "insights": []
        }
        
        # Immediate actions (critical priority)
        critical_items = [
            f for f in prioritized_feedback
            if f.priority_level == PriorityScore.CRITICAL
        ]
        
        for item in critical_items[:5]:  # Top 5 critical items
            recommendations["immediate_actions"].append({
                "feedback_id": item.feedback_id,
                "type": item.feedback_type.value,
                "priority_score": item.priority_score,
                "reason": f"Critical priority with score {item.priority_score:.1f}",
                "affected_personas": item.affected_personas,
                "estimated_effort": item.implementation_effort
            })
        
        # Short-term roadmap (high priority, reasonable effort)
        high_priority_items = [
            f for f in prioritized_feedback
            if f.priority_level == PriorityScore.HIGH
            and f.implementation_effort < 70  # Reasonable effort
        ]
        
        for item in high_priority_items[:10]:  # Top 10 high priority items
            recommendations["short_term_roadmap"].append({
                "feedback_id": item.feedback_id,
                "type": item.feedback_type.value,
                "priority_score": item.priority_score,
                "user_impact": item.user_impact,
                "business_value": item.business_value,
                "estimated_effort": item.implementation_effort
            })
        
        # Long-term considerations (high value, high effort)
        long_term_items = [
            f for f in prioritized_feedback
            if f.priority_level in [PriorityScore.HIGH, PriorityScore.MEDIUM]
            and f.implementation_effort >= 70
            and f.business_value >= 60
        ]
        
        for item in long_term_items[:5]:  # Top 5 long-term items
            recommendations["long_term_considerations"].append({
                "feedback_id": item.feedback_id,
                "type": item.feedback_type.value,
                "priority_score": item.priority_score,
                "business_value": item.business_value,
                "estimated_effort": item.implementation_effort,
                "rationale": "High business value but requires significant effort"
            })
        
        # Generate insights
        if prioritized_feedback:
            top_feedback_type = max(
                set(f.feedback_type for f in prioritized_feedback[:10]),
                key=lambda t: sum(1 for f in prioritized_feedback[:10] if f.feedback_type == t)
            )
            recommendations["insights"].append(
                f"Most common feedback type in top priorities: {top_feedback_type.value}"
            )
        
        # Research insights
        if research_sessions:
            pain_points = []
            for session in research_sessions:
                pain_points.extend(session.pain_points)
            
            if pain_points:
                # Find most common pain point
                from collections import Counter
                pain_point_counts = Counter(pain_points)
                top_pain_point = pain_point_counts.most_common(1)[0]
                recommendations["insights"].append(
                    f"Top pain point from research: {top_pain_point[0]} (mentioned {top_pain_point[1]} times)"
                )
        
        return recommendations

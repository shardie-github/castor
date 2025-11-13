"""
In-App Feedback Channels

Implements:
- In-app NPS prompts
- Feature request collection
- Support ticket integration
- Feedback prioritization
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.measurement.continuous_metrics import ContinuousMeasurement
from src.operations.support import SupportIntegration, SupportChannel

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Feedback types"""
    NPS = "nps"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL_FEEDBACK = "general_feedback"
    SUPPORT_TICKET = "support_ticket"


class FeedbackPriority(Enum):
    """Feedback priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(Enum):
    """Feedback status"""
    NEW = "new"
    REVIEWED = "reviewed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


@dataclass
class InAppFeedback:
    """In-app feedback entry"""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    content: str
    priority: FeedbackPriority
    status: FeedbackStatus
    nps_score: Optional[int] = None  # 0-10 for NPS feedback
    feature_name: Optional[str] = None
    page_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    ticket_id: Optional[str] = None  # Linked support ticket
    upvotes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackPrompt:
    """In-app feedback prompt configuration"""
    prompt_id: str
    prompt_type: FeedbackType
    trigger_condition: Dict[str, Any]  # When to show prompt
    title: str
    message: str
    enabled: bool = True
    frequency: str = "once_per_user"  # once_per_user, once_per_session, always
    target_personas: List[str] = field(default_factory=list)  # Empty = all personas


class InAppFeedbackSystem:
    """
    In-App Feedback System
    
    Manages in-app feedback collection, NPS prompts, and feature requests.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        measurement: ContinuousMeasurement,
        support_integration: SupportIntegration
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.measurement = measurement
        self.support = support_integration
        self._feedback: Dict[str, InAppFeedback] = {}
        self._prompts: Dict[str, FeedbackPrompt] = {}
        self._user_prompt_history: Dict[str, List[str]] = {}  # user_id -> prompt_ids shown
        self._initialize_default_prompts()
        
    def _initialize_default_prompts(self):
        """Initialize default feedback prompts"""
        # NPS prompt after first report
        nps_prompt = FeedbackPrompt(
            prompt_id="nps_first_report",
            prompt_type=FeedbackType.NPS,
            trigger_condition={
                "event": "report_generated",
                "count": 1  # First report
            },
            title="How likely are you to recommend us?",
            message="Your feedback helps us improve!",
            frequency="once_per_user"
        )
        self._prompts[nps_prompt.prompt_id] = nps_prompt
        
        # Feature request prompt
        feature_request_prompt = FeedbackPrompt(
            prompt_id="feature_request_general",
            prompt_type=FeedbackType.FEATURE_REQUEST,
            trigger_condition={
                "event": "feature_request_clicked"
            },
            title="Request a Feature",
            message="What feature would make your experience better?",
            frequency="always"
        )
        self._prompts[feature_request_prompt.prompt_id] = feature_request_prompt
        
    async def should_show_prompt(
        self,
        user_id: str,
        event_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[FeedbackPrompt]:
        """Check if a feedback prompt should be shown"""
        context = context or {}
        
        for prompt in self._prompts.values():
            if not prompt.enabled:
                continue
            
            # Check frequency
            if prompt.frequency == "once_per_user":
                user_history = self._user_prompt_history.get(user_id, [])
                if prompt.prompt_id in user_history:
                    continue
            
            # Check trigger condition
            condition = prompt.trigger_condition
            if condition.get("event") == event_type:
                # Check count if specified
                if "count" in condition:
                    event_count = context.get("event_count", 0)
                    if event_count != condition["count"]:
                        continue
                
                # Mark as shown
                if user_id not in self._user_prompt_history:
                    self._user_prompt_history[user_id] = []
                self._user_prompt_history[user_id].append(prompt.prompt_id)
                
                return prompt
        
        return None
    
    async def submit_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        content: str,
        nps_score: Optional[int] = None,
        feature_name: Optional[str] = None,
        page_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_create_ticket: bool = False
    ) -> InAppFeedback:
        """Submit in-app feedback"""
        feedback_id = str(uuid4())
        
        # Determine priority
        priority = self._determine_priority(feedback_type, content, nps_score)
        
        feedback = InAppFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            feedback_type=feedback_type,
            content=content,
            priority=priority,
            status=FeedbackStatus.NEW,
            nps_score=nps_score,
            feature_name=feature_name,
            page_url=page_url,
            tags=tags or []
        )
        
        self._feedback[feedback_id] = feedback
        
        # Record NPS if provided
        if nps_score is not None:
            await self.measurement.record_satisfaction(
                user_id=user_id,
                score=nps_score,
                feature=feature_name,
                page=page_url,
                feedback=content
            )
        
        # Create support ticket if requested
        if auto_create_ticket and feedback_type in [
            FeedbackType.BUG_REPORT,
            FeedbackType.SUPPORT_TICKET
        ]:
            ticket = await self.support.create_ticket(
                user_id=user_id,
                channel=SupportChannel.IN_APP,
                subject=f"{feedback_type.value}: {content[:50]}",
                description=content,
                priority=self._convert_priority(feedback.priority),
                tags=feedback.tags
            )
            feedback.ticket_id = ticket.ticket_id
        
        # Record metrics
        self.metrics.increment_counter(
            "in_app_feedback_submitted",
            tags={
                "feedback_type": feedback_type.value,
                "priority": priority.value
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="in_app_feedback_submitted",
            user_id=user_id,
            properties={
                "feedback_id": feedback_id,
                "feedback_type": feedback_type.value,
                "nps_score": nps_score,
                "feature_name": feature_name
            }
        )
        
        return feedback
    
    def _determine_priority(
        self,
        feedback_type: FeedbackType,
        content: str,
        nps_score: Optional[int] = None
    ) -> FeedbackPriority:
        """Determine feedback priority"""
        content_lower = content.lower()
        
        # Critical keywords
        if any(keyword in content_lower for keyword in [
            "critical", "broken", "down", "error", "cannot", "urgent"
        ]):
            return FeedbackPriority.CRITICAL
        
        # Low NPS score
        if nps_score is not None and nps_score <= 3:
            return FeedbackPriority.HIGH
        
        # Bug reports are high priority
        if feedback_type == FeedbackType.BUG_REPORT:
            return FeedbackPriority.HIGH
        
        # Default to medium
        return FeedbackPriority.MEDIUM
    
    def _convert_priority(
        self,
        priority: FeedbackPriority
    ):
        """Convert feedback priority to ticket priority"""
        from src.operations.support import TicketPriority
        
        mapping = {
            FeedbackPriority.CRITICAL: TicketPriority.CRITICAL,
            FeedbackPriority.HIGH: TicketPriority.HIGH,
            FeedbackPriority.MEDIUM: TicketPriority.MEDIUM,
            FeedbackPriority.LOW: TicketPriority.LOW
        }
        
        return mapping.get(priority, TicketPriority.MEDIUM)
    
    async def upvote_feedback(
        self,
        feedback_id: str,
        user_id: str
    ) -> InAppFeedback:
        """Upvote a feedback entry"""
        feedback = self._feedback.get(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")
        
        feedback.upvotes += 1
        
        # Log event
        await self.events.log_event(
            event_type="feedback_upvoted",
            user_id=user_id,
            properties={
                "feedback_id": feedback_id,
                "upvotes": feedback.upvotes
            }
        )
        
        return feedback
    
    async def prioritize_feedback(
        self,
        days: int = 30
    ) -> List[InAppFeedback]:
        """Prioritize feedback based on upvotes, priority, and recency"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        feedback_list = [
            f for f in self._feedback.values()
            if f.created_at >= cutoff_date
            and f.status in [FeedbackStatus.NEW, FeedbackStatus.REVIEWED]
        ]
        
        # Sort by priority score
        def priority_score(f: InAppFeedback) -> float:
            priority_weights = {
                FeedbackPriority.CRITICAL: 100,
                FeedbackPriority.HIGH: 50,
                FeedbackPriority.MEDIUM: 25,
                FeedbackPriority.LOW: 10
            }
            
            priority_weight = priority_weights.get(f.priority, 0)
            upvote_weight = f.upvotes * 5
            recency_weight = (datetime.now(timezone.utc) - f.created_at).days * -1
            
            return priority_weight + upvote_weight + recency_weight
        
        feedback_list.sort(key=priority_score, reverse=True)
        
        return feedback_list
    
    async def get_feedback_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get feedback summary"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        feedback_list = [
            f for f in self._feedback.values()
            if f.created_at >= cutoff_date
        ]
        
        # Aggregate by type
        by_type = {}
        for feedback_type in FeedbackType:
            type_feedback = [f for f in feedback_list if f.feedback_type == feedback_type]
            by_type[feedback_type.value] = {
                "count": len(type_feedback),
                "avg_nps": sum(f.nps_score for f in type_feedback if f.nps_score) / len([f for f in type_feedback if f.nps_score]) if any(f.nps_score for f in type_feedback) else 0
            }
        
        # Top feature requests
        feature_requests = [
            f for f in feedback_list
            if f.feedback_type == FeedbackType.FEATURE_REQUEST
        ]
        feature_requests.sort(key=lambda f: f.upvotes, reverse=True)
        
        return {
            "period_days": days,
            "total_feedback": len(feedback_list),
            "by_type": by_type,
            "top_feature_requests": [
                {
                    "feedback_id": f.feedback_id,
                    "content": f.content[:100],
                    "upvotes": f.upvotes,
                    "created_at": f.created_at.isoformat()
                }
                for f in feature_requests[:10]
            ],
            "prioritized_feedback": [
                {
                    "feedback_id": f.feedback_id,
                    "type": f.feedback_type.value,
                    "priority": f.priority.value,
                    "upvotes": f.upvotes,
                    "content": f.content[:100]
                }
                for f in await self.prioritize_feedback(days=days)[:20]
            ]
        }
    
    def get_feedback(self, feedback_id: str) -> Optional[InAppFeedback]:
        """Get feedback by ID"""
        return self._feedback.get(feedback_id)
    
    async def update_feedback_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
        reviewed_by: Optional[str] = None
    ) -> InAppFeedback:
        """Update feedback status"""
        feedback = self._feedback.get(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")
        
        feedback.status = status
        feedback.reviewed_at = datetime.now(timezone.utc)
        feedback.reviewed_by = reviewed_by
        
        # Log event
        await self.events.log_event(
            event_type="feedback_status_updated",
            user_id=reviewed_by,
            properties={
                "feedback_id": feedback_id,
                "status": status.value
            }
        )
        
        return feedback

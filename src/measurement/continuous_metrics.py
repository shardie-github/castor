"""
Continuous Measurement Framework

Implements in-line metrics for usage, satisfaction, and ease:
- NPS (Net Promoter Score)
- Time to complete tasks
- Success/failure rates
- Feature usage tracking
- User satisfaction scores
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task completion status"""
    SUCCESS = "success"
    FAILURE = "failure"
    ABANDONED = "abandoned"
    IN_PROGRESS = "in_progress"


@dataclass
class TaskMetric:
    """Task completion metric"""
    task_id: str
    user_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.IN_PROGRESS
    time_to_complete: Optional[float] = None  # seconds
    attempts: int = 1
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SatisfactionScore:
    """User satisfaction score"""
    score_id: str
    user_id: str
    feature: Optional[str] = None
    page: Optional[str] = None
    score: int = 0  # 1-10 scale
    nps_score: Optional[int] = None  # -100 to 100
    feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ContinuousMeasurement:
    """
    Continuous Measurement Framework
    
    Tracks usage, satisfaction, and ease metrics for all features.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._active_tasks: Dict[str, TaskMetric] = {}
        self._task_history: List[TaskMetric] = []
        self._satisfaction_scores: List[SatisfactionScore] = []
        
    def start_task(
        self,
        user_id: str,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a task
        
        Returns:
            task_id for tracking
        """
        task_id = str(uuid4())
        
        task = TaskMetric(
            task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            start_time=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self._active_tasks[task_id] = task
        
        # Log event
        asyncio.create_task(self.events.log_event(
            event_type="task_started",
            user_id=user_id,
            properties={
                "task_id": task_id,
                "task_type": task_type,
                "metadata": metadata
            }
        ))
        
        return task_id
    
    def complete_task(
        self,
        task_id: str,
        status: TaskStatus = TaskStatus.SUCCESS,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskMetric]:
        """
        Complete a task and record metrics
        
        Returns:
            Completed task metric
        """
        task = self._active_tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None
        
        task.end_time = datetime.now(timezone.utc)
        task.status = status
        task.error_message = error_message
        
        # Calculate time to complete
        task.time_to_complete = (task.end_time - task.start_time).total_seconds()
        
        # Update metadata
        if metadata:
            task.metadata.update(metadata)
        
        # Move to history
        self._task_history.append(task)
        del self._active_tasks[task_id]
        
        # Record metrics
        self.metrics.record_histogram(
            f"task_completion_time_{task.task_type}",
            task.time_to_complete,
            tags={"status": status.value, "user_id": task.user_id}
        )
        
        self.metrics.increment_counter(
            f"task_{status.value}_{task.task_type}",
            tags={"user_id": task.user_id}
        )
        
        # Calculate success rate
        success_rate = self._calculate_success_rate(task.task_type)
        self.metrics.record_gauge(
            f"task_success_rate_{task.task_type}",
            success_rate * 100,
            tags={}
        )
        
        # Log event
        asyncio.create_task(self.events.log_event(
            event_type="task_completed",
            user_id=task.user_id,
            properties={
                "task_id": task_id,
                "task_type": task.task_type,
                "status": status.value,
                "time_to_complete": task.time_to_complete,
                "success": status == TaskStatus.SUCCESS
            }
        ))
        
        return task
    
    def _calculate_success_rate(self, task_type: str) -> float:
        """Calculate success rate for a task type"""
        tasks = [t for t in self._task_history if t.task_type == task_type]
        if not tasks:
            return 0.0
        
        successful = len([t for t in tasks if t.status == TaskStatus.SUCCESS])
        return successful / len(tasks)
    
    async def record_satisfaction(
        self,
        user_id: str,
        score: int,
        feature: Optional[str] = None,
        page: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> SatisfactionScore:
        """
        Record user satisfaction score
        
        Args:
            user_id: User ID
            score: Satisfaction score (1-10)
            feature: Feature name if applicable
            page: Page/route if applicable
            feedback: Optional feedback text
        """
        score_id = str(uuid4())
        
        # Calculate NPS score (convert 1-10 to -100 to 100)
        # Promoters: 9-10, Passives: 7-8, Detractors: 1-6
        if score >= 9:
            nps_score = 100
        elif score >= 7:
            nps_score = 0
        else:
            nps_score = -100
        
        satisfaction = SatisfactionScore(
            score_id=score_id,
            user_id=user_id,
            feature=feature,
            page=page,
            score=score,
            nps_score=nps_score,
            feedback=feedback
        )
        
        self._satisfaction_scores.append(satisfaction)
        
        # Record metrics
        self.metrics.record_gauge(
            "user_satisfaction_score",
            score,
            tags={"feature": feature or "overall", "page": page or "none"}
        )
        
        if nps_score is not None:
            self.metrics.record_gauge(
                "nps_score",
                nps_score,
                tags={"feature": feature or "overall"}
            )
        
        # Log event
        await self.events.log_event(
            event_type="satisfaction_recorded",
            user_id=user_id,
            properties={
                "score_id": score_id,
                "score": score,
                "nps_score": nps_score,
                "feature": feature,
                "page": page
            },
            feature=feature,
            page=page
        )
        
        return satisfaction
    
    async def calculate_nps(
        self,
        feature: Optional[str] = None,
        days: int = 30
    ) -> float:
        """
        Calculate Net Promoter Score
        
        Args:
            feature: Feature name (None for overall)
            days: Number of days to look back
            
        Returns:
            NPS score (-100 to 100)
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        scores = [
            s for s in self._satisfaction_scores
            if s.timestamp >= cutoff_date
        ]
        
        if feature:
            scores = [s for s in scores if s.feature == feature]
        
        if not scores:
            return 0.0
        
        # Count promoters, passives, detractors
        promoters = len([s for s in scores if s.nps_score == 100])
        passives = len([s for s in scores if s.nps_score == 0])
        detractors = len([s for s in scores if s.nps_score == -100])
        
        total = len(scores)
        
        if total == 0:
            return 0.0
        
        # Calculate NPS: % Promoters - % Detractors
        nps = ((promoters - detractors) / total) * 100
        
        # Record metric
        self.metrics.record_gauge(
            "calculated_nps",
            nps,
            tags={"feature": feature or "overall", "days": str(days)}
        )
        
        return nps
    
    def get_task_statistics(
        self,
        task_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get task completion statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        tasks = [
            t for t in self._task_history
            if t.end_time and t.end_time >= cutoff_date
        ]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        if not tasks:
            return {
                "total": 0,
                "success_rate": 0.0,
                "avg_time_to_complete": 0.0,
                "failure_rate": 0.0
            }
        
        successful = [t for t in tasks if t.status == TaskStatus.SUCCESS]
        failed = [t for t in tasks if t.status == TaskStatus.FAILURE]
        
        completion_times = [
            t.time_to_complete for t in successful
            if t.time_to_complete is not None
        ]
        
        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0.0
        
        return {
            "total": len(tasks),
            "successful": len(successful),
            "failed": len(failed),
            "abandoned": len([t for t in tasks if t.status == TaskStatus.ABANDONED]),
            "success_rate": len(successful) / len(tasks) if tasks else 0.0,
            "failure_rate": len(failed) / len(tasks) if tasks else 0.0,
            "avg_time_to_complete": avg_time,
            "median_time_to_complete": sorted(completion_times)[len(completion_times) // 2] if completion_times else 0.0
        }
    
    def track_feature_usage(
        self,
        user_id: str,
        feature: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track feature usage"""
        self.metrics.increment_counter(
            "feature_usage",
            tags={"feature": feature, "action": action, "user_id": user_id}
        )
        
        asyncio.create_task(self.events.log_feature_usage(
            user_id=user_id,
            feature=feature,
            properties={
                "action": action,
                "metadata": metadata
            }
        ))


# Context manager for task tracking
class TaskTracker:
    """Context manager for automatic task tracking"""
    
    def __init__(
        self,
        measurement: ContinuousMeasurement,
        user_id: str,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.measurement = measurement
        self.user_id = user_id
        self.task_type = task_type
        self.metadata = metadata
        self.task_id = None
        
    def __enter__(self):
        self.task_id = self.measurement.start_task(
            self.user_id,
            self.task_type,
            self.metadata
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.task_id:
            if exc_type:
                self.measurement.complete_task(
                    self.task_id,
                    status=TaskStatus.FAILURE,
                    error_message=str(exc_val)
                )
            else:
                self.measurement.complete_task(
                    self.task_id,
                    status=TaskStatus.SUCCESS
                )


# Import asyncio for async operations
import asyncio

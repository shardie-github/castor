"""
Onboarding Automation Module

Automates user onboarding tasks:
- Welcome emails
- Initial setup guidance
- First campaign creation assistance
- Feature discovery
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import User

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Onboarding steps"""
    SIGNUP = "signup"
    EMAIL_VERIFIED = "email_verified"
    PODCAST_ADDED = "podcast_added"
    FIRST_CAMPAIGN = "first_campaign"
    FIRST_REPORT = "first_report"
    COMPLETED = "completed"


class OnboardingStatus(Enum):
    """Onboarding status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class OnboardingProgress:
    """User onboarding progress"""
    user_id: str
    status: OnboardingStatus
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep]
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class OnboardingAutomation:
    """
    Onboarding Automation
    
    Automates onboarding workflows:
    - Tracks user progress
    - Sends welcome emails
    - Provides setup guidance
    - Triggers feature discovery
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._progress: Dict[str, OnboardingProgress] = {}
    
    async def start_onboarding(self, user: User) -> OnboardingProgress:
        """Start onboarding process for a new user"""
        progress = OnboardingProgress(
            user_id=user.user_id,
            status=OnboardingStatus.IN_PROGRESS,
            current_step=OnboardingStep.SIGNUP,
            completed_steps=[OnboardingStep.SIGNUP],
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc),
            metadata={}
        )
        
        self._progress[user.user_id] = progress
        
        # Send welcome email
        await self._send_welcome_email(user)
        
        # Log event
        await self.events.log_event(
            event_type="onboarding_started",
            user_id=user.user_id,
            properties={
                "persona_segment": user.persona_segment,
                "subscription_tier": user.subscription_tier.value
            }
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "onboarding_started",
            tags={
                "persona": user.persona_segment or "unknown",
                "tier": user.subscription_tier.value
            }
        )
        
        return progress
    
    async def update_progress(
        self,
        user_id: str,
        step: OnboardingStep
    ) -> Optional[OnboardingProgress]:
        """Update onboarding progress"""
        progress = self._progress.get(user_id)
        if not progress:
            logger.warning(f"No onboarding progress found for user {user_id}")
            return None
        
        # Check if step is already completed
        if step in progress.completed_steps:
            return progress
        
        # Add step to completed
        progress.completed_steps.append(step)
        progress.current_step = step
        progress.last_activity_at = datetime.now(timezone.utc)
        
        # Check if onboarding is complete
        if step == OnboardingStep.COMPLETED:
            progress.status = OnboardingStatus.COMPLETED
            progress.completed_at = datetime.now(timezone.utc)
            
            # Send completion email
            user = await self._get_user(user_id)
            if user:
                await self._send_completion_email(user)
            
            # Record telemetry
            self.metrics.increment_counter(
                "onboarding_completed",
                tags={"user_id": user_id}
            )
            
            # Calculate time to complete
            duration_days = (progress.completed_at - progress.started_at).days
            self.metrics.record_histogram(
                "onboarding_duration_days",
                duration_days,
                tags={"user_id": user_id}
            )
        
        # Log event
        await self.events.log_event(
            event_type="onboarding_step_completed",
            user_id=user_id,
            properties={
                "step": step.value,
                "completed_steps": [s.value for s in progress.completed_steps]
            }
        )
        
        return progress
    
    async def check_abandonment(self):
        """Check for abandoned onboarding processes"""
        now = datetime.now(timezone.utc)
        abandoned_threshold = timedelta(days=7)  # 7 days of inactivity
        
        for user_id, progress in self._progress.items():
            if progress.status != OnboardingStatus.IN_PROGRESS:
                continue
            
            if progress.last_activity_at:
                time_since_activity = now - progress.last_activity_at
                if time_since_activity > abandoned_threshold:
                    progress.status = OnboardingStatus.ABANDONED
                    
                    # Send re-engagement email
                    user = await self._get_user(user_id)
                    if user:
                        await self._send_reengagement_email(user, progress)
                    
                    # Log event
                    await self.events.log_event(
                        event_type="onboarding_abandoned",
                        user_id=user_id,
                        properties={
                            "days_inactive": time_since_activity.days,
                            "current_step": progress.current_step.value
                        }
                    )
                    
                    # Record telemetry
                    self.metrics.increment_counter(
                        "onboarding_abandoned",
                        tags={"user_id": user_id}
                    )
    
    async def get_next_steps(self, user_id: str) -> List[str]:
        """Get next recommended steps for user"""
        progress = self._progress.get(user_id)
        if not progress:
            return []
        
        next_steps = []
        
        if OnboardingStep.PODCAST_ADDED not in progress.completed_steps:
            next_steps.append("Add your first podcast")
        
        if OnboardingStep.FIRST_CAMPAIGN not in progress.completed_steps:
            next_steps.append("Create your first campaign")
        
        if OnboardingStep.FIRST_REPORT not in progress.completed_steps:
            next_steps.append("Generate your first report")
        
        return next_steps
    
    async def _send_welcome_email(self, user: User):
        """Send welcome email to new user"""
        # In production, this would use an email service (SendGrid, AWS SES, etc.)
        logger.info(f"Sending welcome email to {user.email}")
        
        # Record telemetry
        self.metrics.increment_counter(
            "onboarding_email_sent",
            tags={"email_type": "welcome", "user_id": user.user_id}
        )
    
    async def _send_completion_email(self, user: User):
        """Send onboarding completion email"""
        logger.info(f"Sending completion email to {user.email}")
        
        self.metrics.increment_counter(
            "onboarding_email_sent",
            tags={"email_type": "completion", "user_id": user.user_id}
        )
    
    async def _send_reengagement_email(self, user: User, progress: OnboardingProgress):
        """Send re-engagement email for abandoned onboarding"""
        logger.info(f"Sending re-engagement email to {user.email}")
        
        self.metrics.increment_counter(
            "onboarding_email_sent",
            tags={"email_type": "reengagement", "user_id": user.user_id}
        )
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID (placeholder - would use UserManager in production)"""
        # In production, this would use UserManager
        return None
    
    async def get_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        """Get onboarding progress for user"""
        return self._progress.get(user_id)

"""
Self-Service Onboarding Wizard

Automated onboarding flow with step-by-step guidance.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import uuid

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class OnboardingStep(str, Enum):
    """Onboarding steps"""
    WELCOME = "welcome"
    ACCOUNT_SETUP = "account_setup"
    INTEGRATION_SETUP = "integration_setup"
    FIRST_CAMPAIGN = "first_campaign"
    ATTRIBUTION_SETUP = "attribution_setup"
    COMPLETE = "complete"


class OnboardingStatus(str, Enum):
    """Onboarding status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class OnboardingProgress:
    """Onboarding progress data model"""
    onboarding_id: str
    tenant_id: str
    current_step: OnboardingStep
    status: OnboardingStatus
    completed_steps: List[str]
    started_at: datetime
    completed_at: Optional[datetime]
    metadata: Dict


class OnboardingWizard:
    """Manages self-service onboarding"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
        
        # Define onboarding steps
        self.steps = [
            {
                "id": OnboardingStep.WELCOME,
                "title": "Welcome",
                "description": "Get started with your analytics platform",
                "required": True
            },
            {
                "id": OnboardingStep.ACCOUNT_SETUP,
                "title": "Account Setup",
                "description": "Configure your account settings",
                "required": True
            },
            {
                "id": OnboardingStep.INTEGRATION_SETUP,
                "title": "Connect Integrations",
                "description": "Connect your hosting platform or RSS feed",
                "required": True
            },
            {
                "id": OnboardingStep.ATTRIBUTION_SETUP,
                "title": "Set Up Attribution",
                "description": "Configure attribution tracking",
                "required": False
            },
            {
                "id": OnboardingStep.FIRST_CAMPAIGN,
                "title": "Create First Campaign",
                "description": "Set up your first sponsorship campaign",
                "required": False
            },
            {
                "id": OnboardingStep.COMPLETE,
                "title": "Complete",
                "description": "You're all set!",
                "required": False
            }
        ]
    
    async def start_onboarding(self, tenant_id: str) -> OnboardingProgress:
        """Start onboarding for a tenant"""
        onboarding_id = str(uuid.uuid4())
        
        progress = OnboardingProgress(
            onboarding_id=onboarding_id,
            tenant_id=tenant_id,
            current_step=OnboardingStep.WELCOME,
            status=OnboardingStatus.IN_PROGRESS,
            completed_steps=[],
            started_at=datetime.utcnow(),
            completed_at=None,
            metadata={}
        )
        
        await self._save_progress(progress)
        
        self.metrics_collector.increment_counter("onboarding_started_total")
        self.event_logger.log_event("onboarding_started", {
            "onboarding_id": onboarding_id,
            "tenant_id": tenant_id
        })
        
        return progress
    
    async def complete_step(
        self,
        tenant_id: str,
        step: OnboardingStep,
        metadata: Optional[Dict] = None
    ) -> OnboardingProgress:
        """Mark a step as completed"""
        progress = await self.get_progress(tenant_id)
        if not progress:
            progress = await self.start_onboarding(tenant_id)
        
        if step.value not in progress.completed_steps:
            progress.completed_steps.append(step.value)
        
        # Move to next step
        current_step_index = next(
            (i for i, s in enumerate(self.steps) if s["id"] == progress.current_step),
            0
        )
        
        if current_step_index < len(self.steps) - 1:
            progress.current_step = self.steps[current_step_index + 1]["id"]
        
        if metadata:
            progress.metadata.update(metadata)
        
        # Check if onboarding is complete
        required_steps = [s["id"].value for s in self.steps if s.get("required")]
        if all(step in progress.completed_steps for step in required_steps):
            progress.status = OnboardingStatus.COMPLETED
            progress.current_step = OnboardingStep.COMPLETE
            progress.completed_at = datetime.utcnow()
        
        progress.updated_at = datetime.utcnow()
        await self._save_progress(progress)
        
        self.metrics_collector.increment_counter("onboarding_step_completed_total", {
            "step": step.value
        })
        
        if progress.status == OnboardingStatus.COMPLETED:
            self.metrics_collector.increment_counter("onboarding_completed_total")
            self.event_logger.log_event("onboarding_completed", {
                "onboarding_id": progress.onboarding_id,
                "tenant_id": tenant_id
            })
        
        return progress
    
    async def get_progress(self, tenant_id: str) -> Optional[OnboardingProgress]:
        """Get onboarding progress for a tenant"""
        query = "SELECT * FROM onboarding_progress WHERE tenant_id = $1"
        row = await self.postgres_conn.fetch_one(query, tenant_id)
        if not row:
            return None
        return self._row_to_progress(row)
    
    async def get_onboarding_steps(self) -> List[Dict]:
        """Get list of onboarding steps"""
        return self.steps
    
    async def get_next_step(self, tenant_id: str) -> Optional[Dict]:
        """Get the next step for a tenant"""
        progress = await self.get_progress(tenant_id)
        if not progress:
            return self.steps[0] if self.steps else None
        
        current_index = next(
            (i for i, s in enumerate(self.steps) if s["id"] == progress.current_step),
            0
        )
        
        if current_index < len(self.steps) - 1:
            return self.steps[current_index]
        
        return None
    
    async def _save_progress(self, progress: OnboardingProgress):
        """Save onboarding progress"""
        query = """
            INSERT INTO onboarding_progress (
                onboarding_id, tenant_id, current_step, status,
                completed_steps, started_at, completed_at, metadata, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
                current_step = EXCLUDED.current_step,
                status = EXCLUDED.status,
                completed_steps = EXCLUDED.completed_steps,
                completed_at = EXCLUDED.completed_at,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
        """
        
        await self.postgres_conn.execute(
            query,
            progress.onboarding_id,
            progress.tenant_id,
            progress.current_step.value,
            progress.status.value,
            progress.completed_steps,
            progress.started_at,
            progress.completed_at,
            progress.metadata,
            datetime.utcnow()
        )
    
    def _row_to_progress(self, row: Dict) -> OnboardingProgress:
        """Convert database row to OnboardingProgress"""
        return OnboardingProgress(
            onboarding_id=row["onboarding_id"],
            tenant_id=row["tenant_id"],
            current_step=OnboardingStep(row["current_step"]),
            status=OnboardingStatus(row["status"]),
            completed_steps=row.get("completed_steps", []),
            started_at=row["started_at"],
            completed_at=row.get("completed_at"),
            metadata=row.get("metadata", {})
        )

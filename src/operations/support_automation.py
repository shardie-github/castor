"""
Support Automation System

Implements:
- Support escalation workflows
- Automated ticket handling
- Self-serve tutorial system
- Ticket routing and categorization
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.operations.support import (
    SupportIntegration,
    SupportTicket,
    TicketStatus,
    TicketPriority,
    EscalationLevel
)

logger = logging.getLogger(__name__)


class TutorialCategory(Enum):
    """Tutorial categories"""
    ONBOARDING = "onboarding"
    FEATURE_USAGE = "feature_usage"
    TROUBLESHOOTING = "troubleshooting"
    BEST_PRACTICES = "best_practices"
    ADVANCED = "advanced"


class TutorialStatus(Enum):
    """Tutorial status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class SelfServeTutorial:
    """Self-serve tutorial"""
    tutorial_id: str
    title: str
    description: str
    category: TutorialCategory
    content: str  # Markdown or HTML content
    video_url: Optional[str] = None
    related_features: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: TutorialStatus = TutorialStatus.DRAFT
    views: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TicketResolution:
    """Automated ticket resolution"""
    resolution_id: str
    ticket_id: str
    resolution_type: str  # "automated", "tutorial_suggested", "escalated"
    tutorial_id: Optional[str] = None
    resolution_notes: str = ""
    resolved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SupportAutomation:
    """
    Support Automation System
    
    Automates support workflows, ticket handling, and provides self-serve resources.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        support_integration: SupportIntegration
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.support = support_integration
        self._tutorials: Dict[str, SelfServeTutorial] = {}
        self._resolutions: Dict[str, TicketResolution] = {}
        self._initialize_default_tutorials()
        
    def _initialize_default_tutorials(self):
        """Initialize default tutorials"""
        # Onboarding tutorial
        onboarding_tutorial = SelfServeTutorial(
            tutorial_id="onboarding_basics",
            title="Getting Started: Your First Campaign",
            description="Learn how to create your first campaign and generate reports",
            category=TutorialCategory.ONBOARDING,
            content="# Getting Started\n\nThis tutorial will guide you through creating your first campaign...",
            related_features=["campaign_creation", "report_generation"],
            tags=["onboarding", "basics", "first-steps"],
            status=TutorialStatus.PUBLISHED
        )
        self._tutorials[onboarding_tutorial.tutorial_id] = onboarding_tutorial
        
        # Troubleshooting tutorial
        troubleshooting_tutorial = SelfServeTutorial(
            tutorial_id="troubleshooting_attribution",
            title="Troubleshooting Attribution Issues",
            description="Common attribution problems and how to fix them",
            category=TutorialCategory.TROUBLESHOOTING,
            content="# Troubleshooting Attribution\n\nIf you're experiencing attribution issues...",
            related_features=["attribution", "tracking"],
            tags=["troubleshooting", "attribution", "help"],
            status=TutorialStatus.PUBLISHED
        )
        self._tutorials[troubleshooting_tutorial.tutorial_id] = troubleshooting_tutorial
        
    async def create_tutorial(
        self,
        title: str,
        description: str,
        category: TutorialCategory,
        content: str,
        video_url: Optional[str] = None,
        related_features: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> SelfServeTutorial:
        """Create a new tutorial"""
        tutorial_id = str(uuid4())
        
        tutorial = SelfServeTutorial(
            tutorial_id=tutorial_id,
            title=title,
            description=description,
            category=category,
            content=content,
            video_url=video_url,
            related_features=related_features or [],
            tags=tags or []
        )
        
        self._tutorials[tutorial_id] = tutorial
        
        # Log event
        await self.events.log_event(
            event_type="tutorial_created",
            user_id=None,
            properties={
                "tutorial_id": tutorial_id,
                "title": title,
                "category": category.value
            }
        )
        
        return tutorial
    
    async def suggest_tutorials_for_ticket(
        self,
        ticket: SupportTicket
    ) -> List[SelfServeTutorial]:
        """Suggest relevant tutorials for a ticket"""
        suggestions = []
        
        # Analyze ticket content
        ticket_text = (ticket.subject + " " + ticket.description).lower()
        
        # Match tutorials based on tags and content
        for tutorial in self._tutorials.values():
            if tutorial.status != TutorialStatus.PUBLISHED:
                continue
            
            # Check if tutorial tags match ticket tags
            if ticket.tags and any(tag in tutorial.tags for tag in ticket.tags):
                suggestions.append(tutorial)
                continue
            
            # Check if tutorial title/description matches ticket content
            tutorial_keywords = (tutorial.title + " " + tutorial.description).lower()
            if any(keyword in ticket_text for keyword in tutorial_keywords.split()[:5]):
                suggestions.append(tutorial)
        
        # Sort by relevance (views, helpful count)
        suggestions.sort(
            key=lambda t: (t.views * 0.3 + t.helpful_count * 0.7),
            reverse=True
        )
        
        return suggestions[:3]  # Return top 3
    
    async def attempt_automated_resolution(
        self,
        ticket: SupportTicket
    ) -> Optional[TicketResolution]:
        """Attempt to automatically resolve a ticket"""
        # Suggest tutorials
        tutorials = await self.suggest_tutorials_for_ticket(ticket)
        
        if tutorials:
            # Create resolution with tutorial suggestion
            resolution_id = str(uuid4())
            resolution = TicketResolution(
                resolution_id=resolution_id,
                ticket_id=ticket.ticket_id,
                resolution_type="tutorial_suggested",
                tutorial_id=tutorials[0].tutorial_id,
                resolution_notes=f"Suggested tutorial: {tutorials[0].title}"
            )
            
            self._resolutions[resolution_id] = resolution
            
            # Update ticket status
            await self.support.update_ticket_status(
                ticket.ticket_id,
                TicketStatus.WAITING_CUSTOMER,
                notes=f"Tutorial suggested: {tutorials[0].title}"
            )
            
            # Record metrics
            self.metrics.increment_counter(
                "automated_ticket_resolution",
                tags={
                    "resolution_type": "tutorial_suggested",
                    "ticket_priority": ticket.priority.value
                }
            )
            
            # Log event
            await self.events.log_event(
                event_type="automated_ticket_resolution",
                user_id=ticket.user_id,
                properties={
                    "ticket_id": ticket.ticket_id,
                    "resolution_type": "tutorial_suggested",
                    "tutorial_id": tutorials[0].tutorial_id
                }
            )
            
            return resolution
        
        # Check if ticket can be auto-resolved based on common issues
        if self._can_auto_resolve(ticket):
            resolution_id = str(uuid4())
            resolution = TicketResolution(
                resolution_id=resolution_id,
                ticket_id=ticket.ticket_id,
                resolution_type="automated",
                resolution_notes=self._get_auto_resolution_message(ticket)
            )
            
            self._resolutions[resolution_id] = resolution
            
            # Auto-resolve ticket
            await self.support.update_ticket_status(
                ticket.ticket_id,
                TicketStatus.RESOLVED,
                notes=resolution.resolution_notes
            )
            
            # Record metrics
            self.metrics.increment_counter(
                "automated_ticket_resolution",
                tags={
                    "resolution_type": "automated",
                    "ticket_priority": ticket.priority.value
                }
            )
            
            return resolution
        
        return None
    
    def _can_auto_resolve(self, ticket: SupportTicket) -> bool:
        """Check if ticket can be auto-resolved"""
        ticket_text = (ticket.subject + " " + ticket.description).lower()
        
        # Common auto-resolvable issues
        auto_resolvable_patterns = [
            "how do i",
            "where can i find",
            "how to",
            "password reset",
            "forgot password"
        ]
        
        # Only auto-resolve low/medium priority tickets
        if ticket.priority in [TicketPriority.HIGH, TicketPriority.URGENT, TicketPriority.CRITICAL]:
            return False
        
        return any(pattern in ticket_text for pattern in auto_resolvable_patterns)
    
    def _get_auto_resolution_message(self, ticket: SupportTicket) -> str:
        """Get auto-resolution message for ticket"""
        ticket_text = (ticket.subject + " " + ticket.description).lower()
        
        if "password" in ticket_text:
            return "Password reset instructions have been sent to your email. Please check your inbox."
        
        if "how do i" in ticket_text or "how to" in ticket_text:
            return "Please check our knowledge base tutorials. A relevant tutorial has been suggested in your ticket."
        
        return "This issue has been automatically resolved. If you need further assistance, please reply to this ticket."
    
    async def handle_ticket_escalation(
        self,
        ticket: SupportTicket,
        escalation_reason: str
    ) -> SupportTicket:
        """Handle ticket escalation with automated workflows"""
        # Determine escalation level based on priority and content
        if ticket.priority == TicketPriority.CRITICAL:
            new_level = EscalationLevel.ADMIN
        elif ticket.priority == TicketPriority.URGENT:
            new_level = EscalationLevel.LEVEL_3
        elif ticket.priority == TicketPriority.HIGH:
            new_level = EscalationLevel.LEVEL_2
        else:
            new_level = EscalationLevel.LEVEL_1
        
        # Escalate ticket
        escalated_ticket = await self.support.escalate_ticket(
            ticket.ticket_id,
            new_level,
            reason=escalation_reason
        )
        
        # Record metrics
        self.metrics.increment_counter(
            "ticket_escalated_automated",
            tags={
                "from_level": ticket.escalation_level.value,
                "to_level": new_level.value,
                "priority": ticket.priority.value
            }
        )
        
        return escalated_ticket
    
    async def track_tutorial_view(
        self,
        tutorial_id: str,
        user_id: Optional[str] = None
    ):
        """Track tutorial view"""
        tutorial = self._tutorials.get(tutorial_id)
        if not tutorial:
            return
        
        tutorial.views += 1
        tutorial.updated_at = datetime.now(timezone.utc)
        
        # Record metrics
        self.metrics.increment_counter(
            "tutorial_viewed",
            tags={
                "tutorial_id": tutorial_id,
                "category": tutorial.category.value
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="tutorial_viewed",
            user_id=user_id,
            properties={
                "tutorial_id": tutorial_id,
                "title": tutorial.title,
                "category": tutorial.category.value
            }
        )
    
    async def mark_tutorial_helpful(
        self,
        tutorial_id: str,
        helpful: bool,
        user_id: Optional[str] = None
    ):
        """Mark tutorial as helpful or not helpful"""
        tutorial = self._tutorials.get(tutorial_id)
        if not tutorial:
            return
        
        if helpful:
            tutorial.helpful_count += 1
        else:
            tutorial.not_helpful_count += 1
        
        tutorial.updated_at = datetime.now(timezone.utc)
        
        # Record metrics
        self.metrics.increment_counter(
            "tutorial_feedback",
            tags={
                "tutorial_id": tutorial_id,
                "helpful": str(helpful)
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="tutorial_feedback",
            user_id=user_id,
            properties={
                "tutorial_id": tutorial_id,
                "helpful": helpful
            }
        )
    
    async def get_tutorials_by_category(
        self,
        category: TutorialCategory
    ) -> List[SelfServeTutorial]:
        """Get tutorials by category"""
        return [
            t for t in self._tutorials.values()
            if t.category == category
            and t.status == TutorialStatus.PUBLISHED
        ]
    
    async def search_tutorials(
        self,
        query: str
    ) -> List[SelfServeTutorial]:
        """Search tutorials by query"""
        query_lower = query.lower()
        
        results = []
        for tutorial in self._tutorials.values():
            if tutorial.status != TutorialStatus.PUBLISHED:
                continue
            
            # Check title, description, tags
            if (query_lower in tutorial.title.lower() or
                query_lower in tutorial.description.lower() or
                any(query_lower in tag.lower() for tag in tutorial.tags)):
                results.append(tutorial)
        
        # Sort by relevance (views, helpful count)
        results.sort(
            key=lambda t: (t.views * 0.3 + t.helpful_count * 0.7),
            reverse=True
        )
        
        return results
    
    def get_tutorial(self, tutorial_id: str) -> Optional[SelfServeTutorial]:
        """Get tutorial by ID"""
        return self._tutorials.get(tutorial_id)
    
    async def get_support_automation_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get support automation metrics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Count automated resolutions
        automated_resolutions = [
            r for r in self._resolutions.values()
            if r.resolved_at >= cutoff_date
        ]
        
        tutorial_suggestions = len([
            r for r in automated_resolutions
            if r.resolution_type == "tutorial_suggested"
        ])
        
        fully_automated = len([
            r for r in automated_resolutions
            if r.resolution_type == "automated"
        ])
        
        # Tutorial metrics
        total_tutorial_views = sum(
            t.views for t in self._tutorials.values()
        )
        
        return {
            "period_days": days,
            "automated_resolutions": len(automated_resolutions),
            "tutorial_suggestions": tutorial_suggestions,
            "fully_automated": fully_automated,
            "automation_rate": len(automated_resolutions) / max(1, len(automated_resolutions)) * 100,  # Placeholder
            "total_tutorials": len(self._tutorials),
            "total_tutorial_views": total_tutorial_views,
            "top_tutorials": sorted(
                [
                    {
                        "tutorial_id": t.tutorial_id,
                        "title": t.title,
                        "views": t.views,
                        "helpful_count": t.helpful_count
                    }
                    for t in self._tutorials.values()
                ],
                key=lambda x: x["views"],
                reverse=True
            )[:10]
        }

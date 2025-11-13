"""
Cross-Channel Support Integration Module

Handles:
- Multi-channel support integration (email, chat, tickets, in-app)
- Admin escalation paths
- Support ticket management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class SupportChannel(Enum):
    """Support channels"""
    EMAIL = "email"
    CHAT = "chat"
    TICKET = "ticket"
    IN_APP = "in_app"
    PHONE = "phone"
    SLACK = "slack"
    DISCORD = "discord"


class EscalationLevel(Enum):
    """Escalation levels"""
    LEVEL_1 = "level_1"  # Standard support
    LEVEL_2 = "level_2"  # Senior support
    LEVEL_3 = "level_3"  # Engineering/Product
    ADMIN = "admin"  # Admin escalation
    URGENT = "urgent"  # Critical issues


class TicketPriority(Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(Enum):
    """Ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


@dataclass
class SupportTicket:
    """Support ticket"""
    ticket_id: str
    user_id: str
    channel: SupportChannel
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    escalation_level: EscalationLevel
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class EscalationPath:
    """Escalation path configuration"""
    path_id: str
    name: str
    trigger_conditions: Dict[str, Any]  # Conditions that trigger escalation
    escalation_rules: List[Dict[str, Any]]  # Rules for escalation
    auto_escalate: bool = False
    notification_channels: List[str] = field(default_factory=list)


class SupportIntegration:
    """
    Cross-Channel Support Integration
    
    Integrates support across multiple channels and manages escalation paths.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._tickets: Dict[str, SupportTicket] = {}
        self._escalation_paths: Dict[str, EscalationPath] = {}
        self._initialize_default_escalation_paths()
        
    def _initialize_default_escalation_paths(self):
        """Initialize default escalation paths"""
        # Critical issue escalation
        critical_path = EscalationPath(
            path_id="critical_issues",
            name="Critical Issues",
            trigger_conditions={
                "priority": ["urgent", "critical"],
                "tags": ["system_error", "data_loss", "security"]
            },
            escalation_rules=[
                {"condition": "priority == 'critical'", "escalate_to": EscalationLevel.ADMIN},
                {"condition": "response_time > 3600", "escalate_to": EscalationLevel.LEVEL_3}
            ],
            auto_escalate=True,
            notification_channels=["slack", "email", "pagerduty"]
        )
        self._escalation_paths[critical_path.path_id] = critical_path
        
        # Account health escalation
        account_health_path = EscalationPath(
            path_id="account_health",
            name="Account Health Issues",
            trigger_conditions={
                "tags": ["churn_risk", "subscription_issue", "billing"]
            },
            escalation_rules=[
                {"condition": "user_tier == 'enterprise'", "escalate_to": EscalationLevel.LEVEL_2},
                {"condition": "revenue_at_risk > 10000", "escalate_to": EscalationLevel.ADMIN}
            ],
            auto_escalate=True,
            notification_channels=["email", "slack"]
        )
        self._escalation_paths[account_health_path.path_id] = account_health_path
        
        # Feature request escalation
        feature_request_path = EscalationPath(
            path_id="feature_requests",
            name="Feature Requests",
            trigger_conditions={
                "tags": ["feature_request", "enhancement"]
            },
            escalation_rules=[
                {"condition": "user_tier == 'enterprise'", "escalate_to": EscalationLevel.LEVEL_3},
                {"condition": "request_count > 10", "escalate_to": EscalationLevel.LEVEL_3}
            ],
            auto_escalate=False,
            notification_channels=["email"]
        )
        self._escalation_paths[feature_request_path.path_id] = feature_request_path
    
    async def create_ticket(
        self,
        user_id: str,
        channel: SupportChannel,
        subject: str,
        description: str,
        priority: Optional[TicketPriority] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SupportTicket:
        """
        Create a new support ticket
        
        Args:
            user_id: User ID
            channel: Support channel
            subject: Ticket subject
            description: Ticket description
            priority: Ticket priority (auto-determined if not provided)
            tags: Optional tags
            metadata: Optional metadata
            
        Returns:
            SupportTicket
        """
        ticket_id = str(uuid4())
        
        # Auto-determine priority if not provided
        if priority is None:
            priority = self._determine_priority(subject, description, tags or [])
        
        # Determine initial escalation level
        escalation_level = self._determine_escalation_level(priority, tags or [], metadata or {})
        
        ticket = SupportTicket(
            ticket_id=ticket_id,
            user_id=user_id,
            channel=channel,
            subject=subject,
            description=description,
            priority=priority,
            status=TicketStatus.OPEN,
            escalation_level=escalation_level,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self._tickets[ticket_id] = ticket
        
        # Check for auto-escalation
        await self._check_auto_escalation(ticket)
        
        # Record metrics
        self.metrics.increment_counter(
            "support_ticket_created",
            tags={
                "channel": channel.value,
                "priority": priority.value,
                "escalation_level": escalation_level.value
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="support_ticket_created",
            user_id=user_id,
            properties={
                "ticket_id": ticket_id,
                "channel": channel.value,
                "priority": priority.value,
                "subject": subject
            }
        )
        
        return ticket
    
    def _determine_priority(
        self,
        subject: str,
        description: str,
        tags: List[str]
    ) -> TicketPriority:
        """Auto-determine ticket priority"""
        text = (subject + " " + description).lower()
        
        # Critical keywords
        if any(keyword in text for keyword in ["critical", "down", "outage", "security breach", "data loss"]):
            return TicketPriority.CRITICAL
        
        # Urgent keywords
        if any(keyword in text for keyword in ["urgent", "blocking", "cannot", "broken", "error"]):
            return TicketPriority.URGENT
        
        # High priority tags
        if any(tag in tags for tag in ["billing", "account", "subscription"]):
            return TicketPriority.HIGH
        
        # Default to medium
        return TicketPriority.MEDIUM
    
    def _determine_escalation_level(
        self,
        priority: TicketPriority,
        tags: List[str],
        metadata: Dict[str, Any]
    ) -> EscalationLevel:
        """Determine initial escalation level"""
        if priority == TicketPriority.CRITICAL:
            return EscalationLevel.ADMIN
        
        if priority == TicketPriority.URGENT:
            return EscalationLevel.LEVEL_3
        
        # Check for enterprise users
        if metadata.get("user_tier") == "enterprise":
            return EscalationLevel.LEVEL_2
        
        # Default to level 1
        return EscalationLevel.LEVEL_1
    
    async def _check_auto_escalation(self, ticket: SupportTicket):
        """Check if ticket should be auto-escalated"""
        for path in self._escalation_paths.values():
            if not path.auto_escalate:
                continue
            
            # Check if ticket matches trigger conditions
            if self._matches_trigger_conditions(ticket, path.trigger_conditions):
                # Apply escalation rules
                new_level = await self._apply_escalation_rules(ticket, path.escalation_rules)
                if new_level and new_level.value != ticket.escalation_level.value:
                    await self.escalate_ticket(ticket.ticket_id, new_level, reason="Auto-escalation rule")
    
    def _matches_trigger_conditions(
        self,
        ticket: SupportTicket,
        conditions: Dict[str, Any]
    ) -> bool:
        """Check if ticket matches trigger conditions"""
        # Check priority
        if "priority" in conditions:
            if ticket.priority.value not in conditions["priority"]:
                return False
        
        # Check tags
        if "tags" in conditions:
            if not any(tag in ticket.tags for tag in conditions["tags"]):
                return False
        
        return True
    
    async def _apply_escalation_rules(
        self,
        ticket: SupportTicket,
        rules: List[Dict[str, Any]]
    ) -> Optional[EscalationLevel]:
        """Apply escalation rules and return new level if escalated"""
        for rule in rules:
            condition = rule.get("condition", "")
            escalate_to = rule.get("escalate_to")
            
            # Simple condition evaluation (in production, would use proper expression evaluator)
            if self._evaluate_condition(ticket, condition):
                return EscalationLevel(escalate_to) if isinstance(escalate_to, str) else escalate_to
        
        return None
    
    def _evaluate_condition(self, ticket: SupportTicket, condition: str) -> bool:
        """Evaluate escalation condition (simplified)"""
        # In production, would use proper expression evaluator
        # For now, simple keyword matching
        if "priority == 'critical'" in condition:
            return ticket.priority == TicketPriority.CRITICAL
        
        if "user_tier == 'enterprise'" in condition:
            return ticket.metadata.get("user_tier") == "enterprise"
        
        return False
    
    async def escalate_ticket(
        self,
        ticket_id: str,
        escalation_level: EscalationLevel,
        reason: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> SupportTicket:
        """
        Escalate a ticket to a higher level
        
        Args:
            ticket_id: Ticket ID
            escalation_level: New escalation level
            reason: Reason for escalation
            assigned_to: Optional assignee
            
        Returns:
            Updated ticket
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        old_level = ticket.escalation_level
        ticket.escalation_level = escalation_level
        ticket.status = TicketStatus.ESCALATED
        ticket.updated_at = datetime.now(timezone.utc)
        
        if assigned_to:
            ticket.assigned_to = assigned_to
        
        if reason:
            ticket.metadata["escalation_reason"] = reason
        
        # Record metrics
        self.metrics.increment_counter(
            "support_ticket_escalated",
            tags={
                "from_level": old_level.value,
                "to_level": escalation_level.value,
                "ticket_id": ticket_id
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="support_ticket_escalated",
            user_id=ticket.user_id,
            properties={
                "ticket_id": ticket_id,
                "from_level": old_level.value,
                "to_level": escalation_level.value,
                "reason": reason
            }
        )
        
        # Send notifications
        await self._send_escalation_notifications(ticket, old_level, escalation_level)
        
        return ticket
    
    async def _send_escalation_notifications(
        self,
        ticket: SupportTicket,
        old_level: EscalationLevel,
        new_level: EscalationLevel
    ):
        """Send escalation notifications"""
        # In production, would send to:
        # - Slack channels
        # - Email notifications
        # - PagerDuty (for critical)
        # - Admin dashboard
        
        logger.info(
            f"Ticket {ticket.ticket_id} escalated from {old_level.value} to {new_level.value}"
        )
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        notes: Optional[str] = None
    ) -> SupportTicket:
        """Update ticket status"""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)
        
        if status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now(timezone.utc)
        
        if notes:
            ticket.metadata["status_notes"] = notes
        
        # Record metrics
        if status == TicketStatus.RESOLVED:
            resolution_time = None
            if ticket.created_at and ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds()
            
            self.metrics.record_histogram(
                "support_ticket_resolution_time_seconds",
                resolution_time or 0,
                tags={"priority": ticket.priority.value}
            )
        
        await self.events.log_event(
            event_type="support_ticket_status_updated",
            user_id=ticket.user_id,
            properties={
                "ticket_id": ticket_id,
                "status": status.value,
                "notes": notes
            }
        )
        
        return ticket
    
    async def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get ticket by ID"""
        return self._tickets.get(ticket_id)
    
    async def list_tickets(
        self,
        user_id: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None
    ) -> List[SupportTicket]:
        """List tickets with optional filters"""
        tickets = list(self._tickets.values())
        
        if user_id:
            tickets = [t for t in tickets if t.user_id == user_id]
        
        if status:
            tickets = [t for t in tickets if t.status == status]
        
        if priority:
            tickets = [t for t in tickets if t.priority == priority]
        
        return tickets
    
    async def add_escalation_path(self, path: EscalationPath):
        """Add a new escalation path"""
        self._escalation_paths[path.path_id] = path
    
    async def get_escalation_path(self, path_id: str) -> Optional[EscalationPath]:
        """Get escalation path by ID"""
        return self._escalation_paths.get(path_id)

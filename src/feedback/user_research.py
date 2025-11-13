"""
User Research Validation System

Validates user needs through:
- Ongoing interviews
- Surveys
- Review analysis
- Persona and JTBD adjustment
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


class ResearchType(Enum):
    """Research types"""
    USER_INTERVIEW = "user_interview"
    SURVEY = "survey"
    REVIEW_ANALYSIS = "review_analysis"
    FEEDBACK_ANALYSIS = "feedback_analysis"
    USABILITY_TEST = "usability_test"


class ResearchStatus(Enum):
    """Research status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    ACTIONED = "actioned"


@dataclass
class ResearchSession:
    """Research session (interview, survey, etc.)"""
    session_id: str
    research_type: ResearchType
    user_id: Optional[str] = None
    persona_segment: Optional[str] = None
    status: ResearchStatus = ResearchStatus.PLANNED
    scheduled_at: Optional[datetime] = None
    conducted_at: Optional[datetime] = None
    notes: str = ""
    insights: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    feature_requests: List[str] = field(default_factory=list)
    jtbd_updates: List[Dict[str, Any]] = field(default_factory=list)
    persona_updates: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonaUpdate:
    """Persona definition update"""
    update_id: str
    persona_segment: str
    field_name: str
    old_value: Any
    new_value: Any
    reason: str
    research_session_id: str
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class JTBDUpdate:
    """Jobs-to-be-Done update"""
    update_id: str
    jtbd_id: str
    persona_segment: str
    change_type: str  # "new", "updated", "deprecated"
    old_jtbd: Optional[Dict[str, Any]] = None
    new_jtbd: Optional[Dict[str, Any]] = None
    reason: str = ""
    research_session_id: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UserResearchValidation:
    """
    User Research Validation System
    
    Manages ongoing user research, analyzes findings, and updates personas/JTBD.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._sessions: Dict[str, ResearchSession] = {}
        self._persona_updates: List[PersonaUpdate] = []
        self._jtbd_updates: List[JTBDUpdate] = []
        
    async def create_research_session(
        self,
        research_type: ResearchType,
        user_id: Optional[str] = None,
        persona_segment: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchSession:
        """Create a new research session"""
        session_id = str(uuid4())
        
        session = ResearchSession(
            session_id=session_id,
            research_type=research_type,
            user_id=user_id,
            persona_segment=persona_segment,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        
        self._sessions[session_id] = session
        
        # Log event
        await self.events.log_event(
            event_type="research_session_created",
            user_id=user_id,
            properties={
                "session_id": session_id,
                "research_type": research_type.value,
                "persona_segment": persona_segment
            }
        )
        
        return session
    
    async def conduct_research_session(
        self,
        session_id: str,
        notes: str,
        insights: Optional[List[str]] = None,
        pain_points: Optional[List[str]] = None,
        feature_requests: Optional[List[str]] = None
    ) -> ResearchSession:
        """Conduct a research session and record findings"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Research session {session_id} not found")
        
        session.status = ResearchStatus.COMPLETED
        session.conducted_at = datetime.now(timezone.utc)
        session.notes = notes
        session.insights = insights or []
        session.pain_points = pain_points or []
        session.feature_requests = feature_requests or []
        
        # Log event
        await self.events.log_event(
            event_type="research_session_conducted",
            user_id=session.user_id,
            properties={
                "session_id": session_id,
                "insights_count": len(session.insights),
                "pain_points_count": len(session.pain_points),
                "feature_requests_count": len(session.feature_requests)
            }
        )
        
        return session
    
    async def analyze_research_session(
        self,
        session_id: str,
        persona_updates: Optional[List[Dict[str, Any]]] = None,
        jtbd_updates: Optional[List[Dict[str, Any]]] = None
    ) -> ResearchSession:
        """Analyze research session and extract persona/JTBD updates"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Research session {session_id} not found")
        
        session.status = ResearchStatus.ANALYZED
        session.analyzed_at = datetime.now(timezone.utc)
        session.persona_updates = persona_updates or []
        session.jtbd_updates = jtbd_updates or []
        
        # Create persona updates
        for update_data in session.persona_updates:
            await self.create_persona_update(
                persona_segment=update_data.get("persona_segment", session.persona_segment or "unknown"),
                field_name=update_data["field_name"],
                old_value=update_data.get("old_value"),
                new_value=update_data["new_value"],
                reason=update_data.get("reason", ""),
                research_session_id=session_id
            )
        
        # Create JTBD updates
        for update_data in session.jtbd_updates:
            await self.create_jtbd_update(
                jtbd_id=update_data.get("jtbd_id", ""),
                persona_segment=update_data.get("persona_segment", session.persona_segment or "unknown"),
                change_type=update_data["change_type"],
                old_jtbd=update_data.get("old_jtbd"),
                new_jtbd=update_data.get("new_jtbd"),
                reason=update_data.get("reason", ""),
                research_session_id=session_id
            )
        
        # Log event
        await self.events.log_event(
            event_type="research_session_analyzed",
            user_id=session.user_id,
            properties={
                "session_id": session_id,
                "persona_updates_count": len(session.persona_updates),
                "jtbd_updates_count": len(session.jtbd_updates)
            }
        )
        
        return session
    
    async def create_persona_update(
        self,
        persona_segment: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        research_session_id: str
    ) -> PersonaUpdate:
        """Create a persona update"""
        update_id = str(uuid4())
        
        update = PersonaUpdate(
            update_id=update_id,
            persona_segment=persona_segment,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            research_session_id=research_session_id
        )
        
        self._persona_updates.append(update)
        
        # Record metrics
        self.metrics.increment_counter(
            "persona_updated",
            tags={
                "persona_segment": persona_segment,
                "field_name": field_name
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="persona_updated",
            user_id=None,
            properties={
                "update_id": update_id,
                "persona_segment": persona_segment,
                "field_name": field_name,
                "research_session_id": research_session_id
            }
        )
        
        return update
    
    async def create_jtbd_update(
        self,
        jtbd_id: str,
        persona_segment: str,
        change_type: str,
        old_jtbd: Optional[Dict[str, Any]] = None,
        new_jtbd: Optional[Dict[str, Any]] = None,
        reason: str = "",
        research_session_id: str = ""
    ) -> JTBDUpdate:
        """Create a JTBD update"""
        update_id = str(uuid4())
        
        update = JTBDUpdate(
            update_id=update_id,
            jtbd_id=jtbd_id,
            persona_segment=persona_segment,
            change_type=change_type,
            old_jtbd=old_jtbd,
            new_jtbd=new_jtbd,
            reason=reason,
            research_session_id=research_session_id
        )
        
        self._jtbd_updates.append(update)
        
        # Record metrics
        self.metrics.increment_counter(
            "jtbd_updated",
            tags={
                "persona_segment": persona_segment,
                "change_type": change_type
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="jtbd_updated",
            user_id=None,
            properties={
                "update_id": update_id,
                "jtbd_id": jtbd_id,
                "persona_segment": persona_segment,
                "change_type": change_type,
                "research_session_id": research_session_id
            }
        )
        
        return update
    
    async def get_research_summary(
        self,
        days: int = 90,
        persona_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get research summary for a period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        sessions = [
            s for s in self._sessions.values()
            if s.created_at >= cutoff_date
        ]
        
        if persona_segment:
            sessions = [s for s in sessions if s.persona_segment == persona_segment]
        
        # Aggregate insights
        all_insights = []
        all_pain_points = []
        all_feature_requests = []
        
        for session in sessions:
            all_insights.extend(session.insights)
            all_pain_points.extend(session.pain_points)
            all_feature_requests.extend(session.feature_requests)
        
        # Count persona/JTBD updates
        persona_updates_count = len([
            u for u in self._persona_updates
            if u.updated_at >= cutoff_date
        ])
        
        jtbd_updates_count = len([
            u for u in self._jtbd_updates
            if u.updated_at >= cutoff_date
        ])
        
        return {
            "period_days": days,
            "total_sessions": len(sessions),
            "sessions_by_type": {
                rt.value: len([s for s in sessions if s.research_type == rt])
                for rt in ResearchType
            },
            "insights_count": len(all_insights),
            "pain_points_count": len(all_pain_points),
            "feature_requests_count": len(all_feature_requests),
            "persona_updates_count": persona_updates_count,
            "jtbd_updates_count": jtbd_updates_count,
            "top_insights": all_insights[:10],
            "top_pain_points": all_pain_points[:10],
            "top_feature_requests": all_feature_requests[:10]
        }
    
    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get research session by ID"""
        return self._sessions.get(session_id)
    
    def list_sessions(
        self,
        research_type: Optional[ResearchType] = None,
        status: Optional[ResearchStatus] = None,
        persona_segment: Optional[str] = None
    ) -> List[ResearchSession]:
        """List research sessions"""
        sessions = list(self._sessions.values())
        
        if research_type:
            sessions = [s for s in sessions if s.research_type == research_type]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        if persona_segment:
            sessions = [s for s in sessions if s.persona_segment == persona_segment]
        
        return sessions

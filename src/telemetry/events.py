"""
Event Logging Module

Handles user action events, feature usage tracking, friction/confusion signals,
and support flow triggers. Integrates with marketing/analytics platforms.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types"""
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    FEATURE_USAGE = "feature_usage"
    FRICTION_SIGNAL = "friction_signal"
    SUPPORT_TRIGGER = "support_trigger"
    CONVERSION_EVENT = "conversion_event"
    ERROR = "error"


@dataclass
class Event:
    """Event data structure"""
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    properties: Dict[str, Any]
    page: Optional[str] = None
    feature: Optional[str] = None


class EventLogger:
    """
    Event Logger
    
    Logs user events for analytics, marketing, and product insights.
    Captures friction signals and triggers support flows.
    """
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 5):
        self.events: List[Event] = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._enabled = True
        self._flush_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize event logger"""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
    async def cleanup(self):
        """Cleanup and flush remaining events"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()
        
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        properties: Dict[str, Any],
        session_id: Optional[str] = None,
        page: Optional[str] = None,
        feature: Optional[str] = None
    ):
        """
        Log an event
        
        Args:
            event_type: Type of event (page_view, user_action, etc.)
            user_id: User identifier
            properties: Event properties
            session_id: Session identifier
            page: Page/route where event occurred
            feature: Feature name if applicable
        """
        if not self._enabled:
            return
            
        event = Event(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            properties=properties,
            page=page,
            feature=feature
        )
        
        self.events.append(event)
        
        # Check for friction signals
        await self._detect_friction(event)
        
        # Flush if batch size reached
        if len(self.events) >= self.batch_size:
            await self.flush()
    
    async def log_page_view(
        self,
        user_id: Optional[str],
        page: str,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """Log a page view event"""
        await self.log_event(
            event_type=EventType.PAGE_VIEW.value,
            user_id=user_id,
            properties=properties or {},
            session_id=session_id,
            page=page
        )
    
    async def log_user_action(
        self,
        user_id: Optional[str],
        action: str,
        properties: Optional[Dict[str, Any]] = None,
        page: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log a user action event"""
        props = properties or {}
        props["action"] = action
        
        await self.log_event(
            event_type=EventType.USER_ACTION.value,
            user_id=user_id,
            properties=props,
            session_id=session_id,
            page=page
        )
    
    async def log_feature_usage(
        self,
        user_id: Optional[str],
        feature: str,
        properties: Optional[Dict[str, Any]] = None,
        page: Optional[str] = None
    ):
        """Log feature usage"""
        props = properties or {}
        props["feature_name"] = feature
        
        await self.log_event(
            event_type=EventType.FEATURE_USAGE.value,
            user_id=user_id,
            properties=props,
            page=page,
            feature=feature
        )
    
    async def log_friction_signal(
        self,
        user_id: Optional[str],
        signal_type: str,
        properties: Optional[Dict[str, Any]] = None,
        page: Optional[str] = None,
        feature: Optional[str] = None
    ):
        """
        Log a friction/confusion signal
        
        Signal types:
        - form_abandonment: User started but didn't complete form
        - error_retry: User retried after error
        - help_click: User clicked help/documentation
        - support_contact: User contacted support
        - long_dwell: User spent excessive time on page
        - rapid_clicks: User clicked rapidly (confusion indicator)
        """
        props = properties or {}
        props["signal_type"] = signal_type
        
        await self.log_event(
            event_type=EventType.FRICTION_SIGNAL.value,
            user_id=user_id,
            properties=props,
            page=page,
            feature=feature
        )
        
        # Trigger support flow if needed
        if signal_type in ["support_contact", "error_retry"]:
            await self._trigger_support_flow(user_id, signal_type, page, feature)
    
    async def _detect_friction(self, event: Event):
        """Detect friction signals from events"""
        props = event.properties
        
        # Detect form abandonment
        if event.event_type == EventType.USER_ACTION.value:
            if props.get("action") == "form_started" and not props.get("form_completed"):
                # Check if form was abandoned (no completion within timeout)
                await self.log_friction_signal(
                    event.user_id,
                    "form_abandonment",
                    {"form_name": props.get("form_name")},
                    event.page,
                    event.feature
                )
        
        # Detect error retries
        if props.get("error") and props.get("retry_count", 0) > 0:
            await self.log_friction_signal(
                event.user_id,
                "error_retry",
                {"error": props.get("error"), "retry_count": props.get("retry_count")},
                event.page,
                event.feature
            )
        
        # Detect long dwell time (confusion indicator)
        if event.event_type == EventType.PAGE_VIEW.value:
            dwell_time = props.get("dwell_time_seconds", 0)
            if dwell_time > 300:  # 5 minutes
                await self.log_friction_signal(
                    event.user_id,
                    "long_dwell",
                    {"dwell_time_seconds": dwell_time},
                    event.page
                )
    
    async def _trigger_support_flow(
        self,
        user_id: Optional[str],
        signal_type: str,
        page: Optional[str],
        feature: Optional[str]
    ):
        """Trigger automated support flow"""
        await self.log_event(
            event_type=EventType.SUPPORT_TRIGGER.value,
            user_id=user_id,
            properties={
                "trigger_type": signal_type,
                "page": page,
                "feature": feature,
                "auto_support_enabled": True
            },
            page=page,
            feature=feature
        )
        
        # In production, this would trigger:
        # - In-app help widget
        # - Support ticket creation
        # - Contextual help display
        # - Email to support team
        
        logger.info(f"Support flow triggered for user {user_id} on {page}/{feature}")
    
    async def flush(self):
        """Flush events to storage/analytics platform"""
        if not self.events:
            return
            
        events_to_flush = self.events.copy()
        self.events.clear()
        
        # Send to internal analytics store (PostgreSQL)
        try:
            # Import here to avoid circular dependencies
            from src.database import PostgresConnection
            from src.main import postgres_conn
            
            if postgres_conn:
                for event in events_to_flush:
                    try:
                        await postgres_conn.execute(
                            """
                            INSERT INTO events (event_id, event_type, user_id, session_id, timestamp, properties, context)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (event_id) DO NOTHING
                            """,
                            event.event_id,
                            event.event_type,
                            event.user_id,
                            event.session_id,
                            event.timestamp,
                            json.dumps(event.properties, default=str),
                            json.dumps(event.context, default=str)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store event {event.event_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to flush events to database: {e}")
        
        # In production, this would also send to:
        # - PostHog/Mixpanel/Amplitude (via their SDKs)
        # - Segment
        # - Data warehouse
        # For now, we store in PostgreSQL events table
        
        logger.info(f"Flushed {len(events_to_flush)} events to storage")
        
        # Also log for debugging
        for event in events_to_flush[:10]:  # Log first 10 to avoid spam
            logger.debug(f"Event: {event.event_type} - {json.dumps(asdict(event), default=str)}")
    
    async def _periodic_flush(self):
        """Periodically flush events"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    def enable(self):
        """Enable event logging"""
        self._enabled = True
    
    def disable(self):
        """Disable event logging"""
        self._enabled = False

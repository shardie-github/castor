"""
Tests for telemetry event logging
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from src.telemetry.events import EventLogger, EventType


@pytest.fixture
def mock_postgres_conn():
    """Mock PostgreSQL connection"""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value=None)
    return conn


@pytest.fixture
def event_logger(mock_metrics_collector, mock_postgres_conn):
    """Create event logger instance"""
    return EventLogger(
        metrics_collector=mock_metrics_collector,
        postgres_conn=mock_postgres_conn,
        flush_interval=60.0
    )


@pytest.mark.asyncio
class TestEventLogger:
    """Test event logger functionality"""
    
    async def test_create_event_logger(self, event_logger):
        """Test creating event logger"""
        assert event_logger is not None
        assert event_logger.metrics_collector is not None
        assert event_logger.postgres_conn is not None
    
    async def test_log_event(self, event_logger):
        """Test logging an event"""
        await event_logger.log_event(
            event_type="test.event",
            user_id="user123",
            properties={"key": "value"}
        )
        
        # Verify event was added to buffer
        assert len(event_logger._event_buffer) == 1
        event = event_logger._event_buffer[0]
        assert event["event_type"] == "test.event"
        assert event["user_id"] == "user123"
        assert event["properties"]["key"] == "value"
    
    async def test_log_user_action(self, event_logger):
        """Test logging a user action"""
        await event_logger.log_user_action(
            user_id="user123",
            action="button_click",
            page="/dashboard",
            properties={"button": "submit"}
        )
        
        assert len(event_logger._event_buffer) == 1
        event = event_logger._event_buffer[0]
        assert event["event_type"] == "user.action"
        assert event["user_id"] == "user123"
        assert event["properties"]["action"] == "button_click"
    
    async def test_log_feature_usage(self, event_logger):
        """Test logging feature usage"""
        await event_logger.log_feature_usage(
            user_id="user123",
            feature="analytics_dashboard",
            properties={"view": "campaigns"}
        )
        
        assert len(event_logger._event_buffer) == 1
        event = event_logger._event_buffer[0]
        assert event["event_type"] == "feature.usage"
        assert event["user_id"] == "user123"
        assert event["properties"]["feature"] == "analytics_dashboard"
    
    async def test_flush_events(self, event_logger):
        """Test flushing events to database"""
        # Add some events
        await event_logger.log_event("test.event1", "user1")
        await event_logger.log_event("test.event2", "user2")
        
        # Flush
        await event_logger.flush()
        
        # Verify buffer is cleared
        assert len(event_logger._event_buffer) == 0
        # Verify database was called
        assert event_logger.postgres_conn.execute.called
    
    async def test_initialize(self, event_logger):
        """Test initializing event logger"""
        await event_logger.initialize()
        
        # Verify flush task is running
        assert event_logger._flush_task is not None
    
    async def test_cleanup(self, event_logger):
        """Test cleaning up event logger"""
        await event_logger.initialize()
        await event_logger.cleanup()
        
        # Verify flush task is cancelled
        assert event_logger._flush_task is None or event_logger._flush_task.done()

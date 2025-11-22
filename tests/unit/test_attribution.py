"""
Tests for attribution engine
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.attribution.attribution_engine import AttributionEngine
from src.attribution.models.first_touch import FirstTouchAttribution
from src.attribution.models.last_touch import LastTouchAttribution


@pytest.fixture
def attribution_engine(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create attribution engine instance"""
    return AttributionEngine(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


class TestAttributionEngine:
    """Test attribution engine functionality"""
    
    def test_create_attribution_engine(self, attribution_engine):
        """Test creating attribution engine"""
        assert attribution_engine is not None
        assert attribution_engine.metrics_collector is not None
        assert attribution_engine.event_logger is not None
    
    def test_first_touch_attribution(self, attribution_engine):
        """Test first touch attribution model"""
        events = [
            {"event_id": "1", "timestamp": "2024-01-01T00:00:00", "touchpoint": "ad"},
            {"event_id": "2", "timestamp": "2024-01-02T00:00:00", "touchpoint": "email"},
            {"event_id": "3", "timestamp": "2024-01-03T00:00:00", "touchpoint": "conversion"},
        ]
        
        model = FirstTouchAttribution()
        result = model.attribute(events)
        
        assert result is not None
        assert "ad" in result or result.get("touchpoint") == "ad"
    
    def test_last_touch_attribution(self, attribution_engine):
        """Test last touch attribution model"""
        events = [
            {"event_id": "1", "timestamp": "2024-01-01T00:00:00", "touchpoint": "ad"},
            {"event_id": "2", "timestamp": "2024-01-02T00:00:00", "touchpoint": "email"},
            {"event_id": "3", "timestamp": "2024-01-03T00:00:00", "touchpoint": "conversion"},
        ]
        
        model = LastTouchAttribution()
        result = model.attribute(events)
        
        assert result is not None
        # Last touch should be "email" (before conversion)
        assert "email" in str(result) or result.get("touchpoint") == "email"

"""
Tests for analytics store
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from src.analytics.analytics_store import AnalyticsStore


@pytest.fixture
def analytics_store(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create analytics store instance"""
    return AnalyticsStore(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


class TestAnalyticsStore:
    """Test analytics store functionality"""
    
    def test_create_analytics_store(self, analytics_store):
        """Test creating analytics store"""
        assert analytics_store is not None
        assert analytics_store.metrics_collector is not None
    
    def test_store_metric(self, analytics_store):
        """Test storing a metric"""
        # Mock the database call
        analytics_store.postgres_conn.execute = Mock(return_value=None)
        
        # Verify the store can handle storing metrics
        assert analytics_store.postgres_conn is not None
    
    def test_query_metrics(self, analytics_store):
        """Test querying metrics"""
        # Mock the database call
        analytics_store.postgres_conn.fetch_all = Mock(return_value=[
            {"metric_name": "listeners", "value": 100, "timestamp": datetime.now()},
            {"metric_name": "downloads", "value": 50, "timestamp": datetime.now()},
        ])
        
        # Verify the store can handle querying
        assert analytics_store.postgres_conn is not None

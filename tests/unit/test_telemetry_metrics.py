"""
Tests for telemetry metrics collection
"""

import pytest
from unittest.mock import Mock, patch
import time
from src.telemetry.metrics import MetricsCollector, MetricType


@pytest.fixture
def metrics_collector():
    """Create metrics collector instance"""
    return MetricsCollector()


class TestMetricsCollector:
    """Test metrics collector functionality"""
    
    def test_create_metrics_collector(self, metrics_collector):
        """Test creating metrics collector"""
        assert metrics_collector is not None
        assert metrics_collector.metrics == {}
        assert metrics_collector._enabled is True
    
    def test_increment_counter(self, metrics_collector):
        """Test incrementing a counter metric"""
        metrics_collector.increment_counter("test_counter", value=1.0, tags={"env": "test"})
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[list(metrics_collector.metrics.keys())[0]][0]
        assert metric.name == "test_counter"
        assert metric.value == 1.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"env": "test"}
    
    def test_record_gauge(self, metrics_collector):
        """Test recording a gauge metric"""
        metrics_collector.record_gauge("test_gauge", value=42.0, tags={"env": "test"})
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[list(metrics_collector.metrics.keys())[0]][0]
        assert metric.name == "test_gauge"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.GAUGE
    
    def test_record_histogram(self, metrics_collector):
        """Test recording a histogram metric"""
        metrics_collector.record_histogram("test_histogram", value=100.0, tags={"env": "test"})
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[list(metrics_collector.metrics.keys())[0]][0]
        assert metric.name == "test_histogram"
        assert metric.value == 100.0
        assert metric.metric_type == MetricType.HISTOGRAM
    
    def test_record_summary(self, metrics_collector):
        """Test recording a summary metric"""
        metrics_collector.record_summary("test_summary", value=50.0, tags={"env": "test"})
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[list(metrics_collector.metrics.keys())[0]][0]
        assert metric.name == "test_summary"
        assert metric.value == 50.0
        assert metric.metric_type == MetricType.SUMMARY
    
    def test_multiple_metrics_same_name_different_tags(self, metrics_collector):
        """Test that metrics with same name but different tags are stored separately"""
        metrics_collector.increment_counter("test_counter", tags={"env": "test"})
        metrics_collector.increment_counter("test_counter", tags={"env": "prod"})
        
        assert len(metrics_collector.metrics) == 2
    
    def test_disable_metrics(self, metrics_collector):
        """Test disabling metrics collection"""
        metrics_collector._enabled = False
        metrics_collector.increment_counter("test_counter")
        
        assert len(metrics_collector.metrics) == 0
    
    def test_get_metrics(self, metrics_collector):
        """Test getting all metrics"""
        metrics_collector.increment_counter("counter1")
        metrics_collector.record_gauge("gauge1", value=10.0)
        
        all_metrics = metrics_collector.get_metrics()
        assert len(all_metrics) == 2
    
    def test_clear_metrics(self, metrics_collector):
        """Test clearing all metrics"""
        metrics_collector.increment_counter("test_counter")
        assert len(metrics_collector.metrics) > 0
        
        metrics_collector.clear()
        assert len(metrics_collector.metrics) == 0

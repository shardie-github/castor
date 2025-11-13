"""
Metrics Collection Module

Provides metrics collection interface for Prometheus-compatible metrics.
Captures operational telemetry including latency, uptime, error rates, etc.
"""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str]
    timestamp: float


class MetricsCollector:
    """
    Metrics Collector
    
    Collects and records metrics for operational telemetry.
    Compatible with Prometheus metrics format.
    """
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self._enabled = True
        
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        if not self._enabled:
            return
            
        tags = tags or {}
        key = self._make_key(name, tags)
        
        if key not in self.metrics:
            self.metrics[key] = []
            
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            tags=tags,
            timestamp=time.time()
        )
        self.metrics[key].append(metric)
        
    def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a gauge metric"""
        if not self._enabled:
            return
            
        tags = tags or {}
        key = self._make_key(name, tags)
        
        if key not in self.metrics:
            self.metrics[key] = []
            
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            tags=tags,
            timestamp=time.time()
        )
        self.metrics[key].append(metric)
        
    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        buckets: Optional[list] = None
    ):
        """Record a histogram metric"""
        if not self._enabled:
            return
            
        tags = tags or {}
        key = self._make_key(name, tags)
        
        if key not in self.metrics:
            self.metrics[key] = []
            
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            tags=tags,
            timestamp=time.time()
        )
        self.metrics[key].append(metric)
        
    def record_summary(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        quantiles: Optional[list] = None
    ):
        """Record a summary metric"""
        if not self._enabled:
            return
            
        tags = tags or {}
        key = self._make_key(name, tags)
        
        if key not in self.metrics:
            self.metrics[key] = []
            
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.SUMMARY,
            tags=tags,
            timestamp=time.time()
        )
        self.metrics[key].append(metric)
        
    def _make_key(self, name: str, tags: Dict[str, str]) -> str:
        """Create a unique key for metric name + tags"""
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def get_metrics(self) -> Dict[str, list]:
        """Get all collected metrics"""
        return self.metrics.copy()
    
    def clear_metrics(self):
        """Clear all metrics"""
        self.metrics.clear()
    
    def enable(self):
        """Enable metrics collection"""
        self._enabled = True
    
    def disable(self):
        """Disable metrics collection"""
        self._enabled = False


class LatencyTracker:
    """Context manager for tracking latency"""
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics_collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            self.metrics.record_histogram(self.metric_name, latency_ms, tags=self.tags)
            
            if exc_type:
                self.metrics.increment_counter(
                    f"{self.metric_name}_errors",
                    tags={**self.tags, "error_type": exc_type.__name__}
                )

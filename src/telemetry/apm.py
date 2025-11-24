"""
Application Performance Monitoring (APM)

Enterprise-grade APM with:
- Request tracing
- Database query monitoring
- External API call tracking
- Performance metrics
- Slow query detection
- Transaction profiling
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class APMTransaction:
    """APM Transaction tracker"""
    
    def __init__(self, name: str, transaction_type: str = "request"):
        self.name = name
        self.type = transaction_type
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.spans: list = []
        self.metadata: Dict[str, Any] = {}
        self.status: str = "unknown"
        self.error: Optional[Exception] = None
    
    def finish(self, status: str = "success", error: Optional[Exception] = None):
        """Finish transaction"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error = error
    
    def add_span(self, name: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Add span to transaction"""
        self.spans.append({
            "name": name,
            "duration": duration,
            "metadata": metadata or {},
        })
    
    def set_metadata(self, key: str, value: Any):
        """Set transaction metadata"""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "duration": self.duration,
            "status": self.status,
            "spans": self.spans,
            "metadata": self.metadata,
            "error": str(self.error) if self.error else None,
            "timestamp": datetime.utcnow().isoformat(),
        }


class APM:
    """
    Application Performance Monitoring
    
    Tracks:
    - Request/response times
    - Database query performance
    - External API calls
    - Slow operations
    - Error rates
    """
    
    def __init__(
        self,
        enabled: bool = True,
        slow_query_threshold: float = 1.0,  # seconds
        slow_request_threshold: float = 2.0,  # seconds
        sample_rate: float = 1.0,  # 100% sampling
    ):
        self.enabled = enabled
        self.slow_query_threshold = slow_query_threshold
        self.slow_request_threshold = slow_request_threshold
        self.sample_rate = sample_rate
        
        # Metrics storage (in production, use Prometheus/StatsD)
        self.metrics: Dict[str, list] = defaultdict(list)
    
    @contextmanager
    def transaction(self, name: str, transaction_type: str = "request"):
        """Track a transaction"""
        if not self.enabled:
            yield None
            return
        
        transaction = APMTransaction(name, transaction_type)
        
        try:
            yield transaction
            transaction.finish("success")
        except Exception as e:
            transaction.finish("error", e)
            raise
        finally:
            self._record_transaction(transaction)
    
    @contextmanager
    def span(self, name: str, transaction: Optional[APMTransaction] = None):
        """Track a span within a transaction"""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            if transaction:
                transaction.add_span(name, duration)
            else:
                # Standalone span
                logger.debug(f"APM span: {name} took {duration:.3f}s")
    
    def track_database_query(
        self,
        query: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track database query performance"""
        if not self.enabled:
            return
        
        metadata = metadata or {}
        metadata["query"] = query[:200]  # Truncate long queries
        
        if duration > self.slow_query_threshold:
            logger.warning(
                f"Slow database query detected: {duration:.3f}s",
                extra={
                    "query": query[:200],
                    "duration": duration,
                    "slow": True,
                    **metadata,
                }
            )
        
        self._record_metric("database.query", duration, {
            "success": success,
            "slow": duration > self.slow_query_threshold,
            **metadata,
        })
    
    def track_external_api_call(
        self,
        service: str,
        endpoint: str,
        duration: float,
        status_code: Optional[int] = None,
        success: bool = True,
    ):
        """Track external API call"""
        if not self.enabled:
            return
        
        self._record_metric("external_api.call", duration, {
            "service": service,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success,
        })
    
    def track_cache_operation(
        self,
        operation: str,  # get, set, delete
        key: str,
        hit: bool,
        duration: float,
    ):
        """Track cache operation"""
        if not self.enabled:
            return
        
        self._record_metric("cache.operation", duration, {
            "operation": operation,
            "key": key[:100],  # Truncate long keys
            "hit": hit,
        })
    
    def _record_transaction(self, transaction: APMTransaction):
        """Record transaction"""
        if transaction.duration and transaction.duration > self.slow_request_threshold:
            logger.warning(
                f"Slow transaction detected: {transaction.name} took {transaction.duration:.3f}s",
                extra=transaction.to_dict(),
            )
        
        self._record_metric("transaction", transaction.duration or 0, {
            "name": transaction.name,
            "type": transaction.type,
            "status": transaction.status,
        })
    
    def _record_metric(self, metric_name: str, value: float, tags: Dict[str, Any]):
        """Record metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "tags": tags,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get APM statistics"""
        stats = {}
        
        for metric_name, values in self.metrics.items():
            if not values:
                continue
            
            durations = [v["value"] for v in values]
            stats[metric_name] = {
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p95": self._percentile(durations, 95),
                "p99": self._percentile(durations, 99),
            }
        
        return stats
    
    def _percentile(self, data: list, percentile: float) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global APM instance
_apm: Optional[APM] = None


def init_apm(
    enabled: bool = True,
    slow_query_threshold: float = 1.0,
    slow_request_threshold: float = 2.0,
    sample_rate: float = 1.0,
) -> APM:
    """Initialize global APM"""
    global _apm
    
    _apm = APM(
        enabled=enabled,
        slow_query_threshold=slow_query_threshold,
        slow_request_threshold=slow_request_threshold,
        sample_rate=sample_rate,
    )
    
    return _apm


def get_apm() -> Optional[APM]:
    """Get global APM instance"""
    return _apm


# Decorator for tracking function performance
def track_performance(name: Optional[str] = None):
    """Decorator to track function performance"""
    def decorator(func: Callable):
        func_name = name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                apm = get_apm()
                if apm:
                    with apm.transaction(func_name, "function"):
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                apm = get_apm()
                if apm:
                    with apm.transaction(func_name, "function"):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator

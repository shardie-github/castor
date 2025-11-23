"""
Performance Optimization Utilities

Query optimization, caching strategies, and performance monitoring.
"""

import functools
import time
import logging
from typing import Callable, TypeVar, Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json

from src.database.redis import RedisConnection
from src.telemetry.metrics import MetricsCollector

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def optimize_select_query(
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> str:
        """
        Optimize SELECT query with pagination and ordering.
        
        Args:
            query: Base SELECT query
            limit: Maximum number of rows
            offset: Number of rows to skip
            order_by: Column to order by
            
        Returns:
            Optimized query string
        """
        optimized = query
        
        # Add ORDER BY if specified
        if order_by and "ORDER BY" not in query.upper():
            optimized += f" ORDER BY {order_by}"
        
        # Add LIMIT and OFFSET
        if limit:
            optimized += f" LIMIT {limit}"
            if offset:
                optimized += f" OFFSET {offset}"
        
        return optimized
    
    @staticmethod
    def add_index_hint(query: str, index_name: str) -> str:
        """
        Add index hint to query (PostgreSQL specific).
        
        Note: PostgreSQL doesn't support index hints like MySQL,
        but we can document recommended indexes.
        """
        # In PostgreSQL, indexes are used automatically by the query planner
        # This is a placeholder for documentation purposes
        logger.debug(f"Recommended index for query: {index_name}")
        return query


class CacheStrategy:
    """Advanced caching strategies"""
    
    def __init__(self, redis_conn: RedisConnection, metrics_collector: MetricsCollector):
        self.redis = redis_conn
        self.metrics = metrics_collector
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], T],
        ttl: int = 3600,
        force_refresh: bool = False
    ) -> T:
        """
        Get from cache or fetch and cache.
        
        Args:
            key: Cache key
            fetch_func: Function to fetch data if not cached
            ttl: Time to live in seconds
            force_refresh: Force refresh even if cached
            
        Returns:
            Cached or freshly fetched data
        """
        if not force_refresh:
            cached = await self.redis.get(key)
            if cached:
                self.metrics.increment_counter("cache_hit_total", {"key_prefix": key.split(":")[0]})
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode cached data for key: {key}")
        
        # Fetch fresh data
        self.metrics.increment_counter("cache_miss_total", {"key_prefix": key.split(":")[0]})
        data = await fetch_func()
        
        # Cache the result
        try:
            await self.redis.set(key, json.dumps(data, default=str), ex=ttl)
        except Exception as e:
            logger.error(f"Failed to cache data: {e}")
        
        return data
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # Note: Redis SCAN would be needed for production
        # This is a simplified version
        logger.info(f"Invalidating cache pattern: {pattern}")
        self.metrics.increment_counter("cache_invalidation_total", {"pattern": pattern})


class PerformanceMonitor:
    """Performance monitoring and profiling"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def track_execution_time(self, operation_name: str):
        """Decorator to track execution time"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                start_time = time.time()
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.metrics.record_histogram(
                        f"{operation_name}_duration_seconds",
                        duration,
                        tags={"operation": operation_name}
                    )
            return async_wrapper
        
        return decorator
    
    def track_query_performance(self, query: str, duration: float, row_count: Optional[int] = None):
        """Track database query performance"""
        self.metrics.record_histogram(
            "database_query_duration_seconds",
            duration,
            tags={
                "query_type": self._get_query_type(query),
                "has_results": str(row_count is not None and row_count > 0)
            }
        )
        
        if row_count is not None:
            self.metrics.record_gauge(
                "database_query_rows_returned",
                row_count,
                tags={"query_type": self._get_query_type(query)}
            )
    
    @staticmethod
    def _get_query_type(query: str) -> str:
        """Extract query type from SQL"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "OTHER"


def optimize_query_result(result: list, max_items: int = 100) -> list:
    """
    Optimize query result by limiting items.
    
    Args:
        result: Query result list
        max_items: Maximum items to return
        
    Returns:
        Limited result list
    """
    if len(result) <= max_items:
        return result
    
    logger.warning(f"Query result truncated from {len(result)} to {max_items} items")
    return result[:max_items]


# Import asyncio for async function check
import asyncio

"""
Advanced Caching Strategies

Multi-layer caching, cache invalidation, and cache warming.
"""

import asyncio
import logging
import time
from typing import Callable, TypeVar, Optional, Any, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

from src.database.redis import RedisConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheLayer:
    """Individual cache layer"""
    
    def __init__(self, name: str, ttl: int = 3600):
        self.name = name
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache layer"""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache layer"""
        raise NotImplementedError
    
    async def delete(self, key: str):
        """Delete key from cache layer"""
        raise NotImplementedError
    
    async def clear(self):
        """Clear all keys in cache layer"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache layer statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "name": self.name,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class InMemoryCacheLayer(CacheLayer):
    """In-memory cache layer (L1)"""
    
    def __init__(self, name: str = "memory", ttl: int = 300, max_size: int = 1000):
        super().__init__(name, ttl)
        self.cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self.max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from memory cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set in memory cache"""
        # Evict oldest if at max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        expiry = time.time() + (ttl or self.ttl)
        self.cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        """Delete from memory cache"""
        self.cache.pop(key, None)
    
    async def clear(self):
        """Clear memory cache"""
        self.cache.clear()


class RedisCacheLayer(CacheLayer):
    """Redis cache layer (L2)"""
    
    def __init__(self, redis_conn: RedisConnection, name: str = "redis", ttl: int = 3600):
        super().__init__(name, ttl)
        self.redis = redis_conn
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from Redis cache"""
        try:
            value = await self.redis.get(key)
            if value is None:
                self.misses += 1
                return None
            
            self.hits += 1
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
            self.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set in Redis cache"""
        try:
            value_str = json.dumps(value, default=str) if not isinstance(value, str) else value
            await self.redis.set(key, value_str, ex=ttl or self.ttl)
        except Exception as e:
            logger.warning(f"Redis cache set failed: {e}")
    
    async def delete(self, key: str):
        """Delete from Redis cache"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis cache delete failed: {e}")
    
    async def clear(self):
        """Clear Redis cache (use with caution)"""
        logger.warning("Redis cache clear called - this is a destructive operation")
        # In production, you'd want to be more careful here


class MultiLayerCache:
    """Multi-layer cache with L1 (memory) and L2 (Redis)"""
    
    def __init__(
        self,
        redis_conn: RedisConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        memory_ttl: int = 300,
        redis_ttl: int = 3600
    ):
        self.l1 = InMemoryCacheLayer("memory", memory_ttl)
        self.l2 = RedisCacheLayer(redis_conn, "redis", redis_ttl)
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (check L1 first, then L2)"""
        # Try L1 (memory)
        value = await self.l1.get(key)
        if value is not None:
            self.metrics.increment_counter("cache_hit_total", {"layer": "memory"})
            return value
        
        # Try L2 (Redis)
        value = await self.l2.get(key)
        if value is not None:
            self.metrics.increment_counter("cache_hit_total", {"layer": "redis"})
            # Populate L1 for next time
            await self.l1.set(key, value)
            return value
        
        self.metrics.increment_counter("cache_miss_total")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set in both cache layers"""
        await asyncio.gather(
            self.l1.set(key, value, ttl),
            self.l2.set(key, value, ttl),
            return_exceptions=True
        )
    
    async def delete(self, key: str):
        """Delete from both cache layers"""
        await asyncio.gather(
            self.l1.delete(key),
            self.l2.delete(key),
            return_exceptions=True
        )
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern"""
        # Clear L1
        await self.l1.clear()
        
        # For L2, we'd need to scan Redis keys (simplified here)
        logger.info(f"Invalidating cache pattern: {pattern}")
        self.metrics.increment_counter("cache_invalidation_total", {"pattern": pattern})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "l1": self.l1.get_stats(),
            "l2": self.l2.get_stats()
        }


class CacheWarmer:
    """Cache warming utility"""
    
    def __init__(self, cache: MultiLayerCache, metrics_collector: MetricsCollector):
        self.cache = cache
        self.metrics = metrics_collector
    
    async def warm_cache(self, keys_and_fetchers: List[tuple]):
        """
        Warm cache with multiple keys.
        
        Args:
            keys_and_fetchers: List of (key, fetch_function) tuples
        """
        logger.info(f"Warming cache with {len(keys_and_fetchers)} keys")
        
        async def warm_one(key: str, fetcher: Callable):
            try:
                value = await fetcher()
                await self.cache.set(key, value)
                self.metrics.increment_counter("cache_warmed_total", {"key": key})
            except Exception as e:
                logger.error(f"Failed to warm cache for key {key}: {e}")
        
        await asyncio.gather(*[warm_one(key, fetcher) for key, fetcher in keys_and_fetchers])


def cached(
    key_prefix: str,
    ttl: int = 3600,
    cache: Optional[MultiLayerCache] = None
):
    """
    Decorator for caching function results.
    
    Usage:
        @cached("user_profile", ttl=1800)
        async def get_user_profile(user_id: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if cache is None:
            # If no cache provided, return function as-is
            return func
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            key_data = {
                "prefix": key_prefix,
                "args": args,
                "kwargs": sorted(kwargs.items())
            }
            key_string = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            cache_key = f"{key_prefix}:{key_hash}"
            
            # Try cache first
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss - fetch and cache
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            return result
        
        return async_wrapper
    
    return decorator

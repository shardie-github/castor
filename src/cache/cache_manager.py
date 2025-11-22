"""
Cache Manager

Provides caching layer for frequently accessed data.
Uses Redis if available, falls back to in-memory cache.
"""

import logging
import json
from typing import Optional, Any, Dict
from datetime import timedelta
import hashlib

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache Manager
    
    Provides caching with TTL support.
    Uses Redis if available, otherwise falls back to in-memory cache.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_cache: Dict[str, tuple[Any, float]] = {}
        self._use_redis = redis_client is not None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self._use_redis:
            try:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed, falling back to memory: {e}")
                self._use_redis = False
        
        # Fallback to memory cache
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            import time
            if time.time() < expiry:
                return value
            else:
                del self._memory_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        if self._use_redis:
            try:
                await self.redis.setex(key, ttl_seconds, json.dumps(value))
                return
            except Exception as e:
                logger.warning(f"Redis set failed, falling back to memory: {e}")
                self._use_redis = False
        
        # Fallback to memory cache
        import time
        expiry = time.time() + ttl_seconds
        self._memory_cache[key] = (value, expiry)
        
        # Clean up expired entries periodically
        if len(self._memory_cache) > 1000:
            self._cleanup_expired()
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if self._use_redis:
            try:
                await self.redis.delete(key)
                return
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        if key in self._memory_cache:
            del self._memory_cache[key]
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if self._use_redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                return
            except Exception as e:
                logger.warning(f"Redis pattern invalidation failed: {e}")
        
        # Fallback: delete matching keys from memory
        import re
        regex = re.compile(pattern.replace('*', '.*'))
        keys_to_delete = [k for k in self._memory_cache.keys() if regex.match(k)]
        for key in keys_to_delete:
            del self._memory_cache[key]
    
    def _cleanup_expired(self):
        """Remove expired entries from memory cache"""
        import time
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._memory_cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self._memory_cache[key]
    
    @staticmethod
    def make_cache_key(*parts: str, prefix: str = "") -> str:
        """Generate a cache key from parts"""
        key = ":".join(str(p) for p in parts)
        if prefix:
            key = f"{prefix}:{key}"
        return key
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash a key for consistent length"""
        return hashlib.md5(key.encode()).hexdigest()

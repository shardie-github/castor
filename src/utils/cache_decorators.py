"""
Cache Decorators

Provides decorators for caching function results with TTL support.
"""

import functools
import inspect
import hashlib
import json
import logging
from typing import Callable, Optional, Any, TypeVar
from datetime import timedelta

from src.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


def cached(
    ttl_seconds: int = 300,
    key_prefix: str = "",
    cache_manager: Optional[CacheManager] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
        cache_manager: CacheManager instance (if None, will try to get from context)
        key_func: Custom function to generate cache key from args/kwargs
    
    Usage:
        @cached(ttl_seconds=600, key_prefix="podcast")
        async def get_podcast(podcast_id: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get cache manager
            cache = cache_manager
            if cache is None:
                # Try to get from function context (if available)
                # This is a fallback - ideally cache_manager should be injected
                cache = getattr(wrapper, '_cache_manager', None)
            
            if cache is None:
                # No cache available, just execute function
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: str = ""
) -> str:
    """Generate cache key from function and arguments"""
    # Get function name
    func_name = func.__name__
    
    # Serialize arguments
    try:
        args_str = json.dumps(args, default=str, sort_keys=True)
        kwargs_str = json.dumps(kwargs, default=str, sort_keys=True)
        key_data = f"{func_name}:{args_str}:{kwargs_str}"
    except (TypeError, ValueError):
        # Fallback for non-serializable arguments
        key_data = f"{func_name}:{str(args)}:{str(kwargs)}"
    
    # Hash for consistent length
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    
    # Build final key
    if prefix:
        return f"{prefix}:{func_name}:{key_hash}"
    return f"{func_name}:{key_hash}"


def invalidate_cache(
    pattern: str,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator to invalidate cache entries after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate (supports wildcards)
        cache_manager: CacheManager instance
    
    Usage:
        @invalidate_cache("podcast:*")
        async def update_podcast(podcast_id: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Execute function
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Invalidate cache
            cache = cache_manager
            if cache is None:
                cache = getattr(wrapper, '_cache_manager', None)
            
            if cache:
                await cache.invalidate_pattern(pattern)
                logger.debug(f"Invalidated cache pattern: {pattern}")
            
            return result
        
        return wrapper
    return decorator

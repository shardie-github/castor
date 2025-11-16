"""
Rate Limiting Middleware

Provides per-endpoint rate limiting using Redis.
"""

import time
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis"""
    
    def __init__(
        self,
        redis_conn: redis.Redis,
        calls: int = 60,
        period: int = 60,
        key_prefix: str = "rate_limit"
    ):
        self.redis_conn = redis_conn
        self.calls = calls
        self.period = period
        self.key_prefix = key_prefix
    
    async def _get_key(self, identifier: str) -> str:
        """Get Redis key for rate limit"""
        return f"{self.key_prefix}:{identifier}:{int(time.time() / self.period)}"
    
    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, info_dict)
        """
        key = await self._get_key(identifier)
        
        try:
            # Increment counter
            current = await self.redis_conn.incr(key)
            
            # Set expiration if this is the first request in this window
            if current == 1:
                await self.redis_conn.expire(key, self.period)
            
            # Check if limit exceeded
            is_allowed = current <= self.calls
            
            # Calculate remaining
            remaining = max(0, self.calls - current)
            reset_time = int(time.time() / self.period) * self.period + self.period
            
            return is_allowed, {
                "limit": self.calls,
                "remaining": remaining,
                "reset": reset_time
            }
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if Redis fails
            return True, {"limit": self.calls, "remaining": self.calls, "reset": 0}


def create_rate_limiter(
    redis_conn: redis.Redis,
    calls: int = 60,
    period: int = 60
) -> RateLimiter:
    """Create a rate limiter instance"""
    return RateLimiter(redis_conn, calls=calls, period=period)


async def rate_limit_middleware(
    request: Request,
    call_next: Callable,
    redis_conn: Optional[redis.Redis] = None
):
    """Rate limiting middleware"""
    if not redis_conn:
        # Skip rate limiting if Redis not available
        return await call_next(request)
    
    # Get identifier (IP address or user ID)
    identifier = request.client.host
    if hasattr(request.state, 'user_id'):
        identifier = f"user:{request.state.user_id}"
    
    # Get rate limit config from endpoint
    rate_limit_config = getattr(request.scope.get("endpoint"), "__rate_limit__", None)
    
    if rate_limit_config:
        calls = rate_limit_config.get("calls", 60)
        period = rate_limit_config.get("period", 60)
        limiter = RateLimiter(redis_conn, calls=calls, period=period)
    else:
        # Default rate limit
        limiter = RateLimiter(redis_conn, calls=60, period=60)
    
    # Check rate limit
    is_allowed, info = await limiter.is_allowed(identifier)
    
    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "limit": info["limit"],
                "remaining": info["remaining"],
                "reset": info["reset"]
            },
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset"])
            }
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset"])
    
    return response


def rate_limit(calls: int = 60, period: int = 60):
    """
    Decorator to add rate limiting to an endpoint.
    
    Usage:
        @router.get("/endpoint")
        @rate_limit(calls=100, period=60)
        async def endpoint():
            ...
    """
    def decorator(func):
        func.__rate_limit__ = {"calls": calls, "period": period}
        return func
    return decorator

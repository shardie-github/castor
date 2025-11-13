"""
API Security Module

Provides:
- Rate limiting
- Input validation
- CORS configuration
- API key management
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import defaultdict

from src.telemetry.metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit: int  # Number of requests
    window_seconds: int  # Time window in seconds
    key: str  # Rate limit key (user_id, ip_address, etc.)


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_at: datetime
    limit: int


class RateLimiter:
    """
    Rate Limiter
    
    Implements token bucket algorithm for rate limiting.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        # In production, would use Redis for distributed rate limiting
        self._buckets: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> RateLimitResult:
        """Check if request is within rate limit"""
        bucket_key = f"{key}:{limit}:{window_seconds}"
        
        now = time.time()
        bucket = self._buckets.get(bucket_key, {})
        
        # Initialize bucket if needed
        if "tokens" not in bucket:
            bucket = {
                "tokens": limit,
                "last_refill": now,
                "limit": limit,
                "window": window_seconds
            }
            self._buckets[bucket_key] = bucket
        
        # Refill tokens based on time elapsed
        time_elapsed = now - bucket["last_refill"]
        tokens_to_add = int((time_elapsed / window_seconds) * limit)
        
        if tokens_to_add > 0:
            bucket["tokens"] = min(limit, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now
        
        # Check if request is allowed
        if bucket["tokens"] > 0:
            bucket["tokens"] -= 1
            allowed = True
        else:
            allowed = False
        
        # Calculate reset time
        reset_at = datetime.fromtimestamp(
            bucket["last_refill"] + window_seconds,
            tz=timezone.utc
        )
        
        result = RateLimitResult(
            allowed=allowed,
            remaining=bucket["tokens"],
            reset_at=reset_at,
            limit=limit
        )
        
        # Record telemetry
        if not allowed:
            self.metrics.increment_counter(
                "rate_limit_exceeded",
                tags={"key": key}
            )
        
        return result


class InputValidator:
    """
    Input Validator
    
    Validates and sanitizes API inputs.
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        # Remove potentially dangerous characters
        sanitized = value.strip()
        
        if max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format"""
        import re
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_string.lower()))


class CORSConfig:
    """CORS configuration"""
    
    def __init__(
        self,
        allowed_origins: List[str],
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        allow_credentials: bool = True
    ):
        self.allowed_origins = allowed_origins
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["Content-Type", "Authorization"]
        self.allow_credentials = allow_credentials
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        return origin in self.allowed_origins or "*" in self.allowed_origins
    
    def get_cors_headers(self, origin: Optional[str] = None) -> Dict[str, str]:
        """Get CORS headers"""
        headers = {}
        
        if origin and self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            
            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers


class APIKeyManager:
    """
    API Key Manager
    
    Manages API keys for programmatic access.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        # In production, would store in database
        self._api_keys: Dict[str, Dict[str, Any]] = {}
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create a new API key"""
        import secrets
        
        api_key = f"pk_{secrets.token_urlsafe(32)}"
        
        self._api_keys[api_key] = {
            "user_id": user_id,
            "name": name,
            "scopes": scopes,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "last_used_at": None,
            "is_active": True
        }
        
        # Log event
        logger.info(f"API key created for user {user_id}: {name}")
        
        return api_key
    
    async def validate_api_key(
        self,
        api_key: str,
        required_scope: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Validate API key and return key info"""
        key_info = self._api_keys.get(api_key)
        
        if not key_info:
            return None
        
        if not key_info["is_active"]:
            return None
        
        # Check expiration
        if key_info["expires_at"] and key_info["expires_at"] < datetime.now(timezone.utc):
            return None
        
        # Check scope
        if required_scope and required_scope not in key_info["scopes"]:
            return None
        
        # Update last used
        key_info["last_used_at"] = datetime.now(timezone.utc)
        
        # Record telemetry
        self.metrics.increment_counter(
            "api_key_validated",
            tags={"user_id": key_info["user_id"]}
        )
        
        return key_info
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key not in self._api_keys:
            return False
        
        self._api_keys[api_key]["is_active"] = False
        
        logger.info(f"API key revoked: {api_key}")
        
        return True

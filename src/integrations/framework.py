"""
Integration Framework

Provides base classes and utilities for all integrations.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
import asyncio
import aiohttp
from functools import wraps

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"


class IntegrationType(Enum):
    """Integration types"""
    HOSTING = "hosting"
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"


class IntegrationBase(ABC):
    """
    Base class for all integrations
    
    Provides common functionality:
    - OAuth token management
    - Rate limiting
    - Error handling and retries
    - Webhook handling
    - Health monitoring
    """
    
    def __init__(
        self,
        integration_name: str,
        integration_type: IntegrationType,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.integration_name = integration_name
        self.integration_type = integration_type
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
        self._rate_limit_cache: Dict[str, Any] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize integration"""
        self._session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Cleanup integration"""
        if self._session:
            await self._session.close()
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with integration provider"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to integration"""
        pass
    
    @abstractmethod
    async def sync_data(self, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Sync data from integration"""
        pass
    
    async def get_oauth_token(
        self,
        tenant_id: str,
        refresh: bool = False
    ) -> Optional[str]:
        """Get OAuth token for tenant"""
        # Get token from database
        row = await self.postgres.fetchrow(
            """
            SELECT token_value, expires_at, refresh_token
            FROM integration_tokens
            WHERE tenant_id = $1 AND integration_name = $2
            """,
            tenant_id, self.integration_name
        )
        
        if not row:
            return None
        
        # Check if token is expired
        if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc):
            if refresh and row["refresh_token"]:
                # Refresh token
                return await self._refresh_oauth_token(tenant_id, row["refresh_token"])
            return None
        
        return row["token_value"]
    
    async def store_oauth_token(
        self,
        tenant_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ):
        """Store OAuth token"""
        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        await self.postgres.execute(
            """
            INSERT INTO integration_tokens (
                token_id, tenant_id, integration_name, token_value,
                refresh_token, expires_at, updated_at
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
            ON CONFLICT (tenant_id, integration_name)
            DO UPDATE SET
                token_value = $3,
                refresh_token = COALESCE($4, integration_tokens.refresh_token),
                expires_at = $5,
                updated_at = NOW()
            """,
            tenant_id, self.integration_name, access_token, refresh_token, expires_at
        )
    
    async def _refresh_oauth_token(
        self,
        tenant_id: str,
        refresh_token: str
    ) -> Optional[str]:
        """Refresh OAuth token"""
        # In production, call OAuth refresh endpoint
        # For now, return None (implementation depends on provider)
        logger.warning(f"Token refresh not implemented for {self.integration_name}")
        return None
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make HTTP request with rate limiting and retries
        """
        # Check rate limit
        await self._check_rate_limit(url)
        
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self._session:
                    await self.initialize()
                
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    # Check for rate limit errors
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Record metrics
                    self.metrics.increment_counter(
                        "integration_request",
                        tags={
                            "integration": self.integration_name,
                            "method": method,
                            "status_code": str(response.status)
                        }
                    )
                    
                    return response
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Request failed after retries")
    
    async def _check_rate_limit(self, endpoint: str):
        """Check and enforce rate limits"""
        rate_limit_key = f"{self.integration_name}:{endpoint}"
        
        # Get rate limit config
        rate_limit = await self._get_rate_limit()
        
        if rate_limit_key in self._rate_limit_cache:
            last_request_time, request_count = self._rate_limit_cache[rate_limit_key]
            
            # Reset if time window passed
            if (datetime.now(timezone.utc) - last_request_time).total_seconds() > 60:
                self._rate_limit_cache[rate_limit_key] = (
                    datetime.now(timezone.utc), 1
                )
            elif request_count >= rate_limit:
                # Rate limit exceeded
                wait_time = 60 - (datetime.now(timezone.utc) - last_request_time).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self._rate_limit_cache[rate_limit_key] = (
                    datetime.now(timezone.utc), 1
                )
            else:
                self._rate_limit_cache[rate_limit_key] = (
                    last_request_time, request_count + 1
                )
        else:
            self._rate_limit_cache[rate_limit_key] = (
                datetime.now(timezone.utc), 1
            )
    
    async def _get_rate_limit(self) -> int:
        """Get rate limit for integration"""
        # Default: 100 requests per minute
        return 100
    
    async def handle_webhook(
        self,
        tenant_id: str,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook
        
        Args:
            tenant_id: Tenant ID
            webhook_data: Webhook payload
            signature: Webhook signature for verification
            
        Returns:
            Response data
        """
        # Verify webhook signature
        if signature and not await self._verify_webhook_signature(webhook_data, signature):
            raise ValueError("Invalid webhook signature")
        
        # Process webhook
        result = await self._process_webhook(tenant_id, webhook_data)
        
        # Log event
        await self.events.log_event(
            event_type="webhook_received",
            user_id=None,
            properties={
                "integration": self.integration_name,
                "tenant_id": tenant_id,
                "webhook_type": webhook_data.get("type")
            }
        )
        
        return result
    
    async def _verify_webhook_signature(
        self,
        webhook_data: Dict[str, Any],
        signature: str
    ) -> bool:
        """Verify webhook signature"""
        # In production, implement signature verification
        # For now, return True
        return True
    
    async def _process_webhook(
        self,
        tenant_id: str,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process webhook data"""
        # Override in subclasses
        return {"status": "processed"}
    
    async def check_health(self) -> Dict[str, Any]:
        """Check integration health"""
        try:
            is_connected = await self.test_connection()
            
            return {
                "integration": self.integration_name,
                "status": "healthy" if is_connected else "unhealthy",
                "connected": is_connected,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "integration": self.integration_name,
                "status": "error",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }


def rate_limited(requests_per_minute: int = 60):
    """Decorator for rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, backoff: float = 1.0):
    """Decorator for retry logic"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(backoff * (2 ** attempt))
            return None
        return wrapper
    return decorator

"""
API Key Management

Manages API keys for programmatic access.
"""

import logging
import hashlib
import secrets
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    API Key Manager
    
    Manages API key generation, validation, and rotation.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def create_api_key(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        permissions: Optional[List[str]] = None,
        rate_limit_per_hour: int = 1000,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, str]:
        """
        Create new API key
        
        Returns:
            Dictionary with key_id and api_key (only shown once)
        """
        # Generate API key
        api_key = self._generate_api_key()
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:8]  # First 8 chars for identification
        
        key_id = str(uuid4())
        
        # Store in database
        await self.postgres.execute(
            """
            INSERT INTO api_keys (
                key_id, tenant_id, user_id, key_hash, key_prefix, name,
                permissions, rate_limit_per_hour, expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            key_id, tenant_id, user_id, key_hash, key_prefix, name,
            permissions or [], rate_limit_per_hour, expires_at
        )
        
        # Log event
        await self.events.log_event(
            event_type="api_key_created",
            user_id=user_id,
            properties={"key_id": key_id, "name": name}
        )
        
        return {
            "key_id": key_id,
            "api_key": api_key,  # Only shown once
            "key_prefix": key_prefix
        }
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info"""
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:8]
        
        # Look up key by prefix first (faster)
        row = await self.postgres.fetchrow(
            """
            SELECT key_id, tenant_id, user_id, permissions, rate_limit_per_hour,
                   expires_at, revoked, last_used_at
            FROM api_keys
            WHERE key_prefix = $1 AND revoked = FALSE
            """,
            key_prefix
        )
        
        if not row:
            return None
        
        # Verify hash matches
        stored_hash = await self.postgres.fetchval(
            "SELECT key_hash FROM api_keys WHERE key_id = $1",
            row["key_id"]
        )
        
        if not self._verify_hash(api_key, stored_hash):
            return None
        
        # Check expiration
        if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc):
            return None
        
        # Update last used
        await self.postgres.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE key_id = $1",
            row["key_id"]
        )
        
        return {
            "key_id": str(row["key_id"]),
            "tenant_id": str(row["tenant_id"]),
            "user_id": str(row["user_id"]),
            "permissions": row["permissions"] or [],
            "rate_limit_per_hour": row["rate_limit_per_hour"]
        }
    
    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke API key"""
        await self.postgres.execute(
            """
            UPDATE api_keys
            SET revoked = TRUE, revoked_at = NOW()
            WHERE key_id = $1 AND user_id = $2
            """,
            key_id, user_id
        )
        
        # Log event
        await self.events.log_event(
            event_type="api_key_revoked",
            user_id=user_id,
            properties={"key_id": key_id}
        )
        
        return True
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        # Generate 32-byte random key, base64 encoded
        return secrets.token_urlsafe(32)
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _verify_hash(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash"""
        return self._hash_key(api_key) == stored_hash

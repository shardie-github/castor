"""
Feature Flag Service

Provides runtime feature flag management with database-backed configuration.
Supports per-tenant flags, gradual rollouts, and A/B testing.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureFlagStatus(Enum):
    """Feature flag status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    GRADUAL_ROLLOUT = "gradual_rollout"


class FeatureFlagService:
    """
    Feature Flag Service
    
    Manages feature flags with support for:
    - Global flags
    - Per-tenant flags
    - Gradual rollouts
    - A/B testing
    """
    
    def __init__(self, postgres_conn):
        self.postgres_conn = postgres_conn
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 60  # Cache for 60 seconds
    
    async def initialize(self):
        """Initialize feature flag service"""
        # Create feature_flags table if it doesn't exist
        await self._ensure_table_exists()
        # Load flags into cache
        await self._refresh_cache()
    
    async def _ensure_table_exists(self):
        """Ensure feature_flags table exists"""
        query = """
            CREATE TABLE IF NOT EXISTS feature_flags (
                flag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flag_name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(50) NOT NULL DEFAULT 'disabled',
                rollout_percentage INTEGER DEFAULT 0,
                tenant_id UUID,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_feature_flags_name ON feature_flags(flag_name);
            CREATE INDEX IF NOT EXISTS idx_feature_flags_tenant ON feature_flags(tenant_id);
        """
        try:
            await self.postgres_conn.execute(query)
        except Exception as e:
            logger.warning(f"Feature flags table creation skipped: {e}")
    
    async def _refresh_cache(self):
        """Refresh feature flag cache"""
        try:
            query = """
                SELECT flag_name, status, rollout_percentage, tenant_id, metadata
                FROM feature_flags
                WHERE status IN ('enabled', 'gradual_rollout')
            """
            flags = await self.postgres_conn.fetch(query)
            
            self._cache = {}
            for flag in flags:
                key = self._cache_key(flag['flag_name'], flag.get('tenant_id'))
                self._cache[key] = {
                    'status': flag['status'],
                    'rollout_percentage': flag['rollout_percentage'],
                    'metadata': flag.get('metadata', {})
                }
        except Exception as e:
            logger.warning(f"Failed to refresh feature flag cache: {e}")
    
    def _cache_key(self, flag_name: str, tenant_id: Optional[str] = None) -> str:
        """Generate cache key"""
        if tenant_id:
            return f"{flag_name}:{tenant_id}"
        return f"{flag_name}:global"
    
    async def is_enabled(
        self,
        flag_name: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            tenant_id: Optional tenant ID for per-tenant flags
            user_id: Optional user ID for gradual rollouts
        
        Returns:
            True if feature is enabled, False otherwise
        """
        # Check cache first
        cache_key = self._cache_key(flag_name, tenant_id)
        if cache_key in self._cache:
            flag_data = self._cache[cache_key]
            return self._evaluate_flag(flag_data, user_id)
        
        # Check database
        try:
            query = """
                SELECT status, rollout_percentage, metadata
                FROM feature_flags
                WHERE flag_name = $1
                AND (tenant_id = $2 OR tenant_id IS NULL)
                ORDER BY tenant_id DESC NULLS LAST
                LIMIT 1
            """
            flag = await self.postgres_conn.fetchrow(query, flag_name, tenant_id)
            
            if flag:
                flag_data = {
                    'status': flag['status'],
                    'rollout_percentage': flag['rollout_percentage'],
                    'metadata': flag.get('metadata', {})
                }
                # Update cache
                self._cache[cache_key] = flag_data
                return self._evaluate_flag(flag_data, user_id)
        except Exception as e:
            logger.error(f"Error checking feature flag {flag_name}: {e}")
        
        # Fall back to environment variable
        env_key = f"ENABLE_{flag_name.upper().replace('-', '_')}"
        return os.getenv(env_key, "false").lower() == "true"
    
    def _evaluate_flag(self, flag_data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Evaluate feature flag based on status and rollout"""
        status = flag_data.get('status')
        
        if status == 'disabled':
            return False
        elif status == 'enabled':
            return True
        elif status == 'gradual_rollout':
            rollout_percentage = flag_data.get('rollout_percentage', 0)
            if user_id:
                # Use user_id hash for consistent rollout
                hash_value = hash(user_id) % 100
                return hash_value < rollout_percentage
            return False
        
        return False
    
    async def set_flag(
        self,
        flag_name: str,
        status: str,
        tenant_id: Optional[str] = None,
        rollout_percentage: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Set a feature flag"""
        query = """
            INSERT INTO feature_flags (flag_name, status, tenant_id, rollout_percentage, metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (flag_name) 
            DO UPDATE SET
                status = EXCLUDED.status,
                tenant_id = EXCLUDED.tenant_id,
                rollout_percentage = EXCLUDED.rollout_percentage,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
        """
        await self.postgres_conn.execute(
            query,
            flag_name,
            status,
            tenant_id,
            rollout_percentage,
            metadata or {}
        )
        # Refresh cache
        await self._refresh_cache()
    
    async def get_flag(self, flag_name: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get feature flag configuration"""
        query = """
            SELECT flag_name, status, rollout_percentage, tenant_id, metadata, created_at, updated_at
            FROM feature_flags
            WHERE flag_name = $1
            AND (tenant_id = $2 OR tenant_id IS NULL)
            ORDER BY tenant_id DESC NULLS LAST
            LIMIT 1
        """
        flag = await self.postgres_conn.fetchrow(query, flag_name, tenant_id)
        if flag:
            return dict(flag)
        return None
    
    async def list_flags(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all feature flags"""
        if tenant_id:
            query = """
                SELECT flag_name, status, rollout_percentage, tenant_id, metadata
                FROM feature_flags
                WHERE tenant_id = $1 OR tenant_id IS NULL
                ORDER BY flag_name
            """
            flags = await self.postgres_conn.fetch(query, tenant_id)
        else:
            query = """
                SELECT flag_name, status, rollout_percentage, tenant_id, metadata
                FROM feature_flags
                ORDER BY flag_name
            """
            flags = await self.postgres_conn.fetch(query)
        
        return [dict(flag) for flag in flags]


# Global instance (will be initialized in main.py)
_feature_flag_service: Optional[FeatureFlagService] = None


def get_feature_flag_service() -> Optional[FeatureFlagService]:
    """Get global feature flag service instance"""
    return _feature_flag_service


async def get_feature_flag(
    flag_name: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """Convenience function to check feature flag"""
    service = get_feature_flag_service()
    if service:
        return await service.is_enabled(flag_name, tenant_id, user_id)
    
    # Fall back to environment variable
    env_key = f"ENABLE_{flag_name.upper().replace('-', '_')}"
    return os.getenv(env_key, "false").lower() == "true"

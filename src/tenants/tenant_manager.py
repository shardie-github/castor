"""
Tenant Management Module

Manages tenant CRUD operations, quotas, and settings.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class Tenant:
    """Tenant data structure"""
    tenant_id: str
    name: str
    slug: str
    domain: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    billing_email: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantQuota:
    """Tenant quota configuration"""
    tenant_id: str
    quota_type: str  # 'api_calls', 'storage_gb', 'users', 'campaigns', etc.
    limit_value: int
    current_usage: int = 0
    reset_period: str = "monthly"  # 'daily', 'weekly', 'monthly'
    last_reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TenantSettings:
    """Tenant settings"""
    tenant_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """
    Tenant Manager
    
    Manages tenant CRUD operations, quotas, and settings with database persistence.
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
    
    async def create_tenant(
        self,
        name: str,
        slug: str,
        domain: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        billing_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a new tenant"""
        tenant_id = str(uuid4())
        
        # Check if slug already exists
        existing = await self.get_tenant_by_slug(slug)
        if existing:
            raise ValueError(f"Tenant with slug '{slug}' already exists")
        
        # Insert tenant
        await self.postgres.execute(
            """
            INSERT INTO tenants (tenant_id, name, slug, domain, subscription_tier, status, billing_email, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            tenant_id, name, slug, domain, subscription_tier.value, TenantStatus.ACTIVE.value,
            billing_email, metadata or {}
        )
        
        # Initialize default quotas based on tier
        await self._initialize_default_quotas(tenant_id, subscription_tier)
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            domain=domain,
            subscription_tier=subscription_tier,
            status=TenantStatus.ACTIVE,
            billing_email=billing_email,
            metadata=metadata or {}
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "tenant_created",
            tags={"subscription_tier": subscription_tier.value}
        )
        
        # Log event
        await self.events.log_event(
            event_type="tenant_created",
            user_id=None,  # System event
            properties={
                "tenant_id": tenant_id,
                "slug": slug,
                "subscription_tier": subscription_tier.value
            }
        )
        
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        row = await self.postgres.fetchrow(
            """
            SELECT tenant_id, name, slug, domain, subscription_tier, status, billing_email,
                   created_at, updated_at, metadata
            FROM tenants
            WHERE tenant_id = $1
            """,
            tenant_id
        )
        
        if not row:
            return None
        
        return Tenant(
            tenant_id=str(row["tenant_id"]),
            name=row["name"],
            slug=row["slug"],
            domain=row["domain"],
            subscription_tier=SubscriptionTier(row["subscription_tier"]),
            status=TenantStatus(row["status"]),
            billing_email=row["billing_email"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=row["metadata"] or {}
        )
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        row = await self.postgres.fetchrow(
            """
            SELECT tenant_id, name, slug, domain, subscription_tier, status, billing_email,
                   created_at, updated_at, metadata
            FROM tenants
            WHERE slug = $1
            """,
            slug
        )
        
        if not row:
            return None
        
        return Tenant(
            tenant_id=str(row["tenant_id"]),
            name=row["name"],
            slug=row["slug"],
            domain=row["domain"],
            subscription_tier=SubscriptionTier(row["subscription_tier"]),
            status=TenantStatus(row["status"]),
            billing_email=row["billing_email"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=row["metadata"] or {}
        )
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        row = await self.postgres.fetchrow(
            """
            SELECT tenant_id, name, slug, domain, subscription_tier, status, billing_email,
                   created_at, updated_at, metadata
            FROM tenants
            WHERE domain = $1
            """,
            domain
        )
        
        if not row:
            return None
        
        return Tenant(
            tenant_id=str(row["tenant_id"]),
            name=row["name"],
            slug=row["slug"],
            domain=row["domain"],
            subscription_tier=SubscriptionTier(row["subscription_tier"]),
            status=TenantStatus(row["status"]),
            billing_email=row["billing_email"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=row["metadata"] or {}
        )
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Tenant]:
        """Update tenant"""
        set_clauses = []
        values = []
        param_index = 1
        
        allowed_updates = ["name", "domain", "subscription_tier", "status", "billing_email", "metadata"]
        
        for key, value in updates.items():
            if key in allowed_updates:
                if key == "subscription_tier" and isinstance(value, SubscriptionTier):
                    value = value.value
                elif key == "status" and isinstance(value, TenantStatus):
                    value = value.value
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1
        
        if not set_clauses:
            return await self.get_tenant(tenant_id)
        
        set_clauses.append(f"updated_at = ${param_index}")
        values.append(datetime.now(timezone.utc))
        param_index += 1
        
        values.append(tenant_id)
        
        await self.postgres.execute(
            f"""
            UPDATE tenants
            SET {', '.join(set_clauses)}
            WHERE tenant_id = ${param_index}
            """,
            *values
        )
        
        # If subscription tier changed, update quotas
        if "subscription_tier" in updates:
            await self._update_quotas_for_tier(tenant_id, SubscriptionTier(updates["subscription_tier"]))
        
        # Log event
        await self.events.log_event(
            event_type="tenant_updated",
            user_id=None,
            properties={
                "tenant_id": tenant_id,
                "updated_fields": list(updates.keys())
            }
        )
        
        return await self.get_tenant(tenant_id)
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete by setting status to cancelled)"""
        await self.postgres.execute(
            """
            UPDATE tenants
            SET status = 'cancelled', updated_at = NOW()
            WHERE tenant_id = $1
            """,
            tenant_id
        )
        
        # Log event
        await self.events.log_event(
            event_type="tenant_deleted",
            user_id=None,
            properties={"tenant_id": tenant_id}
        )
        
        return True
    
    async def get_tenant_quota(self, tenant_id: str, quota_type: str) -> Optional[TenantQuota]:
        """Get tenant quota"""
        row = await self.postgres.fetchrow(
            """
            SELECT tenant_id, quota_type, limit_value, current_usage, reset_period, last_reset_at
            FROM tenant_quotas
            WHERE tenant_id = $1 AND quota_type = $2
            """,
            tenant_id, quota_type
        )
        
        if not row:
            return None
        
        return TenantQuota(
            tenant_id=str(row["tenant_id"]),
            quota_type=row["quota_type"],
            limit_value=row["limit_value"],
            current_usage=row["current_usage"],
            reset_period=row["reset_period"],
            last_reset_at=row["last_reset_at"]
        )
    
    async def check_quota(self, tenant_id: str, quota_type: str, requested_amount: int = 1) -> bool:
        """Check if tenant has quota available"""
        quota = await self.get_tenant_quota(tenant_id, quota_type)
        if not quota:
            return False
        
        return (quota.current_usage + requested_amount) <= quota.limit_value
    
    async def increment_quota_usage(self, tenant_id: str, quota_type: str, amount: int = 1) -> bool:
        """Increment quota usage"""
        quota = await self.get_tenant_quota(tenant_id, quota_type)
        if not quota:
            return False
        
        if (quota.current_usage + amount) > quota.limit_value:
            return False
        
        await self.postgres.execute(
            """
            UPDATE tenant_quotas
            SET current_usage = current_usage + $1, updated_at = NOW()
            WHERE tenant_id = $2 AND quota_type = $3
            """,
            amount, tenant_id, quota_type
        )
        
        return True
    
    async def reset_quota(self, tenant_id: str, quota_type: str) -> bool:
        """Reset quota usage"""
        await self.postgres.execute(
            """
            UPDATE tenant_quotas
            SET current_usage = 0, last_reset_at = NOW(), updated_at = NOW()
            WHERE tenant_id = $1 AND quota_type = $2
            """,
            tenant_id, quota_type
        )
        
        return True
    
    async def get_tenant_settings(self, tenant_id: str) -> Dict[str, Any]:
        """Get all tenant settings"""
        rows = await self.postgres.fetch(
            """
            SELECT setting_key, setting_value
            FROM tenant_settings
            WHERE tenant_id = $1
            """,
            tenant_id
        )
        
        return {row["setting_key"]: row["setting_value"] for row in rows}
    
    async def set_tenant_setting(self, tenant_id: str, key: str, value: Any) -> bool:
        """Set tenant setting"""
        import json
        await self.postgres.execute(
            """
            INSERT INTO tenant_settings (tenant_id, setting_key, setting_value, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (tenant_id, setting_key)
            DO UPDATE SET setting_value = $3, updated_at = NOW()
            """,
            tenant_id, key, json.dumps(value) if not isinstance(value, (dict, list)) else value
        )
        
        return True
    
    async def _initialize_default_quotas(self, tenant_id: str, tier: SubscriptionTier):
        """Initialize default quotas based on subscription tier"""
        quotas = {
            SubscriptionTier.FREE: {
                "api_calls": 1000,
                "storage_gb": 1,
                "users": 1,
                "campaigns": 5,
                "reports_per_month": 10
            },
            SubscriptionTier.STARTER: {
                "api_calls": 10000,
                "storage_gb": 10,
                "users": 5,
                "campaigns": 50,
                "reports_per_month": 100
            },
            SubscriptionTier.PROFESSIONAL: {
                "api_calls": 100000,
                "storage_gb": 100,
                "users": 25,
                "campaigns": 500,
                "reports_per_month": 1000
            },
            SubscriptionTier.ENTERPRISE: {
                "api_calls": -1,  # Unlimited
                "storage_gb": -1,
                "users": -1,
                "campaigns": -1,
                "reports_per_month": -1
            }
        }
        
        tier_quotas = quotas.get(tier, quotas[SubscriptionTier.FREE])
        
        for quota_type, limit_value in tier_quotas.items():
            await self.postgres.execute(
                """
                INSERT INTO tenant_quotas (tenant_id, quota_type, limit_value, current_usage, reset_period, last_reset_at)
                VALUES ($1, $2, $3, 0, 'monthly', NOW())
                """,
                tenant_id, quota_type, limit_value
            )
    
    async def _update_quotas_for_tier(self, tenant_id: str, tier: SubscriptionTier):
        """Update quotas when subscription tier changes"""
        await self._initialize_default_quotas(tenant_id, tier)
        
        # Reset all quotas
        await self.postgres.execute(
            """
            UPDATE tenant_quotas
            SET current_usage = 0, last_reset_at = NOW(), updated_at = NOW()
            WHERE tenant_id = $1
            """,
            tenant_id
        )

"""
Tenant Configuration Module

Manages tenant-specific configuration and feature flags.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.tenants.tenant_manager import TenantManager, SubscriptionTier


@dataclass
class TenantConfig:
    """Tenant configuration"""
    tenant_id: str
    subscription_tier: SubscriptionTier
    feature_flags: Dict[str, bool]
    limits: Dict[str, int]
    settings: Dict[str, Any]
    
    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to feature"""
        return self.feature_flags.get(feature, False)
    
    def get_limit(self, limit_type: str) -> int:
        """Get limit for resource type"""
        return self.limits.get(limit_type, 0)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get tenant setting"""
        return self.settings.get(key, default)


class TenantConfigManager:
    """Manages tenant configuration"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
    
    async def get_config(self, tenant_id: str) -> TenantConfig:
        """Get tenant configuration"""
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Get feature flags based on tier
        feature_flags = self._get_feature_flags(tenant.subscription_tier)
        
        # Get limits from quotas
        limits = {}
        quota_types = ["api_calls", "storage_gb", "users", "campaigns", "reports_per_month"]
        for quota_type in quota_types:
            quota = await self.tenant_manager.get_tenant_quota(tenant_id, quota_type)
            if quota:
                limits[quota_type] = quota.limit_value
        
        # Get settings
        settings = await self.tenant_manager.get_tenant_settings(tenant_id)
        
        return TenantConfig(
            tenant_id=tenant_id,
            subscription_tier=tenant.subscription_tier,
            feature_flags=feature_flags,
            limits=limits,
            settings=settings
        )
    
    def _get_feature_flags(self, tier: SubscriptionTier) -> Dict[str, bool]:
        """Get feature flags based on subscription tier"""
        base_flags = {
            "api_access": False,
            "advanced_analytics": False,
            "ai_insights": False,
            "white_label": False,
            "custom_integrations": False,
            "priority_support": False,
            "dedicated_infrastructure": False
        }
        
        if tier == SubscriptionTier.FREE:
            return {
                **base_flags,
                "api_access": False,
                "advanced_analytics": False
            }
        elif tier == SubscriptionTier.STARTER:
            return {
                **base_flags,
                "api_access": True,
                "advanced_analytics": True
            }
        elif tier == SubscriptionTier.PROFESSIONAL:
            return {
                **base_flags,
                "api_access": True,
                "advanced_analytics": True,
                "ai_insights": True,
                "custom_integrations": True
            }
        elif tier == SubscriptionTier.ENTERPRISE:
            return {
                **base_flags,
                "api_access": True,
                "advanced_analytics": True,
                "ai_insights": True,
                "white_label": True,
                "custom_integrations": True,
                "priority_support": True,
                "dedicated_infrastructure": True
            }
        
        return base_flags

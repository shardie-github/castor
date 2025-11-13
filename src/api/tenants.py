"""
Tenant Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

from src.tenants import TenantManager, SubscriptionTier, TenantStatus
from src.tenants.tenant_isolation import get_current_tenant
from fastapi import Request

router = APIRouter()


class TenantCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    subscription_tier: str = "free"
    billing_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    subscription_tier: Optional[str] = None
    status: Optional[str] = None
    billing_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    domain: Optional[str]
    subscription_tier: str
    status: str
    billing_email: Optional[str]
    created_at: str
    updated_at: str


# Dependency to get tenant manager
def get_tenant_manager(request: Request) -> TenantManager:
    return request.app.state.tenant_manager


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Create a new tenant"""
    try:
        tier = SubscriptionTier(tenant_data.subscription_tier)
        tenant = await tenant_manager.create_tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            subscription_tier=tier,
            billing_email=tenant_data.billing_email,
            metadata=tenant_data.metadata
        )
        
        return TenantResponse(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            slug=tenant.slug,
            domain=tenant.domain,
            subscription_tier=tenant.subscription_tier.value,
            status=tenant.status.value,
            billing_email=tenant.billing_email,
            created_at=tenant.created_at.isoformat(),
            updated_at=tenant.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Get tenant by ID"""
    tenant = await tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        domain=tenant.domain,
        subscription_tier=tenant.subscription_tier.value,
        status=tenant.status.value,
        billing_email=tenant.billing_email,
        created_at=tenant.created_at.isoformat(),
        updated_at=tenant.updated_at.isoformat()
    )


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    updates: TenantUpdate,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Update tenant"""
    update_dict = updates.dict(exclude_unset=True)
    
    if "subscription_tier" in update_dict:
        update_dict["subscription_tier"] = SubscriptionTier(update_dict["subscription_tier"])
    if "status" in update_dict:
        update_dict["status"] = TenantStatus(update_dict["status"])
    
    tenant = await tenant_manager.update_tenant(tenant_id, update_dict)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        domain=tenant.domain,
        subscription_tier=tenant.subscription_tier.value,
        status=tenant.status.value,
        billing_email=tenant.billing_email,
        created_at=tenant.created_at.isoformat(),
        updated_at=tenant.updated_at.isoformat()
    )


@router.get("/{tenant_id}/quota/{quota_type}")
async def get_quota(
    tenant_id: str,
    quota_type: str,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Get tenant quota"""
    quota = await tenant_manager.get_tenant_quota(tenant_id, quota_type)
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return {
        "tenant_id": quota.tenant_id,
        "quota_type": quota.quota_type,
        "limit_value": quota.limit_value,
        "current_usage": quota.current_usage,
        "reset_period": quota.reset_period,
        "last_reset_at": quota.last_reset_at.isoformat()
    }

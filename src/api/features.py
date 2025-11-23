"""
Feature Flag API Routes

Provides endpoints for managing feature flags.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID

from src.features.flags import FeatureFlagService, get_feature_flag_service

router = APIRouter()


class FeatureFlagCreate(BaseModel):
    flag_name: str
    status: str  # enabled, disabled, gradual_rollout
    tenant_id: Optional[UUID] = None
    rollout_percentage: int = 0
    metadata: Optional[Dict[str, Any]] = None


class FeatureFlagUpdate(BaseModel):
    status: Optional[str] = None
    rollout_percentage: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/flags", response_model=List[Dict[str, Any]])
async def list_feature_flags(
    tenant_id: Optional[UUID] = None,
    feature_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """List all feature flags"""
    if not feature_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feature flag service not available"
        )
    
    flags = await feature_service.list_flags(str(tenant_id) if tenant_id else None)
    return flags


@router.get("/flags/{flag_name}", response_model=Dict[str, Any])
async def get_feature_flag(
    flag_name: str,
    tenant_id: Optional[UUID] = None,
    feature_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Get a specific feature flag"""
    if not feature_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feature flag service not available"
        )
    
    flag = await feature_service.get_flag(flag_name, str(tenant_id) if tenant_id else None)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{flag_name}' not found"
        )
    
    return flag


@router.post("/flags", status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    flag_data: FeatureFlagCreate,
    feature_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Create a new feature flag"""
    if not feature_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feature flag service not available"
        )
    
    await feature_service.set_flag(
        flag_name=flag_data.flag_name,
        status=flag_data.status,
        tenant_id=str(flag_data.tenant_id) if flag_data.tenant_id else None,
        rollout_percentage=flag_data.rollout_percentage,
        metadata=flag_data.metadata
    )
    
    return {"message": f"Feature flag '{flag_data.flag_name}' created"}


@router.put("/flags/{flag_name}")
async def update_feature_flag(
    flag_name: str,
    flag_data: FeatureFlagUpdate,
    tenant_id: Optional[UUID] = None,
    feature_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Update a feature flag"""
    if not feature_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feature flag service not available"
        )
    
    # Get existing flag
    existing = await feature_service.get_flag(flag_name, str(tenant_id) if tenant_id else None)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{flag_name}' not found"
        )
    
    # Update with new values
    await feature_service.set_flag(
        flag_name=flag_name,
        status=flag_data.status or existing['status'],
        tenant_id=str(tenant_id) if tenant_id else existing.get('tenant_id'),
        rollout_percentage=flag_data.rollout_percentage if flag_data.rollout_percentage is not None else existing.get('rollout_percentage', 0),
        metadata=flag_data.metadata or existing.get('metadata')
    )
    
    return {"message": f"Feature flag '{flag_name}' updated"}


@router.get("/flags/{flag_name}/check")
async def check_feature_flag(
    flag_name: str,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    feature_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Check if a feature flag is enabled"""
    if not feature_service:
        # Fall back to environment variable
        import os
        env_key = f"ENABLE_{flag_name.upper().replace('-', '_')}"
        enabled = os.getenv(env_key, "false").lower() == "true"
        return {"enabled": enabled, "source": "environment"}
    
    enabled = await feature_service.is_enabled(
        flag_name,
        str(tenant_id) if tenant_id else None,
        str(user_id) if user_id else None
    )
    
    return {"enabled": enabled, "source": "database"}

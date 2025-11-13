"""
Security API Routes

Provides endpoints for OAuth, MFA, API keys, and security management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List

from src.security.auth import OAuth2Provider, MFAProvider, APIKeyManager
from src.tenants.tenant_isolation import get_current_tenant
from fastapi import Request

router = APIRouter()


class APIKeyCreate(BaseModel):
    name: str
    permissions: Optional[List[str]] = None
    rate_limit_per_hour: int = 1000
    expires_at: Optional[str] = None


class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str  # Only shown once
    key_prefix: str


def get_api_key_manager(request: Request) -> APIKeyManager:
    return request.app.state.api_key_manager


def get_mfa_provider(request: Request) -> MFAProvider:
    return request.app.state.mfa_provider


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request_data: APIKeyCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = None,  # Would come from auth middleware
    api_key_manager: APIKeyManager = Depends(get_api_key_manager)
):
    """Create new API key"""
    # In production, get user_id from authenticated user
    if not user_id:
        user_id = "system"  # Placeholder
    
    result = await api_key_manager.create_api_key(
        tenant_id=tenant_id,
        user_id=user_id,
        name=request_data.name,
        permissions=request_data.permissions,
        rate_limit_per_hour=request_data.rate_limit_per_hour
    )
    
    return APIKeyResponse(**result)


@router.post("/mfa/enable")
async def enable_mfa(
    request: Request,
    user_id: str = None,  # Would come from auth middleware
    mfa_provider: MFAProvider = Depends(get_mfa_provider)
):
    """Enable MFA for user"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    secret = mfa_provider.generate_secret()
    await mfa_provider.enable_mfa(user_id, secret)
    
    # Generate QR code URL (in production, use pyotp)
    return {
        "secret": secret,
        "qr_code_url": f"otpauth://totp/YourApp?secret={secret}&issuer=PodcastAnalytics"
    }


@router.post("/mfa/verify")
async def verify_mfa(
    code: str,
    request: Request,
    user_id: str = None,  # Would come from auth middleware
    mfa_provider: MFAProvider = Depends(get_mfa_provider)
):
    """Verify MFA code"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    is_valid = await mfa_provider.verify_totp(user_id, code)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    return {"status": "verified"}

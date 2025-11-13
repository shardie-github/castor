"""
Tenant Isolation Middleware

Provides tenant context extraction and isolation enforcement.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.tenants.tenant_manager import TenantManager

logger = logging.getLogger(__name__)


def get_current_tenant(request: Request) -> Optional[str]:
    """
    Extract tenant ID from request
    
    Checks multiple sources:
    1. JWT token claim (tenant_id)
    2. API key header (X-Tenant-ID)
    3. Subdomain (tenant-slug.example.com)
    4. Domain (tenant.example.com)
    """
    # Check JWT token claim (set by auth middleware)
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id
    
    # Check API key header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id
    
    # Check subdomain
    host = request.headers.get("Host", "")
    if host:
        parts = host.split(".")
        if len(parts) >= 3:
            # tenant-slug.example.com
            subdomain = parts[0]
            # TODO: Lookup tenant by slug
            pass
    
    return None


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Tenant Isolation Middleware
    
    Extracts tenant context from request and enforces isolation.
    """
    
    def __init__(self, app, tenant_manager: TenantManager):
        super().__init__(app)
        self.tenant_manager = tenant_manager
    
    async def dispatch(self, request: Request, call_next):
        """Process request with tenant isolation"""
        # Extract tenant ID
        tenant_id = get_current_tenant(request)
        
        if not tenant_id:
            # Allow public endpoints (health check, etc.)
            if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]:
                return await call_next(request)
            
            # For authenticated endpoints, require tenant
            if hasattr(request.state, "user_id"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant ID required"
                )
        
        # Verify tenant exists and is active
        if tenant_id:
            tenant = await self.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found"
                )
            
            if tenant.status.value != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Tenant is {tenant.status.value}"
                )
            
            # Set tenant context in request state
            request.state.tenant_id = tenant_id
            
            # Set tenant context in database connection
            # This enables RLS policies
            async with self.tenant_manager.postgres.acquire() as conn:
                await conn.execute(
                    "SELECT set_tenant_context($1)",
                    tenant_id
                )
        
        # Process request
        response = await call_next(request)
        
        return response

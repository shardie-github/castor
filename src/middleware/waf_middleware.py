"""
WAF Middleware for FastAPI

Integrates WAF into FastAPI request pipeline.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from src.security.waf import get_waf

logger = logging.getLogger(__name__)


class WAFMiddleware(BaseHTTPMiddleware):
    """WAF middleware for FastAPI"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request through WAF"""
        waf = get_waf()
        
        if not waf:
            # WAF not initialized, allow request
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Get request body (if available)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8", errors="ignore")
                # Re-create request body for downstream
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception:
                pass
        
        # Check request against WAF
        allowed, rule_name, reason = waf.check_request(
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            body=body,
            client_ip=client_ip,
        )
        
        if not allowed:
            logger.warning(
                f"WAF blocked request: {rule_name}",
                extra={
                    "rule": rule_name,
                    "reason": reason,
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": client_ip,
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Request blocked: {reason or 'Security policy violation'}",
            )
        
        # Process request
        response = await call_next(request)
        return response

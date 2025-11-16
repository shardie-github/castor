"""
CSRF Protection Middleware

Provides CSRF token generation and validation.
"""

import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF protection middleware"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_token(self, token: str, session_token: Optional[str] = None) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
        
        # In production, compare with session token
        # For now, basic validation
        return len(token) >= 32
    
    async def __call__(self, request: Request, call_next):
        """CSRF middleware"""
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Skip CSRF for API endpoints (use API keys instead)
        if request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Get CSRF token from header
        csrf_token = request.headers.get("X-CSRF-Token")
        
        # Get session token from cookies
        session_token = request.cookies.get("csrf_token")
        
        # Validate token
        if not self.validate_token(csrf_token, session_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token validation failed"}
            )
        
        return await call_next(request)


def create_csrf_protection(secret_key: str) -> CSRFProtection:
    """Create CSRF protection instance"""
    return CSRFProtection(secret_key)

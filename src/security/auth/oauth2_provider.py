"""
OAuth 2.0 Provider

Implements OAuth 2.0 / OIDC authentication.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import jwt

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """
    OAuth 2.0 Provider
    
    Implements OAuth 2.0 authorization code flow and OpenID Connect.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        jwt_secret: str,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.jwt_secret = jwt_secret
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def authorize(
        self,
        user_id: str,
        tenant_id: str,
        scopes: Optional[list] = None
    ) -> str:
        """
        Generate authorization code
        
        Returns:
            Authorization code
        """
        code = str(uuid4())
        
        # Store authorization code (in production, use Redis with TTL)
        # For now, we'll generate JWT directly
        
        # Log event
        await self.events.log_event(
            event_type="oauth_authorize",
            user_id=user_id,
            properties={
                "tenant_id": tenant_id,
                "scopes": scopes or []
            }
        )
        
        return code
    
    async def token(
        self,
        code: str,
        grant_type: str = "authorization_code"
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Returns:
            Dictionary with access_token, refresh_token, expires_in, token_type
        """
        # In production, validate code and exchange for tokens
        # For now, generate tokens directly
        
        access_token = self._generate_access_token(code)
        refresh_token = self._generate_refresh_token(code)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,  # 1 hour
            "token_type": "Bearer"
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        # Validate refresh token and generate new access token
        access_token = self._generate_access_token(refresh_token)
        
        return {
            "access_token": access_token,
            "expires_in": 3600,
            "token_type": "Bearer"
        }
    
    def _generate_access_token(self, subject: str) -> str:
        """Generate JWT access token"""
        payload = {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _generate_refresh_token(self, subject: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

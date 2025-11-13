"""
User Management Module

Handles user authentication, authorization, and management including:
- User CRUD operations
- Authentication (OAuth, JWT)
- Role-based access control (RBAC)
- Subscription/billing integration
"""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import jwt

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection, RedisConnection

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class User:
    """User data structure"""
    user_id: str
    email: str
    password_hash: str
    name: str
    role: UserRole
    subscription_tier: SubscriptionTier
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    is_active: bool = True
    persona_segment: Optional[str] = None  # solo_podcaster, producer, agency, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UserManager:
    """
    User Manager
    
    Manages users, authentication, and authorization.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        jwt_secret: str = "change-me-in-production",
        postgres_conn: Optional[PostgresConnection] = None,
        redis_conn: Optional[RedisConnection] = None
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.jwt_secret = jwt_secret
        self.postgres = postgres_conn
        self.redis = redis_conn
        # Fallback to in-memory storage if no database connection
        self._use_db = postgres_conn is not None
        self._use_redis = redis_conn is not None
        if not self._use_db:
            self._users: Dict[str, User] = {}
        if not self._use_redis:
            self._sessions: Dict[str, Session] = {}
        
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        return self._hash_password(password) == password_hash
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        persona_segment: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> User:
        """Create a new user"""
        # Check if user exists
        existing = await self.get_user_by_email(email)
        if existing:
            raise ValueError("User with this email already exists")
        
        user_id = str(uuid4())
        password_hash = self._hash_password(password)
        
        user = User(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            name=name,
            role=UserRole.USER,
            subscription_tier=subscription_tier,
            persona_segment=persona_segment
        )
        
        self._users[user_id] = user
        
        # Record telemetry
        self.metrics.increment_counter(
            "user_created",
            tags={"subscription_tier": subscription_tier.value, "persona": persona_segment or "unknown"}
        )
        
        # Log event
        await self.events.log_event(
            event_type="user_created",
            user_id=user_id,
            properties={
                "email": email,
                "subscription_tier": subscription_tier.value,
                "persona_segment": persona_segment
            }
        )
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Session]:
        """Authenticate user and create session"""
        user = await self.get_user_by_email(email)
        if not user:
            self.metrics.increment_counter("auth_failed", tags={"reason": "user_not_found"})
            return None
        
        if not self._verify_password(password, user.password_hash):
            self.metrics.increment_counter("auth_failed", tags={"reason": "invalid_password"})
            return None
        
        if not user.is_active:
            self.metrics.increment_counter("auth_failed", tags={"reason": "user_inactive"})
            return None
        
        # Create session
        session_id = str(uuid4())
        token = self._generate_jwt_token(user.user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            token=token,
            expires_at=expires_at
        )
        
        self._sessions[session_id] = session
        
        # Update user last login
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        
        # Record telemetry
        self.metrics.increment_counter("user_login", tags={"user_id": user.user_id})
        
        # Log event
        await self.events.log_event(
            event_type="user_login",
            user_id=user.user_id,
            properties={"session_id": session_id}
        )
        
        return session
    
    def _generate_jwt_token(self, user_id: str) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[User]:
        """Update user"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        if "name" in updates:
            user.name = updates["name"]
        if "subscription_tier" in updates:
            user.subscription_tier = SubscriptionTier(updates["subscription_tier"])
        if "persona_segment" in updates:
            user.persona_segment = updates["persona_segment"]
        if "is_active" in updates:
            user.is_active = updates["is_active"]
        
        user.updated_at = datetime.now(timezone.utc)
        
        # Log event
        await self.events.log_event(
            event_type="user_updated",
            user_id=user_id,
            properties={"updated_fields": list(updates.keys())}
        )
        
        return user
    
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has permission for resource/action"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            return True
        
        # Role-based permissions
        permissions = {
            UserRole.USER: ["read", "write", "delete"],
            UserRole.VIEWER: ["read"]
        }
        
        user_permissions = permissions.get(user.role, [])
        return action in user_permissions
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return session
        return None
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

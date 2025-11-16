"""
Authentication API Routes

Provides endpoints for user registration, login, email verification, password reset, and session management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from passlib.context import CryptContext

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.config import config

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    accept_terms: bool = False
    accept_privacy: bool = False
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('accept_terms', 'accept_privacy')
    def validate_acceptance(cls, v):
        if not v:
            raise ValueError('Must accept terms and privacy policy')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class EmailVerification(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# Helper Functions
def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user from database
    postgres_conn: PostgresConnection = request.app.state.postgres_conn
    user = await postgres_conn.fetchrow(
        "SELECT user_id, email, name, role, subscription_tier, is_active FROM users WHERE user_id = $1",
        user_id
    )
    
    if not user or not user.get('is_active'):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return dict(user)


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


# API Endpoints
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await postgres_conn.fetchrow(
        "SELECT user_id FROM users WHERE email = $1",
        user_data.email
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)
    verification_token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
    
    # Create user
    user_id = await postgres_conn.fetchval(
        """
        INSERT INTO users (email, password_hash, name, role, subscription_tier, email_verified, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING user_id
        """,
        user_data.email,
        hashed_password,
        user_data.name,
        'user',
        'free',
        False,
        {
            'accept_terms': user_data.accept_terms,
            'accept_privacy': user_data.accept_privacy,
            'verification_token': verification_token_hash
        }
    )
    
    # Store verification token
    await postgres_conn.execute(
        """
        INSERT INTO email_verification_tokens (user_id, token_hash, expires_at)
        VALUES ($1, $2, $3)
        """,
        user_id,
        verification_token_hash,
        datetime.utcnow() + timedelta(days=7)
    )
    
    # Log event
    await event_logger.log_event(
        event_type='user.registered',
        user_id=str(user_id),
        properties={'email': user_data.email}
    )
    
    # Record metrics
    metrics.increment_counter('user_registrations_total')
    
    # TODO: Send verification email
    
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": str(user_id),
        "verification_token": verification_token  # Remove in production, use email
    }


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Login user"""
    # Get user
    user = await postgres_conn.fetchrow(
        "SELECT user_id, email, password_hash, name, role, subscription_tier, is_active, email_verified FROM users WHERE email = $1",
        credentials.email
    )
    
    if not user or not verify_password(credentials.password, user['password_hash']):
        metrics.increment_counter('login_failures_total')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user['user_id']), "email": user['email']},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user['user_id']), "email": user['email']}
    )
    
    # Store refresh token
    await postgres_conn.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET token_hash = $2, expires_at = $3
        """,
        user['user_id'],
        hashlib.sha256(refresh_token.encode()).hexdigest(),
        datetime.utcnow() + timedelta(days=30)
    )
    
    # Update last login
    await postgres_conn.execute(
        "UPDATE users SET last_login = $1 WHERE user_id = $2",
        datetime.utcnow(),
        user['user_id']
    )
    
    # Log event
    await event_logger.log_event(
        event_type='user.logged_in',
        user_id=str(user['user_id']),
        properties={'email': user['email']}
    )
    
    # Record metrics
    metrics.increment_counter('login_successes_total')
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
        user={
            "user_id": str(user['user_id']),
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "subscription_tier": user['subscription_tier'],
            "email_verified": user['email_verified']
        }
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Logout user"""
    # Invalidate refresh token
    await postgres_conn.execute(
        "DELETE FROM refresh_tokens WHERE user_id = $1",
        current_user['user_id']
    )
    
    return {"message": "Logged out successfully"}


@router.post("/verify-email")
async def verify_email(
    verification: EmailVerification,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Verify user email"""
    token_hash = hashlib.sha256(verification.token.encode()).hexdigest()
    
    # Find verification token
    verification_record = await postgres_conn.fetchrow(
        """
        SELECT evt.user_id, evt.expires_at
        FROM email_verification_tokens evt
        WHERE evt.token_hash = $1 AND evt.expires_at > NOW()
        """,
        token_hash
    )
    
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user
    await postgres_conn.execute(
        "UPDATE users SET email_verified = TRUE WHERE user_id = $1",
        verification_record['user_id']
    )
    
    # Delete verification token
    await postgres_conn.execute(
        "DELETE FROM email_verification_tokens WHERE token_hash = $1",
        token_hash
    )
    
    # Log event
    await event_logger.log_event(
        event_type='user.email_verified',
        user_id=str(verification_record['user_id']),
        properties={}
    )
    
    metrics.increment_counter('email_verifications_total')
    
    return {"message": "Email verified successfully"}


@router.post("/reset-password-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector)
):
    """Request password reset"""
    # Get user
    user = await postgres_conn.fetchrow(
        "SELECT user_id FROM users WHERE email = $1",
        reset_request.email
    )
    
    # Always return success (security best practice)
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    
    # Store reset token
    await postgres_conn.execute(
        """
        INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET token_hash = $2, expires_at = $3
        """,
        user['user_id'],
        reset_token_hash,
        datetime.utcnow() + timedelta(hours=1)
    )
    
    # TODO: Send password reset email
    
    metrics.increment_counter('password_reset_requests_total')
    
    return {
        "message": "If the email exists, a password reset link has been sent",
        "reset_token": reset_token  # Remove in production, use email
    }


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Reset password using token"""
    token_hash = hashlib.sha256(reset_data.token.encode()).hexdigest()
    
    # Find reset token
    reset_record = await postgres_conn.fetchrow(
        """
        SELECT prt.user_id, prt.expires_at
        FROM password_reset_tokens prt
        WHERE prt.token_hash = $1 AND prt.expires_at > NOW()
        """,
        token_hash
    )
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    hashed_password = hash_password(reset_data.new_password)
    await postgres_conn.execute(
        "UPDATE users SET password_hash = $1 WHERE user_id = $2",
        hashed_password,
        reset_record['user_id']
    )
    
    # Delete reset token
    await postgres_conn.execute(
        "DELETE FROM password_reset_tokens WHERE token_hash = $1",
        token_hash
    )
    
    # Invalidate all refresh tokens
    await postgres_conn.execute(
        "DELETE FROM refresh_tokens WHERE user_id = $1",
        reset_record['user_id']
    )
    
    # Log event
    await event_logger.log_event(
        event_type='user.password_reset',
        user_id=str(reset_record['user_id']),
        properties={}
    )
    
    metrics.increment_counter('password_resets_total')
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Change password for authenticated user"""
    # Get current password hash
    user = await postgres_conn.fetchrow(
        "SELECT password_hash FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    # Verify current password
    if not verify_password(password_data.current_password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    hashed_password = hash_password(password_data.new_password)
    await postgres_conn.execute(
        "UPDATE users SET password_hash = $1 WHERE user_id = $2",
        hashed_password,
        current_user['user_id']
    )
    
    # Log event
    await event_logger.log_event(
        event_type='user.password_changed',
        user_id=str(current_user['user_id']),
        properties={}
    )
    
    return {"message": "Password changed successfully"}


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    request: Request,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Refresh access token"""
    # Verify refresh token
    payload = verify_token(refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    
    # Verify refresh token exists in database
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    stored_token = await postgres_conn.fetchrow(
        """
        SELECT rt.user_id, rt.expires_at
        FROM refresh_tokens rt
        WHERE rt.user_id = $1 AND rt.token_hash = $2 AND rt.expires_at > NOW()
        """,
        user_id,
        token_hash
    )
    
    if not stored_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": user_id, "email": payload.get("email")},
        expires_delta=timedelta(minutes=30)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

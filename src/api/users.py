"""
Users API Routes

Provides endpoints for user profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()


# Pydantic Models
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    persona_segment: Optional[str] = None
    metadata: Optional[dict] = None


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    subscription_tier: str
    persona_segment: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    is_active: bool


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


# API Endpoints
@router.get("/users/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get current user's profile"""
    query = """
        SELECT user_id, email, name, role, subscription_tier, persona_segment,
               created_at, updated_at, last_login, is_active
        FROM users
        WHERE user_id = $1
    """
    
    result = await postgres_conn.fetchrow(query, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse(**dict(result))


@router.put("/users/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update current user's profile"""
    # Build update query dynamically
    updates = []
    values = []
    param_num = 1
    
    if profile_data.name is not None:
        updates.append(f"name = ${param_num}")
        values.append(profile_data.name)
        param_num += 1
    
    if profile_data.email is not None:
        # Check if email is already taken
        existing = await postgres_conn.fetchrow(
            "SELECT user_id FROM users WHERE email = $1 AND user_id != $2",
            profile_data.email,
            current_user['user_id']
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        updates.append(f"email = ${param_num}")
        values.append(profile_data.email)
        param_num += 1
    
    if profile_data.persona_segment is not None:
        updates.append(f"persona_segment = ${param_num}")
        values.append(profile_data.persona_segment)
        param_num += 1
    
    if profile_data.metadata is not None:
        # Merge with existing metadata
        current_user_data = await postgres_conn.fetchrow(
            "SELECT metadata FROM users WHERE user_id = $1",
            current_user['user_id']
        )
        current_metadata = current_user_data['metadata'] or {}
        merged_metadata = {**current_metadata, **profile_data.metadata}
        
        updates.append(f"metadata = ${param_num}")
        values.append(merged_metadata)
        param_num += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updates.append(f"updated_at = ${param_num}")
    values.append(datetime.utcnow())
    param_num += 1
    
    values.append(current_user['user_id'])
    
    query = f"""
        UPDATE users
        SET {', '.join(updates)}
        WHERE user_id = ${param_num}
        RETURNING user_id, email, name, role, subscription_tier, persona_segment,
                  created_at, updated_at, last_login, is_active
    """
    
    result = await postgres_conn.fetchrow(query, *values)
    
    await event_logger.log_event(
        event_type='user.profile.updated',
        user_id=str(current_user['user_id']),
        properties={'updated_fields': list(profile_data.dict(exclude_unset=True).keys())}
    )
    
    return UserProfileResponse(**dict(result))


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete current user's account"""
    # Soft delete by setting is_active to False
    query = """
        UPDATE users
        SET is_active = FALSE, updated_at = NOW()
        WHERE user_id = $1
        RETURNING user_id
    """
    
    result = await postgres_conn.fetchrow(query, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await event_logger.log_event(
        event_type='user.deleted',
        user_id=str(current_user['user_id']),
        properties={}
    )
    
    return None

"""
Sponsors API Routes

Provides endpoints for sponsor CRUD operations and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()


# Pydantic Models
class SponsorCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class SponsorUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class SponsorResponse(BaseModel):
    sponsor_id: str
    user_id: str
    name: str
    company: Optional[str]
    email: Optional[str]
    contact_name: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    logo_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


# API Endpoints
@router.post("/sponsors", response_model=SponsorResponse, status_code=status.HTTP_201_CREATED)
async def create_sponsor(
    sponsor_data: SponsorCreate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Create a new sponsor"""
    query = """
        INSERT INTO sponsors (
            user_id, name, company, email, contact_name, phone,
            website, logo_url, notes, metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING sponsor_id, user_id, name, company, email, contact_name,
                  phone, website, logo_url, notes, created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(
        query,
        current_user['user_id'],
        sponsor_data.name,
        sponsor_data.company,
        sponsor_data.email,
        sponsor_data.contact_name,
        sponsor_data.phone,
        sponsor_data.website,
        sponsor_data.logo_url,
        sponsor_data.notes,
        sponsor_data.metadata or {}
    )
    
    await event_logger.log_event(
        event_type='sponsor.created',
        user_id=str(current_user['user_id']),
        properties={'sponsor_id': str(result['sponsor_id'])}
    )
    
    return SponsorResponse(**dict(result))


@router.get("/sponsors", response_model=List[SponsorResponse])
async def list_sponsors(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    skip: int = 0,
    limit: int = 100
):
    """List all sponsors for the current user (cached for 5 minutes)"""
    from src.cache.cache_manager import CacheManager
    
    # Get cache manager from app state
    cache_manager = getattr(request.app.state, 'cache_manager', None) if request else None
    
    # Generate cache key
    cache_key = f"sponsors:user:{current_user['user_id']}:skip:{skip}:limit:{limit}"
    
    # Try cache first
    if cache_manager:
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
    
    # Cache miss - query database
    query = """
        SELECT sponsor_id, user_id, name, company, email, contact_name,
               phone, website, logo_url, notes, created_at, updated_at
        FROM sponsors
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    
    results = await postgres_conn.fetch(query, current_user['user_id'], limit, skip, use_read_replica=True)
    sponsors = [SponsorResponse(**dict(row)) for row in results]
    
    # Cache result
    if cache_manager:
        await cache_manager.set(cache_key, sponsors, ttl_seconds=300)  # 5 minutes
    
    return sponsors


@router.get("/sponsors/{sponsor_id}", response_model=SponsorResponse)
async def get_sponsor(
    sponsor_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get a specific sponsor"""
    query = """
        SELECT sponsor_id, user_id, name, company, email, contact_name,
               phone, website, logo_url, notes, created_at, updated_at
        FROM sponsors
        WHERE sponsor_id = $1 AND user_id = $2
    """
    
    result = await postgres_conn.fetchrow(query, sponsor_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )
    
    return SponsorResponse(**dict(result))


@router.put("/sponsors/{sponsor_id}", response_model=SponsorResponse)
async def update_sponsor(
    sponsor_id: str,
    sponsor_data: SponsorUpdate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update a sponsor"""
    # Build update query dynamically
    updates = []
    values = []
    param_num = 1
    
    if sponsor_data.name is not None:
        updates.append(f"name = ${param_num}")
        values.append(sponsor_data.name)
        param_num += 1
    
    if sponsor_data.company is not None:
        updates.append(f"company = ${param_num}")
        values.append(sponsor_data.company)
        param_num += 1
    
    if sponsor_data.email is not None:
        updates.append(f"email = ${param_num}")
        values.append(sponsor_data.email)
        param_num += 1
    
    if sponsor_data.contact_name is not None:
        updates.append(f"contact_name = ${param_num}")
        values.append(sponsor_data.contact_name)
        param_num += 1
    
    if sponsor_data.phone is not None:
        updates.append(f"phone = ${param_num}")
        values.append(sponsor_data.phone)
        param_num += 1
    
    if sponsor_data.website is not None:
        updates.append(f"website = ${param_num}")
        values.append(sponsor_data.website)
        param_num += 1
    
    if sponsor_data.logo_url is not None:
        updates.append(f"logo_url = ${param_num}")
        values.append(sponsor_data.logo_url)
        param_num += 1
    
    if sponsor_data.notes is not None:
        updates.append(f"notes = ${param_num}")
        values.append(sponsor_data.notes)
        param_num += 1
    
    if sponsor_data.metadata is not None:
        updates.append(f"metadata = ${param_num}")
        values.append(sponsor_data.metadata)
        param_num += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updates.append(f"updated_at = ${param_num}")
    values.append(datetime.utcnow())
    param_num += 1
    
    values.extend([sponsor_id, current_user['user_id']])
    
    query = f"""
        UPDATE sponsors
        SET {', '.join(updates)}
        WHERE sponsor_id = ${param_num} AND user_id = ${param_num + 1}
        RETURNING sponsor_id, user_id, name, company, email, contact_name,
                  phone, website, logo_url, notes, created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(query, *values)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )
    
    await event_logger.log_event(
        event_type='sponsor.updated',
        user_id=str(current_user['user_id']),
        properties={'sponsor_id': sponsor_id}
    )
    
    return SponsorResponse(**dict(result))


@router.delete("/sponsors/{sponsor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sponsor(
    sponsor_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete a sponsor"""
    query = "DELETE FROM sponsors WHERE sponsor_id = $1 AND user_id = $2 RETURNING sponsor_id"
    result = await postgres_conn.fetchrow(query, sponsor_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )
    
    await event_logger.log_event(
        event_type='sponsor.deleted',
        user_id=str(current_user['user_id']),
        properties={'sponsor_id': sponsor_id}
    )
    
    return None

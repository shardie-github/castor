"""
Podcasts API Routes

Provides endpoints for podcast CRUD operations and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()


# Pydantic Models
class PodcastCreate(BaseModel):
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    feed_url: str
    website_url: Optional[str] = None
    language: str = "en"
    category: Optional[str] = None
    explicit: bool = False
    platform_configs: Optional[dict] = None


class PodcastUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    feed_url: Optional[str] = None
    website_url: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    explicit: Optional[bool] = None
    platform_configs: Optional[dict] = None
    ingestion_status: Optional[str] = None


class PodcastResponse(BaseModel):
    podcast_id: str
    user_id: str
    title: str
    description: Optional[str]
    author: Optional[str]
    image_url: Optional[str]
    feed_url: str
    website_url: Optional[str]
    language: str
    category: Optional[str]
    explicit: bool
    ingestion_status: str
    last_ingested_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


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
@router.post("/podcasts", response_model=PodcastResponse, status_code=status.HTTP_201_CREATED)
async def create_podcast(
    podcast_data: PodcastCreate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Create a new podcast"""
    query = """
        INSERT INTO podcasts (
            user_id, title, description, author, image_url, feed_url,
            website_url, language, category, explicit, platform_configs
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING podcast_id, user_id, title, description, author, image_url,
                  feed_url, website_url, language, category, explicit,
                  ingestion_status, last_ingested_at, created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(
        query,
        current_user['user_id'],
        podcast_data.title,
        podcast_data.description,
        podcast_data.author,
        podcast_data.image_url,
        podcast_data.feed_url,
        podcast_data.website_url,
        podcast_data.language,
        podcast_data.category,
        podcast_data.explicit,
        podcast_data.platform_configs or {}
    )
    
    await event_logger.log_event(
        event_type='podcast.created',
        user_id=str(current_user['user_id']),
        properties={'podcast_id': str(result['podcast_id'])}
    )
    
    return PodcastResponse(**dict(result))


@router.get("/podcasts", response_model=List[PodcastResponse])
async def list_podcasts(
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    skip: int = 0,
    limit: int = 100
):
    """List all podcasts for the current user"""
    query = """
        SELECT podcast_id, user_id, title, description, author, image_url,
               feed_url, website_url, language, category, explicit,
               ingestion_status, last_ingested_at, created_at, updated_at
        FROM podcasts
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    
    results = await postgres_conn.fetch(query, current_user['user_id'], limit, skip)
    return [PodcastResponse(**dict(row)) for row in results]


@router.get("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get a specific podcast"""
    query = """
        SELECT podcast_id, user_id, title, description, author, image_url,
               feed_url, website_url, language, category, explicit,
               ingestion_status, last_ingested_at, created_at, updated_at
        FROM podcasts
        WHERE podcast_id = $1 AND user_id = $2
    """
    
    result = await postgres_conn.fetchrow(query, podcast_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    return PodcastResponse(**dict(result))


@router.put("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def update_podcast(
    podcast_id: str,
    podcast_data: PodcastUpdate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update a podcast"""
    # Build update query dynamically
    updates = []
    values = []
    param_num = 1
    
    if podcast_data.title is not None:
        updates.append(f"title = ${param_num}")
        values.append(podcast_data.title)
        param_num += 1
    
    if podcast_data.description is not None:
        updates.append(f"description = ${param_num}")
        values.append(podcast_data.description)
        param_num += 1
    
    if podcast_data.author is not None:
        updates.append(f"author = ${param_num}")
        values.append(podcast_data.author)
        param_num += 1
    
    if podcast_data.image_url is not None:
        updates.append(f"image_url = ${param_num}")
        values.append(podcast_data.image_url)
        param_num += 1
    
    if podcast_data.feed_url is not None:
        updates.append(f"feed_url = ${param_num}")
        values.append(podcast_data.feed_url)
        param_num += 1
    
    if podcast_data.website_url is not None:
        updates.append(f"website_url = ${param_num}")
        values.append(podcast_data.website_url)
        param_num += 1
    
    if podcast_data.language is not None:
        updates.append(f"language = ${param_num}")
        values.append(podcast_data.language)
        param_num += 1
    
    if podcast_data.category is not None:
        updates.append(f"category = ${param_num}")
        values.append(podcast_data.category)
        param_num += 1
    
    if podcast_data.explicit is not None:
        updates.append(f"explicit = ${param_num}")
        values.append(podcast_data.explicit)
        param_num += 1
    
    if podcast_data.platform_configs is not None:
        updates.append(f"platform_configs = ${param_num}")
        values.append(podcast_data.platform_configs)
        param_num += 1
    
    if podcast_data.ingestion_status is not None:
        updates.append(f"ingestion_status = ${param_num}")
        values.append(podcast_data.ingestion_status)
        param_num += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updates.append(f"updated_at = ${param_num}")
    values.append(datetime.utcnow())
    param_num += 1
    
    values.extend([podcast_id, current_user['user_id']])
    
    query = f"""
        UPDATE podcasts
        SET {', '.join(updates)}
        WHERE podcast_id = ${param_num} AND user_id = ${param_num + 1}
        RETURNING podcast_id, user_id, title, description, author, image_url,
                  feed_url, website_url, language, category, explicit,
                  ingestion_status, last_ingested_at, created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(query, *values)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    await event_logger.log_event(
        event_type='podcast.updated',
        user_id=str(current_user['user_id']),
        properties={'podcast_id': podcast_id}
    )
    
    return PodcastResponse(**dict(result))


@router.delete("/podcasts/{podcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_podcast(
    podcast_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete a podcast"""
    query = "DELETE FROM podcasts WHERE podcast_id = $1 AND user_id = $2 RETURNING podcast_id"
    result = await postgres_conn.fetchrow(query, podcast_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    await event_logger.log_event(
        event_type='podcast.deleted',
        user_id=str(current_user['user_id']),
        properties={'podcast_id': podcast_id}
    )
    
    return None

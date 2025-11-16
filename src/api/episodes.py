"""
Episodes API Routes

Provides endpoints for episode CRUD operations and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()


# Pydantic Models
class EpisodeCreate(BaseModel):
    podcast_id: str
    guid: str
    title: str
    description: Optional[str] = None
    audio_url: str
    duration_seconds: Optional[int] = None
    publish_date: datetime
    link: Optional[str] = None
    author: Optional[str] = None
    categories: Optional[List[str]] = None
    explicit: bool = False
    transcript_url: Optional[str] = None
    ad_slots: Optional[List[dict]] = None


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    publish_date: Optional[datetime] = None
    link: Optional[str] = None
    author: Optional[str] = None
    categories: Optional[List[str]] = None
    explicit: Optional[bool] = None
    transcript_url: Optional[str] = None
    transcript_status: Optional[str] = None
    ad_slots: Optional[List[dict]] = None


class EpisodeResponse(BaseModel):
    episode_id: str
    podcast_id: str
    guid: str
    title: str
    description: Optional[str]
    audio_url: str
    duration_seconds: Optional[int]
    publish_date: datetime
    link: Optional[str]
    author: Optional[str]
    categories: Optional[List[str]]
    explicit: bool
    transcript_url: Optional[str]
    transcript_status: str
    ad_slots: Optional[List[dict]]
    created_at: datetime
    updated_at: datetime


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


# API Endpoints
@router.post("/episodes", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    episode_data: EpisodeCreate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Create a new episode"""
    # Verify podcast belongs to user
    podcast = await postgres_conn.fetchrow(
        "SELECT podcast_id FROM podcasts WHERE podcast_id = $1 AND user_id = $2",
        episode_data.podcast_id,
        current_user['user_id']
    )
    
    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    query = """
        INSERT INTO episodes (
            podcast_id, guid, title, description, audio_url, duration_seconds,
            publish_date, link, author, categories, explicit,
            transcript_url, ad_slots
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING episode_id, podcast_id, guid, title, description, audio_url,
                  duration_seconds, publish_date, link, author, categories,
                  explicit, transcript_url, transcript_status, ad_slots,
                  created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(
        query,
        episode_data.podcast_id,
        episode_data.guid,
        episode_data.title,
        episode_data.description,
        episode_data.audio_url,
        episode_data.duration_seconds,
        episode_data.publish_date,
        episode_data.link,
        episode_data.author,
        episode_data.categories or [],
        episode_data.explicit,
        episode_data.transcript_url,
        episode_data.ad_slots or []
    )
    
    await event_logger.log_event(
        event_type='episode.created',
        user_id=str(current_user['user_id']),
        properties={
            'episode_id': str(result['episode_id']),
            'podcast_id': episode_data.podcast_id
        }
    )
    
    return EpisodeResponse(**dict(result))


@router.get("/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    podcast_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    skip: int = 0,
    limit: int = 100
):
    """List episodes, optionally filtered by podcast"""
    if podcast_id:
        # Verify podcast belongs to user
        podcast = await postgres_conn.fetchrow(
            "SELECT podcast_id FROM podcasts WHERE podcast_id = $1 AND user_id = $2",
            podcast_id,
            current_user['user_id']
        )
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        query = """
            SELECT e.episode_id, e.podcast_id, e.guid, e.title, e.description,
                   e.audio_url, e.duration_seconds, e.publish_date, e.link,
                   e.author, e.categories, e.explicit, e.transcript_url,
                   e.transcript_status, e.ad_slots, e.created_at, e.updated_at
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.podcast_id
            WHERE e.podcast_id = $1 AND p.user_id = $2
            ORDER BY e.publish_date DESC
            LIMIT $3 OFFSET $4
        """
        results = await postgres_conn.fetch(query, podcast_id, current_user['user_id'], limit, skip)
    else:
        query = """
            SELECT e.episode_id, e.podcast_id, e.guid, e.title, e.description,
                   e.audio_url, e.duration_seconds, e.publish_date, e.link,
                   e.author, e.categories, e.explicit, e.transcript_url,
                   e.transcript_status, e.ad_slots, e.created_at, e.updated_at
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.podcast_id
            WHERE p.user_id = $1
            ORDER BY e.publish_date DESC
            LIMIT $2 OFFSET $3
        """
        results = await postgres_conn.fetch(query, current_user['user_id'], limit, skip)
    
    return [EpisodeResponse(**dict(row)) for row in results]


@router.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get a specific episode"""
    query = """
        SELECT e.episode_id, e.podcast_id, e.guid, e.title, e.description,
               e.audio_url, e.duration_seconds, e.publish_date, e.link,
               e.author, e.categories, e.explicit, e.transcript_url,
               e.transcript_status, e.ad_slots, e.created_at, e.updated_at
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.podcast_id
        WHERE e.episode_id = $1 AND p.user_id = $2
    """
    
    result = await postgres_conn.fetchrow(query, episode_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    return EpisodeResponse(**dict(result))


@router.put("/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: str,
    episode_data: EpisodeUpdate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update an episode"""
    # Build update query dynamically
    updates = []
    values = []
    param_num = 1
    
    if episode_data.title is not None:
        updates.append(f"title = ${param_num}")
        values.append(episode_data.title)
        param_num += 1
    
    if episode_data.description is not None:
        updates.append(f"description = ${param_num}")
        values.append(episode_data.description)
        param_num += 1
    
    if episode_data.audio_url is not None:
        updates.append(f"audio_url = ${param_num}")
        values.append(episode_data.audio_url)
        param_num += 1
    
    if episode_data.duration_seconds is not None:
        updates.append(f"duration_seconds = ${param_num}")
        values.append(episode_data.duration_seconds)
        param_num += 1
    
    if episode_data.publish_date is not None:
        updates.append(f"publish_date = ${param_num}")
        values.append(episode_data.publish_date)
        param_num += 1
    
    if episode_data.link is not None:
        updates.append(f"link = ${param_num}")
        values.append(episode_data.link)
        param_num += 1
    
    if episode_data.author is not None:
        updates.append(f"author = ${param_num}")
        values.append(episode_data.author)
        param_num += 1
    
    if episode_data.categories is not None:
        updates.append(f"categories = ${param_num}")
        values.append(episode_data.categories)
        param_num += 1
    
    if episode_data.explicit is not None:
        updates.append(f"explicit = ${param_num}")
        values.append(episode_data.explicit)
        param_num += 1
    
    if episode_data.transcript_url is not None:
        updates.append(f"transcript_url = ${param_num}")
        values.append(episode_data.transcript_url)
        param_num += 1
    
    if episode_data.transcript_status is not None:
        updates.append(f"transcript_status = ${param_num}")
        values.append(episode_data.transcript_status)
        param_num += 1
    
    if episode_data.ad_slots is not None:
        updates.append(f"ad_slots = ${param_num}")
        values.append(episode_data.ad_slots)
        param_num += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updates.append(f"updated_at = ${param_num}")
    values.append(datetime.utcnow())
    param_num += 1
    
    values.extend([episode_id, current_user['user_id']])
    
    query = f"""
        UPDATE episodes
        SET {', '.join(updates)}
        WHERE episode_id = ${param_num}
        AND podcast_id IN (
            SELECT podcast_id FROM podcasts WHERE user_id = ${param_num + 1}
        )
        RETURNING episode_id, podcast_id, guid, title, description, audio_url,
                  duration_seconds, publish_date, link, author, categories,
                  explicit, transcript_url, transcript_status, ad_slots,
                  created_at, updated_at
    """
    
    result = await postgres_conn.fetchrow(query, *values)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    await event_logger.log_event(
        event_type='episode.updated',
        user_id=str(current_user['user_id']),
        properties={'episode_id': episode_id}
    )
    
    return EpisodeResponse(**dict(result))


@router.delete("/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete an episode"""
    query = """
        DELETE FROM episodes
        WHERE episode_id = $1
        AND podcast_id IN (
            SELECT podcast_id FROM podcasts WHERE user_id = $2
        )
        RETURNING episode_id
    """
    result = await postgres_conn.fetchrow(query, episode_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    await event_logger.log_event(
        event_type='episode.deleted',
        user_id=str(current_user['user_id']),
        properties={'episode_id': episode_id}
    )
    
    return None

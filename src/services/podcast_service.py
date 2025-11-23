"""
Podcast Service

Business logic for podcast management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.utils.error_responses import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class PodcastService:
    """Service for podcast business logic"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def create_podcast(
        self,
        tenant_id: str,
        user_id: str,
        podcast_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new podcast"""
        # Validate RSS feed URL if provided
        rss_url = podcast_data.get('rss_feed_url')
        if rss_url and not rss_url.startswith(('http://', 'https://')):
            raise ValidationError("RSS feed URL must be a valid HTTP/HTTPS URL")
        
        query = """
            INSERT INTO podcasts (
                tenant_id, name, rss_feed_url, description, created_by
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING podcast_id, tenant_id, name, rss_feed_url, description,
                      created_at, updated_at
        """
        
        podcast = await self.postgres_conn.fetchrow(
            query,
            tenant_id,
            podcast_data['name'],
            rss_url,
            podcast_data.get('description'),
            user_id
        )
        
        await self.events.log_event(
            event_type='podcast.created',
            user_id=user_id,
            properties={
                'podcast_id': str(podcast['podcast_id']),
                'tenant_id': tenant_id
            }
        )
        
        self.metrics.increment_counter('podcasts_created_total', {
            'tenant_id': tenant_id
        })
        
        return dict(podcast)
    
    async def get_podcast(
        self,
        podcast_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Get a podcast by ID"""
        podcast = await self.postgres_conn.fetchrow(
            """
            SELECT podcast_id, tenant_id, name, rss_feed_url, description,
                   created_at, updated_at
            FROM podcasts
            WHERE podcast_id = $1 AND tenant_id = $2
            """,
            podcast_id,
            tenant_id
        )
        
        if not podcast:
            raise NotFoundError("podcast", podcast_id)
        
        return dict(podcast)
    
    async def list_podcasts(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List podcasts for a tenant"""
        podcasts = await self.postgres_conn.fetch(
            """
            SELECT podcast_id, tenant_id, name, rss_feed_url, description,
                   created_at, updated_at
            FROM podcasts
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id,
            limit,
            offset
        )
        
        return [dict(podcast) for podcast in podcasts]
    
    async def update_podcast(
        self,
        podcast_id: str,
        tenant_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a podcast"""
        podcast = await self.get_podcast(podcast_id, tenant_id)
        
        updates = []
        params = []
        param_index = 1
        
        if 'name' in update_data:
            updates.append(f"name = ${param_index}")
            params.append(update_data['name'])
            param_index += 1
        
        if 'rss_feed_url' in update_data:
            updates.append(f"rss_feed_url = ${param_index}")
            params.append(update_data['rss_feed_url'])
            param_index += 1
        
        if 'description' in update_data:
            updates.append(f"description = ${param_index}")
            params.append(update_data['description'])
            param_index += 1
        
        if not updates:
            return podcast
        
        updates.append("updated_at = NOW()")
        params.extend([podcast_id, tenant_id])
        
        query = f"""
            UPDATE podcasts
            SET {', '.join(updates)}
            WHERE podcast_id = ${param_index} AND tenant_id = ${param_index + 1}
            RETURNING podcast_id, tenant_id, name, rss_feed_url, description,
                      created_at, updated_at
        """
        
        updated = await self.postgres_conn.fetchrow(query, *params)
        
        await self.events.log_event(
            event_type='podcast.updated',
            user_id=user_id,
            properties={
                'podcast_id': podcast_id,
                'tenant_id': tenant_id
            }
        )
        
        return dict(updated)

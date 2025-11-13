"""
Host API Integration Module

Integrates with podcast hosting platforms to fetch:
- Episode data
- Analytics metrics
- Listener statistics
"""

import logging
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class HostPlatform(Enum):
    """Supported hosting platforms"""
    LIBSYN = "libsyn"
    ANCHOR = "anchor"
    BUZZSPROUT = "buzzsprout"
    SOUNDCLOUD = "soundcloud"
    SPREAKER = "spreaker"
    PODBEAN = "podbean"
    CASTOS = "castos"
    SIMPLECAST = "simplecast"


@dataclass
class HostCredentials:
    """Host platform credentials"""
    platform: HostPlatform
    api_key: str
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class HostEpisode:
    """Episode data from host platform"""
    episode_id: str
    title: str
    description: str
    audio_url: str
    publish_date: datetime
    duration_seconds: int
    download_count: Optional[int] = None
    play_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HostAnalytics:
    """Analytics data from host platform"""
    podcast_id: str
    date_range_start: datetime
    date_range_end: datetime
    total_downloads: int
    total_plays: int
    unique_listeners: int
    completion_rate: Optional[float] = None
    demographics: Optional[Dict[str, Any]] = None
    platform_breakdown: Optional[Dict[str, int]] = None


class HostAPIClient:
    """
    Base class for host API clients
    """
    
    def __init__(
        self,
        credentials: HostCredentials,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.credentials = credentials
        self.metrics = metrics_collector
        self.events = event_logger
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def get_episodes(
        self,
        podcast_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[HostEpisode]:
        """Get episodes from host platform"""
        raise NotImplementedError
    
    async def get_analytics(
        self,
        podcast_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> HostAnalytics:
        """Get analytics from host platform"""
        raise NotImplementedError


class LibsynAPIClient(HostAPIClient):
    """Libsyn API client"""
    
    BASE_URL = "https://api.libsyn.com"
    
    async def get_episodes(
        self,
        podcast_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[HostEpisode]:
        """Get episodes from Libsyn"""
        url = f"{self.BASE_URL}/episodes"
        headers = {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "show_id": podcast_id,
            "limit": limit,
            "offset": offset
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                episodes = []
                for item in data.get("episodes", []):
                    episode = HostEpisode(
                        episode_id=str(item.get("id")),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        audio_url=item.get("media_url", ""),
                        publish_date=datetime.fromisoformat(item.get("published_at", "")),
                        duration_seconds=item.get("duration", 0),
                        download_count=item.get("downloads", 0),
                        play_count=item.get("plays", 0),
                        metadata=item
                    )
                    episodes.append(episode)
                
                # Record telemetry
                self.metrics.increment_counter(
                    "host_api_episodes_fetched",
                    tags={"platform": HostPlatform.LIBSYN.value, "count": len(episodes)}
                )
                
                return episodes
                
        except Exception as e:
            logger.error(f"Error fetching Libsyn episodes: {e}")
            self.metrics.increment_counter(
                "host_api_errors",
                tags={"platform": HostPlatform.LIBSYN.value, "error_type": type(e).__name__}
            )
            raise
    
    async def get_analytics(
        self,
        podcast_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> HostAnalytics:
        """Get analytics from Libsyn"""
        url = f"{self.BASE_URL}/analytics"
        headers = {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "show_id": podcast_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                analytics = HostAnalytics(
                    podcast_id=podcast_id,
                    date_range_start=start_date,
                    date_range_end=end_date,
                    total_downloads=data.get("total_downloads", 0),
                    total_plays=data.get("total_plays", 0),
                    unique_listeners=data.get("unique_listeners", 0),
                    completion_rate=data.get("completion_rate"),
                    demographics=data.get("demographics"),
                    platform_breakdown=data.get("platform_breakdown")
                )
                
                # Record telemetry
                self.metrics.increment_counter(
                    "host_api_analytics_fetched",
                    tags={"platform": HostPlatform.LIBSYN.value}
                )
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error fetching Libsyn analytics: {e}")
            self.metrics.increment_counter(
                "host_api_errors",
                tags={"platform": HostPlatform.LIBSYN.value, "error_type": type(e).__name__}
            )
            raise


class AnchorAPIClient(HostAPIClient):
    """Anchor (Spotify) API client"""
    
    BASE_URL = "https://api.anchor.fm/api"
    
    async def get_episodes(
        self,
        podcast_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[HostEpisode]:
        """Get episodes from Anchor"""
        # Anchor API implementation
        # Note: Anchor uses Spotify's API for some data
        url = f"{self.BASE_URL}/v1/episodes"
        headers = {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "show_id": podcast_id,
            "limit": limit,
            "offset": offset
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                episodes = []
                for item in data.get("items", []):
                    episode = HostEpisode(
                        episode_id=item.get("id", ""),
                        title=item.get("name", ""),
                        description=item.get("description", ""),
                        audio_url=item.get("audio_preview_url", ""),
                        publish_date=datetime.fromisoformat(item.get("release_date", "")),
                        duration_seconds=item.get("duration_ms", 0) // 1000,
                        metadata=item
                    )
                    episodes.append(episode)
                
                self.metrics.increment_counter(
                    "host_api_episodes_fetched",
                    tags={"platform": HostPlatform.ANCHOR.value, "count": len(episodes)}
                )
                
                return episodes
                
        except Exception as e:
            logger.error(f"Error fetching Anchor episodes: {e}")
            self.metrics.increment_counter(
                "host_api_errors",
                tags={"platform": HostPlatform.ANCHOR.value, "error_type": type(e).__name__}
            )
            raise
    
    async def get_analytics(
        self,
        podcast_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> HostAnalytics:
        """Get analytics from Anchor"""
        # Implementation similar to Libsyn
        # Placeholder for now
        raise NotImplementedError("Anchor analytics not yet implemented")


class HostAPIManager:
    """
    Manager for host API integrations
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._clients: Dict[str, HostAPIClient] = {}
    
    def register_client(
        self,
        podcast_id: str,
        credentials: HostCredentials
    ):
        """Register a host API client for a podcast"""
        client_class = self._get_client_class(credentials.platform)
        client = client_class(credentials, self.metrics, self.events)
        self._clients[podcast_id] = client
    
    def _get_client_class(self, platform: HostPlatform) -> type[HostAPIClient]:
        """Get client class for platform"""
        clients = {
            HostPlatform.LIBSYN: LibsynAPIClient,
            HostPlatform.ANCHOR: AnchorAPIClient,
        }
        return clients.get(platform, HostAPIClient)
    
    async def get_episodes(
        self,
        podcast_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[HostEpisode]:
        """Get episodes for a podcast"""
        client = self._clients.get(podcast_id)
        if not client:
            raise ValueError(f"No host API client registered for podcast {podcast_id}")
        
        if not client.session:
            await client.initialize()
        
        return await client.get_episodes(podcast_id, limit, offset)
    
    async def get_analytics(
        self,
        podcast_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> HostAnalytics:
        """Get analytics for a podcast"""
        client = self._clients.get(podcast_id)
        if not client:
            raise ValueError(f"No host API client registered for podcast {podcast_id}")
        
        if not client.session:
            await client.initialize()
        
        return await client.get_analytics(podcast_id, start_date, end_date)
    
    async def sync_all_podcasts(self):
        """Sync all registered podcasts"""
        for podcast_id, client in self._clients.items():
            try:
                if not client.session:
                    await client.initialize()
                
                episodes = await client.get_episodes(podcast_id)
                
                # Log event
                await self.events.log_event(
                    event_type="host_api_sync_completed",
                    user_id=None,
                    properties={
                        "podcast_id": podcast_id,
                        "platform": client.credentials.platform.value,
                        "episodes_synced": len(episodes)
                    }
                )
                
            except Exception as e:
                logger.error(f"Error syncing podcast {podcast_id}: {e}")
                self.metrics.increment_counter(
                    "host_api_sync_errors",
                    tags={"podcast_id": podcast_id, "error_type": type(e).__name__}
                )
    
    async def cleanup(self):
        """Cleanup all clients"""
        for client in self._clients.values():
            await client.cleanup()

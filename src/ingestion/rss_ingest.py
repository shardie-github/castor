"""
RSS/Feed Ingestion Module

This module handles RSS feed polling, episode metadata extraction,
and feed validation/normalization. It includes telemetry capture for
ingestion latency, feed errors, and poll success rates.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import feedparser
import aiohttp
from urllib.parse import urlparse

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class FeedStatus(Enum):
    """Feed processing status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID = "invalid"


@dataclass
class EpisodeMetadata:
    """Episode metadata extracted from RSS feed"""
    episode_id: str
    title: str
    description: str
    publish_date: datetime
    duration: Optional[int]  # in seconds
    audio_url: str
    guid: str
    link: Optional[str]
    author: Optional[str]
    categories: List[str]
    explicit: bool = False


@dataclass
class FeedMetadata:
    """Feed metadata"""
    feed_url: str
    podcast_title: str
    podcast_description: str
    podcast_author: str
    podcast_image_url: Optional[str]
    language: str
    last_build_date: Optional[datetime]
    episodes: List[EpisodeMetadata]


class RSSIngestService:
    """
    RSS Feed Ingestion Service
    
    Handles:
    - RSS feed polling (every 15 minutes)
    - Episode metadata extraction
    - Feed validation & normalization
    - Telemetry capture
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        poll_interval: int = 900  # 15 minutes
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.poll_interval = poll_interval
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def poll_feed(self, feed_url: str, podcast_id: str) -> FeedMetadata:
        """
        Poll RSS feed and extract metadata
        
        Args:
            feed_url: RSS feed URL
            podcast_id: Podcast identifier
            
        Returns:
            FeedMetadata with episodes
            
        Telemetry:
            - ingestion_latency: Time to fetch and parse feed
            - feed_errors: Feed parsing errors
            - poll_success_rate: Success rate of feed polls
        """
        start_time = datetime.now(timezone.utc)
        status = FeedStatus.SUCCESS
        error_message = None
        
        try:
            # Fetch feed
            feed_data = await self._fetch_feed(feed_url)
            
            # Parse feed
            parsed_feed = feedparser.parse(feed_data)
            
            # Validate feed
            if parsed_feed.bozo:
                status = FeedStatus.INVALID
                error_message = str(parsed_feed.bozo_exception)
                logger.warning(f"Invalid feed {feed_url}: {error_message}")
            
            # Extract metadata
            feed_metadata = self._extract_feed_metadata(parsed_feed, feed_url)
            
            # Log success
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics.record_histogram(
                "ingestion_latency",
                latency_ms,
                tags={"podcast_id": podcast_id, "feed_url": feed_url}
            )
            self.metrics.increment_counter(
                "feed_poll_success",
                tags={"podcast_id": podcast_id, "status": status.value}
            )
            
            # Log event
            await self.events.log_event(
                event_type="feed_polled",
                user_id=None,
                properties={
                    "podcast_id": podcast_id,
                    "feed_url": feed_url,
                    "status": status.value,
                    "episode_count": len(feed_metadata.episodes),
                    "latency_ms": latency_ms
                }
            )
            
            return feed_metadata
            
        except asyncio.TimeoutError:
            status = FeedStatus.TIMEOUT
            error_message = "Feed fetch timeout"
            logger.error(f"Timeout fetching feed {feed_url}")
            
        except Exception as e:
            status = FeedStatus.ERROR
            error_message = str(e)
            logger.error(f"Error fetching feed {feed_url}: {e}")
            
        finally:
            # Record telemetry
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics.record_histogram(
                "ingestion_latency",
                latency_ms,
                tags={"podcast_id": podcast_id, "status": status.value}
            )
            self.metrics.increment_counter(
                "feed_poll_errors",
                tags={"podcast_id": podcast_id, "error_type": type(e).__name__ if 'e' in locals() else "unknown"}
            )
            
            if status != FeedStatus.SUCCESS:
                await self.events.log_event(
                    event_type="feed_poll_failed",
                    user_id=None,
                    properties={
                        "podcast_id": podcast_id,
                        "feed_url": feed_url,
                        "status": status.value,
                        "error": error_message
                    }
                )
                
        if status != FeedStatus.SUCCESS:
            raise Exception(f"Failed to poll feed: {error_message}")
    
    async def _fetch_feed(self, feed_url: str) -> str:
        """Fetch RSS feed content"""
        if not self.session:
            await self.initialize()
            
        async with self.session.get(feed_url) as response:
            response.raise_for_status()
            return await response.text()
    
    def _extract_feed_metadata(self, parsed_feed: feedparser.FeedParserDict, feed_url: str) -> FeedMetadata:
        """Extract feed and episode metadata"""
        feed_info = parsed_feed.feed
        
        # Extract feed metadata
        podcast_title = feed_info.get("title", "Unknown")
        podcast_description = feed_info.get("description", "")
        podcast_author = feed_info.get("author", feed_info.get("itunes_author", "Unknown"))
        podcast_image_url = feed_info.get("image", {}).get("href") if feed_info.get("image") else None
        language = feed_info.get("language", "en")
        
        # Parse last build date
        last_build_date = None
        if feed_info.get("updated_parsed"):
            last_build_date = datetime(*feed_info.updated_parsed[:6], tzinfo=timezone.utc)
        
        # Extract episodes
        episodes = []
        for entry in parsed_feed.entries:
            episode = self._extract_episode_metadata(entry)
            if episode:
                episodes.append(episode)
        
        return FeedMetadata(
            feed_url=feed_url,
            podcast_title=podcast_title,
            podcast_description=podcast_description,
            podcast_author=podcast_author,
            podcast_image_url=podcast_image_url,
            language=language,
            last_build_date=last_build_date,
            episodes=episodes
        )
    
    def _extract_episode_metadata(self, entry: Dict[str, Any]) -> Optional[EpisodeMetadata]:
        """Extract episode metadata from feed entry"""
        try:
            # Get GUID (unique identifier)
            guid = entry.get("id") or entry.get("guid", "")
            if not guid:
                logger.warning("Episode missing GUID, skipping")
                return None
            
            # Get audio URL
            audio_url = None
            for link in entry.get("links", []):
                if link.get("type", "").startswith("audio/"):
                    audio_url = link.get("href")
                    break
            
            if not audio_url:
                # Try itunes_enclosure
                enclosures = entry.get("enclosures", [])
                if enclosures:
                    audio_url = enclosures[0].get("href")
            
            if not audio_url:
                logger.warning(f"Episode {guid} missing audio URL, skipping")
                return None
            
            # Parse publish date
            publish_date = datetime.now(timezone.utc)
            if entry.get("published_parsed"):
                publish_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif entry.get("updated_parsed"):
                publish_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            
            # Get duration
            duration = None
            if entry.get("itunes_duration"):
                duration_str = entry.itunes_duration
                # Parse HH:MM:SS or MM:SS format
                parts = duration_str.split(":")
                if len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
            
            # Get explicit flag
            explicit = entry.get("itunes_explicit", "").lower() in ("yes", "true", "explicit")
            
            return EpisodeMetadata(
                episode_id=f"{guid}_{publish_date.isoformat()}",
                title=entry.get("title", "Untitled"),
                description=entry.get("description", entry.get("summary", "")),
                publish_date=publish_date,
                duration=duration,
                audio_url=audio_url,
                guid=guid,
                link=entry.get("link"),
                author=entry.get("author", entry.get("itunes_author")),
                categories=[tag.term for tag in entry.get("tags", [])],
                explicit=explicit
            )
            
        except Exception as e:
            logger.error(f"Error extracting episode metadata: {e}")
            return None
    
    async def poll_all_feeds(self, feed_configs: List[Dict[str, str]]) -> Dict[str, FeedMetadata]:
        """
        Poll multiple feeds concurrently
        
        Args:
            feed_configs: List of dicts with 'feed_url' and 'podcast_id'
            
        Returns:
            Dict mapping podcast_id to FeedMetadata
        """
        tasks = [
            self.poll_feed(config["feed_url"], config["podcast_id"])
            for config in feed_configs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        feed_metadata_map = {}
        for i, result in enumerate(results):
            podcast_id = feed_configs[i]["podcast_id"]
            if isinstance(result, Exception):
                logger.error(f"Error polling feed for {podcast_id}: {result}")
            else:
                feed_metadata_map[podcast_id] = result
                
        return feed_metadata_map


class FeedPollScheduler:
    """
    Background scheduler for RSS feed polling
    
    Polls feeds every 15 minutes and processes updates
    """
    
    def __init__(
        self,
        ingest_service: RSSIngestService,
        feed_storage: Any,  # FeedStorage interface
        metrics_collector: MetricsCollector
    ):
        self.ingest_service = ingest_service
        self.feed_storage = feed_storage
        self.metrics = metrics_collector
        self.running = False
        
    async def start(self):
        """Start polling scheduler"""
        self.running = True
        await self.ingest_service.initialize()
        
        while self.running:
            try:
                # Get all active feeds
                feeds = await self.feed_storage.get_active_feeds()
                
                # Poll all feeds
                feed_configs = [
                    {"feed_url": feed["feed_url"], "podcast_id": feed["podcast_id"]}
                    for feed in feeds
                ]
                
                if feed_configs:
                    results = await self.ingest_service.poll_all_feeds(feed_configs)
                    
                    # Store results
                    for podcast_id, feed_metadata in results.items():
                        await self.feed_storage.store_feed_metadata(podcast_id, feed_metadata)
                    
                    # Record success rate
                    success_count = len(results)
                    total_count = len(feed_configs)
                    success_rate = success_count / total_count if total_count > 0 else 0
                    
                    self.metrics.record_gauge(
                        "feed_poll_success_rate",
                        success_rate * 100,
                        tags={}
                    )
                
                # Wait for next poll interval
                await asyncio.sleep(self.ingest_service.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in feed poll scheduler: {e}")
                self.metrics.increment_counter(
                    "feed_scheduler_errors",
                    tags={"error_type": type(e).__name__}
                )
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop(self):
        """Stop polling scheduler"""
        self.running = False
        await self.ingest_service.cleanup()

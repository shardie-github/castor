"""
Analytics Store Module

Handles storage and retrieval of analytics data including:
- Listener metrics (downloads, streams, completion rates)
- Attribution events
- Campaign performance data
- Time-series data aggregation
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.database import TimescaleConnection, PostgresConnection

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Analytics metric types"""
    DOWNLOADS = "downloads"
    STREAMS = "streams"
    COMPLETION_RATE = "completion_rate"
    LISTENERS = "listeners"
    ATTRIBUTION_EVENTS = "attribution_events"
    CONVERSIONS = "conversions"


@dataclass
class ListenerMetric:
    """Listener metric data point"""
    timestamp: datetime
    podcast_id: str
    episode_id: Optional[str]
    metric_type: MetricType
    value: float
    platform: Optional[str] = None
    country: Optional[str] = None
    device: Optional[str] = None


@dataclass
class AttributionEvent:
    """Attribution event"""
    event_id: str
    timestamp: datetime
    campaign_id: str
    podcast_id: str
    episode_id: Optional[str]
    attribution_method: str  # promo_code, pixel, utm
    conversion_value: Optional[float] = None
    conversion_type: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class CampaignPerformance:
    """Campaign performance metrics"""
    campaign_id: str
    podcast_id: str
    start_date: datetime
    end_date: datetime
    total_downloads: int
    total_streams: int
    total_listeners: int
    attribution_events: int
    conversions: int
    conversion_value: float
    roi: Optional[float] = None
    roas: Optional[float] = None


class AnalyticsStore:
    """
    Analytics Store
    
    Stores and retrieves analytics data with support for:
    - Time-series queries
    - Aggregations
    - Campaign performance calculations
    - Attribution tracking
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        timescale_conn: Optional[TimescaleConnection] = None,
        postgres_conn: Optional[PostgresConnection] = None
    ):
        self.metrics = metrics_collector
        self.timescale = timescale_conn
        self.postgres = postgres_conn
        # Use database if connections are available, otherwise fallback to in-memory
        # Prefer PostgreSQL for attribution events even if TimescaleDB is not available
        self._use_db = (timescale_conn is not None) or (postgres_conn is not None)
        self._use_timescale = timescale_conn is not None
        self._use_postgres = postgres_conn is not None
        
        # Initialize in-memory storage as fallback
        self._storage: Dict[str, List[ListenerMetric]] = {}
        self._attribution_events: Dict[str, List[AttributionEvent]] = {}
        self._campaign_performance: Dict[str, CampaignPerformance] = {}
        
        if not self._use_db:
            logger.warning("AnalyticsStore initialized without database connections - using in-memory storage only")
        
    async def store_listener_metric(self, metric: ListenerMetric):
        """Store a listener metric"""
        if self._use_db and self.timescale:
            # Store in TimescaleDB
            query = """
                INSERT INTO listener_metrics 
                (timestamp, podcast_id, episode_id, metric_type, value, platform, country, device)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            await self.timescale.execute(
                query,
                metric.timestamp,
                metric.podcast_id,
                metric.episode_id,
                metric.metric_type.value,
                metric.value,
                metric.platform,
                metric.country,
                metric.device
            )
        else:
            # Fallback to in-memory storage
            key = f"{metric.podcast_id}_{metric.metric_type.value}"
            if key not in self._storage:
                self._storage[key] = []
            self._storage[key].append(metric)
        
        # Record telemetry
        self.metrics.increment_counter(
            "analytics_metric_stored",
            tags={"metric_type": metric.metric_type.value, "podcast_id": metric.podcast_id}
        )
    
    async def store_attribution_event(self, event: AttributionEvent):
        """Store an attribution event"""
        if self._use_postgres and self.postgres:
            try:
                # Store in PostgreSQL
                query = """
                    INSERT INTO attribution_events 
                    (event_id, timestamp, campaign_id, podcast_id, episode_id, attribution_method, 
                     conversion_value, conversion_type, user_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (event_id) DO NOTHING
                """
                await self.postgres.execute(
                    query,
                    event.event_id,
                    event.timestamp,
                    event.campaign_id,
                    event.podcast_id,
                    event.episode_id,
                    event.attribution_method,
                    event.conversion_value,
                    event.conversion_type,
                    event.user_id
                )
            except Exception as e:
                logger.error(f"Failed to store attribution event in database: {e}, falling back to in-memory")
                # Fallback to in-memory storage
                campaign_key = f"campaign_{event.campaign_id}"
                if campaign_key not in self._attribution_events:
                    self._attribution_events[campaign_key] = []
                self._attribution_events[campaign_key].append(event)
        else:
            # Fallback to in-memory storage
            campaign_key = f"campaign_{event.campaign_id}"
            if campaign_key not in self._attribution_events:
                self._attribution_events[campaign_key] = []
            self._attribution_events[campaign_key].append(event)
        
        # Record telemetry
        self.metrics.increment_counter(
            "attribution_event_stored",
            tags={"campaign_id": event.campaign_id, "method": event.attribution_method}
        )
    
    async def get_listener_metrics(
        self,
        podcast_id: str,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[str] = None,
        episode_id: Optional[str] = None
    ) -> List[ListenerMetric]:
        """Get listener metrics for a time range"""
        import time
        start_time = time.time()
        
        if self._use_db and self.timescale:
            # Query from TimescaleDB
            query = """
                SELECT timestamp, podcast_id, episode_id, metric_type, value, platform, country, device
                FROM listener_metrics
                WHERE podcast_id = $1 AND metric_type = $2 
                  AND timestamp >= $3 AND timestamp <= $4
            """
            params = [podcast_id, metric_type.value, start_date, end_date]
            
            if platform:
                query += " AND platform = $5"
                params.append(platform)
            
            if episode_id:
                query += " AND episode_id = $6"
                params.append(episode_id)
            
            rows = await self.timescale.fetch(query, *params)
            
            metrics = [
                ListenerMetric(
                    timestamp=row["timestamp"],
                    podcast_id=row["podcast_id"],
                    episode_id=row["episode_id"],
                    metric_type=MetricType(row["metric_type"]),
                    value=float(row["value"]),
                    platform=row["platform"],
                    country=row["country"],
                    device=row["device"]
                )
                for row in rows
            ]
        else:
            # Fallback to in-memory storage
            key = f"{podcast_id}_{metric_type.value}"
            metrics = self._storage.get(key, [])
            
            # Filter by date range
            filtered = [
                m for m in metrics
                if start_date <= m.timestamp <= end_date
            ]
            
            # Filter by platform if specified
            if platform:
                filtered = [m for m in filtered if m.platform == platform]
            
            # Filter by episode if specified
            if episode_id:
                filtered = [m for m in filtered if m.episode_id == episode_id]
            
            metrics = filtered
        
        # Record query telemetry
        latency = time.time() - start_time
        self.metrics.record_histogram(
            "analytics_query_latency",
            latency,
            tags={"metric_type": metric_type.value, "podcast_id": podcast_id}
        )
        
        return metrics
    
    async def get_attribution_events(
        self,
        campaign_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttributionEvent]:
        """Get attribution events for a campaign"""
        if self._use_postgres and self.postgres:
            try:
                # Query from PostgreSQL
                query = """
                    SELECT event_id, timestamp, campaign_id, podcast_id, episode_id,
                           attribution_method, conversion_value, conversion_type, user_id
                    FROM attribution_events
                    WHERE campaign_id = $1
                """
                params = [campaign_id]
                
                if start_date:
                    query += " AND timestamp >= $" + str(len(params) + 1)
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= $" + str(len(params) + 1)
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC"
                
                rows = await self.postgres.fetch(query, *params)
                
                events = [
                    AttributionEvent(
                        event_id=str(row["event_id"]),
                        timestamp=row["timestamp"],
                        campaign_id=str(row["campaign_id"]),
                        podcast_id=str(row["podcast_id"]),
                        episode_id=str(row["episode_id"]) if row["episode_id"] else None,
                        attribution_method=row["attribution_method"],
                        conversion_value=float(row["conversion_value"]) if row["conversion_value"] else None,
                        conversion_type=row["conversion_type"],
                        user_id=str(row["user_id"]) if row["user_id"] else None
                    )
                    for row in rows
                ]
                
                return events
            except Exception as e:
                logger.warning(f"Failed to query attribution events from database: {e}, falling back to in-memory")
                # Fallback to in-memory
                campaign_key = f"campaign_{campaign_id}"
                events = self._attribution_events.get(campaign_key, [])
                
                if start_date and end_date:
                    events = [
                        e for e in events
                        if start_date <= e.timestamp <= end_date
                    ]
                
                return events
        else:
            # Fallback to in-memory storage
            campaign_key = f"campaign_{campaign_id}"
            events = self._attribution_events.get(campaign_key, [])
            
            if start_date and end_date:
                events = [
                    e for e in events
                    if start_date <= e.timestamp <= end_date
                ]
            
            return events
    
    async def calculate_campaign_performance(
        self,
        campaign_id: str,
        podcast_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> CampaignPerformance:
        """Calculate campaign performance metrics"""
        # Get listener metrics for campaign period
        downloads = await self.get_listener_metrics(
            podcast_id, MetricType.DOWNLOADS, start_date, end_date
        )
        streams = await self.get_listener_metrics(
            podcast_id, MetricType.STREAMS, start_date, end_date
        )
        listeners = await self.get_listener_metrics(
            podcast_id, MetricType.LISTENERS, start_date, end_date
        )
        
        # Get attribution events
        attribution_events = await self.get_attribution_events(campaign_id, start_date, end_date)
        
        # Calculate totals
        total_downloads = sum(m.value for m in downloads)
        total_streams = sum(m.value for m in streams)
        total_listeners = len(set(m.value for m in listeners))
        
        # Calculate conversions
        conversions = len([e for e in attribution_events if e.conversion_type])
        conversion_value = sum(e.conversion_value or 0 for e in attribution_events)
        
        performance = CampaignPerformance(
            campaign_id=campaign_id,
            podcast_id=podcast_id,
            start_date=start_date,
            end_date=end_date,
            total_downloads=int(total_downloads),
            total_streams=int(total_streams),
            total_listeners=int(total_listeners),
            attribution_events=len(attribution_events),
            conversions=conversions,
            conversion_value=conversion_value
        )
        
        # Store performance
        self._campaign_performance[campaign_id] = performance
        
        return performance
    
    async def aggregate_metrics(
        self,
        podcast_id: str,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
        aggregation: str = "sum"  # sum, avg, min, max
    ) -> float:
        """Aggregate metrics over time range"""
        metrics = await self.get_listener_metrics(
            podcast_id, metric_type, start_date, end_date
        )
        
        if not metrics:
            return 0.0
        
        if aggregation == "sum":
            return sum(m.value for m in metrics)
        elif aggregation == "avg":
            return sum(m.value for m in metrics) / len(metrics)
        elif aggregation == "min":
            return min(m.value for m in metrics)
        elif aggregation == "max":
            return max(m.value for m in metrics)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
    
    async def get_campaign_performance(self, campaign_id: str) -> Optional[CampaignPerformance]:
        """Get stored campaign performance"""
        return self._campaign_performance.get(campaign_id)
    
    async def calculate_ttfv(self, user_id: str) -> Optional[float]:
        """
        Calculate Time to First Value (TTFV) for a user.
        TTFV = time from user.registered event to campaign.created event (in seconds)
        """
        if not self._use_postgres or not self.postgres:
            logger.warning("Cannot calculate TTFV without database connection")
            return None
        
        try:
            # Get user registration timestamp from events or users table
            user_registered = await self.postgres.fetchval(
                """
                SELECT created_at FROM users WHERE user_id = $1
                """,
                user_id
            )
            
            if not user_registered:
                return None
            
            # Get first campaign creation timestamp
            first_campaign = await self.postgres.fetchval(
                """
                SELECT MIN(c.created_at) FROM campaigns c
                INNER JOIN podcasts p ON c.podcast_id = p.podcast_id
                WHERE p.user_id = $1
                """,
                user_id
            )
            
            if not first_campaign:
                return None
            
            # Calculate TTFV in seconds
            ttfv_seconds = (first_campaign - user_registered).total_seconds()
            
            # Store TTFV for later retrieval
            await self.postgres.execute(
                """
                INSERT INTO user_metrics (user_id, metric_name, metric_value, recorded_at)
                VALUES ($1, 'ttfv_seconds', $2, NOW())
                ON CONFLICT (user_id, metric_name) 
                DO UPDATE SET metric_value = EXCLUDED.metric_value, recorded_at = EXCLUDED.recorded_at
                """,
                user_id,
                ttfv_seconds
            )
            
            return ttfv_seconds
        except Exception as e:
            logger.error(f"Failed to calculate TTFV: {e}")
            return None
    
    async def get_ttfv_distribution(self) -> Dict[str, Any]:
        """
        Get TTFV distribution statistics for all users.
        Returns percentiles and summary statistics.
        """
        if not self._use_postgres or not self.postgres:
            return {
                "p50": None,
                "p75": None,
                "p90": None,
                "p95": None,
                "mean": None,
                "count": 0
            }
        
        try:
            # Get TTFV values from user_metrics or calculate on the fly
            ttfv_values = await self.postgres.fetch(
                """
                SELECT metric_value FROM user_metrics
                WHERE metric_name = 'ttfv_seconds' AND metric_value IS NOT NULL
                ORDER BY metric_value
                """
            )
            
            if not ttfv_values:
                return {
                    "p50": None,
                    "p75": None,
                    "p90": None,
                    "p95": None,
                    "mean": None,
                    "count": 0
                }
            
            values = [float(row['metric_value']) for row in ttfv_values]
            count = len(values)
            
            if count == 0:
                return {
                    "p50": None,
                    "p75": None,
                    "p90": None,
                    "p95": None,
                    "mean": None,
                    "count": 0
                }
            
            # Calculate percentiles
            sorted_values = sorted(values)
            p50_idx = int(count * 0.5)
            p75_idx = int(count * 0.75)
            p90_idx = int(count * 0.90)
            p95_idx = int(count * 0.95)
            
            return {
                "p50": sorted_values[p50_idx] if p50_idx < count else None,
                "p75": sorted_values[p75_idx] if p75_idx < count else None,
                "p90": sorted_values[p90_idx] if p90_idx < count else None,
                "p95": sorted_values[p95_idx] if p95_idx < count else None,
                "mean": sum(values) / count,
                "count": count
            }
        except Exception as e:
            logger.error(f"Failed to get TTFV distribution: {e}")
            return {
                "p50": None,
                "p75": None,
                "p90": None,
                "p95": None,
                "mean": None,
                "count": 0
            }
    
    async def calculate_completion_rate(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> float:
        """
        Calculate campaign completion rate.
        Completion rate = campaigns with reports generated / total campaigns created
        """
        if not self._use_postgres or not self.postgres:
            return 0.0
        
        try:
            # Build date filter
            date_filter = ""
            params = []
            if start_date:
                date_filter += " AND c.created_at >= $" + str(len(params) + 1)
                params.append(start_date)
            if end_date:
                date_filter += " AND c.created_at <= $" + str(len(params) + 1)
                params.append(end_date)
            
            # Get total campaigns created
            total_campaigns = await self.postgres.fetchval(
                f"""
                SELECT COUNT(*) FROM campaigns c
                WHERE 1=1 {date_filter}
                """,
                *params
            ) or 0
            
            if total_campaigns == 0:
                return 0.0
            
            # Get campaigns with reports generated
            completed_campaigns = await self.postgres.fetchval(
                f"""
                SELECT COUNT(DISTINCT c.campaign_id) FROM campaigns c
                INNER JOIN reports r ON c.campaign_id = r.campaign_id
                WHERE 1=1 {date_filter}
                """,
                *params
            ) or 0
            
            completion_rate = (completed_campaigns / total_campaigns) * 100 if total_campaigns > 0 else 0.0
            
            return completion_rate
        except Exception as e:
            logger.error(f"Failed to calculate completion rate: {e}")
            return 0.0

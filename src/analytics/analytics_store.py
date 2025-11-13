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
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        # In production, this would connect to InfluxDB/TimescaleDB
        self._storage: Dict[str, List[ListenerMetric]] = {}
        self._attribution_events: Dict[str, List[AttributionEvent]] = {}
        self._campaign_performance: Dict[str, CampaignPerformance] = {}
        
    async def store_listener_metric(self, metric: ListenerMetric):
        """Store a listener metric"""
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
        
        # Record query telemetry
        self.metrics.record_histogram(
            "analytics_query_latency",
            value=0.1,  # Placeholder
            tags={"metric_type": metric_type.value, "podcast_id": podcast_id}
        )
        
        return filtered
    
    async def get_attribution_events(
        self,
        campaign_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttributionEvent]:
        """Get attribution events for a campaign"""
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

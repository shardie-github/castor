"""
ROI Calculation Engine

Calculates Return on Investment (ROI) and Return on Ad Spend (ROAS)
for podcast sponsorship campaigns.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.campaigns.campaign_manager import Campaign
from src.analytics.analytics_store import AttributionEvent, CampaignPerformance

logger = logging.getLogger(__name__)


class ROICalculationMethod(Enum):
    """ROI calculation methods"""
    SIMPLE = "simple"  # (revenue - cost) / cost
    ATTRIBUTED = "attributed"  # Based on attributed conversions only
    INCREMENTAL = "incremental"  # Incremental lift over baseline
    MULTI_TOUCH = "multi_touch"  # Multi-touch attribution model


@dataclass
class ROIMetrics:
    """ROI calculation results"""
    campaign_id: str
    campaign_cost: float
    conversion_value: float
    roi: float  # (conversion_value - campaign_cost) / campaign_cost
    roas: float  # conversion_value / campaign_cost
    net_profit: float  # conversion_value - campaign_cost
    payback_period_days: Optional[int] = None
    conversion_count: int = 0
    average_order_value: Optional[float] = None
    cost_per_conversion: Optional[float] = None
    conversion_rate: Optional[float] = None
    calculation_method: ROICalculationMethod = ROICalculationMethod.SIMPLE
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttributionROI:
    """ROI broken down by attribution method"""
    promo_code_roi: Optional[ROIMetrics] = None
    pixel_roi: Optional[ROIMetrics] = None
    utm_roi: Optional[ROIMetrics] = None
    direct_roi: Optional[ROIMetrics] = None
    overall_roi: ROIMetrics = None


class ROICalculator:
    """
    ROI Calculator
    
    Calculates ROI metrics for campaigns using various methods:
    - Simple ROI: (Revenue - Cost) / Cost
    - Attributed ROI: Based on attributed conversions
    - Incremental ROI: Lift over baseline
    - Multi-touch ROI: Multi-touch attribution
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def calculate_roi(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent],
        baseline_conversion_rate: Optional[float] = None,
        method: ROICalculationMethod = ROICalculationMethod.ATTRIBUTED
    ) -> ROIMetrics:
        """
        Calculate ROI for a campaign
        
        Args:
            campaign: Campaign object
            attribution_events: List of attribution events
            baseline_conversion_rate: Optional baseline conversion rate for incremental ROI
            method: Calculation method
            
        Returns:
            ROIMetrics with calculated ROI
        """
        campaign_cost = campaign.campaign_value
        
        if method == ROICalculationMethod.SIMPLE:
            return await self._calculate_simple_roi(campaign, attribution_events)
        elif method == ROICalculationMethod.ATTRIBUTED:
            return await self._calculate_attributed_roi(campaign, attribution_events)
        elif method == ROICalculationMethod.INCREMENTAL:
            return await self._calculate_incremental_roi(
                campaign, attribution_events, baseline_conversion_rate
            )
        elif method == ROICalculationMethod.MULTI_TOUCH:
            return await self._calculate_multi_touch_roi(campaign, attribution_events)
        else:
            raise ValueError(f"Unknown ROI calculation method: {method}")
    
    async def _calculate_simple_roi(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent]
    ) -> ROIMetrics:
        """Calculate simple ROI: (Revenue - Cost) / Cost"""
        campaign_cost = campaign.campaign_value
        
        # Sum all conversion values
        conversion_value = sum(
            event.conversion_value or 0
            for event in attribution_events
            if event.conversion_value is not None
        )
        
        # Calculate ROI
        roi = (conversion_value - campaign_cost) / campaign_cost if campaign_cost > 0 else 0.0
        roas = conversion_value / campaign_cost if campaign_cost > 0 else 0.0
        net_profit = conversion_value - campaign_cost
        
        # Count conversions
        conversions = [e for e in attribution_events if e.conversion_type]
        conversion_count = len(conversions)
        
        # Calculate additional metrics
        avg_order_value = conversion_value / conversion_count if conversion_count > 0 else None
        cost_per_conversion = campaign_cost / conversion_count if conversion_count > 0 else None
        
        return ROIMetrics(
            campaign_id=campaign.campaign_id,
            campaign_cost=campaign_cost,
            conversion_value=conversion_value,
            roi=roi,
            roas=roas,
            net_profit=net_profit,
            conversion_count=conversion_count,
            average_order_value=avg_order_value,
            cost_per_conversion=cost_per_conversion,
            calculation_method=ROICalculationMethod.SIMPLE
        )
    
    async def _calculate_attributed_roi(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent]
    ) -> ROIMetrics:
        """Calculate ROI based on attributed conversions only"""
        campaign_cost = campaign.campaign_value
        
        # Filter to only attributed events (those matching campaign attribution config)
        attributed_events = self._filter_attributed_events(campaign, attribution_events)
        
        # Sum conversion values from attributed events
        conversion_value = sum(
            event.conversion_value or 0
            for event in attributed_events
            if event.conversion_value is not None
        )
        
        # Calculate ROI
        roi = (conversion_value - campaign_cost) / campaign_cost if campaign_cost > 0 else 0.0
        roas = conversion_value / campaign_cost if campaign_cost > 0 else 0.0
        net_profit = conversion_value - campaign_cost
        
        # Count conversions
        conversions = [e for e in attributed_events if e.conversion_type]
        conversion_count = len(conversions)
        
        # Calculate additional metrics
        avg_order_value = conversion_value / conversion_count if conversion_count > 0 else None
        cost_per_conversion = campaign_cost / conversion_count if conversion_count > 0 else None
        
        # Calculate conversion rate (if we have listener data)
        # This would require listener event data
        conversion_rate = None
        
        return ROIMetrics(
            campaign_id=campaign.campaign_id,
            campaign_cost=campaign_cost,
            conversion_value=conversion_value,
            roi=roi,
            roas=roas,
            net_profit=net_profit,
            conversion_count=conversion_count,
            average_order_value=avg_order_value,
            cost_per_conversion=cost_per_conversion,
            conversion_rate=conversion_rate,
            calculation_method=ROICalculationMethod.ATTRIBUTED,
            metadata={"attributed_events_count": len(attributed_events)}
        )
    
    async def _calculate_incremental_roi(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent],
        baseline_conversion_rate: Optional[float]
    ) -> ROIMetrics:
        """Calculate incremental ROI (lift over baseline)"""
        if baseline_conversion_rate is None:
            logger.warning("Baseline conversion rate not provided, falling back to attributed ROI")
            return await self._calculate_attributed_roi(campaign, attribution_events)
        
        campaign_cost = campaign.campaign_value
        
        # Get attributed events
        attributed_events = self._filter_attributed_events(campaign, attribution_events)
        
        # Calculate actual conversion rate
        # This would require listener event data to calculate total listeners
        # For now, use attributed conversions as proxy
        actual_conversions = len([e for e in attributed_events if e.conversion_type])
        
        # Calculate incremental conversions
        # This is a simplified calculation - in production, would use actual listener data
        conversion_value = sum(
            event.conversion_value or 0
            for event in attributed_events
            if event.conversion_value is not None
        )
        
        # Calculate ROI with incremental lift
        roi = (conversion_value - campaign_cost) / campaign_cost if campaign_cost > 0 else 0.0
        roas = conversion_value / campaign_cost if campaign_cost > 0 else 0.0
        net_profit = conversion_value - campaign_cost
        
        return ROIMetrics(
            campaign_id=campaign.campaign_id,
            campaign_cost=campaign_cost,
            conversion_value=conversion_value,
            roi=roi,
            roas=roas,
            net_profit=net_profit,
            conversion_count=actual_conversions,
            calculation_method=ROICalculationMethod.INCREMENTAL,
            metadata={
                "baseline_conversion_rate": baseline_conversion_rate,
                "incremental_lift": None  # Would calculate actual lift
            }
        )
    
    async def _calculate_multi_touch_roi(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent]
    ) -> ROIMetrics:
        """Calculate ROI using multi-touch attribution model"""
        # Multi-touch attribution assigns fractional credit to each touchpoint
        # For now, implement a simple linear model (equal credit to all touchpoints)
        
        campaign_cost = campaign.campaign_value
        
        # Group events by user/session to identify multi-touch paths
        user_paths = self._build_user_paths(attribution_events)
        
        # Calculate fractional attribution
        total_attributed_value = 0.0
        conversion_count = 0
        
        for user_id, events in user_paths.items():
            conversions = [e for e in events if e.conversion_type]
            if conversions:
                # Use last-touch attribution for now
                # In production, would use more sophisticated models (linear, time-decay, etc.)
                last_event = conversions[-1]
                if last_event.conversion_value:
                    total_attributed_value += last_event.conversion_value
                    conversion_count += 1
        
        # Calculate ROI
        roi = (total_attributed_value - campaign_cost) / campaign_cost if campaign_cost > 0 else 0.0
        roas = total_attributed_value / campaign_cost if campaign_cost > 0 else 0.0
        net_profit = total_attributed_value - campaign_cost
        
        return ROIMetrics(
            campaign_id=campaign.campaign_id,
            campaign_cost=campaign_cost,
            conversion_value=total_attributed_value,
            roi=roi,
            roas=roas,
            net_profit=net_profit,
            conversion_count=conversion_count,
            calculation_method=ROICalculationMethod.MULTI_TOUCH,
            metadata={"user_paths_count": len(user_paths)}
        )
    
    def _filter_attributed_events(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent]
    ) -> List[AttributionEvent]:
        """Filter events that match campaign attribution configuration"""
        config = campaign.attribution_config
        
        filtered = []
        for event in attribution_events:
            if event.campaign_id != campaign.campaign_id:
                continue
            
            # Match by attribution method
            if event.attribution_method == config.method.value:
                filtered.append(event)
            # Additional matching logic based on config (promo codes, UTM params, etc.)
            elif config.method.value == "promo_code" and config.promo_code:
                # Check if event has matching promo code
                # This would require access to event attribution_data
                pass
        
        return filtered
    
    def _build_user_paths(
        self,
        attribution_events: List[AttributionEvent]
    ) -> Dict[str, List[AttributionEvent]]:
        """Build user conversion paths for multi-touch attribution"""
        paths = {}
        
        for event in attribution_events:
            user_id = event.user_id or event.session_id or "unknown"
            if user_id not in paths:
                paths[user_id] = []
            paths[user_id].append(event)
        
        # Sort events by timestamp
        for user_id in paths:
            paths[user_id].sort(key=lambda e: e.timestamp)
        
        return paths
    
    async def calculate_payback_period(
        self,
        campaign: Campaign,
        roi_metrics: ROIMetrics,
        daily_conversion_rate: Optional[float] = None
    ) -> Optional[int]:
        """
        Calculate payback period in days
        
        Args:
            campaign: Campaign object
            roi_metrics: Calculated ROI metrics
            daily_conversion_rate: Optional daily conversion rate
            
        Returns:
            Payback period in days, or None if cannot be calculated
        """
        if roi_metrics.net_profit <= 0:
            return None  # No payback if negative ROI
        
        if daily_conversion_rate is None:
            # Estimate from campaign duration
            campaign_duration = (campaign.end_date - campaign.start_date).days
            if campaign_duration > 0 and roi_metrics.conversion_count > 0:
                daily_conversion_rate = roi_metrics.conversion_value / campaign_duration
            else:
                return None
        
        if daily_conversion_rate <= 0:
            return None
        
        # Calculate days to recover campaign cost
        payback_days = campaign.campaign_value / daily_conversion_rate
        
        return int(payback_days)
    
    async def calculate_roi_by_attribution_method(
        self,
        campaign: Campaign,
        attribution_events: List[AttributionEvent]
    ) -> AttributionROI:
        """Calculate ROI broken down by attribution method"""
        # Group events by attribution method
        by_method: Dict[str, List[AttributionEvent]] = {}
        for event in attribution_events:
            method = event.attribution_method
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(event)
        
        # Calculate ROI for each method
        promo_code_roi = None
        pixel_roi = None
        utm_roi = None
        direct_roi = None
        
        if "promo_code" in by_method:
            promo_code_roi = await self._calculate_attributed_roi(
                campaign, by_method["promo_code"]
            )
        
        if "pixel" in by_method:
            pixel_roi = await self._calculate_attributed_roi(
                campaign, by_method["pixel"]
            )
        
        if "utm" in by_method:
            utm_roi = await self._calculate_attributed_roi(
                campaign, by_method["utm"]
            )
        
        if "direct" in by_method:
            direct_roi = await self._calculate_attributed_roi(
                campaign, by_method["direct"]
            )
        
        # Calculate overall ROI
        overall_roi = await self._calculate_attributed_roi(campaign, attribution_events)
        
        return AttributionROI(
            promo_code_roi=promo_code_roi,
            pixel_roi=pixel_roi,
            utm_roi=utm_roi,
            direct_roi=direct_roi,
            overall_roi=overall_roi
        )
    
    async def compare_campaign_roi(
        self,
        campaigns: List[Campaign],
        attribution_events_map: Dict[str, List[AttributionEvent]]
    ) -> Dict[str, ROIMetrics]:
        """Compare ROI across multiple campaigns"""
        results = {}
        
        for campaign in campaigns:
            events = attribution_events_map.get(campaign.campaign_id, [])
            roi_metrics = await self.calculate_roi(campaign, events)
            results[campaign.campaign_id] = roi_metrics
        
        # Record telemetry
        self.metrics.increment_counter(
            "roi_calculations_completed",
            tags={"campaign_count": len(campaigns)}
        )
        
        return results

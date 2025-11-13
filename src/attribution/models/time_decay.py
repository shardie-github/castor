"""
Time-Decay Attribution Model

Gives more credit to recent touchpoints using exponential decay.
"""

from typing import List, Dict
from datetime import datetime, timezone, timedelta
from src.attribution.models.base import AttributionModel
from src.attribution.attribution_engine import AttributionPath, AttributionResult


class TimeDecayModel(AttributionModel):
    """
    Time-decay attribution model
    
    Uses exponential decay: credit = e^(-λ * days_since_touchpoint)
    Default half-life: 7 days (λ = ln(2) / 7)
    """
    
    def __init__(self, half_life_days: float = 7.0):
        """
        Initialize time-decay model
        
        Args:
            half_life_days: Half-life in days (default: 7 days)
        """
        self.half_life_days = half_life_days
        self.decay_rate = 0.693147 / half_life_days  # ln(2) / half_life
    
    def calculate(self, paths: List[AttributionPath]) -> AttributionResult:
        """Calculate time-decay attribution"""
        if not paths:
            return AttributionResult(
                campaign_id="",
                model_type=None,
                total_conversions=0,
                total_conversion_value=0.0,
                attributed_conversions=0,
                attributed_conversion_value=0.0,
                touchpoint_credits={},
                confidence_score=0.0
            )
        
        campaign_id = paths[0].touchpoints[0].campaign_id if paths[0].touchpoints else ""
        
        total_conversions = len(paths)
        total_conversion_value = sum(
            path.conversion_value or 0.0 for path in paths
        )
        
        attributed_conversions = 0
        attributed_conversion_value = 0.0
        touchpoint_credits: Dict[str, float] = {}
        
        for path in paths:
            if not path.touchpoints or not path.conversion_at:
                continue
            
            conversion_value = path.conversion_value or 0.0
            conversion_time = path.conversion_at
            
            # Calculate weights for each touchpoint
            weights: Dict[str, float] = {}
            total_weight = 0.0
            
            for touchpoint in path.touchpoints:
                days_since = (conversion_time - touchpoint.timestamp).total_seconds() / 86400
                # Exponential decay: weight = e^(-decay_rate * days)
                weight = 2.71828 ** (-self.decay_rate * max(0, days_since))
                weights[touchpoint.touchpoint_id] = weight
                total_weight += weight
            
            if total_weight == 0:
                continue
            
            # Distribute credit proportionally to weights
            for touchpoint in path.touchpoints:
                touchpoint_id = touchpoint.touchpoint_id
                weight = weights[touchpoint_id]
                
                if touchpoint_id not in touchpoint_credits:
                    touchpoint_credits[touchpoint_id] = 0.0
                
                credit = conversion_value * (weight / total_weight)
                touchpoint_credits[touchpoint_id] += credit
            
            attributed_conversions += 1
            attributed_conversion_value += conversion_value
        
        confidence_score = self._calculate_confidence_score(paths)
        
        return AttributionResult(
            campaign_id=campaign_id,
            model_type=None,
            total_conversions=total_conversions,
            total_conversion_value=total_conversion_value,
            attributed_conversions=attributed_conversions,
            attributed_conversion_value=attributed_conversion_value,
            touchpoint_credits=touchpoint_credits,
            confidence_score=confidence_score
        )

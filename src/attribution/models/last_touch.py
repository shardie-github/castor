"""
Last-Touch Attribution Model

Gives 100% credit to the last touchpoint in the conversion path.
"""

from typing import List, Dict
from src.attribution.models.base import AttributionModel
from src.attribution.attribution_engine import AttributionPath, AttributionResult


class LastTouchModel(AttributionModel):
    """Last-touch attribution model"""
    
    def calculate(self, paths: List[AttributionPath]) -> AttributionResult:
        """Calculate last-touch attribution"""
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
        
        # Count conversions attributed to last touchpoint
        attributed_conversions = 0
        attributed_conversion_value = 0.0
        touchpoint_credits: Dict[str, float] = {}
        
        for path in paths:
            if not path.touchpoints:
                continue
            
            # Last touchpoint gets 100% credit
            last_touchpoint = path.touchpoints[-1]
            touchpoint_id = last_touchpoint.touchpoint_id
            
            if touchpoint_id not in touchpoint_credits:
                touchpoint_credits[touchpoint_id] = 0.0
            
            conversion_value = path.conversion_value or 0.0
            touchpoint_credits[touchpoint_id] += conversion_value
            
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

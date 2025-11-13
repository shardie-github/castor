"""
Position-Based Attribution Model (U-Shaped)

Gives more credit to first and last touchpoints (40% each),
with remaining 20% distributed evenly among middle touchpoints.
"""

from typing import List, Dict
from src.attribution.models.base import AttributionModel
from src.attribution.attribution_engine import AttributionPath, AttributionResult


class PositionBasedModel(AttributionModel):
    """
    Position-based attribution model (U-shaped)
    
    Credit distribution:
    - First touchpoint: 40%
    - Last touchpoint: 40%
    - Middle touchpoints: 20% divided equally
    """
    
    FIRST_TOUCH_WEIGHT = 0.4
    LAST_TOUCH_WEIGHT = 0.4
    MIDDLE_TOUCH_WEIGHT = 0.2
    
    def calculate(self, paths: List[AttributionPath]) -> AttributionResult:
        """Calculate position-based attribution"""
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
            if not path.touchpoints:
                continue
            
            conversion_value = path.conversion_value or 0.0
            num_touchpoints = len(path.touchpoints)
            
            if num_touchpoints == 0:
                continue
            
            # Calculate credits
            first_touchpoint = path.touchpoints[0]
            last_touchpoint = path.touchpoints[-1]
            
            # First touchpoint gets 40%
            first_credit = conversion_value * self.FIRST_TOUCH_WEIGHT
            if first_touchpoint.touchpoint_id not in touchpoint_credits:
                touchpoint_credits[first_touchpoint.touchpoint_id] = 0.0
            touchpoint_credits[first_touchpoint.touchpoint_id] += first_credit
            
            # Last touchpoint gets 40%
            last_credit = conversion_value * self.LAST_TOUCH_WEIGHT
            if last_touchpoint.touchpoint_id not in touchpoint_credits:
                touchpoint_credits[last_touchpoint.touchpoint_id] = 0.0
            touchpoint_credits[last_touchpoint.touchpoint_id] += last_credit
            
            # Middle touchpoints get remaining 20% divided equally
            if num_touchpoints > 2:
                middle_touchpoints = path.touchpoints[1:-1]
                middle_credit_per_touchpoint = (conversion_value * self.MIDDLE_TOUCH_WEIGHT) / len(middle_touchpoints)
                
                for touchpoint in middle_touchpoints:
                    if touchpoint.touchpoint_id not in touchpoint_credits:
                        touchpoint_credits[touchpoint.touchpoint_id] = 0.0
                    touchpoint_credits[touchpoint.touchpoint_id] += middle_credit_per_touchpoint
            elif num_touchpoints == 1:
                # Single touchpoint gets 100%
                if first_touchpoint.touchpoint_id not in touchpoint_credits:
                    touchpoint_credits[first_touchpoint.touchpoint_id] = 0.0
                touchpoint_credits[first_touchpoint.touchpoint_id] += conversion_value
            
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

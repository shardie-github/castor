"""
Linear Attribution Model

Gives equal credit to all touchpoints in the conversion path.
"""

from typing import List, Dict
from src.attribution.models.base import AttributionModel
from src.attribution.attribution_engine import AttributionPath, AttributionResult


class LinearModel(AttributionModel):
    """Linear attribution model (equal credit to all touchpoints)"""
    
    def calculate(self, paths: List[AttributionPath]) -> AttributionResult:
        """Calculate linear attribution"""
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
        
        # Count conversions with equal credit distribution
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
            
            # Equal credit to each touchpoint
            credit_per_touchpoint = conversion_value / num_touchpoints
            
            for touchpoint in path.touchpoints:
                touchpoint_id = touchpoint.touchpoint_id
                
                if touchpoint_id not in touchpoint_credits:
                    touchpoint_credits[touchpoint_id] = 0.0
                
                touchpoint_credits[touchpoint_id] += credit_per_touchpoint
            
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

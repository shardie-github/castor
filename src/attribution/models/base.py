"""
Base Attribution Model

Abstract base class for attribution models.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from src.attribution.attribution_engine import AttributionPath, AttributionResult


class AttributionModel(ABC):
    """Base class for attribution models"""
    
    @abstractmethod
    def calculate(self, paths: List[AttributionPath]) -> AttributionResult:
        """
        Calculate attribution for given paths
        
        Args:
            paths: List of attribution paths
            
        Returns:
            AttributionResult with calculated attribution
        """
        pass
    
    def _calculate_confidence_score(self, paths: List[AttributionPath]) -> float:
        """
        Calculate confidence score for attribution
        
        Based on:
        - Number of touchpoints per path
        - Time between touchpoints
        - Data completeness
        """
        if not paths:
            return 0.0
        
        total_paths = len(paths)
        paths_with_multiple_touchpoints = sum(
            1 for path in paths if len(path.touchpoints) > 1
        )
        
        # Confidence increases with more touchpoints
        multi_touch_ratio = paths_with_multiple_touchpoints / total_paths if total_paths > 0 else 0
        
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on multi-touch ratio
        confidence += multi_touch_ratio * 0.3
        
        # Increase confidence if we have user IDs (better tracking)
        paths_with_user_id = sum(1 for path in paths if path.user_id)
        user_id_ratio = paths_with_user_id / total_paths if total_paths > 0 else 0
        confidence += user_id_ratio * 0.2
        
        return min(confidence, 1.0)

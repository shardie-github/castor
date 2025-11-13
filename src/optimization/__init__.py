"""
Post-Launch Optimization Module

Provides A/B testing, churn analysis, and onboarding optimization.
"""

from src.optimization.ab_testing import ABTestingFramework, Experiment, ExperimentResult
from src.optimization.churn import ChurnPredictor, ChurnAnalyzer, ChurnPrevention
from src.optimization.onboarding import OnboardingAnalyzer, OnboardingOptimizer

__all__ = [
    "ABTestingFramework",
    "Experiment",
    "ExperimentResult",
    "ChurnPredictor",
    "ChurnAnalyzer",
    "ChurnPrevention",
    "OnboardingAnalyzer",
    "OnboardingOptimizer",
]

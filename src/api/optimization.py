"""
Optimization API Endpoints

Provides endpoints for A/B testing, churn analysis, and onboarding optimization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from src.optimization import ABTestingFramework, ChurnPredictor, ChurnAnalyzer, OnboardingAnalyzer
from src.tenants.tenant_isolation import get_current_tenant

router = APIRouter()


class ExperimentCreate(BaseModel):
    experiment_name: str
    experiment_type: str
    variants: List[Dict[str, Any]]
    traffic_allocation: float = 100.0
    hypothesis: Optional[str] = None


class ExperimentResponse(BaseModel):
    experiment_id: str
    experiment_name: str
    status: str
    variants: List[Dict[str, Any]]


@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment_data: ExperimentCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    ab_testing: ABTestingFramework = Depends(lambda: request.app.state.ab_testing)
):
    """Create A/B test experiment"""
    from src.optimization.ab_testing import ExperimentType
    
    experiment = await ab_testing.create_experiment(
        tenant_id=tenant_id,
        experiment_name=experiment_data.experiment_name,
        experiment_type=ExperimentType(experiment_data.experiment_type),
        variants=experiment_data.variants,
        traffic_allocation=experiment_data.traffic_allocation,
        hypothesis=experiment_data.hypothesis
    )
    
    return ExperimentResponse(
        experiment_id=experiment.experiment_id,
        experiment_name=experiment.experiment_name,
        status=experiment.status.value,
        variants=experiment.variants
    )


@router.get("/churn/at-risk")
async def get_at_risk_users(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    threshold: float = 0.7,
    churn_predictor: ChurnPredictor = Depends(lambda: request.app.state.churn_predictor)
):
    """Get users at risk of churning"""
    at_risk = await churn_predictor.identify_at_risk_users(tenant_id, threshold)
    return {"at_risk_users": at_risk}


@router.get("/onboarding/funnel")
async def get_onboarding_funnel(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    onboarding_analyzer: OnboardingAnalyzer = Depends(lambda: request.app.state.onboarding_analyzer)
):
    """Get onboarding funnel analysis"""
    funnel = await onboarding_analyzer.analyze_onboarding_funnel(tenant_id)
    return funnel

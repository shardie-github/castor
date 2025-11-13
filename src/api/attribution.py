"""
Attribution API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.attribution import AttributionEngine, AttributionModelType
from src.tenants.tenant_isolation import get_current_tenant
from fastapi import Request

router = APIRouter()


class AttributionRequest(BaseModel):
    campaign_id: str
    model_type: str  # "first_touch", "last_touch", "linear", "time_decay", "position_based"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AttributionResponse(BaseModel):
    campaign_id: str
    model_type: str
    total_conversions: int
    total_conversion_value: float
    attributed_conversions: int
    attributed_conversion_value: float
    touchpoint_credits: Dict[str, float]
    confidence_score: float
    calculated_at: str


def get_attribution_engine(request: Request) -> AttributionEngine:
    return request.app.state.attribution_engine


@router.post("/calculate", response_model=AttributionResponse)
async def calculate_attribution(
    request_data: AttributionRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    attribution_engine: AttributionEngine = Depends(get_attribution_engine)
):
    """Calculate attribution for a campaign"""
    try:
        model_type = AttributionModelType(request_data.model_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type: {request_data.model_type}"
        )
    
    start_date = None
    end_date = None
    
    if request_data.start_date:
        start_date = datetime.fromisoformat(request_data.start_date.replace("Z", "+00:00"))
    if request_data.end_date:
        end_date = datetime.fromisoformat(request_data.end_date.replace("Z", "+00:00"))
    
    result = await attribution_engine.calculate_attribution(
        campaign_id=request_data.campaign_id,
        tenant_id=tenant_id,
        model_type=model_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return AttributionResponse(
        campaign_id=result.campaign_id,
        model_type=result.model_type.value if result.model_type else request_data.model_type,
        total_conversions=result.total_conversions,
        total_conversion_value=result.total_conversion_value,
        attributed_conversions=result.attributed_conversions,
        attributed_conversion_value=result.attributed_conversion_value,
        touchpoint_credits=result.touchpoint_credits,
        confidence_score=result.confidence_score,
        calculated_at=result.calculated_at.isoformat()
    )


@router.post("/compare")
async def compare_models(
    campaign_id: str,
    model_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    attribution_engine: AttributionEngine = Depends(get_attribution_engine)
):
    """Compare multiple attribution models"""
    if model_types is None:
        model_types = [mt.value for mt in AttributionModelType]
    
    model_type_enums = []
    for mt in model_types:
        try:
            model_type_enums.append(AttributionModelType(mt))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model type: {mt}")
    
    start_date_dt = None
    end_date_dt = None
    
    if start_date:
        start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        end_date_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    results = await attribution_engine.compare_models(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        model_types=model_type_enums,
        start_date=start_date_dt,
        end_date=end_date_dt
    )
    
    return {
        "campaign_id": campaign_id,
        "comparisons": {
            mt.value: {
                "total_conversions": r.total_conversions,
                "attributed_conversions": r.attributed_conversions,
                "attributed_conversion_value": r.attributed_conversion_value,
                "confidence_score": r.confidence_score
            }
            for mt, r in results.items()
        }
    }

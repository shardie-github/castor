"""
Cost Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from src.cost import CostTracker, CostType
from src.tenants.tenant_isolation import get_current_tenant
from fastapi import Request

router = APIRouter()


class CostAllocationRequest(BaseModel):
    cost_type: str
    service_name: str
    amount: float
    resource_id: Optional[str] = None
    currency: str = "USD"
    unit: Optional[str] = None
    quantity: Optional[float] = None


def get_cost_tracker(request: Request) -> CostTracker:
    return request.app.state.cost_tracker


@router.post("/allocate")
async def allocate_cost(
    request_data: CostAllocationRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    cost_tracker: CostTracker = Depends(get_cost_tracker)
):
    """Allocate cost to tenant"""
    try:
        cost_type = CostType(request_data.cost_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cost type: {request_data.cost_type}")
    
    await cost_tracker.allocate_cost(
        tenant_id=tenant_id,
        cost_type=cost_type,
        service_name=request_data.service_name,
        amount=request_data.amount,
        resource_id=request_data.resource_id,
        currency=request_data.currency,
        unit=request_data.unit,
        quantity=request_data.quantity
    )
    
    return {"status": "success"}


@router.get("/")
async def get_costs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    cost_tracker: CostTracker = Depends(get_cost_tracker)
):
    """Get costs for tenant"""
    start_date_dt = None
    end_date_dt = None
    
    if start_date:
        start_date_dt = date.fromisoformat(start_date)
    if end_date:
        end_date_dt = date.fromisoformat(end_date)
    
    costs = await cost_tracker.get_tenant_costs(
        tenant_id=tenant_id,
        start_date=start_date_dt,
        end_date=end_date_dt
    )
    
    return {
        "costs": [
            {
                "allocation_id": c.allocation_id,
                "date": c.date.isoformat(),
                "cost_type": c.cost_type.value,
                "service_name": c.service_name,
                "amount": c.amount,
                "currency": c.currency
            }
            for c in costs
        ],
        "total": await cost_tracker.get_total_cost(tenant_id, start_date_dt, end_date_dt)
    }

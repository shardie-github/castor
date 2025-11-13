"""
Risk Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from src.operations.risk_management import (
    RiskManager, RiskCategory, RiskStatus, RiskSeverity
)

router = APIRouter(prefix="/api/v1/risks", tags=["risks"])


class RiskCreate(BaseModel):
    tenant_id: Optional[str] = None
    category: RiskCategory
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    impact: int = Field(..., ge=1, le=5)
    probability: int = Field(..., ge=1, le=5)
    owner: str
    mitigation_strategies: List[str] = []
    next_review_date: Optional[datetime] = None
    metadata: Optional[dict] = {}


class RiskUpdate(BaseModel):
    impact: Optional[int] = Field(None, ge=1, le=5)
    probability: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[RiskStatus] = None
    owner: Optional[str] = None
    mitigation_strategies: Optional[List[str]] = None
    next_review_date: Optional[datetime] = None
    metadata: Optional[dict] = None


class MitigationCreate(BaseModel):
    description: str
    mitigation_type: str = "action"
    due_date: Optional[datetime] = None
    owner: Optional[str] = None


class RiskResponse(BaseModel):
    risk_id: str
    tenant_id: Optional[str]
    category: str
    title: str
    description: str
    impact: int
    probability: int
    risk_score: int
    severity: str
    status: str
    owner: str
    mitigation_strategies: List[str]
    next_review_date: datetime
    created_at: datetime
    updated_at: datetime
    metadata: dict

    class Config:
        from_attributes = True


# Dependency injection for RiskManager
def get_risk_manager() -> RiskManager:
    # In production, get from app state
    from src.main import risk_manager
    return risk_manager


@router.post("", response_model=RiskResponse, status_code=201)
async def create_risk(
    risk_data: RiskCreate,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Create a new risk"""
    try:
        risk = await risk_manager.create_risk(
            tenant_id=risk_data.tenant_id,
            category=risk_data.category,
            title=risk_data.title,
            description=risk_data.description,
            impact=risk_data.impact,
            probability=risk_data.probability,
            owner=risk_data.owner,
            mitigation_strategies=risk_data.mitigation_strategies,
            next_review_date=risk_data.next_review_date,
            metadata=risk_data.metadata
        )
        
        return RiskResponse(
            risk_id=risk.risk_id,
            tenant_id=risk.tenant_id,
            category=risk.category.value,
            title=risk.title,
            description=risk.description,
            impact=risk.impact,
            probability=risk.probability,
            risk_score=risk.risk_score,
            severity=risk.severity.value,
            status=risk.status.value,
            owner=risk.owner,
            mitigation_strategies=risk.mitigation_strategies,
            next_review_date=risk.next_review_date,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
            metadata=risk.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: str,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Get a risk by ID"""
    risk = await risk_manager.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    return RiskResponse(
        risk_id=risk.risk_id,
        tenant_id=risk.tenant_id,
        category=risk.category.value,
        title=risk.title,
        description=risk.description,
        impact=risk.impact,
        probability=risk.probability,
        risk_score=risk.risk_score,
        severity=risk.severity.value,
        status=risk.status.value,
        owner=risk.owner,
        mitigation_strategies=risk.mitigation_strategies,
        next_review_date=risk.next_review_date,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
        metadata=risk.metadata
    )


@router.get("", response_model=List[RiskResponse])
async def list_risks(
    tenant_id: Optional[str] = None,
    category: Optional[RiskCategory] = None,
    status: Optional[RiskStatus] = None,
    severity: Optional[RiskSeverity] = None,
    limit: int = 100,
    offset: int = 0,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """List risks with filters"""
    risks = await risk_manager.list_risks(
        tenant_id=tenant_id,
        category=category,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset
    )
    
    return [
        RiskResponse(
            risk_id=risk.risk_id,
            tenant_id=risk.tenant_id,
            category=risk.category.value,
            title=risk.title,
            description=risk.description,
            impact=risk.impact,
            probability=risk.probability,
            risk_score=risk.risk_score,
            severity=risk.severity.value,
            status=risk.status.value,
            owner=risk.owner,
            mitigation_strategies=risk.mitigation_strategies,
            next_review_date=risk.next_review_date,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
            metadata=risk.metadata
        )
        for risk in risks
    ]


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str,
    risk_data: RiskUpdate,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Update a risk"""
    risk = await risk_manager.update_risk(
        risk_id=risk_id,
        impact=risk_data.impact,
        probability=risk_data.probability,
        status=risk_data.status,
        owner=risk_data.owner,
        mitigation_strategies=risk_data.mitigation_strategies,
        next_review_date=risk_data.next_review_date,
        metadata=risk_data.metadata
    )
    
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    return RiskResponse(
        risk_id=risk.risk_id,
        tenant_id=risk.tenant_id,
        category=risk.category.value,
        title=risk.title,
        description=risk.description,
        impact=risk.impact,
        probability=risk.probability,
        risk_score=risk.risk_score,
        severity=risk.severity.value,
        status=risk.status.value,
        owner=risk.owner,
        mitigation_strategies=risk.mitigation_strategies,
        next_review_date=risk.next_review_date,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
        metadata=risk.metadata
    )


@router.post("/{risk_id}/mitigations")
async def add_mitigation(
    risk_id: str,
    mitigation_data: MitigationCreate,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Add a mitigation action to a risk"""
    mitigation_id = await risk_manager.add_mitigation(
        risk_id=risk_id,
        mitigation_description=mitigation_data.description,
        mitigation_type=mitigation_data.mitigation_type,
        due_date=mitigation_data.due_date,
        owner=mitigation_data.owner
    )
    
    return {"mitigation_id": mitigation_id, "status": "created"}


@router.get("/summary/stats")
async def get_risk_summary(
    tenant_id: Optional[str] = None,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Get risk summary statistics"""
    summary = await risk_manager.get_risk_summary(tenant_id=tenant_id)
    return summary


@router.get("/due-for-review")
async def get_risks_due_for_review(
    days_ahead: int = 7,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """Get risks due for review"""
    risks = await risk_manager.get_risks_due_for_review(days_ahead=days_ahead)
    
    return [
        RiskResponse(
            risk_id=risk.risk_id,
            tenant_id=risk.tenant_id,
            category=risk.category.value,
            title=risk.title,
            description=risk.description,
            impact=risk.impact,
            probability=risk.probability,
            risk_score=risk.risk_score,
            severity=risk.severity.value,
            status=risk.status.value,
            owner=risk.owner,
            mitigation_strategies=risk.mitigation_strategies,
            next_review_date=risk.next_review_date,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
            metadata=risk.metadata
        )
        for risk in risks
    ]

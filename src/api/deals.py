"""
DELTA:20251113_064143 Deal Pipeline API Routes

Deal pipeline stage management endpoints (extends campaigns table).
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deals", tags=["deals"])


class UpdateStageRequest(BaseModel):
    """DELTA:20251113_064143 Update deal stage request"""
    stage: str  # lead, qualified, proposal, negotiation, won, lost


class CampaignResponse(BaseModel):
    """DELTA:20251113_064143 Campaign response with stage"""
    campaign_id: str
    name: str
    status: str
    stage: str
    stage_changed_at: Optional[str]


def get_postgres_conn(request: Request) -> PostgresConnection:
    """DELTA:20251113_064143 Get PostgreSQL connection"""
    return request.app.state.postgres_conn


def get_event_logger(request: Request) -> EventLogger:
    """DELTA:20251113_064143 Get event logger"""
    return request.app.state.event_logger


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if deal pipeline is enabled"""
    return os.getenv("ENABLE_DEAL_PIPELINE", "false").lower() == "true"


VALID_STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost']


@router.patch("/{campaign_id}/stage", response_model=CampaignResponse)
async def update_deal_stage(
    campaign_id: str,
    request_data: UpdateStageRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """DELTA:20251113_064143 Update deal pipeline stage"""
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="Deal pipeline is disabled. Set ENABLE_DEAL_PIPELINE=true to enable."
        )
    
    # Validate stage
    if request_data.stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {VALID_STAGES}"
        )
    
    try:
        # Get current stage
        current_query = """
            SELECT stage FROM campaigns
            WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
        """
        current_row = await postgres_conn.fetchrow(current_query, campaign_id, tenant_id)
        
        if not current_row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        current_stage = current_row['stage'] or 'lead'
        
        # Update stage
        update_query = """
            UPDATE campaigns
            SET stage = $1,
                stage_changed_at = NOW(),
                updated_at = NOW()
            WHERE campaign_id = $2::uuid AND tenant_id = $3::uuid
            RETURNING campaign_id, name, status, stage, stage_changed_at;
        """
        
        row = await postgres_conn.fetchrow(
            update_query,
            request_data.stage,
            campaign_id,
            tenant_id
        )
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to update stage")
        
        # Emit event
        await event_logger.log_event(
            event_type='deal.stage_changed',
            user_id=None,
            properties={
                'campaign_id': campaign_id,
                'from': current_stage,
                'to': request_data.stage
            }
        )
        
        return CampaignResponse(
            campaign_id=str(row['campaign_id']),
            name=row['name'],
            status=row['status'],
            stage=row['stage'],
            stage_changed_at=row['stage_changed_at'].isoformat() if row['stage_changed_at'] else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deal stage update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update stage: {str(e)}")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_deal(
    campaign_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get deal with stage"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Deal pipeline is disabled")
    
    query = """
        SELECT campaign_id, name, status, stage, stage_changed_at
        FROM campaigns
        WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
    """
    
    row = await postgres_conn.fetchrow(query, campaign_id, tenant_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignResponse(
        campaign_id=str(row['campaign_id']),
        name=row['name'],
        status=row['status'],
        stage=row['stage'] or 'lead',
        stage_changed_at=row['stage_changed_at'].isoformat() if row['stage_changed_at'] else None
    )

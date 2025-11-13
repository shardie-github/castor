"""
DELTA:20251113T114706Z Orchestration API Routes

API endpoints for workflow orchestration, intelligent automation, and optimization.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orchestration", tags=["orchestration"])


class WorkflowExecutionResponse(BaseModel):
    """DELTA:20251113T114706Z Workflow execution response"""
    execution_id: str
    workflow_id: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]


class AutomationDecisionResponse(BaseModel):
    """DELTA:20251113T114706Z Automation decision response"""
    action: str
    confidence: float
    reasoning: Dict[str, Any]


def get_workflow_engine(request: Request):
    """DELTA:20251113T114706Z Get workflow engine"""
    return request.app.state.workflow_engine


def get_intelligent_automation(request: Request):
    """DELTA:20251113T114706Z Get intelligent automation engine"""
    return request.app.state.intelligent_automation


def get_smart_scheduler(request: Request):
    """DELTA:20251113T114706Z Get smart scheduler"""
    return request.app.state.smart_scheduler


def get_auto_optimizer(request: Request):
    """DELTA:20251113T114706Z Get auto optimizer"""
    return request.app.state.auto_optimizer


def get_predictive_automation(request: Request):
    """DELTA:20251113T114706Z Get predictive automation"""
    return request.app.state.predictive_automation


def check_feature_flag() -> bool:
    """DELTA:20251113T114706Z Check if orchestration is enabled"""
    return os.getenv("ENABLE_ORCHESTRATION", "false").lower() == "true"


@router.post("/workflows/{workflow_id}/start")
async def start_workflow(
    workflow_id: str,
    context: Dict[str, Any],
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    workflow_engine = Depends(get_workflow_engine)
):
    """DELTA:20251113T114706Z Start a workflow execution"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        context['tenant_id'] = tenant_id
        execution_id = await workflow_engine.start_workflow(workflow_id, context)
        
        return {
            'execution_id': execution_id,
            'workflow_id': workflow_id,
            'status': 'started'
        }
    except Exception as e:
        logger.error(f"Workflow start failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{execution_id}/status")
async def get_workflow_status(
    execution_id: str,
    request: Request = None,
    workflow_engine = Depends(get_workflow_engine)
):
    """DELTA:20251113T114706Z Get workflow execution status"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    execution = await workflow_engine.get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return WorkflowExecutionResponse(
        execution_id=execution.execution_id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None
    )


@router.post("/automation/deals/{campaign_id}/evaluate")
async def evaluate_deal_automation(
    campaign_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    intelligent_automation = Depends(get_intelligent_automation)
):
    """DELTA:20251113T114706Z Evaluate deal for automation"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        # Get current stage
        from src.database import PostgresConnection
        postgres_conn: PostgresConnection = request.app.state.postgres_conn
        
        query = """
            SELECT stage FROM campaigns
            WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
        """
        row = await postgres_conn.fetchrow(query, campaign_id, tenant_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        decision = await intelligent_automation.evaluate_deal_auto_progression(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            current_stage=row['stage'] or 'lead'
        )
        
        return AutomationDecisionResponse(
            action=decision.get('action'),
            confidence=decision.get('confidence', 0),
            reasoning=decision.get('reasoning', {})
        )
    except Exception as e:
        logger.error(f"Deal automation evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/campaigns/{campaign_id}/optimize")
async def optimize_campaign(
    campaign_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    auto_optimizer = Depends(get_auto_optimizer)
):
    """DELTA:20251113T114706Z Optimize campaign"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        result = await auto_optimizer.optimize_campaign(campaign_id, tenant_id)
        return result
    except Exception as e:
        logger.error(f"Campaign optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/matchmaking/optimize")
async def optimize_matchmaking(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    auto_optimizer = Depends(get_auto_optimizer)
):
    """DELTA:20251113T114706Z Optimize matchmaking algorithm"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        result = await auto_optimizer.optimize_matchmaking(tenant_id)
        return result
    except Exception as e:
        logger.error(f"Matchmaking optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictive/deals/predict-and-automate")
async def predict_and_automate_deals(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    lookahead_days: int = Query(30, ge=1, le=90),
    predictive_automation = Depends(get_predictive_automation)
):
    """DELTA:20251113T114706Z Predict deal outcomes and trigger automation"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        result = await predictive_automation.predict_and_automate_deals(
            tenant_id=tenant_id,
            lookahead_days=lookahead_days
        )
        return result
    except Exception as e:
        logger.error(f"Predictive automation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/schedule")
async def schedule_job(
    job_id: str,
    priority: Optional[str] = Query(None),
    context: Optional[Dict[str, Any]] = None,
    request: Request = None,
    smart_scheduler = Depends(get_smart_scheduler)
):
    """DELTA:20251113T114706Z Schedule a job for execution"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Orchestration is disabled")
    
    try:
        from src.orchestration.smart_scheduler import JobPriority
        
        job_priority = JobPriority[priority.upper()] if priority else None
        execution_id = await smart_scheduler.schedule_job(
            job_id=job_id,
            priority=job_priority,
            context=context or {}
        )
        
        return {
            'execution_id': execution_id,
            'job_id': job_id,
            'status': 'scheduled'
        }
    except Exception as e:
        logger.error(f"Job scheduling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

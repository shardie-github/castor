"""
DELTA:20251113_064143 Automation API Routes

Endpoints for triggering automation jobs.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import Request
from pydantic import BaseModel
from typing import Optional

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.agents.automation_jobs import AutomationJobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


def get_postgres_conn(request: Request) -> PostgresConnection:
    """DELTA:20251113_064143 Get PostgreSQL connection"""
    return request.app.state.postgres_conn


def get_automation_jobs(request: Request) -> AutomationJobs:
    """DELTA:20251113_064143 Get automation jobs instance"""
    return AutomationJobs(
        postgres_conn=request.app.state.postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if automation is enabled"""
    return os.getenv("ENABLE_AUTOMATION_JOBS", "false").lower() == "true"


@router.post("/etl-health-check")
async def trigger_etl_health_check(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    automation_jobs: AutomationJobs = Depends(get_automation_jobs)
):
    """DELTA:20251113_064143 Trigger ETL health check"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Automation jobs are disabled")
    
    result = await automation_jobs.check_etl_health(tenant_id)
    return result


@router.post("/recalculate-matches")
async def trigger_matchmaking_recalculation(
    advertiser_id: Optional[str] = None,
    podcast_id: Optional[str] = None,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    automation_jobs: AutomationJobs = Depends(get_automation_jobs),
    background_tasks: BackgroundTasks = None
):
    """DELTA:20251113_064143 Trigger matchmaking recalculation"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Automation jobs are disabled")
    
    # Run in background if no specific IDs (expensive operation)
    if not advertiser_id and not podcast_id:
        background_tasks.add_task(
            automation_jobs.recalculate_matches,
            tenant_id=tenant_id
        )
        return {
            'status': 'queued',
            'message': 'Matchmaking recalculation queued for background processing'
        }
    
    result = await automation_jobs.recalculate_matches(
        advertiser_id=advertiser_id,
        podcast_id=podcast_id,
        tenant_id=tenant_id
    )
    return result


@router.post("/refresh-metrics-daily")
async def trigger_metrics_refresh(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    automation_jobs: AutomationJobs = Depends(get_automation_jobs)
):
    """DELTA:20251113_064143 Trigger metrics_daily refresh"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Automation jobs are disabled")
    
    result = await automation_jobs.refresh_metrics_daily()
    return result


@router.post("/pipeline-alerts")
async def trigger_pipeline_alerts_check(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    automation_jobs: AutomationJobs = Depends(get_automation_jobs)
):
    """DELTA:20251113_064143 Check deal pipeline alerts"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Automation jobs are disabled")
    
    result = await automation_jobs.check_deal_pipeline_alerts(tenant_id)
    return result


@router.post("/run-all")
async def trigger_all_jobs(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    automation_jobs: AutomationJobs = Depends(get_automation_jobs),
    background_tasks: BackgroundTasks = None
):
    """DELTA:20251113_064143 Run all scheduled automation jobs"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Automation jobs are disabled")
    
    # Run in background
    background_tasks.add_task(
        automation_jobs.run_scheduled_jobs,
        tenant_id=tenant_id
    )
    
    return {
        'status': 'queued',
        'message': 'All automation jobs queued for background processing'
    }

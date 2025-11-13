"""
DELTA:20251113_064143 Monetization API Routes

Endpoints for:
- Agency/Consultancy management
- Affiliate marketing
- AI token billing
- White-labeling
- API usage tracking
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional, List

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.monetization.agency_manager import AgencyManager
from src.monetization.affiliate_manager import AffiliateManager
from src.monetization.ai_token_manager import AITokenManager
from src.monetization.api_usage_tracker import APIUsageTracker
from src.monetization.white_label_manager import WhiteLabelManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monetization", tags=["monetization"])


def get_postgres_conn(request: Request) -> PostgresConnection:
    """DELTA:20251113_064143 Get PostgreSQL connection"""
    return request.app.state.postgres_conn


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if monetization is enabled"""
    return os.getenv("ENABLE_MONETIZATION", "false").lower() == "true"


# Agency endpoints
class CreateAgencyRequest(BaseModel):
    name: str
    slug: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    commission_rate_percent: float = 0.0


@router.post("/agencies")
async def create_agency(
    request_data: CreateAgencyRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Create agency"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AgencyManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    agency_id = await manager.create_agency(
        tenant_id=tenant_id,
        name=request_data.name,
        slug=request_data.slug,
        contact_email=request_data.contact_email,
        contact_phone=request_data.contact_phone,
        commission_rate_percent=request_data.commission_rate_percent
    )
    
    return {'agency_id': agency_id}


@router.get("/agencies")
async def list_agencies(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    status: Optional[str] = Query(None)
):
    """DELTA:20251113_064143 List agencies"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AgencyManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    agencies = await manager.list_agencies(tenant_id, status)
    return {'agencies': agencies}


# Affiliate endpoints
class CreateAffiliateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    agency_id: Optional[str] = None
    commission_rate_percent: float = 10.0


@router.post("/affiliates")
async def create_affiliate(
    request_data: CreateAffiliateRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Create affiliate"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AffiliateManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    result = await manager.create_affiliate(
        tenant_id=tenant_id,
        name=request_data.name,
        email=request_data.email,
        agency_id=request_data.agency_id,
        commission_rate_percent=request_data.commission_rate_percent
    )
    
    return result


@router.post("/affiliates/track")
async def track_referral(
    referral_code: str = Query(...),
    referred_tenant_id: Optional[str] = Query(None),
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Track referral"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AffiliateManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    referral_id = await manager.track_referral(
        tenant_id=tenant_id,
        referral_code=referral_code,
        referred_tenant_id=referred_tenant_id
    )
    
    return {'referral_id': referral_id}


@router.get("/affiliates/{affiliate_id}/stats")
async def get_affiliate_stats(
    affiliate_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get affiliate statistics"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AffiliateManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    stats = await manager.get_affiliate_stats(affiliate_id, tenant_id)
    return stats


# AI Token endpoints
class PurchaseTokensRequest(BaseModel):
    tokens_to_purchase: int
    transaction_id: Optional[str] = None


@router.post("/ai-tokens/purchase")
async def purchase_tokens(
    request_data: PurchaseTokensRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Purchase AI tokens"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AITokenManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    result = await manager.purchase_tokens(
        tenant_id=tenant_id,
        tokens_to_purchase=request_data.tokens_to_purchase,
        transaction_id=request_data.transaction_id
    )
    
    return result


@router.get("/ai-tokens/balance")
async def get_token_balance(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get AI token balance"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AITokenManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    balance = await manager.get_balance(tenant_id)
    return balance


@router.get("/ai-tokens/usage")
async def get_token_usage(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    limit: int = Query(100, ge=1, le=1000)
):
    """DELTA:20251113_064143 Get AI token usage history"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = AITokenManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    usage = await manager.get_usage_history(tenant_id, limit)
    return {'usage': usage}


# API Usage endpoints
@router.get("/api-usage/summary")
async def get_api_usage_summary(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get API usage summary"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    tracker = APIUsageTracker(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    summary = await tracker.get_usage_summary(tenant_id)
    return summary


@router.get("/api-usage/rate-limit")
async def check_rate_limit(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    limit_per_hour: int = Query(1000, ge=1)
):
    """DELTA:20251113_064143 Check API rate limit"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    tracker = APIUsageTracker(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    result = await tracker.check_rate_limit(tenant_id, limit_per_hour)
    return result


# White Label endpoints
class UpdateWhiteLabelRequest(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    custom_css: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    support_email: Optional[str] = None
    support_url: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/white-label")
async def get_white_label_settings(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get white label settings"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = WhiteLabelManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    settings = await manager.get_settings(tenant_id)
    return settings or {}


@router.put("/white-label")
async def update_white_label_settings(
    request_data: UpdateWhiteLabelRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Update white label settings"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Monetization is disabled")
    
    manager = WhiteLabelManager(
        postgres_conn=postgres_conn,
        metrics_collector=request.app.state.metrics_collector,
        event_logger=request.app.state.event_logger
    )
    
    settings = await manager.update_settings(
        tenant_id=tenant_id,
        brand_name=request_data.brand_name,
        logo_url=request_data.logo_url,
        primary_color=request_data.primary_color,
        secondary_color=request_data.secondary_color,
        custom_domain=request_data.custom_domain,
        custom_css=request_data.custom_css,
        email_from_name=request_data.email_from_name,
        email_from_address=request_data.email_from_address,
        support_email=request_data.support_email,
        support_url=request_data.support_url,
        enabled=request_data.enabled
    )
    
    return settings

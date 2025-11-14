"""
DELTA:20251113_064143 IO Bookings API Routes

Insertion order (IO) booking management endpoints.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/io", tags=["io"])


class IOBookingRequest(BaseModel):
    """DELTA:20251113_064143 IO booking request"""
    campaign_id: str
    ad_unit_id: Optional[str] = None
    episode_id: Optional[str] = None
    flight_start: str  # ISO format
    flight_end: str  # ISO format
    booked_impressions: Optional[int] = None
    booked_cpm_cents: Optional[int] = None
    promo_code: Optional[str] = None
    vanity_url: Optional[str] = None


class IOBookingResponse(BaseModel):
    """DELTA:20251113_064143 IO booking response"""
    io_id: str
    campaign_id: str
    ad_unit_id: Optional[str]
    episode_id: Optional[str]
    flight_start: str
    flight_end: str
    booked_impressions: Optional[int]
    booked_cpm_cents: Optional[int]
    promo_code: Optional[str]
    vanity_url: Optional[str]
    status: str


def get_postgres_conn(request: Request) -> PostgresConnection:
    """DELTA:20251113_064143 Get PostgreSQL connection"""
    return request.app.state.postgres_conn


def get_event_logger(request: Request) -> EventLogger:
    """DELTA:20251113_064143 Get event logger"""
    return request.app.state.event_logger


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if IO bookings are enabled"""
    return os.getenv("ENABLE_IO_BOOKINGS", "false").lower() == "true"


def generate_promo_code(campaign_id: str) -> str:
    """DELTA:20251113_064143 Generate promo code (simple implementation)"""
    import random
    import string
    # Simple implementation: PODCAST + random 6 chars
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PODCAST{random_chars}"


def generate_vanity_url(campaign_id: str, promo_code: str) -> str:
    """DELTA:20251113_064143 Generate vanity URL (simple implementation)"""
    base_url = os.getenv("VANITY_URL_BASE", "https://track.example.com")
    return f"{base_url}/{promo_code.lower()}"


@router.post("", response_model=IOBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_io_booking(
    request_data: IOBookingRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """DELTA:20251113_064143 Create IO booking"""
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="IO bookings are disabled. Set ENABLE_IO_BOOKINGS=true to enable."
        )
    
    try:
        # Parse dates
        flight_start = datetime.fromisoformat(request_data.flight_start.replace("Z", "+00:00"))
        flight_end = datetime.fromisoformat(request_data.flight_end.replace("Z", "+00:00"))
        
        # Generate promo code and vanity URL if not provided
        promo_code = request_data.promo_code or generate_promo_code(request_data.campaign_id)
        vanity_url = request_data.vanity_url or generate_vanity_url(request_data.campaign_id, promo_code)
        
        # Insert IO booking
        query = """
            INSERT INTO io_bookings (
                tenant_id, campaign_id, ad_unit_id, episode_id,
                flight_start, flight_end, booked_impressions, booked_cpm_cents,
                promo_code, vanity_url, status
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6, $7, $8, $9, $10, 'scheduled')
            RETURNING io_id, campaign_id, ad_unit_id, episode_id, flight_start, flight_end,
                      booked_impressions, booked_cpm_cents, promo_code, vanity_url, status;
        """
        
        row = await postgres_conn.fetchrow(
            query,
            tenant_id,
            request_data.campaign_id,
            request_data.ad_unit_id,
            request_data.episode_id,
            flight_start,
            flight_end,
            request_data.booked_impressions,
            request_data.booked_cpm_cents,
            promo_code,
            vanity_url
        )
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create IO booking")
        
        # Emit event
        await event_logger.log_event(
            event_type='io.scheduled',
            user_id=None,
            properties={
                'io_id': str(row['io_id']),
                'campaign_id': request_data.campaign_id,
                'episode_id': request_data.episode_id,
                'flight_start': request_data.flight_start,
                'flight_end': request_data.flight_end
            }
        )
        
        return IOBookingResponse(
            io_id=str(row['io_id']),
            campaign_id=str(row['campaign_id']),
            ad_unit_id=str(row['ad_unit_id']) if row['ad_unit_id'] else None,
            episode_id=str(row['episode_id']) if row['episode_id'] else None,
            flight_start=row['flight_start'].isoformat(),
            flight_end=row['flight_end'].isoformat(),
            booked_impressions=row['booked_impressions'],
            booked_cpm_cents=row['booked_cpm_cents'],
            promo_code=row['promo_code'],
            vanity_url=row['vanity_url'],
            status=row['status']
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"IO booking creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create IO booking: {str(e)}")


@router.get("/{io_id}", response_model=IOBookingResponse)
async def get_io_booking(
    io_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get IO booking"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="IO bookings are disabled")
    
    query = """
        SELECT io_id, campaign_id, ad_unit_id, episode_id, flight_start, flight_end,
               booked_impressions, booked_cpm_cents, promo_code, vanity_url, status
        FROM io_bookings
        WHERE io_id = $1::uuid AND tenant_id = $2::uuid;
    """
    
    row = await postgres_conn.fetchrow(query, io_id, tenant_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="IO booking not found")
    
    return IOBookingResponse(
        io_id=str(row['io_id']),
        campaign_id=str(row['campaign_id']),
        ad_unit_id=str(row['ad_unit_id']) if row['ad_unit_id'] else None,
        episode_id=str(row['episode_id']) if row['episode_id'] else None,
        flight_start=row['flight_start'].isoformat(),
        flight_end=row['flight_end'].isoformat(),
        booked_impressions=row['booked_impressions'],
        booked_cpm_cents=row['booked_cpm_cents'],
        promo_code=row['promo_code'],
        vanity_url=row['vanity_url'],
        status=row['status']
    )


class UpdateIOStatusRequest(BaseModel):
    """DELTA:20251113T114706Z Update IO status request"""
    status: str  # scheduled, active, completed, cancelled, makegood


@router.patch("/{io_id}/status", response_model=IOBookingResponse)
async def update_io_status(
    io_id: str,
    request_data: UpdateIOStatusRequest,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """DELTA:20251113T114706Z Update IO booking status"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="IO bookings are disabled")
    
    # Validate status
    valid_statuses = ['scheduled', 'active', 'completed', 'cancelled', 'makegood']
    if request_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    try:
        # Get current status
        current_query = """
            SELECT status FROM io_bookings
            WHERE io_id = $1::uuid AND tenant_id = $2::uuid;
        """
        current_row = await postgres_conn.fetchrow(current_query, io_id, tenant_id)
        
        if not current_row:
            raise HTTPException(status_code=404, detail="IO booking not found")
        
        current_status = current_row['status']
        
        # Update status
        update_query = """
            UPDATE io_bookings
            SET status = $1,
                updated_at = NOW()
            WHERE io_id = $2::uuid AND tenant_id = $3::uuid
            RETURNING io_id, campaign_id, ad_unit_id, episode_id, flight_start, flight_end,
                      booked_impressions, booked_cpm_cents, promo_code, vanity_url, status;
        """
        
        row = await postgres_conn.fetchrow(
            update_query,
            request_data.status,
            io_id,
            tenant_id
        )
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to update IO status")
        
        # Emit event based on status change
        if request_data.status == 'completed' and current_status != 'completed':
            # DELTA:20251113T114706Z Emit io.delivered event when IO completes
            await event_logger.log_event(
                event_type='io.delivered',
                user_id=None,
                properties={
                    'io_id': str(row['io_id']),
                    'campaign_id': str(row['campaign_id']),
                    'episode_id': str(row['episode_id']) if row['episode_id'] else None,
                    'flight_start': row['flight_start'].isoformat(),
                    'flight_end': row['flight_end'].isoformat(),
                    'booked_impressions': row['booked_impressions'],
                    'from_status': current_status,
                    'to_status': request_data.status
                }
            )
        else:
            # Emit generic status change event
            await event_logger.log_event(
                event_type='io.status_changed',
                user_id=None,
                properties={
                    'io_id': str(row['io_id']),
                    'campaign_id': str(row['campaign_id']),
                    'from_status': current_status,
                    'to_status': request_data.status
                }
            )
        
        return IOBookingResponse(
            io_id=str(row['io_id']),
            campaign_id=str(row['campaign_id']),
            ad_unit_id=str(row['ad_unit_id']) if row['ad_unit_id'] else None,
            episode_id=str(row['episode_id']) if row['episode_id'] else None,
            flight_start=row['flight_start'].isoformat(),
            flight_end=row['flight_end'].isoformat(),
            booked_impressions=row['booked_impressions'],
            booked_cpm_cents=row['booked_cpm_cents'],
            promo_code=row['promo_code'],
            vanity_url=row['vanity_url'],
            status=row['status']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IO status update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update IO status: {str(e)}")


@router.get("/{io_id}/export/pdf")
async def export_io_pdf(
    io_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """DELTA:20251113_064143 Export IO booking as PDF"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="IO bookings are disabled")
    
    try:
        # Get IO booking with campaign details
        query = """
            SELECT 
                io.io_id, io.campaign_id, io.ad_unit_id, io.episode_id,
                io.flight_start, io.flight_end, io.booked_impressions, io.booked_cpm_cents,
                io.promo_code, io.vanity_url, io.status,
                c.campaign_name, c.campaign_value,
                p.title as podcast_title,
                e.title as episode_title
            FROM io_bookings io
            LEFT JOIN campaigns c ON c.campaign_id = io.campaign_id
            LEFT JOIN podcasts p ON p.podcast_id = c.podcast_id
            LEFT JOIN episodes e ON e.episode_id = io.episode_id
            WHERE io.io_id = $1::uuid AND io.tenant_id = $2::uuid;
        """
        
        row = await postgres_conn.fetchrow(query, io_id, tenant_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="IO booking not found")
        
        # Use existing report generator
        from src.reporting.report_generator import ReportGenerator, ReportFormat
        
        report_gen = ReportGenerator(
            metrics_collector=request.app.state.metrics_collector,
            event_logger=event_logger
        )
        
        # Generate IO-specific report data
        io_data = {
            "io_id": str(row['io_id']),
            "campaign_name": row['campaign_name'],
            "podcast_title": row['podcast_title'],
            "episode_title": row['episode_title'],
            "flight_start": row['flight_start'].isoformat(),
            "flight_end": row['flight_end'].isoformat(),
            "booked_impressions": row['booked_impressions'],
            "booked_cpm_cents": row['booked_cpm_cents'],
            "promo_code": row['promo_code'],
            "vanity_url": row['vanity_url'],
            "status": row['status'],
            "campaign_value": float(row['campaign_value'] or 0)
        }
        
        # Generate PDF (simplified - in production would use proper PDF library)
        # For now, return JSON representation that can be converted to PDF client-side
        # or use a PDF generation service
        
        # Log event
        await event_logger.log_event(
            event_type='io.pdf_exported',
            user_id=None,
            properties={
                'io_id': str(row['io_id']),
                'campaign_id': str(row['campaign_id'])
            }
        )
        
        # Return PDF data (in production, would return actual PDF file)
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "io_id": str(row['io_id']),
            "pdf_url": f"/api/v1/io/{io_id}/pdf/download",  # Placeholder
            "data": io_data,
            "note": "PDF generation requires PDF library. This endpoint returns structured data."
        })
    
    except Exception as e:
        logger.error(f"IO PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export IO PDF: {str(e)}")

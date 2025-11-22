"""
Reports API Routes

Provides endpoints for report generation and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user
from src.reporting.report_generator import ReportGenerator, ReportType, ReportFormat

router = APIRouter()


# Pydantic Models
class ReportGenerateRequest(BaseModel):
    campaign_id: str
    report_type: str = "sponsor_report"
    format: str = "pdf"
    template_id: Optional[str] = None
    include_roi: bool = True
    include_attribution: bool = True
    include_benchmarks: bool = False
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReportResponse(BaseModel):
    report_id: str
    campaign_id: str
    template_id: Optional[str]
    report_type: str
    format: str
    generated_at: datetime
    file_size_bytes: Optional[int]
    file_url: Optional[str]
    includes_roi: bool
    includes_attribution: bool


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


def get_report_generator(
    metrics: MetricsCollector = Depends(get_metrics_collector),
    event_logger: EventLogger = Depends(get_event_logger)
) -> ReportGenerator:
    """Get report generator instance"""
    return ReportGenerator(
        metrics_collector=metrics,
        event_logger=event_logger
    )


# API Endpoints
@router.post("/reports/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    report_data: ReportGenerateRequest,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    report_generator: ReportGenerator = Depends(get_report_generator),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Generate a new report"""
    # Verify campaign belongs to user
    campaign = await postgres_conn.fetchrow(
        """
        SELECT c.campaign_id FROM campaigns c
        JOIN podcasts p ON c.podcast_id = p.podcast_id
        WHERE c.campaign_id = $1 AND p.user_id = $2
        """,
        report_data.campaign_id,
        current_user['user_id']
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Generate report
    try:
        report_type = ReportType(report_data.report_type)
        report_format = ReportFormat(report_data.format)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type or format: {str(e)}"
        )
    
    # Get dependencies for report generation
    from src.analytics.analytics_store import AnalyticsStore
    from src.analytics.roi_calculator import ROICalculator
    from src.database import TimescaleConnection
    
    timescale_conn = request.app.state.timescale_conn if hasattr(request.app.state, 'timescale_conn') else None
    analytics_store = AnalyticsStore(
        metrics_collector=request.app.state.metrics_collector,
        timescale_conn=timescale_conn,
        postgres_conn=postgres_conn
    )
    
    roi_calculator = ROICalculator(
        metrics_collector=request.app.state.metrics_collector,
        event_logger=event_logger
    )
    
    report = await report_generator.generate_report(
        campaign_id=report_data.campaign_id,
        report_type=report_type,
        format=report_format,
        template_id=report_data.template_id,
        include_roi=report_data.include_roi,
        include_attribution=report_data.include_attribution,
        include_benchmarks=report_data.include_benchmarks,
        start_date=report_data.start_date,
        end_date=report_data.end_date,
        postgres_conn=postgres_conn,
        analytics_store=analytics_store,
        roi_calculator=roi_calculator
    )
    
    # Store report metadata in database
    query = """
        INSERT INTO reports (
            report_id, campaign_id, user_id, report_type, format,
            template_id, generated_at, file_size_bytes, file_url,
            includes_roi, includes_attribution, metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING report_id
    """
    
    await postgres_conn.execute(
        query,
        report.report_id,
        report.campaign_id,
        current_user['user_id'],
        report.report_type.value,
        report.format.value,
        report.template_id,
        report.generated_at,
        report.file_size_bytes,
        report.file_url,
        report.includes_roi,
        report.includes_attribution,
        report.metadata
    )
    
    await event_logger.log_event(
        event_type='report.generated',
        user_id=str(current_user['user_id']),
        properties={
            'report_id': report.report_id,
            'campaign_id': report.campaign_id,
            'report_type': report.report_type.value,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    # Update campaign status to 'completed' when report is generated
    try:
        await postgres_conn.execute(
            """
            UPDATE campaigns 
            SET status = 'completed', updated_at = NOW()
            WHERE campaign_id = $1
            """,
            report.campaign_id
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to update campaign status: {e}")
    
    return ReportResponse(
        report_id=report.report_id,
        campaign_id=report.campaign_id,
        template_id=report.template_id,
        report_type=report.report_type.value,
        format=report.format.value,
        generated_at=report.generated_at,
        file_size_bytes=report.file_size_bytes,
        file_url=report.file_url,
        includes_roi=report.includes_roi,
        includes_attribution=report.includes_attribution
    )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Download a generated report"""
    # Verify ownership
    report = await postgres_conn.fetchrow(
        """
        SELECT file_url, format FROM reports
        WHERE report_id = $1 AND user_id = $2
        """,
        report_id,
        current_user['user_id']
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    file_url = report.get('file_url')
    if not file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not available"
        )
    
    # In production, would serve from S3 or similar
    import os
    reports_dir = os.getenv("REPORTS_STORAGE_PATH", "/tmp/reports")
    file_path = os.path.join(reports_dir, os.path.basename(file_url))
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on server"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type="application/pdf" if report['format'] == 'pdf' else "application/octet-stream",
        filename=os.path.basename(file_path)
    )


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    campaign_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    skip: int = 0,
    limit: int = 100
):
    """List reports for the current user"""
    if campaign_id:
        query = """
            SELECT r.report_id, r.campaign_id, r.template_id, r.report_type,
                   r.format, r.generated_at, r.file_size_bytes, r.file_url,
                   r.includes_roi, r.includes_attribution
            FROM reports r
            WHERE r.campaign_id = $1 AND r.user_id = $2
            ORDER BY r.generated_at DESC
            LIMIT $3 OFFSET $4
        """
        results = await postgres_conn.fetch(query, campaign_id, current_user['user_id'], limit, skip)
    else:
        query = """
            SELECT r.report_id, r.campaign_id, r.template_id, r.report_type,
                   r.format, r.generated_at, r.file_size_bytes, r.file_url,
                   r.includes_roi, r.includes_attribution
            FROM reports r
            WHERE r.user_id = $1
            ORDER BY r.generated_at DESC
            LIMIT $2 OFFSET $3
        """
        results = await postgres_conn.fetch(query, current_user['user_id'], limit, skip)
    
    return [ReportResponse(**dict(row)) for row in results]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get a specific report"""
    query = """
        SELECT report_id, campaign_id, template_id, report_type, format,
               generated_at, file_size_bytes, file_url, includes_roi,
               includes_attribution
        FROM reports
        WHERE report_id = $1 AND user_id = $2
    """
    
    result = await postgres_conn.fetchrow(query, report_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportResponse(**dict(result))


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Download a report file"""
    query = """
        SELECT file_url, format FROM reports
        WHERE report_id = $1 AND user_id = $2
    """
    
    result = await postgres_conn.fetchrow(query, report_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if not result['file_url']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not available"
        )
    
    # In production, this would stream the file from storage
    # For now, return redirect to file URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=result['file_url'])


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Delete a report"""
    query = "DELETE FROM reports WHERE report_id = $1 AND user_id = $2 RETURNING report_id"
    result = await postgres_conn.fetchrow(query, report_id, current_user['user_id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    await event_logger.log_event(
        event_type='report.deleted',
        user_id=str(current_user['user_id']),
        properties={'report_id': report_id}
    )
    
    return None

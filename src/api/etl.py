"""
DELTA:20251113_064143 ETL API Routes

CSV upload and import endpoints for manual data ingestion.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi import Request
from pydantic import BaseModel
from typing import Optional, List

from src.etl.csv_importer import CSVImporter
from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/etl", tags=["etl"])


class ImportStatusResponse(BaseModel):
    """DELTA:20251113_064143 Import status response"""
    import_id: str
    status: str
    records_imported: int
    records_failed: int
    error_message: Optional[str] = None


class ImportHistoryResponse(BaseModel):
    """DELTA:20251113_064143 Import history response"""
    imports: List[ImportStatusResponse]


def get_csv_importer(request: Request) -> CSVImporter:
    """DELTA:20251113_064143 Get CSV importer service"""
    postgres_conn: PostgresConnection = request.app.state.postgres_conn
    metrics_collector: MetricsCollector = request.app.state.metrics_collector
    event_logger: EventLogger = request.app.state.event_logger
    
    return CSVImporter(
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if ETL CSV upload is enabled"""
    return os.getenv("ENABLE_ETL_CSV_UPLOAD", "false").lower() == "true"


@router.post("/upload", response_model=ImportStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    file: UploadFile = File(...),
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    importer: CSVImporter = Depends(get_csv_importer)
):
    """
    DELTA:20251113_064143 Upload and import CSV file
    
    CSV format: day,episode_id,source,downloads,listeners,completion_rate,ctr,conversions,revenue_cents
    """
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="ETL CSV upload is disabled. Set ENABLE_ETL_CSV_UPLOAD=true to enable."
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    import_id = None
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Track import start
        import_id = await importer.track_import(
            tenant_id=tenant_id,
            source='csv',
            file_name=file.filename,
            status='processing',
            records_imported=0,
            records_failed=0
        )
        
        # Parse and validate CSV
        rows = await importer.parse_csv(csv_content)
        
        # Import to database
        result = await importer.import_to_listener_metrics(
            rows=rows,
            tenant_id=tenant_id,
            import_id=import_id
        )
        
        # Update import status
        await importer.update_import_status(
            import_id=import_id,
            status='completed',
            records_imported=result['imported'],
            records_failed=result['failed']
        )
        
        # Emit event
        await request.app.state.event_logger.log_event(
            event_type='etl.import_completed',
            user_id=None,  # System event
            properties={
                'import_id': import_id,
                'source': 'csv',
                'file_name': file.filename,
                'records_imported': result['imported'],
                'records_failed': result['failed']
            }
        )
        
        return ImportStatusResponse(
            import_id=import_id,
            status='completed',
            records_imported=result['imported'],
            records_failed=result['failed']
        )
        
    except ValueError as e:
        # Validation error
        error_msg = str(e)
        if import_id:
            await importer.update_import_status(
                import_id=import_id,
                status='failed',
                records_imported=0,
                records_failed=0,
                error_message=error_msg
            )
        
        # Emit error event
        await request.app.state.event_logger.log_event(
            event_type='etl.error',
            user_id=None,
            properties={
                'import_id': import_id or 'unknown',
                'source': 'csv',
                'file_name': file.filename,
                'error': error_msg
            }
        )
        
        raise HTTPException(
            status_code=400,
            detail=f"CSV validation error: {error_msg}"
        )
    
    except Exception as e:
        # Unexpected error
        error_msg = str(e)
        logger.error(f"ETL import failed: {error_msg}", exc_info=True)
        
        if import_id:
            await importer.update_import_status(
                import_id=import_id,
                status='failed',
                records_imported=0,
                records_failed=0,
                error_message=error_msg
            )
        
        # Emit error event
        await request.app.state.event_logger.log_event(
            event_type='etl.error',
            user_id=None,
            properties={
                'import_id': import_id or 'unknown',
                'source': 'csv',
                'file_name': file.filename,
                'error': error_msg
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {error_msg}"
        )


@router.get("/status/{import_id}", response_model=ImportStatusResponse)
async def get_import_status(
    import_id: str,
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    importer: CSVImporter = Depends(get_csv_importer)
):
    """DELTA:20251113_064143 Get import status"""
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="ETL CSV upload is disabled"
        )
    
    query = """
        SELECT import_id, status, records_imported, records_failed, error_message
        FROM etl_imports
        WHERE import_id = $1::uuid AND tenant_id = $2::uuid;
    """
    
    row = await importer.postgres_conn.fetchrow(query, import_id, tenant_id)
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Import not found"
        )
    
    return ImportStatusResponse(
        import_id=str(row['import_id']),
        status=row['status'],
        records_imported=row['records_imported'],
        records_failed=row['records_failed'],
        error_message=row['error_message']
    )


@router.get("/history", response_model=ImportHistoryResponse)
async def get_import_history(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    importer: CSVImporter = Depends(get_csv_importer),
    limit: int = 50
):
    """DELTA:20251113_064143 Get import history"""
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="ETL CSV upload is disabled"
        )
    
    query = """
        SELECT import_id, status, records_imported, records_failed, error_message
        FROM etl_imports
        WHERE tenant_id = $1::uuid
        ORDER BY started_at DESC
        LIMIT $2;
    """
    
    rows = await importer.postgres_conn.fetch(query, tenant_id, limit)
    
    imports = [
        ImportStatusResponse(
            import_id=str(row['import_id']),
            status=row['status'],
            records_imported=row['records_imported'],
            records_failed=row['records_failed'],
            error_message=row['error_message']
        )
        for row in rows
    ]
    
    return ImportHistoryResponse(imports=imports)

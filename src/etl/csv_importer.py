"""
DELTA:20251113_064143 CSV Importer Module

Handles CSV file parsing, validation, and import into listener_metrics table.
"""

import logging
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class MetricsDailyRow(BaseModel):
    """DELTA:20251113_064143 CSV row schema for metrics_daily"""
    day: str = Field(..., description="Date in YYYY-MM-DD format")
    episode_id: str = Field(..., description="Episode UUID")
    source: str = Field(..., description="Source platform (e.g., 'spotify', 'apple')")
    downloads: Optional[int] = Field(None, ge=0)
    listeners: Optional[int] = Field(None, ge=0)
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    ctr: Optional[float] = Field(None, ge=0.0, le=1.0, description="Click-through rate")
    conversions: Optional[int] = Field(None, ge=0)
    revenue_cents: Optional[int] = Field(None, ge=0)

    @validator('day')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('day must be in YYYY-MM-DD format')

    @validator('episode_id')
    def validate_uuid(cls, v):
        """Validate UUID format"""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('episode_id must be a valid UUID')


class CSVImporter:
    """
    DELTA:20251113_064143 CSV Importer
    
    Parses and validates CSV files, then imports into listener_metrics table.
    """
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def parse_csv(self, csv_content: str) -> List[MetricsDailyRow]:
        """
        Parse CSV content and validate rows
        
        Args:
            csv_content: CSV file content as string
            
        Returns:
            List of validated MetricsDailyRow objects
            
        Raises:
            ValueError: If CSV is invalid or rows fail validation
        """
        rows = []
        errors = []
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Validate header
        expected_headers = ['day', 'episode_id', 'source', 'downloads', 'listeners', 
                          'completion_rate', 'ctr', 'conversions', 'revenue_cents']
        if reader.fieldnames != expected_headers:
            raise ValueError(
                f"Invalid CSV header. Expected: {expected_headers}, "
                f"Got: {reader.fieldnames}"
            )
        
        # Validate and parse rows
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Convert empty strings to None for optional fields
                parsed_row = {}
                for key, value in row.items():
                    if value == '' or value is None:
                        parsed_row[key] = None
                    elif key in ['downloads', 'listeners', 'conversions', 'revenue_cents']:
                        parsed_row[key] = int(value) if value else None
                    elif key in ['completion_rate', 'ctr']:
                        parsed_row[key] = float(value) if value else None
                    else:
                        parsed_row[key] = value
                
                validated_row = MetricsDailyRow(**parsed_row)
                rows.append(validated_row)
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if errors:
            raise ValueError(f"CSV validation errors:\n" + "\n".join(errors))
        
        return rows
    
    async def import_to_listener_metrics(
        self,
        rows: List[MetricsDailyRow],
        tenant_id: str,
        import_id: str
    ) -> Dict[str, int]:
        """
        Import validated rows into listener_metrics table
        
        Args:
            rows: List of validated MetricsDailyRow objects
            tenant_id: Tenant ID for multi-tenant isolation
            import_id: Import ID for tracking
            
        Returns:
            Dict with 'imported' and 'failed' counts
        """
        imported = 0
        failed = 0
        
        for row in rows:
            try:
                # Convert day string to timestamp (start of day UTC)
                day_dt = datetime.strptime(row.day, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                
                # Insert into listener_metrics (hypertable)
                # Using upsert logic: if (day, episode_id, source) exists, update; else insert
                query = """
                    INSERT INTO listener_metrics (
                        timestamp, podcast_id, episode_id, tenant_id,
                        metric_type, value, platform, metadata
                    )
                    SELECT 
                        $1::timestamptz,
                        (SELECT podcast_id FROM episodes WHERE episode_id = $2::uuid),
                        $2::uuid,
                        $3::uuid,
                        'daily_aggregate',
                        COALESCE($4, 0)::numeric, -- downloads as primary value
                        $5,
                        jsonb_build_object(
                            'import_id', $6,
                            'listeners', $7,
                            'completion_rate', $8,
                            'ctr', $9,
                            'conversions', $10,
                            'revenue_cents', $11
                        )
                    ON CONFLICT DO NOTHING
                    RETURNING 1;
                """
                
                # Note: listener_metrics doesn't have unique constraint on (timestamp, episode_id, source)
                # So we use DO NOTHING to avoid duplicates, or we could use a more sophisticated upsert
                # For now, we'll insert and let the application handle deduplication
                
                # Simplified insert (without conflict handling for now)
                query = """
                    INSERT INTO listener_metrics (
                        timestamp, episode_id, tenant_id,
                        metric_type, value, platform, metadata
                    )
                    VALUES (
                        $1::timestamptz,
                        $2::uuid,
                        $3::uuid,
                        'daily_aggregate',
                        COALESCE($4, 0)::numeric,
                        $5,
                        jsonb_build_object(
                            'import_id', $6,
                            'listeners', $7,
                            'completion_rate', $8,
                            'ctr', $9,
                            'conversions', $10,
                            'revenue_cents', $11,
                            'source', $5
                        )
                    );
                """
                
                await self.postgres_conn.execute(
                    query,
                    day_dt,
                    row.episode_id,
                    tenant_id,
                    row.downloads,
                    row.source,
                    import_id,
                    row.listeners,
                    row.completion_rate,
                    row.ctr,
                    row.conversions,
                    row.revenue_cents
                )
                
                imported += 1
            except Exception as e:
                logger.error(f"Failed to import row {row.day}/{row.episode_id}: {e}")
                failed += 1
        
        return {'imported': imported, 'failed': failed}
    
    async def track_import(
        self,
        tenant_id: str,
        source: str,
        file_name: Optional[str],
        status: str,
        records_imported: int,
        records_failed: int,
        error_message: Optional[str] = None
    ) -> str:
        """
        Track import in etl_imports table
        
        Returns:
            Import ID (UUID)
        """
        import uuid
        
        import_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO etl_imports (
                import_id, tenant_id, source, file_name, status,
                records_imported, records_failed, error_message,
                started_at, completed_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, NOW(), 
                    CASE WHEN $5 IN ('completed', 'failed') THEN NOW() ELSE NULL END)
            RETURNING import_id;
        """
        
        await self.postgres_conn.execute(
            query,
            import_id,
            tenant_id,
            source,
            file_name,
            status,
            records_imported,
            records_failed,
            error_message
        )
        
        return import_id
    
    async def update_import_status(
        self,
        import_id: str,
        status: str,
        records_imported: int,
        records_failed: int,
        error_message: Optional[str] = None
    ):
        """Update import status"""
        query = """
            UPDATE etl_imports
            SET status = $1,
                records_imported = $2,
                records_failed = $3,
                error_message = $4,
                completed_at = CASE WHEN $1 IN ('completed', 'failed') THEN NOW() ELSE NULL END
            WHERE import_id = $5::uuid;
        """
        
        await self.postgres_conn.execute(
            query,
            status,
            records_imported,
            records_failed,
            error_message,
            import_id
        )

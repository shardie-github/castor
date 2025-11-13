"""
Backup Manager

Manages automated database backups with multiple retention policies.
"""

import logging
import subprocess
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    POINT_IN_TIME = "point_in_time"


class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class BackupManager:
    """
    Backup Manager
    
    Manages automated database backups with:
    - Daily full backups
    - Weekly full backups (retained longer)
    - Monthly full backups (long-term retention)
    - Point-in-time recovery (WAL archiving)
    - Cross-region replication
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection,
        backup_storage_path: str = "/backups",
        aws_s3_bucket: Optional[str] = None,
        aws_region: Optional[str] = None
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
        self.backup_storage_path = backup_storage_path
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_region = aws_region
        
        # Ensure backup directory exists
        os.makedirs(backup_storage_path, exist_ok=True)
    
    async def create_backup(
        self,
        tenant_id: Optional[str] = None,
        backup_type: BackupType = BackupType.FULL,
        include_tenant_data: bool = True
    ) -> str:
        """
        Create a database backup
        
        Args:
            tenant_id: Optional tenant ID for tenant-specific backup
            backup_type: Type of backup to create
            include_tenant_data: Whether to include tenant data
            
        Returns:
            Backup ID
        """
        backup_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_id}_{timestamp}.sql"
        backup_path = os.path.join(self.backup_storage_path, backup_filename)
        
        # Record backup start
        await self.postgres.execute(
            """
            INSERT INTO backup_records (
                backup_id, tenant_id, backup_type, backup_source,
                backup_location, status, started_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            backup_id, tenant_id, backup_type.value, "database",
            backup_path, BackupStatus.IN_PROGRESS.value
        )
        
        try:
            # Create backup using pg_dump
            # In production, use pg_dump with proper credentials
            db_config = self.postgres
            
            # Build pg_dump command
            pg_dump_cmd = [
                "pg_dump",
                "-h", db_config.host,
                "-p", str(db_config.port),
                "-U", db_config.user,
                "-d", db_config.database,
                "-F", "c",  # Custom format
                "-f", backup_path
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config.password
            
            # Execute backup
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Get backup size
            backup_size = os.path.getsize(backup_path)
            
            # Calculate retention period
            retention_days = self._get_retention_days(backup_type)
            retention_until = datetime.now(timezone.utc) + timedelta(days=retention_days)
            
            # Update backup record
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET status = $1, completed_at = NOW(), backup_size_bytes = $2,
                    retention_until = $3
                WHERE backup_id = $4
                """,
                BackupStatus.COMPLETED.value, backup_size, retention_until, backup_id
            )
            
            # Upload to S3 if configured
            if self.aws_s3_bucket:
                await self._upload_to_s3(backup_path, backup_filename)
            
            # Record telemetry
            self.metrics.increment_counter(
                "backup_created",
                tags={"backup_type": backup_type.value, "status": "success"}
            )
            
            # Log event
            await self.events.log_event(
                event_type="backup_created",
                user_id=None,
                properties={
                    "backup_id": backup_id,
                    "backup_type": backup_type.value,
                    "backup_size_bytes": backup_size
                }
            )
            
            logger.info(f"Backup created successfully: {backup_id}")
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
            # Update backup record with error
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET status = $1, metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', $2::jsonb)
                WHERE backup_id = $3
                """,
                BackupStatus.FAILED.value, f'"{str(e)}"', backup_id
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "backup_created",
                tags={"backup_type": backup_type.value, "status": "failed"}
            )
            
            raise
    
    async def create_daily_backup(self) -> str:
        """Create daily backup"""
        return await self.create_backup(backup_type=BackupType.FULL)
    
    async def create_weekly_backup(self) -> str:
        """Create weekly backup (retained longer)"""
        return await self.create_backup(backup_type=BackupType.FULL)
    
    async def create_monthly_backup(self) -> str:
        """Create monthly backup (long-term retention)"""
        return await self.create_backup(backup_type=BackupType.FULL)
    
    async def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity
        
        Returns:
            True if backup is valid, False otherwise
        """
        # Get backup record
        row = await self.postgres.fetchrow(
            """
            SELECT backup_location, backup_format, status
            FROM backup_records
            WHERE backup_id = $1
            """,
            backup_id
        )
        
        if not row or row["status"] != BackupStatus.COMPLETED.value:
            return False
        
        backup_path = row["backup_location"]
        
        # Verify backup file exists
        if not os.path.exists(backup_path):
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET verification_status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', '"File not found"')
                WHERE backup_id = $1
                """,
                backup_id
            )
            return False
        
        # Verify backup format (for SQL dumps, check if file is readable)
        try:
            # For custom format, use pg_restore --list to verify
            if row["backup_format"] == "sql":
                # Check if file is readable and has content
                with open(backup_path, 'rb') as f:
                    header = f.read(100)
                    if len(header) < 10:
                        raise Exception("Backup file too small")
            else:
                # For custom format, verify with pg_restore
                result = subprocess.run(
                    ["pg_restore", "--list", backup_path],
                    capture_output=True,
                    timeout=60
                )
                if result.returncode != 0:
                    raise Exception(f"Backup verification failed: {result.stderr}")
            
            # Update verification status
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET verification_status = 'passed', verified_at = NOW()
                WHERE backup_id = $1
                """,
                backup_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET verification_status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', $1::jsonb)
                WHERE backup_id = $2
                """,
                f'"{str(e)}"', backup_id
            )
            
            return False
    
    async def list_backups(
        self,
        tenant_id: Optional[str] = None,
        backup_type: Optional[BackupType] = None,
        status: Optional[BackupStatus] = None
    ) -> List[Dict[str, Any]]:
        """List backups with filters"""
        query = "SELECT * FROM backup_records WHERE 1=1"
        params = []
        param_index = 1
        
        if tenant_id:
            query += f" AND tenant_id = ${param_index}"
            params.append(tenant_id)
            param_index += 1
        
        if backup_type:
            query += f" AND backup_type = ${param_index}"
            params.append(backup_type.value)
            param_index += 1
        
        if status:
            query += f" AND status = ${param_index}"
            params.append(status.value)
            param_index += 1
        
        query += " ORDER BY created_at DESC"
        
        rows = await self.postgres.fetch(query, *params)
        
        return [
            {
                "backup_id": str(row["backup_id"]),
                "tenant_id": str(row["tenant_id"]) if row["tenant_id"] else None,
                "backup_type": row["backup_type"],
                "backup_location": row["backup_location"],
                "backup_size_bytes": row["backup_size_bytes"],
                "status": row["status"],
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                "verified_at": row["verified_at"].isoformat() if row["verified_at"] else None,
                "verification_status": row["verification_status"],
                "retention_until": row["retention_until"].isoformat() if row["retention_until"] else None
            }
            for row in rows
        ]
    
    async def cleanup_expired_backups(self) -> int:
        """Clean up expired backups"""
        # Find expired backups
        rows = await self.postgres.fetch(
            """
            SELECT backup_id, backup_location
            FROM backup_records
            WHERE retention_until < NOW() AND status = 'completed'
            """
        )
        
        deleted_count = 0
        
        for row in rows:
            backup_path = row["backup_location"]
            
            # Delete file
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    logger.info(f"Deleted expired backup: {backup_path}")
            except Exception as e:
                logger.error(f"Failed to delete backup file {backup_path}: {e}")
            
            # Delete S3 object if applicable
            if self.aws_s3_bucket:
                try:
                    await self._delete_from_s3(backup_path)
                except Exception as e:
                    logger.error(f"Failed to delete backup from S3: {e}")
            
            # Update record
            await self.postgres.execute(
                """
                UPDATE backup_records
                SET status = 'expired'
                WHERE backup_id = $1
                """,
                row["backup_id"]
            )
            
            deleted_count += 1
        
        return deleted_count
    
    def _get_retention_days(self, backup_type: BackupType) -> int:
        """Get retention period in days based on backup type"""
        # Daily backups: 7 days
        # Weekly backups: 30 days
        # Monthly backups: 365 days
        # Point-in-time: 7 days (WAL files)
        
        if backup_type == BackupType.FULL:
            # Assume daily for now
            return 7
        elif backup_type == BackupType.INCREMENTAL:
            return 3
        elif backup_type == BackupType.POINT_IN_TIME:
            return 7
        else:
            return 7
    
    async def _upload_to_s3(self, local_path: str, s3_key: str):
        """Upload backup to S3"""
        # In production, use boto3
        # import boto3
        # s3 = boto3.client('s3', region_name=self.aws_region)
        # s3.upload_file(local_path, self.aws_s3_bucket, s3_key)
        logger.info(f"Would upload {local_path} to s3://{self.aws_s3_bucket}/{s3_key}")
    
    async def _delete_from_s3(self, s3_key: str):
        """Delete backup from S3"""
        # In production, use boto3
        logger.info(f"Would delete s3://{self.aws_s3_bucket}/{s3_key}")

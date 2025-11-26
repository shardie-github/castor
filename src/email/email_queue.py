"""
Email Queue System

Handles asynchronous email sending with queue management, retries, and error handling.
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from uuid import uuid4

from src.database import PostgresConnection
from src.email.email_service import EmailService, EmailTemplate
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class EmailStatus(Enum):
    """Email queue status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueuedEmail:
    """Email queue item"""
    email_id: str
    to_email: str
    template: EmailTemplate
    context: Dict
    subject: Optional[str] = None
    body: Optional[str] = None
    status: EmailStatus = EmailStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class EmailQueue:
    """
    Email Queue Manager
    
    Manages email queue with:
    - Database-backed queue
    - Retry logic
    - Priority handling
    - Batch processing
    """
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        email_service: EmailService,
        metrics_collector: Optional[MetricsCollector] = None,
        event_logger: Optional[EventLogger] = None,
        batch_size: int = 10,
        processing_interval: int = 5
    ):
        self.postgres_conn = postgres_conn
        self.email_service = email_service
        self.metrics = metrics_collector
        self.events = event_logger
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def initialize_queue_table(self):
        """Initialize email queue table if it doesn't exist"""
        query = """
            CREATE TABLE IF NOT EXISTS email_queue (
                email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                to_email VARCHAR(255) NOT NULL,
                template VARCHAR(50) NOT NULL,
                context JSONB NOT NULL,
                subject VARCHAR(500),
                body TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                priority INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                processed_at TIMESTAMP,
                error_message TEXT,
                scheduled_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status, scheduled_at);
            CREATE INDEX IF NOT EXISTS idx_email_queue_priority ON email_queue(priority DESC, created_at);
        """
        await self.postgres_conn.execute(query)
    
    async def enqueue(
        self,
        to_email: str,
        template: EmailTemplate,
        context: Dict,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        priority: int = 0,
        scheduled_at: Optional[datetime] = None
    ) -> str:
        """Add email to queue"""
        email_id = str(uuid4())
        
        if scheduled_at is None:
            scheduled_at = datetime.utcnow()
        
        query = """
            INSERT INTO email_queue (
                email_id, to_email, template, context, subject, body,
                status, priority, scheduled_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING email_id
        """
        
        result = await self.postgres_conn.fetchval(
            query,
            email_id,
            to_email,
            template.value,
            context,
            subject,
            body,
            EmailStatus.PENDING.value,
            priority,
            scheduled_at
        )
        
        if self.metrics:
            self.metrics.increment_counter(
                "emails_queued_total",
                tags={"template": template.value}
            )
        
        logger.info(f"Email queued: {email_id} to {to_email}")
        return result
    
    async def process_queue(self):
        """Process emails from queue"""
        while self._running:
            try:
                # Get pending emails ordered by priority and creation time
                query = """
                    SELECT email_id, to_email, template, context, subject, body,
                           retry_count, max_retries, status
                    FROM email_queue
                    WHERE status IN ('pending', 'retrying')
                      AND scheduled_at <= NOW()
                    ORDER BY priority DESC, created_at ASC
                    LIMIT $1
                    FOR UPDATE SKIP LOCKED
                """
                
                emails = await self.postgres_conn.fetch(query, self.batch_size)
                
                if not emails:
                    await asyncio.sleep(self.processing_interval)
                    continue
                
                for email_row in emails:
                    await self._process_email(email_row)
                
                await asyncio.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"Error processing email queue: {str(e)}")
                await asyncio.sleep(self.processing_interval)
    
    async def _process_email(self, email_row: dict):
        """Process a single email"""
        email_id = email_row['email_id']
        
        try:
            # Update status to processing
            await self.postgres_conn.execute(
                "UPDATE email_queue SET status = $1 WHERE email_id = $2",
                EmailStatus.PROCESSING.value,
                email_id
            )
            
            # Send email
            template = EmailTemplate(email_row['template'])
            success = await self.email_service.send_email(
                to_email=email_row['to_email'],
                template=template,
                context=email_row['context'],
                subject=email_row.get('subject'),
                body=email_row.get('body')
            )
            
            if success:
                # Mark as sent
                await self.postgres_conn.execute(
                    """
                    UPDATE email_queue 
                    SET status = $1, processed_at = NOW()
                    WHERE email_id = $2
                    """,
                    EmailStatus.SENT.value,
                    email_id
                )
                
                if self.metrics:
                    self.metrics.increment_counter(
                        "emails_sent_total",
                        tags={"template": template.value, "status": "success"}
                    )
            else:
                # Handle failure
                await self._handle_failure(email_id, email_row, "Email send failed")
                
        except Exception as e:
            logger.error(f"Error processing email {email_id}: {str(e)}")
            await self._handle_failure(email_id, email_row, str(e))
    
    async def _handle_failure(self, email_id: str, email_row: dict, error_message: str):
        """Handle email sending failure"""
        retry_count = email_row['retry_count'] + 1
        max_retries = email_row['max_retries']
        
        if retry_count < max_retries:
            # Retry with exponential backoff
            retry_delay = min(300, 60 * (2 ** retry_count))  # Max 5 minutes
            scheduled_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            await self.postgres_conn.execute(
                """
                UPDATE email_queue 
                SET status = $1, retry_count = $2, error_message = $3,
                    scheduled_at = $4
                WHERE email_id = $5
                """,
                EmailStatus.RETRYING.value,
                retry_count,
                error_message,
                scheduled_at,
                email_id
            )
            
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_retry_total",
                    tags={"template": email_row['template'], "retry_count": str(retry_count)}
                )
        else:
            # Mark as failed
            await self.postgres_conn.execute(
                """
                UPDATE email_queue 
                SET status = $1, processed_at = NOW(), error_message = $2
                WHERE email_id = $3
                """,
                EmailStatus.FAILED.value,
                error_message,
                email_id
            )
            
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_failed_total",
                    tags={"template": email_row['template']}
                )
    
    async def start(self):
        """Start queue processor"""
        await self.initialize_queue_table()
        self._running = True
        self._task = asyncio.create_task(self.process_queue())
        logger.info("Email queue processor started")
    
    async def stop(self):
        """Stop queue processor"""
        self._running = False
        if self._task:
            await self._task
        logger.info("Email queue processor stopped")
    
    async def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        query = """
            SELECT 
                status,
                COUNT(*) as count
            FROM email_queue
            GROUP BY status
        """
        
        results = await self.postgres_conn.fetch(query)
        
        stats = {
            "pending": 0,
            "processing": 0,
            "sent": 0,
            "failed": 0,
            "retrying": 0
        }
        
        for row in results:
            stats[row['status']] = row['count']
        
        return stats

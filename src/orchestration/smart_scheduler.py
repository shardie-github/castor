"""
DELTA:20251113T114706Z Smart Job Scheduler

Intelligent job scheduling with priority management, dependency resolution,
and resource-aware execution.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from heapq import heappush, heappop

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    """Scheduled job definition"""
    job_id: str
    name: str
    handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    schedule: str  # Cron expression or 'immediate'
    priority: JobPriority = JobPriority.NORMAL
    depends_on: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: Optional[int] = None
    resource_requirements: Dict[str, int] = field(default_factory=dict)  # e.g., {'cpu': 1, 'memory_mb': 512}
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


@dataclass
class JobExecution:
    """Job execution instance"""
    execution_id: str
    job_id: str
    status: JobStatus
    priority: JobPriority
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None


class SmartScheduler:
    """
    DELTA:20251113T114706Z Smart Job Scheduler
    
    Features:
    - Priority-based execution
    - Dependency resolution
    - Resource-aware scheduling
    - Retry logic
    - Timeout handling
    - Concurrent execution limits
    """
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        max_concurrent_jobs: int = 10
    ):
        self.postgres = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
        self.max_concurrent = max_concurrent_jobs
        
        # Job registry
        self._jobs: Dict[str, ScheduledJob] = {}
        
        # Execution queue (priority queue)
        self._queue: List[tuple] = []  # (priority_value, execution_id, execution)
        self._executions: Dict[str, JobExecution] = {}
        self._running_executions: Dict[str, JobExecution] = {}
        
        # Resource tracking
        self._available_resources = {
            'cpu': 100,  # Percentage
            'memory_mb': 8192,  # MB
            'concurrent_jobs': max_concurrent_jobs
        }
        self._used_resources = {
            'cpu': 0,
            'memory_mb': 0,
            'concurrent_jobs': 0
        }
        
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    def register_job(self, job: ScheduledJob):
        """Register a scheduled job"""
        self._jobs[job.job_id] = job
        
        # Calculate next run time
        if job.schedule == 'immediate':
            job.next_run = datetime.now(timezone.utc)
        else:
            # Parse cron expression and calculate next run
            job.next_run = self._parse_cron_next_run(job.schedule)
        
        logger.info(f"Registered job: {job.name} (next run: {job.next_run})")
    
    async def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Smart scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Smart scheduler stopped")
    
    async def schedule_job(
        self,
        job_id: str,
        priority: Optional[JobPriority] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule a job for immediate execution"""
        job = self._jobs.get(job_id)
        if not job or not job.enabled:
            raise ValueError(f"Job {job_id} not found or disabled")
        
        execution_id = str(uuid4())
        execution = JobExecution(
            execution_id=execution_id,
            job_id=job_id,
            status=JobStatus.QUEUED,
            priority=priority or job.priority
        )
        
        self._executions[execution_id] = execution
        
        # Add to priority queue
        priority_value = execution.priority.value
        heappush(self._queue, (priority_value, execution_id, execution, context or {}))
        
        logger.info(f"Scheduled job {job_id} with execution {execution_id}")
        
        return execution_id
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Check for scheduled jobs
                await self._check_scheduled_jobs()
                
                # Process queue
                await self._process_queue()
                
                # Wait before next iteration
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _check_scheduled_jobs(self):
        """Check if any scheduled jobs are due"""
        now = datetime.now(timezone.utc)
        
        for job in self._jobs.values():
            if not job.enabled:
                continue
            
            if job.next_run and job.next_run <= now:
                # Schedule job for execution
                await self.schedule_job(job.job_id)
                
                # Calculate next run time
                if job.schedule != 'immediate':
                    job.last_run = now
                    job.next_run = self._parse_cron_next_run(job.schedule)
    
    async def _process_queue(self):
        """Process jobs from queue"""
        while self._queue and len(self._running_executions) < self.max_concurrent:
            # Get highest priority job
            priority_value, execution_id, execution, context = heappop(self._queue)
            
            # Check dependencies
            job = self._jobs[execution.job_id]
            if not self._check_dependencies(job, execution_id):
                # Re-queue with lower priority (will be checked again)
                heappush(self._queue, (priority_value + 1, execution_id, execution, context))
                continue
            
            # Check resource availability
            if not self._check_resources(job):
                # Re-queue
                heappush(self._queue, (priority_value, execution_id, execution, context))
                continue
            
            # Execute job
            asyncio.create_task(self._execute_job(execution, job, context))
    
    async def _execute_job(
        self,
        execution: JobExecution,
        job: ScheduledJob,
        context: Dict[str, Any]
    ):
        """Execute a job"""
        execution.status = JobStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        self._running_executions[execution.execution_id] = execution
        
        # Allocate resources
        self._allocate_resources(job)
        
        try:
            # Execute with timeout if specified
            if job.timeout:
                result = await asyncio.wait_for(
                    job.handler(context),
                    timeout=job.timeout
                )
            else:
                result = await job.handler(context)
            
            execution.status = JobStatus.COMPLETED
            execution.result = result
            execution.completed_at = datetime.now(timezone.utc)
            
            # Record metrics
            duration = (execution.completed_at - execution.started_at).total_seconds()
            self.metrics.record_histogram(
                'job_execution_duration_seconds',
                duration,
                tags={'job_id': job.job_id, 'status': 'completed'}
            )
            
            # Log event
            await self.events.log_event(
                event_type='job.completed',
                user_id=None,
                properties={
                    'execution_id': execution.execution_id,
                    'job_id': job.job_id,
                    'duration_seconds': duration
                }
            )
        
        except asyncio.TimeoutError:
            execution.status = JobStatus.FAILED
            execution.error_message = f"Job timed out after {job.timeout}s"
            logger.error(f"Job {job.job_id} timed out")
        
        except Exception as e:
            execution.status = JobStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}", exc_info=True)
            
            # Retry logic
            if execution.execution_id not in [e.execution_id for e in self._executions.values() if e.job_id == job.job_id]:
                retry_count = sum(
                    1 for e in self._executions.values()
                    if e.job_id == job.job_id and e.status == JobStatus.FAILED
                )
                
                if retry_count < job.max_retries:
                    # Re-queue with lower priority
                    execution.status = JobStatus.QUEUED
                    heappush(self._queue, (job.priority.value + 1, execution.execution_id, execution, context))
        
        finally:
            # Release resources
            self._release_resources(job)
            self._running_executions.pop(execution.execution_id, None)
    
    def _check_dependencies(self, job: ScheduledJob, execution_id: str) -> bool:
        """Check if job dependencies are satisfied"""
        for dep_job_id in job.depends_on:
            # Check if dependency job has completed
            dep_executions = [
                e for e in self._executions.values()
                if e.job_id == dep_job_id and e.status == JobStatus.COMPLETED
            ]
            
            if not dep_executions:
                return False
        
        return True
    
    def _check_resources(self, job: ScheduledJob) -> bool:
        """Check if required resources are available"""
        for resource, required in job.resource_requirements.items():
            available = self._available_resources.get(resource, 0) - self._used_resources.get(resource, 0)
            if available < required:
                return False
        return True
    
    def _allocate_resources(self, job: ScheduledJob):
        """Allocate resources for job"""
        for resource, amount in job.resource_requirements.items():
            self._used_resources[resource] = self._used_resources.get(resource, 0) + amount
    
    def _release_resources(self, job: ScheduledJob):
        """Release resources after job completion"""
        for resource, amount in job.resource_requirements.items():
            self._used_resources[resource] = max(0, self._used_resources.get(resource, 0) - amount)
    
    def _parse_cron_next_run(self, cron_expr: str) -> datetime:
        """Parse cron expression and calculate next run time"""
        # Simplified cron parser - in production, use library like croniter
        # For now, support simple formats:
        # - "daily" -> next day at 2 AM
        # - "hourly" -> next hour
        # - "*/5 * * * *" -> every 5 minutes
        
        now = datetime.now(timezone.utc)
        
        if cron_expr == "daily":
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif cron_expr == "hourly":
            next_run = now.replace(minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
            return next_run
        
        elif cron_expr.startswith("*/"):
            # Simple interval (e.g., "*/5" = every 5 minutes)
            interval = int(cron_expr.split("/")[1].split()[0])
            next_run = now.replace(second=0, microsecond=0)
            next_run = next_run.replace(minute=(next_run.minute // interval + 1) * interval)
            if next_run.minute >= 60:
                next_run = next_run.replace(hour=next_run.hour + 1, minute=0)
            return next_run
        
        else:
            # Default: run in 1 hour
            return now + timedelta(hours=1)
    
    async def get_job_status(self, execution_id: str) -> Optional[JobExecution]:
        """Get job execution status"""
        return self._executions.get(execution_id)
    
    async def cancel_job(self, execution_id: str):
        """Cancel a queued or running job"""
        execution = self._executions.get(execution_id)
        if execution:
            if execution.status == JobStatus.RUNNING:
                # Mark as cancelled (actual cancellation depends on job implementation)
                execution.status = JobStatus.CANCELLED
            elif execution.status == JobStatus.QUEUED:
                execution.status = JobStatus.CANCELLED
                # Remove from queue
                self._queue = [(p, eid, e, ctx) for p, eid, e, ctx in self._queue if eid != execution_id]

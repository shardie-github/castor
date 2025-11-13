"""
Team Automation Features

Automated task scheduling, workflow automation, and team efficiency tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import uuid
import asyncio

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScheduledTask:
    """Scheduled task data model"""
    task_id: str
    task_name: str
    task_type: str
    schedule_cron: Optional[str] = None
    schedule_interval_seconds: Optional[int] = None
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict = None
    created_at: datetime = None
    updated_at: datetime = None


class TaskScheduler:
    """Manages scheduled tasks and automation"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a task handler"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered task handler for type: {task_type}")
    
    async def create_task(
        self,
        task_name: str,
        task_type: str,
        schedule_cron: Optional[str] = None,
        schedule_interval_seconds: Optional[int] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
        metadata: Optional[Dict] = None
    ) -> ScheduledTask:
        """Create a scheduled task"""
        task_id = str(uuid.uuid4())
        
        # Calculate next run time
        next_run_at = None
        if schedule_interval_seconds:
            next_run_at = datetime.utcnow() + timedelta(seconds=schedule_interval_seconds)
        elif schedule_cron:
            # In production, use croniter to calculate next run
            next_run_at = datetime.utcnow() + timedelta(hours=1)  # Placeholder
        
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            schedule_cron=schedule_cron,
            schedule_interval_seconds=schedule_interval_seconds,
            next_run_at=next_run_at,
            status=TaskStatus.SCHEDULED,
            priority=priority,
            max_retries=max_retries,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self._save_task(task)
        
        self.metrics_collector.increment_counter("tasks_created_total", {
            "task_type": task_type,
            "priority": priority.value
        })
        
        return task
    
    async def execute_task(self, task_id: str) -> bool:
        """Execute a task"""
        task = await self.get_task(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        if task.task_type not in self.task_handlers:
            logger.error(f"No handler registered for task type: {task.task_type}")
            return False
        
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.utcnow()
        await self._save_task(task)
        
        try:
            handler = self.task_handlers[task.task_type]
            await handler(task)
            
            task.status = TaskStatus.COMPLETED
            task.last_run_at = datetime.utcnow()
            task.retry_count = 0
            task.error_message = None
            
            # Calculate next run time
            if task.schedule_interval_seconds:
                task.next_run_at = datetime.utcnow() + timedelta(seconds=task.schedule_interval_seconds)
            
            await self._save_task(task)
            
            self.metrics_collector.increment_counter("tasks_completed_total", {
                "task_type": task.task_type
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Task execution failed: {task_id}", exc_info=e)
            
            task.retry_count += 1
            task.error_message = str(e)
            
            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.FAILED
            else:
                task.status = TaskStatus.PENDING
                # Exponential backoff
                backoff_seconds = 60 * (2 ** task.retry_count)
                task.next_run_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            
            task.updated_at = datetime.utcnow()
            await self._save_task(task)
            
            self.metrics_collector.increment_counter("tasks_failed_total", {
                "task_type": task.task_type
            })
            
            return False
    
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID"""
        query = "SELECT * FROM scheduled_tasks WHERE task_id = $1"
        row = await self.postgres_conn.fetch_one(query, task_id)
        if not row:
            return None
        return self._row_to_task(row)
    
    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScheduledTask]:
        """List tasks"""
        conditions = []
        params = []
        param_idx = 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if task_type:
            conditions.append(f"task_type = ${param_idx}")
            params.append(task_type)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM scheduled_tasks
            WHERE {where_clause}
            ORDER BY priority DESC, next_run_at ASC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        params.extend([limit, offset])
        rows = await self.postgres_conn.fetch_all(query, *params)
        return [self._row_to_task(row) for row in rows]
    
    async def get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due to run"""
        query = """
            SELECT * FROM scheduled_tasks
            WHERE status IN ('scheduled', 'pending')
            AND next_run_at <= NOW()
            ORDER BY priority DESC, next_run_at ASC
        """
        
        rows = await self.postgres_conn.fetch_all(query)
        return [self._row_to_task(row) for row in rows]
    
    async def start_scheduler(self):
        """Start the task scheduler"""
        if self.running:
            return
        
        self.running = True
        logger.info("Task scheduler started")
        
        while self.running:
            try:
                due_tasks = await self.get_due_tasks()
                
                for task in due_tasks:
                    asyncio.create_task(self.execute_task(task.task_id))
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in task scheduler loop", exc_info=e)
                await asyncio.sleep(60)
    
    async def stop_scheduler(self):
        """Stop the task scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    async def _save_task(self, task: ScheduledTask):
        """Save task to database"""
        query = """
            INSERT INTO scheduled_tasks (
                task_id, task_name, task_type, schedule_cron,
                schedule_interval_seconds, next_run_at, last_run_at,
                status, priority, max_retries, retry_count,
                error_message, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            ON CONFLICT (task_id) DO UPDATE SET
                task_name = EXCLUDED.task_name,
                schedule_cron = EXCLUDED.schedule_cron,
                schedule_interval_seconds = EXCLUDED.schedule_interval_seconds,
                next_run_at = EXCLUDED.next_run_at,
                last_run_at = EXCLUDED.last_run_at,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                retry_count = EXCLUDED.retry_count,
                error_message = EXCLUDED.error_message,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
        """
        
        await self.postgres_conn.execute(
            query,
            task.task_id,
            task.task_name,
            task.task_type,
            task.schedule_cron,
            task.schedule_interval_seconds,
            task.next_run_at,
            task.last_run_at,
            task.status.value,
            task.priority.value,
            task.max_retries,
            task.retry_count,
            task.error_message,
            task.metadata,
            task.created_at,
            task.updated_at
        )
    
    def _row_to_task(self, row: Dict) -> ScheduledTask:
        """Convert database row to ScheduledTask"""
        return ScheduledTask(
            task_id=row["task_id"],
            task_name=row["task_name"],
            task_type=row["task_type"],
            schedule_cron=row.get("schedule_cron"),
            schedule_interval_seconds=row.get("schedule_interval_seconds"),
            next_run_at=row.get("next_run_at"),
            last_run_at=row.get("last_run_at"),
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            max_retries=row["max_retries"],
            retry_count=row["retry_count"],
            error_message=row.get("error_message"),
            metadata=row.get("metadata", {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

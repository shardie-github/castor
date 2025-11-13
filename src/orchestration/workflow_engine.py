"""
DELTA:20251113T114706Z Workflow Orchestration Engine

Event-driven workflow orchestration for automated business processes.
Handles complex multi-step workflows triggered by events.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from uuid import uuid4

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Workflow step definition"""
    step_id: str
    name: str
    handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 3
    retry_delay: int = 5
    timeout: Optional[int] = None
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger_event: str  # Event type that triggers this workflow
    steps: List[WorkflowStep]
    enabled: bool = True
    max_concurrent: int = 1


@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    tenant_id: str
    status: WorkflowStatus
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WorkflowEngine:
    """
    DELTA:20251113T114706Z Workflow Orchestration Engine
    
    Coordinates complex multi-step workflows triggered by events.
    Supports:
    - Event-driven triggers
    - Step dependencies
    - Conditional execution
    - Retries and error handling
    - Parallel and sequential execution
    """
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
        
        # Workflow registry
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._running = False
        
        # Event listeners
        self._event_handlers: Dict[str, List[str]] = {}  # event_type -> workflow_ids
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        self._workflows[workflow.workflow_id] = workflow
        
        # Register event handler
        if workflow.trigger_event not in self._event_handlers:
            self._event_handlers[workflow.trigger_event] = []
        self._event_handlers[workflow.trigger_event].append(workflow.workflow_id)
        
        logger.info(f"Registered workflow: {workflow.name} (trigger: {workflow.trigger_event})")
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Handle incoming event and trigger workflows
        
        Args:
            event_type: Type of event (e.g., 'deal.stage_changed', 'io.delivered')
            event_data: Event payload
        """
        if event_type not in self._event_handlers:
            return
        
        workflow_ids = self._event_handlers[event_type]
        
        for workflow_id in workflow_ids:
            workflow = self._workflows.get(workflow_id)
            if not workflow or not workflow.enabled:
                continue
            
            # Check if we can start new execution (max_concurrent limit)
            running_count = sum(
                1 for e in self._executions.values()
                if e.workflow_id == workflow_id and e.status == WorkflowStatus.RUNNING
            )
            
            if running_count >= workflow.max_concurrent:
                logger.warning(f"Max concurrent executions reached for workflow {workflow_id}")
                continue
            
            # Start workflow execution
            execution_id = await self.start_workflow(workflow_id, event_data)
            logger.info(f"Started workflow {workflow_id} execution {execution_id} triggered by {event_type}")
    
    async def start_workflow(
        self,
        workflow_id: str,
        initial_context: Dict[str, Any]
    ) -> str:
        """Start a workflow execution"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid4())
        tenant_id = initial_context.get('tenant_id') or initial_context.get('user_id')
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            tenant_id=tenant_id or 'unknown',
            status=WorkflowStatus.PENDING,
            context=initial_context.copy(),
            started_at=datetime.now(timezone.utc)
        )
        
        self._executions[execution_id] = execution
        
        # Execute workflow asynchronously
        asyncio.create_task(self._execute_workflow(execution, workflow))
        
        return execution_id
    
    async def _execute_workflow(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition
    ):
        """Execute workflow steps"""
        execution.status = WorkflowStatus.RUNNING
        
        try:
            # Determine execution order based on dependencies
            execution_order = self._topological_sort(workflow.steps)
            
            # Execute steps in order
            for step in execution_order:
                # Check if step should be skipped (condition)
                if step.condition and not step.condition(execution.context):
                    logger.info(f"Skipping step {step.step_id} due to condition")
                    execution.step_results[step.step_id] = {
                        'status': WorkflowStepStatus.SKIPPED.value,
                        'skipped': True
                    }
                    continue
                
                # Check dependencies
                if not self._check_dependencies(step, execution.step_results):
                    logger.warning(f"Dependencies not met for step {step.step_id}")
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = f"Dependencies not met for step {step.step_id}"
                    break
                
                # Execute step with retries
                step_result = await self._execute_step_with_retry(step, execution.context)
                execution.step_results[step.step_id] = step_result
                
                # Update context with step result
                execution.context[f'step_{step.step_id}'] = step_result
                
                # If step failed, stop workflow
                if step_result.get('status') == WorkflowStepStatus.FAILED.value:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = step_result.get('error')
                    break
            
            # Mark as completed if all steps succeeded
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
        
        finally:
            # Record metrics
            duration = (execution.completed_at or datetime.now(timezone.utc)) - execution.started_at
            self.metrics.record_histogram(
                'workflow_execution_duration_seconds',
                duration.total_seconds(),
                tags={
                    'workflow_id': workflow.workflow_id,
                    'status': execution.status.value
                }
            )
            
            # Log event
            await self.events.log_event(
                event_type='workflow.completed',
                user_id=None,
                properties={
                    'execution_id': execution.execution_id,
                    'workflow_id': workflow.workflow_id,
                    'status': execution.status.value,
                    'duration_seconds': duration.total_seconds()
                }
            )
    
    async def _execute_step_with_retry(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute step with retry logic"""
        last_error = None
        
        for attempt in range(step.retry_count):
            try:
                # Execute step with timeout if specified
                if step.timeout:
                    result = await asyncio.wait_for(
                        step.handler(context),
                        timeout=step.timeout
                    )
                else:
                    result = await step.handler(context)
                
                return {
                    'status': WorkflowStepStatus.COMPLETED.value,
                    'result': result,
                    'attempt': attempt + 1
                }
            
            except Exception as e:
                last_error = e
                logger.warning(f"Step {step.step_id} attempt {attempt + 1} failed: {e}")
                
                if attempt < step.retry_count - 1:
                    await asyncio.sleep(step.retry_delay)
        
        # All retries failed
        return {
            'status': WorkflowStepStatus.FAILED.value,
            'error': str(last_error),
            'attempts': step.retry_count
        }
    
    def _topological_sort(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Sort steps based on dependencies (topological sort)"""
        # Simple implementation - in production, use proper topological sort
        sorted_steps = []
        remaining = steps.copy()
        completed_ids = set()
        
        while remaining:
            progress = False
            
            for step in remaining[:]:
                # Check if all dependencies are satisfied
                if all(dep in completed_ids for dep in step.depends_on):
                    sorted_steps.append(step)
                    remaining.remove(step)
                    completed_ids.add(step.step_id)
                    progress = True
            
            if not progress:
                # Circular dependency or missing dependency
                logger.warning("Circular dependency detected, using original order")
                sorted_steps.extend(remaining)
                break
        
        return sorted_steps
    
    def _check_dependencies(
        self,
        step: WorkflowStep,
        step_results: Dict[str, Any]
    ) -> bool:
        """Check if step dependencies are satisfied"""
        for dep_id in step.depends_on:
            if dep_id not in step_results:
                return False
            
            dep_result = step_results[dep_id]
            if dep_result.get('status') != WorkflowStepStatus.COMPLETED.value:
                return False
        
        return True
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution status"""
        return self._executions.get(execution_id)
    
    async def cancel_execution(self, execution_id: str):
        """Cancel a running workflow execution"""
        execution = self._executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now(timezone.utc)
            logger.info(f"Cancelled workflow execution {execution_id}")

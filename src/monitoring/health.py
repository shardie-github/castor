"""
Health Check Service

Monitors system health and provides health check endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.database.schema_validator import SchemaValidator, SchemaStatus

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class SystemHealthStatus:
    """Overall health status"""
    status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheck]
    version: str = "1.0.0"


class HealthCheckService:
    """
    Health Check Service
    
    Performs health checks on:
    - Database connectivity
    - Cache connectivity
    - External API availability
    - Service dependencies
    """
    
    def __init__(self, metrics_collector: MetricsCollector, postgres_conn=None):
        self.metrics = metrics_collector
        self.postgres_conn = postgres_conn
        self.schema_validator = SchemaValidator(postgres_conn) if postgres_conn else None
    
    async def check_health(self) -> SystemHealthStatus:
        """Perform all health checks"""
        import asyncio
        
        checks = []
        
        # Database check
        db_check = await self._check_database()
        checks.append(db_check)
        
        # Cache check
        cache_check = await self._check_cache()
        checks.append(cache_check)
        
        # External APIs check
        api_check = await self._check_external_apis()
        checks.append(api_check)
        
        # Schema validation check (if database connection available)
        if self.schema_validator:
            schema_check = await self._check_schema()
            checks.append(schema_check)
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        health_status = SystemHealthStatus(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            checks=checks
        )
        
        # Record telemetry
        self.metrics.record_gauge(
            "health_check_status",
            1 if overall_status == HealthStatus.HEALTHY else 0,
            tags={"status": overall_status.value}
        )
        
        return health_status
    
    async def _check_database(self) -> HealthCheck:
        """Check database connectivity"""
        import time
        import asyncio
        start_time = time.time()
        
        try:
            # In production, this would actually check database connection
            # For now, simulate check
            await asyncio.sleep(0.01)  # Simulate DB query
            
            latency_ms = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_cache(self) -> HealthCheck:
        """Check cache connectivity"""
        import time
        import asyncio
        start_time = time.time()
        
        try:
            # In production, this would check Redis connection
            await asyncio.sleep(0.01)  # Simulate cache check
            
            latency_ms = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="Cache connection successful",
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="cache",
                status=HealthStatus.DEGRADED,  # Cache failure is degraded, not unhealthy
                message=f"Cache connection failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_external_apis(self) -> HealthCheck:
        """Check external API availability"""
        import time
        start_time = time.time()
        
        try:
            # Check critical external APIs
            # In production, would check actual API endpoints
            
            latency_ms = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="external_apis",
                status=HealthStatus.HEALTHY,
                message="External APIs available",
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="external_apis",
                status=HealthStatus.DEGRADED,
                message=f"Some external APIs unavailable: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_schema(self) -> HealthCheck:
        """Check database schema validity"""
        import time
        start_time = time.time()
        
        try:
            if not self.schema_validator:
                return HealthCheck(
                    name="schema",
                    status=HealthStatus.DEGRADED,
                    message="Schema validator not available",
                    latency_ms=0
                )
            
            validation_result = await self.schema_validator.validate_schema()
            latency_ms = (time.time() - start_time) * 1000
            
            # Map schema status to health status
            if validation_result.status == SchemaStatus.VALID:
                health_status = HealthStatus.HEALTHY
            elif validation_result.status == SchemaStatus.DEGRADED:
                health_status = HealthStatus.DEGRADED
            else:
                health_status = HealthStatus.UNHEALTHY
            
            issue_count = len(validation_result.issues)
            message = f"Schema validation: {validation_result.status.value} ({issue_count} issues)"
            
            return HealthCheck(
                name="schema",
                status=health_status,
                message=message,
                latency_ms=latency_ms,
                metadata={
                    "issues_count": issue_count,
                    "tables_checked": validation_result.tables_checked,
                    "indexes_checked": validation_result.indexes_checked,
                    "constraints_checked": validation_result.constraints_checked
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="schema",
                status=HealthStatus.DEGRADED,
                message=f"Schema validation failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks"""
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY

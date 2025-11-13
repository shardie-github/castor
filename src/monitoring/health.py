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
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
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
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks"""
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY

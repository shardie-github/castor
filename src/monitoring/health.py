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
    
    def __init__(self, metrics_collector: MetricsCollector, postgres_conn=None, redis_conn=None, timescale_conn=None):
        self.metrics = metrics_collector
        self.postgres_conn = postgres_conn
        self.redis_conn = redis_conn
        self.timescale_conn = timescale_conn
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
        
        # TimescaleDB check (if available)
        timescale_check = await self._check_timescaledb()
        checks.append(timescale_check)
        
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
        start_time = time.time()
        
        try:
            if not self.postgres_conn:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database connection not configured",
                    latency_ms=0
                )
            
            # Actually check database connection
            is_healthy = await self.postgres_conn.health_check()
            latency_ms = (time.time() - start_time) * 1000
            
            if is_healthy:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    latency_ms=latency_ms
                )
            else:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database health check failed",
                    latency_ms=latency_ms
                )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check error: {e}", exc_info=True)
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_cache(self) -> HealthCheck:
        """Check cache connectivity"""
        import time
        start_time = time.time()
        
        try:
            # Check if Redis connection is available from app state
            # This will be injected via dependency injection
            redis_conn = getattr(self, 'redis_conn', None)
            
            if not redis_conn:
                # Cache is optional, so degraded status is acceptable
                return HealthCheck(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    message="Cache connection not configured",
                    latency_ms=0
                )
            
            # Actually check Redis connection
            try:
                is_healthy = await redis_conn.health_check()
                latency_ms = (time.time() - start_time) * 1000
                
                if is_healthy:
                    return HealthCheck(
                        name="cache",
                        status=HealthStatus.HEALTHY,
                        message="Cache connection successful",
                        latency_ms=latency_ms
                    )
                else:
                    return HealthCheck(
                        name="cache",
                        status=HealthStatus.DEGRADED,  # Cache failure is degraded, not unhealthy
                        message="Cache health check failed",
                        latency_ms=latency_ms
                    )
            except Exception as ping_error:
                latency_ms = (time.time() - start_time) * 1000
                return HealthCheck(
                    name="cache",
                    status=HealthStatus.DEGRADED,  # Cache failure is degraded, not unhealthy
                    message=f"Cache ping failed: {str(ping_error)}",
                    latency_ms=latency_ms
                )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.warning(f"Cache health check error: {e}", exc_info=True)
            return HealthCheck(
                name="cache",
                status=HealthStatus.DEGRADED,  # Cache failure is degraded, not unhealthy
                message=f"Cache connection failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_external_apis(self) -> HealthCheck:
        """Check external API availability"""
        import time
        import os
        import httpx
        start_time = time.time()
        
        try:
            api_statuses = {}
            
            # Check Stripe API (if configured)
            stripe_key = os.getenv("STRIPE_SECRET_KEY")
            if stripe_key:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        # Stripe health check endpoint
                        response = await client.get(
                            "https://api.stripe.com/v1/charges",
                            headers={"Authorization": f"Bearer {stripe_key}"},
                            params={"limit": 1}
                        )
                        api_statuses["stripe"] = response.status_code < 500
                except Exception:
                    api_statuses["stripe"] = False
            
            # Check SendGrid API (if configured)
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            if sendgrid_key:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(
                            "https://api.sendgrid.com/v3/user/profile",
                            headers={"Authorization": f"Bearer {sendgrid_key}"}
                        )
                        api_statuses["sendgrid"] = response.status_code < 500
                except Exception:
                    api_statuses["sendgrid"] = False
            
            # Check Supabase (if configured)
            supabase_url = os.getenv("SUPABASE_URL")
            if supabase_url:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{supabase_url}/rest/v1/")
                        api_statuses["supabase"] = response.status_code < 500
                except Exception:
                    api_statuses["supabase"] = False
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Determine status
            if not api_statuses:
                return HealthCheck(
                    name="external_apis",
                    status=HealthStatus.HEALTHY,
                    message="No external APIs configured",
                    latency_ms=latency_ms
                )
            
            unhealthy_count = sum(1 for status in api_statuses.values() if not status)
            if unhealthy_count == 0:
                status_val = HealthStatus.HEALTHY
                message = "All external APIs available"
            elif unhealthy_count < len(api_statuses):
                status_val = HealthStatus.DEGRADED
                message = f"Some external APIs unavailable ({unhealthy_count}/{len(api_statuses)})"
            else:
                status_val = HealthStatus.UNHEALTHY
                message = "All external APIs unavailable"
            
            return HealthCheck(
                name="external_apis",
                status=status_val,
                message=message,
                latency_ms=latency_ms,
                metadata={"api_statuses": api_statuses}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="external_apis",
                status=HealthStatus.DEGRADED,
                message=f"External API check failed: {str(e)}",
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
    
    async def _check_timescaledb(self) -> HealthCheck:
        """Check TimescaleDB hypertables"""
        import time
        start_time = time.time()
        
        try:
            if not self.timescale_conn:
                return HealthCheck(
                    name="timescaledb",
                    status=HealthStatus.DEGRADED,
                    message="TimescaleDB connection not configured",
                    latency_ms=0
                )
            
            # Check if TimescaleDB extension is available
            query = """
                SELECT COUNT(*) as count
                FROM pg_extension
                WHERE extname = 'timescaledb';
            """
            result = await self.timescale_conn.fetchval(query)
            latency_ms = (time.time() - start_time) * 1000
            
            if result and result > 0:
                # Check hypertables
                hypertable_query = """
                    SELECT COUNT(*) as count
                    FROM _timescaledb_catalog.hypertable;
                """
                hypertable_count = await self.timescale_conn.fetchval(hypertable_query)
                
                return HealthCheck(
                    name="timescaledb",
                    status=HealthStatus.HEALTHY,
                    message=f"TimescaleDB extension active ({hypertable_count} hypertables)",
                    latency_ms=latency_ms,
                    metadata={"hypertable_count": hypertable_count}
                )
            else:
                return HealthCheck(
                    name="timescaledb",
                    status=HealthStatus.DEGRADED,
                    message="TimescaleDB extension not installed",
                    latency_ms=latency_ms
                )
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.warning(f"TimescaleDB health check error: {e}", exc_info=True)
            return HealthCheck(
                name="timescaledb",
                status=HealthStatus.DEGRADED,
                message=f"TimescaleDB check failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks"""
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY

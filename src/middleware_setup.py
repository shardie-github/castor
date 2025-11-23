"""
Middleware Setup

Configures all application middleware.
"""

from fastapi import FastAPI
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.tenants import TenantIsolationMiddleware, TenantManager
from src.utils.error_handler import register_error_handlers


def setup_middleware(
    app: FastAPI,
    metrics_collector: MetricsCollector,
    event_logger: EventLogger,
    tenant_manager: TenantManager
):
    """Setup all application middleware"""
    
    # Register error handlers first
    register_error_handlers(app)
    
    # Security middleware
    from src.security.middleware import setup_security_middleware
    setup_security_middleware(app, metrics_collector, event_logger)
    
    # Tenant isolation middleware
    app.add_middleware(
        TenantIsolationMiddleware,
        tenant_manager=tenant_manager
    )
    
    # Metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        """Middleware to collect metrics"""
        import time
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_histogram(
            "api_request_duration_seconds",
            duration_ms / 1000,
            tags={
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": str(response.status_code)
            }
        )
        
        metrics_collector.increment_counter(
            "api_requests_total",
            tags={
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": str(response.status_code)
            }
        )
        
        if response.status_code >= 400:
            metrics_collector.increment_counter(
                "api_errors_total",
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": str(response.status_code)
                }
            )
        
        return response

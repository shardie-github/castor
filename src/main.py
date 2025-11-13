"""
Main Application Entry Point

FastAPI application with all routes and middleware.
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.config import config
from src.database import PostgresConnection, TimescaleConnection, RedisConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.monitoring.health import HealthCheckService

# Initialize global services
metrics_collector = MetricsCollector()
event_logger = EventLogger()
health_service = HealthCheckService(metrics_collector)

# Database connections
postgres_conn = PostgresConnection(
    host=config.database.postgres_host,
    port=config.database.postgres_port,
    database=config.database.postgres_database,
    user=config.database.postgres_user,
    password=config.database.postgres_password
)

timescale_conn = TimescaleConnection(
    host=config.database.postgres_host,
    port=config.database.postgres_port,
    database=config.database.postgres_database,
    user=config.database.postgres_user,
    password=config.database.postgres_password
)

redis_conn = RedisConnection(
    host=config.database.redis_host,
    port=config.database.redis_port,
    password=config.database.redis_password
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logging.info("Starting application...")
    
    # Initialize database connections
    await postgres_conn.initialize()
    await timescale_conn.initialize()
    await redis_conn.initialize()
    
    # Initialize event logger
    await event_logger.initialize()
    
    yield
    
    # Shutdown
    logging.info("Shutting down application...")
    
    # Close connections
    await postgres_conn.close()
    await timescale_conn.close()
    await redis_conn.close()
    await event_logger.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Podcast Analytics & Sponsorship Platform",
    description="Comprehensive analytics and sponsorship management for podcasts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Podcast Analytics & Sponsorship Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = await health_service.check_health()
    
    status_code = 200
    if health_status.status.value == "unhealthy":
        status_code = 503
    elif health_status.status.value == "degraded":
        status_code = 200  # Still return 200 but indicate degraded
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": health_status.status.value,
            "timestamp": health_status.timestamp.isoformat(),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "latency_ms": check.latency_ms
                }
                for check in health_status.checks
            ]
        }
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    # Convert internal metrics to Prometheus format
    # In production, use prometheus_client directly
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Import routers
# from src.api import campaigns, analytics, reports, integrations
# app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
# app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Main Application Entry Point

FastAPI application with all routes and middleware.
Refactored to use lifespan and middleware setup modules.
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.lifespan import lifespan
from src.middleware_setup import setup_middleware
from src.monitoring.health import HealthCheckService

# Global health service (will be set in lifespan)
health_service: HealthCheckService = None


# Create FastAPI app with OpenAPI documentation
app = FastAPI(
    title="Podcast Analytics & Sponsorship Platform",
    description="Comprehensive analytics and sponsorship management for podcasts",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "tenants", "description": "Multi-tenant management"},
        {"name": "attribution", "description": "Attribution tracking and ROI calculations"},
        {"name": "ai", "description": "AI-powered features and content analysis"},
        {"name": "cost", "description": "Cost tracking and optimization"},
        {"name": "security", "description": "Authentication, authorization, and security"},
        {"name": "backup", "description": "Backup and restore operations"},
        {"name": "optimization", "description": "A/B testing, churn prediction, and optimization"},
        {"name": "risks", "description": "Risk management and compliance"},
        {"name": "partners", "description": "Partner programs and marketplace"},
        {"name": "business", "description": "Business analytics and insights"},
        {"name": "features", "description": "Feature flag management"},
    ]
)


def configure_app(app: FastAPI):
    """Configure application middleware and routes"""
    # Setup middleware (will be called after app.state is populated in lifespan)
    # Note: This is a placeholder - actual setup happens in lifespan
    pass


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Podcast Analytics & Sponsorship Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    health_service = request.app.state.health_service
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


# Register all routes
from src.api.route_registration import register_all_routes
register_all_routes(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

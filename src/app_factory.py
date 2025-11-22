"""
Application Factory

Creates and configures the FastAPI application instance.
Separates app creation from service initialization for better testability.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.config.validation import load_and_validate_env
from src.telemetry.structured_logging import StructuredLogger, LogLevel
from src.telemetry.tracing import setup_tracing
from src.monitoring.health import HealthCheckService


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="Podcast Analytics API",
        description="Comprehensive podcast analytics and sponsorship platform",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.cors_allowed_origins,
        allow_credentials=settings.cors.cors_allow_credentials,
        allow_methods=settings.cors.cors_allowed_methods,
        allow_headers=["*"],
        max_age=settings.cors.cors_max_age,
    )
    
    # Add error handling middleware
    @app.middleware("http")
    async def error_handler(request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logging.error(f"Unhandled exception: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Podcast Analytics API",
            "version": "1.0.0",
            "status": "running"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        # Health check will be available after lifespan startup
        health_service = getattr(app.state, "health_service", None)
        if health_service:
            return await health_service.check_health()
        return {"status": "starting"}
    
    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        metrics_collector = getattr(app.state, "metrics_collector", None)
        if metrics_collector:
            return metrics_collector.get_metrics()
        return {}
    
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown logic.
    """
    # Setup structured logging
    environment = os.getenv("ENVIRONMENT", "development")
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = LogLevel[log_level_str.upper()] if hasattr(LogLevel, log_level_str.upper()) else LogLevel.INFO
    logger = StructuredLogger(__name__, log_level)
    
    # Setup OpenTelemetry tracing
    service_name = os.getenv("SERVICE_NAME", "podcast-analytics-api")
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    setup_tracing(service_name=service_name, otlp_endpoint=otlp_endpoint)
    
    # Startup
    logger.info("Starting application...")
    
    # Validate environment variables
    try:
        validated_env = load_and_validate_env()
        logger.info("Environment validation passed")
    except ValueError as e:
        logger.error("Environment validation failed", extra={"error": str(e)})
        if environment == "production":
            logger.critical("Production environment validation failed. Exiting.")
            sys.exit(1)
        else:
            logger.warning("Continuing with default values in development mode")
    
    # Initialize services (lazy import to avoid circular dependencies)
    from src.services import initialize_services
    
    services = await initialize_services()
    
    # Store services in app state for dependency injection
    for key, value in services.items():
        setattr(app.state, key, value)
    
    # Initialize health check service
    health_service = HealthCheckService(
        services["metrics_collector"],
        postgres_conn=services.get("postgres_conn")
    )
    app.state.health_service = health_service
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cleanup services
    if "postgres_conn" in services:
        await services["postgres_conn"].close()
    if "timescale_conn" in services:
        await services["timescale_conn"].close()
    if "redis_conn" in services:
        await services["redis_conn"].close()
    if "event_logger" in services:
        await services["event_logger"].cleanup()

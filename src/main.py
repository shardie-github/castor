"""
Main Application Entry Point

FastAPI application with all routes and middleware.
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from src.config import config
from src.database import PostgresConnection, TimescaleConnection, RedisConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.monitoring.health import HealthCheckService

# Multi-tenant and advanced features
from src.tenants import TenantManager, TenantIsolationMiddleware
from src.attribution import AttributionEngine
from src.attribution.cross_platform import CrossPlatformAttribution
from src.ai import AIFramework, ContentAnalyzer
from src.cost import CostTracker
from src.security.auth import OAuth2Provider, MFAProvider, APIKeyManager
from src.security.authorization import RBACManager, ABACManager, PermissionEngine
from src.backup import BackupManager, RestoreManager
from src.disaster_recovery import FailoverManager, ReplicationManager
from src.optimization import ABTestingFramework, ChurnPredictor, ChurnAnalyzer, OnboardingAnalyzer
from src.operations.risk_management import RiskManager
from src.partners import ReferralProgram, MarketplaceManager, PartnerPortal
from src.automation.team_automation import TaskScheduler
from src.self_service.onboarding_wizard import OnboardingWizard

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

# Initialize advanced services
tenant_manager = TenantManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

attribution_engine = AttributionEngine(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize AI framework
from src.ai.framework import AIProvider

ai_api_keys = {}
if os.getenv("OPENAI_API_KEY"):
    ai_api_keys[AIProvider.OPENAI] = os.getenv("OPENAI_API_KEY")
if os.getenv("ANTHROPIC_API_KEY"):
    ai_api_keys[AIProvider.ANTHROPIC] = os.getenv("ANTHROPIC_API_KEY")

ai_framework = AIFramework(
    primary_provider=AIProvider.OPENAI if AIProvider.OPENAI in ai_api_keys else (list(ai_api_keys.keys())[0] if ai_api_keys else None),
    api_keys=ai_api_keys
)

content_analyzer = ContentAnalyzer(
    ai_framework=ai_framework,
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

cost_tracker = CostTracker(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize security services
oauth2_provider = OAuth2Provider(
    client_id=os.getenv("OAUTH_CLIENT_ID", "default_client"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET", "default_secret"),
    redirect_uri=os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback"),
    jwt_secret=config.jwt_secret,
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

mfa_provider = MFAProvider(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

api_key_manager = APIKeyManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize authorization services
rbac_manager = RBACManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

abac_manager = ABACManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

permission_engine = PermissionEngine(
    rbac_manager=rbac_manager,
    abac_manager=abac_manager,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

# Initialize cross-platform attribution
cross_platform_attribution = CrossPlatformAttribution(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize backup and disaster recovery
backup_manager = BackupManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn,
    backup_storage_path=os.getenv("BACKUP_STORAGE_PATH", "/backups"),
    aws_s3_bucket=os.getenv("AWS_S3_BACKUP_BUCKET"),
    aws_region=os.getenv("AWS_REGION", "us-east-1")
)

failover_manager = FailoverManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn,
    primary_region=os.getenv("PRIMARY_REGION", "us-east-1"),
    secondary_region=os.getenv("SECONDARY_REGION", "us-west-2")
)

replication_manager = ReplicationManager(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize optimization services
ab_testing = ABTestingFramework(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

churn_predictor = ChurnPredictor(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

churn_analyzer = ChurnAnalyzer(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

onboarding_analyzer = OnboardingAnalyzer(
    metrics_collector=metrics_collector,
    event_logger=event_logger,
    postgres_conn=postgres_conn
)

# Initialize risk management
risk_manager = RiskManager(
    postgres_conn=postgres_conn,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

# Initialize partnership tools
referral_program = ReferralProgram(
    postgres_conn=postgres_conn,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

marketplace_manager = MarketplaceManager(
    postgres_conn=postgres_conn,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

partner_portal = PartnerPortal(
    postgres_conn=postgres_conn,
    referral_program=referral_program,
    marketplace_manager=marketplace_manager,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

# Initialize automation
task_scheduler = TaskScheduler(
    postgres_conn=postgres_conn,
    metrics_collector=metrics_collector,
    event_logger=event_logger
)

# Initialize self-service
onboarding_wizard = OnboardingWizard(
    postgres_conn=postgres_conn,
    metrics_collector=metrics_collector,
    event_logger=event_logger
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
    
    # Store services in app state for dependency injection
    app.state.metrics_collector = metrics_collector
    app.state.event_logger = event_logger
    app.state.postgres_conn = postgres_conn
    app.state.timescale_conn = timescale_conn
    app.state.redis_conn = redis_conn
    app.state.tenant_manager = tenant_manager
    app.state.attribution_engine = attribution_engine
    app.state.cross_platform_attribution = cross_platform_attribution
    app.state.ai_framework = ai_framework
    app.state.content_analyzer = content_analyzer
    app.state.cost_tracker = cost_tracker
    app.state.oauth2_provider = oauth2_provider
    app.state.mfa_provider = mfa_provider
    app.state.api_key_manager = api_key_manager
    app.state.rbac_manager = rbac_manager
    app.state.abac_manager = abac_manager
    app.state.permission_engine = permission_engine
    app.state.backup_manager = backup_manager
    app.state.failover_manager = failover_manager
    app.state.replication_manager = replication_manager
    app.state.ab_testing = ab_testing
    app.state.churn_predictor = churn_predictor
    app.state.churn_analyzer = churn_analyzer
    app.state.onboarding_analyzer = onboarding_analyzer
    app.state.risk_manager = risk_manager
    app.state.referral_program = referral_program
    app.state.marketplace_manager = marketplace_manager
    app.state.partner_portal = partner_portal
    app.state.task_scheduler = task_scheduler
    app.state.onboarding_wizard = onboarding_wizard
    
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

# Security middleware (replaces basic CORS)
from src.security.middleware import setup_security_middleware
setup_security_middleware(app, metrics_collector, event_logger)

# Tenant isolation middleware
app.add_middleware(
    TenantIsolationMiddleware,
    tenant_manager=tenant_manager
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
from src.api import tenants, attribution, ai, cost, security, backup, optimization, risk, partners, business

# DELTA:20251113_064143 Import ETL and Match routers
try:
    from src.api import etl
    ETL_AVAILABLE = True
except ImportError:
    ETL_AVAILABLE = False

try:
    from src.api import match
    MATCH_AVAILABLE = True
except ImportError:
    MATCH_AVAILABLE = False

try:
    from src.api import io
    IO_AVAILABLE = True
except ImportError:
    IO_AVAILABLE = False

try:
    from src.api import deals
    DEALS_AVAILABLE = True
except ImportError:
    DEALS_AVAILABLE = False

try:
    from src.api import dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False

try:
    from src.api import automation
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False

# Include API routers
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(attribution.router, prefix="/api/v1/attribution", tags=["attribution"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(cost.router, prefix="/api/v1/cost", tags=["cost"])
app.include_router(security.router, prefix="/api/v1/security", tags=["security"])
app.include_router(backup.router, prefix="/api/v1/backup", tags=["backup"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"])
app.include_router(risk.router, tags=["risks"])
app.include_router(partners.router, tags=["partners"])
app.include_router(business.router, tags=["business"])

# DELTA:20251113_064143 Include ETL router if available and feature flag enabled
if ETL_AVAILABLE and os.getenv("ENABLE_ETL_CSV_UPLOAD", "false").lower() == "true":
    app.include_router(etl.router)

# DELTA:20251113_064143 Include Match router if available and feature flag enabled
if MATCH_AVAILABLE and os.getenv("ENABLE_MATCHMAKING", "false").lower() == "true":
    app.include_router(match.router)

# DELTA:20251113_064143 Include IO router if available and feature flag enabled
if IO_AVAILABLE and os.getenv("ENABLE_IO_BOOKINGS", "false").lower() == "true":
    app.include_router(io.router)

# DELTA:20251113_064143 Include Deals router if available and feature flag enabled
if DEALS_AVAILABLE and os.getenv("ENABLE_DEAL_PIPELINE", "false").lower() == "true":
    app.include_router(deals.router)

# DELTA:20251113_064143 Include Dashboard router if available and feature flag enabled
if DASHBOARD_AVAILABLE and os.getenv("ENABLE_NEW_DASHBOARD_CARDS", "false").lower() == "true":
    app.include_router(dashboard.router)

# DELTA:20251113_064143 Include Automation router if available and feature flag enabled
if AUTOMATION_AVAILABLE and os.getenv("ENABLE_AUTOMATION_JOBS", "false").lower() == "true":
    app.include_router(automation.router)

# Legacy routers (if they exist)
# from src.api import campaigns, analytics, reports, integrations
# app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
# app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

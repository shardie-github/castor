"""
Route Registration

Centralized route registration to keep main.py clean.
"""

import os
from fastapi import FastAPI


def register_all_routes(app: FastAPI):
    """Register all API routes"""
    from src.api import (
        tenants, attribution, ai, cost, security, backup, optimization,
        risk, partners, business, auth, billing, campaigns, podcasts,
        episodes, sponsors, reports, analytics, users, email,
        sprint_metrics, monitoring, features
    )
    
    # Core routes (always available)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
    app.include_router(campaigns.router, prefix="/api/v1", tags=["campaigns"])
    app.include_router(podcasts.router, prefix="/api/v1", tags=["podcasts"])
    app.include_router(episodes.router, prefix="/api/v1", tags=["episodes"])
    app.include_router(sponsors.router, prefix="/api/v1", tags=["sponsors"])
    app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
    app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
    app.include_router(sprint_metrics.router, prefix="/api/v1", tags=["sprint-metrics"])
    app.include_router(monitoring.router, prefix="/api/v1", tags=["monitoring"])
    app.include_router(users.router, prefix="/api/v1", tags=["users"])
    app.include_router(email.router, prefix="/api/v1", tags=["email"])
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
    app.include_router(features.router, prefix="/api/v1", tags=["features"])
    
    # Feature-flagged routes
    _register_feature_flagged_routes(app)


def _register_feature_flagged_routes(app: FastAPI):
    """Register routes that are behind feature flags"""
    
    # ETL routes
    if os.getenv("ENABLE_ETL_CSV_UPLOAD", "false").lower() == "true":
        try:
            from src.api import etl
            app.include_router(etl.router)
        except ImportError:
            pass
    
    # Matchmaking routes
    if os.getenv("ENABLE_MATCHMAKING", "false").lower() == "true":
        try:
            from src.api import match
            app.include_router(match.router)
        except ImportError:
            pass
    
    # IO booking routes
    if os.getenv("ENABLE_IO_BOOKINGS", "false").lower() == "true":
        try:
            from src.api import io
            app.include_router(io.router)
        except ImportError:
            pass
    
    # Deal pipeline routes
    if os.getenv("ENABLE_DEAL_PIPELINE", "false").lower() == "true":
        try:
            from src.api import deals
            app.include_router(deals.router)
        except ImportError:
            pass
    
    # Dashboard routes
    if os.getenv("ENABLE_NEW_DASHBOARD_CARDS", "false").lower() == "true":
        try:
            from src.api import dashboard
            app.include_router(dashboard.router)
        except ImportError:
            pass
    
    # Automation routes
    if os.getenv("ENABLE_AUTOMATION_JOBS", "false").lower() == "true":
        try:
            from src.api import automation
            app.include_router(automation.router)
        except ImportError:
            pass
    
    # Monetization routes
    if os.getenv("ENABLE_MONETIZATION", "false").lower() == "true":
        try:
            from src.api import monetization
            app.include_router(monetization.router)
        except ImportError:
            pass
    
    # Orchestration routes
    if os.getenv("ENABLE_ORCHESTRATION", "false").lower() == "true":
        try:
            from src.api import orchestration
            app.include_router(orchestration.router)
            
            # Add API usage tracking middleware if orchestration is enabled
            try:
                from src.middleware.api_usage_middleware import APIUsageMiddleware
                app.add_middleware(
                    APIUsageMiddleware,
                    postgres_conn=app.state.postgres_conn,
                    metrics_collector=app.state.metrics_collector,
                    event_logger=app.state.event_logger
                )
            except ImportError:
                import logging
                logging.warning("API usage middleware not available")
        except ImportError:
            pass

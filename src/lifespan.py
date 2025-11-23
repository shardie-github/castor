"""
Application Lifespan Management

Handles application startup and shutdown logic.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI

from src.config import config
from src.config.validation import load_and_validate_env
from src.database import PostgresConnection, TimescaleConnection, RedisConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.telemetry.structured_logging import StructuredLogger, LogLevel
from src.telemetry.tracing import setup_tracing
from src.monitoring.health import HealthCheckService
from src.tenants import TenantManager
from src.attribution import AttributionEngine
from src.attribution.cross_platform import CrossPlatformAttribution
from src.ai import AIFramework, ContentAnalyzer
from src.ai.framework import AIProvider
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
from src.orchestration import (
    WorkflowEngine,
    IntelligentAutomationEngine,
    SmartScheduler,
    AutoOptimizer,
    PredictiveAutomation
)
from src.ai import PredictiveEngine
from src.features.flags import FeatureFlagService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Setup structured logging
    environment = os.getenv("ENVIRONMENT", "development")
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = LogLevel[log_level_str.upper()] if hasattr(LogLevel, log_level_str.upper()) else LogLevel.INFO
    structured_logger = StructuredLogger(__name__, log_level)
    
    # Setup OpenTelemetry tracing
    service_name = os.getenv("SERVICE_NAME", "podcast-analytics-api")
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    setup_tracing(service_name=service_name, otlp_endpoint=otlp_endpoint)
    
    # Startup
    structured_logger.info("Starting application...")
    
    # Validate environment variables
    try:
        validated_env = load_and_validate_env()
        structured_logger.info("Environment validation passed")
    except ValueError as e:
        structured_logger.error("Environment validation failed", extra={"error": str(e)})
        if environment == "production":
            structured_logger.critical("Production environment validation failed. Exiting.")
            sys.exit(1)
        else:
            structured_logger.warning("Continuing with default values in development mode")
    
    # Initialize database connections
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
    
    await postgres_conn.initialize()
    await timescale_conn.initialize()
    await redis_conn.initialize()
    
    # Initialize services
    metrics_collector = MetricsCollector()
    event_logger = EventLogger()
    
    # Initialize health check service
    health_service = HealthCheckService(
        metrics_collector,
        postgres_conn=postgres_conn,
        redis_conn=redis_conn,
        timescale_conn=timescale_conn
    )
    
    await event_logger.initialize()
    
    # Initialize Stripe payment processor
    from src.payments.stripe import StripePaymentProcessor
    stripe_processor = StripePaymentProcessor(
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )
    
    # Initialize tenant manager
    tenant_manager = TenantManager(
        metrics_collector=metrics_collector,
        event_logger=event_logger,
        postgres_conn=postgres_conn
    )
    
    # Initialize attribution engine
    attribution_engine = AttributionEngine(
        metrics_collector=metrics_collector,
        event_logger=event_logger,
        postgres_conn=postgres_conn
    )
    
    # Initialize AI framework
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
    
    # Initialize orchestration components
    workflow_engine = WorkflowEngine(
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )
    
    intelligent_automation = IntelligentAutomationEngine(
        ai_framework=ai_framework,
        predictive_engine=PredictiveEngine(
            ai_framework=ai_framework,
            metrics_collector=metrics_collector,
            event_logger=event_logger,
            postgres_conn=postgres_conn
        ),
        workflow_engine=workflow_engine,
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )
    
    smart_scheduler = SmartScheduler(
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger,
        max_concurrent_jobs=10
    )
    
    auto_optimizer = AutoOptimizer(
        ai_framework=ai_framework,
        predictive_engine=PredictiveEngine(
            ai_framework=ai_framework,
            metrics_collector=metrics_collector,
            event_logger=event_logger,
            postgres_conn=postgres_conn
        ),
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )
    
    predictive_automation = PredictiveAutomation(
        predictive_engine=PredictiveEngine(
            ai_framework=ai_framework,
            metrics_collector=metrics_collector,
            event_logger=event_logger,
            postgres_conn=postgres_conn
        ),
        workflow_engine=workflow_engine,
        intelligent_automation=intelligent_automation,
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )
    
    # Initialize feature flag service
    feature_flag_service = FeatureFlagService(postgres_conn)
    await feature_flag_service.initialize()
    
    # Store services in app state for dependency injection
    app.state.metrics_collector = metrics_collector
    app.state.event_logger = event_logger
    app.state.postgres_conn = postgres_conn
    app.state.stripe_processor = stripe_processor
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
    app.state.workflow_engine = workflow_engine
    app.state.intelligent_automation = intelligent_automation
    app.state.smart_scheduler = smart_scheduler
    app.state.auto_optimizer = auto_optimizer
    app.state.predictive_automation = predictive_automation
    app.state.feature_flag_service = feature_flag_service
    app.state.health_service = health_service
    
    # Start smart scheduler
    await smart_scheduler.start()
    
    # Register default workflows
    await _register_default_workflows(workflow_engine, postgres_conn, metrics_collector, event_logger)
    
    # Setup middleware after app state is populated
    from src.middleware_setup import setup_middleware
    setup_middleware(app, metrics_collector, event_logger, tenant_manager)
    
    structured_logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    structured_logger.info("Shutting down application...")
    
    await smart_scheduler.stop()
    
    # Close connections
    await postgres_conn.close()
    await timescale_conn.close()
    await redis_conn.close()
    await event_logger.cleanup()
    
    structured_logger.info("Application shutdown complete")


async def _register_default_workflows(
    workflow_engine: WorkflowEngine,
    postgres_conn: PostgresConnection,
    metrics_collector: MetricsCollector,
    event_logger: EventLogger
):
    """Register default workflows"""
    from src.orchestration.workflow_engine import WorkflowDefinition, WorkflowStep
    
    # Workflow: Auto-create IO when deal is won
    async def check_deal_stage_handler(context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if deal stage is 'won'"""
        return {'stage': context.get('to')} if context.get('to') == 'won' else {'skip': True}
    
    async def create_io_handler(context: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = context.get('campaign_id')
        tenant_id = context.get('tenant_id')
        
        query = """
            SELECT campaign_id, podcast_id, sponsor_id, campaign_value
            FROM campaigns
            WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
        """
        deal = await postgres_conn.fetchrow(query, campaign_id, tenant_id)
        
        if not deal:
            raise ValueError("Deal not found")
        
        io_query = """
            INSERT INTO io_bookings (
                tenant_id, campaign_id, flight_start, flight_end,
                booked_impressions, booked_cpm_cents, status
            )
            VALUES (
                $1::uuid, $2::uuid,
                NOW(), NOW() + INTERVAL '30 days',
                50000, 3000, 'scheduled'
            )
            RETURNING io_id;
        """
        io_id = await postgres_conn.fetchval(io_query, tenant_id, campaign_id)
        
        await event_logger.log_event(
            event_type='io.auto_created',
            user_id=None,
            properties={'io_id': str(io_id), 'campaign_id': campaign_id}
        )
        
        return {'io_id': str(io_id)}
    
    io_creation_workflow = WorkflowDefinition(
        workflow_id='auto_create_io_on_deal_won',
        name='Auto-Create IO on Deal Won',
        description='Automatically create IO booking when deal reaches won stage',
        trigger_event='deal.stage_changed',
        steps=[
            WorkflowStep(
                step_id='check_deal_stage',
                name='Check Deal Stage',
                handler=check_deal_stage_handler,
                condition=lambda ctx: ctx.get('to') == 'won'
            ),
            WorkflowStep(
                step_id='create_io',
                name='Create IO Booking',
                handler=create_io_handler,
                depends_on=['check_deal_stage']
            )
        ]
    )
    
    workflow_engine.register_workflow(io_creation_workflow)
    
    # Workflow: Auto-recalculate matches on data change
    async def recalc_matches_handler(context: Dict[str, Any]) -> Dict[str, Any]:
        entity_type = context.get('entity_type')
        entity_id = context.get('entity_id')
        tenant_id = context.get('tenant_id')
        
        from src.agents.automation_jobs import AutomationJobs
        automation = AutomationJobs(
            postgres_conn=postgres_conn,
            metrics_collector=metrics_collector,
            event_logger=event_logger
        )
        
        if entity_type == 'advertiser':
            result = await automation.recalculate_matches(
                advertiser_id=entity_id,
                tenant_id=tenant_id
            )
        else:
            result = await automation.recalculate_matches(
                podcast_id=entity_id,
                tenant_id=tenant_id
            )
        
        return result
    
    match_recalc_workflow = WorkflowDefinition(
        workflow_id='auto_recalculate_matches',
        name='Auto-Recalculate Matches',
        description='Automatically recalculate matches when advertiser/podcast data changes',
        trigger_event='match.auto_recalculate',
        steps=[
            WorkflowStep(
                step_id='recalculate',
                name='Recalculate Matches',
                handler=recalc_matches_handler
            )
        ]
    )
    
    workflow_engine.register_workflow(match_recalc_workflow)

"""
Service Initialization

Initializes all application services.
Separated from app_factory for better organization.
"""

import os
from typing import Dict, Any
from src.config.settings import get_settings
from src.database import PostgresConnection, TimescaleConnection, RedisConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger


async def initialize_services() -> Dict[str, Any]:
    """
    Initialize all application services.
    
    Returns:
        Dict[str, Any]: Dictionary of initialized services
    """
    settings = get_settings()
    config = settings  # For backward compatibility
    
    # Initialize telemetry
    metrics_collector = MetricsCollector()
    event_logger = EventLogger()
    
    # Initialize database connections
    postgres_conn = PostgresConnection(
        host=settings.database.postgres_host,
        port=settings.database.postgres_port,
        database=settings.database.postgres_database,
        user=settings.database.postgres_user,
        password=settings.database.postgres_password
    )
    
    timescale_conn = TimescaleConnection(
        host=settings.database.postgres_host,
        port=settings.database.postgres_port,
        database=settings.database.postgres_database,
        user=settings.database.postgres_user,
        password=settings.database.postgres_password
    )
    
    redis_conn = RedisConnection(
        host=settings.database.redis_host,
        port=settings.database.redis_port,
        password=settings.database.redis_password
    )
    
    # Initialize connections
    await postgres_conn.initialize()
    await timescale_conn.initialize()
    await redis_conn.initialize()
    
    # Initialize event logger
    await event_logger.initialize()
    
    # Initialize other services (lazy imports to avoid circular dependencies)
    services = {
        "metrics_collector": metrics_collector,
        "event_logger": event_logger,
        "postgres_conn": postgres_conn,
        "timescale_conn": timescale_conn,
        "redis_conn": redis_conn,
    }
    
    # Initialize advanced services (optional, can be added as needed)
    # These are imported lazily to avoid heavy module-level imports
    
    return services

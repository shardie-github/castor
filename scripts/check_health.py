#!/usr/bin/env python3
"""
Health Check Script

Checks the health of all infrastructure services.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import PostgresConnection, RedisConnection
from src.config import load_config
from src.monitoring.health import HealthCheckService
from src.telemetry.metrics import MetricsCollector

async def check_all_services():
    """Check health of all services"""
    config = load_config()
    
    print("=" * 60)
    print("Infrastructure Health Check")
    print("=" * 60)
    print()
    
    # Check PostgreSQL
    print("Checking PostgreSQL...")
    try:
        postgres = PostgresConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        await postgres.initialize()
        
        if await postgres.health_check():
            print("  ✓ PostgreSQL: Healthy")
        else:
            print("  ✗ PostgreSQL: Unhealthy")
        
        await postgres.close()
    except Exception as e:
        print(f"  ✗ PostgreSQL: Error - {e}")
    
    print()
    
    # Check Redis
    print("Checking Redis...")
    try:
        redis = RedisConnection(
            host=config.database.redis_host,
            port=config.database.redis_port,
            password=config.database.redis_password
        )
        await redis.initialize()
        
        if await redis.health_check():
            print("  ✓ Redis: Healthy")
        else:
            print("  ✗ Redis: Unhealthy")
        
        await redis.close()
    except Exception as e:
        print(f"  ✗ Redis: Error - {e}")
    
    print()
    
    # Check Health Service
    print("Checking Health Service...")
    try:
        metrics = MetricsCollector()
        health_service = HealthCheckService(metrics)
        health_status = await health_service.check_health()
        
        print(f"  Status: {health_status.status.value}")
        print(f"  Checks:")
        for check in health_status.checks:
            status_icon = "✓" if check.status.value == "healthy" else "✗"
            print(f"    {status_icon} {check.name}: {check.status.value} ({check.latency_ms}ms)")
            if check.message:
                print(f"      {check.message}")
    except Exception as e:
        print(f"  ✗ Health Service: Error - {e}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_all_services())

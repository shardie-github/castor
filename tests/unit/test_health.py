"""
Unit tests for health check service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.monitoring.health import (
    HealthCheckService,
    HealthStatus,
    HealthCheck,
    SystemHealthStatus
)
from src.telemetry.metrics import MetricsCollector


@pytest.fixture
def mock_postgres_conn():
    """Mock PostgreSQL connection"""
    conn = Mock()
    conn.health_check = AsyncMock(return_value=True)
    return conn


@pytest.fixture
def mock_redis_conn():
    """Mock Redis connection"""
    conn = Mock()
    conn.health_check = AsyncMock(return_value=True)
    return conn


@pytest.fixture
def health_service(mock_metrics_collector, mock_postgres_conn, mock_redis_conn):
    """Health check service with mocked dependencies"""
    return HealthCheckService(
        metrics_collector=mock_metrics_collector,
        postgres_conn=mock_postgres_conn,
        redis_conn=mock_redis_conn
    )


@pytest.mark.asyncio
async def test_check_health_all_healthy(health_service, mock_postgres_conn, mock_redis_conn):
    """Test health check when all services are healthy"""
    mock_postgres_conn.health_check.return_value = True
    mock_redis_conn.health_check.return_value = True
    
    result = await health_service.check_health()
    
    assert result.status == HealthStatus.HEALTHY
    assert len(result.checks) >= 3  # database, cache, external_apis
    
    db_check = next((c for c in result.checks if c.name == "database"), None)
    assert db_check is not None
    assert db_check.status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_check_health_database_unhealthy(health_service, mock_postgres_conn):
    """Test health check when database is unhealthy"""
    mock_postgres_conn.health_check.return_value = False
    
    result = await health_service.check_health()
    
    assert result.status == HealthStatus.UNHEALTHY
    
    db_check = next((c for c in result.checks if c.name == "database"), None)
    assert db_check is not None
    assert db_check.status == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_check_health_database_exception(health_service, mock_postgres_conn):
    """Test health check when database raises exception"""
    mock_postgres_conn.health_check.side_effect = Exception("Connection failed")
    
    result = await health_service.check_health()
    
    db_check = next((c for c in result.checks if c.name == "database"), None)
    assert db_check is not None
    assert db_check.status == HealthStatus.UNHEALTHY
    assert "failed" in db_check.message.lower()


@pytest.mark.asyncio
async def test_check_health_cache_degraded(health_service, mock_redis_conn):
    """Test health check when cache is degraded"""
    mock_redis_conn.health_check.return_value = False
    
    result = await health_service.check_health()
    
    cache_check = next((c for c in result.checks if c.name == "cache"), None)
    assert cache_check is not None
    assert cache_check.status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_check_health_no_postgres(health_service):
    """Test health check when PostgreSQL connection is not configured"""
    health_service.postgres_conn = None
    
    result = await health_service.check_health()
    
    db_check = next((c for c in result.checks if c.name == "database"), None)
    assert db_check is not None
    assert db_check.status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_check_health_no_redis(health_service):
    """Test health check when Redis connection is not configured"""
    health_service.redis_conn = None
    
    result = await health_service.check_health()
    
    cache_check = next((c for c in result.checks if c.name == "cache"), None)
    assert cache_check is not None
    assert cache_check.status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_check_health_latency_tracking(health_service, mock_postgres_conn):
    """Test that health checks track latency"""
    mock_postgres_conn.health_check.return_value = True
    
    result = await health_service.check_health()
    
    db_check = next((c for c in result.checks if c.name == "database"), None)
    assert db_check is not None
    assert db_check.latency_ms is not None
    assert db_check.latency_ms >= 0


@pytest.mark.asyncio
async def test_determine_overall_status_unhealthy(health_service):
    """Test overall status determination when unhealthy"""
    checks = [
        HealthCheck("test1", HealthStatus.UNHEALTHY),
        HealthCheck("test2", HealthStatus.HEALTHY),
    ]
    
    status = health_service._determine_overall_status(checks)
    assert status == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_determine_overall_status_degraded(health_service):
    """Test overall status determination when degraded"""
    checks = [
        HealthCheck("test1", HealthStatus.DEGRADED),
        HealthCheck("test2", HealthStatus.HEALTHY),
    ]
    
    status = health_service._determine_overall_status(checks)
    assert status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_determine_overall_status_healthy(health_service):
    """Test overall status determination when all healthy"""
    checks = [
        HealthCheck("test1", HealthStatus.HEALTHY),
        HealthCheck("test2", HealthStatus.HEALTHY),
    ]
    
    status = health_service._determine_overall_status(checks)
    assert status == HealthStatus.HEALTHY

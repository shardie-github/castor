"""
API Performance Benchmarks

Tests API endpoint performance and identifies bottlenecks.
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.mark.performance
class TestAPIPerformance:
    """API performance benchmarks"""
    
    def test_health_endpoint_performance(self, client):
        """Health endpoint should respond quickly"""
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.1  # Should respond in < 100ms
    
    def test_root_endpoint_performance(self, client):
        """Root endpoint should respond quickly"""
        start = time.time()
        response = client.get("/")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.1
    
    def test_metrics_endpoint_performance(self, client):
        """Metrics endpoint should respond quickly"""
        start = time.time()
        response = client.get("/metrics")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.5  # Metrics can take slightly longer
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        duration = time.time() - start
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
        # Should handle 50 requests in reasonable time
        assert duration < 5.0
        # Average response time should be reasonable
        avg_time = duration / len(results)
        assert avg_time < 0.2


@pytest.mark.performance
class TestDatabasePerformance:
    """Database query performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_simple_query_performance(self):
        """Simple queries should be fast"""
        from src.database import PostgresConnection
        from src.config import config
        
        conn = PostgresConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        
        await conn.initialize()
        
        try:
            start = time.time()
            async with conn.acquire() as db_conn:
                result = await db_conn.fetchval("SELECT 1")
            duration = time.time() - start
            
            assert result == 1
            assert duration < 0.05  # Simple query should be < 50ms
            
        finally:
            await conn.close()
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_query_performance(self):
        """Tenant isolation queries should be efficient"""
        from src.database import PostgresConnection
        from src.config import config
        
        conn = PostgresConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        
        await conn.initialize()
        
        try:
            # Test tenant-scoped query performance
            start = time.time()
            async with conn.acquire() as db_conn:
                result = await db_conn.fetch("""
                    SELECT id, name FROM tenants LIMIT 10
                """)
            duration = time.time() - start
            
            assert duration < 0.1  # Should be fast with proper indexes
            
        finally:
            await conn.close()


@pytest.mark.performance
class TestCachePerformance:
    """Cache performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_redis_cache_performance(self):
        """Redis cache operations should be fast"""
        from src.database import RedisConnection
        from src.config import config
        
        redis = RedisConnection(
            host=config.database.redis_host,
            port=config.database.redis_port,
            password=config.database.redis_password
        )
        
        await redis.initialize()
        
        try:
            # Test set operation
            start = time.time()
            await redis.set("perf_test", "value", ttl=60)
            set_duration = time.time() - start
            
            # Test get operation
            start = time.time()
            value = await redis.get("perf_test")
            get_duration = time.time() - start
            
            assert value == "value"
            assert set_duration < 0.01  # Redis should be very fast
            assert get_duration < 0.01
            
        finally:
            await redis.close()


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")

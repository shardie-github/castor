"""
Smoke Tests

Basic health checks to verify the application is running correctly.
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_backend_health():
    """Test backend health endpoint"""
    api_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/health", timeout=5.0)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_backend_root():
    """Test backend root endpoint"""
    api_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/", timeout=5.0)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
async def test_backend_metrics():
    """Test backend metrics endpoint"""
    api_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/metrics", timeout=5.0)
        
        assert response.status_code == 200
        # Prometheus metrics format
        assert "prometheus" in response.headers.get("content-type", "").lower() or len(response.text) > 0


@pytest.mark.asyncio
async def test_frontend_health(backend_url: str = None):
    """Test frontend health (if health endpoint exists)"""
    frontend_url = "http://localhost:3000"
    
    async with httpx.AsyncClient() as client:
        # Try health endpoint first
        try:
            response = await client.get(f"{frontend_url}/api/health", timeout=5.0)
            assert response.status_code == 200
        except httpx.ConnectError:
            # If no health endpoint, just check root
            response = await client.get(f"{frontend_url}/", timeout=5.0)
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_database_connectivity():
    """Test database connectivity via backend"""
    api_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/health", timeout=5.0)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if database check is in health status
        checks = data.get("checks", [])
        db_check = next((c for c in checks if "database" in c.get("name", "").lower()), None)
        
        if db_check:
            assert db_check["status"] in ["healthy", "degraded"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

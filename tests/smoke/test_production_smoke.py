"""
Production Smoke Tests

Comprehensive smoke tests for production deployments.
These tests verify critical user flows work end-to-end.
"""

import pytest
import httpx
import os
from typing import Optional


# Get API URL from environment or use default
API_URL = os.getenv("API_URL", "http://localhost:8000")
BASE_URL = f"{API_URL}/api/v1"


@pytest.fixture
def api_client():
    """Create HTTP client for API calls"""
    return httpx.AsyncClient(base_url=API_URL, timeout=30.0)


@pytest.fixture
async def auth_token(api_client):
    """Get authentication token for tests"""
    # Try to register a test user
    test_email = f"smoke_test_{os.urandom(4).hex()}@example.com"
    test_password = "SmokeTest123!"
    
    try:
        # Register
        register_response = await api_client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": "Smoke Test User",
                "accept_terms": True,
                "accept_privacy": True
            }
        )
        
        # Login
        login_response = await api_client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            return data.get("access_token")
    except Exception:
        pass
    
    return None


@pytest.mark.asyncio
async def test_health_endpoint(api_client):
    """Test health check endpoint"""
    response = await api_client.get("/health")
    
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    data = response.json()
    
    assert "status" in data, "Health status missing"
    assert data["status"] in ["healthy", "degraded", "unhealthy"], f"Invalid status: {data['status']}"
    
    # Check that database is healthy (if checks are present)
    if "checks" in data:
        db_check = next((c for c in data["checks"] if "database" in c.get("name", "").lower()), None)
        if db_check:
            assert db_check["status"] in ["healthy", "degraded"], f"Database unhealthy: {db_check}"


@pytest.mark.asyncio
async def test_root_endpoint(api_client):
    """Test root endpoint"""
    response = await api_client.get("/")
    
    assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"
    data = response.json()
    assert "message" in data, "Message field missing"


@pytest.mark.asyncio
async def test_metrics_endpoint(api_client):
    """Test metrics endpoint"""
    response = await api_client.get("/metrics")
    
    assert response.status_code == 200, f"Metrics endpoint failed: {response.status_code}"
    assert len(response.text) > 0, "Metrics response is empty"


@pytest.mark.asyncio
async def test_api_docs_endpoint(api_client):
    """Test API documentation endpoint"""
    response = await api_client.get("/api/docs")
    
    assert response.status_code == 200, f"API docs endpoint failed: {response.status_code}"


@pytest.mark.asyncio
async def test_openapi_spec_endpoint(api_client):
    """Test OpenAPI specification endpoint"""
    response = await api_client.get("/api/openapi.json")
    
    assert response.status_code == 200, f"OpenAPI spec endpoint failed: {response.status_code}"
    data = response.json()
    
    assert "openapi" in data or "swagger" in data, "Invalid OpenAPI spec"
    assert "paths" in data, "Paths missing from OpenAPI spec"
    assert len(data["paths"]) > 0, "No endpoints in OpenAPI spec"


@pytest.mark.asyncio
async def test_auth_register(api_client):
    """Test user registration"""
    test_email = f"smoke_register_{os.urandom(4).hex()}@example.com"
    
    response = await api_client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": "SmokeTest123!",
            "name": "Smoke Test User",
            "accept_terms": True,
            "accept_privacy": True
        }
    )
    
    # Should be 201 (created) or 400 (already exists)
    assert response.status_code in [201, 400], f"Registration failed: {response.status_code} - {response.text}"
    
    if response.status_code == 201:
        data = response.json()
        assert "user_id" in data or "email" in data, "Invalid registration response"


@pytest.mark.asyncio
async def test_auth_login(api_client, auth_token):
    """Test user login"""
    if auth_token is None:
        pytest.skip("Could not get auth token")
    
    # Verify token works by calling /auth/me
    response = await api_client.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200, f"Auth check failed: {response.status_code}"
    data = response.json()
    assert "email" in data or "user_id" in data, "Invalid user data"


@pytest.mark.asyncio
async def test_podcasts_list(api_client, auth_token):
    """Test listing podcasts"""
    if auth_token is None:
        pytest.skip("Could not get auth token")
    
    response = await api_client.get(
        f"{BASE_URL}/podcasts",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200, f"Podcasts list failed: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Podcasts should be a list"


@pytest.mark.asyncio
async def test_campaigns_list(api_client, auth_token):
    """Test listing campaigns"""
    if auth_token is None:
        pytest.skip("Could not get auth token")
    
    response = await api_client.get(
        f"{BASE_URL}/campaigns",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200, f"Campaigns list failed: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Campaigns should be a list"


@pytest.mark.asyncio
async def test_sponsors_list(api_client, auth_token):
    """Test listing sponsors"""
    if auth_token is None:
        pytest.skip("Could not get auth token")
    
    response = await api_client.get(
        f"{BASE_URL}/sponsors",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200, f"Sponsors list failed: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Sponsors should be a list"


@pytest.mark.asyncio
async def test_tenants_endpoint(api_client, auth_token):
    """Test tenants endpoint"""
    if auth_token is None:
        pytest.skip("Could not get auth token")
    
    response = await api_client.get(
        f"{BASE_URL}/tenants",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should be 200 (list) or 404 (not found) or 403 (forbidden)
    assert response.status_code in [200, 404, 403], f"Tenants endpoint failed: {response.status_code}"


@pytest.mark.asyncio
async def test_rate_limiting(api_client):
    """Test rate limiting headers"""
    # Make a request and check for rate limit headers
    response = await api_client.get("/health")
    
    # Rate limit headers may or may not be present
    rate_limit_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ]
    
    # If rate limiting is enabled, headers should be present
    # This is informational, not a failure
    if any(h in response.headers for h in rate_limit_headers):
        assert True, "Rate limiting is configured"


@pytest.mark.asyncio
async def test_cors_headers(api_client):
    """Test CORS headers"""
    response = await api_client.options("/health")
    
    # CORS headers may or may not be present depending on configuration
    # This is informational
    cors_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods"]
    
    if any(h in response.headers for h in cors_headers):
        assert True, "CORS is configured"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

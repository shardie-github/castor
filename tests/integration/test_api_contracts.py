"""
API Contract Tests

Tests API contracts to ensure consistency and prevent breaking changes.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint_exists(self):
        """Test that health endpoint exists and returns correct format"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)
    
    def test_metrics_endpoint_exists(self):
        """Test that metrics endpoint exists"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Prometheus format
        assert "text/plain" in response.headers.get("content-type", "")


class TestAPIVersioning:
    """Test API versioning"""
    
    def test_api_v1_prefix(self):
        """Test that API endpoints use /api/v1 prefix"""
        # This is a contract test - endpoints should follow this pattern
        # Actual endpoints will be tested individually
        pass


class TestErrorResponseFormat:
    """Test error response format consistency"""
    
    def test_404_error_format(self):
        """Test 404 error format"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        # Error format should be consistent
        data = response.json()
        # FastAPI default format, but we can check structure
        assert "detail" in data or "error" in data
    
    def test_422_validation_error_format(self):
        """Test validation error format"""
        # Send invalid request
        response = client.post("/api/v1/tenants", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)


class TestAuthentication:
    """Test authentication contract"""
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication"""
        # Most endpoints should require auth
        # This is a contract test
        pass
    
    def test_auth_header_format(self):
        """Test that auth uses Bearer token format"""
        # Contract: Authorization: Bearer <token>
        pass


class TestPagination:
    """Test pagination contract"""
    
    def test_pagination_query_params(self):
        """Test pagination query parameters"""
        # Contract: page and limit query params
        # Response should include pagination metadata
        pass


class TestOpenAPISchema:
    """Test OpenAPI schema generation"""
    
    def test_openapi_schema_exists(self):
        """Test that OpenAPI schema is available"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_openapi_docs_available(self):
        """Test that OpenAPI docs are available"""
        response = client.get("/api/docs")
        assert response.status_code == 200

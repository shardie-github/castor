"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_services():
    """Mock all services"""
    return {
        "risk_manager": MagicMock(),
        "referral_program": MagicMock(),
        "marketplace_manager": MagicMock(),
        "partner_portal": MagicMock()
    }


@pytest.fixture
def client(mock_services):
    """Create test client"""
    # In a real implementation, you would inject mocked services
    from src.main import app
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May be unhealthy in test
    assert "status" in response.json()


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200

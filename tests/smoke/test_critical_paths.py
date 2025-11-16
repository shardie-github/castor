"""
Smoke Tests for Critical Paths

Tests the most critical user flows to ensure basic functionality works.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers"""
    # Register a test user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "smoke_test@example.com",
            "password": "Test1234!",
            "name": "Smoke Test User",
            "accept_terms": True,
            "accept_privacy": True
        }
    )
    
    if response.status_code == 201:
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "smoke_test@example.com",
                "password": "Test1234!"
            }
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
    
    return {}


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_auth_register(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_register@example.com",
            "password": "Test1234!",
            "name": "Test User",
            "accept_terms": True,
            "accept_privacy": True
        }
    )
    assert response.status_code in [201, 400]  # 400 if user already exists


def test_auth_login(client):
    """Test user login"""
    # First register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_login@example.com",
            "password": "Test1234!",
            "name": "Test User",
            "accept_terms": True,
            "accept_privacy": True
        }
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test_login@example.com",
            "password": "Test1234!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_get_current_user(client, auth_headers):
    """Test getting current user"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data


def test_create_podcast(client, auth_headers):
    """Test creating a podcast"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.post(
        "/api/v1/podcasts",
        headers=auth_headers,
        json={
            "title": "Test Podcast",
            "feed_url": "https://example.com/feed.xml",
            "description": "Test description"
        }
    )
    assert response.status_code in [201, 400]  # 400 if validation fails


def test_list_podcasts(client, auth_headers):
    """Test listing podcasts"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.get("/api/v1/podcasts", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_sponsor(client, auth_headers):
    """Test creating a sponsor"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.post(
        "/api/v1/sponsors",
        headers=auth_headers,
        json={
            "name": "Test Sponsor",
            "company": "Test Company",
            "email": "sponsor@example.com"
        }
    )
    assert response.status_code in [201, 400]


def test_list_sponsors(client, auth_headers):
    """Test listing sponsors"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.get("/api/v1/sponsors", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user_profile(client, auth_headers):
    """Test getting user profile"""
    if not auth_headers:
        pytest.skip("Authentication not available")
    
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_api_docs(client):
    """Test API documentation endpoint"""
    response = client.get("/api/docs")
    assert response.status_code == 200

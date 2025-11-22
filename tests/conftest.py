"""
Shared test fixtures and configuration
"""

import pytest
import os
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient

# Set test environment variables before any imports
os.environ["SKIP_ENV_VALIDATION"] = "true"
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db")
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")
os.environ["JWT_SECRET"] = os.getenv("JWT_SECRET", "test_secret_key_min_32_chars_long_for_testing")
os.environ["ENCRYPTION_KEY"] = os.getenv("ENCRYPTION_KEY", "test_encryption_key_min_32_chars_long_for_testing")
os.environ["POSTGRES_DATABASE"] = "test_db"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector"""
    collector = Mock()
    collector.increment = Mock()
    collector.gauge = Mock()
    collector.histogram = Mock()
    collector.summary = Mock()
    return collector


@pytest.fixture
def mock_event_logger():
    """Mock event logger"""
    logger = Mock()
    logger.log_event = Mock()
    logger.log_user_action = Mock()
    logger.log_feature_usage = Mock()
    return logger


@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection"""
    conn = Mock()
    conn.execute = Mock(return_value=None)
    conn.fetch_one = Mock(return_value=None)
    conn.fetch_all = Mock(return_value=[])
    conn.close = Mock()
    return conn


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection"""
    conn = Mock()
    conn.get = Mock(return_value=None)
    conn.set = Mock(return_value=True)
    conn.delete = Mock(return_value=True)
    conn.exists = Mock(return_value=False)
    conn.close = Mock()
    return conn


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "Test1234!",
        "name": "Test User",
        "user_id": "test-user-id",
    }


@pytest.fixture
def test_podcast_data():
    """Test podcast data"""
    return {
        "podcast_id": "test-podcast-id",
        "title": "Test Podcast",
        "feed_url": "https://example.com/feed.xml",
        "description": "Test description",
        "user_id": "test-user-id",
    }


@pytest.fixture
def test_campaign_data():
    """Test campaign data"""
    return {
        "campaign_id": "test-campaign-id",
        "name": "Test Campaign",
        "sponsor_id": "test-sponsor-id",
        "podcast_id": "test-podcast-id",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    }


@pytest.fixture
def auth_token():
    """Generate a test auth token"""
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    
    secret = os.getenv("JWT_SECRET", "test_secret_key_min_32_chars_long_for_testing")
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    # Import here to avoid loading app before env vars are set
    from src.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config singleton before each test"""
    import src.config.settings
    src.config.settings._settings = None
    yield
    src.config.settings._settings = None

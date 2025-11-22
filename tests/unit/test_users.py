"""
Tests for user management
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from src.users.user_manager import UserManager


@pytest.fixture
def user_manager(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create user manager instance"""
    return UserManager(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


@pytest.mark.asyncio
class TestUserManager:
    """Test user manager functionality"""
    
    async def test_create_user_manager(self, user_manager):
        """Test creating user manager"""
        assert user_manager is not None
        assert user_manager.metrics_collector is not None
        assert user_manager.event_logger is not None
    
    async def test_create_user(self, user_manager):
        """Test creating a user"""
        mock_row = {
            "user_id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "created_at": datetime.now(timezone.utc)
        }
        user_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        user_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        user = await user_manager.create_user(
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password",
            tenant_id="tenant-123"
        )
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
    
    async def test_get_user_by_id(self, user_manager):
        """Test getting a user by ID"""
        mock_row = {
            "user_id": "user-123",
            "email": "test@example.com",
            "name": "Test User"
        }
        user_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        
        user = await user_manager.get_user_by_id("user-123")
        
        assert user is not None
        assert user["user_id"] == "user-123"
        assert user["email"] == "test@example.com"
    
    async def test_get_user_by_email(self, user_manager):
        """Test getting a user by email"""
        mock_row = {
            "user_id": "user-123",
            "email": "test@example.com",
            "name": "Test User"
        }
        user_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        
        user = await user_manager.get_user_by_email("test@example.com")
        
        assert user is not None
        assert user["email"] == "test@example.com"
    
    async def test_update_user(self, user_manager):
        """Test updating a user"""
        updates = {"name": "Updated Name"}
        mock_row = {
            "user_id": "user-123",
            "email": "test@example.com",
            "name": "Updated Name"
        }
        user_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        user_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        user = await user_manager.update_user("user-123", updates)
        
        assert user is not None
        assert user["name"] == "Updated Name"
    
    async def test_delete_user(self, user_manager):
        """Test deleting a user"""
        user_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        await user_manager.delete_user("user-123")
        
        user_manager.postgres_conn.execute.assert_called()

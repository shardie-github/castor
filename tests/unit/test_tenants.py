"""
Tests for tenant management
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from src.tenants.tenant_manager import TenantManager, Tenant, TenantStatus, SubscriptionTier
from src.tenants.tenant_isolation import get_current_tenant, TenantIsolationMiddleware


@pytest.fixture
def tenant_manager(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create tenant manager instance"""
    return TenantManager(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


@pytest.fixture
def sample_tenant():
    """Sample tenant data"""
    return Tenant(
        tenant_id="test-tenant-123",
        name="Test Tenant",
        slug="test-tenant",
        subscription_tier=SubscriptionTier.STARTER,
        status=TenantStatus.ACTIVE,
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
class TestTenantManager:
    """Test tenant manager functionality"""
    
    async def test_create_tenant_manager(self, tenant_manager):
        """Test creating tenant manager"""
        assert tenant_manager is not None
        assert tenant_manager.metrics_collector is not None
        assert tenant_manager.event_logger is not None
    
    async def test_create_tenant(self, tenant_manager):
        """Test creating a tenant"""
        mock_row = {
            "tenant_id": "test-tenant-123",
            "name": "Test Tenant",
            "slug": "test-tenant",
            "subscription_tier": "starter",
            "status": "active"
        }
        tenant_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        tenant_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        tenant = await tenant_manager.create_tenant(
            name="Test Tenant",
            slug="test-tenant",
            subscription_tier=SubscriptionTier.STARTER
        )
        
        assert tenant is not None
        assert tenant.name == "Test Tenant"
        assert tenant.slug == "test-tenant"
    
    async def test_get_tenant(self, tenant_manager, sample_tenant):
        """Test getting a tenant by ID"""
        mock_row = {
            "tenant_id": sample_tenant.tenant_id,
            "name": sample_tenant.name,
            "slug": sample_tenant.slug,
            "subscription_tier": sample_tenant.subscription_tier.value,
            "status": sample_tenant.status.value
        }
        tenant_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        
        tenant = await tenant_manager.get_tenant(sample_tenant.tenant_id)
        
        assert tenant is not None
        assert tenant.tenant_id == sample_tenant.tenant_id
        assert tenant.name == sample_tenant.name
    
    async def test_get_tenant_by_slug(self, tenant_manager, sample_tenant):
        """Test getting a tenant by slug"""
        mock_row = {
            "tenant_id": sample_tenant.tenant_id,
            "name": sample_tenant.name,
            "slug": sample_tenant.slug,
            "subscription_tier": sample_tenant.subscription_tier.value,
            "status": sample_tenant.status.value
        }
        tenant_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        
        tenant = await tenant_manager.get_tenant_by_slug(sample_tenant.slug)
        
        assert tenant is not None
        assert tenant.slug == sample_tenant.slug
    
    async def test_update_tenant(self, tenant_manager, sample_tenant):
        """Test updating a tenant"""
        updates = {"name": "Updated Name"}
        mock_row = {
            "tenant_id": sample_tenant.tenant_id,
            "name": "Updated Name",
            "slug": sample_tenant.slug,
            "subscription_tier": sample_tenant.subscription_tier.value,
            "status": sample_tenant.status.value
        }
        tenant_manager.postgres_conn.fetchrow = AsyncMock(return_value=mock_row)
        tenant_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        tenant = await tenant_manager.update_tenant(sample_tenant.tenant_id, updates)
        
        assert tenant is not None
        assert tenant.name == "Updated Name"
    
    async def test_delete_tenant(self, tenant_manager):
        """Test deleting a tenant"""
        tenant_manager.postgres_conn.execute = AsyncMock(return_value=None)
        
        await tenant_manager.delete_tenant("test-tenant-123")
        
        tenant_manager.postgres_conn.execute.assert_called()


@pytest.mark.asyncio
class TestTenantIsolation:
    """Test tenant isolation functionality"""
    
    async def test_get_current_tenant_from_state(self):
        """Test extracting tenant ID from request state"""
        mock_request = Mock()
        mock_request.state.tenant_id = "test-tenant-123"
        
        tenant_id = await get_current_tenant(mock_request)
        
        assert tenant_id == "test-tenant-123"
    
    async def test_get_current_tenant_from_header(self):
        """Test extracting tenant ID from header"""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.tenant_id = None
        mock_request.headers = {"X-Tenant-ID": "test-tenant-456"}
        
        tenant_id = await get_current_tenant(mock_request)
        
        assert tenant_id == "test-tenant-456"
    
    async def test_get_current_tenant_from_subdomain(self):
        """Test extracting tenant ID from subdomain"""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.tenant_id = None
        mock_request.headers = {"Host": "test-tenant.example.com"}
        mock_request.app.state.tenant_manager = Mock()
        mock_tenant = Mock()
        mock_tenant.tenant_id = "test-tenant-789"
        mock_request.app.state.tenant_manager.get_tenant_by_slug = AsyncMock(return_value=mock_tenant)
        
        tenant_id = await get_current_tenant(mock_request)
        
        assert tenant_id == "test-tenant-789"
    
    async def test_get_current_tenant_none(self):
        """Test when no tenant ID is found"""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.tenant_id = None
        mock_request.headers = {}
        
        tenant_id = await get_current_tenant(mock_request)
        
        assert tenant_id is None

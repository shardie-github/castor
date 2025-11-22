"""
Tests for cost tracking
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import date, datetime, timezone
from src.cost.cost_tracker import CostTracker, CostType, CostAllocation


@pytest.fixture
def cost_tracker(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create cost tracker instance"""
    return CostTracker(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


@pytest.mark.asyncio
class TestCostTracker:
    """Test cost tracker functionality"""
    
    async def test_create_cost_tracker(self, cost_tracker):
        """Test creating cost tracker"""
        assert cost_tracker is not None
        assert cost_tracker.metrics is not None
        assert cost_tracker.events is not None
        assert cost_tracker.postgres is not None
    
    async def test_track_resource_usage(self, cost_tracker):
        """Test tracking resource usage"""
        cost_tracker.postgres.execute = AsyncMock(return_value=None)
        
        await cost_tracker.track_resource_usage(
            tenant_id="test-tenant-123",
            resource_type="compute",
            metric_name="cpu_hours",
            metric_value=10.5,
            unit="hours"
        )
        
        cost_tracker.postgres.execute.assert_called_once()
        cost_tracker.metrics.increment_counter.assert_called()
    
    async def test_allocate_cost(self, cost_tracker):
        """Test allocating cost to tenant"""
        cost_tracker.postgres.execute = AsyncMock(return_value=None)
        
        await cost_tracker.allocate_cost(
            tenant_id="test-tenant-123",
            cost_type=CostType.COMPUTE,
            service_name="api",
            amount=100.50,
            date=date.today()
        )
        
        cost_tracker.postgres.execute.assert_called_once()
        cost_tracker.metrics.increment_counter.assert_called()
    
    async def test_allocate_cost_default_date(self, cost_tracker):
        """Test allocating cost with default date"""
        cost_tracker.postgres.execute = AsyncMock(return_value=None)
        
        await cost_tracker.allocate_cost(
            tenant_id="test-tenant-123",
            cost_type=CostType.STORAGE,
            service_name="database",
            amount=50.25
        )
        
        # Verify execute was called
        cost_tracker.postgres.execute.assert_called_once()
    
    async def test_get_tenant_costs(self, cost_tracker):
        """Test getting costs for tenant"""
        mock_rows = [
            {
                "allocation_id": "alloc-1",
                "tenant_id": "test-tenant-123",
                "date": date.today(),
                "cost_type": "compute",
                "service_name": "api",
                "amount": 100.50,
                "currency": "USD",
                "metadata": {}
            }
        ]
        cost_tracker.postgres.fetch = AsyncMock(return_value=mock_rows)
        
        costs = await cost_tracker.get_tenant_costs("test-tenant-123")
        
        assert len(costs) == 1
        assert isinstance(costs[0], CostAllocation)
        assert costs[0].allocation_id == "alloc-1"
        assert costs[0].amount == 100.50
    
    async def test_get_tenant_costs_with_date_range(self, cost_tracker):
        """Test getting costs with date range"""
        mock_rows = []
        cost_tracker.postgres.fetch = AsyncMock(return_value=mock_rows)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        costs = await cost_tracker.get_tenant_costs(
            "test-tenant-123",
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(costs) == 0
        cost_tracker.postgres.fetch.assert_called_once()
    
    async def test_get_total_cost(self, cost_tracker):
        """Test getting total cost for tenant"""
        cost_tracker.postgres.fetchval = AsyncMock(return_value=250.75)
        
        total = await cost_tracker.get_total_cost("test-tenant-123")
        
        assert total == 250.75
        cost_tracker.postgres.fetchval.assert_called_once()
    
    async def test_get_total_cost_zero(self, cost_tracker):
        """Test getting total cost when no costs exist"""
        cost_tracker.postgres.fetchval = AsyncMock(return_value=None)
        
        total = await cost_tracker.get_total_cost("test-tenant-123")
        
        assert total == 0.0

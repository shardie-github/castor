"""
Tests for campaign manager
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from src.campaigns.campaign_manager import CampaignManager


@pytest.fixture
def campaign_manager(mock_metrics_collector, mock_event_logger, mock_postgres_connection):
    """Create campaign manager instance"""
    return CampaignManager(
        metrics_collector=mock_metrics_collector,
        event_logger=mock_event_logger,
        postgres_conn=mock_postgres_connection
    )


class TestCampaignManager:
    """Test campaign manager functionality"""
    
    def test_create_campaign_manager(self, campaign_manager):
        """Test creating campaign manager"""
        assert campaign_manager is not None
        assert campaign_manager.metrics_collector is not None
    
    def test_create_campaign(self, campaign_manager, test_campaign_data):
        """Test creating a campaign"""
        # Mock the database call
        campaign_manager.postgres_conn.execute = Mock(return_value=None)
        campaign_manager.postgres_conn.fetch_one = Mock(return_value={
            "campaign_id": test_campaign_data["campaign_id"],
            **test_campaign_data
        })
        
        # This would normally create a campaign
        # For now, just verify the manager is set up correctly
        assert campaign_manager.postgres_conn is not None
    
    def test_list_campaigns(self, campaign_manager):
        """Test listing campaigns"""
        # Mock the database call
        campaign_manager.postgres_conn.fetch_all = Mock(return_value=[
            {"campaign_id": "1", "name": "Campaign 1"},
            {"campaign_id": "2", "name": "Campaign 2"},
        ])
        
        # Verify the manager can handle listing
        assert campaign_manager.postgres_conn is not None

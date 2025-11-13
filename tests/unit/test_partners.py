"""
Unit tests for Partnership Tools
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.partners.referral import ReferralProgram, ReferralStatus
from src.partners.marketplace import MarketplaceManager, MarketplaceType, ListingStatus


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection"""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.fetch_one = AsyncMock()
    mock.fetch_all = AsyncMock()
    return mock


@pytest.fixture
def mock_metrics():
    """Mock metrics collector"""
    mock = MagicMock()
    mock.increment_counter = MagicMock()
    return mock


@pytest.fixture
def mock_events():
    """Mock event logger"""
    mock = MagicMock()
    mock.log_event = MagicMock()
    return mock


@pytest.fixture
def referral_program(mock_postgres, mock_metrics, mock_events):
    """Create ReferralProgram instance"""
    return ReferralProgram(
        postgres_conn=mock_postgres,
        metrics_collector=mock_metrics,
        event_logger=mock_events
    )


@pytest.fixture
def marketplace_manager(mock_postgres, mock_metrics, mock_events):
    """Create MarketplaceManager instance"""
    return MarketplaceManager(
        postgres_conn=mock_postgres,
        metrics_collector=mock_metrics,
        event_logger=mock_events
    )


@pytest.mark.asyncio
async def test_create_referral(referral_program, mock_postgres):
    """Test creating a referral"""
    mock_postgres.execute = AsyncMock()
    
    referral = await referral_program.create_referral(
        referrer_id="partner-123",
        first_year_rate=0.20,
        recurring_rate=0.10
    )
    
    assert referral.referral_id is not None
    assert referral.referrer_id == "partner-123"
    assert referral.first_year_commission_rate == 0.20
    assert referral.recurring_commission_rate == 0.10
    assert referral.status == ReferralStatus.PENDING
    assert referral.referral_code is not None
    assert mock_postgres.execute.called


@pytest.mark.asyncio
async def test_track_referral_conversion(referral_program, mock_postgres):
    """Test tracking referral conversion"""
    # Mock get_referral_by_code
    mock_row = {
        "referral_id": "ref-123",
        "referrer_id": "partner-123",
        "referred_customer_id": None,
        "referral_code": "REF12345",
        "referral_link": "https://app.example.com/signup?ref=REF12345",
        "status": "pending",
        "first_year_commission_rate": 0.20,
        "recurring_commission_rate": 0.10,
        "total_commission_earned": 0.0,
        "created_at": datetime.utcnow(),
        "converted_at": None,
        "metadata": {}
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    mock_postgres.execute = AsyncMock()
    
    referral = await referral_program.track_referral_conversion(
        referral_code="REF12345",
        customer_id="customer-456",
        customer_revenue=1000.0
    )
    
    assert referral is not None
    assert referral.referred_customer_id == "customer-456"
    assert referral.status == ReferralStatus.ACTIVE
    assert referral.converted_at is not None


@pytest.mark.asyncio
async def test_calculate_commission(referral_program, mock_postgres):
    """Test commission calculation"""
    # Mock get_referral
    mock_row = {
        "referral_id": "ref-123",
        "referrer_id": "partner-123",
        "referred_customer_id": "customer-456",
        "referral_code": "REF12345",
        "referral_link": "https://app.example.com/signup?ref=REF12345",
        "status": "active",
        "first_year_commission_rate": 0.20,
        "recurring_commission_rate": 0.10,
        "total_commission_earned": 0.0,
        "created_at": datetime.utcnow(),
        "converted_at": datetime.utcnow(),
        "metadata": {}
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    mock_postgres.execute = AsyncMock()
    
    commission = await referral_program.calculate_commission(
        referral_id="ref-123",
        revenue=1000.0,
        is_first_year=True
    )
    
    assert commission == 200.0  # 20% of 1000


@pytest.mark.asyncio
async def test_create_marketplace_listing(marketplace_manager, mock_postgres):
    """Test creating marketplace listing"""
    mock_postgres.execute = AsyncMock()
    
    listing = await marketplace_manager.create_listing(
        marketplace_type=MarketplaceType.SHOPIFY,
        app_name="Podcast Analytics",
        app_description="Analytics for podcasts",
        revenue_share_rate=0.20
    )
    
    assert listing.listing_id is not None
    assert listing.marketplace_type == MarketplaceType.SHOPIFY
    assert listing.app_name == "Podcast Analytics"
    assert listing.revenue_share_rate == 0.20
    assert listing.status == ListingStatus.DRAFT
    assert mock_postgres.execute.called


@pytest.mark.asyncio
async def test_track_marketplace_install(marketplace_manager, mock_postgres):
    """Test tracking marketplace install"""
    # Mock get_listing
    mock_row = {
        "listing_id": "listing-123",
        "marketplace_type": "shopify",
        "app_id": None,
        "app_name": "Podcast Analytics",
        "app_description": "Analytics",
        "status": "live",
        "revenue_share_rate": 0.20,
        "total_revenue": 0.0,
        "total_installs": 0,
        "created_at": datetime.utcnow(),
        "published_at": datetime.utcnow(),
        "metadata": {}
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    mock_postgres.execute = AsyncMock()
    
    await marketplace_manager.track_install(
        listing_id="listing-123",
        customer_id="customer-456",
        revenue=100.0
    )
    
    assert mock_postgres.execute.called

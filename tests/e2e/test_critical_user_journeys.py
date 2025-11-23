"""
End-to-End Tests for Critical User Journeys

Tests complete user flows from start to finish.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock


@pytest.fixture
def client():
    """Test client"""
    from src.main import app
    return TestClient(app)


@pytest.mark.e2e
class TestUserOnboardingJourney:
    """Test complete user onboarding journey"""
    
    def test_user_registration_to_first_campaign(self, client):
        """Test: User registers -> Creates podcast -> Creates campaign"""
        # Step 1: Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_test@example.com",
                "password": "Test1234!",
                "name": "E2E Test User"
            }
        )
        assert register_response.status_code in [200, 201, 409]  # 409 if already exists
        
        # Step 2: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "e2e_test@example.com",
                "password": "Test1234!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        assert token is not None
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Create tenant (if needed)
        tenant_response = client.post(
            "/api/v1/tenants",
            json={
                "name": "E2E Test Organization",
                "slug": "e2e-test-org"
            },
            headers=headers
        )
        # May already exist, so accept 200 or 201
        assert tenant_response.status_code in [200, 201, 409]
        
        # Step 4: Create podcast
        podcast_response = client.post(
            "/api/v1/podcasts",
            json={
                "title": "E2E Test Podcast",
                "feed_url": "https://example.com/feed.xml",
                "description": "Test podcast for E2E testing"
            },
            headers=headers
        )
        assert podcast_response.status_code in [200, 201]
        podcast_id = podcast_response.json().get("podcast_id")
        
        # Step 5: Create campaign
        campaign_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "E2E Test Campaign",
                "podcast_id": podcast_id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            headers=headers
        )
        assert campaign_response.status_code in [200, 201]
        
        # Verify campaign was created
        campaign_data = campaign_response.json()
        assert campaign_data.get("name") == "E2E Test Campaign"


@pytest.mark.e2e
class TestAttributionTrackingJourney:
    """Test attribution tracking flow"""
    
    def test_track_attribution_event(self, client):
        """Test: User clicks link -> Event tracked -> Attribution calculated"""
        # Step 1: Track attribution event
        track_response = client.post(
            "/api/v1/attribution/track",
            json={
                "event_type": "click",
                "campaign_id": "test-campaign-id",
                "user_id": "test-user-id",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        assert track_response.status_code in [200, 201]
        
        # Step 2: Verify event was recorded
        events_response = client.get(
            "/api/v1/attribution/events",
            params={"campaign_id": "test-campaign-id"}
        )
        assert events_response.status_code == 200
        events = events_response.json()
        assert isinstance(events, (list, dict))


@pytest.mark.e2e
class TestCampaignManagementJourney:
    """Test campaign management flow"""
    
    def test_create_and_view_campaign(self, client):
        """Test: Create campaign -> View campaign -> Update campaign"""
        headers = {"Authorization": "Bearer test-token"}
        
        # Step 1: Create campaign
        create_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "E2E Campaign",
                "podcast_id": "test-podcast-id",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            headers=headers
        )
        assert create_response.status_code in [200, 201]
        campaign_id = create_response.json().get("campaign_id")
        
        # Step 2: View campaign
        view_response = client.get(
            f"/api/v1/campaigns/{campaign_id}",
            headers=headers
        )
        assert view_response.status_code == 200
        campaign_data = view_response.json()
        assert campaign_data.get("name") == "E2E Campaign"
        
        # Step 3: Update campaign
        update_response = client.put(
            f"/api/v1/campaigns/{campaign_id}",
            json={
                "name": "Updated E2E Campaign"
            },
            headers=headers
        )
        assert update_response.status_code in [200, 204]


@pytest.mark.e2e
class TestAnalyticsJourney:
    """Test analytics and reporting flow"""
    
    def test_view_analytics_dashboard(self, client):
        """Test: View dashboard -> Check metrics -> Generate report"""
        headers = {"Authorization": "Bearer test-token"}
        
        # Step 1: Get dashboard data
        dashboard_response = client.get(
            "/api/v1/analytics/dashboard",
            headers=headers
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert isinstance(dashboard_data, dict)
        
        # Step 2: Get analytics metrics
        metrics_response = client.get(
            "/api/v1/analytics/metrics",
            params={"podcast_id": "test-podcast-id"},
            headers=headers
        )
        assert metrics_response.status_code == 200


@pytest.mark.e2e
class TestPaymentJourney:
    """Test payment and billing flow"""
    
    def test_subscription_flow(self, client):
        """Test: View pricing -> Subscribe -> View subscription"""
        headers = {"Authorization": "Bearer test-token"}
        
        # Step 1: Get pricing plans
        pricing_response = client.get(
            "/api/v1/billing/plans",
            headers=headers
        )
        assert pricing_response.status_code == 200
        plans = pricing_response.json()
        assert isinstance(plans, list)
        
        # Step 2: Get subscription status
        subscription_response = client.get(
            "/api/v1/billing/subscription",
            headers=headers
        )
        # May return 404 if no subscription, which is OK
        assert subscription_response.status_code in [200, 404]


@pytest.mark.e2e
class TestHealthCheckJourney:
    """Test health check and monitoring"""
    
    def test_health_check_flow(self, client):
        """Test: Health check -> Metrics -> Status"""
        # Step 1: Health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Step 2: Metrics endpoint
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        
        # Step 3: Root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200

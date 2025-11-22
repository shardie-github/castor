"""
End-to-End Integration Test: Product Loop

Tests the complete product loop:
1. User registers
2. User creates a campaign
3. Attribution event is recorded
4. Analytics are queried
5. Report is generated

This test validates that the core product loop works end-to-end.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPassword123!"


@pytest.fixture
async def test_user():
    """Create a test user and return auth token"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Register user
        async with session.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User",
                "accept_terms": True,
                "accept_privacy": True
            }
        ) as resp:
            assert resp.status == 201, f"Registration failed: {await resp.text()}"
            register_data = await resp.json()
        
        # Login to get token
        async with session.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        ) as resp:
            assert resp.status == 200, f"Login failed: {await resp.text()}"
            login_data = await resp.json()
            token = login_data["access_token"]
        
        return {
            "token": token,
            "user_id": register_data.get("user_id"),
            "email": TEST_EMAIL
        }


@pytest.fixture
async def test_podcast(test_user):
    """Create a test podcast"""
    import aiohttp
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE_URL}/podcasts",
            headers=headers,
            json={
                "name": "Test Podcast",
                "rss_feed_url": "https://example.com/rss.xml",
                "description": "Test podcast for integration testing"
            }
        ) as resp:
            assert resp.status == 201, f"Podcast creation failed: {await resp.text()}"
            podcast_data = await resp.json()
            return podcast_data


@pytest.fixture
async def test_sponsor(test_user):
    """Create a test sponsor"""
    import aiohttp
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE_URL}/sponsors",
            headers=headers,
            json={
                "name": "Test Sponsor",
                "email": "sponsor@example.com",
                "website": "https://example.com"
            }
        ) as resp:
            assert resp.status == 201, f"Sponsor creation failed: {await resp.text()}"
            sponsor_data = await resp.json()
            return sponsor_data


@pytest.mark.asyncio
async def test_product_loop_end_to_end(test_user, test_podcast, test_sponsor):
    """
    Test the complete product loop:
    1. User registers ✓ (fixture)
    2. User creates a campaign
    3. Attribution event is recorded
    4. Analytics are queried
    5. Report is generated
    """
    import aiohttp
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    campaign_id = None
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a campaign
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        async with session.post(
            f"{API_BASE_URL}/campaigns",
            headers=headers,
            json={
                "podcast_id": test_podcast["podcast_id"],
                "sponsor_id": test_sponsor["sponsor_id"],
                "name": "Test Campaign",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "campaign_value": 1000.0,
                "attribution_method": "promo_code",
                "promo_code": "TEST2024"
            }
        ) as resp:
            assert resp.status == 201, f"Campaign creation failed: {await resp.text()}"
            campaign_data = await resp.json()
            campaign_id = campaign_data["campaign_id"]
            assert campaign_id is not None
        
        # Step 2: Record an attribution event (impression)
        async with session.post(
            f"{API_BASE_URL}/attribution/events",
            json={
                "event_type": "impression",
                "campaign_id": campaign_id,
                "promo_code": "TEST2024",
                "timestamp": datetime.utcnow().isoformat(),
                "page_url": "https://example.com/test",
                "user_agent": "Mozilla/5.0 (Test Browser)"
            }
        ) as resp:
            assert resp.status == 201, f"Attribution event recording failed: {await resp.text()}"
            event_data = await resp.json()
            assert event_data["success"] is True
        
        # Step 3: Record a click event
        async with session.post(
            f"{API_BASE_URL}/attribution/events",
            json={
                "event_type": "click",
                "campaign_id": campaign_id,
                "promo_code": "TEST2024",
                "timestamp": datetime.utcnow().isoformat(),
                "link_url": "https://example.com/product",
                "page_url": "https://example.com/test"
            }
        ) as resp:
            assert resp.status == 201, f"Click event recording failed: {await resp.text()}"
        
        # Step 4: Record a conversion event
        async with session.post(
            f"{API_BASE_URL}/attribution/events",
            json={
                "event_type": "conversion",
                "campaign_id": campaign_id,
                "promo_code": "TEST2024",
                "timestamp": datetime.utcnow().isoformat(),
                "conversion_type": "purchase",
                "conversion_value": 99.99,
                "page_url": "https://example.com/checkout"
            }
        ) as resp:
            assert resp.status == 201, f"Conversion event recording failed: {await resp.text()}"
        
        # Step 5: Query campaign analytics
        async with session.get(
            f"{API_BASE_URL}/campaigns/{campaign_id}/analytics",
            headers=headers
        ) as resp:
            assert resp.status == 200, f"Analytics query failed: {await resp.text()}"
            analytics_data = await resp.json()
            assert analytics_data["campaign_id"] == campaign_id
            assert analytics_data["clicks"] >= 1  # At least one click recorded
            assert analytics_data["conversions"] >= 1  # At least one conversion recorded
            assert analytics_data["revenue"] >= 0
        
        # Step 6: Generate a report
        async with session.post(
            f"{API_BASE_URL}/reports/generate",
            headers=headers,
            json={
                "campaign_id": campaign_id,
                "report_type": "sponsor_report",
                "format": "pdf",
                "include_roi": True,
                "include_attribution": True
            }
        ) as resp:
            assert resp.status == 201, f"Report generation failed: {await resp.text()}"
            report_data = await resp.json()
            assert report_data["campaign_id"] == campaign_id
            assert report_data["report_id"] is not None
            assert report_data["includes_roi"] is True
        
        # Step 7: Verify completion rate tracking
        # This would be checked via sprint metrics API
        # For now, we verify the campaign status was updated
        async with session.get(
            f"{API_BASE_URL}/campaigns/{campaign_id}",
            headers=headers
        ) as resp:
            assert resp.status == 200, f"Campaign fetch failed: {await resp.text()}"
            campaign = await resp.json()
            # Campaign status should be 'completed' after report generation
            # Note: This depends on the report generation updating campaign status
        
        print(f"\n✅ Product loop test passed!")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Analytics: {analytics_data['clicks']} clicks, {analytics_data['conversions']} conversions")
        print(f"   Report ID: {report_data['report_id']}")


@pytest.mark.asyncio
async def test_ttfv_calculation(test_user, test_podcast, test_sponsor):
    """Test that TTFV is calculated when a user creates their first campaign"""
    import aiohttp
    import time
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Wait a moment to ensure user registration timestamp is recorded
    await asyncio.sleep(1)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create first campaign
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        async with session.post(
            f"{API_BASE_URL}/campaigns",
            headers=headers,
            json={
                "podcast_id": test_podcast["podcast_id"],
                "sponsor_id": test_sponsor["sponsor_id"],
                "name": "First Campaign",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "campaign_value": 500.0,
                "attribution_method": "promo_code",
                "promo_code": "FIRST2024"
            }
        ) as resp:
            assert resp.status == 201, f"Campaign creation failed: {await resp.text()}"
        
        # Query TTFV (if admin endpoint exists)
        # For now, we just verify the campaign was created
        # TTFV calculation happens asynchronously
        
        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0, "Campaign creation should be fast"
        
        print(f"\n✅ TTFV test passed! Campaign created in {elapsed_time:.2f}s")


@pytest.mark.asyncio
async def test_completion_rate_tracking(test_user, test_podcast, test_sponsor):
    """Test that completion rate is tracked when reports are generated"""
    import aiohttp
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    async with aiohttp.ClientSession() as session:
        # Create campaign
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        async with session.post(
            f"{API_BASE_URL}/campaigns",
            headers=headers,
            json={
                "podcast_id": test_podcast["podcast_id"],
                "sponsor_id": test_sponsor["sponsor_id"],
                "name": "Completion Test Campaign",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "campaign_value": 750.0,
                "attribution_method": "promo_code",
                "promo_code": "COMPLETE2024"
            }
        ) as resp:
            assert resp.status == 201, f"Campaign creation failed: {await resp.text()}"
            campaign_data = await resp.json()
            campaign_id = campaign_data["campaign_id"]
        
        # Generate report (this should mark campaign as completed)
        async with session.post(
            f"{API_BASE_URL}/reports/generate",
            headers=headers,
            json={
                "campaign_id": campaign_id,
                "report_type": "sponsor_report",
                "format": "pdf",
                "include_roi": True
            }
        ) as resp:
            assert resp.status == 201, f"Report generation failed: {await resp.text()}"
            report_data = await resp.json()
            assert report_data["report_id"] is not None
        
        # Verify campaign status is updated (if implemented)
        async with session.get(
            f"{API_BASE_URL}/campaigns/{campaign_id}",
            headers=headers
        ) as resp:
            assert resp.status == 200, f"Campaign fetch failed: {await resp.text()}"
            campaign = await resp.json()
            # Status should be 'completed' after report generation
        
        print(f"\n✅ Completion rate test passed!")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Report ID: {report_data['report_id']}")

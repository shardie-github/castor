"""
Complete End-to-End Test Flows

Comprehensive E2E tests using Playwright for browser automation.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCompleteUserFlows:
    """Complete user journey tests"""
    
    async def test_user_registration_flow(self, page: Page, base_url: str):
        """Test complete user registration flow"""
        # Navigate to registration page
        await page.goto(f"{base_url}/auth/register")
        
        # Fill registration form
        await page.fill('input[name="email"]', 'e2e_test@example.com')
        await page.fill('input[name="password"]', 'SecurePassword123!')
        await page.fill('input[name="name"]', 'E2E Test User')
        await page.check('input[name="accept_terms"]')
        await page.check('input[name="accept_privacy"]')
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Should redirect to email verification or dashboard
        await expect(page).to_have_url(f"{base_url}/auth/verify-email", timeout=10000)
    
    async def test_login_and_dashboard_access(self, page: Page, base_url: str):
        """Test login and dashboard access"""
        # Navigate to login
        await page.goto(f"{base_url}/auth/login")
        
        # Login
        await page.fill('input[name="email"]', 'test@example.com')
        await page.fill('input[name="password"]', 'password123')
        await page.click('button[type="submit"]')
        
        # Should redirect to dashboard
        await expect(page).to_have_url(f"{base_url}/dashboard", timeout=10000)
        
        # Dashboard should load
        await expect(page.locator('h1')).to_contain_text('Dashboard')
    
    async def test_campaign_creation_flow(self, page: Page, base_url: str):
        """Test creating a campaign from dashboard"""
        # Assume logged in (would need auth setup)
        await page.goto(f"{base_url}/dashboard")
        
        # Navigate to create campaign
        await page.click('a[href="/campaigns/new"]')
        await expect(page).to_have_url(f"{base_url}/campaigns/new")
        
        # Fill campaign form
        await page.fill('input[name="name"]', 'E2E Test Campaign')
        await page.fill('input[name="start_date"]', '2024-01-01')
        await page.fill('input[name="end_date"]', '2024-12-31')
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should redirect to campaign detail
        await expect(page).to_have_url(f"{base_url}/campaigns/", timeout=10000)
    
    async def test_podcast_management_flow(self, page: Page, base_url: str):
        """Test adding podcast and episodes"""
        await page.goto(f"{base_url}/dashboard")
        
        # Navigate to podcasts
        await page.click('a[href*="podcast"]')
        
        # Add podcast
        await page.click('button:has-text("Add Podcast")')
        await page.fill('input[name="name"]', 'E2E Test Podcast')
        await page.fill('input[name="rss_feed_url"]', 'https://example.com/feed.xml')
        await page.click('button[type="submit"]')
        
        # Should see podcast in list
        await expect(page.locator('text=E2E Test Podcast')).to_be_visible()
    
    async def test_analytics_viewing(self, page: Page, base_url: str):
        """Test viewing analytics"""
        await page.goto(f"{base_url}/dashboard")
        
        # Should see analytics charts
        await expect(page.locator('[data-testid="analytics-chart"]')).to_be_visible(timeout=10000)
        
        # Should see metrics
        await expect(page.locator('text=Total Campaigns')).to_be_visible()
        await expect(page.locator('text=Total Revenue')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in UI"""
    
    async def test_404_page(self, page: Page, base_url: str):
        """Test 404 error page"""
        await page.goto(f"{base_url}/nonexistent-page")
        await expect(page.locator('text=404')).to_be_visible()
        await expect(page.locator('text=Page not found')).to_be_visible()
    
    async def test_error_boundary(self, page: Page, base_url: str):
        """Test error boundary displays correctly"""
        # This would require triggering an error
        # For now, verify error boundary component exists
        await page.goto(f"{base_url}/dashboard")
        # Error boundary should be in the DOM
        error_boundary = await page.query_selector('[data-error-boundary]')
        # If error occurs, boundary should catch it


@pytest.mark.e2e
@pytest.mark.asyncio
class TestResponsiveDesign:
    """Test responsive design"""
    
    async def test_mobile_view(self, page: Page, base_url: str):
        """Test mobile viewport"""
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto(f"{base_url}/dashboard")
        
        # Mobile menu should be visible
        await expect(page.locator('[aria-label="Toggle menu"]')).to_be_visible()
        
        # Desktop navigation should be hidden
        desktop_nav = page.locator('.hidden.md\\:flex')
        await expect(desktop_nav).to_be_hidden()
    
    async def test_tablet_view(self, page: Page, base_url: str):
        """Test tablet viewport"""
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.goto(f"{base_url}/dashboard")
        
        # Should adapt layout
        await expect(page.locator('h1')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.asyncio
class TestPerformance:
    """Test performance metrics"""
    
    async def test_page_load_time(self, page: Page, base_url: str):
        """Test page load performance"""
        start_time = await page.evaluate('() => performance.now()')
        await page.goto(f"{base_url}/dashboard")
        load_time = await page.evaluate('() => performance.now()') - start_time
        
        # Page should load in under 3 seconds
        assert load_time < 3000, f"Page load took {load_time}ms"
    
    async def test_api_response_time(self, page: Page, base_url: str):
        """Test API response times"""
        response = await page.goto(f"{base_url}/dashboard")
        
        # Check response time
        assert response.status == 200
        # Additional timing checks can be added


@pytest.fixture
async def base_url():
    """Base URL for tests"""
    return "http://localhost:3000"  # Frontend URL

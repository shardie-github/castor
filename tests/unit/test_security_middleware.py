"""
Unit tests for security middleware
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.security.middleware import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    WAFMiddleware,
)


@pytest.fixture
def mock_request():
    """Mock FastAPI request"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.url.query = ""
    request.url.scheme = "http"
    request.client.host = "127.0.0.1"
    request.headers = {}
    request.method = "GET"
    return request


@pytest.fixture
def mock_response():
    """Mock FastAPI response"""
    response = Mock(spec=Response)
    response.headers = {}
    response.status_code = 200
    return response


@pytest.mark.asyncio
async def test_security_headers_middleware(mock_request, mock_response):
    """Test security headers middleware"""
    async def call_next(request):
        return mock_response
    
    middleware = SecurityHeadersMiddleware(Mock())
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.enable_security_headers = True
        mock_config.x_content_type_options = "nosniff"
        mock_config.x_frame_options = "DENY"
        mock_config.x_xss_protection = "1; mode=block"
        mock_config.referrer_policy = "strict-origin-when-cross-origin"
        mock_config.permissions_policy = "geolocation=()"
        mock_config.content_security_policy = None
        mock_config.hsts_enabled = False
        
        response = await middleware.dispatch(mock_request, call_next)
        
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


@pytest.mark.asyncio
async def test_https_redirect_middleware(mock_request):
    """Test HTTPS redirect middleware"""
    async def call_next(request):
        return Mock(spec=Response)
    
    middleware = HTTPSRedirectMiddleware(Mock())
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.force_https = True
        mock_request.url.scheme = "http"
        mock_request.url.replace = Mock(return_value=Mock(scheme="https"))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        # Should redirect
        assert response.status_code == 301


@pytest.mark.asyncio
async def test_rate_limit_middleware(mock_request):
    """Test rate limit middleware"""
    async def call_next(request):
        response = Mock(spec=Response)
        response.headers = {}
        return response
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = RateLimitMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.rate_limit_enabled = True
        mock_config.rate_limit_per_minute = 60
        mock_config.rate_limit_per_hour = 1000
        
        # First request should pass
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 200
        
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_exceeded(mock_request):
    """Test rate limit exceeded"""
    async def call_next(request):
        response = Mock(spec=Response)
        response.headers = {}
        return response
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = RateLimitMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.rate_limit_enabled = True
        mock_config.rate_limit_per_minute = 1  # Very low limit
        mock_config.rate_limit_per_hour = 1
        
        # First request passes
        await middleware.dispatch(mock_request, call_next)
        
        # Second request should be blocked
        with pytest.raises(Exception):  # Should raise HTTPException
            await middleware.dispatch(mock_request, call_next)


@pytest.mark.asyncio
async def test_waf_middleware_sql_injection(mock_request):
    """Test WAF middleware blocking SQL injection"""
    async def call_next(request):
        return Mock(spec=Response)
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = WAFMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.waf_enabled = True
        mock_config.block_sql_injection = True
        
        mock_request.url.path = "/api/test'; DROP TABLE users--"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await middleware.dispatch(mock_request, call_next)


@pytest.mark.asyncio
async def test_waf_middleware_xss(mock_request):
    """Test WAF middleware blocking XSS"""
    async def call_next(request):
        return Mock(spec=Response)
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = WAFMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.waf_enabled = True
        mock_config.block_xss = True
        
        mock_request.url.path = "/api/test<script>alert('xss')</script>"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await middleware.dispatch(mock_request, call_next)


@pytest.mark.asyncio
async def test_waf_middleware_path_traversal(mock_request):
    """Test WAF middleware blocking path traversal"""
    async def call_next(request):
        return Mock(spec=Response)
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = WAFMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.waf_enabled = True
        mock_config.block_path_traversal = True
        
        mock_request.url.path = "/api/../../../etc/passwd"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await middleware.dispatch(mock_request, call_next)


@pytest.mark.asyncio
async def test_waf_middleware_disabled(mock_request):
    """Test WAF middleware when disabled"""
    async def call_next(request):
        response = Mock(spec=Response)
        return response
    
    mock_metrics = Mock()
    mock_events = Mock()
    
    middleware = WAFMiddleware(Mock(), mock_metrics, mock_events)
    
    with patch("src.security.middleware.security_config") as mock_config:
        mock_config.waf_enabled = False
        
        response = await middleware.dispatch(mock_request, call_next)
        assert response is not None

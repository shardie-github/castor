"""
Security Middleware

CORS, security headers, rate limiting, and WAF protection.
"""

import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
from collections import defaultdict
from datetime import datetime, timedelta

from src.config.security import security_config
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        if security_config.enable_security_headers:
            response.headers["X-Content-Type-Options"] = security_config.x_content_type_options
            response.headers["X-Frame-Options"] = security_config.x_frame_options
            response.headers["X-XSS-Protection"] = security_config.x_xss_protection
            response.headers["Referrer-Policy"] = security_config.referrer_policy
            response.headers["Permissions-Policy"] = security_config.permissions_policy
            
            if security_config.content_security_policy:
                response.headers["Content-Security-Policy"] = security_config.content_security_policy
            
            if security_config.hsts_enabled and security_config.force_https:
                response.headers["Strict-Transport-Security"] = security_config.strict_transport_security
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        if security_config.force_https:
            if request.url.scheme == "http":
                https_url = request.url.replace(scheme="https")
                return StarletteResponse(
                    status_code=301,
                    headers={"Location": str(https_url)}
                )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, metrics_collector: MetricsCollector, event_logger: EventLogger):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
        self.rate_limits: dict = defaultdict(lambda: {"requests": [], "blocked": 0})
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not security_config.rate_limit_enabled:
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        now = datetime.utcnow()
        
        # Clean old requests
        self._clean_old_requests(client_id, now)
        
        # Check rate limits
        if self._is_rate_limited(client_id, now):
            self.metrics_collector.increment_counter("rate_limit_exceeded_total", {
                "client_id": client_id[:10]  # Truncate for privacy
            })
            self.event_logger.log_event("rate_limit_exceeded", {
                "client_id": client_id[:10],
                "path": str(request.url.path)
            })
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record request
        self.rate_limits[client_id]["requests"].append(now)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id, now)
        response.headers["X-RateLimit-Limit"] = str(security_config.rate_limit_per_hour)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(hours=1)).timestamp()))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier"""
        # Check for API key first
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key:
            return f"api_key:{api_key[:20]}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    def _clean_old_requests(self, client_id: str, now: datetime):
        """Remove requests older than 1 hour"""
        cutoff = now - timedelta(hours=1)
        self.rate_limits[client_id]["requests"] = [
            req_time for req_time in self.rate_limits[client_id]["requests"]
            if req_time > cutoff
        ]
    
    def _is_rate_limited(self, client_id: str, now: datetime) -> bool:
        """Check if client is rate limited"""
        requests = self.rate_limits[client_id]["requests"]
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        minute_requests = [r for r in requests if r > minute_ago]
        if len(minute_requests) >= security_config.rate_limit_per_minute:
            return True
        
        # Check per-hour limit
        hour_ago = now - timedelta(hours=1)
        hour_requests = [r for r in requests if r > hour_ago]
        if len(hour_requests) >= security_config.rate_limit_per_hour:
            return True
        
        return False
    
    def _get_remaining_requests(self, client_id: str, now: datetime) -> int:
        """Get remaining requests in current window"""
        hour_ago = now - timedelta(hours=1)
        hour_requests = [r for r in self.rate_limits[client_id]["requests"] if r > hour_ago]
        return max(0, security_config.rate_limit_per_hour - len(hour_requests))


class WAFMiddleware(BaseHTTPMiddleware):
    """Web Application Firewall middleware"""
    
    def __init__(self, app, metrics_collector: MetricsCollector, event_logger: EventLogger):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not security_config.waf_enabled:
            return await call_next(request)
        
        # Check for malicious patterns
        if self._is_malicious(request):
            self.metrics_collector.increment_counter("waf_blocked_total", {
                "path": str(request.url.path)
            })
            self.event_logger.log_event("waf_blocked", {
                "path": str(request.url.path),
                "client": request.client.host if request.client else "unknown"
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request blocked by security policy"
            )
        
        return await call_next(request)
    
    def _is_malicious(self, request: Request) -> bool:
        """Check if request contains malicious patterns"""
        # Get all request data as string
        request_str = f"{request.url.path} {request.url.query} {request.headers}"
        
        # SQL Injection patterns
        if security_config.block_sql_injection:
            sql_patterns = [
                "'; DROP",
                "UNION SELECT",
                "1=1",
                "OR 1=1",
                "'; --",
                "EXEC(",
                "xp_cmdshell"
            ]
            if any(pattern.lower() in request_str.lower() for pattern in sql_patterns):
                return True
        
        # XSS patterns
        if security_config.block_xss:
            xss_patterns = [
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
                "onclick=",
                "eval(",
                "document.cookie"
            ]
            if any(pattern.lower() in request_str.lower() for pattern in xss_patterns):
                return True
        
        # Path traversal patterns
        if security_config.block_path_traversal:
            if "../" in request_str or "..\\" in request_str:
                return True
        
        # Command injection patterns
        if security_config.block_command_injection:
            cmd_patterns = [
                "; ls",
                "| cat",
                "`whoami`",
                "$(id)",
                "&& rm",
                "|| rm"
            ]
            if any(pattern.lower() in request_str.lower() for pattern in cmd_patterns):
                return True
        
        return False


def setup_security_middleware(app, metrics_collector: MetricsCollector, event_logger: EventLogger):
    """Setup all security middleware"""
    from src.config.security import security_config
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.cors_allowed_origins if security_config.cors_allowed_origins else ["*"],
        allow_credentials=security_config.cors_allow_credentials,
        allow_methods=security_config.cors_allowed_methods,
        allow_headers=security_config.cors_allowed_headers,
        max_age=security_config.cors_max_age,
    )
    
    # HTTPS redirect (should be first)
    if security_config.force_https:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # WAF (before rate limiting)
    if security_config.waf_enabled:
        app.add_middleware(WAFMiddleware, metrics_collector=metrics_collector, event_logger=event_logger)
    
    # Rate limiting
    if security_config.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware, metrics_collector=metrics_collector, event_logger=event_logger)

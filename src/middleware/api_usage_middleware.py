"""
DELTA:20251113_064143 API Usage Middleware

Middleware to track API calls for billing.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.monetization.api_usage_tracker import APIUsageTracker

logger = logging.getLogger(__name__)


class APIUsageMiddleware(BaseHTTPMiddleware):
    """DELTA:20251113_064143 API usage tracking middleware"""
    
    def __init__(self, app, postgres_conn: PostgresConnection, metrics_collector: MetricsCollector, event_logger: EventLogger):
        super().__init__(app)
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
        self.tracker = APIUsageTracker(postgres_conn, metrics_collector, event_logger)
    
    async def dispatch(self, request: Request, call_next):
        """Track API usage"""
        # Skip tracking for certain endpoints
        skip_paths = ['/health', '/metrics', '/docs', '/openapi.json', '/redoc']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Get tenant ID
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return await call_next(request)
        
        # Get API key ID if available
        api_key_id = getattr(request.state, 'api_key_id', None)
        
        # Track request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Track API call (async, don't wait)
            try:
                await self.tracker.track_api_call(
                    tenant_id=str(tenant_id),
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    api_key_id=str(api_key_id) if api_key_id else None
                )
            except Exception as e:
                logger.error(f"Failed to track API usage: {e}", exc_info=True)
            
            return response
        
        except Exception as e:
            # Track failed request
            response_time_ms = int((time.time() - start_time) * 1000)
            
            try:
                await self.tracker.track_api_call(
                    tenant_id=str(tenant_id),
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=500,
                    response_time_ms=response_time_ms,
                    api_key_id=str(api_key_id) if api_key_id else None
                )
            except Exception as track_error:
                logger.error(f"Failed to track API usage: {track_error}", exc_info=True)
            
            raise

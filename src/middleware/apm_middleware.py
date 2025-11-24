"""
APM Middleware for FastAPI

Tracks request performance and creates APM transactions.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

from src.telemetry.apm import get_apm

logger = logging.getLogger(__name__)


class APMMiddleware(BaseHTTPMiddleware):
    """APM middleware for FastAPI"""
    
    async def dispatch(self, request: Request, call_next):
        """Track request performance"""
        apm = get_apm()
        
        if not apm:
            return await call_next(request)
        
        # Create transaction name
        transaction_name = f"{request.method} {request.url.path}"
        
        # Track transaction
        with apm.transaction(transaction_name, "request") as transaction:
            # Set metadata
            transaction.set_metadata("method", request.method)
            transaction.set_metadata("path", str(request.url.path))
            transaction.set_metadata("client_ip", request.client.host if request.client else None)
            
            # Track request processing
            start_time = time.time()
            
            try:
                response = await call_next(request)
                
                # Track response
                transaction.set_metadata("status_code", response.status_code)
                transaction.finish("success" if response.status_code < 400 else "error")
                
                # Add performance headers
                duration = time.time() - start_time
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                
                return response
            except Exception as e:
                transaction.finish("error", e)
                raise

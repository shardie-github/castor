"""
Standardized Error Responses

Provides consistent error response formats across all API routes.
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from pydantic import BaseModel
from datetime import datetime


class ErrorDetail(BaseModel):
    """Error detail model"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = datetime.utcnow()
    path: Optional[str] = None
    request_id: Optional[str] = None


class APIError(HTTPException):
    """Custom API error with standardized format"""
    
    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        path: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.error = error
        self.message = message
        self.details = details or []
        self.path = path
        self.request_id = request_id
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": error,
                "message": message,
                "details": [d.dict() for d in details] if details else None,
                "timestamp": datetime.utcnow().isoformat(),
                "path": path,
                "request_id": request_id
            }
        )


class ValidationError(APIError):
    """Validation error (400)"""
    
    def __init__(self, message: str, details: Optional[List[ErrorDetail]] = None, **kwargs):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="validation_error",
            message=message,
            details=details,
            **kwargs
        )


class NotFoundError(APIError):
    """Not found error (404)"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None, **kwargs):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error="not_found",
            message=message,
            **kwargs
        )


class UnauthorizedError(APIError):
    """Unauthorized error (401)"""
    
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="unauthorized",
            message=message,
            **kwargs
        )


class ForbiddenError(APIError):
    """Forbidden error (403)"""
    
    def __init__(self, message: str = "Access forbidden", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error="forbidden",
            message=message,
            **kwargs
        )


class ConflictError(APIError):
    """Conflict error (409)"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error="conflict",
            message=message,
            **kwargs
        )


class RateLimitError(APIError):
    """Rate limit error (429)"""
    
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error="rate_limit_exceeded",
            message=message,
            **kwargs
        )


class InternalServerError(APIError):
    """Internal server error (500)"""
    
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="internal_server_error",
            message=message,
            **kwargs
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error (503)"""
    
    def __init__(self, message: str = "Service temporarily unavailable", **kwargs):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="service_unavailable",
            message=message,
            **kwargs
        )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 400,
    details: Optional[List[ErrorDetail]] = None,
    path: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": error_type,
        "message": message,
        "details": [d.dict() for d in details] if details else None,
        "timestamp": datetime.utcnow().isoformat(),
        "path": path,
        "request_id": request_id
    }

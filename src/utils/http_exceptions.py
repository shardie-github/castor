"""
Sanitized HTTP Exceptions

Provides sanitized HTTPException helpers that prevent information disclosure in production.
"""

import os
from fastapi import HTTPException, status
from src.utils.error_sanitizer import sanitize_http_exception_detail


def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def sanitized_http_exception(
    status_code: int,
    detail: str,
    headers: dict = None
) -> HTTPException:
    """
    Create an HTTPException with sanitized detail message.
    
    In production, error messages are sanitized to prevent information disclosure.
    """
    if is_production():
        detail = sanitize_http_exception_detail(detail)
    
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )


# Convenience functions for common HTTP exceptions
def bad_request(detail: str = "Bad request", headers: dict = None) -> HTTPException:
    """400 Bad Request"""
    return sanitized_http_exception(status.HTTP_400_BAD_REQUEST, detail, headers)


def unauthorized(detail: str = "Authentication required", headers: dict = None) -> HTTPException:
    """401 Unauthorized"""
    return sanitized_http_exception(status.HTTP_401_UNAUTHORIZED, detail, headers)


def forbidden(detail: str = "Permission denied", headers: dict = None) -> HTTPException:
    """403 Forbidden"""
    return sanitized_http_exception(status.HTTP_403_FORBIDDEN, detail, headers)


def not_found(detail: str = "Resource not found", headers: dict = None) -> HTTPException:
    """404 Not Found"""
    return sanitized_http_exception(status.HTTP_404_NOT_FOUND, detail, headers)


def conflict(detail: str = "Resource conflict", headers: dict = None) -> HTTPException:
    """409 Conflict"""
    return sanitized_http_exception(status.HTTP_409_CONFLICT, detail, headers)


def rate_limit_exceeded(retry_after: int = None, headers: dict = None) -> HTTPException:
    """429 Too Many Requests"""
    if headers is None:
        headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)
    return sanitized_http_exception(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Rate limit exceeded",
        headers
    )


def internal_error(detail: str = None, headers: dict = None) -> HTTPException:
    """500 Internal Server Error"""
    if detail is None:
        detail = "An internal error occurred" if is_production() else "Internal server error"
    return sanitized_http_exception(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, headers)


def service_unavailable(detail: str = "Service temporarily unavailable", headers: dict = None) -> HTTPException:
    """503 Service Unavailable"""
    return sanitized_http_exception(status.HTTP_503_SERVICE_UNAVAILABLE, detail, headers)

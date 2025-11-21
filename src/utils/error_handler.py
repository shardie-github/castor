"""
Standardized Error Handling

Provides consistent error handling across the application with proper
logging, user-friendly error messages, and security considerations.
"""

import os
import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error"""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error (400)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class AuthenticationError(AppError):
    """Authentication error (401)"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(AppError):
    """Authorization error (403)"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


class NotFoundError(AppError):
    """Not found error (404)"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND", 404)


class ConflictError(AppError):
    """Conflict error (409)"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)


class RateLimitError(AppError):
    """Rate limit error (429)"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429, details)


class ExternalServiceError(AppError):
    """External service error (502)"""
    
    def __init__(self, service: str, message: Optional[str] = None):
        msg = message or f"External service error: {service}"
        super().__init__(msg, "EXTERNAL_SERVICE_ERROR", 502, {"service": service})


def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def sanitize_error_message(error: Exception) -> str:
    """Sanitize error message for user display"""
    # Don't expose internal error details in production
    if is_production():
        # Return generic message for unexpected errors
        if isinstance(error, AppError):
            return error.message
        return "An error occurred. Please try again later."
    else:
        # In development, show full error
        return str(error)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application errors"""
    # Log error with context
    logger.error(
        f"Application error: {exc.code}",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    response_data = {
        "error": {
            "code": exc.code,
            "message": sanitize_error_message(exc),
        }
    }
    
    # Add details if available and not sensitive
    if exc.details and not is_production():
        response_data["error"]["details"] = exc.details
    
    # Add retry_after header for rate limit errors
    headers = {}
    if isinstance(exc, RateLimitError) and exc.details.get("retry_after"):
        headers["Retry-After"] = str(exc.details["retry_after"])
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
            }
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    # Log full error with stack trace
    logger.error(
        f"Unhandled error: {type(exc).__name__}",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )
    
    # In production, don't expose error details
    if is_production():
        message = "An internal error occurred. Please try again later."
        details = None
    else:
        message = str(exc)
        details = {
            "type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
    
    response_data = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": message,
        }
    }
    
    if details:
        response_data["error"]["details"] = details
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


def register_error_handlers(app):
    """Register error handlers with FastAPI app"""
    from fastapi import FastAPI
    
    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI instance")
    
    # Register custom exception handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    
    logger.info("Error handlers registered")


def create_error_response(
    code: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                **(details or {}),
            }
        }
    )

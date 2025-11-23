"""
Unit tests for error handling
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.error_handler import (
    AppError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    app_error_handler,
    validation_error_handler,
    generic_error_handler,
    sanitize_error_message,
    is_production,
)


def test_app_error():
    """Test AppError creation"""
    error = AppError("Test error", "TEST_ERROR", 400)
    
    assert error.message == "Test error"
    assert error.code == "TEST_ERROR"
    assert error.status_code == 400
    assert str(error) == "Test error"


def test_validation_error():
    """Test ValidationError"""
    error = ValidationError("Invalid input")
    
    assert error.message == "Invalid input"
    assert error.code == "VALIDATION_ERROR"
    assert error.status_code == 400


def test_authentication_error():
    """Test AuthenticationError"""
    error = AuthenticationError("Not authenticated")
    
    assert error.message == "Not authenticated"
    assert error.code == "AUTHENTICATION_ERROR"
    assert error.status_code == 401


def test_authorization_error():
    """Test AuthorizationError"""
    error = AuthorizationError("Permission denied")
    
    assert error.message == "Permission denied"
    assert error.code == "AUTHORIZATION_ERROR"
    assert error.status_code == 403


def test_not_found_error():
    """Test NotFoundError"""
    error = NotFoundError("Resource", "123")
    
    assert "Resource" in error.message
    assert "123" in error.message
    assert error.code == "NOT_FOUND"
    assert error.status_code == 404


def test_conflict_error():
    """Test ConflictError"""
    error = ConflictError("Resource already exists")
    
    assert error.message == "Resource already exists"
    assert error.code == "CONFLICT"
    assert error.status_code == 409


def test_rate_limit_error():
    """Test RateLimitError"""
    error = RateLimitError("Rate limit exceeded", retry_after=60)
    
    assert error.message == "Rate limit exceeded"
    assert error.code == "RATE_LIMIT_EXCEEDED"
    assert error.status_code == 429
    assert error.details["retry_after"] == 60


def test_external_service_error():
    """Test ExternalServiceError"""
    error = ExternalServiceError("stripe")
    
    assert "stripe" in error.message.lower()
    assert error.code == "EXTERNAL_SERVICE_ERROR"
    assert error.status_code == 502
    assert error.details["service"] == "stripe"


@pytest.mark.asyncio
async def test_app_error_handler(mock_event_logger):
    """Test app error handler"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.method = "GET"
    
    error = AppError("Test error", "TEST_ERROR", 400, {"key": "value"})
    
    with patch("src.utils.error_handler.is_production", return_value=False):
        response = await app_error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        content = response.body.decode()
        assert "TEST_ERROR" in content
        assert "Test error" in content


@pytest.mark.asyncio
async def test_app_error_handler_production(mock_event_logger):
    """Test app error handler in production (sanitized)"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.method = "GET"
    
    error = AppError("Test error", "TEST_ERROR", 400)
    
    with patch("src.utils.error_handler.is_production", return_value=True):
        response = await app_error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_validation_error_handler():
    """Test validation error handler"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.method = "POST"
    
    errors = [
        {"loc": ("body", "email"), "msg": "Invalid email", "type": "value_error"}
    ]
    validation_error = RequestValidationError(errors)
    
    response = await validation_error_handler(request, validation_error)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generic_error_handler():
    """Test generic error handler"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.method = "GET"
    
    error = ValueError("Unexpected error")
    
    with patch("src.utils.error_handler.is_production", return_value=False):
        response = await generic_error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generic_error_handler_production():
    """Test generic error handler in production"""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.method = "GET"
    
    error = ValueError("Unexpected error")
    
    with patch("src.utils.error_handler.is_production", return_value=True):
        response = await generic_error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        # In production, should not expose error details
        content = response.body.decode()
        assert "Unexpected error" not in content


def test_sanitize_error_message_production():
    """Test error message sanitization in production"""
    error = ValueError("Internal error details")
    
    with patch("src.utils.error_handler.is_production", return_value=True):
        message = sanitize_error_message(error)
        assert "Internal error details" not in message
        assert "An error occurred" in message


def test_sanitize_error_message_development():
    """Test error message in development"""
    error = ValueError("Internal error details")
    
    with patch("src.utils.error_handler.is_production", return_value=False):
        message = sanitize_error_message(error)
        assert "Internal error details" in message


def test_sanitize_error_message_app_error():
    """Test sanitization with AppError"""
    error = AppError("User-friendly error", "TEST_ERROR", 400)
    
    with patch("src.utils.error_handler.is_production", return_value=True):
        message = sanitize_error_message(error)
        assert message == "User-friendly error"

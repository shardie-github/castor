"""
Utility modules for common functionality.

This package provides:
- Retry logic with exponential backoff
- Standardized error handling
- Circuit breaker pattern (to be implemented)
- Timeout decorators (to be implemented)
"""

from src.utils.retry import (
    retry_with_backoff,
    retry_decorator,
    RetryConfig,
    RetryExhausted,
    get_retry_config,
    RETRY_CONFIGS,
)

from src.utils.error_handler import (
    AppError,
    ValidationError as AppValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    register_error_handlers,
    create_error_response,
)

__all__ = [
    # Retry
    "retry_with_backoff",
    "retry_decorator",
    "RetryConfig",
    "RetryExhausted",
    "get_retry_config",
    "RETRY_CONFIGS",
    # Error handling
    "AppError",
    "AppValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ExternalServiceError",
    "register_error_handlers",
    "create_error_response",
]

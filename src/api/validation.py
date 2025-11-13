"""
API Request Validation and Error Handling

Enhanced validation, user-friendly error messages, and input sanitization.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import re


class ValidationError(BaseModel):
    """Structured validation error"""
    field: str
    message: str
    code: str
    value: Any = None


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: bool = True
    message: str
    code: str
    details: Optional[List[ValidationError]] = None
    timestamp: str
    path: str


def create_error_response(
    message: str,
    code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[List[ValidationError]] = None,
    path: str = ""
) -> HTTPException:
    """Create a standardized error response"""
    from datetime import datetime
    
    error_response = ErrorResponse(
        error=True,
        message=message,
        code=code,
        details=details or [],
        timestamp=datetime.utcnow().isoformat(),
        path=path
    )
    
    return HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )


class EmailValidator:
    """Email validation"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @classmethod
    def validate(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def sanitize(cls, email: str) -> str:
        """Sanitize email input"""
        return email.strip().lower()


class URLValidator:
    """URL validation"""
    
    URL_PATTERN = re.compile(
        r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?$'
    )
    
    @classmethod
    def validate(cls, url: str) -> bool:
        """Validate URL format"""
        if not url or len(url) > 2048:
            return False
        return bool(cls.URL_PATTERN.match(url))
    
    @classmethod
    def sanitize(cls, url: str) -> str:
        """Sanitize URL input"""
        return url.strip()


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Sanitize SQL input (basic protection)"""
        # Remove SQL injection patterns
        dangerous_patterns = [
            r"';",
            r"--",
            r"\/\*",
            r"\*\/",
            r"xp_",
            r"exec\(",
            r"union\s+select"
        ]
        
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized


# User-friendly error messages
ERROR_MESSAGES = {
    "VALIDATION_ERROR": "Please check your input and try again",
    "AUTHENTICATION_REQUIRED": "Please sign in to continue",
    "AUTHORIZATION_FAILED": "You don't have permission to perform this action",
    "NOT_FOUND": "The requested resource was not found",
    "RATE_LIMIT_EXCEEDED": "Too many requests. Please try again later",
    "INTERNAL_ERROR": "Something went wrong. Our team has been notified",
    "INVALID_EMAIL": "Please enter a valid email address",
    "INVALID_URL": "Please enter a valid URL",
    "REQUIRED_FIELD": "This field is required",
    "INVALID_FORMAT": "Invalid format. Please check your input",
    "DUPLICATE_ENTRY": "This entry already exists",
    "PAYMENT_FAILED": "Payment processing failed. Please check your payment method",
    "SUBSCRIPTION_EXPIRED": "Your subscription has expired. Please renew to continue",
    "QUOTA_EXCEEDED": "You've reached your usage limit. Please upgrade your plan"
}


def get_user_friendly_message(error_code: str, default: Optional[str] = None) -> str:
    """Get user-friendly error message"""
    return ERROR_MESSAGES.get(error_code, default or "An error occurred")


# Validation decorators
def validate_email(email: str) -> str:
    """Validate and sanitize email"""
    sanitized = EmailValidator.sanitize(email)
    if not EmailValidator.validate(sanitized):
        raise create_error_response(
            message=get_user_friendly_message("INVALID_EMAIL"),
            code="INVALID_EMAIL",
            path="email"
        )
    return sanitized


def validate_url(url: str) -> str:
    """Validate and sanitize URL"""
    sanitized = URLValidator.sanitize(url)
    if not URLValidator.validate(sanitized):
        raise create_error_response(
            message=get_user_friendly_message("INVALID_URL"),
            code="INVALID_URL",
            path="url"
        )
    return sanitized

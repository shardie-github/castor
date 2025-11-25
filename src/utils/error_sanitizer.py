"""
Error Message Sanitizer

Sanitizes error messages to prevent information disclosure in production.
"""

import os
import re
from typing import Any, Dict


def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def sanitize_error_detail(detail: Any) -> Any:
    """
    Sanitize error detail to remove sensitive information.
    
    Removes:
    - File paths
    - Line numbers
    - Stack traces
    - Database connection strings
    - API keys
    - Internal error types
    """
    if not is_production():
        return detail
    
    if isinstance(detail, str):
        # Remove file paths
        detail = re.sub(r'/[\w/.-]+\.py', '[file]', detail)
        # Remove line numbers
        detail = re.sub(r'line \d+', '[line]', detail)
        # Remove stack trace indicators
        detail = re.sub(r'Traceback.*', '', detail, flags=re.DOTALL)
        # Remove database connection strings
        detail = re.sub(r'postgresql://[^\s]+', '[database]', detail)
        detail = re.sub(r'redis://[^\s]+', '[cache]', detail)
        # Remove API keys (common patterns)
        detail = re.sub(r'(api[_-]?key|secret|token)\s*[:=]\s*[\w-]+', r'\1=[hidden]', detail, flags=re.IGNORECASE)
        # Remove email addresses (might be sensitive)
        detail = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', detail)
        # Remove UUIDs (might be sensitive)
        detail = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[id]', detail, flags=re.IGNORECASE)
        # Limit length
        if len(detail) > 200:
            detail = detail[:200] + "..."
        return detail
    elif isinstance(detail, dict):
        return {k: sanitize_error_detail(v) for k, v in detail.items()}
    elif isinstance(detail, list):
        return [sanitize_error_detail(item) for item in detail]
    else:
        return detail


def sanitize_http_exception_detail(detail: str) -> str:
    """
    Sanitize HTTPException detail message for production.
    
    Returns generic messages for common error types to prevent information disclosure.
    """
    if not is_production():
        return detail
    
    # Common error patterns that should be genericized
    generic_patterns = [
        (r'not found', 'Resource not found'),
        (r'permission denied|unauthorized|forbidden', 'Access denied'),
        (r'invalid|validation error', 'Invalid request'),
        (r'database|connection|query', 'Service temporarily unavailable'),
        (r'key|secret|token|password', 'Authentication error'),
    ]
    
    detail_lower = detail.lower()
    for pattern, generic_msg in generic_patterns:
        if re.search(pattern, detail_lower):
            return generic_msg
    
    # If no pattern matches, sanitize and return
    return sanitize_error_detail(detail)

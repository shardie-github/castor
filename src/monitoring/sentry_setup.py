"""
Sentry Error Tracking Setup

Configures Sentry for error tracking and performance monitoring.
"""

import logging
import os
from typing import Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
):
    """
    Initialize Sentry error tracking
    
    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name (defaults to ENVIRONMENT env var)
        release: Release version (defaults to VERSION env var)
        traces_sample_rate: Sample rate for performance traces (0.0 to 1.0)
        profiles_sample_rate: Sample rate for profiling (0.0 to 1.0)
    """
    if not SENTRY_AVAILABLE:
        logger.warning("sentry-sdk not installed. Install with: pip install sentry-sdk")
        return False
    
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("Sentry DSN not configured. Set SENTRY_DSN environment variable.")
        return False
    
    environment = environment or os.getenv("ENVIRONMENT", "development")
    release = release or os.getenv("VERSION", "unknown")
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions
            # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
            before_send=before_send_filter,
            # Ignore specific exceptions
            ignore_errors=[
                KeyboardInterrupt,
                SystemExit,
            ],
        )
        logger.info(f"Sentry initialized for environment: {environment}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}")
        return False


def before_send_filter(event, hint):
    """Filter events before sending to Sentry"""
    # Don't send events in development unless explicitly enabled
    if os.getenv("ENVIRONMENT") == "development" and not os.getenv("SENTRY_ENABLE_DEV"):
        return None
    
    # Filter out sensitive data
    if event.get("request"):
        # Remove sensitive headers
        if "headers" in event["request"]:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                event["request"]["headers"].pop(header, None)
    
    return event


def capture_exception(error: Exception, **kwargs):
    """Capture an exception in Sentry"""
    if SENTRY_AVAILABLE:
        sentry_sdk.capture_exception(error, **kwargs)


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message in Sentry"""
    if SENTRY_AVAILABLE:
        sentry_sdk.capture_message(message, level=level, **kwargs)


def set_user(user_id: Optional[str] = None, email: Optional[str] = None, **kwargs):
    """Set user context for Sentry"""
    if SENTRY_AVAILABLE:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            **kwargs
        })


def set_context(key: str, value: dict):
    """Set additional context for Sentry"""
    if SENTRY_AVAILABLE:
        sentry_sdk.set_context(key, value)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **kwargs):
    """Add a breadcrumb to Sentry"""
    if SENTRY_AVAILABLE:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            **kwargs
        )

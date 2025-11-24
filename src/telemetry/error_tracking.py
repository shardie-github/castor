"""
Enterprise-Grade Error Tracking

Integrates with Sentry, Rollbar, or custom error tracking services.
Provides structured error reporting with context, user information, and stack traces.
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ErrorTracker:
    """
    Enterprise error tracking with multiple backend support.
    
    Supports:
    - Sentry (primary)
    - Rollbar (fallback)
    - Custom webhook (fallback)
    - Structured logging (always)
    """
    
    def __init__(
        self,
        sentry_dsn: Optional[str] = None,
        rollbar_token: Optional[str] = None,
        webhook_url: Optional[str] = None,
        environment: str = "development",
        release: Optional[str] = None,
        enable_sentry: bool = True,
        enable_rollbar: bool = True,
    ):
        self.sentry_dsn = sentry_dsn
        self.rollbar_token = rollbar_token
        self.webhook_url = webhook_url
        self.environment = environment
        self.release = release or os.getenv("APP_VERSION", "unknown")
        
        # Initialize Sentry if available
        self.sentry_client = None
        if enable_sentry and sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                from sentry_sdk.integrations.redis import RedisIntegration
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment=environment,
                    release=release,
                    integrations=[
                        FastApiIntegration(),
                        SqlalchemyIntegration(),
                        RedisIntegration(),
                    ],
                    traces_sample_rate=0.1,  # 10% of transactions
                    profiles_sample_rate=0.1,  # 10% of transactions
                    before_send=self._before_send,
                )
                self.sentry_client = sentry_sdk
                logger.info("Sentry error tracking initialized")
            except ImportError:
                logger.warning("Sentry SDK not installed, skipping Sentry integration")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
        
        # Initialize Rollbar if available
        self.rollbar_client = None
        if enable_rollbar and rollbar_token:
            try:
                import rollbar
                rollbar.init(
                    rollbar_token,
                    environment=environment,
                    code_version=release,
                )
                self.rollbar_client = rollbar
                logger.info("Rollbar error tracking initialized")
            except ImportError:
                logger.warning("Rollbar SDK not installed, skipping Rollbar integration")
            except Exception as e:
                logger.error(f"Failed to initialize Rollbar: {e}")
    
    def _before_send(self, event, hint):
        """Filter sensitive data before sending to Sentry"""
        # Remove sensitive fields
        if "request" in event:
            if "headers" in event["request"]:
                sensitive_headers = ["authorization", "cookie", "x-api-key"]
                for header in sensitive_headers:
                    event["request"]["headers"].pop(header, None)
        
        return event
    
    def capture_exception(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        fingerprint: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Capture an exception with full context.
        
        Returns:
            Error ID if captured, None otherwise
        """
        error_id = None
        context = context or {}
        tags = tags or {}
        
        # Add stack trace
        context["stack_trace"] = traceback.format_exc()
        context["exception_type"] = type(exception).__name__
        context["exception_message"] = str(exception)
        
        # Capture in Sentry
        if self.sentry_client:
            try:
                with self.sentry_client.push_scope() as scope:
                    if user:
                        scope.user = user
                    if tags:
                        scope.set_tags(tags)
                    if context:
                        scope.set_context("custom", context)
                    if fingerprint:
                        scope.fingerprint = fingerprint
                    
                    error_id = self.sentry_client.capture_exception(exception)
            except Exception as e:
                logger.error(f"Failed to capture exception in Sentry: {e}")
        
        # Capture in Rollbar
        if self.rollbar_client:
            try:
                extra_data = {**context, "tags": tags}
                if user:
                    extra_data["user"] = user
                
                error_id = self.rollbar_client.report_exc_info(
                    sys.exc_info(),
                    level=severity.value,
                    extra_data=extra_data,
                    fingerprint_data=fingerprint,
                )
            except Exception as e:
                logger.error(f"Failed to capture exception in Rollbar: {e}")
        
        # Send to webhook
        if self.webhook_url:
            try:
                self._send_webhook({
                    "type": "exception",
                    "severity": severity.value,
                    "exception": {
                        "type": type(exception).__name__,
                        "message": str(exception),
                        "stack_trace": context.get("stack_trace"),
                    },
                    "context": context,
                    "user": user,
                    "tags": tags,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.error(f"Failed to send error to webhook: {e}")
        
        # Always log to structured logging
        logger.error(
            f"Exception captured: {type(exception).__name__}: {str(exception)}",
            extra={
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "severity": severity.value,
                "context": context,
                "user": user,
                "tags": tags,
                "error_id": error_id,
            }
        )
        
        return error_id
    
    def capture_message(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.INFO,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Capture a message/event"""
        error_id = None
        context = context or {}
        tags = tags or {}
        
        # Capture in Sentry
        if self.sentry_client:
            try:
                with self.sentry_client.push_scope() as scope:
                    if user:
                        scope.user = user
                    if tags:
                        scope.set_tags(tags)
                    if context:
                        scope.set_context("custom", context)
                    
                    error_id = self.sentry_client.capture_message(
                        message,
                        level=severity.value,
                    )
            except Exception as e:
                logger.error(f"Failed to capture message in Sentry: {e}")
        
        # Capture in Rollbar
        if self.rollbar_client:
            try:
                extra_data = {**context, "tags": tags}
                if user:
                    extra_data["user"] = user
                
                error_id = self.rollbar_client.report_message(
                    message,
                    level=severity.value,
                    extra_data=extra_data,
                )
            except Exception as e:
                logger.error(f"Failed to capture message in Rollbar: {e}")
        
        # Send to webhook
        if self.webhook_url:
            try:
                self._send_webhook({
                    "type": "message",
                    "severity": severity.value,
                    "message": message,
                    "context": context,
                    "user": user,
                    "tags": tags,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.error(f"Failed to send message to webhook: {e}")
        
        return error_id
    
    def _send_webhook(self, payload: Dict[str, Any]):
        """Send error to webhook"""
        import httpx
        
        try:
            httpx.post(
                self.webhook_url,
                json=payload,
                timeout=5.0,
            )
        except Exception as e:
            logger.error(f"Webhook request failed: {e}")
    
    def set_user(self, user_id: str, email: Optional[str] = None, **kwargs):
        """Set user context for error tracking"""
        user_data = {"id": user_id, **kwargs}
        if email:
            user_data["email"] = email
        
        if self.sentry_client:
            try:
                self.sentry_client.set_user(user_data)
            except Exception:
                pass
        
        if self.rollbar_client:
            try:
                self.rollbar_client.set_person(user_id, email, **kwargs)
            except Exception:
                pass
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ):
        """Add breadcrumb for error context"""
        if self.sentry_client:
            try:
                self.sentry_client.add_breadcrumb(
                    message=message,
                    category=category,
                    level=level,
                    data=data or {},
                )
            except Exception:
                pass


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def init_error_tracking(
    sentry_dsn: Optional[str] = None,
    rollbar_token: Optional[str] = None,
    webhook_url: Optional[str] = None,
    environment: str = "development",
    release: Optional[str] = None,
) -> ErrorTracker:
    """Initialize global error tracker"""
    global _error_tracker
    
    _error_tracker = ErrorTracker(
        sentry_dsn=sentry_dsn or os.getenv("SENTRY_DSN"),
        rollbar_token=rollbar_token or os.getenv("ROLLBAR_TOKEN"),
        webhook_url=webhook_url or os.getenv("ERROR_WEBHOOK_URL"),
        environment=environment,
        release=release,
    )
    
    return _error_tracker


def get_error_tracker() -> Optional[ErrorTracker]:
    """Get global error tracker instance"""
    return _error_tracker

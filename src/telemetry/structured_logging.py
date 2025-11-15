"""
Structured Logging

Provides structured logging with JSON output for better observability.
Integrates with OpenTelemetry for distributed tracing.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Structured logger with JSON output"""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add JSON formatter handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """Internal logging method"""
        log_data = {
            "message": message,
            "level": level.value,
            "logger": self.name,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if extra:
            log_data.update(extra)
        
        if exc_info:
            log_data["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exc()
            }
        
        # Add trace context if available
        trace_id = self._get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        log_method = getattr(self.logger, level.value.lower())
        log_method(json.dumps(log_data))
    
    def _get_trace_id(self) -> Optional[str]:
        """Get trace ID from OpenTelemetry context if available"""
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                return format(span.get_span_context().trace_id, '032x')
        except ImportError:
            pass
        return None
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, kwargs)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, message, kwargs, exc_info)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, kwargs, exc_info)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def get_logger(name: str, level: LogLevel = LogLevel.INFO) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name, level)

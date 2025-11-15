"""
OpenTelemetry Tracing

Provides distributed tracing with OpenTelemetry.
"""

import os
import asyncio
from typing import Optional
from functools import wraps
import logging

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not available - tracing disabled")


def setup_tracing(service_name: str = "podcast-analytics", otlp_endpoint: Optional[str] = None):
    """
    Setup OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP endpoint URL (e.g., http://localhost:4317)
    """
    if not OPENTELEMETRY_AVAILABLE:
        logging.warning("OpenTelemetry not available - skipping tracing setup")
        return
    
    # Get OTLP endpoint from environment if not provided
    if not otlp_endpoint:
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter if endpoint is configured
    if otlp_endpoint and otlp_endpoint != "disabled":
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument FastAPI
    try:
        FastAPIInstrumentor().instrument()
    except Exception as e:
        logging.warning(f"Failed to instrument FastAPI: {e}")
    
    # Instrument HTTP clients
    try:
        HTTPXClientInstrumentor().instrument()
    except Exception as e:
        logging.warning(f"Failed to instrument HTTPX: {e}")
    
    # Instrument asyncpg
    try:
        AsyncPGInstrumentor().instrument()
    except Exception as e:
        logging.warning(f"Failed to instrument AsyncPG: {e}")
    
    logging.info(f"OpenTelemetry tracing initialized for {service_name}")


def get_tracer(name: str):
    """Get a tracer instance"""
    if not OPENTELEMETRY_AVAILABLE:
        return None
    
    return trace.get_tracer(name)


def trace_function(name: Optional[str] = None):
    """
    Decorator to trace function execution.
    
    Usage:
        @trace_function("my_function")
        async def my_function():
            ...
    """
    def decorator(func):
        func_name = name or f"{func.__module__}.{func.__name__}"
        tracer = get_tracer(func.__module__)
        
        if tracer is None:
            return func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(func_name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(func_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

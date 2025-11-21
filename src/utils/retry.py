"""
Retry Logic with Exponential Backoff

Provides retry functionality for external API calls, database operations,
and other operations that may fail transiently.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Optional, Tuple, Any
from functools import wraps
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[type, ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback called on each retry (attempt_number, exception)
    
    Returns:
        Result of the function call
    
    Raises:
        RetryExhausted: If all retry attempts are exhausted
        Exception: The last exception raised by the function
    """
    delay = initial_delay
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                # Last attempt failed
                logger.error(
                    f"Retry exhausted after {max_retries + 1} attempts",
                    extra={
                        "function": func.__name__,
                        "attempts": attempt + 1,
                        "exception": str(e),
                    }
                )
                raise RetryExhausted(
                    f"Function {func.__name__} failed after {max_retries + 1} attempts"
                ) from e
            
            # Call retry callback if provided
            if on_retry:
                try:
                    if asyncio.iscoroutinefunction(on_retry):
                        await on_retry(attempt + 1, e)
                    else:
                        on_retry(attempt + 1, e)
                except Exception as callback_error:
                    logger.warning(f"Retry callback failed: {callback_error}")
            
            logger.warning(
                f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__}",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "delay": delay,
                    "exception": str(e),
                }
            )
            
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
    
    # Should never reach here, but type checker needs it
    if last_exception:
        raise last_exception
    raise RetryExhausted("Unexpected retry failure")


def retry_decorator(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[type, ...] = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Usage:
        @retry_decorator(max_retries=3, exceptions=(ConnectionError, TimeoutError))
        async def my_function():
            # ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async def wrapped():
                return await func(*args, **kwargs)
            return await retry_with_backoff(
                wrapped,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                max_delay=max_delay,
                exceptions=exceptions,
            )
        return wrapper
    return decorator


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        exceptions: Tuple[type, ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.exceptions = exceptions


# Pre-configured retry configs for common scenarios
RETRY_CONFIGS = {
    "external_api": RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(ConnectionError, TimeoutError, Exception),
    ),
    "database": RetryConfig(
        max_retries=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        exceptions=(ConnectionError, Exception),
    ),
    "payment": RetryConfig(
        max_retries=5,
        initial_delay=2.0,
        backoff_factor=2.0,
        exceptions=(Exception,),  # Retry all exceptions for payments
    ),
}


def get_retry_config(name: str) -> RetryConfig:
    """Get a pre-configured retry config by name"""
    return RETRY_CONFIGS.get(name, RetryConfig())

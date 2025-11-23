"""
Circuit Breaker Pattern

Implements circuit breaker for external service calls to prevent cascading failures.
"""

import asyncio
import logging
import time
from typing import Callable, Optional, TypeVar, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes (half-open)
    timeout_seconds: float = 60.0  # Time before attempting half-open
    expected_exception: type = Exception  # Exception type to catch


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    state: CircuitState = CircuitState.CLOSED
    total_requests: int = 0
    rejected_requests: int = 0


class CircuitBreaker:
    """
    Circuit Breaker
    
    Prevents cascading failures by opening circuit when service fails repeatedly.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[str, CircuitState], None]] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self.on_state_change = on_state_change
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of function call
            
        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if circuit should transition
            await self._check_state_transition()
            
            # Reject if circuit is open
            if self.stats.state == CircuitState.OPEN:
                self.stats.rejected_requests += 1
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Last failure: {self.stats.last_failure_time}"
                )
        
        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success
            await self._record_success()
            return result
            
        except self.config.expected_exception as e:
            # Failure
            await self._record_failure()
            raise
    
    async def _check_state_transition(self):
        """Check and update circuit breaker state"""
        now = datetime.utcnow()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.last_failure_time:
                time_since_failure = (now - self.stats.last_failure_time).total_seconds()
                if time_since_failure >= self.config.timeout_seconds:
                    # Transition to half-open
                    await self._transition_to(CircuitState.HALF_OPEN)
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Half-open state is managed by success/failure recording
            pass
    
    async def _record_success(self):
        """Record successful call"""
        async with self._lock:
            self.stats.total_requests += 1
            self.stats.successes += 1
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Check if we have enough successes to close
                if self.stats.successes >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
            else:
                # Reset failure count on success
                self.stats.failures = 0
    
    async def _record_failure(self):
        """Record failed call"""
        async with self._lock:
            self.stats.total_requests += 1
            self.stats.failures += 1
            self.stats.last_failure_time = datetime.utcnow()
            self.stats.successes = 0  # Reset success count
            
            if self.stats.state == CircuitState.CLOSED:
                # Check if we should open circuit
                if self.stats.failures >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
            
            elif self.stats.state == CircuitState.HALF_OPEN:
                # Any failure in half-open opens circuit immediately
                await self._transition_to(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        if self.stats.state != new_state:
            old_state = self.stats.state
            self.stats.state = new_state
            
            logger.info(
                f"Circuit breaker '{self.name}' transitioned: {old_state.value} -> {new_state.value}",
                extra={
                    "circuit_breaker": self.name,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "failures": self.stats.failures,
                    "successes": self.stats.successes,
                }
            )
            
            # Call state change callback
            if self.on_state_change:
                try:
                    if asyncio.iscoroutinefunction(self.on_state_change):
                        await self.on_state_change(self.name, new_state)
                    else:
                        self.on_state_change(self.name, new_state)
                except Exception as e:
                    logger.error(f"State change callback failed: {e}")
            
            # Reset counters on state change
            if new_state == CircuitState.CLOSED:
                self.stats.failures = 0
                self.stats.successes = 0
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.stats.failures = 0
        self.stats.successes = 0
        self.stats.last_failure_time = None
        self.stats.state = CircuitState.CLOSED
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_requests": self.stats.total_requests,
            "rejected_requests": self.stats.rejected_requests,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
        }


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker_decorator(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator for circuit breaker protection.
    
    Usage:
        @circuit_breaker_decorator("sendgrid", CircuitBreakerConfig(failure_threshold=5))
        async def send_email(...):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker = get_circuit_breaker(name, config)
        
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

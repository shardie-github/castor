"""
Tests for Circuit Breaker
"""

import pytest
import asyncio
from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState
)


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state (normal operation)"""
    breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.stats.state == CircuitState.CLOSED
    assert breaker.stats.failures == 0


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
    
    async def fail_func():
        raise Exception("Test failure")
    
    # First failure
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    assert breaker.stats.state == CircuitState.CLOSED
    assert breaker.stats.failures == 1
    
    # Second failure - should open circuit
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    assert breaker.stats.state == CircuitState.OPEN
    assert breaker.stats.failures == 2


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open():
    """Test circuit breaker rejects requests when open"""
    breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
    
    async def fail_func():
        raise Exception("Test failure")
    
    # Open circuit
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    
    # Next call should be rejected
    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(fail_func)
    
    assert breaker.stats.rejected_requests > 0


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """Test manual circuit breaker reset"""
    breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
    
    async def fail_func():
        raise Exception("Test failure")
    
    # Open circuit
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    
    assert breaker.stats.state == CircuitState.OPEN
    
    # Reset
    breaker.reset()
    assert breaker.stats.state == CircuitState.CLOSED
    assert breaker.stats.failures == 0

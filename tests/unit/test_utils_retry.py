"""
Tests for retry utility
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.utils.retry import retry_with_backoff, async_retry_with_backoff


class TestRetryUtility:
    """Test retry utility functionality"""
    
    def test_retry_success_first_attempt(self):
        """Test that function succeeds on first attempt"""
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_retry_success_after_retries(self):
        """Test that function succeeds after retries"""
        attempts = []
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert len(attempts) == 2
    
    def test_retry_max_retries_exceeded(self):
        """Test that exception is raised after max retries"""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def test_func():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError, match="Persistent error"):
            test_func()
    
    @pytest.mark.asyncio
    async def test_async_retry_success_first_attempt(self):
        """Test that async function succeeds on first attempt"""
        @async_retry_with_backoff(max_retries=3, initial_delay=0.1)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_retry_success_after_retries(self):
        """Test that async function succeeds after retries"""
        attempts = []
        
        @async_retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def test_func():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert len(attempts) == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_max_retries_exceeded(self):
        """Test that exception is raised after max retries for async"""
        @async_retry_with_backoff(max_retries=2, initial_delay=0.01)
        async def test_func():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError, match="Persistent error"):
            await test_func()

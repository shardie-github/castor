"""
Tests for Cache Decorators
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.utils.cache_decorators import cached
from src.cache.cache_manager import CacheManager


@pytest.mark.asyncio
async def test_cached_decorator_cache_hit():
    """Test cached decorator returns cached value"""
    cache_manager = MagicMock(spec=CacheManager)
    cache_manager.get = AsyncMock(return_value="cached_value")
    cache_manager.set = AsyncMock()
    
    @cached(ttl_seconds=300, cache_manager=cache_manager)
    async def test_func(arg1: str):
        return f"result_{arg1}"
    
    result = await test_func("test")
    
    assert result == "cached_value"
    cache_manager.get.assert_called_once()
    cache_manager.set.assert_not_called()


@pytest.mark.asyncio
async def test_cached_decorator_cache_miss():
    """Test cached decorator executes function on cache miss"""
    cache_manager = MagicMock(spec=CacheManager)
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock()
    
    @cached(ttl_seconds=300, cache_manager=cache_manager)
    async def test_func(arg1: str):
        return f"result_{arg1}"
    
    result = await test_func("test")
    
    assert result == "result_test"
    cache_manager.get.assert_called_once()
    cache_manager.set.assert_called_once()


@pytest.mark.asyncio
async def test_cached_decorator_no_cache():
    """Test cached decorator works without cache manager"""
    @cached(ttl_seconds=300, cache_manager=None)
    async def test_func(arg1: str):
        return f"result_{arg1}"
    
    result = await test_func("test")
    assert result == "result_test"

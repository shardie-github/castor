"""
Integration tests for database connections
"""

import pytest
import asyncio
from src.database import PostgresConnection, RedisConnection
from src.config import load_config

config = load_config()


@pytest.mark.asyncio
async def test_postgres_connection():
    """Test PostgreSQL connection"""
    conn = PostgresConnection(
        host=config.database.postgres_host,
        port=config.database.postgres_port,
        database=config.database.postgres_database,
        user=config.database.postgres_user,
        password=config.database.postgres_password
    )
    
    try:
        await conn.initialize()
        assert await conn.health_check()
        
        # Test query
        result = await conn.fetchval("SELECT 1")
        assert result == 1
        
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_redis_connection():
    """Test Redis connection"""
    conn = RedisConnection(
        host=config.database.redis_host,
        port=config.database.redis_port,
        password=config.database.redis_password
    )
    
    try:
        await conn.initialize()
        assert await conn.health_check()
        
        # Test set/get
        await conn.set("test_key", "test_value", ex=60)
        value = await conn.get("test_key")
        assert value == "test_value"
        
        # Cleanup
        await conn.delete("test_key")
        
    finally:
        await conn.close()

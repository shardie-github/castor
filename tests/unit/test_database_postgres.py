"""
Tests for PostgreSQL database connection
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg
from src.database.postgres import PostgresConnection


@pytest.fixture
def postgres_conn():
    """Create PostgreSQL connection instance"""
    return PostgresConnection(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_password",
        min_size=2,
        max_size=5
    )


@pytest.mark.asyncio
class TestPostgresConnection:
    """Test PostgreSQL connection functionality"""
    
    async def test_create_postgres_connection(self, postgres_conn):
        """Test creating PostgreSQL connection"""
        assert postgres_conn.host == "localhost"
        assert postgres_conn.port == 5432
        assert postgres_conn.database == "test_db"
        assert postgres_conn.user == "test_user"
        assert postgres_conn.pool is None
    
    @patch('asyncpg.create_pool')
    async def test_initialize(self, mock_create_pool, postgres_conn):
        """Test initializing connection pool"""
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool
        
        await postgres_conn.initialize()
        
        assert postgres_conn.pool == mock_pool
        mock_create_pool.assert_called_once()
    
    async def test_close(self, postgres_conn):
        """Test closing connection pool"""
        mock_pool = AsyncMock()
        postgres_conn.pool = mock_pool
        
        await postgres_conn.close()
        
        mock_pool.close.assert_called_once()
        assert postgres_conn.pool is None
    
    async def test_execute(self, postgres_conn):
        """Test executing a query"""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="OK")
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        postgres_conn.pool = mock_pool
        
        result = await postgres_conn.execute("SELECT 1")
        
        assert result == "OK"
        mock_conn.execute.assert_called_once_with("SELECT 1")
    
    async def test_fetch(self, postgres_conn):
        """Test fetching rows"""
        mock_conn = AsyncMock()
        mock_rows = [{"id": 1, "name": "test"}]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        postgres_conn.pool = mock_pool
        
        result = await postgres_conn.fetch("SELECT * FROM test")
        
        assert result == mock_rows
        mock_conn.fetch.assert_called_once_with("SELECT * FROM test")
    
    async def test_fetchrow(self, postgres_conn):
        """Test fetching a single row"""
        mock_conn = AsyncMock()
        mock_row = {"id": 1, "name": "test"}
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        postgres_conn.pool = mock_pool
        
        result = await postgres_conn.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        
        assert result == mock_row
        mock_conn.fetchrow.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
    
    async def test_fetchval(self, postgres_conn):
        """Test fetching a single value"""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=42)
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        postgres_conn.pool = mock_pool
        
        result = await postgres_conn.fetchval("SELECT COUNT(*) FROM test")
        
        assert result == 42
        mock_conn.fetchval.assert_called_once_with("SELECT COUNT(*) FROM test")
    
    async def test_acquire_auto_initialize(self, postgres_conn):
        """Test that acquire auto-initializes if pool is None"""
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock()
        
        with patch.object(postgres_conn, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = None
            postgres_conn.pool = mock_pool
            
            async with postgres_conn.acquire() as conn:
                pass
            
            # Should not initialize if pool exists
            mock_init.assert_not_called()

"""
PostgreSQL Database Connection

Handles PostgreSQL database connections with connection pooling.
"""

import logging
import asyncpg
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class PostgresConnection:
    """
    PostgreSQL Connection Manager
    
    Manages PostgreSQL connections with connection pooling and read replica support.
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_size: int = 5,
        max_size: int = 20,
        read_replica_host: Optional[str] = None,
        read_replica_port: Optional[int] = None
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        
        # Read replica configuration
        self.read_replica_host = read_replica_host
        self.read_replica_port = read_replica_port or port
        self.read_replica_pool: Optional[asyncpg.Pool] = None
        self._use_read_replica = read_replica_host is not None
    
    async def initialize(self):
        """Initialize connection pools (primary and read replica if configured)"""
        try:
            # Initialize primary pool
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size
            )
            logger.info(f"PostgreSQL connection pool initialized: {self.database}")
            
            # Initialize read replica pool if configured
            if self._use_read_replica:
                try:
                    self.read_replica_pool = await asyncpg.create_pool(
                        host=self.read_replica_host,
                        port=self.read_replica_port,
                        database=self.database,
                        user=self.user,
                        password=self.password,
                        min_size=max(2, self.min_size // 2),  # Smaller pool for reads
                        max_size=max(5, self.max_size // 2)
                    )
                    logger.info(f"PostgreSQL read replica pool initialized: {self.read_replica_host}:{self.read_replica_port}")
                except Exception as e:
                    logger.warning(f"Failed to initialize read replica pool, falling back to primary: {e}")
                    self._use_read_replica = False
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            raise
    
    async def close(self):
        """Close connection pools"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
        if self.read_replica_pool:
            await self.read_replica_pool.close()
            logger.info("PostgreSQL read replica pool closed")
    
    @asynccontextmanager
    async def acquire(self, use_read_replica: bool = False):
        """
        Acquire a connection from the pool.
        
        Args:
            use_read_replica: If True and read replica is configured, use read replica pool
        """
        if not self.pool:
            await self.initialize()
        
        # Use read replica if requested and available
        pool = self.pool
        if use_read_replica and self._use_read_replica and self.read_replica_pool:
            pool = self.read_replica_pool
        
        async with pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args, use_read_replica: bool = False) -> list:
        """Fetch rows from a query"""
        async with self.acquire(use_read_replica=use_read_replica) as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args, use_read_replica: bool = False) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        async with self.acquire(use_read_replica=use_read_replica) as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args, use_read_replica: bool = False) -> Any:
        """Fetch a single value"""
        async with self.acquire(use_read_replica=use_read_replica) as conn:
            return await conn.fetchval(query, *args)
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

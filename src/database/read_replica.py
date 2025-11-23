"""
Read Replica Configuration and Query Routing

Routes read queries to read replicas for better performance.
"""

import logging
from typing import Optional, Callable, TypeVar, Any
from contextlib import asynccontextmanager

from src.database.postgres import PostgresConnection

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ReadReplicaRouter:
    """
    Routes database queries to read replicas when appropriate.
    
    Automatically routes SELECT queries to read replicas and
    write operations to the primary database.
    """
    
    def __init__(
        self,
        primary_conn: PostgresConnection,
        read_replica_conn: Optional[PostgresConnection] = None,
        replica_available: bool = True
    ):
        self.primary = primary_conn
        self.replica = read_replica_conn
        self.replica_available = replica_available and read_replica_conn is not None
    
    def _is_read_query(self, query: str) -> bool:
        """Determine if query is a read operation"""
        query_upper = query.strip().upper()
        return query_upper.startswith("SELECT") or query_upper.startswith("WITH")
    
    def _should_use_replica(self, query: str, use_read_replica: bool = False) -> bool:
        """Determine if query should use read replica"""
        if not self.replica_available:
            return False
        
        if use_read_replica:
            return True
        
        # Auto-detect read queries
        return self._is_read_query(query)
    
    async def execute(self, query: str, *args, use_read_replica: Optional[bool] = None) -> str:
        """
        Execute query, routing to appropriate database.
        
        Args:
            query: SQL query
            *args: Query parameters
            use_read_replica: Force use of read replica (None = auto-detect)
        """
        if use_read_replica is None:
            use_read_replica = self._should_use_replica(query)
        
        if use_read_replica and self.replica_available:
            logger.debug(f"Routing read query to replica: {query[:50]}...")
            return await self.replica.execute(query, *args)
        else:
            logger.debug(f"Routing query to primary: {query[:50]}...")
            return await self.primary.execute(query, *args)
    
    async def fetch(self, query: str, *args, use_read_replica: Optional[bool] = None) -> list:
        """
        Fetch rows, routing to read replica if appropriate.
        
        Args:
            query: SQL query
            *args: Query parameters
            use_read_replica: Force use of read replica (None = auto-detect)
        """
        if use_read_replica is None:
            use_read_replica = self._should_use_replica(query)
        
        if use_read_replica and self.replica_available:
            logger.debug(f"Routing fetch to replica: {query[:50]}...")
            return await self.replica.fetch(query, *args, use_read_replica=True)
        else:
            return await self.primary.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args, use_read_replica: Optional[bool] = None) -> Optional[Any]:
        """
        Fetch single row, routing to read replica if appropriate.
        
        Args:
            query: SQL query
            *args: Query parameters
            use_read_replica: Force use of read replica (None = auto-detect)
        """
        if use_read_replica is None:
            use_read_replica = self._should_use_replica(query)
        
        if use_read_replica and self.replica_available:
            logger.debug(f"Routing fetchrow to replica: {query[:50]}...")
            return await self.replica.fetchrow(query, *args, use_read_replica=True)
        else:
            return await self.primary.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args, use_read_replica: Optional[bool] = None) -> Any:
        """
        Fetch single value, routing to read replica if appropriate.
        
        Args:
            query: SQL query
            *args: Query parameters
            use_read_replica: Force use of read replica (None = auto-detect)
        """
        if use_read_replica is None:
            use_read_replica = self._should_use_replica(query)
        
        if use_read_replica and self.replica_available:
            logger.debug(f"Routing fetchval to replica: {query[:50]}...")
            return await self.replica.fetchval(query, *args, use_read_replica=True)
        else:
            return await self.primary.fetchval(query, *args)
    
    @asynccontextmanager
    async def acquire(self, use_read_replica: bool = False):
        """
        Acquire connection from appropriate database.
        
        Args:
            use_read_replica: Use read replica connection
        """
        if use_read_replica and self.replica_available:
            async with self.replica.acquire(use_read_replica=True):
                yield
        else:
            async with self.primary.acquire():
                yield
    
    async def health_check(self) -> dict:
        """Check health of both primary and replica"""
        primary_healthy = await self.primary.health_check()
        
        replica_healthy = False
        if self.replica_available:
            replica_healthy = await self.replica.health_check()
        
        return {
            "primary": primary_healthy,
            "replica": replica_healthy if self.replica_available else None,
            "replica_available": self.replica_available
        }

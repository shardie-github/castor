"""
Redis Connection

Handles Redis connections for caching and session management.
"""

import logging
import redis.asyncio as redis
from typing import Optional, Any
import json

logger = logging.getLogger(__name__)


class RedisConnection:
    """
    Redis Connection Manager
    
    Manages Redis connections for caching and session storage.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self.decode_responses
            )
            
            # Test connection
            await self.client.ping()
            logger.info(f"Redis connection initialized: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            await self.initialize()
        return await self.client.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None  # Expiration in seconds
    ) -> bool:
        """Set value in Redis"""
        if not self.client:
            await self.initialize()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, key: str) -> int:
        """Delete key from Redis"""
        if not self.client:
            await self.initialize()
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            await self.initialize()
        return bool(await self.client.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self.client:
            await self.initialize()
        return await self.client.expire(key, seconds)
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.client:
                await self.initialize()
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

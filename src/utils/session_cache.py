"""
Session Cache Utilities

Provides session caching functionality using Redis.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import timedelta
from src.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class SessionCache:
    """Session cache manager"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.session_ttl = 3600  # 1 hour default
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        cache_key = f"session:{session_id}"
        return await self.cache.get(cache_key)
    
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """Set session data"""
        cache_key = f"session:{session_id}"
        ttl = ttl_seconds or self.session_ttl
        await self.cache.set(cache_key, data, ttl_seconds=ttl)
    
    async def delete_session(self, session_id: str):
        """Delete session"""
        cache_key = f"session:{session_id}"
        await self.cache.delete(cache_key)
    
    async def refresh_session(self, session_id: str, ttl_seconds: Optional[int] = None):
        """Refresh session TTL"""
        session_data = await self.get_session(session_id)
        if session_data:
            await self.set_session(session_id, session_data, ttl_seconds)

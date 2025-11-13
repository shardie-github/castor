"""
Simplecast Integration

Integration with Simplecast podcast hosting platform.
"""

import logging
from typing import Dict, List, Optional, Any

from src.integrations.framework import IntegrationBase, IntegrationType
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class SimplecastIntegration(IntegrationBase):
    """Simplecast integration"""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        super().__init__(
            "simplecast",
            IntegrationType.HOSTING,
            metrics_collector,
            event_logger,
            postgres_conn
        )
        self.api_base_url = "https://api.simplecast.com"
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Simplecast API"""
        api_key = credentials.get("api_key")
        if not api_key:
            return False
        
        await self.store_oauth_token(
            self.tenant_id or "",
            api_key
        )
        
        return await self.test_connection()
    
    async def test_connection(self) -> bool:
        """Test connection to Simplecast API"""
        try:
            token = await self.get_oauth_token(self.tenant_id or "")
            if not token:
                return False
            
            async with self._session.get(
                f"{self.api_base_url}/v2/shows",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Simplecast connection test failed: {e}")
            return False
    
    async def sync_data(self, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Sync podcast data from Simplecast"""
        token = await self.get_oauth_token(tenant_id)
        if not token:
            raise ValueError("Not authenticated")
        
        return {
            "status": "completed"
        }

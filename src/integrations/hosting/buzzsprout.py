"""
Buzzsprout Integration

Integration with Buzzsprout podcast hosting platform.
"""

import logging
from typing import Dict, List, Optional, Any

from src.integrations.framework import IntegrationBase, IntegrationType
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class BuzzsproutIntegration(IntegrationBase):
    """Buzzsprout integration"""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        super().__init__(
            "buzzsprout",
            IntegrationType.HOSTING,
            metrics_collector,
            event_logger,
            postgres_conn
        )
        self.api_base_url = "https://www.buzzsprout.com/api"
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Buzzsprout API"""
        api_token = credentials.get("api_token")
        if not api_token:
            return False
        
        await self.store_oauth_token(
            self.tenant_id or "",
            api_token
        )
        
        return await self.test_connection()
    
    async def test_connection(self) -> bool:
        """Test connection to Buzzsprout API"""
        try:
            token = await self.get_oauth_token(self.tenant_id or "")
            if not token:
                return False
            
            async with self._session.get(
                f"{self.api_base_url}/podcasts.json",
                headers={"Authorization": f"Token {token}"}
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Buzzsprout connection test failed: {e}")
            return False
    
    async def sync_data(self, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Sync podcast data from Buzzsprout"""
        token = await self.get_oauth_token(tenant_id)
        if not token:
            raise ValueError("Not authenticated")
        
        # Sync podcasts and episodes
        # In production, implement full sync logic
        
        return {
            "status": "completed"
        }

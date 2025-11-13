"""
Wix Integration Module

Integrates with Wix to:
- Track conversions from podcast campaigns
- Sync product data
- Create discount codes
"""

import logging
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


@dataclass
class WixConfig:
    """Wix API configuration"""
    site_id: str
    api_key: str
    access_token: str


class WixIntegration:
    """
    Wix Integration
    
    Handles:
    - Order tracking
    - Discount code creation
    - Conversion attribution
    """
    
    def __init__(
        self,
        config: WixConfig,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.config = config
        self.metrics = metrics_collector
        self.events = event_logger
        self.base_url = f"https://www.wixapis.com/stores/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "Authorization": self.config.access_token,
            "Content-Type": "application/json",
            "wix-site-id": self.config.site_id
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def create_discount_code(
        self,
        code: str,
        discount_type: str = "PERCENTAGE",
        value: float = 10.0
    ) -> Dict[str, Any]:
        """Create a discount code in Wix"""
        url = f"{self.base_url}/discounts"
        
        payload = {
            "discount": {
                "name": f"Podcast Campaign: {code}",
                "code": code,
                "type": discount_type,
                "value": value,
                "appliesTo": {
                    "type": "ALL"
                },
                "startDate": datetime.now(timezone.utc).isoformat(),
                "endDate": None,
                "usageLimit": None
            }
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Record telemetry
                self.metrics.increment_counter(
                    "wix_discount_code_created",
                    tags={"code": code}
                )
                
                return data
                
        except Exception as e:
            logger.error(f"Error creating Wix discount code: {e}")
            self.metrics.increment_counter(
                "wix_api_errors",
                tags={"operation": "create_discount_code", "error_type": type(e).__name__}
            )
            raise
    
    async def get_orders(
        self,
        discount_code: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get orders from Wix"""
        url = f"{self.base_url}/orders"
        params = {"limit": limit}
        
        if discount_code:
            params["discountCode"] = discount_code
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                orders = data.get("orders", [])
                
                # Record telemetry
                self.metrics.increment_counter(
                    "wix_orders_fetched",
                    tags={"count": len(orders), "has_discount_code": discount_code is not None}
                )
                
                return orders
                
        except Exception as e:
            logger.error(f"Error fetching Wix orders: {e}")
            self.metrics.increment_counter(
                "wix_api_errors",
                tags={"operation": "get_orders", "error_type": type(e).__name__}
            )
            raise

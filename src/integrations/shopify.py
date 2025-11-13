"""
Shopify Integration Module

Integrates with Shopify to:
- Track conversions from podcast campaigns
- Sync product data
- Create discount codes
- Track orders
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
class ShopifyConfig:
    """Shopify API configuration"""
    shop_domain: str
    api_key: str
    api_secret: str
    access_token: str
    webhook_secret: Optional[str] = None


@dataclass
class ShopifyOrder:
    """Shopify order data"""
    order_id: str
    order_number: str
    total_price: float
    discount_codes: List[str]
    created_at: datetime
    customer_email: Optional[str] = None
    line_items: List[Dict[str, Any]] = None


class ShopifyIntegration:
    """
    Shopify Integration
    
    Handles:
    - Order tracking
    - Discount code creation
    - Conversion attribution
    - Webhook processing
    """
    
    def __init__(
        self,
        config: ShopifyConfig,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.config = config
        self.metrics = metrics_collector
        self.events = event_logger
        self.base_url = f"https://{config.shop_domain}.myshopify.com/admin/api/2024-01"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "X-Shopify-Access-Token": self.config.access_token,
            "Content-Type": "application/json"
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def create_discount_code(
        self,
        code: str,
        value: float,
        discount_type: str = "percentage"  # percentage or fixed_amount
    ) -> Dict[str, Any]:
        """Create a discount code in Shopify"""
        url = f"{self.base_url}/price_rules.json"
        
        payload = {
            "price_rule": {
                "title": f"Podcast Campaign: {code}",
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": discount_type,
                "value": f"-{value}" if discount_type == "percentage" else f"-{value}",
                "customer_selection": "all",
                "starts_at": datetime.now(timezone.utc).isoformat(),
                "usage_limit": None
            }
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Create discount code
                price_rule_id = data["price_rule"]["id"]
                discount_url = f"{self.base_url}/price_rules/{price_rule_id}/discount_codes.json"
                
                discount_payload = {
                    "discount_code": {
                        "code": code
                    }
                }
                
                async with self.session.post(discount_url, json=discount_payload) as response:
                    response.raise_for_status()
                    discount_data = await response.json()
                
                # Record telemetry
                self.metrics.increment_counter(
                    "shopify_discount_code_created",
                    tags={"code": code}
                )
                
                return discount_data
                
        except Exception as e:
            logger.error(f"Error creating Shopify discount code: {e}")
            self.metrics.increment_counter(
                "shopify_api_errors",
                tags={"operation": "create_discount_code", "error_type": type(e).__name__}
            )
            raise
    
    async def get_orders(
        self,
        discount_code: Optional[str] = None,
        since_id: Optional[str] = None,
        limit: int = 250
    ) -> List[ShopifyOrder]:
        """Get orders from Shopify"""
        url = f"{self.base_url}/orders.json"
        params = {"limit": limit}
        
        if discount_code:
            params["discount_codes"] = discount_code
        
        if since_id:
            params["since_id"] = since_id
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                orders = []
                for order_data in data.get("orders", []):
                    order = ShopifyOrder(
                        order_id=str(order_data["id"]),
                        order_number=str(order_data["order_number"]),
                        total_price=float(order_data["total_price"]),
                        discount_codes=[
                            dc["code"] for dc in order_data.get("discount_codes", [])
                        ],
                        created_at=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00")),
                        customer_email=order_data.get("email"),
                        line_items=order_data.get("line_items", [])
                    )
                    orders.append(order)
                
                # Record telemetry
                self.metrics.increment_counter(
                    "shopify_orders_fetched",
                    tags={"count": len(orders), "has_discount_code": discount_code is not None}
                )
                
                return orders
                
        except Exception as e:
            logger.error(f"Error fetching Shopify orders: {e}")
            self.metrics.increment_counter(
                "shopify_api_errors",
                tags={"operation": "get_orders", "error_type": type(e).__name__}
            )
            raise
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process Shopify webhook event"""
        event_type = webhook_data.get("event")
        
        try:
            if event_type == "orders/create":
                order_data = webhook_data.get("order", {})
                await self._process_order_created(order_data)
            elif event_type == "orders/paid":
                order_data = webhook_data.get("order", {})
                await self._process_order_paid(order_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            # Record telemetry
            self.metrics.increment_counter(
                "shopify_webhooks_processed",
                tags={"event_type": event_type}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Shopify webhook: {e}")
            self.metrics.increment_counter(
                "shopify_webhook_errors",
                tags={"event_type": event_type, "error_type": type(e).__name__}
            )
            return False
    
    async def _process_order_created(self, order_data: Dict[str, Any]):
        """Process order created event"""
        discount_codes = [dc["code"] for dc in order_data.get("discount_codes", [])]
        
        # Log event for attribution
        await self.events.log_event(
            event_type="shopify_order_created",
            user_id=None,
            properties={
                "order_id": str(order_data["id"]),
                "order_number": str(order_data["order_number"]),
                "total_price": float(order_data["total_price"]),
                "discount_codes": discount_codes,
                "customer_email": order_data.get("email")
            }
        )
    
    async def _process_order_paid(self, order_data: Dict[str, Any]):
        """Process order paid event"""
        # Similar to order created, but for paid orders
        await self._process_order_created(order_data)

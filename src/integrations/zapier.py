"""
Zapier Integration Module

Provides Zapier webhooks and triggers for:
- Campaign events
- Report generation
- Attribution events
- User actions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


@dataclass
class ZapierWebhook:
    """Zapier webhook configuration"""
    webhook_id: str
    user_id: str
    event_type: str
    webhook_url: str
    enabled: bool = True
    created_at: datetime = None


class ZapierIntegration:
    """
    Zapier Integration
    
    Provides webhooks and triggers for Zapier automation:
    - Campaign created/updated/completed
    - Report generated
    - Attribution event
    - User signup
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._webhooks: Dict[str, List[ZapierWebhook]] = {}
    
    async def register_webhook(
        self,
        user_id: str,
        event_type: str,
        webhook_url: str
    ) -> ZapierWebhook:
        """Register a Zapier webhook"""
        webhook_id = f"zap_{user_id}_{event_type}_{datetime.now(timezone.utc).timestamp()}"
        
        webhook = ZapierWebhook(
            webhook_id=webhook_id,
            user_id=user_id,
            event_type=event_type,
            webhook_url=webhook_url,
            created_at=datetime.now(timezone.utc)
        )
        
        if user_id not in self._webhooks:
            self._webhooks[user_id] = []
        
        self._webhooks[user_id].append(webhook)
        
        # Log event
        await self.events.log_event(
            event_type="zapier_webhook_registered",
            user_id=user_id,
            properties={
                "webhook_id": webhook_id,
                "event_type": event_type
            }
        )
        
        return webhook
    
    async def trigger_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Trigger Zapier webhooks for an event"""
        import aiohttp
        
        # Find matching webhooks
        webhooks_to_trigger = []
        
        if user_id:
            # User-specific webhooks
            user_webhooks = self._webhooks.get(user_id, [])
            webhooks_to_trigger.extend([
                w for w in user_webhooks
                if w.event_type == event_type and w.enabled
            ])
        
        # Global webhooks (for all users)
        for user_id_key, webhooks in self._webhooks.items():
            for webhook in webhooks:
                if webhook.event_type == event_type and webhook.enabled:
                    if webhook not in webhooks_to_trigger:
                        webhooks_to_trigger.append(webhook)
        
        # Trigger webhooks
        async with aiohttp.ClientSession() as session:
            for webhook in webhooks_to_trigger:
                try:
                    async with session.post(
                        webhook.webhook_url,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response.raise_for_status()
                        
                        # Record telemetry
                        self.metrics.increment_counter(
                            "zapier_webhook_triggered",
                            tags={"event_type": event_type, "status": "success"}
                        )
                        
                except Exception as e:
                    logger.error(f"Error triggering Zapier webhook: {e}")
                    self.metrics.increment_counter(
                        "zapier_webhook_errors",
                        tags={"event_type": event_type, "error_type": type(e).__name__}
                    )
    
    async def get_webhooks(self, user_id: str) -> List[ZapierWebhook]:
        """Get webhooks for a user"""
        return self._webhooks.get(user_id, [])
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        for user_id, webhooks in self._webhooks.items():
            for i, webhook in enumerate(webhooks):
                if webhook.webhook_id == webhook_id:
                    del webhooks[i]
                    
                    # Log event
                    await self.events.log_event(
                        event_type="zapier_webhook_deleted",
                        user_id=user_id,
                        properties={"webhook_id": webhook_id}
                    )
                    
                    return True
        
        return False

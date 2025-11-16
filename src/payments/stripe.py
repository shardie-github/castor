"""
Stripe Payment Processing Integration

Handles payment processing using Stripe API.
"""

import logging
import os
import stripe
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.config import config

logger = logging.getLogger(__name__)

# Initialize Stripe (will be set when processor is created)
stripe.api_key = config.stripe_secret_key or os.getenv("STRIPE_SECRET_KEY", "")


@dataclass
class PaymentIntent:
    """Payment intent data"""
    intent_id: str
    amount: float
    currency: str
    status: str
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class Subscription:
    """Stripe subscription data"""
    subscription_id: str
    customer_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    plan_id: str
    cancel_at_period_end: bool = False


class StripePaymentProcessor:
    """
    Stripe Payment Processor
    
    Handles:
    - Payment intents
    - Subscription management
    - Invoice generation
    - Webhook processing
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_customer_created",
                tags={"email": email}
            )
            
            # Log event
            await self.events.log_event(
                event_type="stripe_customer_created",
                user_id=None,
                properties={
                    "customer_id": customer.id,
                    "email": email
                }
            )
            
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "create_customer", "error_type": type(e).__name__}
            )
            raise
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """Create a payment intent"""
        try:
            intent_params = {
                "amount": int(amount * 100),  # Convert to cents
                "currency": currency,
                "metadata": metadata or {}
            }
            
            if customer_id:
                intent_params["customer"] = customer_id
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            payment_intent = PaymentIntent(
                intent_id=intent.id,
                amount=amount,
                currency=currency,
                status=intent.status,
                customer_id=intent.customer,
                metadata=intent.metadata
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_payment_intent_created",
                tags={"currency": currency, "status": intent.status}
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "create_payment_intent", "error_type": type(e).__name__}
            )
            raise
    
    async def confirm_payment(
        self,
        payment_intent_id: str,
        payment_method_id: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a payment intent"""
        try:
            intent_params = {}
            if payment_method_id:
                intent_params["payment_method"] = payment_method_id
            
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **intent_params
            )
            
            payment_intent = PaymentIntent(
                intent_id=intent.id,
                amount=intent.amount / 100,  # Convert from cents
                currency=intent.currency,
                status=intent.status,
                customer_id=intent.customer,
                metadata=intent.metadata
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_payment_confirmed",
                tags={"status": intent.status}
            )
            
            # Log event
            await self.events.log_event(
                event_type="stripe_payment_confirmed",
                user_id=None,
                properties={
                    "payment_intent_id": payment_intent_id,
                    "status": intent.status,
                    "amount": payment_intent.amount
                }
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "confirm_payment", "error_type": type(e).__name__}
            )
            raise
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """Create a subscription"""
        try:
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {}
            }
            
            stripe_subscription = stripe.Subscription.create(**subscription_params)
            
            subscription = Subscription(
                subscription_id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start,
                    tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end,
                    tz=timezone.utc
                ),
                plan_id=price_id,
                cancel_at_period_end=False
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_subscription_created",
                tags={"status": subscription.status}
            )
            
            # Log event
            await self.events.log_event(
                event_type="stripe_subscription_created",
                user_id=None,
                properties={
                    "subscription_id": subscription.subscription_id,
                    "customer_id": customer_id,
                    "price_id": price_id
                }
            )
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "create_subscription", "error_type": type(e).__name__}
            )
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_immediately: bool = False
    ) -> Subscription:
        """Cancel a subscription"""
        try:
            if cancel_immediately:
                stripe_subscription = stripe.Subscription.delete(subscription_id)
            else:
                stripe_subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            subscription = Subscription(
                subscription_id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start,
                    tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end,
                    tz=timezone.utc
                ),
                plan_id=stripe_subscription.items.data[0].price.id if stripe_subscription.items.data else "",
                cancel_at_period_end=stripe_subscription.cancel_at_period_end
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_subscription_cancelled",
                tags={"cancel_immediately": str(cancel_immediately)}
            )
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "cancel_subscription", "error_type": type(e).__name__}
            )
            raise
    
    async def create_invoice(
        self,
        customer_id: str,
        amount: float,
        currency: str = "usd",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an invoice"""
        try:
            # Create invoice item
            invoice_item = stripe.InvoiceItem.create(
                customer=customer_id,
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                description=description
            )
            
            # Create invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True
            )
            
            # Finalize invoice
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_invoice_created",
                tags={"currency": currency}
            )
            
            return invoice
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating invoice: {e}")
            self.metrics.increment_counter(
                "stripe_errors",
                tags={"operation": "create_invoice", "error_type": type(e).__name__}
            )
            raise
    
    async def process_webhook(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> Dict[str, Any]:
        """Process Stripe webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                webhook_secret
            )
            
            # Handle different event types
            if event.type == "payment_intent.succeeded":
                await self._handle_payment_succeeded(event.data.object)
            elif event.type == "payment_intent.payment_failed":
                await self._handle_payment_failed(event.data.object)
            elif event.type == "customer.subscription.created":
                await self._handle_subscription_created(event.data.object)
            elif event.type == "customer.subscription.updated":
                await self._handle_subscription_updated(event.data.object)
            elif event.type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event.data.object)
            elif event.type == "invoice.payment_succeeded":
                await self._handle_invoice_payment_succeeded(event.data.object)
            elif event.type == "invoice.payment_failed":
                await self._handle_invoice_payment_failed(event.data.object)
            
            # Record telemetry
            self.metrics.increment_counter(
                "stripe_webhooks_processed",
                tags={"event_type": event.type}
            )
            
            return event
            
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise
    
    async def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]):
        """Handle payment succeeded event"""
        await self.events.log_event(
            event_type="stripe_payment_succeeded",
            user_id=None,
            properties={
                "payment_intent_id": payment_intent["id"],
                "amount": payment_intent["amount"] / 100,
                "customer_id": payment_intent.get("customer")
            }
        )
    
    async def _handle_payment_failed(self, payment_intent: Dict[str, Any]):
        """Handle payment failed event"""
        await self.events.log_event(
            event_type="stripe_payment_failed",
            user_id=None,
            properties={
                "payment_intent_id": payment_intent["id"],
                "customer_id": payment_intent.get("customer")
            }
        )
    
    async def _handle_subscription_created(self, subscription: Dict[str, Any]):
        """Handle subscription created event"""
        await self.events.log_event(
            event_type="stripe_subscription_created",
            user_id=None,
            properties={
                "subscription_id": subscription["id"],
                "customer_id": subscription["customer"]
            }
        )
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription updated event"""
        await self.events.log_event(
            event_type="stripe_subscription_updated",
            user_id=None,
            properties={
                "subscription_id": subscription["id"],
                "status": subscription["status"]
            }
        )
    
    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription deleted event"""
        await self.events.log_event(
            event_type="stripe_subscription_deleted",
            user_id=None,
            properties={
                "subscription_id": subscription["id"],
                "customer_id": subscription["customer"]
            }
        )
    
    async def _handle_invoice_payment_succeeded(self, invoice: Dict[str, Any]):
        """Handle invoice payment succeeded event"""
        await self.events.log_event(
            event_type="stripe_invoice_payment_succeeded",
            user_id=None,
            properties={
                "invoice_id": invoice["id"],
                "customer_id": invoice["customer"],
                "amount": invoice["amount_paid"] / 100
            }
        )
    
    async def _handle_invoice_payment_failed(self, invoice: Dict[str, Any]):
        """Handle invoice payment failed event"""
        await self.events.log_event(
            event_type="stripe_invoice_payment_failed",
            user_id=None,
            properties={
                "invoice_id": invoice["id"],
                "customer_id": invoice["customer"]
            }
        )

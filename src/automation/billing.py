"""
Billing Automation Module

Automates billing-related tasks:
- Subscription renewals
- Usage-based billing calculations
- Invoice generation
- Payment processing
- Dunning management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import User, SubscriptionTier
from src.monetization.pricing import PricingCalculator

logger = logging.getLogger(__name__)


class BillingStatus(Enum):
    """Billing status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    EXPIRED = "expired"


class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Invoice:
    """Invoice data"""
    invoice_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    due_date: datetime = None
    paid_at: Optional[datetime] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """Subscription data"""
    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    status: BillingStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BillingAutomation:
    """
    Billing Automation
    
    Handles:
    - Subscription management
    - Invoice generation
    - Payment processing
    - Usage tracking
    - Dunning management
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        pricing_calculator: PricingCalculator
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.pricing = pricing_calculator
        self._subscriptions: Dict[str, Subscription] = {}
        self._invoices: Dict[str, Invoice] = {}
    
    async def create_subscription(
        self,
        user: User,
        tier: SubscriptionTier,
        trial_days: int = 0
    ) -> Subscription:
        """Create a new subscription"""
        subscription_id = f"sub_{user.user_id}_{datetime.now(timezone.utc).timestamp()}"
        
        now = datetime.now(timezone.utc)
        period_start = now
        period_end = now + timedelta(days=30)  # Monthly billing
        
        if trial_days > 0:
            trial_end = now + timedelta(days=trial_days)
            status = BillingStatus.TRIAL
        else:
            trial_end = None
            status = BillingStatus.ACTIVE
        
        subscription = Subscription(
            subscription_id=subscription_id,
            user_id=user.user_id,
            tier=tier,
            status=status,
            current_period_start=period_start,
            current_period_end=period_end,
            trial_end=trial_end
        )
        
        self._subscriptions[user.user_id] = subscription
        
        # Generate initial invoice if not in trial
        if not trial_days:
            await self.generate_invoice(user, subscription)
        
        # Log event
        await self.events.log_event(
            event_type="subscription_created",
            user_id=user.user_id,
            properties={
                "subscription_id": subscription_id,
                "tier": tier.value,
                "trial_days": trial_days
            }
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "subscriptions_created",
            tags={"tier": tier.value}
        )
        
        return subscription
    
    async def renew_subscription(self, user_id: str) -> Optional[Subscription]:
        """Renew subscription for next billing period"""
        subscription = self._subscriptions.get(user_id)
        if not subscription:
            return None
        
        # Check if subscription should be renewed
        if subscription.cancel_at_period_end:
            subscription.status = BillingStatus.CANCELLED
            return None
        
        # Extend period
        subscription.current_period_start = subscription.current_period_end
        subscription.current_period_end = subscription.current_period_end + timedelta(days=30)
        
        # Generate invoice
        user = await self._get_user(user_id)
        if user:
            await self.generate_invoice(user, subscription)
        
        # Log event
        await self.events.log_event(
            event_type="subscription_renewed",
            user_id=user_id,
            properties={
                "subscription_id": subscription.subscription_id,
                "new_period_end": subscription.current_period_end.isoformat()
            }
        )
        
        return subscription
    
    async def generate_invoice(
        self,
        user: User,
        subscription: Subscription
    ) -> Invoice:
        """Generate invoice for subscription"""
        # Calculate amount based on tier
        amount = self.pricing.get_tier_price(subscription.tier)
        
        invoice_id = f"inv_{user.user_id}_{datetime.now(timezone.utc).timestamp()}"
        
        invoice = Invoice(
            invoice_id=invoice_id,
            user_id=user.user_id,
            amount=amount,
            due_date=subscription.current_period_end,
            items=[{
                "description": f"{subscription.tier.value} subscription",
                "amount": amount,
                "quantity": 1
            }]
        )
        
        self._invoices[invoice_id] = invoice
        
        # Log event
        await self.events.log_event(
            event_type="invoice_generated",
            user_id=user.user_id,
            properties={
                "invoice_id": invoice_id,
                "amount": amount,
                "tier": subscription.tier.value
            }
        )
        
        # Record telemetry
        self.metrics.record_gauge(
            "invoice_amount",
            amount,
            tags={"tier": subscription.tier.value}
        )
        
        return invoice
    
    async def process_payment(
        self,
        invoice_id: str,
        payment_method: str
    ) -> bool:
        """Process payment for invoice"""
        invoice = self._invoices.get(invoice_id)
        if not invoice:
            return False
        
        # In production, this would integrate with payment processor (Stripe, etc.)
        # For now, simulate payment processing
        try:
            # Simulate payment processing
            await self._charge_payment_method(invoice, payment_method)
            
            invoice.status = PaymentStatus.SUCCEEDED
            invoice.paid_at = datetime.now(timezone.utc)
            
            # Update subscription status
            subscription = self._subscriptions.get(invoice.user_id)
            if subscription:
                subscription.status = BillingStatus.ACTIVE
            
            # Log event
            await self.events.log_event(
                event_type="payment_succeeded",
                user_id=invoice.user_id,
                properties={
                    "invoice_id": invoice_id,
                    "amount": invoice.amount
                }
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "payments_succeeded",
                tags={"tier": subscription.tier.value if subscription else "unknown"}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            invoice.status = PaymentStatus.FAILED
            
            # Update subscription status
            subscription = self._subscriptions.get(invoice.user_id)
            if subscription:
                subscription.status = BillingStatus.PAST_DUE
            
            # Log event
            await self.events.log_event(
                event_type="payment_failed",
                user_id=invoice.user_id,
                properties={
                    "invoice_id": invoice_id,
                    "error": str(e)
                }
            )
            
            # Record telemetry
            self.metrics.increment_counter(
                "payments_failed",
                tags={"error_type": type(e).__name__}
            )
            
            return False
    
    async def check_past_due_invoices(self):
        """Check for past due invoices and send reminders"""
        now = datetime.now(timezone.utc)
        
        for invoice_id, invoice in self._invoices.items():
            if invoice.status == PaymentStatus.PENDING and invoice.due_date < now:
                # Send reminder
                await self._send_payment_reminder(invoice)
                
                # Update subscription status
                subscription = self._subscriptions.get(invoice.user_id)
                if subscription:
                    subscription.status = BillingStatus.PAST_DUE
                
                # Log event
                await self.events.log_event(
                    event_type="payment_reminder_sent",
                    user_id=invoice.user_id,
                    properties={
                        "invoice_id": invoice_id,
                        "days_past_due": (now - invoice.due_date).days
                    }
                )
    
    async def cancel_subscription(
        self,
        user_id: str,
        cancel_immediately: bool = False
    ) -> bool:
        """Cancel subscription"""
        subscription = self._subscriptions.get(user_id)
        if not subscription:
            return False
        
        if cancel_immediately:
            subscription.status = BillingStatus.CANCELLED
        else:
            subscription.cancel_at_period_end = True
        
        # Log event
        await self.events.log_event(
            event_type="subscription_cancelled",
            user_id=user_id,
            properties={
                "subscription_id": subscription.subscription_id,
                "cancel_immediately": cancel_immediately
            }
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "subscriptions_cancelled",
            tags={"tier": subscription.tier.value}
        )
        
        return True
    
    async def _charge_payment_method(self, invoice: Invoice, payment_method: str):
        """Charge payment method (placeholder - would use payment processor)"""
        # In production, this would use Stripe, PayPal, etc.
        logger.info(f"Charging {invoice.amount} to {payment_method} for invoice {invoice.invoice_id}")
    
    async def _send_payment_reminder(self, invoice: Invoice):
        """Send payment reminder email"""
        # In production, this would send email via email service
        logger.info(f"Sending payment reminder for invoice {invoice.invoice_id}")
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID (placeholder)"""
        return None

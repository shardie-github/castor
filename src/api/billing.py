"""
Billing API Routes

Provides endpoints for subscription management, billing, invoices, and payment methods.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import stripe

from src.payments.stripe import StripePaymentProcessor
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user

router = APIRouter()


# Pydantic Models
class SubscriptionCreate(BaseModel):
    price_id: str
    payment_method_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    price_id: str


class PaymentMethodCreate(BaseModel):
    payment_method_id: str


class InvoiceResponse(BaseModel):
    invoice_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    due_date: Optional[datetime] = None
    pdf_url: Optional[str] = None


class SubscriptionResponse(BaseModel):
    subscription_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    plan_id: str
    cancel_at_period_end: bool


def get_stripe_processor(request: Request) -> StripePaymentProcessor:
    """Get Stripe processor from app state"""
    return request.app.state.stripe_processor


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_metrics_collector(request: Request) -> MetricsCollector:
    """Get metrics collector from app state"""
    return request.app.state.metrics_collector


def get_event_logger(request: Request) -> EventLogger:
    """Get event logger from app state"""
    return request.app.state.event_logger


# API Endpoints
@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    stripe_processor: StripePaymentProcessor = Depends(get_stripe_processor),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Create a new subscription"""
    # Get or create Stripe customer
    user = await postgres_conn.fetchrow(
        "SELECT email, name, stripe_customer_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    customer_id = user.get('stripe_customer_id')
    
    if not customer_id:
        # Create Stripe customer
        customer = await stripe_processor.create_customer(
            email=user['email'],
            name=user['name'],
            metadata={'user_id': str(current_user['user_id'])}
        )
        customer_id = customer['id']
        
        # Store customer ID
        await postgres_conn.execute(
            "UPDATE users SET stripe_customer_id = $1 WHERE user_id = $2",
            customer_id,
            current_user['user_id']
        )
    
    # Attach payment method if provided
    if subscription_data.payment_method_id:
        stripe.PaymentMethod.attach(
            subscription_data.payment_method_id,
            customer=customer_id
        )
        stripe.Customer.modify(
            customer_id,
            invoice_settings={'default_payment_method': subscription_data.payment_method_id}
        )
    
    # Create subscription
    subscription = await stripe_processor.create_subscription(
        customer_id=customer_id,
        price_id=subscription_data.price_id,
        metadata={'user_id': str(current_user['user_id'])}
    )
    
    # Update user subscription tier
    tier_mapping = {
        'price_starter': 'starter',
        'price_professional': 'professional',
        'price_enterprise': 'enterprise'
    }
    tier = tier_mapping.get(subscription_data.price_id, 'starter')
    
    await postgres_conn.execute(
        """
        UPDATE users 
        SET subscription_tier = $1, stripe_subscription_id = $2
        WHERE user_id = $3
        """,
        tier,
        subscription.subscription_id,
        current_user['user_id']
    )
    
    # Log event
    await event_logger.log_event(
        event_type='subscription.created',
        user_id=str(current_user['user_id']),
        properties={
            'subscription_id': subscription.subscription_id,
            'tier': tier
        }
    )
    
    return SubscriptionResponse(
        subscription_id=subscription.subscription_id,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        plan_id=subscription.plan_id,
        cancel_at_period_end=subscription.cancel_at_period_end
    )


@router.put("/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    stripe_processor: StripePaymentProcessor = Depends(get_stripe_processor),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Update subscription (upgrade/downgrade)"""
    # Get current subscription
    user = await postgres_conn.fetchrow(
        "SELECT stripe_subscription_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_subscription_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Update subscription in Stripe
    stripe_subscription = stripe.Subscription.modify(
        user['stripe_subscription_id'],
        items=[{'price': subscription_data.price_id}],
        proration_behavior='always_invoice'
    )
    
    # Update user subscription tier
    tier_mapping = {
        'price_starter': 'starter',
        'price_professional': 'professional',
        'price_enterprise': 'enterprise'
    }
    tier = tier_mapping.get(subscription_data.price_id, 'starter')
    
    await postgres_conn.execute(
        "UPDATE users SET subscription_tier = $1 WHERE user_id = $2",
        tier,
        current_user['user_id']
    )
    
    # Log event
    await event_logger.log_event(
        event_type='subscription.updated',
        user_id=str(current_user['user_id']),
        properties={
            'subscription_id': stripe_subscription.id,
            'tier': tier
        }
    )
    
    return SubscriptionResponse(
        subscription_id=stripe_subscription.id,
        status=stripe_subscription.status,
        current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
        current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
        plan_id=subscription_data.price_id,
        cancel_at_period_end=stripe_subscription.cancel_at_period_end
    )


@router.post("/subscription/cancel")
async def cancel_subscription(
    cancel_immediately: bool = False,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    stripe_processor: StripePaymentProcessor = Depends(get_stripe_processor),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """Cancel subscription"""
    # Get current subscription
    user = await postgres_conn.fetchrow(
        "SELECT stripe_subscription_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_subscription_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Cancel subscription
    subscription = await stripe_processor.cancel_subscription(
        user['stripe_subscription_id'],
        cancel_immediately=cancel_immediately
    )
    
    # Update user subscription tier
    if cancel_immediately:
        await postgres_conn.execute(
            "UPDATE users SET subscription_tier = 'free', stripe_subscription_id = NULL WHERE user_id = $1",
            current_user['user_id']
        )
    
    # Log event
    await event_logger.log_event(
        event_type='subscription.cancelled',
        user_id=str(current_user['user_id']),
        properties={
            'subscription_id': subscription.subscription_id,
            'cancel_immediately': cancel_immediately
        }
    )
    
    return {"message": "Subscription cancelled successfully"}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get current subscription"""
    user = await postgres_conn.fetchrow(
        "SELECT stripe_subscription_id, subscription_tier FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_subscription_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Get subscription from Stripe
    stripe_subscription = stripe.Subscription.retrieve(user['stripe_subscription_id'])
    
    return SubscriptionResponse(
        subscription_id=stripe_subscription.id,
        status=stripe_subscription.status,
        current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
        current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
        plan_id=stripe_subscription.items.data[0].price.id if stripe_subscription.items.data else "",
        cancel_at_period_end=stripe_subscription.cancel_at_period_end
    )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get invoice history"""
    user = await postgres_conn.fetchrow(
        "SELECT stripe_customer_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_customer_id'):
        return []
    
    # Get invoices from Stripe
    invoices = stripe.Invoice.list(customer=user['stripe_customer_id'], limit=100)
    
    return [
        InvoiceResponse(
            invoice_id=inv.id,
            amount=inv.amount_paid / 100,
            currency=inv.currency,
            status=inv.status,
            created_at=datetime.fromtimestamp(inv.created),
            due_date=datetime.fromtimestamp(inv.due_date) if inv.due_date else None,
            pdf_url=inv.invoice_pdf
        )
        for inv in invoices.data
    ]


@router.post("/payment-methods")
async def add_payment_method(
    payment_method_data: PaymentMethodCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Add payment method"""
    user = await postgres_conn.fetchrow(
        "SELECT stripe_customer_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_customer_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found. Please create a subscription first."
        )
    
    # Attach payment method
    stripe.PaymentMethod.attach(
        payment_method_data.payment_method_id,
        customer=user['stripe_customer_id']
    )
    
    # Set as default
    stripe.Customer.modify(
        user['stripe_customer_id'],
        invoice_settings={'default_payment_method': payment_method_data.payment_method_id}
    )
    
    return {"message": "Payment method added successfully"}


@router.get("/payment-methods")
async def get_payment_methods(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get payment methods"""
    user = await postgres_conn.fetchrow(
        "SELECT stripe_customer_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_customer_id'):
        return []
    
    # Get payment methods from Stripe
    payment_methods = stripe.PaymentMethod.list(
        customer=user['stripe_customer_id'],
        type='card'
    )
    
    return [
        {
            "id": pm.id,
            "type": pm.type,
            "card": {
                "brand": pm.card.brand,
                "last4": pm.card.last4,
                "exp_month": pm.card.exp_month,
                "exp_year": pm.card.exp_year
            } if pm.card else None
        }
        for pm in payment_methods.data
    ]


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Delete payment method"""
    user = await postgres_conn.fetchrow(
        "SELECT stripe_customer_id FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user.get('stripe_customer_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Detach payment method
    stripe.PaymentMethod.detach(payment_method_id)
    
    return {"message": "Payment method deleted successfully"}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    stripe_processor: StripePaymentProcessor = Depends(get_stripe_processor),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Handle Stripe webhook events"""
    import os
    payload = await request.body()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    try:
        event = await stripe_processor.process_webhook(
            payload,
            stripe_signature,
            webhook_secret
        )
        
        # Handle subscription updates in database
        if event.type in ["customer.subscription.updated", "customer.subscription.deleted"]:
            subscription = event.data.object
            customer_id = subscription.get("customer")
            
            # Find user by customer ID
            user = await postgres_conn.fetchrow(
                "SELECT user_id FROM users WHERE stripe_customer_id = $1",
                customer_id
            )
            
            if user and event.type == "customer.subscription.deleted":
                await postgres_conn.execute(
                    "UPDATE users SET subscription_tier = 'free', stripe_subscription_id = NULL WHERE user_id = $1",
                    user['user_id']
                )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {str(e)}"
        )

"""
Integration tests for Stripe payment processing
"""

import pytest
from src.payments.stripe import StripePaymentProcessor
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger


@pytest.mark.asyncio
async def test_stripe_customer_creation():
    """Test Stripe customer creation"""
    processor = StripePaymentProcessor(
        MetricsCollector(),
        EventLogger()
    )
    
    # Use test mode
    import stripe
    stripe.api_key = "sk_test_..."  # Use test key
    
    try:
        customer = await processor.create_customer(
            email="test@example.com",
            name="Test User"
        )
        
        assert customer.id is not None
        assert customer.email == "test@example.com"
        
    except stripe.error.InvalidRequestError:
        pytest.skip("Stripe test key not configured")


@pytest.mark.asyncio
async def test_stripe_payment_intent():
    """Test Stripe payment intent creation"""
    processor = StripePaymentProcessor(
        MetricsCollector(),
        EventLogger()
    )
    
    import stripe
    stripe.api_key = "sk_test_..."  # Use test key
    
    try:
        intent = await processor.create_payment_intent(
            amount=10.00,
            currency="usd"
        )
        
        assert intent.intent_id is not None
        assert intent.amount == 10.00
        assert intent.currency == "usd"
        
    except stripe.error.InvalidRequestError:
        pytest.skip("Stripe test key not configured")

# Monetization Guide

**DELTA:20251113_064143**

This guide covers all monetization features including agency/consultancy management, affiliate marketing, AI token billing, white-labeling, and API usage tracking.

## Overview

The monetization system provides multiple revenue streams:

1. **Agency/Consultancy** - Manage agencies and track commissions
2. **Affiliate Marketing** - Referral program with commission tracking
3. **AI Token Billing** - Pay-per-use AI features (content generation, ad generation, analytics)
4. **White-Labeling** - Custom branding for enterprise customers
5. **API Usage Tracking** - Metered API billing
6. **Subscription Tiers** - Tiered pricing with feature limits

## Feature Flags

Enable monetization features:

```bash
export ENABLE_MONETIZATION=true
```

## Agency/Consultancy Management

### Create Agency

```bash
POST /api/v1/monetization/agencies
{
  "name": "Acme Media Agency",
  "slug": "acme-media",
  "contact_email": "contact@acme.com",
  "commission_rate_percent": 15.0
}
```

### List Agencies

```bash
GET /api/v1/monetization/agencies?status=active
```

Agencies can be associated with campaigns and earn commissions on transactions.

## Affiliate Marketing

### Create Affiliate

```bash
POST /api/v1/monetization/affiliates
{
  "name": "John Doe",
  "email": "john@example.com",
  "commission_rate_percent": 10.0
}
```

Returns a unique `referral_code` that affiliates can share.

### Track Referral

When a new tenant signs up with a referral code:

```bash
POST /api/v1/monetization/affiliates/track?referral_code=ABC123XYZ&referred_tenant_id=<tenant_id>
```

### Convert Referral

When referred tenant subscribes:

```python
from src.monetization.affiliate_manager import AffiliateManager

manager = AffiliateManager(...)
result = await manager.convert_referral(
    referral_id=referral_id,
    tenant_id=tenant_id,
    conversion_value_cents=50000  # $500 subscription
)
# Returns commission_cents calculated automatically
```

### Get Affiliate Stats

```bash
GET /api/v1/monetization/affiliates/{affiliate_id}/stats
```

## AI Token Billing

### Pricing

- **$0.10 per 1,000 tokens** (configurable via `AITokenManager.TOKEN_PRICE_CENTS_PER_1K`)

### Purchase Tokens

```bash
POST /api/v1/monetization/ai-tokens/purchase
{
  "tokens_to_purchase": 100000,  # 100K tokens = $10
  "transaction_id": "stripe_payment_123"
}
```

### Check Balance

```bash
GET /api/v1/monetization/ai-tokens/balance
```

### Use Tokens

```python
from src.monetization.ai_token_manager import AITokenManager

manager = AITokenManager(...)

# Use tokens for AI feature
result = await manager.use_tokens(
    tenant_id=tenant_id,
    tokens_used=5000,  # ~$0.50
    feature_type='content_generation',
    user_id=user_id,
    request_id=request_id
)
```

### Usage History

```bash
GET /api/v1/monetization/ai-tokens/usage?limit=100
```

## API Usage Tracking

### Automatic Tracking

API calls are automatically tracked via `APIUsageMiddleware` when monetization is enabled.

### Pricing

- **$0.05 per 1,000 API calls** (configurable via `APIUsageTracker.API_PRICE_CENTS_PER_1K`)
- Only successful calls (status < 400) are charged

### Get Usage Summary

```bash
GET /api/v1/monetization/api-usage/summary
```

Returns:
- Total calls
- Successful/failed calls
- Total cost
- Average response time

### Rate Limiting

```bash
GET /api/v1/monetization/api-usage/rate-limit?limit_per_hour=1000
```

## White-Labeling

### Get Settings

```bash
GET /api/v1/monetization/white-label
```

### Update Settings

```bash
PUT /api/v1/monetization/white-label
{
  "brand_name": "Acme Podcast Platform",
  "logo_url": "https://example.com/logo.png",
  "primary_color": "#3b82f6",
  "secondary_color": "#10b981",
  "custom_domain": "podcasts.acme.com",
  "custom_css": ".custom-class { ... }",
  "email_from_name": "Acme Podcasts",
  "email_from_address": "noreply@acme.com",
  "support_email": "support@acme.com",
  "support_url": "https://support.acme.com",
  "enabled": true
}
```

White-label settings are applied to:
- Email templates
- Dashboard UI (via custom CSS)
- API responses (branding)
- Support links

## Subscription Tiers

Subscription tiers are stored in `subscription_tiers` table and can include:

- Monthly price
- AI tokens included
- API calls included
- Advanced analytics enabled
- White-label enabled
- Limits (podcasts, episodes, users)

Example tiers:

| Tier | Price | AI Tokens | API Calls | Features |
|------|-------|-----------|-----------|----------|
| Free | $0 | 0 | 1,000/month | Basic |
| Starter | $29 | 10,000 | 10,000/month | Standard |
| Professional | $99 | 100,000 | 100,000/month | Advanced analytics |
| Enterprise | Custom | Unlimited | Unlimited | White-label, custom |

## Billing Transactions

All monetization transactions are recorded in `billing_transactions` table:

- Subscription payments
- AI token purchases
- API usage charges
- Commission payouts
- Affiliate payouts

## Database Schema

See migrations:
- `migrations/20251113_064143/04_monetization_schema.sql`
- `migrations/20251113_064143/05_monetization_policies.sql`

## Integration Examples

### AI Content Generation with Token Billing

```python
from src.monetization.ai_token_manager import AITokenManager

async def generate_content(tenant_id: str, prompt: str):
    token_manager = AITokenManager(...)
    
    # Estimate tokens (simplified)
    estimated_tokens = len(prompt.split()) * 1.3  # Rough estimate
    
    # Check balance
    balance = await token_manager.get_balance(tenant_id)
    if balance['tokens_remaining'] < estimated_tokens:
        raise ValueError("Insufficient tokens")
    
    # Generate content (call AI service)
    result = await ai_service.generate(prompt)
    actual_tokens = result['tokens_used']
    
    # Deduct tokens
    await token_manager.use_tokens(
        tenant_id=tenant_id,
        tokens_used=actual_tokens,
        feature_type='content_generation',
        request_id=result['request_id']
    )
    
    return result['content']
```

### API Rate Limiting

```python
from src.monetization.api_usage_tracker import APIUsageTracker

async def check_rate_limit(tenant_id: str):
    tracker = APIUsageTracker(...)
    limit_check = await tracker.check_rate_limit(tenant_id, limit_per_hour=1000)
    
    if limit_check['exceeded']:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return limit_check['remaining']
```

## Revenue Reporting

Query `billing_transactions` table for revenue reports:

```sql
-- Monthly revenue by type
SELECT 
    transaction_type,
    DATE_TRUNC('month', created_at) as month,
    SUM(amount_cents) as revenue_cents
FROM billing_transactions
WHERE status = 'completed'
GROUP BY transaction_type, month
ORDER BY month DESC;
```

## Best Practices

1. **Token Management**: Monitor token balances and set up alerts for low balances
2. **Rate Limiting**: Set appropriate limits per subscription tier
3. **Commission Tracking**: Automatically calculate commissions on conversions
4. **White-Labeling**: Test custom domains and CSS thoroughly
5. **Billing**: Reconcile transactions with payment provider regularly

## Troubleshooting

### Tokens not deducting
- Check `ai_token_balances` table
- Verify `use_tokens()` is called after successful AI operations
- Check for errors in `ai_token_usage` table

### API calls not tracking
- Ensure `ENABLE_MONETIZATION=true`
- Verify `APIUsageMiddleware` is added to FastAPI app
- Check middleware is not skipping endpoints

### Affiliate conversions not recording
- Verify referral is tracked before conversion
- Check `referrals` table for conversion_status
- Ensure commission rates are set correctly

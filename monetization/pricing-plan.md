# Tiered Monetization Plan

## Overview

This document defines the tiered monetization plan with price points informed by persona willingness-to-pay (WTP) and value metrics. It includes automated freemium conversion/upsell logic and links pricing events to actual product use and segment signals.

## Pricing Tiers

### Tier 1: Free
**Target Persona:** Solo Podcaster (early stage), Trial Users

**Price:** $0/month

**Features:**
- 1 podcast
- Basic analytics (downloads, streams)
- 1 campaign per month
- Basic report generation (limited templates)
- Community support
- Attribution tracking (promo codes only)

**Limitations:**
- No ROI calculations
- No automated reports
- No API access
- No white-labeling
- Limited historical data (30 days)

**Conversion Triggers:**
- User generates 3+ reports
- User creates 2+ campaigns
- User views dashboard 10+ times
- User exports data 5+ times
- Campaign renewal rate >50%

**Conversion Logic:**
```python
if (
    reports_generated >= 3 or
    campaigns_created >= 2 or
    dashboard_views >= 10 or
    data_exports >= 5 or
    renewal_rate > 0.5
) and days_since_signup >= 7:
    trigger_upsell_to_starter()
```

**WTP Data:**
- Solo Podcaster: $0-29/month
- Average: $15/month

---

### Tier 2: Starter
**Target Persona:** Solo Podcaster (growing), Small Producers

**Price:** $29/month (or $290/year - save 17%)

**Features:**
- 3 podcasts
- Advanced analytics (engagement, completion rates)
- Unlimited campaigns
- Automated report generation
- ROI calculations
- Email support
- Attribution tracking (promo codes + pixels)
- Report templates (5 templates)
- Historical data (90 days)

**Value Metrics:**
- Time saved: 2 hours/week → $116/month value
- Revenue increase: 20% higher renewal rate → $200-500/month value
- Professional image: Improved sponsor relationships

**Conversion Triggers:**
- User manages 5+ campaigns simultaneously
- User generates 10+ reports/month
- User requests API access
- User needs white-labeling
- User manages multiple podcasts (4+)
- User requests team features

**Conversion Logic:**
```python
if (
    active_campaigns >= 5 or
    monthly_reports >= 10 or
    api_access_requested or
    white_label_requested or
    podcasts_count >= 4 or
    team_features_requested
) and subscription_age >= 30:
    trigger_upsell_to_professional()
```

**WTP Data:**
- Solo Podcaster: $29-79/month
- Producer: $50-150/month
- Average: $45/month

---

### Tier 3: Professional
**Target Persona:** Producers, Small Agencies, Growing Solo Podcasters

**Price:** $99/month (or $990/year - save 17%)

**Features:**
- 10 podcasts
- All Starter features
- API access
- White-label reports
- Advanced attribution (multi-touch)
- Custom report templates
- Priority support
- Historical data (1 year)
- Campaign comparison tools
- Performance alerts
- Bulk operations
- Export to data warehouse

**Value Metrics:**
- Time saved: 5 hours/week → $290/month value
- Revenue increase: 30% higher renewal rate → $500-1500/month value
- Scalability: Manage 10+ shows efficiently
- API integration: Custom workflows

**Conversion Triggers:**
- User manages 15+ campaigns
- User manages 10+ podcasts
- User needs team collaboration
- User requests custom integrations
- User needs advanced security/compliance
- User requests dedicated support

**Conversion Logic:**
```python
if (
    active_campaigns >= 15 or
    podcasts_count >= 10 or
    team_collaboration_requested or
    custom_integrations_requested or
    compliance_requirements or
    dedicated_support_requested
) and subscription_age >= 60:
    trigger_upsell_to_enterprise()
```

**WTP Data:**
- Producer: $99-299/month
- Agency: $150-500/month
- Average: $120/month

---

### Tier 4: Enterprise
**Target Persona:** Large Agencies, Networks, Enterprise Brands

**Price:** Custom pricing (starts at $499/month)

**Features:**
- Unlimited podcasts
- All Professional features
- Team collaboration (unlimited users)
- Role-based access control
- SSO/SAML authentication
- Dedicated account manager
- Custom integrations
- SLA guarantees (99.9% uptime)
- Advanced security & compliance
- Custom reporting & analytics
- Data warehouse integration
- White-label portal
- Priority feature requests

**Value Metrics:**
- Time saved: 10+ hours/week → $580+/month value
- Revenue increase: 40% higher renewal rate → $2000+/month value
- Team efficiency: 2x clients per team member
- Custom workflows: Integrated with existing stack

**WTP Data:**
- Agency: $500-2000/month
- Enterprise: $1000-5000/month
- Average: $1500/month

---

## Automated Conversion Logic

### Freemium to Paid Conversion

**Trigger Events:**
1. **Value Realization:** User generates first report
2. **Engagement:** User views dashboard 5+ times
3. **Feature Limitation:** User hits free tier limit
4. **Time-Based:** User active for 7+ days

**Conversion Flow:**
```python
def check_freemium_conversion(user_id: str):
    user = get_user(user_id)
    if user.subscription_tier != SubscriptionTier.FREE:
        return
    
    # Check conversion signals
    signals = {
        "reports_generated": count_reports(user_id),
        "campaigns_created": count_campaigns(user_id),
        "dashboard_views": count_dashboard_views(user_id),
        "data_exports": count_exports(user_id),
        "days_active": days_since_signup(user_id),
        "renewal_rate": calculate_renewal_rate(user_id)
    }
    
    # Calculate conversion score
    conversion_score = (
        (signals["reports_generated"] >= 3) * 20 +
        (signals["campaigns_created"] >= 2) * 20 +
        (signals["dashboard_views"] >= 10) * 15 +
        (signals["data_exports"] >= 5) * 15 +
        (signals["days_active"] >= 7) * 10 +
        (signals["renewal_rate"] > 0.5) * 20
    )
    
    if conversion_score >= 50:
        trigger_upsell_notification(user_id, "starter")
```

### Upsell Logic

**Starter → Professional:**
- User hits campaign limit (5+ active campaigns)
- User requests API access
- User needs white-labeling
- User manages multiple podcasts (4+)

**Professional → Enterprise:**
- User hits podcast limit (10+ podcasts)
- User requests team features
- User needs custom integrations
- User requests dedicated support

**Upsell Timing:**
- **Immediate:** User hits hard limit (campaigns, podcasts)
- **Proactive:** User shows high engagement (10+ reports/month)
- **Time-Based:** After 30 days on current tier
- **Value-Based:** User achieves significant ROI

---

## Pricing Event Tracking

### Events Linked to Product Use

**Usage-Based Events:**
```python
# Campaign creation
log_pricing_event(
    event_type="campaign_created",
    user_id=user_id,
    properties={
        "subscription_tier": user.subscription_tier,
        "campaign_count": user_campaign_count,
        "tier_limit": tier_limits[user.subscription_tier]["campaigns"]
    }
)

# Report generation
log_pricing_event(
    event_type="report_generated",
    user_id=user_id,
    properties={
        "subscription_tier": user.subscription_tier,
        "monthly_report_count": monthly_reports,
        "tier_limit": tier_limits[user.subscription_tier]["reports"]
    }
)

# API usage
log_pricing_event(
    event_type="api_call",
    user_id=user_id,
    properties={
        "subscription_tier": user.subscription_tier,
        "api_calls_this_month": api_calls,
        "tier_limit": tier_limits[user.subscription_tier]["api_calls"]
    }
)
```

### Segment Signals

**Persona-Based Pricing:**
```python
def get_recommended_tier(persona_segment: str, usage_metrics: dict) -> SubscriptionTier:
    """Recommend tier based on persona and usage"""
    
    persona_tier_mapping = {
        "solo_podcaster": {
            "low": SubscriptionTier.FREE,
            "medium": SubscriptionTier.STARTER,
            "high": SubscriptionTier.PROFESSIONAL
        },
        "producer": {
            "low": SubscriptionTier.STARTER,
            "medium": SubscriptionTier.PROFESSIONAL,
            "high": SubscriptionTier.ENTERPRISE
        },
        "agency": {
            "low": SubscriptionTier.PROFESSIONAL,
            "medium": SubscriptionTier.ENTERPRISE,
            "high": SubscriptionTier.ENTERPRISE
        }
    }
    
    # Calculate usage level
    usage_level = calculate_usage_level(usage_metrics)
    
    return persona_tier_mapping.get(persona_segment, {}).get(usage_level, SubscriptionTier.STARTER)
```

---

## Revenue Optimization

### Pricing Strategy

1. **Value-Based Pricing:** Price based on value delivered (time saved, revenue increase)
2. **Usage-Based Upsells:** Upsell when users hit limits
3. **Persona-Specific Pricing:** Adjust messaging based on persona
4. **Annual Discounts:** 17% discount for annual plans

### Conversion Funnels

**Free → Starter:**
- Target: 10% conversion rate
- Average time to convert: 14 days
- Key trigger: First report generation

**Starter → Professional:**
- Target: 25% conversion rate
- Average time to convert: 60 days
- Key trigger: API access request

**Professional → Enterprise:**
- Target: 15% conversion rate
- Average time to convert: 90 days
- Key trigger: Team collaboration request

### Churn Prevention

**Risk Signals:**
- Low engagement (<5 dashboard views/month)
- No reports generated in 30 days
- Support tickets increasing
- Feature requests denied (tier limitations)

**Retention Actions:**
- Proactive outreach for at-risk users
- Feature education campaigns
- Success story sharing
- Discount offers for annual plans

---

## Implementation

### Pricing Module

See `src/monetization/pricing.py` for implementation of:
- Tier management
- Conversion logic
- Usage tracking
- Upsell triggers
- Pricing event logging

### Integration Points

1. **User Management:** Track subscription tier
2. **Feature Flags:** Enable/disable features by tier
3. **Usage Tracking:** Monitor feature usage for upsell triggers
4. **Event Logging:** Log pricing events for analytics
5. **Billing Integration:** Connect to Stripe/Chargebee

---

*Last Updated: [Current Date]*
*Version: 1.0*

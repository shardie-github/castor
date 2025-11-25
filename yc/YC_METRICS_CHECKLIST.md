# YC Metrics Checklist

**For:** YC Application & Interview Prep  
**Last Updated:** 2024

---

## Overview

YC partners expect founders to know their numbers cold. This document maps what metrics are instrumented in the repo vs. what YC will ask for, and proposes how to close the gaps.

---

## A. USAGE METRICS

### Proposed Metrics

#### 1. Daily/Weekly/Monthly Active Users (DAU/WAU/MAU)

**Definition:**
- **DAU:** Users who logged in or performed any action in the last 24 hours
- **WAU:** Users active in the last 7 days
- **MAU:** Users active in the last 30 days

**Current State:**
- ✅ **Instrumented:** Event logging system (`src/telemetry/events.py`) tracks user actions
- ✅ **Storage:** Events stored in PostgreSQL `events` table
- ⚠️ **Missing:** Aggregation queries for DAU/WAU/MAU

**Where It's Instrumented:**
- `src/telemetry/events.py` - Event logging
- `src/telemetry/metrics.py` - Metrics collection
- Database: `events` table (user_id, timestamp, event_type)

**How to Calculate:**
```sql
-- DAU
SELECT COUNT(DISTINCT user_id) 
FROM events 
WHERE timestamp >= NOW() - INTERVAL '24 hours';

-- WAU
SELECT COUNT(DISTINCT user_id) 
FROM events 
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- MAU
SELECT COUNT(DISTINCT user_id) 
FROM events 
WHERE timestamp >= NOW() - INTERVAL '30 days';
```

**Proposed Implementation:**
- Add daily aggregation job (`src/analytics/user_metrics_aggregator.py`)
- Create `user_metrics_daily` table (or use existing `metrics_daily` view)
- Expose via API endpoint: `GET /api/v1/metrics/users/active`

**Files to Create/Modify:**
- `src/analytics/user_metrics_aggregator.py` (new)
- `src/api/metrics.py` (add endpoint)
- Database migration: Add `user_metrics_daily` table if needed

---

#### 2. Activation Rate

**Definition:**
- **Activation:** User completes onboarding AND generates first value (report, campaign, or attribution setup)
- **Activation Rate:** % of signups who activate within 7 days

**Current State:**
- ✅ **Instrumented:** Onboarding events tracked (`validation/analytics-events.md`)
- ✅ **Events:** `onboarding_started`, `onboarding_completed`, `first_value_delivered`
- ⚠️ **Missing:** Activation calculation logic

**Where It's Instrumented:**
- `src/telemetry/events.py` - Event logging
- `validation/analytics-events.md` - Event definitions
- Database: `events` table

**How to Calculate:**
```sql
-- Activation Rate (7-day window)
WITH signups AS (
  SELECT user_id, MIN(timestamp) as signup_time
  FROM events
  WHERE event_type = 'onboarding_started'
  GROUP BY user_id
),
activations AS (
  SELECT DISTINCT user_id
  FROM events
  WHERE event_type IN ('report_generated', 'campaign_launched', 'attribution_setup_completed')
)
SELECT 
  COUNT(DISTINCT a.user_id) * 100.0 / COUNT(DISTINCT s.user_id) as activation_rate
FROM signups s
LEFT JOIN activations a ON s.user_id = a.user_id
WHERE s.signup_time >= NOW() - INTERVAL '30 days';
```

**Proposed Implementation:**
- Add activation calculation to `src/business/analytics.py`
- Expose via API: `GET /api/v1/metrics/activation`

**Target:** >70% activation rate (from `validation/analytics-events.md`)

---

#### 3. Retention Rate

**Definition:**
- **Retention:** User returns after initial activation
- **Day 1 Retention:** % of activated users who return on day 1
- **Day 7 Retention:** % of activated users who return on day 7
- **Day 30 Retention:** % of activated users who return on day 30

**Current State:**
- ✅ **Instrumented:** Event logging tracks user activity
- ⚠️ **Missing:** Retention calculation logic

**Where It's Instrumented:**
- `src/telemetry/events.py` - Event logging
- Database: `events` table

**How to Calculate:**
```sql
-- Day 7 Retention
WITH activations AS (
  SELECT user_id, MIN(timestamp) as activation_time
  FROM events
  WHERE event_type IN ('report_generated', 'campaign_launched', 'attribution_setup_completed')
  GROUP BY user_id
),
returns AS (
  SELECT DISTINCT a.user_id
  FROM activations a
  JOIN events e ON a.user_id = e.user_id
  WHERE e.timestamp >= a.activation_time + INTERVAL '7 days'
    AND e.timestamp < a.activation_time + INTERVAL '8 days'
)
SELECT 
  COUNT(DISTINCT r.user_id) * 100.0 / COUNT(DISTINCT a.user_id) as day_7_retention
FROM activations a
LEFT JOIN returns r ON a.user_id = r.user_id
WHERE a.activation_time >= NOW() - INTERVAL '60 days';
```

**Proposed Implementation:**
- Add retention calculation to `src/business/analytics.py`
- Expose via API: `GET /api/v1/metrics/retention`

**Target:** >40% Day 7 retention, >20% Day 30 retention

---

#### 4. Engagement Metrics

**Definition:**
- **Dashboard Views:** Average dashboard views per active user per week
- **Reports Generated:** Average reports per active user per month
- **Campaigns Created:** Average campaigns per active user per month
- **Attribution Events Tracked:** Average attribution events per campaign

**Current State:**
- ✅ **Instrumented:** Events tracked (`dashboard_viewed`, `report_generated`, `campaign_created`, `attribution_setup_completed`)
- ⚠️ **Missing:** Aggregation queries

**Where It's Instrumented:**
- `src/telemetry/events.py` - Event logging
- `validation/analytics-events.md` - Event definitions
- Database: `events` table

**How to Calculate:**
```sql
-- Engagement Metrics (Last 30 Days)
SELECT 
  COUNT(DISTINCT user_id) as active_users,
  COUNT(*) FILTER (WHERE event_type = 'dashboard_viewed') as dashboard_views,
  COUNT(*) FILTER (WHERE event_type = 'report_generated') as reports_generated,
  COUNT(*) FILTER (WHERE event_type = 'campaign_created') as campaigns_created,
  COUNT(*) FILTER (WHERE event_type = 'attribution_setup_completed') as attribution_setups
FROM events
WHERE timestamp >= NOW() - INTERVAL '30 days';
```

**Proposed Implementation:**
- Add engagement metrics to `src/business/analytics.py`
- Expose via API: `GET /api/v1/metrics/engagement`

**Targets:**
- Dashboard views: >5 per active user per week
- Reports generated: >1 per active user per month
- Campaigns created: >2 per active user per month

---

## B. GROWTH & ACQUISITION

### Where Users Come From

**Current State:**
- ⚠️ **Partially Instrumented:** Event logging has `source` property in `onboarding_started` event
- ⚠️ **Missing:** UTM parameter tracking, referral tracking

**Where It's Instrumented:**
- `validation/analytics-events.md` - `onboarding_started` event has `source` property
- `src/telemetry/events.py` - Event logging

**Proposed Implementation:**
- Add UTM parameter tracking to signup flow
- Add referral code tracking
- Track source in `users` table: `signup_source`, `utm_source`, `utm_medium`, `utm_campaign`, `referral_code`

**Files to Modify:**
- `src/api/auth.py` (signup endpoint) - Capture UTM parameters
- Database migration: Add columns to `users` table
- `src/telemetry/events.py` - Include UTM parameters in events

---

### Proposed Funnel

**Funnel Stages:**
1. **Visitor** → Lands on website
2. **Signup** → Creates account
3. **Activated** → Completes onboarding + generates first value
4. **Retained** → Returns after activation
5. **Paying** → Converts to paid tier

**Current State:**
- ✅ **Stage 1 (Visitor):** Not instrumented (needs frontend analytics)
- ✅ **Stage 2 (Signup):** Instrumented (`onboarding_started` event)
- ✅ **Stage 3 (Activated):** Instrumented (`first_value_delivered` event)
- ✅ **Stage 4 (Retained):** Instrumented (event logging)
- ✅ **Stage 5 (Paying):** Instrumented (`pricing` events, `subscription_tier` in users table)

**Where It's Instrumented:**
- `src/telemetry/events.py` - Event logging
- `src/monetization/pricing.py` - Conversion tracking
- Database: `users` table (subscription_tier), `events` table

**Proposed Implementation:**
- Add frontend analytics (Google Analytics, PostHog, or Mixpanel) for visitor tracking
- Create funnel calculation in `src/business/analytics.py`
- Expose via API: `GET /api/v1/metrics/funnel`

**Target Conversion Rates:**
- Visitor → Signup: 5-10%
- Signup → Activated: >70%
- Activated → Retained (Day 7): >40%
- Retained → Paying: 10-15%

---

## C. REVENUE & UNIT ECONOMICS

### How The Product Makes Money

**Business Model:**
- **Freemium:** Free tier → Starter ($29/mo) → Professional ($99/mo) → Enterprise (custom)
- **Usage-Based:** API calls, additional features
- **White-Label:** Enterprise licensing

**Current State:**
- ✅ **Instrumented:** Pricing logic (`src/monetization/pricing.py`)
- ✅ **Instrumented:** Revenue tracking (`src/business/analytics.py`)
- ✅ **Instrumented:** API usage tracking (`src/monetization/api_usage_tracker.py`)
- ⚠️ **Missing:** Stripe/billing integration (assumed, not visible in repo)

**Where It's Instrumented:**
- `src/monetization/pricing.py` - Tier management, conversion logic
- `src/business/analytics.py` - Revenue metrics calculation
- `src/monetization/api_usage_tracker.py` - API usage/cost tracking
- Database: `payments` table (assumed), `users` table (subscription_tier)

---

### Suggested Metrics

#### 1. ARPU (Average Revenue Per User)

**Definition:** Total monthly recurring revenue / Total paying users

**Current State:**
- ✅ **Instrumented:** `src/business/analytics.py` - `average_revenue_per_user` calculated

**How It's Calculated:**
```python
# From src/business/analytics.py
avg_revenue_per_user = (
    total_revenue / paying_customers if paying_customers > 0 else 0
)
```

**Target:** $29-99/month (depending on tier mix)

---

#### 2. ACV (Annual Contract Value)

**Definition:** ARPU × 12 (for annual plans, use actual ACV)

**Current State:**
- ⚠️ **Missing:** Annual plan tracking (pricing plan mentions 17% discount for annual)

**Proposed Implementation:**
- Track annual vs. monthly plans in `subscriptions` table
- Calculate ACV: `monthly_price * 12` for monthly, `annual_price` for annual

---

#### 3. Gross Margin Drivers

**Cost Components:**
- **Infrastructure:** Database (PostgreSQL/TimescaleDB), Redis, compute
- **Third-Party APIs:** Attribution APIs, analytics APIs (if used)
- **Support:** Customer support costs

**Current State:**
- ✅ **Instrumented:** Cost tracking (`src/cost/cost_tracker.py`)
- ✅ **Instrumented:** API usage tracking (`src/monetization/api_usage_tracker.py`)
- ⚠️ **Missing:** Gross margin calculation

**Where It's Instrumented:**
- `src/cost/cost_tracker.py` - Resource usage tracking
- `src/monetization/api_usage_tracker.py` - API call costs
- Database: `cost_tracking` table (assumed)

**Proposed Implementation:**
- Add gross margin calculation to `src/business/analytics.py`
- Track infrastructure costs per tenant
- Calculate: `(Revenue - COGS) / Revenue`

**Target:** >70% gross margin (SaaS benchmark)

---

#### 4. CAC (Customer Acquisition Cost)

**Definition:** Total marketing/sales spend / New customers acquired

**Current State:**
- ⚠️ **Missing:** Marketing spend tracking

**Proposed Implementation:**
- Track marketing spend by channel (ads, content, events)
- Calculate CAC: `total_marketing_spend / new_customers`
- Track CAC by channel: `channel_spend / channel_customers`

**Files to Create:**
- `src/marketing/spend_tracker.py` (new)
- Database: `marketing_spend` table (new)

**Target:** CAC < $100 (for $29-99/month ARPU)

---

#### 5. Payback Period

**Definition:** CAC / (ARPU × Gross Margin %)

**Current State:**
- ⚠️ **Missing:** Payback period calculation

**Proposed Implementation:**
- Calculate: `CAC / (ARPU * gross_margin_percentage)`
- Add to `src/business/analytics.py`

**Target:** <12 months payback period

---

#### 6. LTV (Lifetime Value)

**Definition:** ARPU × Average Customer Lifetime (months)

**Current State:**
- ✅ **Instrumented:** `src/business/analytics.py` - `lifetime_value` calculated (simplified)

**How It's Calculated:**
```python
# From src/business/analytics.py (simplified)
avg_monthly_revenue = recurring_revenue / max(period_days / 30, 1)
avg_customer_lifetime_months = 12  # Simplified assumption
lifetime_value = avg_monthly_revenue * avg_customer_lifetime_months
```

**Proposed Improvement:**
- Calculate actual customer lifetime from churn data
- Use: `ARPU / churn_rate` (if churn rate is monthly)

**Target:** LTV > 3× CAC

---

### Minimal Data to Capture

**If Missing Revenue Data:**
1. **Subscription Events:** Track subscription creation, renewal, cancellation
2. **Payment Events:** Track payment success, failure, refund
3. **Usage Events:** Track feature usage (reports, campaigns, API calls)
4. **Conversion Events:** Track freemium → paid conversions

**Minimal Schema Changes:**
- `subscriptions` table: `tenant_id`, `tier`, `status`, `created_at`, `cancelled_at`, `renewal_date`
- `payments` table: `subscription_id`, `amount`, `status`, `created_at`
- `usage_events` table: `tenant_id`, `feature`, `usage_count`, `period_start`, `period_end`

---

## D. METRICS DASHBOARD REQUIREMENTS

### What Founders Should Have Handy

**Daily Metrics:**
- DAU, WAU, MAU
- New signups
- Activation rate (7-day)
- Revenue (MRR)

**Weekly Metrics:**
- Funnel conversion rates
- Retention (Day 1, 7, 30)
- Engagement metrics
- CAC by channel

**Monthly Metrics:**
- ARPU, ACV
- LTV, CAC, Payback Period
- Gross margin
- Churn rate

**See:** `YC_METRICS_DASHBOARD_SKETCH.md` for dashboard design

---

## E. GAPS SUMMARY

### High Priority (YC Will Ask)

1. **DAU/WAU/MAU** - ⚠️ Missing aggregation queries
2. **Activation Rate** - ⚠️ Missing calculation logic
3. **Retention Rate** - ⚠️ Missing calculation logic
4. **CAC** - ⚠️ Missing marketing spend tracking
5. **LTV** - ⚠️ Needs improvement (currently simplified)

### Medium Priority

1. **Engagement Metrics** - ⚠️ Missing aggregation queries
2. **Funnel Tracking** - ⚠️ Missing visitor tracking (frontend analytics)
3. **Gross Margin** - ⚠️ Missing calculation
4. **Payback Period** - ⚠️ Missing calculation

### Low Priority

1. **ACV** - ⚠️ Missing annual plan tracking
2. **UTM Tracking** - ⚠️ Missing implementation

---

## F. IMPLEMENTATION PRIORITY

### Week 1: Core Usage Metrics
- [ ] Add DAU/WAU/MAU aggregation queries
- [ ] Add activation rate calculation
- [ ] Add retention rate calculation
- [ ] Expose via API endpoints

### Week 2: Revenue Metrics
- [ ] Add CAC tracking (marketing spend)
- [ ] Improve LTV calculation (use actual churn data)
- [ ] Add gross margin calculation
- [ ] Add payback period calculation

### Week 3: Growth Metrics
- [ ] Add funnel tracking (frontend analytics)
- [ ] Add UTM parameter tracking
- [ ] Add referral code tracking
- [ ] Add engagement metrics aggregation

---

*This document should be updated as metrics are implemented and real data becomes available.*

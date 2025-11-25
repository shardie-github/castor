# YC Metrics Dashboard Sketch

**For:** YC Application & Interview Prep  
**Last Updated:** 2024

---

## Overview

This document describes what a basic metrics dashboard should show for YC prep. Founders should have these numbers handy during the interview and be able to pull them up quickly.

---

## Dashboard Layout

### Section 1: Top-Level KPIs (Always Visible)

**Display:** Large numbers, easy to read

**Metrics:**
1. **MRR (Monthly Recurring Revenue)**
   - Current MRR: $X,XXX
   - Growth: +X% MoM
   - Trend: Up/Down arrow

2. **Active Users**
   - MAU: X,XXX
   - WAU: X,XXX
   - DAU: X,XXX
   - Growth: +X% MoM

3. **Activation Rate**
   - 7-Day Activation: XX%
   - Trend: Up/Down arrow

4. **Retention**
   - Day 7 Retention: XX%
   - Day 30 Retention: XX%
   - Trend: Up/Down arrow

**Where to Get:**
- `GET /api/v1/metrics/dashboard` (needs to be created)
- Or query database directly (see `YC_METRICS_CHECKLIST.md`)

---

### Section 2: Growth Funnel

**Display:** Funnel chart (bar chart showing conversion at each stage)

**Stages:**
1. **Visitors** → X,XXX
2. **Signups** → X,XXX (X% conversion)
3. **Activated** → X,XXX (X% conversion)
4. **Retained (Day 7)** → X,XXX (X% conversion)
5. **Paying** → X,XXX (X% conversion)

**Time Period:** Last 30 days

**Where to Get:**
- `GET /api/v1/metrics/funnel` (needs to be created)

---

### Section 3: Revenue Metrics

**Display:** Cards with key revenue metrics

**Metrics:**
1. **ARPU (Average Revenue Per User)**
   - Current: $XX/month
   - Trend: Up/Down

2. **ACV (Annual Contract Value)**
   - Current: $X,XXX
   - Trend: Up/Down

3. **LTV (Lifetime Value)**
   - Current: $X,XXX
   - Trend: Up/Down

4. **CAC (Customer Acquisition Cost)**
   - Current: $XXX
   - By Channel: [Breakdown]
   - Trend: Up/Down

5. **LTV:CAC Ratio**
   - Current: X:1
   - Target: >3:1

6. **Payback Period**
   - Current: X months
   - Target: <12 months

**Where to Get:**
- `GET /api/v1/metrics/revenue` (needs to be created)
- `GET /api/v1/metrics/cac` (needs to be created)

---

### Section 4: User Engagement

**Display:** Charts showing engagement trends

**Metrics:**
1. **Dashboard Views**
   - Average per active user per week: X.X
   - Trend: Line chart (last 12 weeks)

2. **Reports Generated**
   - Total: X,XXX (last 30 days)
   - Average per active user: X.X
   - Trend: Line chart (last 12 weeks)

3. **Campaigns Created**
   - Total: X,XXX (last 30 days)
   - Average per active user: X.X
   - Trend: Line chart (last 12 weeks)

4. **Attribution Events Tracked**
   - Total: X,XXX (last 30 days)
   - Average per campaign: X.X
   - Trend: Line chart (last 12 weeks)

**Where to Get:**
- `GET /api/v1/metrics/engagement` (needs to be created)

---

### Section 5: Retention Cohorts

**Display:** Cohort retention table

**Format:**
```
Cohort    | Week 0 | Week 1 | Week 2 | Week 3 | Week 4 | Week 8 | Week 12
Jan 2024  | 100%   | 45%   | 38%   | 32%   | 28%   | 22%   | 18%
Feb 2024  | 100%   | 48%   | 40%   | 35%   | 30%   | -     | -
Mar 2024  | 100%   | 50%   | 42%   | -     | -     | -     | -
```

**Where to Get:**
- `GET /api/v1/metrics/retention/cohorts` (needs to be created)

---

### Section 6: Conversion Funnel (Free → Paid)

**Display:** Conversion funnel + timeline

**Metrics:**
1. **Free Users** → X,XXX
2. **Conversion Triggers** → X,XXX (X% of free users)
   - Reports generated: X,XXX
   - Campaigns created: X,XXX
   - Dashboard views: X,XXX
3. **Upsell Notifications Sent** → X,XXX
4. **Paid Conversions** → X,XXX (X% conversion rate)
5. **Average Time to Convert** → X days

**Where to Get:**
- `GET /api/v1/metrics/conversion` (needs to be created)
- `src/monetization/pricing.py` - Conversion logic

---

### Section 7: Churn Analysis

**Display:** Churn metrics + reasons

**Metrics:**
1. **Monthly Churn Rate**
   - Current: X.X%
   - Trend: Line chart (last 12 months)
   - Target: <5% monthly

2. **Churn by Tier**
   - Free: X.X%
   - Starter: X.X%
   - Professional: X.X%
   - Enterprise: X.X%

3. **Churn Reasons** (if tracked)
   - Too expensive: X%
   - Missing features: X%
   - Found alternative: X%
   - Not using: X%

**Where to Get:**
- `GET /api/v1/metrics/churn` (needs to be created)
- `src/business/analytics.py` - Customer metrics

---

## Quick Reference Numbers (For Interview)

### One-Liner Metrics

**Growth:**
- "We have X,XXX MAU, growing X% MoM"
- "We're adding X new users per week"
- "Our activation rate is XX%"

**Revenue:**
- "We're at $X,XXX MRR, growing X% MoM"
- "ARPU is $XX/month"
- "LTV:CAC is X:1"

**Engagement:**
- "Active users check the dashboard X times per week"
- "Users generate X reports per month on average"
- "Day 7 retention is XX%"

**Conversion:**
- "X% of free users convert to paid"
- "Average time to convert is X days"
- "Our churn rate is X% monthly"

---

## Implementation Notes

### API Endpoints Needed

**Priority 1 (Must Have):**
- `GET /api/v1/metrics/dashboard` - Top-level KPIs
- `GET /api/v1/metrics/funnel` - Growth funnel
- `GET /api/v1/metrics/revenue` - Revenue metrics

**Priority 2 (Should Have):**
- `GET /api/v1/metrics/engagement` - Engagement metrics
- `GET /api/v1/metrics/retention/cohorts` - Retention cohorts
- `GET /api/v1/metrics/conversion` - Conversion funnel

**Priority 3 (Nice to Have):**
- `GET /api/v1/metrics/churn` - Churn analysis

### Frontend Dashboard

**Recommended Tools:**
- **Internal Dashboard:** Build custom dashboard in Next.js frontend
- **Analytics Platform:** PostHog, Mixpanel, or Amplitude (for real-time analytics)
- **BI Tool:** Metabase, Retool, or Looker (for SQL queries and charts)

**Quick Win:**
- Create simple dashboard page: `/dashboard/metrics`
- Query database directly (for now)
- Display key metrics in cards/charts
- Update daily (or real-time if possible)

---

## Sample Dashboard Queries

### Top-Level KPIs

```sql
-- MRR
SELECT SUM(monthly_price) as mrr
FROM subscriptions
WHERE status = 'active';

-- MAU
SELECT COUNT(DISTINCT user_id) as mau
FROM events
WHERE timestamp >= NOW() - INTERVAL '30 days';

-- Activation Rate (7-day)
WITH signups AS (
  SELECT user_id, MIN(timestamp) as signup_time
  FROM events
  WHERE event_type = 'onboarding_started'
  GROUP BY user_id
),
activations AS (
  SELECT DISTINCT user_id
  FROM events
  WHERE event_type IN ('report_generated', 'campaign_launched')
)
SELECT 
  COUNT(DISTINCT a.user_id) * 100.0 / COUNT(DISTINCT s.user_id) as activation_rate
FROM signups s
LEFT JOIN activations a ON s.user_id = a.user_id
WHERE s.signup_time >= NOW() - INTERVAL '30 days';
```

---

## What YC Partners Will Ask

**Common Questions:**
1. "What's your MRR?" → Show MRR card
2. "How many active users?" → Show MAU/WAU/DAU
3. "What's your activation rate?" → Show activation rate card
4. "What's your retention?" → Show retention cohorts
5. "What's your CAC?" → Show CAC card
6. "What's your LTV:CAC?" → Show ratio
7. "How fast are you growing?" → Show growth chart
8. "What's your churn?" → Show churn rate

**Be Ready To:**
- Pull up dashboard quickly (bookmark it)
- Explain trends (why up/down)
- Compare to targets (are you on track?)
- Show cohort data (retention over time)

---

## Dashboard Mockup (Text)

```
┌─────────────────────────────────────────────────────────────┐
│  PODCAST ANALYTICS PLATFORM - METRICS DASHBOARD             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   MRR    │  │   MAU     │  │Activation│  │Retention │  │
│  │ $12,450  │  │  1,234    │  │   72%    │  │  42%     │  │
│  │ +15% MoM │  │ +12% MoM  │  │  +5%     │  │  +3%     │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  GROWTH FUNNEL (Last 30 Days)                          │ │
│  │                                                          │ │
│  │  Visitors    →  5,000  (100%)                           │ │
│  │  Signups     →    250   (5%)                            │ │
│  │  Activated   →    180  (72%)                            │ │
│  │  Retained    →     76  (42%)                            │ │
│  │  Paying      →     27  (15%)                            │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   ARPU   │  │    LTV    │  │   CAC    │  │LTV:CAC   │  │
│  │  $46/mo  │  │  $1,380   │  │   $85    │  │  16:1    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  ENGAGEMENT TRENDS (Last 12 Weeks)                      │ │
│  │                                                          │ │
│  │  Dashboard Views: ████████████ 5.2/week                │ │
│  │  Reports Generated: ████████ 1.8/month                  │ │
│  │  Campaigns Created: ██████████ 2.3/month                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

*This dashboard should be built and accessible before YC interview. Founders should be able to pull it up instantly.*

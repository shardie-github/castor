# Metrics & Forecasting Framework

## Overview

This document defines the product analytics framework and revenue forecasting model for the Podcast Analytics & Sponsorship Platform. It establishes what we measure, how we measure it, and how we forecast growth and revenue.

---

## 1. Core Product Metrics

### North Star Metric

**Metric Name:** **Campaigns with ROI Reports Generated (Monthly)**

**Definition:** Number of unique campaigns per month where a sponsor report (with ROI data) was successfully generated and exported.

**Formula:** 
```
COUNT(DISTINCT campaign_id) 
WHERE report_generated = true 
  AND report_exported = true 
  AND includes_roi = true
  AND report_generated_at >= start_of_month
```

**Rationale:** 
- Directly measures value delivery to users (the core job-to-be-done)
- Correlates with user success and retention
- Predicts monetization (users who generate reports are more likely to convert to paid)
- Aligns with product mission: proving ROI to sponsors

**Target:** [PLACEHOLDER: e.g., 80% of active campaigns generate reports]

**Data Requirements:**
- `campaigns` table: `campaign_id`, `user_id`, `created_at`
- `reports` table: `report_id`, `campaign_id`, `generated_at`, `exported_at`, `includes_roi`
- Event: `REPORT_EXPORTED` with `campaign_id` and `includes_roi` properties

---

### Supporting Metrics

#### A. Acquisition Metrics

**A1. New User Signups (Weekly/Monthly)**
- **Definition:** Count of new user registrations
- **Formula:** `COUNT(DISTINCT user_id) WHERE created_at >= period_start`
- **Events:** `USER_SIGNED_UP`
- **Database:** `users.created_at`
- **Target:** [PLACEHOLDER: e.g., 100 new signups/week]

**A2. Signup Conversion Rate**
- **Definition:** % of visitors who sign up
- **Formula:** `signups / unique_visitors`
- **Events:** `PAGE_VIEWED` (landing page), `USER_SIGNED_UP`
- **Database:** Track via analytics platform (Segment/Mixpanel)
- **Target:** [PLACEHOLDER: e.g., 2-5%]

**A3. Traffic Source Distribution**
- **Definition:** % of signups by acquisition channel
- **Formula:** `COUNT(signups) GROUP BY source`
- **Events:** `USER_SIGNED_UP` with `source` property (organic, paid, referral, etc.)
- **Database:** `users.metadata['signup_source']`
- **Target:** [PLACEHOLDER: e.g., 40% organic, 30% paid, 20% referral, 10% other]

**A4. Cost Per Acquisition (CPA)**
- **Definition:** Marketing spend / new signups
- **Formula:** `total_marketing_spend / new_signups`
- **Events:** Track marketing spend separately, link via `source` attribution
- **Database:** External tracking (marketing spend) + `users` table
- **Target:** [PLACEHOLDER: e.g., $50-150 per signup depending on channel]

---

#### B. Activation Metrics

**B1. Time to First Value (TTFV)**
- **Definition:** Time from signup to first report generated (or first campaign launched)
- **Formula:** `MIN(report_generated_at - user.created_at) WHERE user_id = X`
- **Events:** `USER_SIGNED_UP`, `FIRST_VALUE_DELIVERED` (with `value_type` and `time_to_value`)
- **Database:** `users.created_at`, `reports.generated_at` (or `campaigns.launched_at`)
- **Target:** [PLACEHOLDER: e.g., <30 minutes for 80% of users]

**B2. Onboarding Completion Rate**
- **Definition:** % of users who complete onboarding (connect RSS feed + create first campaign)
- **Formula:** `users_completed_onboarding / users_signed_up`
- **Events:** `ONBOARDING_STARTED`, `PODCAST_CONNECTED`, `CAMPAIGN_CREATED`
- **Database:** `users.metadata['onboarding_completed']` or derive from `podcasts` and `campaigns` tables
- **Target:** [PLACEHOLDER: e.g., >70% completion rate]

**B3. First Campaign Created Rate**
- **Definition:** % of users who create at least one campaign within 7 days
- **Formula:** `COUNT(DISTINCT user_id) WHERE campaign_created_at <= signup_at + 7 days / COUNT(DISTINCT user_id)`
- **Events:** `CAMPAIGN_CREATED` with `is_first_campaign` flag
- **Database:** `campaigns.user_id`, `campaigns.created_at`, `users.created_at`
- **Target:** [PLACEHOLDER: e.g., >60% within 7 days]

**B4. First Report Generated Rate**
- **Definition:** % of users who generate at least one report within 14 days
- **Formula:** `COUNT(DISTINCT user_id) WHERE report_generated_at <= signup_at + 14 days / COUNT(DISTINCT user_id)`
- **Events:** `REPORT_GENERATED` with `is_first_report` flag
- **Database:** `reports.user_id`, `reports.generated_at`, `users.created_at`
- **Target:** [PLACEHOLDER: e.g., >50% within 14 days]

---

#### C. Engagement & Retention Metrics

**C1. Daily Active Users (DAU)**
- **Definition:** Unique users who perform any action in the app on a given day
- **Formula:** `COUNT(DISTINCT user_id) WHERE last_action_at >= start_of_day`
- **Events:** Any user action event (`PAGE_VIEWED`, `CAMPAIGN_CREATED`, `REPORT_GENERATED`, etc.)
- **Database:** `users.last_login` or event stream aggregation
- **Target:** [PLACEHOLDER: e.g., 30-40% of MAU]

**C2. Monthly Active Users (MAU)**
- **Definition:** Unique users active in the past 30 days
- **Formula:** `COUNT(DISTINCT user_id) WHERE last_action_at >= 30_days_ago`
- **Events:** Any user action event
- **Database:** Event stream aggregation or `users.last_login`
- **Target:** [PLACEHOLDER: e.g., 10,000 MAU by month 12]

**C3. Campaign Creation Rate (per Active User)**
- **Definition:** Average campaigns created per active user per month
- **Formula:** `COUNT(campaigns) WHERE created_at >= month_start / COUNT(DISTINCT user_id) WHERE active`
- **Events:** `CAMPAIGN_CREATED`
- **Database:** `campaigns.created_at`, `campaigns.user_id`
- **Target:** [PLACEHOLDER: e.g., 2 campaigns/user/month]

**C4. Report Generation Rate**
- **Definition:** Average reports generated per campaign
- **Formula:** `COUNT(reports) / COUNT(campaigns)`
- **Events:** `REPORT_GENERATED`
- **Database:** `reports.campaign_id`, `campaigns.campaign_id`
- **Target:** [PLACEHOLDER: e.g., 1.2 reports per campaign]

**C5. Monthly Churn Rate**
- **Definition:** % of paying users who cancel in a given month
- **Formula:** `cancelled_users_in_month / paying_users_at_start_of_month`
- **Events:** `SUBSCRIPTION_CANCELLED`
- **Database:** `subscriptions.status`, `subscriptions.cancelled_at`
- **Target:** [PLACEHOLDER: e.g., <5% monthly churn]

**C6. Retention Rate (D1, D7, D30)**
- **Definition:** % of users who return on day 1, 7, and 30 after signup
- **Formula:** `COUNT(DISTINCT user_id) WHERE active_on_day_X / COUNT(DISTINCT user_id) WHERE signed_up_on_day_0`
- **Events:** Any user action event with timestamp
- **Database:** Event stream aggregation
- **Target:** [PLACEHOLDER: e.g., D1: 40%, D7: 25%, D30: 15%]

---

#### D. Monetization Metrics

**D1. Free-to-Paid Conversion Rate**
- **Definition:** % of free users who convert to paid within 90 days
- **Formula:** `COUNT(DISTINCT user_id) WHERE converted_to_paid <= signup_at + 90 days / COUNT(DISTINCT free_users)`
- **Events:** `SUBSCRIPTION_UPGRADED` (from FREE to STARTER/PROFESSIONAL/ENTERPRISE)
- **Database:** `subscriptions.tier`, `subscriptions.created_at`, `users.created_at`
- **Target:** [PLACEHOLDER: e.g., 10-15% conversion rate]

**D2. Average Revenue Per User (ARPU)**
- **Definition:** Total MRR / Total paying users
- **Formula:** `SUM(monthly_revenue) / COUNT(DISTINCT paying_user_id)`
- **Events:** `SUBSCRIPTION_CREATED`, `SUBSCRIPTION_UPDATED`
- **Database:** `subscriptions.tier`, `subscriptions.price`, `subscriptions.status`
- **Target:** [PLACEHOLDER: e.g., $45-60 ARPU]

**D3. Monthly Recurring Revenue (MRR)**
- **Definition:** Sum of all active subscription revenue (normalized to monthly)
- **Formula:** `SUM(monthly_price) WHERE subscription_status = 'active'`
- **Events:** `SUBSCRIPTION_CREATED`, `SUBSCRIPTION_UPDATED`, `SUBSCRIPTION_CANCELLED`
- **Database:** `subscriptions.price`, `subscriptions.billing_period`, `subscriptions.status`
- **Target:** [PLACEHOLDER: e.g., $50K MRR by month 12]

**D4. Customer Lifetime Value (LTV)**
- **Definition:** Average revenue per customer over their lifetime
- **Formula:** `ARPU / monthly_churn_rate` OR `ARPU * average_months_active`
- **Events:** `SUBSCRIPTION_CREATED`, `SUBSCRIPTION_CANCELLED`
- **Database:** `subscriptions` table with lifetime calculation
- **Target:** [PLACEHOLDER: e.g., $500-800 LTV]

**D5. Upgrade Rate (Tier Progression)**
- **Definition:** % of users who upgrade to a higher tier
- **Formula:** `COUNT(upgrades) / COUNT(eligible_users)`
- **Events:** `SUBSCRIPTION_UPGRADED` with `from_tier` and `to_tier`
- **Database:** `subscriptions` history or event log
- **Target:** [PLACEHOLDER: e.g., 25% upgrade from Starter to Professional]

**D6. Revenue Churn Rate**
- **Definition:** % of MRR lost from cancellations and downgrades
- **Formula:** `(MRR_lost_from_cancellations + MRR_lost_from_downgrades) / MRR_at_start_of_month`
- **Events:** `SUBSCRIPTION_CANCELLED`, `SUBSCRIPTION_DOWNGRADED`
- **Database:** `subscriptions` table with price changes
- **Target:** [PLACEHOLDER: e.g., <3% revenue churn]

---

## 2. Event & Data Model

### Event Schema

All events follow this base structure:

```json
{
  "event_id": "uuid",
  "event_type": "EVENT_NAME",
  "user_id": "uuid",
  "session_id": "uuid",
  "timestamp": "ISO8601",
  "properties": {
    // Event-specific properties
  },
  "context": {
    "ip_address": "string",
    "user_agent": "string",
    "page": "string",
    "referrer": "string"
  }
}
```

### Core Events

#### User Lifecycle Events

**EVENT: `USER_SIGNED_UP`**
- **Trigger:** User completes registration
- **Location:** `src/api/auth.py` → `register()` endpoint
- **Required Properties:**
  - `email` (hashed/anonymized)
  - `source` (organic, paid, referral, etc.)
  - `persona_segment` (solo_podcaster, producer, agency, etc.)
  - `signup_method` (email, oauth_google, oauth_github, etc.)
- **Optional Properties:**
  - `utm_source`, `utm_medium`, `utm_campaign`
  - `referral_code`

**EVENT: `ONBOARDING_STARTED`**
- **Trigger:** User begins onboarding flow
- **Location:** `src/automation/onboarding.py` → `start_onboarding()`
- **Required Properties:**
  - `user_id`
  - `onboarding_version` (if A/B testing)

**EVENT: `PODCAST_CONNECTED`**
- **Trigger:** User successfully connects RSS feed
- **Location:** `src/ingestion/rss_ingest.py` → after successful feed validation
- **Required Properties:**
  - `user_id`
  - `podcast_id`
  - `connection_method` (rss_feed, api, etc.)
  - `time_to_connect` (seconds from onboarding start)

**EVENT: `ONBOARDING_COMPLETED`**
- **Trigger:** User completes onboarding (podcast connected + first campaign created)
- **Location:** `src/automation/onboarding.py` → when all steps complete
- **Required Properties:**
  - `user_id`
  - `time_to_complete` (seconds)
  - `steps_completed` (array)

---

#### Campaign Events

**EVENT: `CAMPAIGN_CREATED`**
- **Trigger:** User creates a new campaign
- **Location:** `src/api/campaigns.py` → `create_campaign()` endpoint
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `is_first_campaign` (boolean)
  - `campaign_type` (single_episode, multi_episode, ongoing)
  - `time_to_create` (seconds)

**EVENT: `CAMPAIGN_LAUNCHED`**
- **Trigger:** User marks campaign as live or launches first ad
- **Location:** `src/campaigns/campaign_manager.py` → `launch_campaign()`
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `time_to_launch` (seconds from creation)

**EVENT: `ATTRIBUTION_SETUP_COMPLETED`**
- **Trigger:** User completes attribution setup (promo code, pixel, etc.)
- **Location:** `src/attribution/` → after setup validation
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `attribution_method` (promo_code, pixel, utm, etc.)
  - `time_to_setup` (seconds)

---

#### Report Events

**EVENT: `REPORT_GENERATION_STARTED`**
- **Trigger:** User clicks "Generate Report"
- **Location:** `src/api/reports.py` → `generate_report()` endpoint
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `report_type` (sponsor_report, performance_summary, roi_report)

**EVENT: `REPORT_GENERATED`**
- **Trigger:** Report successfully generated
- **Location:** `src/reporting/report_generator.py` → after PDF generation
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `report_id`
  - `is_first_report` (boolean)
  - `time_to_generate` (seconds)
  - `includes_roi` (boolean)
  - `report_size_bytes` (integer)

**EVENT: `REPORT_EXPORTED`**
- **Trigger:** User downloads/exports report
- **Location:** `src/api/reports.py` → `download_report()` endpoint
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `report_id`
  - `export_format` (pdf, csv, excel)

**EVENT: `REPORT_SHARED`**
- **Trigger:** User shares report (email, link)
- **Location:** `src/api/reports.py` → share functionality
- **Required Properties:**
  - `user_id`
  - `campaign_id`
  - `report_id`
  - `share_method` (email, link)
  - `recipient_type` (sponsor, team_member)

---

#### Monetization Events

**EVENT: `SUBSCRIPTION_CREATED`**
- **Trigger:** User subscribes to a paid tier
- **Location:** `src/automation/billing.py` → `create_subscription()`
- **Required Properties:**
  - `user_id`
  - `subscription_id`
  - `tier` (starter, professional, enterprise)
  - `price` (monthly price)
  - `billing_period` (monthly, annual)
  - `from_tier` (free, starter, professional)

**EVENT: `SUBSCRIPTION_UPGRADED`**
- **Trigger:** User upgrades to higher tier
- **Location:** `src/automation/billing.py` → `upgrade_subscription()`
- **Required Properties:**
  - `user_id`
  - `subscription_id`
  - `from_tier`
  - `to_tier`
  - `price_change` (delta)

**EVENT: `SUBSCRIPTION_DOWNGRADED`**
- **Trigger:** User downgrades to lower tier
- **Location:** `src/automation/billing.py` → `downgrade_subscription()`
- **Required Properties:**
  - `user_id`
  - `subscription_id`
  - `from_tier`
  - `to_tier`
  - `price_change` (delta)

**EVENT: `SUBSCRIPTION_CANCELLED`**
- **Trigger:** User cancels subscription
- **Location:** `src/automation/billing.py` → `cancel_subscription()`
- **Required Properties:**
  - `user_id`
  - `subscription_id`
  - `tier`
  - `cancellation_reason` (if provided)
  - `days_active` (lifetime of subscription)

---

#### Engagement Events

**EVENT: `DASHBOARD_VIEWED`**
- **Trigger:** User views main dashboard
- **Location:** `src/api/analytics.py` → dashboard endpoint
- **Required Properties:**
  - `user_id`
  - `view_duration` (seconds)

**EVENT: `FIRST_VALUE_DELIVERED`**
- **Trigger:** User completes first key action (campaign created, report generated, etc.)
- **Location:** Multiple (triggered after first campaign/report)
- **Required Properties:**
  - `user_id`
  - `value_type` (campaign_created, report_generated, attribution_setup)
  - `time_to_value` (seconds from signup)

---

### Data Storage Plan

#### Event Storage

**Primary Storage: Event Stream**
- **Technology:** PostHog / Mixpanel / Amplitude / Segment
- **Purpose:** Real-time event analytics, user journeys, funnel analysis
- **Retention:** 2+ years
- **Schema:** Event-based (as defined above)

**Secondary Storage: Data Warehouse**
- **Technology:** PostgreSQL (TimescaleDB for time-series) or BigQuery / Snowflake
- **Purpose:** Aggregated metrics, historical analysis, forecasting
- **Tables:**
  - `events` (raw event log)
  - `daily_user_metrics` (aggregated daily metrics per user)
  - `daily_campaign_metrics` (aggregated daily metrics per campaign)
  - `monthly_aggregates` (monthly rollups for forecasting)

#### Database Schema for Metrics

```sql
-- Daily user metrics aggregation
CREATE TABLE daily_user_metrics (
    date DATE NOT NULL,
    user_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT false,
    campaigns_created INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    reports_exported INTEGER DEFAULT 0,
    dashboard_views INTEGER DEFAULT 0,
    subscription_tier VARCHAR(50),
    PRIMARY KEY (date, user_id)
);

-- Daily campaign metrics
CREATE TABLE daily_campaign_metrics (
    date DATE NOT NULL,
    campaign_id UUID NOT NULL,
    user_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT false,
    reports_generated INTEGER DEFAULT 0,
    reports_exported INTEGER DEFAULT 0,
    attribution_events INTEGER DEFAULT 0,
    PRIMARY KEY (date, campaign_id)
);

-- Monthly aggregates for forecasting
CREATE TABLE monthly_aggregates (
    month DATE NOT NULL PRIMARY KEY,
    total_users INTEGER DEFAULT 0,
    new_signups INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    paying_users INTEGER DEFAULT 0,
    mrr DECIMAL(10, 2) DEFAULT 0,
    churned_users INTEGER DEFAULT 0,
    campaigns_created INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    reports_with_roi INTEGER DEFAULT 0
);

-- Subscription events log
CREATE TABLE subscription_events (
    event_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- created, upgraded, downgraded, cancelled
    tier VARCHAR(50),
    price DECIMAL(10, 2),
    occurred_at TIMESTAMP NOT NULL,
    properties JSONB
);
```

#### Metrics Calculation

**Real-time Metrics:**
- Calculated from event stream (PostHog/Mixpanel dashboards)
- Updated every 5-15 minutes via aggregation jobs

**Historical Metrics:**
- Calculated via daily ETL jobs from event stream → data warehouse
- Stored in `daily_user_metrics` and `monthly_aggregates` tables
- Used for forecasting and trend analysis

---

## 3. Forecasting Framework

### Core Assumptions

**User Growth Assumptions:**
- **Month 1 Signups:** [PLACEHOLDER: 100]
- **Monthly Growth Rate:** [PLACEHOLDER: 15%] (compounding)
- **Activation Rate:** [PLACEHOLDER: 60%] (users who create first campaign)
- **Active User Rate:** [PLACEHOLDER: 40%] (of signups, become monthly active)

**Conversion Assumptions:**
- **Free-to-Paid Conversion:** [PLACEHOLDER: 12%] (within 90 days)
- **Time to Convert:** [PLACEHOLDER: 30 days] (average days to convert)
- **Tier Distribution (of paying users):**
  - Starter: [PLACEHOLDER: 60%]
  - Professional: [PLACEHOLDER: 30%]
  - Enterprise: [PLACEHOLDER: 10%]

**Retention Assumptions:**
- **Monthly Churn Rate:** [PLACEHOLDER: 4%] (of paying users)
- **Free User Churn:** [PLACEHOLDER: 15%] (monthly inactive)
- **D30 Retention:** [PLACEHOLDER: 15%] (of signups)

**Revenue Assumptions:**
- **Starter Price:** $29/month
- **Professional Price:** $99/month
- **Enterprise Price:** [PLACEHOLDER: $499/month] (average)
- **Annual Discount:** [PLACEHOLDER: 17%] (applied to annual plans)
- **Annual Plan Mix:** [PLACEHOLDER: 20%] (of paying users)

**Usage Assumptions:**
- **Campaigns per Active User:** [PLACEHOLDER: 2/month]
- **Reports per Campaign:** [PLACEHOLDER: 1.2]
- **Reports with ROI:** [PLACEHOLDER: 80%] (of reports generated)

---

### Forecasting Model Structure

**Model Flow:**
```
New Signups → Active Users → Paying Users → MRR
     ↓            ↓              ↓           ↓
  Growth      Activation    Conversion   Revenue
```

**Monthly Calculation Steps:**

1. **Calculate New Signups:**
   ```
   Month N Signups = Month (N-1) Signups × (1 + Growth Rate)
   ```

2. **Calculate Total Users:**
   ```
   Total Users = Previous Month Total + New Signups - Churned Users
   ```

3. **Calculate Active Users:**
   ```
   Active Users = Total Users × Active User Rate
   ```

4. **Calculate New Paying Users:**
   ```
   New Paying Users = (New Signups × Activation Rate × Conversion Rate) + Upgrades
   ```

5. **Calculate Total Paying Users:**
   ```
   Paying Users = Previous Month Paying Users × (1 - Churn Rate) + New Paying Users
   ```

6. **Calculate MRR:**
   ```
   MRR = Σ(Paying Users by Tier × Tier Price)
   ```

7. **Calculate North Star Metric:**
   ```
   Campaigns with ROI Reports = Active Users × Campaigns per User × Reports per Campaign × ROI Report Rate
   ```

---

### Scenario 1: Conservative Growth

**Assumptions:**
- Month 1 Signups: 100
- Monthly Growth Rate: 10%
- Activation Rate: 50%
- Free-to-Paid Conversion: 10%
- Monthly Churn: 5%
- Tier Mix: Starter 70%, Professional 25%, Enterprise 5%

**12-Month Forecast:**

| Month | New Signups | Total Users | Active Users | Paying Users | MRR | North Star (Reports w/ ROI) |
|-------|-------------|-------------|--------------|--------------|-----|------------------------------|
| 1     | 100         | 100         | 40           | 5            | $145| 38                            |
| 2     | 110         | 205         | 82           | 10           | $290| 79                            |
| 3     | 121         | 316         | 126          | 16           | $464| 121                           |
| 4     | 133         | 434         | 174          | 22           | $638| 167                           |
| 5     | 146         | 560         | 224          | 29           | $841| 215                           |
| 6     | 161         | 694         | 278          | 37           | $1,073| 267                        |
| 7     | 177         | 836         | 334          | 45           | $1,305| 321                        |
| 8     | 195         | 987         | 395          | 54           | $1,566| 379                        |
| 9     | 214         | 1,147       | 459          | 64           | $1,856| 441                        |
| 10    | 236         | 1,317       | 527          | 75           | $2,175| 506                        |
| 11    | 259         | 1,497       | 599          | 87           | $2,523| 575                        |
| 12    | 285         | 1,688       | 675          | 100          | $2,900| 648                        |

**Year-End Totals:**
- Total Users: 1,688
- Active Users: 675
- Paying Users: 100
- MRR: $2,900
- Annual Revenue Run Rate: $34,800

---

### Scenario 2: Aggressive Growth

**Assumptions:**
- Month 1 Signups: 200
- Monthly Growth Rate: 20%
- Activation Rate: 65%
- Free-to-Paid Conversion: 15%
- Monthly Churn: 3%
- Tier Mix: Starter 60%, Professional 30%, Enterprise 10%

**12-Month Forecast:**

| Month | New Signups | Total Users | Active Users | Paying Users | MRR | North Star (Reports w/ ROI) |
|-------|-------------|-------------|--------------|--------------|-----|------------------------------|
| 1     | 200         | 200         | 130          | 20           | $580| 125                           |
| 2     | 240         | 434         | 282          | 43           | $1,247| 271                        |
| 3     | 288         | 699         | 454          | 70           | $2,030| 437                        |
| 4     | 346         | 1,005       | 653          | 101          | $2,929| 627                        |
| 5     | 415         | 1,356       | 881          | 136          | $3,944| 846                        |
| 6     | 498         | 1,757       | 1,142        | 176          | $5,104| 1,097                       |
| 7     | 598         | 2,214       | 1,439        | 222          | $6,438| 1,382                       |
| 8     | 717         | 2,733       | 1,776        | 274          | $7,946| 1,705                       |
| 9     | 861         | 3,320       | 2,158        | 333          | $9,657| 2,072                       |
| 10    | 1,033       | 3,983       | 2,589        | 399          | $11,571| 2,485                      |
| 11    | 1,240       | 4,730       | 3,075        | 474          | $13,746| 2,952                      |
| 12    | 1,488       | 5,568       | 3,619        | 558          | $16,182| 3,474                      |

**Year-End Totals:**
- Total Users: 5,568
- Active Users: 3,619
- Paying Users: 558
- MRR: $16,182
- Annual Revenue Run Rate: $194,184

---

### Key Forecasting Variables

**Variables to Monitor & Adjust:**

1. **Growth Rate:** Track actual vs. forecasted signups monthly
2. **Activation Rate:** Monitor onboarding completion and first campaign creation
3. **Conversion Rate:** Track free-to-paid conversion funnel
4. **Churn Rate:** Monitor subscription cancellations and downgrades
5. **Tier Mix:** Track tier distribution and upgrade/downgrade patterns
6. **Usage Patterns:** Monitor campaigns per user and reports per campaign

**Forecast Updates:**
- Review monthly and adjust assumptions based on actual performance
- Re-run forecast with updated assumptions
- Compare scenarios to identify growth opportunities or risks

---

## 4. Implementation Checklist

### Phase 1: Event Instrumentation (Weeks 1-2)
- [ ] Implement event tracking in authentication endpoints
- [ ] Add event tracking to campaign creation/management
- [ ] Add event tracking to report generation/export
- [ ] Add event tracking to subscription/billing flows
- [ ] Set up event storage (PostHog/Mixpanel/Segment)
- [ ] Create event validation tests

### Phase 2: Metrics Infrastructure (Weeks 3-4)
- [ ] Set up data warehouse (PostgreSQL/TimescaleDB or cloud)
- [ ] Create daily aggregation jobs
- [ ] Build `daily_user_metrics` table and ETL
- [ ] Build `daily_campaign_metrics` table and ETL
- [ ] Build `monthly_aggregates` table and ETL
- [ ] Create metrics calculation queries

### Phase 3: Dashboards & Reporting (Weeks 5-6)
- [ ] Build North Star metric dashboard
- [ ] Build acquisition funnel dashboard
- [ ] Build activation metrics dashboard
- [ ] Build engagement/retention dashboard
- [ ] Build monetization dashboard
- [ ] Build forecasting dashboard

### Phase 4: Forecasting Model (Weeks 7-8)
- [ ] Build forecasting calculation script
- [ ] Create scenario comparison tool
- [ ] Set up monthly forecast review process
- [ ] Document assumption adjustment process

---

## 5. Success Criteria

**Metrics Framework Success:**
- All core events instrumented and firing correctly
- Metrics calculated accurately and updated daily
- Dashboards accessible to product/executive team
- <24 hour lag on metric updates

**Forecasting Success:**
- Forecast accuracy within 20% of actuals after 3 months
- Monthly forecast reviews conducted
- Assumptions updated based on actual performance
- Scenarios used for planning and goal-setting

---

## Appendix: Placeholder Values Reference

All placeholder values in this document should be replaced with:
1. **Industry benchmarks** (where available)
2. **Historical data** (once available)
3. **Target goals** (based on business objectives)
4. **Conservative estimates** (for conservative scenario)
5. **Aggressive estimates** (for aggressive scenario)

**Key Placeholders to Replace:**
- Signup conversion rates
- Activation rates
- Conversion rates
- Churn rates
- Tier distribution
- Pricing (if different from current plan)
- Growth rates
- Usage patterns

---

*Last Updated: [Current Date]*
*Next Review: Monthly*
*Owner: Product Analytics Team*

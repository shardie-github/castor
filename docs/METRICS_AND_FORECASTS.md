# Metrics & Forecasts

## Overview

This document defines the key metrics to track, forecasting models, and success criteria for the Podcast Analytics & Sponsorship Platform. Metrics are organized by category (user, product, business, operational) and include targets and forecasting methodologies.

---

## 1. User Metrics

### 1.1 Acquisition Metrics

**Signups**
- **Definition:** Number of new user registrations
- **Target:** 100+ signups/month (Month 1-3), 500+ signups/month (Month 4-6)
- **Forecast:** Linear growth initially, then exponential as word-of-mouth kicks in
- **Tracking:** Event: `user.signup` (Mixpanel/Amplitude)

**Signup Sources**
- **Organic:** Target 40%+ (SEO, content marketing)
- **Paid:** Target 30%+ (Google Ads, Facebook Ads)
- **Referral:** Target 20%+ (user referrals, partnerships)
- **Direct:** Target 10%+ (brand awareness)

**Cost Per Acquisition (CAC)**
- **Target:** <$50 (Month 1-3), <$30 (Month 4-6)
- **Calculation:** Total marketing spend / New signups
- **Forecast:** Decreases over time as organic channels grow

### 1.2 Activation Metrics

**Activation Rate**
- **Definition:** % of signups who complete core loop (connect podcast + create campaign + generate report)
- **Target:** 70%+ (MVP), 80%+ (Post-MVP)
- **Tracking:** Funnel: Signup → Email Verified → Podcast Connected → Campaign Created → Report Generated

**Time to First Value (TTFV)**
- **Definition:** Time from signup to first report generated
- **Target:** <10 minutes (MVP), <5 minutes (Post-MVP)
- **Tracking:** Timestamp difference between signup and first report generation

**Onboarding Completion Rate**
- **Definition:** % of users who complete onboarding wizard
- **Target:** 70%+ (MVP), 85%+ (Post-MVP)
- **Tracking:** Event: `onboarding.completed`

### 1.3 Engagement Metrics

**Daily Active Users (DAU)**
- **Target:** 30%+ of monthly users (MVP), 40%+ (Post-MVP)
- **Forecast:** Grows with user base, plateaus at 30-40% engagement rate

**Weekly Active Users (WAU)**
- **Target:** 60%+ of monthly users (MVP), 70%+ (Post-MVP)
- **Forecast:** Higher than DAU, indicates regular usage

**Monthly Active Users (MAU)**
- **Target:** 1,000+ (Month 3), 5,000+ (Month 6), 20,000+ (Month 12)
- **Forecast:** Exponential growth after Month 3 (viral coefficient >1)

**Feature Adoption Rate**
- **Campaign Creation:** 80%+ of active users create campaigns
- **Report Generation:** 70%+ of campaigns generate reports
- **Attribution Setup:** 90%+ of campaigns have attribution configured
- **Dashboard Usage:** 90%+ of users view dashboard weekly

### 1.4 Retention Metrics

**Day 1 Retention**
- **Target:** 60%+ (MVP), 70%+ (Post-MVP)
- **Tracking:** % of signups who return on Day 1

**Day 7 Retention**
- **Target:** 40%+ (MVP), 50%+ (Post-MVP)
- **Tracking:** % of signups who return within 7 days

**Day 30 Retention**
- **Target:** 25%+ (MVP), 35%+ (Post-MVP)
- **Tracking:** % of signups who return within 30 days

**Churn Rate (Monthly)**
- **Target:** <10% (Month 1-3), <5% (Month 4-6), <3% (Month 7+)
- **Calculation:** (Users lost in month / Users at start of month) × 100
- **Forecast:** Decreases over time as product improves and users see value

**Net Promoter Score (NPS)**
- **Target:** 40+ (MVP), 50+ (Month 3), 70+ (Month 12)
- **Tracking:** Survey: "How likely are you to recommend us?" (0-10 scale)
- **Calculation:** % Promoters (9-10) - % Detractors (0-6)

---

## 2. Product Metrics

### 2.1 Core Feature Usage

**Campaign Creation Rate**
- **Target:** 80%+ of active users create at least one campaign
- **Tracking:** Event: `campaign.created`
- **Forecast:** Increases as users see value

**Report Generation Rate**
- **Target:** 70%+ of campaigns generate at least one report
- **Tracking:** Event: `report.generated`
- **Forecast:** Core value prop, should be high

**Attribution Setup Rate**
- **Target:** 90%+ of campaigns have attribution configured
- **Tracking:** Event: `attribution.configured`
- **Forecast:** Critical for value, should be very high

**Dashboard Views**
- **Target:** 90%+ of users view dashboard weekly
- **Tracking:** Event: `dashboard.viewed`
- **Forecast:** Indicates engagement and value

### 2.2 Feature Performance

**Report Generation Time**
- **Target:** <30 seconds (p95)
- **Tracking:** Time from request to completion
- **Forecast:** Should decrease as we optimize

**Attribution Accuracy**
- **Target:** >95% accuracy (validated vs. ground truth)
- **Tracking:** Comparison with test campaigns
- **Forecast:** Critical metric, must maintain high accuracy

**API Response Time**
- **Target:** <500ms (p95)
- **Tracking:** APM tool (Datadog/New Relic)
- **Forecast:** Should remain stable as we scale

**Error Rate**
- **Target:** <1% of requests result in errors
- **Tracking:** Error tracking (Sentry)
- **Forecast:** Should decrease as we fix bugs

### 2.3 User Satisfaction

**Feature Satisfaction Score**
- **Target:** 8+/10 average rating
- **Tracking:** In-app surveys after feature use
- **Forecast:** Should increase as we improve features

**Support Ticket Volume**
- **Target:** <5% of users submit tickets monthly
- **Tracking:** Support system (Intercom/Zendesk)
- **Forecast:** Should decrease as product improves and docs expand

**Time to Resolution**
- **Target:** <24 hours for 80%+ of tickets
- **Tracking:** Support system
- **Forecast:** Should decrease as we build self-service resources

---

## 3. Business Metrics

### 3.1 Revenue Metrics

**Monthly Recurring Revenue (MRR)**
- **Target:** $1,000 (Month 1), $5,000 (Month 3), $25,000 (Month 6), $100,000 (Month 12)
- **Calculation:** Sum of all monthly subscription revenue
- **Forecast:** Exponential growth after Month 3 (viral coefficient >1)

**Annual Recurring Revenue (ARR)**
- **Target:** $12,000 (Month 1), $60,000 (Month 3), $300,000 (Month 6), $1.2M (Month 12)
- **Calculation:** MRR × 12
- **Forecast:** Follows MRR growth

**Average Revenue Per User (ARPU)**
- **Target:** $15 (Month 1-3), $25 (Month 4-6), $35 (Month 7+)
- **Calculation:** MRR / Paying users
- **Forecast:** Increases as users upgrade tiers

**Revenue by Tier**
- **Free:** $0 (but drives conversions)
- **Starter ($29/mo):** Target 60%+ of revenue (Month 1-6)
- **Professional ($99/mo):** Target 30%+ of revenue (Month 4+)
- **Enterprise ($499+/mo):** Target 10%+ of revenue (Month 6+)

### 3.2 Conversion Metrics

**Free-to-Paid Conversion Rate**
- **Target:** 5%+ (Month 1-3), 10%+ (Month 4-6), 15%+ (Month 7+)
- **Calculation:** (Paying users / Free users) × 100
- **Forecast:** Increases as product improves and value becomes clear

**Upgrade Rate (Starter → Professional)**
- **Target:** 20%+ (Month 4+)
- **Calculation:** (Upgrades / Starter users) × 100
- **Forecast:** Increases as users hit limits and see value

**Upgrade Rate (Professional → Enterprise)**
- **Target:** 10%+ (Month 6+)
- **Calculation:** (Upgrades / Professional users) × 100
- **Forecast:** Lower but higher ARPU

**Time to Conversion**
- **Target:** <14 days average (Free → Paid)
- **Tracking:** Time from signup to first payment
- **Forecast:** Should decrease as onboarding improves

### 3.3 Unit Economics

**Customer Acquisition Cost (CAC)**
- **Target:** <$50 (Month 1-3), <$30 (Month 4-6)
- **Calculation:** Total marketing spend / New paying customers
- **Forecast:** Decreases as organic channels grow

**Lifetime Value (LTV)**
- **Target:** $500+ (Month 1-3), $1,000+ (Month 4-6), $2,000+ (Month 7+)
- **Calculation:** ARPU × Average customer lifetime (months)
- **Forecast:** Increases as retention improves

**LTV:CAC Ratio**
- **Target:** 3:1+ (Month 1-3), 5:1+ (Month 4-6), 10:1+ (Month 7+)
- **Forecast:** Improves as CAC decreases and LTV increases

**Payback Period**
- **Target:** <6 months (Month 1-3), <3 months (Month 4+)
- **Calculation:** CAC / (ARPU × Gross margin)
- **Forecast:** Decreases as efficiency improves

### 3.4 Growth Metrics

**Month-over-Month (MoM) Growth**
- **Target:** 20%+ (Month 1-6), 15%+ (Month 7-12)
- **Calculation:** ((Current month MRR - Previous month MRR) / Previous month MRR) × 100
- **Forecast:** High initially, then stabilizes

**Viral Coefficient**
- **Target:** >1.0 (Month 4+)
- **Calculation:** Average number of new users each user brings in
- **Forecast:** Should exceed 1.0 for sustainable growth

**Referral Rate**
- **Target:** 20%+ of new signups from referrals (Month 4+)
- **Tracking:** Referral tracking system
- **Forecast:** Increases as product improves and referral program launches

---

## 4. Operational Metrics

### 4.1 Infrastructure Metrics

**Uptime**
- **Target:** 99%+ (MVP), 99.9%+ (Post-MVP)
- **Tracking:** Monitoring tool (Datadog/New Relic)
- **Forecast:** Should remain high with proper infrastructure

**API Latency (p95)**
- **Target:** <500ms
- **Tracking:** APM tool
- **Forecast:** Should remain stable with caching and optimization

**Error Rate**
- **Target:** <1% of requests
- **Tracking:** Error tracking (Sentry)
- **Forecast:** Should decrease as we fix bugs

**Database Performance**
- **Target:** Query time <100ms (p95)
- **Tracking:** Database monitoring
- **Forecast:** Should remain stable with proper indexing

### 4.2 Cost Metrics

**Infrastructure Cost per User**
- **Target:** <$1/user/month (Month 1-6), <$0.50/user/month (Month 7+)
- **Calculation:** Total infrastructure cost / Total users
- **Forecast:** Decreases as we scale and optimize

**Cost of Goods Sold (COGS)**
- **Target:** <30% of revenue (Month 1-6), <20% of revenue (Month 7+)
- **Calculation:** (Infrastructure + Payment processing + Support) / Revenue
- **Forecast:** Decreases as revenue grows

**Gross Margin**
- **Target:** 70%+ (Month 1-6), 80%+ (Month 7+)
- **Calculation:** (Revenue - COGS) / Revenue × 100
- **Forecast:** Improves as we scale

---

## 5. Forecasting Models

### 5.1 User Growth Forecast

**Model:** Exponential growth with S-curve
- **Month 1-3:** Linear growth (100 → 300 → 500 users)
- **Month 4-6:** Exponential growth (1,000 → 2,500 → 5,000 users)
- **Month 7-12:** Continued growth with plateau (10,000 → 20,000 users)

**Assumptions:**
- Viral coefficient >1.0 after Month 3
- Organic growth increases with word-of-mouth
- Paid acquisition scales with revenue

### 5.2 Revenue Forecast

**Model:** MRR growth based on user growth and conversion rates
- **Month 1:** $1,000 MRR (50 paying users × $20 ARPU)
- **Month 3:** $5,000 MRR (200 paying users × $25 ARPU)
- **Month 6:** $25,000 MRR (1,000 paying users × $25 ARPU)
- **Month 12:** $100,000 MRR (3,000 paying users × $33 ARPU)

**Assumptions:**
- 10% free-to-paid conversion (Month 4+)
- 20% upgrade rate (Starter → Professional)
- 5% churn rate (Month 4+)
- ARPU increases as users upgrade

### 5.3 Churn Forecast

**Model:** Decreasing churn as product improves
- **Month 1-3:** 10% monthly churn (early adopters, product issues)
- **Month 4-6:** 5% monthly churn (product improves, value clear)
- **Month 7+:** 3% monthly churn (mature product, strong retention)

**Assumptions:**
- Churn decreases as product improves
- Customer success program reduces churn
- Higher-tier users have lower churn

---

## 6. Success Criteria

### MVP Success (Month 1-3)
- ✅ 500+ signups
- ✅ 70%+ activation rate
- ✅ 10%+ free-to-paid conversion
- ✅ $5,000+ MRR
- ✅ 40+ NPS
- ✅ 99%+ uptime

### Post-MVP Success (Month 4-6)
- ✅ 5,000+ signups
- ✅ 80%+ activation rate
- ✅ 15%+ free-to-paid conversion
- ✅ $25,000+ MRR
- ✅ 50+ NPS
- ✅ 99.9%+ uptime
- ✅ <5% monthly churn

### Scale Success (Month 7-12)
- ✅ 20,000+ signups
- ✅ 85%+ activation rate
- ✅ 20%+ free-to-paid conversion
- ✅ $100,000+ MRR
- ✅ 70+ NPS
- ✅ 99.9%+ uptime
- ✅ <3% monthly churn
- ✅ Product-market fit achieved

---

## 7. Dashboard & Reporting

### Internal Dashboards
- **Executive Dashboard:** MRR, ARR, growth, churn, NPS
- **Product Dashboard:** Activation, engagement, feature usage, satisfaction
- **Operations Dashboard:** Uptime, latency, errors, costs
- **Support Dashboard:** Ticket volume, resolution time, satisfaction

### Reporting Frequency
- **Daily:** Key metrics (signups, revenue, errors)
- **Weekly:** Detailed metrics (activation, engagement, churn)
- **Monthly:** Comprehensive review (all metrics, forecasts, trends)

---

*Last Updated: 2024*  
*Next Review: Weekly during active development*

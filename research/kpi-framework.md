# Cross-Functional KPI Framework: Podcast Sponsor Analytics SaaS

## Overview

This document establishes a comprehensive KPI framework including activation metrics, retention, ROI fidelity, churn, LTV, CAC, and operational health indicators. All metrics feed into a live dashboard for real-time monitoring and decision-making.

## KPI Categories

1. **Activation Metrics** - User onboarding and first value
2. **Retention Metrics** - User engagement and retention
3. **ROI Fidelity Metrics** - Accuracy and trust in ROI calculations
4. **Churn Metrics** - User loss and reasons
5. **LTV (Lifetime Value)** - Customer value over time
6. **CAC (Customer Acquisition Cost)** - Cost to acquire customers
7. **Operational Health** - System performance and reliability

## 1. Activation Metrics

### Primary Activation KPIs

**Time to First Value (TTFV)**
- **Definition:** Time from signup to first report generated or first campaign created
- **Target:** <30 minutes (90th percentile)
- **Current Baseline:** 2+ hours
- **Measurement:** Track timestamp of signup → first value event
- **Segmentation:** By persona, plan tier, acquisition channel
- **Dashboard:** Real-time, daily averages, weekly trends

**Activation Rate**
- **Definition:** % of signups who complete activation (generate first report or create first campaign) within 7 days
- **Target:** 70%+ (industry benchmark: 40-60%)
- **Current Baseline:** 45%
- **Measurement:** Signups with activation event / Total signups
- **Segmentation:** By persona, plan tier, acquisition channel
- **Dashboard:** Daily, weekly, monthly rates

**Onboarding Completion Rate**
- **Definition:** % of users who complete onboarding steps (connect podcast, set up first campaign)
- **Target:** 80%+ completion rate
- **Current Baseline:** 60%
- **Measurement:** Users completing all onboarding steps / Total signups
- **Segmentation:** By persona, step completion
- **Dashboard:** Funnel visualization, drop-off analysis

### Secondary Activation KPIs

**First Report Generation Time**
- **Definition:** Time from signup to first report generated
- **Target:** <15 minutes (median)
- **Measurement:** Timestamp analysis
- **Dashboard:** Distribution histogram, persona breakdown

**First Campaign Creation Time**
- **Definition:** Time from signup to first campaign created
- **Target:** <10 minutes (median)
- **Measurement:** Timestamp analysis
- **Dashboard:** Distribution histogram, persona breakdown

**Platform Connection Rate**
- **Definition:** % of users who connect at least one platform (Apple, Spotify, etc.)
- **Target:** 85%+ connection rate
- **Measurement:** Users with platform connections / Total signups
- **Dashboard:** Platform breakdown, connection success rate

**Attribution Setup Completion Rate**
- **Definition:** % of campaigns with attribution configured
- **Target:** 95%+ of campaigns
- **Measurement:** Campaigns with attribution / Total campaigns
- **Dashboard:** Campaign-level tracking, persona breakdown

## 2. Retention Metrics

### Primary Retention KPIs

**Monthly Active Users (MAU)**
- **Definition:** Unique users who logged in and performed an action in the past 30 days
- **Target:** 80%+ of total users (industry benchmark: 60-70%)
- **Measurement:** Count of unique users with activity in last 30 days
- **Segmentation:** By persona, plan tier, cohort
- **Dashboard:** Daily MAU, weekly trends, cohort analysis

**Weekly Active Users (WAU)**
- **Definition:** Unique users who logged in and performed an action in the past 7 days
- **Target:** 50%+ of MAU (industry benchmark: 30-40%)
- **Measurement:** Count of unique users with activity in last 7 days
- **Segmentation:** By persona, plan tier
- **Dashboard:** Daily WAU, weekly trends

**DAU/MAU Ratio (Stickiness)**
- **Definition:** Daily Active Users / Monthly Active Users
- **Target:** 40%+ (industry benchmark: 20-30%)
- **Measurement:** DAU / MAU
- **Segmentation:** By persona, plan tier
- **Dashboard:** Daily ratio, weekly trends

**Retention Rate (30-day)**
- **Definition:** % of users who are still active 30 days after signup
- **Target:** 70%+ (industry benchmark: 50-60%)
- **Current Baseline:** 55%
- **Measurement:** Users active at day 30 / Users who signed up 30 days ago
- **Segmentation:** By persona, plan tier, acquisition channel, cohort
- **Dashboard:** Cohort retention curves, persona breakdown

**Retention Rate (90-day)**
- **Definition:** % of users who are still active 90 days after signup
- **Target:** 60%+ (industry benchmark: 40-50%)
- **Current Baseline:** 45%
- **Measurement:** Users active at day 90 / Users who signed up 90 days ago
- **Segmentation:** By persona, plan tier, cohort
- **Dashboard:** Cohort retention curves

**Annual Retention Rate**
- **Definition:** % of users who are still active 365 days after signup
- **Target:** 50%+ (industry benchmark: 30-40%)
- **Measurement:** Users active at day 365 / Users who signed up 365 days ago
- **Segmentation:** By persona, plan tier
- **Dashboard:** Annual cohort analysis

### Secondary Retention KPIs

**Feature Adoption Rate**
- **Definition:** % of users who use each feature within 30 days of signup
- **Target:** 60%+ for core features
- **Measurement:** Users using feature / Total users
- **Dashboard:** Feature adoption matrix, persona breakdown

**Engagement Score**
- **Definition:** Composite score based on login frequency, feature usage, data volume
- **Target:** 70+ (out of 100)
- **Measurement:** Weighted formula (login frequency × 0.3 + feature usage × 0.4 + data volume × 0.3)
- **Dashboard:** Distribution histogram, persona breakdown

**Session Frequency**
- **Definition:** Average number of sessions per user per week
- **Target:** 3+ sessions per week
- **Measurement:** Total sessions / Active users / 7 days
- **Dashboard:** Weekly averages, persona breakdown

**Session Duration**
- **Definition:** Average session length in minutes
- **Target:** 8+ minutes per session
- **Measurement:** Total session time / Total sessions
- **Dashboard:** Distribution histogram, persona breakdown

## 3. ROI Fidelity Metrics

### Primary ROI Fidelity KPIs

**Attribution Accuracy**
- **Definition:** % of attribution events that are validated as accurate
- **Target:** 95%+ accuracy rate
- **Measurement:** Validated attribution events / Total attribution events
- **Validation Method:** Test campaigns, manual verification, cross-validation
- **Dashboard:** Accuracy rate, trend over time, by attribution method

**ROI Calculation Accuracy**
- **Definition:** % of ROI calculations that are validated as accurate
- **Target:** 98%+ accuracy rate
- **Measurement:** Validated ROI calculations / Total ROI calculations
- **Validation Method:** Manual verification, comparison to ground truth
- **Dashboard:** Accuracy rate, error analysis, by calculation type

**Data Completeness**
- **Definition:** % of campaigns with complete data (all required metrics available)
- **Target:** 90%+ completeness rate
- **Measurement:** Campaigns with complete data / Total campaigns
- **Dashboard:** Completeness rate, missing data analysis, by data source

**Attribution Coverage**
- **Definition:** % of campaigns with attribution configured and working
- **Target:** 95%+ coverage rate
- **Measurement:** Campaigns with working attribution / Total campaigns
- **Dashboard:** Coverage rate, by persona, by campaign type

### Secondary ROI Fidelity KPIs

**Data Freshness**
- **Definition:** Average time delay between event occurrence and data availability
- **Target:** <1 hour latency
- **Measurement:** Timestamp difference (event time - data availability time)
- **Dashboard:** Latency distribution, by data source, SLA compliance

**Data Quality Score**
- **Definition:** Composite score based on accuracy, completeness, freshness, consistency
- **Target:** 90+ (out of 100)
- **Measurement:** Weighted formula (accuracy × 0.4 + completeness × 0.3 + freshness × 0.2 + consistency × 0.1)
- **Dashboard:** Quality score trends, by data source

**User Trust Score**
- **Definition:** % of users who trust ROI calculations (survey-based)
- **Target:** 85%+ trust rate
- **Measurement:** Users rating trust as 4+ (out of 5) / Total survey respondents
- **Dashboard:** Trust score trends, by persona, by feature

**ROI Discrepancy Rate**
- **Definition:** % of ROI calculations with discrepancies >10% vs. manual calculations
- **Target:** <5% discrepancy rate
- **Measurement:** Discrepancies / Total ROI calculations
- **Dashboard:** Discrepancy analysis, root cause analysis

## 4. Churn Metrics

### Primary Churn KPIs

**Monthly Churn Rate**
- **Definition:** % of users who churned in the past 30 days
- **Target:** <5% monthly (industry benchmark: 5-7%)
- **Current Baseline:** 6.25%
- **Measurement:** Churned users in last 30 days / Total users at start of period
- **Segmentation:** By persona, plan tier, acquisition channel, cohort
- **Dashboard:** Monthly churn rate, trend over time, persona breakdown

**Annual Churn Rate**
- **Definition:** % of users who churned in the past 365 days
- **Target:** <40% annual (industry benchmark: 40-60%)
- **Measurement:** Churned users in last 365 days / Total users at start of period
- **Dashboard:** Annual churn rate, trend over time

**Churn by Persona**
- **Definition:** Churn rate segmented by persona type
- **Target:** <5% for all personas
- **Measurement:** Churned users by persona / Total users by persona
- **Dashboard:** Persona churn comparison, trend over time

**Churn by Plan Tier**
- **Definition:** Churn rate segmented by subscription plan
- **Target:** Lower churn for higher tiers
- **Measurement:** Churned users by plan / Total users by plan
- **Dashboard:** Plan tier churn comparison

### Secondary Churn KPIs

**Churn Reasons**
- **Definition:** Categorized reasons for churn (survey-based)
- **Categories:** Price, missing features, poor experience, found alternative, no longer needed
- **Measurement:** % of churned users citing each reason
- **Dashboard:** Churn reason breakdown, trends over time

**Time to Churn**
- **Definition:** Average time from signup to churn
- **Target:** >6 months average
- **Measurement:** Average of (churn date - signup date) for churned users
- **Dashboard:** Distribution histogram, by persona, by plan tier

**Churn Risk Score**
- **Definition:** Predictive score indicating likelihood of churn (0-100)
- **Target:** Identify at-risk users early
- **Factors:** Low engagement, support tickets, payment issues, feature non-usage
- **Dashboard:** At-risk user list, risk score distribution

**Reactivation Rate**
- **Definition:** % of churned users who reactivate within 90 days
- **Target:** 10%+ reactivation rate
- **Measurement:** Reactivated users / Churned users
- **Dashboard:** Reactivation rate, by persona, by churn reason

## 5. LTV (Lifetime Value) Metrics

### Primary LTV KPIs

**Average LTV**
- **Definition:** Average customer lifetime value (total revenue per customer)
- **Target:** $1,800+ (12 months × $150/month ARPU)
- **Current Baseline:** $1,200
- **Calculation:** Sum of (Monthly Revenue × Months Active) / Total Customers
- **Segmentation:** By persona, plan tier, acquisition channel, cohort
- **Dashboard:** Average LTV, trend over time, persona breakdown

**LTV by Persona**
- **Definition:** Average LTV segmented by persona type
- **Target:** Higher LTV for higher-value personas (Agency > Producer > Solo Podcaster)
- **Measurement:** Average LTV for each persona
- **Dashboard:** Persona LTV comparison, trend over time

**LTV/CAC Ratio**
- **Definition:** Lifetime Value / Customer Acquisition Cost
- **Target:** >3:1 (industry benchmark: 3:1 to 5:1)
- **Current Baseline:** 2.5:1
- **Measurement:** Average LTV / Average CAC
- **Dashboard:** LTV/CAC ratio, trend over time, by acquisition channel

**LTV Payback Period**
- **Definition:** Time to recover CAC (months)
- **Target:** <6 months
- **Measurement:** CAC / (Monthly ARPU × Gross Margin %)
- **Dashboard:** Payback period, trend over time

### Secondary LTV KPIs

**Cohort LTV**
- **Definition:** LTV by signup cohort
- **Target:** Increasing LTV for newer cohorts
- **Measurement:** Average LTV for each monthly/quarterly cohort
- **Dashboard:** Cohort LTV comparison, trend over time

**Expansion Revenue**
- **Definition:** Revenue from upsells, plan upgrades, add-ons
- **Target:** 20%+ of total revenue from expansion
- **Measurement:** Sum of expansion revenue / Total revenue
- **Dashboard:** Expansion revenue, by persona, by plan tier

**Contraction Revenue**
- **Definition:** Revenue lost from downgrades, plan reductions
- **Target:** <5% of total revenue lost to contraction
- **Measurement:** Sum of contraction revenue / Total revenue
- **Dashboard:** Contraction revenue, by persona, by plan tier

## 6. CAC (Customer Acquisition Cost) Metrics

### Primary CAC KPIs

**Average CAC**
- **Definition:** Total acquisition costs / New customers acquired
- **Target:** <$600 (to achieve 3:1 LTV/CAC with $1,800 LTV)
- **Current Baseline:** $480
- **Calculation:** (Marketing Spend + Sales Costs + Onboarding Costs) / New Customers
- **Segmentation:** By acquisition channel, persona, plan tier
- **Dashboard:** Average CAC, trend over time, channel breakdown

**CAC by Acquisition Channel**
- **Definition:** CAC segmented by marketing/sales channel
- **Target:** Optimize channels with best CAC
- **Channels:** Organic, Paid Ads, Content Marketing, Partnerships, Sales
- **Dashboard:** Channel CAC comparison, trend over time

**CAC Payback Period**
- **Definition:** Time to recover CAC (months)
- **Target:** <6 months
- **Measurement:** CAC / (Monthly ARPU × Gross Margin %)
- **Dashboard:** Payback period by channel, trend over time

**CAC Trend**
- **Definition:** CAC trend over time (increasing/decreasing)
- **Target:** Stable or decreasing CAC
- **Measurement:** Monthly CAC averages
- **Dashboard:** CAC trend line, by channel

### Secondary CAC KPIs

**Marketing Efficiency Ratio (MER)**
- **Definition:** Revenue / Marketing Spend
- **Target:** >3:1
- **Measurement:** Total Revenue / Total Marketing Spend
- **Dashboard:** MER trend, by channel

**Sales Efficiency**
- **Definition:** Revenue / Sales Costs
- **Target:** >5:1
- **Measurement:** Total Revenue / Total Sales Costs
- **Dashboard:** Sales efficiency trend

**Acquisition Channel Mix**
- **Definition:** % of new customers from each channel
- **Target:** Diversified mix, optimize high-performing channels
- **Measurement:** New customers by channel / Total new customers
- **Dashboard:** Channel mix pie chart, trend over time

## 7. Operational Health Metrics

### Primary Operational Health KPIs

**System Uptime**
- **Definition:** % of time system is available and operational
- **Target:** 99.9%+ uptime (SLA: 99.9%)
- **Measurement:** (Total Time - Downtime) / Total Time
- **Dashboard:** Real-time uptime, daily/weekly/monthly averages, SLA compliance

**API Uptime**
- **Definition:** % of time API is available and responding
- **Target:** 99.95%+ uptime (SLA: 99.9%)
- **Measurement:** API availability monitoring
- **Dashboard:** Real-time API uptime, endpoint breakdown

**Error Rate**
- **Definition:** % of requests that result in errors
- **Target:** <0.1% error rate
- **Measurement:** Error requests / Total requests
- **Dashboard:** Error rate trends, by endpoint, by error type

**Latency (p50, p95, p99)**
- **Definition:** Response time percentiles (50th, 95th, 99th)
- **Target:** p50 <200ms, p95 <500ms, p99 <1s
- **Measurement:** Response time distribution
- **Dashboard:** Latency percentiles, by endpoint, trend over time

### Secondary Operational Health KPIs

**Data Processing Latency**
- **Definition:** Time from data ingestion to availability
- **Target:** <1 hour latency
- **Measurement:** Timestamp difference (ingestion - availability)
- **Dashboard:** Processing latency, by data source, SLA compliance

**Report Generation Time**
- **Definition:** Time to generate a report (median, p95)
- **Target:** <5 seconds (median), <30 seconds (p95)
- **Measurement:** Report generation timestamps
- **Dashboard:** Generation time distribution, trend over time

**Support Ticket Volume**
- **Definition:** Number of support tickets per week/month
- **Target:** <10% of user base per month
- **Measurement:** Count of support tickets
- **Dashboard:** Ticket volume trends, by category, by persona

**Support Resolution Time**
- **Definition:** Average time to resolve support tickets
- **Target:** <24 hours (median), <48 hours (p95)
- **Measurement:** Time from ticket creation to resolution
- **Dashboard:** Resolution time trends, by category, by priority

**Data Quality Issues**
- **Definition:** Number of data quality issues reported per week
- **Target:** <5 issues per week
- **Measurement:** Count of data quality issues
- **Dashboard:** Issue trends, by type, by data source

## Dashboard Architecture

### Real-Time Dashboard (Grafana)

**Refresh Rate:** 30 seconds
**Data Sources:** Prometheus, InfluxDB, PostgreSQL
**Access:** Product team, engineering team, executives

**Sections:**
1. **Executive Summary**
   - Key metrics (MAU, Churn, LTV/CAC, Revenue)
   - Trend indicators (up/down arrows)
   - Alerts (critical issues)

2. **Activation Metrics**
   - TTFV distribution
   - Activation rate funnel
   - Onboarding completion rates

3. **Retention Metrics**
   - MAU/WAU trends
   - Retention curves (cohort analysis)
   - Engagement scores

4. **ROI Fidelity**
   - Attribution accuracy
   - Data completeness
   - Data quality score

5. **Churn Metrics**
   - Churn rate trends
   - Churn by persona/plan
   - At-risk users

6. **Financial Metrics**
   - LTV trends
   - CAC by channel
   - LTV/CAC ratio

7. **Operational Health**
   - System uptime
   - Error rates
   - Latency percentiles
   - Support metrics

### Weekly KPI Report

**Format:** PDF/Email
**Frequency:** Weekly (Monday)
**Recipients:** Product team, executives, stakeholders

**Sections:**
1. **Executive Summary** (1 page)
   - Key metrics vs. targets
   - Week-over-week changes
   - Critical alerts

2. **Detailed Metrics** (3-4 pages)
   - Activation metrics
   - Retention metrics
   - Churn analysis
   - Financial metrics
   - Operational health

3. **Insights & Actions** (1 page)
   - Key insights
   - Recommended actions
   - Upcoming initiatives

### Monthly KPI Review

**Format:** Presentation
**Frequency:** Monthly (First Monday)
**Duration:** 1 hour
**Participants:** Product team, executives, stakeholders

**Agenda:**
1. **Monthly Performance Review** (20 min)
   - All KPIs vs. targets
   - Month-over-month trends
   - Persona/cohort analysis

2. **Root Cause Analysis** (15 min)
   - Underperforming metrics
   - Success factors
   - Lessons learned

3. **Action Planning** (15 min)
   - Improvement initiatives
   - Resource allocation
   - Next month priorities

4. **Q&A** (10 min)

## KPI Targets & Baselines

### Current Baselines (Q4 2024)

| Metric | Baseline | Target | Timeline |
|--------|----------|--------|----------|
| Time to First Value | 2+ hours | <30 min | Q2 2025 |
| Activation Rate | 45% | 70%+ | Q3 2025 |
| 30-day Retention | 55% | 70%+ | Q2 2025 |
| 90-day Retention | 45% | 60%+ | Q3 2025 |
| Monthly Churn | 6.25% | <5% | Q2 2025 |
| Average LTV | $1,200 | $1,800+ | Q4 2025 |
| LTV/CAC Ratio | 2.5:1 | >3:1 | Q3 2025 |
| Average CAC | $480 | <$600 | Maintain |
| System Uptime | 99.5% | 99.9%+ | Q1 2025 |

### Success Criteria

**Activation Success:**
- 70%+ activation rate
- <30 minutes TTFV (90th percentile)
- 80%+ onboarding completion

**Retention Success:**
- 70%+ 30-day retention
- 60%+ 90-day retention
- 40%+ DAU/MAU ratio

**Financial Success:**
- >3:1 LTV/CAC ratio
- <6 months CAC payback
- 20%+ expansion revenue

**Operational Success:**
- 99.9%+ uptime
- <0.1% error rate
- <200ms p50 latency

---

*Last Updated: [Current Date]*
*Next Review: Monthly*
*Owner: Product Manager + Data Analyst*
*Dashboard Access: Product Team, Engineering Team, Executives*

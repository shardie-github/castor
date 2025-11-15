# Analytics & Intelligence Layer

## North Star Metric

**Metric:** Monthly Active Podcasters (MAP)
**Definition:** Number of unique users who generate at least one report or create at least one campaign per month
**Target:** 10,000 MAP by Month 12

## Activation Metric

**Metric:** Time to First Value (TTFV)
**Definition:** Time from signup to first report generated
**Target:** <10 minutes (p80)
**Current:** TBD

## Retention Metric

**Metric:** 30-Day Retention Rate
**Definition:** Percentage of users active 30 days after signup
**Target:** 80%+ (Month 3), 90%+ (Month 12)
**Current:** TBD

## Engagement Metric

**Metric:** Reports Generated per User per Month
**Definition:** Average number of reports generated per active user per month
**Target:** 2+ reports/user/month
**Current:** TBD

## Cohort Tracking

### Cohorts to Track

1. **Signup Cohort:** Users who signed up in the same week/month
2. **Activation Cohort:** Users who activated in the same week/month
3. **Conversion Cohort:** Users who converted to paid in the same week/month
4. **Feature Cohort:** Users who used a specific feature in the same week/month

### Cohort Metrics

- Retention rate by cohort
- Revenue by cohort
- Feature adoption by cohort
- Churn rate by cohort

## Funnel Instrumentation

### Signup Funnel

1. **Landing Page Visit** → Track: Page views
2. **Signup Form Started** → Track: Form starts
3. **Signup Completed** → Track: Signups
4. **Email Verified** → Track: Email verifications
5. **Onboarding Started** → Track: Onboarding starts
6. **Onboarding Completed** → Track: Activations

### Conversion Funnel

1. **Free User** → Track: Free tier usage
2. **Trial Started** → Track: Trial starts
3. **Trial Completed** → Track: Trial completions
4. **Paid Conversion** → Track: Paid signups
5. **Retention** → Track: 30/60/90-day retention

## Anomaly Detection Logic

### Detection Rules

1. **Sudden Drop in Signups**
   - Threshold: >20% drop week-over-week
   - Alert: Immediate
   - Action: Check marketing channels

2. **Increase in Churn Rate**
   - Threshold: >5% increase month-over-month
   - Alert: Weekly review
   - Action: Investigate churn reasons

3. **Feature Usage Drop**
   - Threshold: >30% drop week-over-week
   - Alert: Immediate
   - Action: Check for bugs/issues

4. **Support Ticket Spike**
   - Threshold: >50% increase week-over-week
   - Alert: Immediate
   - Action: Check for product issues

## Automated Insights Generator

### Daily Insights

- Signup trends
- Activation rates
- Feature usage
- Support ticket volume

### Weekly Insights

- Cohort retention
- Conversion rates
- Churn analysis
- Feature adoption

### Monthly Insights

- Revenue trends
- Customer lifetime value
- Market trends
- Competitive analysis

## Dashboards

### Supabase SQL Dashboards

**Dashboard 1: User Growth**
- Signups over time
- Activation rate
- Conversion rate
- Retention rate

**Dashboard 2: Product Usage**
- Feature adoption
- Reports generated
- Campaigns created
- API usage

**Dashboard 3: Revenue**
- MRR trends
- ARPU
- Churn rate
- LTV

### Google Sheets Dashboards

**Weekly Metrics Sheet:**
- Signups
- Activations
- Conversions
- Churn
- Revenue

### Vercel Analytics

- Page views
- Unique visitors
- Bounce rate
- Conversion rate
- Traffic sources

### TikTok + Meta Ads

**Campaign Performance:**
- Impressions
- Clicks
- Conversions
- CAC
- ROAS

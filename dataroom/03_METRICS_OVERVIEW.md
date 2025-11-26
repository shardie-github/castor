# Metrics Overview

**Key metrics for investors**

---

## Current Status

**Pre-Traction / MVP Complete**

**Evidence:**
- ✅ Metrics infrastructure implemented
- ✅ Dashboard ready: `/api/v1/metrics/dashboard`
- ⚠️ Need to acquire users to populate metrics

---

## Usage Metrics (When Available)

### Active Users
- **DAU:** Daily Active Users
- **WAU:** Weekly Active Users
- **MAU:** Monthly Active Users

**Target:** [FILL IN - Based on growth plan]

### Activation
- **Activation Rate:** % of users who complete onboarding → first value
- **Time to Value:** Minutes from signup to first report generated

**Target:** 60%+ activation rate, <10 minutes to value

### Retention
- **D1 Retention:** % of users active on day 1
- **D7 Retention:** % of users active on day 7
- **D30 Retention:** % of users active on day 30

**Target:** 40%+ D7, 20%+ D30

---

## Revenue Metrics (When Available)

### Revenue
- **MRR:** Monthly Recurring Revenue
- **ARR:** Annual Recurring Revenue
- **ARPU:** Average Revenue Per User

**Target:** [FILL IN - Based on projections]

### Unit Economics
- **CAC:** Customer Acquisition Cost
- **LTV:** Lifetime Value
- **LTV:CAC Ratio:** Target 3:1+
- **Payback Period:** Months to recover CAC

**Projected:**
- CAC: $20-40 (PLG channel)
- LTV: $348-990 (depending on tier)
- Payback: 1-2 months

### Conversion
- **Free → Paid:** % of free users converting
- **Upgrade Rate:** % upgrading to higher tier
- **Churn Rate:** Monthly churn %

**Target:** 5%+ free→paid, <5% monthly churn

---

## Product Metrics

### Engagement
- **Reports Generated:** Per user per month
- **Campaigns Created:** Per user per month
- **Dashboard Views:** Per user per month

**Target:** [FILL IN - Based on usage patterns]

### Feature Adoption
- **Attribution Usage:** % using attribution features
- **Sponsor Matching:** % using matching features
- **API Usage:** % using API (enterprise)

**Target:** [FILL IN - Based on feature priorities]

---

## Growth Metrics

### Acquisition
- **Signups:** New users per month
- **Signup Sources:** By channel (organic, referral, paid)
- **CAC by Channel:** Acquisition cost per channel

**Target:** [FILL IN - Based on distribution plan]

### Virality
- **Viral Coefficient:** Users acquired per existing user
- **Referral Rate:** % of users who refer others
- **Share Rate:** % sharing reports/sponsors

**Target:** 0.3+ viral coefficient

---

## Funnel Metrics

### Signup → Activation
- **Signups:** Users who register
- **Onboarding Started:** % who start onboarding
- **Onboarding Completed:** % who complete onboarding
- **First Value:** % who generate first report

**Target:** 80%+ complete onboarding, 60%+ reach first value

### Activation → Paid
- **Free Users:** Users on free tier
- **Conversion Triggers:** Users hitting limits
- **Upgrade Clicks:** Users clicking upgrade
- **Upgrade Completed:** Users who upgrade

**Target:** 5%+ free→paid conversion

---

## Operational Metrics

### Performance
- **API Response Time:** P95 latency
- **Uptime:** % availability
- **Error Rate:** % of requests failing

**Target:** <200ms P95, 99.9%+ uptime, <0.1% error rate

### Support
- **Support Tickets:** Per user per month
- **Response Time:** Average response time
- **Resolution Time:** Average resolution time

**Target:** [FILL IN - Based on support capacity]

---

## Projections (Example)

**Year 1:**
- Users: [FILL IN]
- MRR: [FILL IN]
- ARR: [FILL IN]
- CAC: $20-40
- LTV: $348-990

**Year 2:**
- Users: [FILL IN]
- MRR: [FILL IN]
- ARR: [FILL IN]

**Year 3:**
- Users: [FILL IN]
- MRR: [FILL IN]
- ARR: [FILL IN]

---

## Metrics Dashboard

**Access:**
- Local: http://localhost:8000/api/v1/metrics/dashboard
- Production: `https://api.yourdomain.com/api/v1/metrics/dashboard`

**API Endpoints:**
- `/api/v1/metrics/dashboard` - Overview
- `/api/v1/metrics/users/active` - Active users
- `/api/v1/metrics/revenue` - Revenue metrics
- `/api/v1/metrics/funnel` - Funnel metrics

---

## Notes

- **Placeholder Values:** Marked with [FILL IN] - replace with real data
- **Targets:** Based on industry benchmarks and projections
- **Update Frequency:** Weekly for active metrics, monthly for projections

---

**See Also:**
- [`yc/YC_METRICS_CHECKLIST.md`](../yc/YC_METRICS_CHECKLIST.md) - Detailed metrics checklist
- [`yc/YC_METRICS_DASHBOARD_SKETCH.md`](../yc/YC_METRICS_DASHBOARD_SKETCH.md) - Dashboard design

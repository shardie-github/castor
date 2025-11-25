# Financial Model

**For:** YC Application & Interview Prep  
**Last Updated:** 2024

---

## Overview

This document outlines financial projections, unit economics, and key assumptions for the podcast analytics and sponsorship platform.

---

## Revenue Projections

### Year 1 (Conservative)

**Assumptions:**
- Start with 0 customers
- Month 1-3: Focus on product development and early users
- Month 4-6: Launch and acquire first paying customers
- Month 7-12: Scale growth

**Monthly Breakdown:**

| Month | Free Users | Starter ($29) | Professional ($99) | Enterprise ($499) | MRR | ARR |
|-------|------------|---------------|-------------------|-------------------|-----|-----|
| 1     | 50         | 0             | 0                 | 0                 | $0  | $0  |
| 2     | 100        | 5             | 0                 | 0                 | $145| $1,740|
| 3     | 200        | 15            | 2                 | 0                 | $633| $7,596|
| 4     | 400        | 30            | 5                 | 0                 | $1,335| $16,020|
| 5     | 600        | 50            | 10                | 1                 | $2,489| $29,868|
| 6     | 800        | 75            | 15                | 2                 | $3,618| $43,416|
| 7     | 1,000      | 100           | 20                | 3                 | $4,777| $57,324|
| 8     | 1,200      | 125           | 25                | 4                 | $5,936| $71,232|
| 9     | 1,400      | 150           | 30                | 5                 | $7,095| $85,140|
| 10    | 1,600      | 175           | 35                | 6                 | $8,254| $99,048|
| 11    | 1,800      | 200           | 40                | 7                 | $9,413| $112,956|
| 12    | 2,000      | 225           | 45                | 8                 | $10,572| $126,864|

**Year 1 Total:** ~$126K ARR

---

### Year 2 (Moderate)

**Assumptions:**
- 20% MoM growth in paying customers
- 10% conversion rate (free → paid)
- 5% churn rate monthly
- Upsell rate: 25% Starter → Professional, 15% Professional → Enterprise

**Year-End Targets:**
- Free Users: 5,000
- Starter: 500 customers ($14,500 MRR)
- Professional: 100 customers ($9,900 MRR)
- Enterprise: 20 customers ($9,980 MRR)
- **Total MRR:** $34,380
- **Total ARR:** $412,560

---

### Year 3 (Optimistic)

**Assumptions:**
- 15% MoM growth
- Market expansion (50K-100K downloads segment)
- International expansion
- White-label licensing

**Year-End Targets:**
- Free Users: 15,000
- Starter: 1,500 customers ($43,500 MRR)
- Professional: 300 customers ($29,700 MRR)
- Enterprise: 50 customers ($24,950 MRR)
- **Total MRR:** $98,150
- **Total ARR:** $1,177,800

---

## Unit Economics

### Current Assumptions (Based on Market Research)

**ARPU (Average Revenue Per User):**
- Year 1: $46/month (mix of Starter and Professional)
- Year 2: $69/month (more Professional and Enterprise)
- Year 3: $65/month (more Enterprise, lower ARPU due to scale)

**CAC (Customer Acquisition Cost):**
- Product-Led Growth: $20-40
- Content Marketing / SEO: $50-100
- Community Marketing: $30-60
- Partnerships: $40-80
- **Target Overall CAC:** <$50

**LTV (Lifetime Value):**
- Average Customer Lifetime: 24 months (5% monthly churn)
- LTV = ARPU × 24 months
- Year 1: $46 × 24 = $1,104
- Year 2: $69 × 24 = $1,656
- Year 3: $65 × 24 = $1,560

**LTV:CAC Ratio:**
- Year 1: $1,104 / $50 = 22:1 (target: >3:1) ✅
- Year 2: $1,656 / $50 = 33:1 ✅
- Year 3: $1,560 / $50 = 31:1 ✅

**Payback Period:**
- Payback = CAC / (ARPU × Gross Margin %)
- Assuming 75% gross margin: $50 / ($46 × 0.75) = 1.45 months
- **Target:** <12 months ✅

**Gross Margin:**
- Infrastructure costs: ~15% of revenue
- Third-party APIs: ~5% of revenue
- Support: ~5% of revenue
- **Target Gross Margin:** 75%+

---

## Cost Structure

### Fixed Costs (Monthly)

**Personnel:**
- Founders: $0 (equity only, pre-funding)
- After funding: $20K-30K/month (2-3 employees)

**Infrastructure:**
- Database (Supabase/PostgreSQL): $200-500/month
- Redis: $50-100/month
- Compute (Fly.io/Kubernetes): $200-500/month
- Monitoring (Prometheus/Grafana): $50-100/month
- **Total Infrastructure:** $500-1,200/month

**Software/Tools:**
- Email (SendGrid): $50-200/month
- Analytics (PostHog/Mixpanel): $100-300/month
- Other tools: $100-200/month
- **Total Software:** $250-700/month

**Marketing:**
- Content creation: $500-1,000/month
- SEO tools: $100-200/month
- Paid ads (if applicable): Variable
- **Total Marketing:** $600-1,200/month

**Total Fixed Costs:** $1,350-3,100/month (pre-funding), $21,350-33,100/month (post-funding)

---

### Variable Costs

**Per Customer:**
- Infrastructure: ~$2-5/month per paying customer
- Support: ~$1-3/month per paying customer
- **Total Variable:** ~$3-8/month per paying customer

**At Scale (1,000 paying customers):**
- Infrastructure: $2,000-5,000/month
- Support: $1,000-3,000/month
- **Total Variable:** $3,000-8,000/month

---

## Break-Even Analysis

### Pre-Funding (Founders Only)

**Break-Even Point:**
- Fixed Costs: $1,350-3,100/month
- Variable Costs: $3-8/customer
- ARPU: $46/month
- Gross Margin: 75%

**Break-Even Customers:**
- ($1,350 / ($46 × 0.75)) + ($3 / ($46 × 0.75)) = ~40 customers
- **Break-Even MRR:** ~$1,840/month

**Timeline:** Month 3-4 (based on projections)

---

### Post-Funding (With Team)

**Break-Even Point:**
- Fixed Costs: $21,350-33,100/month
- Variable Costs: $3-8/customer
- ARPU: $46/month
- Gross Margin: 75%

**Break-Even Customers:**
- ($21,350 / ($46 × 0.75)) + ($3 / ($46 × 0.75)) = ~620 customers
- **Break-Even MRR:** ~$28,500/month

**Timeline:** Month 8-9 (based on projections)

---

## Funding Requirements

### Seed Round (YC)

**Amount:** $500K-1M

**Use of Funds:**
- Team (2-3 employees): $240K-360K/year
- Infrastructure: $6K-14K/year
- Marketing: $7K-14K/year
- Buffer: $50K-100K
- **Total:** $300K-500K/year

**Runway:** 12-18 months

**Milestones:**
- Month 6: $10K MRR
- Month 12: $25K MRR
- Month 18: $50K MRR (Series A ready)

---

## Key Assumptions

### Growth Assumptions

1. **Conversion Rates:**
   - Visitor → Signup: 5-10%
   - Signup → Activated: 70%+
   - Activated → Paying: 10-15%
   - Free → Starter: 10% (within 30 days)
   - Starter → Professional: 25% (within 60 days)
   - Professional → Enterprise: 15% (within 90 days)

2. **Churn Rates:**
   - Free: 20% monthly (inactive)
   - Starter: 5% monthly
   - Professional: 3% monthly
   - Enterprise: 1% monthly

3. **Growth Rates:**
   - Month 1-3: 0% (product development)
   - Month 4-6: 50% MoM
   - Month 7-12: 20% MoM
   - Year 2: 15% MoM
   - Year 3: 10% MoM

---

### Market Assumptions

1. **Market Size:**
   - Total Podcasts: 2.5M globally
   - Active Podcasts: 1M
   - Monetizing Podcasts: 500K
   - Target Segment (1K-50K downloads): 300K

2. **Penetration:**
   - Year 1: 0.7% (2,000 free users)
   - Year 2: 1.7% (5,000 free users)
   - Year 3: 5% (15,000 free users)

3. **Pricing:**
   - Starter: $29/month (or $290/year)
   - Professional: $99/month (or $990/year)
   - Enterprise: $499+/month (custom)

---

## Sensitivity Analysis

### Best Case Scenario

**Assumptions:**
- 30% MoM growth
- 15% conversion rate (free → paid)
- 3% churn rate
- Higher ARPU ($60/month)

**Year 1 ARR:** $200K+
**Year 2 ARR:** $800K+
**Year 3 ARR:** $2M+

---

### Worst Case Scenario

**Assumptions:**
- 10% MoM growth
- 5% conversion rate
- 8% churn rate
- Lower ARPU ($35/month)

**Year 1 ARR:** $50K
**Year 2 ARR:** $150K
**Year 3 ARR:** $400K

---

## Key Metrics to Track

### Monthly Metrics

- MRR (Monthly Recurring Revenue)
- ARPU (Average Revenue Per User)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- LTV:CAC Ratio
- Payback Period
- Gross Margin
- Churn Rate
- Growth Rate (MoM)

### Quarterly Metrics

- ARR (Annual Recurring Revenue)
- Net Revenue Retention
- Customer Count by Tier
- Revenue by Channel
- Unit Economics by Channel

---

*This document should be updated with real financial data as it becomes available.*

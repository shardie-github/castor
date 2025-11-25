# Growth Experiments Tracker

**For:** 500 Global Lens, Growth Team  
**Last Updated:** 2024

---

## Experiment Framework

**Format:**
- **Experiment ID:** [EXP-XXX]
- **Name:** [Experiment Name]
- **Hypothesis:** [If X, then Y, because Z]
- **Launch Date:** [Date]
- **End Date:** [Date]
- **Status:** [Planned/Running/Complete/Cancelled]
- **Primary Metric:** [Metric to measure]
- **Target:** [Target value]
- **Result:** [Actual value]
- **Decision:** [Persevere/Pivot/Kill]
- **Learnings:** [Key learnings]

---

## Growth Levers Inventory

### Lever 1: Referral Program
**Status:** Planned
**Implementation:** `src/api/referrals.py`, `frontend/app/referrals/page.tsx`
**Hypothesis:** Users will refer others if incentivized (discount, credits)
**Target Metric:** 20% referral rate, 0.7 viral coefficient
**Experiment:** EXP-001

### Lever 2: SEO Landing Pages
**Status:** Planned
**Implementation:** `frontend/app/podcast-analytics/page.tsx`, `frontend/app/podcast-roi-attribution/page.tsx`
**Hypothesis:** High-intent keywords → high conversion rate
**Target Metric:** 50+ organic signups/month, 5-10% conversion rate
**Experiment:** EXP-002

### Lever 3: Shareable Reports
**Status:** Planned
**Implementation:** `src/api/reports.py`, `frontend/components/ReportShare.tsx`
**Hypothesis:** Sponsors seeing branded reports → signups
**Target Metric:** 30% share rate, 10% conversion rate from shares
**Experiment:** EXP-003

### Lever 4: Community Content Sharing
**Status:** Planned
**Implementation:** Content templates, UTM tracking
**Hypothesis:** Sharing valuable content in communities → signups
**Target Metric:** 100+ signups/month, <$50 CAC
**Experiment:** EXP-004

### Lever 5: Hosting Platform Integration
**Status:** Planned
**Implementation:** `src/integrations/buzzsprout.py`, `frontend/app/integrations/buzzsprout/page.tsx`
**Hypothesis:** Deep integration → co-marketing → signups
**Target Metric:** 200+ signups/month, <$40 CAC
**Experiment:** EXP-005

### Lever 6: Freemium Conversion
**Status:** ✅ Implemented
**Implementation:** `src/monetization/pricing.py`, `monetization/pricing-plan.md`
**Hypothesis:** Free tier → usage → conversion triggers → paid
**Current Metric:** [TBD - needs data]
**Optimization:** A/B test conversion triggers

### Lever 7: Viral Loops
**Status:** Documented
**Implementation:** `gtm/virality-loops.md`
**Hypothesis:** Built-in growth mechanisms drive viral coefficient
**Target Metric:** 1.2 viral coefficient
**Experiments:** EXP-001, EXP-003, EXP-004

---

## Active Experiments

### EXP-001: Referral Program Launch
**Hypothesis:** If we incentivize users to refer others (1 month free for referrer, 20% off for referred), then 20% of new users will come from referrals, because users will share if incentivized.

**Launch Date:** [TBD]
**End Date:** [TBD]
**Status:** Planned

**Implementation:**
- Add referral code system (`src/api/referrals.py`)
- Create referral dashboard (`frontend/app/referrals/page.tsx`)
- Add referral tracking to signup flow
- Reward: 1 month free for referrer, 20% off for referred

**Metrics:**
- Primary: Referral rate (% of new users from referrals)
- Secondary: Viral coefficient, referral conversion rate
- Target: 20% referral rate, 0.7 viral coefficient

**Tracking:**
- Event: `referral_code_used` in signup flow
- Calculation: `referrals / total_signups`
- Dashboard: Referral metrics in growth dashboard

**Current Result:** [TBD - Not launched]

**Decision Date:** [TBD]

---

### EXP-002: SEO Landing Page for "Podcast ROI Attribution"
**Hypothesis:** If we create an SEO-optimized landing page targeting "podcast ROI attribution" (high-intent keyword), then we'll get 50+ organic signups/month, because high-intent keywords convert better.

**Launch Date:** [TBD]
**End Date:** [TBD]
**Status:** Planned

**Implementation:**
- Create landing page: `/podcast-roi-attribution`
- SEO optimize: Title, meta description, H1, content (2,000+ words)
- Add conversion form (signup CTA)
- Track via UTM: `?utm_source=seo&utm_medium=organic&utm_campaign=roi_attribution`

**Metrics:**
- Primary: Organic signups/month
- Secondary: Conversion rate, CAC
- Target: 50+ signups/month, 5-10% conversion rate, <$50 CAC

**Tracking:**
- Google Search Console: Rankings, impressions, clicks
- Analytics: Signups with UTM parameters
- Calculation: `signups / organic_visitors`

**Current Result:** [TBD - Not launched]

**Decision Date:** [TBD - 3 months after launch]

---

### EXP-003: Shareable Reports with Branding
**Hypothesis:** If we add "Share Report" functionality with "Powered by [Product]" branding, then 30% of reports will be shared and 10% of shares will convert to signups, because sponsors seeing branded reports will discover the product.

**Launch Date:** [TBD]
**End Date:** [TBD]
**Status:** Planned

**Implementation:**
- Add "Share Report" button to report generation
- Generate shareable link (public or password-protected)
- Add "Powered by [Product]" branding (subtle)
- Track share events and conversions

**Metrics:**
- Primary: Share rate (% of reports shared)
- Secondary: Conversion rate from shares, viral coefficient
- Target: 30% share rate, 10% conversion rate, +0.2 viral coefficient

**Tracking:**
- Event: `report_shared` (`src/telemetry/events.py`)
- Track signups from shared report links
- Calculation: `signups_from_shares / total_shares`

**Current Result:** [TBD - Not launched]

**Decision Date:** [TBD - 1 month after launch]

---

### EXP-004: Community Content Sharing
**Hypothesis:** If we share valuable content (case studies, guides) in podcasting communities (r/podcasting, Discord), then we'll get 100+ signups/month, because community members will discover value and sign up.

**Launch Date:** [TBD]
**End Date:** [TBD]
**Status:** Planned

**Implementation:**
- Create shareable content templates (case studies, guides)
- Share in r/podcasting, r/podcast, Discord servers
- Track referrals via UTM: `?utm_source=reddit&utm_medium=community`
- Engage authentically (not sales pitches)

**Metrics:**
- Primary: Signups/month from communities
- Secondary: CAC, engagement (upvotes, comments)
- Target: 100+ signups/month, <$50 CAC, 10+ upvotes/comments per post

**Tracking:**
- Track signups with `utm_source=reddit` or `utm_source=discord`
- Monitor community engagement (upvotes, comments)
- Calculation: `signups / community_impressions`

**Current Result:** [TBD - Not launched]

**Decision Date:** [TBD - Ongoing]

---

### EXP-005: Hosting Platform Integration (Buzzsprout)
**Hypothesis:** If we build a deep integration with Buzzsprout (hosting platform), then we'll get 200+ signups/month from their users, because integration → co-marketing → signups.

**Launch Date:** [TBD]
**End Date:** [TBD]
**Status:** Planned

**Implementation:**
- Build Buzzsprout API integration (`src/integrations/buzzsprout.py`)
- Create integration page (`frontend/app/integrations/buzzsprout/`)
- Reach out to Buzzsprout for co-marketing
- Track signups via UTM: `?utm_source=buzzsprout&utm_medium=integration`

**Metrics:**
- Primary: Signups/month from integration
- Secondary: CAC, integration adoption rate
- Target: 200+ signups/month, <$40 CAC, 10% of Buzzsprout users

**Tracking:**
- Track signups with `utm_source=buzzsprout`
- Monitor integration usage (`src/integrations/buzzsprout.py`)
- Calculation: `signups / buzzsprout_users`

**Current Result:** [TBD - Not launched]

**Decision Date:** [TBD - 1 month after partnership launch]

---

## Completed Experiments

*No experiments completed yet - all are planned.*

---

## Experiment Pipeline

### Next Week
1. **EXP-001:** Referral Program Launch
2. **EXP-003:** Shareable Reports with Branding

### Next Month
1. **EXP-002:** SEO Landing Page
2. **EXP-004:** Community Content Sharing

### Next Quarter
1. **EXP-005:** Hosting Platform Integration

---

## Channel Attribution

### Current Channel Performance

| Channel | Signups | CAC | Conversion Rate | LTV | LTV:CAC | Status |
|---------|---------|-----|-----------------|-----|---------|--------|
| Product-Led Growth | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |
| SEO | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |
| Referrals | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |
| Community | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |
| Partnerships | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |
| Paid | [X] | $[X] | [X]% | $[X] | [X]:1 | 🟢/🟡/🔴 |

**Targets:**
- CAC: $20-40 overall
- LTV:CAC: >3:1
- Conversion Rate: 10%+

---

## Growth Dashboard Metrics

**Location:** `frontend/app/admin/growth/page.tsx` (to be built)

**Metrics to Display:**
- Signups by channel (time series)
- Activation rate by channel
- Conversion rate by channel
- CAC by channel
- LTV by channel
- LTV:CAC ratio by channel
- Viral coefficient
- Referral rate
- Share rate

---

## Experiment Learnings

### Key Learnings (To Be Updated)
1. [Learning 1]
2. [Learning 2]
3. [Learning 3]

### Patterns Identified
- [Pattern 1]
- [Pattern 2]

### Best Practices
- [Best Practice 1]
- [Best Practice 2]

---

## Next Steps

### Immediate (Next 2 Weeks)
1. Launch EXP-001 (Referral Program)
2. Launch EXP-003 (Shareable Reports)
3. Build growth dashboard (`frontend/app/admin/growth/page.tsx`)

### Short-Term (Next Month)
1. Launch EXP-002 (SEO Landing Page)
2. Launch EXP-004 (Community Content Sharing)
3. Implement channel attribution tracking

### Medium-Term (Next Quarter)
1. Launch EXP-005 (Hosting Platform Integration)
2. Optimize winning channels
3. Scale experiments

---

*This document should be updated weekly with experiment status and results.*

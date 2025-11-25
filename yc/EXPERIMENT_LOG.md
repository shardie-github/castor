# Experiment Log

**For:** Techstars Mentors, Growth Team  
**Last Updated:** 2024

---

## Experiment Tracking Framework

**Format:**
- **Experiment ID:** [EXP-001]
- **Name:** [Experiment Name]
- **Hypothesis:** [If X, then Y, because Z]
- **Launch Date:** [Date]
- **End Date:** [Date]
- **Status:** [Planned/Running/Complete/Cancelled]
- **Metric:** [Primary metric to measure]
- **Target:** [Target value]
- **Result:** [Actual value]
- **Decision:** [Persevere/Pivot/Kill]
- **Learnings:** [Key learnings]

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

## Cancelled Experiments

*No experiments cancelled yet.*

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

## Experiment Metrics Dashboard

**Location:** `frontend/app/admin/growth/page.tsx` (to be built)

**Metrics to Display:**
- Active experiments count
- Experiments by status (Planned/Running/Complete/Cancelled)
- Success rate (% of experiments that hit targets)
- Average experiment duration
- Top performing experiments

---

## Experiment Review Process

### Weekly Review
- **When:** Every Monday
- **What:** Review previous week's experiments, launch new experiments
- **Who:** Growth team, founders

### Monthly Review
- **When:** First Monday of each month
- **What:** Review all experiments, decide on persevere/pivot/kill
- **Who:** Growth team, founders, mentors

### Quarterly Review
- **When:** First Monday of each quarter
- **What:** Strategic review of experiment portfolio, plan next quarter
- **Who:** Full team, advisors, mentors

---

## Experiment Templates

### New Experiment Template
```
**Experiment ID:** [EXP-XXX]
**Name:** [Experiment Name]
**Hypothesis:** [If X, then Y, because Z]
**Launch Date:** [Date]
**End Date:** [Date]
**Status:** Planned

**Implementation:**
- [Implementation step 1]
- [Implementation step 2]

**Metrics:**
- Primary: [Metric] - Target: [Target]
- Secondary: [Metric] - Target: [Target]

**Tracking:**
- Event: [Event name]
- Calculation: [Calculation method]

**Current Result:** [TBD]

**Decision Date:** [Date]
```

### Experiment Results Template
```
**Experiment ID:** [EXP-XXX]
**Name:** [Experiment Name]
**Result:** [Actual value] vs Target: [Target]
**Decision:** [Persevere/Pivot/Kill]

**Learnings:**
- [Learning 1]
- [Learning 2]

**Next Steps:**
- [Next step 1]
- [Next step 2]
```

---

*This document should be updated weekly with experiment status and results.*

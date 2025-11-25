# YC Distribution Plan

**For:** YC Application & Interview Prep  
**Last Updated:** 2024

---

## Overview

YC heavily probes distribution. This document makes the distribution strategy explicit, links it to the codebase, and proposes concrete growth experiments.

---

## Current User Acquisition Channels (Inferred from Repo)

### 1. Product-Led Growth (Freemium)

**Current State:**
- ✅ **Implemented:** Free tier with conversion triggers (`src/monetization/pricing.py`)
- ✅ **Implemented:** Self-service onboarding (MVP scope)
- ✅ **Implemented:** Usage-based upsell triggers

**How It Works:**
- Free tier: 1 podcast, 1 campaign/month, basic analytics
- Conversion triggers: 3+ reports, 2+ campaigns, 10+ dashboard views
- Upsell prompts: In-app notifications when limits approached

**Evidence:**
- `monetization/pricing-plan.md` - Freemium conversion logic
- `src/monetization/pricing.py` - `check_freemium_conversion()` method
- `mvp/mvp-scope.md` - Self-service onboarding focus

**CAC:** $20-40 (lowest cost channel)
**LTV:** $348-990 (depending on tier)

---

### 2. Content Marketing / SEO

**Current State:**
- ⚠️ **Planned:** SEO strategy documented (`gtm/seo-engine.md`)
- ⚠️ **Missing:** Blog/content site not visible in repo
- ⚠️ **Missing:** SEO implementation (meta tags, structured data)

**How It Works:**
- Target keywords: "podcast analytics", "podcast ROI attribution"
- Content: How-to guides, case studies, tutorials
- Distribution: Blog, social media, communities

**Evidence:**
- `gtm/seo-engine.md` - Keyword strategy, content calendar
- `gtm/content-engine.md` - Content pillars, formats

**CAC:** $50-100
**LTV:** $348-990

**Proposed Implementation:**
- Add blog to Next.js frontend (`frontend/app/blog/`)
- Add SEO metadata to pages (`frontend/app/layout.tsx`)
- Create content CMS or markdown-based blog

---

### 3. Community Marketing

**Current State:**
- ⚠️ **Planned:** Strategy documented (`gtm/growth-channels.md`)
- ⚠️ **Missing:** Community engagement tracking

**How It Works:**
- Participate in r/podcasting, r/podcast, Discord servers
- Share helpful content (not sales pitches)
- Build reputation as expert

**Evidence:**
- `gtm/growth-channels.md` - Community marketing tactics
- `gtm/virality-loops.md` - Community sharing loop

**CAC:** $30-60
**LTV:** $348-990

**Proposed Implementation:**
- Track referral sources (UTM parameters)
- Add referral code system (`src/api/referrals.py`)
- Create shareable content templates

---

### 4. Partnerships

**Current State:**
- ✅ **Planned:** Integration strategy (`strategy/partnership-ecosystem.md`)
- ⚠️ **Missing:** Actual integrations (hosting platforms, tools)

**How It Works:**
- Integrate with hosting platforms (Buzzsprout, Anchor, Libsyn)
- Co-marketing opportunities
- Referral commissions

**Evidence:**
- `strategy/partnership-ecosystem.md` - Partnership strategy
- `gtm/virality-loops.md` - Integration partner loop (2.0x multiplier)

**CAC:** $40-80
**LTV:** $348-990

**Proposed Implementation:**
- Build hosting platform integrations (`src/integrations/`)
- Create partner portal (`frontend/app/partners/`)
- Add referral tracking

---

## Likely Short-Term Channels (Low-Hanging Fruit)

### 1. Referral Program

**Why:** Built-in virality, low cost, high LTV

**Implementation:**
- Add referral code system
- Track referrals in database
- Reward referrers (discount, credits, features)

**Files to Create:**
- `src/api/referrals.py` - Referral code generation, tracking
- Database: `referrals` table (referrer_id, referred_id, code, status, reward)
- Frontend: Referral dashboard (`frontend/app/referrals/`)

**Goal Metric:** 20% of new users from referrals
**Effort:** LOW (2-3 days)

---

### 2. SEO Landing Pages

**Why:** High-intent traffic, low CAC, scalable

**Implementation:**
- Create SEO-optimized landing pages for target keywords
- Add to Next.js frontend (`frontend/app/[keyword]/`)
- Track conversions via UTM parameters

**Target Keywords:**
- "podcast analytics" → `/podcast-analytics`
- "podcast ROI attribution" → `/podcast-roi-attribution`
- "podcast sponsorship tracking" → `/podcast-sponsorship-tracking`

**Files to Create:**
- `frontend/app/podcast-analytics/page.tsx`
- `frontend/app/podcast-roi-attribution/page.tsx`
- SEO metadata components

**Goal Metric:** 100+ organic signups/month
**Effort:** MEDIUM (1 week)

---

### 3. Shareable Reports

**Why:** Built-in virality, sponsor sharing loop

**Implementation:**
- Add "Share Report" button to reports
- Generate shareable links (public or password-protected)
- Add "Powered by [Product]" branding

**Files to Modify:**
- `src/api/reports.py` - Add sharing functionality
- `frontend/components/ReportShare.tsx` - Share UI
- Database: `shared_reports` table (report_id, share_token, access_level)

**Goal Metric:** 30% of reports shared → 10% conversion rate
**Effort:** LOW (2-3 days)

---

## 3-5 Concrete Growth Experiments

### Experiment 1: Referral Program Launch

**Goal:** Increase viral coefficient from 0.5 to 0.7

**Hypothesis:** Users will refer others if incentivized (discount, credits)

**Implementation:**
1. Add referral code system (`src/api/referrals.py`)
2. Create referral dashboard (`frontend/app/referrals/`)
3. Add referral tracking to signup flow
4. Reward: 1 month free for referrer, 20% off for referred

**Goal Metric:**
- 20% of new users from referrals
- Viral coefficient: 0.5 → 0.7

**How to Measure:**
- Track `referral_code` in signup flow
- Calculate: `referrals / total_signups`
- Monitor referral conversion rate

**Timeline:** 1 week to build, 1 month to measure

**Files to Create/Modify:**
- `src/api/referrals.py` (new)
- `src/api/auth.py` (add referral_code parameter)
- Database migration: `referrals` table
- `frontend/app/referrals/page.tsx` (new)

---

### Experiment 2: SEO Landing Page for "Podcast ROI Attribution"

**Goal:** 50+ organic signups/month from SEO

**Hypothesis:** High-intent keyword → high conversion rate

**Implementation:**
1. Create landing page: `/podcast-roi-attribution`
2. SEO optimize: Title, meta description, H1, content
3. Add conversion form (signup CTA)
4. Track via UTM: `?utm_source=seo&utm_medium=organic&utm_campaign=roi_attribution`

**Goal Metric:**
- 50+ organic signups/month
- Conversion rate: 5-10%
- CAC: <$50

**How to Measure:**
- Google Search Console: Track rankings, impressions, clicks
- Analytics: Track signups with UTM parameters
- Calculate: `signups / organic_visitors`

**Timeline:** 1 week to build, 3 months to rank

**Files to Create:**
- `frontend/app/podcast-roi-attribution/page.tsx` (new)
- SEO metadata component
- Content: 2,000+ word guide

---

### Experiment 3: Shareable Reports with Branding

**Goal:** 30% of reports shared → 10% conversion rate

**Hypothesis:** Sponsors seeing branded reports → signups

**Implementation:**
1. Add "Share Report" button to report generation
2. Generate shareable link (public or password-protected)
3. Add "Powered by [Product]" branding (subtle)
4. Track share events and conversions

**Goal Metric:**
- 30% of reports shared
- 10% conversion rate from shares
- Viral coefficient: +0.2

**How to Measure:**
- Track `report_shared` event (`src/telemetry/events.py`)
- Track signups from shared report links
- Calculate: `signups_from_shares / total_shares`

**Timeline:** 3 days to build, 1 month to measure

**Files to Modify:**
- `src/api/reports.py` - Add sharing functionality
- `frontend/components/ReportShare.tsx` (new)
- Database: `shared_reports` table (new)
- `src/telemetry/events.py` - Add `report_shared` event

---

### Experiment 4: Community Content Sharing

**Goal:** 100+ signups/month from community shares

**Hypothesis:** Sharing valuable content in communities → signups

**Implementation:**
1. Create shareable content templates (case studies, guides)
2. Share in r/podcasting, r/podcast, Discord servers
3. Track referrals via UTM: `?utm_source=reddit&utm_medium=community`
4. Engage authentically (not sales pitches)

**Goal Metric:**
- 100+ signups/month from communities
- CAC: <$50
- Engagement: 10+ upvotes/comments per post

**How to Measure:**
- Track signups with `utm_source=reddit` or `utm_source=discord`
- Monitor community engagement (upvotes, comments)
- Calculate: `signups / community_impressions`

**Timeline:** Ongoing (1-2 posts/week)

**Files to Create:**
- Content templates (`content/templates/`)
- UTM tracking in signup flow
- Analytics dashboard for community metrics

---

### Experiment 5: Hosting Platform Integration (Buzzsprout)

**Goal:** 200+ signups/month from integration

**Hypothesis:** Deep integration → co-marketing → signups

**Implementation:**
1. Build Buzzsprout API integration (`src/integrations/buzzsprout.py`)
2. Create integration page (`frontend/app/integrations/buzzsprout/`)
3. Reach out to Buzzsprout for co-marketing
4. Track signups via UTM: `?utm_source=buzzsprout&utm_medium=integration`

**Goal Metric:**
- 200+ signups/month from integration
- CAC: <$40
- Integration adoption: 10% of Buzzsprout users

**How to Measure:**
- Track signups with `utm_source=buzzsprout`
- Monitor integration usage (`src/integrations/buzzsprout.py`)
- Calculate: `signups / buzzsprout_users`

**Timeline:** 2 weeks to build integration, 1 month to launch partnership

**Files to Create:**
- `src/integrations/buzzsprout.py` (new)
- `frontend/app/integrations/buzzsprout/page.tsx` (new)
- Integration documentation

---

## Distribution Funnel

### Proposed Funnel

**Stage 1: Visitor**
- **Source:** SEO, social media, communities, partnerships
- **Tracking:** Google Analytics, UTM parameters
- **Current:** Not instrumented (needs frontend analytics)

**Stage 2: Signup**
- **Source:** Landing pages, referral links, integrations
- **Tracking:** `onboarding_started` event (`src/telemetry/events.py`)
- **Current:** ✅ Instrumented

**Stage 3: Activated**
- **Source:** Self-service onboarding
- **Tracking:** `first_value_delivered` event
- **Current:** ✅ Instrumented

**Stage 4: Retained**
- **Source:** Product value, engagement
- **Tracking:** Retention metrics (`src/business/analytics.py`)
- **Current:** ⚠️ Missing calculation logic

**Stage 5: Paying**
- **Source:** Conversion triggers (`src/monetization/pricing.py`)
- **Tracking:** `pricing_conversion` events
- **Current:** ✅ Instrumented

---

## Channel Attribution

### How to Track Channel Performance

**Current State:**
- ⚠️ **Partially Instrumented:** `onboarding_started` event has `source` property
- ⚠️ **Missing:** UTM parameter tracking, referral code tracking

**Proposed Implementation:**
1. Add UTM parameter capture to signup flow
2. Store in `users` table: `signup_source`, `utm_source`, `utm_medium`, `utm_campaign`
3. Track conversions by channel
4. Calculate CAC by channel

**Files to Modify:**
- `src/api/auth.py` - Capture UTM parameters in signup
- Database migration: Add columns to `users` table
- `src/business/analytics.py` - Add channel attribution calculation

---

## Growth Experiments Summary

| Experiment | Goal Metric | Effort | Timeline | Files to Create/Modify |
|------------|-------------|--------|----------|------------------------|
| Referral Program | 20% referrals, 0.7 viral coeff | LOW | 1 week | `src/api/referrals.py`, `frontend/app/referrals/` |
| SEO Landing Page | 50+ signups/month | MEDIUM | 1 week | `frontend/app/podcast-roi-attribution/` |
| Shareable Reports | 30% share rate, 10% conversion | LOW | 3 days | `src/api/reports.py`, `frontend/components/ReportShare.tsx` |
| Community Sharing | 100+ signups/month | LOW | Ongoing | Content templates, UTM tracking |
| Hosting Integration | 200+ signups/month | HIGH | 2 weeks | `src/integrations/buzzsprout.py` |

---

## Distribution Strategy by Phase

### Phase 1: Months 1-3 (Foundation)

**Focus:** Product-Led Growth + SEO

**Channels:**
- Product-Led Growth (30%)
- Content Marketing / SEO (40%)
- Community Marketing (20%)
- Paid Social (10%)

**Experiments:**
- Referral Program Launch
- SEO Landing Page
- Shareable Reports

**Goal:** 500+ signups, 50+ paying customers, $2K+ MRR

---

### Phase 2: Months 4-6 (Scale)

**Focus:** Scale winning channels + partnerships

**Channels:**
- Content Marketing / SEO (30%)
- Product-Led Growth (25%)
- Community Marketing (20%)
- Paid Social (15%)
- Partnerships (10%)

**Experiments:**
- Hosting Platform Integration
- Community Content Sharing
- Paid Social Campaigns

**Goal:** 2,000+ signups, 200+ paying customers, $10K+ MRR

---

### Phase 3: Months 7-12 (Optimize)

**Focus:** Optimize CAC/LTV, scale winners

**Channels:**
- Diversify across all channels
- Optimize based on CAC/LTV
- Scale winning channels

**Experiments:**
- A/B test landing pages
- Optimize conversion funnels
- Expand partnerships

**Goal:** 5,000+ signups, 500+ paying customers, $25K+ MRR

---

## Key Metrics to Track

### Channel Metrics

**Per Channel:**
- Signups
- Activation rate
- Conversion rate (free → paid)
- CAC
- LTV
- LTV:CAC ratio

**Overall:**
- Total signups
- Total paying customers
- MRR
- Growth rate (MoM)

### Viral Metrics

- Viral coefficient (current: 0.5, target: 1.2)
- Referral rate (% of users who refer)
- Share rate (% of reports shared)
- Conversion from shares (%)

---

## What YC Partners Will Ask

**Common Questions:**
1. "How do you get users?" → Show distribution plan
2. "What's your CAC?" → Show CAC by channel
3. "What's your LTV:CAC?" → Show ratio (target: >3:1)
4. "How do you scale?" → Show growth experiments
5. "What's your viral coefficient?" → Show viral loops

**Be Ready To:**
- Explain distribution strategy clearly
- Show channel performance data
- Discuss growth experiments (what worked, what didn't)
- Demonstrate understanding of CAC/LTV by channel

---

*This document should be updated as distribution channels are tested and optimized.*

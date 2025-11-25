# Smallest Experiments: Using Existing Codebase

**For:** Lean Startup Lens, Rapid Validation  
**Last Updated:** 2024

---

## Overview

For each hypothesis, identify the smallest experiment that can be run using the existing codebase to validate or invalidate the hypothesis.

---

## Problem Hypotheses

### HYP-001: Problem Exists and Is Urgent

**Smallest Experiment:**
- **What:** Conduct 5 user interviews with solo podcasters
- **Using:** Existing user research framework (`validation/user-interview-framework.md`)
- **Time:** 1 week
- **Cost:** $250 (5 × $50 gift cards)
- **Success Criteria:** 4/5 confirm problem, top 3 pain points identified

**Why This Is Smallest:**
- Uses existing framework
- No code changes needed
- Quick validation (1 week)
- Low cost ($250)

---

### HYP-002: Problem Is Widespread

**Smallest Experiment:**
- **What:** Survey 50 podcasters (via Reddit, Discord, Twitter)
- **Using:** Existing survey questions from user research framework
- **Time:** 1 week
- **Cost:** $0 (free survey tools)
- **Success Criteria:** 70%+ confirm problem

**Why This Is Smallest:**
- Uses existing questions
- No code changes needed
- Quick validation (1 week)
- No cost

---

## Customer Hypotheses

### HYP-003: Solo Podcaster Is Right Beachhead

**Smallest Experiment:**
- **What:** Launch to 10 solo podcasters, track signups and activation
- **Using:** Existing onboarding flow (`frontend/app/onboarding/page.tsx`)
- **Time:** 2 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 7/10 activate (70% activation rate)

**Why This Is Smallest:**
- Uses existing onboarding
- No code changes needed
- Quick validation (2 weeks)
- No cost

---

### HYP-004: Freemium Model Works for Solo Podcasters

**Smallest Experiment:**
- **What:** Track conversion triggers for first 20 free users
- **Using:** Existing conversion logic (`src/monetization/pricing.py`)
- **Time:** 2-4 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 2+ users hit conversion triggers

**Why This Is Smallest:**
- Uses existing conversion logic
- No code changes needed
- Quick validation (2-4 weeks)
- No cost

---

## Feature Hypotheses

### HYP-005: Automated Reporting Is Key Feature

**Smallest Experiment:**
- **What:** Track report generation for first 10 users
- **Using:** Existing report generation (`src/api/reports.py`)
- **Time:** 1-2 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 7/10 generate reports (70% adoption)

**Why This Is Smallest:**
- Uses existing report generation
- No code changes needed
- Quick validation (1-2 weeks)
- No cost

---

### HYP-006: Attribution Tracking Is Key Feature

**Smallest Experiment:**
- **What:** Track attribution setup for first 10 campaigns
- **Using:** Existing attribution tracking (`src/attribution/`)
- **Time:** 2-4 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 8/10 set up attribution (80% setup rate)

**Why This Is Smallest:**
- Uses existing attribution tracking
- No code changes needed
- Quick validation (2-4 weeks)
- No cost

---

### HYP-007: AI Matching Is Differentiator

**Smallest Experiment:**
- **What:** Track matching usage for first 10 users
- **Using:** Existing matching engine (`src/matchmaking/`)
- **Time:** 2-4 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 5/10 use matching (50% adoption)

**Why This Is Smallest:**
- Uses existing matching engine
- No code changes needed
- Quick validation (2-4 weeks)
- No cost

---

## Revenue Hypotheses

### HYP-008: Freemium Conversion Works

**Smallest Experiment:**
- **What:** Track conversion rate for first 20 free users
- **Using:** Existing conversion logic (`src/monetization/pricing.py`)
- **Time:** 2-4 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 2+ convert (10%+ conversion rate)

**Why This Is Smallest:**
- Uses existing conversion logic
- No code changes needed
- Quick validation (2-4 weeks)
- No cost

---

### HYP-009: Pricing Tiers Are Right

**Smallest Experiment:**
- **What:** Track conversion at each tier for first 20 users
- **Using:** Existing pricing tiers (`monetization/pricing-plan.md`)
- **Time:** 2-4 weeks
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** Users convert at expected tiers

**Why This Is Smallest:**
- Uses existing pricing tiers
- No code changes needed
- Quick validation (2-4 weeks)
- No cost

---

## Growth Hypotheses

### HYP-011: Referral Program Works

**Smallest Experiment:**
- **What:** Launch referral program to 10 users, track referrals
- **Using:** Existing referral infrastructure (`src/api/referrals.py` - to be built)
- **Time:** 1 week (build) + 2 weeks (test)
- **Cost:** $200 (referral rewards)
- **Success Criteria:** 2+ referrals (20% referral rate)

**Why This Is Smallest:**
- Minimal code changes (referral system)
- Quick validation (3 weeks total)
- Low cost ($200)

---

### HYP-012: SEO Works

**Smallest Experiment:**
- **What:** Create 1 SEO landing page, track organic signups
- **Using:** Existing Next.js frontend (`frontend/app/`)
- **Time:** 1 week (build) + 1 month (rank)
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 5+ organic signups/month

**Why This Is Smallest:**
- Uses existing frontend
- Minimal code changes (1 landing page)
- Quick validation (1 month)

---

### HYP-013: Shareable Reports Work

**Smallest Experiment:**
- **What:** Add sharing to 5 reports, track shares and conversions
- **Using:** Existing report generation (`src/api/reports.py`)
- **Time:** 3 days (build) + 2 weeks (test)
- **Cost:** $0 (existing infrastructure)
- **Success Criteria:** 2+ reports shared (40% share rate), 1+ conversion

**Why This Is Smallest:**
- Uses existing report generation
- Minimal code changes (sharing functionality)
- Quick validation (2.5 weeks)

---

## Experiment Prioritization

### High Priority (Run First)
1. **HYP-001:** Problem Exists (5 interviews, 1 week, $250)
2. **HYP-003:** Solo Podcaster Beachhead (10 users, 2 weeks, $0)
3. **HYP-005:** Automated Reporting (10 users, 1-2 weeks, $0)

### Medium Priority (Run Next)
4. **HYP-004:** Freemium Model (20 users, 2-4 weeks, $0)
5. **HYP-006:** Attribution Tracking (10 campaigns, 2-4 weeks, $0)
6. **HYP-008:** Freemium Conversion (20 users, 2-4 weeks, $0)

### Low Priority (Run Later)
7. **HYP-011:** Referral Program (10 users, 3 weeks, $200)
8. **HYP-013:** Shareable Reports (5 reports, 2.5 weeks, $0)
9. **HYP-012:** SEO (1 landing page, 1 month, $0)

---

## Experiment Execution Plan

### Week 1-2: Problem Validation
- Run HYP-001 (5 interviews)
- Run HYP-002 (50 survey responses)

### Week 3-4: Customer Validation
- Run HYP-003 (10 solo podcasters)
- Run HYP-004 (20 free users)

### Week 5-6: Feature Validation
- Run HYP-005 (10 users, report generation)
- Run HYP-006 (10 campaigns, attribution)

### Week 7-8: Revenue Validation
- Run HYP-008 (20 users, conversion)
- Run HYP-009 (20 users, pricing tiers)

### Week 9-10: Growth Validation
- Run HYP-011 (10 users, referral program)
- Run HYP-013 (5 reports, shareable)

---

*This document should be updated as experiments are run and results are collected.*

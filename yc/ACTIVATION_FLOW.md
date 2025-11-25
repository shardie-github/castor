# Activation Flow: Onboarding → Activation Optimization

**For:** Product-Led Growth Lens, Activation Optimization  
**Last Updated:** 2024

---

## Overview

This document maps the onboarding → activation flow, identifies bottlenecks, and proposes improvements.

---

## Activation Definition

**What Is Activation?**

Activation is when a user completes onboarding AND generates first value (report, campaign, or attribution setup).

**Activation Criteria:**
1. ✅ Onboarding completed (RSS feed connected)
2. ✅ First value delivered (report generated OR campaign created OR attribution setup)

**Activation Rate Target:** 70%+ (of signups)

---

## Current Activation Flow

### Step 1: Signup (Day 0, <5 minutes)

**What Happens:**
- User signs up (email/password)
- User sees welcome screen
- User starts onboarding

**Current Implementation:**
- ✅ Signup flow (`frontend/app/auth/register/page.tsx`)
- ✅ Welcome screen (`frontend/app/onboarding/page.tsx`)

**Bottlenecks:**
- ⚠️ No value demonstration yet
- ⚠️ No clear value proposition

**Conversion Rate:** [TBD - Need data]

---

### Step 2: Onboarding (Day 0, <30 minutes)

**What Happens:**
1. User sees welcome screen
2. User connects RSS feed
3. User adds podcast information
4. User connects integrations (optional)
5. User completes onboarding

**Current Implementation:**
- ✅ Onboarding flow (`frontend/app/onboarding/page.tsx`)
- ✅ RSS ingestion (`src/ingestion/`)
- ✅ Dashboard (`frontend/app/dashboard/page.tsx`)

**Bottlenecks:**
- ⚠️ No value demonstration during onboarding
- ⚠️ No "aha moment" guidance
- ⚠️ No sample data to show value

**Conversion Rate:** [TBD - Need data]
**Time to Complete:** [Target: <30 minutes]

---

### Step 3: First Campaign (Day 0-1, <1 hour)

**What Happens:**
1. User navigates to campaigns
2. User creates first campaign
3. User sets up attribution (optional)
4. User sees campaign dashboard

**Current Implementation:**
- ✅ Campaign creation (`frontend/app/campaigns/new/page.tsx`)
- ✅ Attribution setup (`src/attribution/`)
- ✅ Campaign dashboard (`frontend/app/campaigns/[id]/page.tsx`)

**Bottlenecks:**
- ⚠️ Campaign creation is complex
- ⚠️ Attribution setup is optional (not guided)
- ⚠️ No value demonstration yet

**Conversion Rate:** [TBD - Need data]
**Time to Complete:** [Target: <1 hour]

---

### Step 4: First Report (Day 0-1, <30 seconds) ⭐ **ACTIVATION**

**What Happens:**
1. User navigates to reports
2. User selects campaign
3. User clicks "Generate Report"
4. Report generated in <30 seconds ⭐ **AHA MOMENT**
5. User sees ROI calculations
6. User downloads PDF

**Current Implementation:**
- ✅ Report generation (`src/api/reports.py`)
- ✅ Report download (`frontend/app/campaigns/[id]/reports/page.tsx`)

**Bottlenecks:**
- ⚠️ No guidance to generate report
- ⚠️ No value highlighting (time savings, ROI)
- ⚠️ No "aha moment" instrumentation

**Conversion Rate:** [TBD - Need data]
**Time to Complete:** [Target: <30 seconds]
**Activation:** ✅ **ACTIVATED** (first value delivered)

---

## Activation Funnel

### Funnel Stages

**Stage 1: Signup**
- **Input:** Landing page visitors
- **Output:** Signed up users
- **Conversion Rate:** [TBD - Need data]
- **Target:** [TBD - Need data]

**Stage 2: Onboarding Started**
- **Input:** Signed up users
- **Output:** Users who start onboarding
- **Conversion Rate:** [TBD - Need data]
- **Target:** 90%+ (most users start onboarding)

**Stage 3: Onboarding Completed**
- **Input:** Users who start onboarding
- **Output:** Users who complete onboarding
- **Conversion Rate:** [TBD - Need data]
- **Target:** 80%+ (most users complete onboarding)

**Stage 4: First Campaign Created**
- **Input:** Users who complete onboarding
- **Output:** Users who create first campaign
- **Conversion Rate:** [TBD - Need data]
- **Target:** 70%+ (most users create campaign)

**Stage 5: First Report Generated** ⭐ **ACTIVATION**
- **Input:** Users who create first campaign
- **Output:** Users who generate first report
- **Conversion Rate:** [TBD - Need data]
- **Target:** 70%+ (most users generate report)

**Overall Activation Rate:**
- **Target:** 70%+ (of signups)
- **Current:** [TBD - Need data]

---

## Bottleneck Analysis

### Bottleneck 1: Onboarding Completion

**Current:** [TBD - Need data]
**Target:** 80%+ completion rate

**Bottlenecks:**
- ⚠️ No value demonstration during onboarding
- ⚠️ No sample data to show value
- ⚠️ No guidance to complete onboarding

**Improvements:**
1. Add sample data during onboarding
2. Show sample report preview
3. Add onboarding hints and tooltips
4. Reduce onboarding steps (if possible)

---

### Bottleneck 2: First Campaign Creation

**Current:** [TBD - Need data]
**Target:** 70%+ campaign creation rate

**Bottlenecks:**
- ⚠️ Campaign creation is complex
- ⚠️ No guidance to create campaign
- ⚠️ No value demonstration yet

**Improvements:**
1. Simplify campaign creation
2. Add campaign creation wizard
3. Add sample campaign
4. Guide users to create first campaign

---

### Bottleneck 3: First Report Generation

**Current:** [TBD - Need data]
**Target:** 70%+ report generation rate

**Bottlenecks:**
- ⚠️ No guidance to generate report
- ⚠️ No value highlighting
- ⚠️ No "aha moment" instrumentation

**Improvements:**
1. Guide users to generate first report
2. Highlight time savings and ROI
3. Instrument "aha moment"
4. Show value immediately

---

## Activation Optimization

### Optimization 1: Reduce Time to Activation

**Current:** [TBD - Need data]
**Target:** <30 minutes from signup to activation

**Optimizations:**
1. Pre-populate sample data
2. Show sample report during onboarding
3. Guide users to generate first report
4. Reduce onboarding steps

**Expected Impact:** 25%+ increase in activation rate

---

### Optimization 2: Make Activation More Obvious

**Current:** Users discover activation themselves
**Target:** Guide users to activation

**Optimizations:**
1. Add onboarding hints ("Generate your first report")
2. Add tooltips and guided tour
3. Highlight activation value (time savings, ROI)
4. Show activation progress

**Expected Impact:** 15%+ increase in activation rate

---

### Optimization 3: Instrument Activation

**Current:** No activation tracking
**Target:** Track activation metrics

**Optimizations:**
1. Track onboarding completion
2. Track first campaign creation
3. Track first report generation
4. Track time to activation

**Expected Impact:** Better visibility, data-driven optimization

---

## Activation Metrics Dashboard

**Location:** `frontend/app/admin/plg/page.tsx` (to be built)

**Metrics to Display:**
- Activation funnel (signup → onboarding → campaign → report)
- Activation rate (%)
- Time to activation (distribution)
- Activation by user segment
- Activation impact (conversion rate, retention)

---

## Next Steps

### Immediate (Next 2-4 Weeks)
1. Instrument activation tracking
2. Collect activation data
3. Identify bottlenecks
4. Optimize activation flow

### Short-Term (Next 1-3 Months)
1. Optimize activation based on data
2. A/B test activation flows
3. Measure impact on conversion and retention

---

*This document should be updated as activation flow is optimized and metrics are collected.*

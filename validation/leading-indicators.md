# Leading Indicators & Measurement Framework

## Overview

This document establishes testable leading indicators for the podcast analytics and sponsorship tool. Leading indicators predict future success and enable proactive optimization, while lagging indicators confirm outcomes after they occur.

## Indicator Categories

### Category 1: Time-to-Value Indicators

#### Indicator 1.1: Time-to-Onboard
**Definition:** Time from account creation to completing onboarding (podcast connected + at least one platform connected)

**Measurement:**
- **Event:** `onboarding_completed`
- **Calculation:** `timestamp(onboarding_completed) - timestamp(onboarding_started)`
- **Unit:** Minutes
- **Frequency:** Per user, calculated on completion

**Targets:**
- **Solo Podcaster:** <20 minutes (90th percentile)
- **Producer:** <30 minutes (90th percentile)
- **Agency:** <45 minutes (90th percentile)
- **Overall:** <30 minutes (90th percentile)

**Why It Matters:**
- Faster onboarding = higher activation rate
- Correlates with long-term retention
- Indicates product clarity and ease of use

**Validation:**
- **Hypothesis:** If onboarding takes <30 minutes, then activation rate increases by 25%
- **Test:** Compare activation rates for users who complete in <30 min vs. >30 min

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track improvement trends
- **Action Threshold:** If >50% take >30 min, prioritize onboarding improvements

---

#### Indicator 1.2: Time-to-First-Value
**Definition:** Time from account creation to first key action (report generated, campaign launched, or attribution data viewed)

**Measurement:**
- **Event:** `first_value_delivered`
- **Calculation:** `timestamp(first_value_delivered) - timestamp(onboarding_started)`
- **Unit:** Minutes
- **Frequency:** Per user, calculated on first value

**Targets:**
- **Solo Podcaster:** <30 minutes (90th percentile)
- **Producer:** <45 minutes (90th percentile)
- **Agency:** <60 minutes (90th percentile)
- **Overall:** <30 minutes (90th percentile)

**Why It Matters:**
- Users who get value quickly are more likely to retain
- Indicates product delivers on promise
- Correlates with NPS and word-of-mouth

**Validation:**
- **Hypothesis:** If time-to-first-value <30 minutes, then 30-day retention increases by 30%
- **Test:** Compare retention for users who get value in <30 min vs. >30 min

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track improvement trends
- **Action Threshold:** If >40% take >30 min, prioritize value delivery improvements

---

### Category 2: Support & Friction Indicators

#### Indicator 2.1: Support Requests Per User Segment
**Definition:** Number of support contacts per user, segmented by persona and context

**Measurement:**
- **Event:** `support_contacted`
- **Calculation:** Count of `support_contacted` events per user
- **Segmentation:** By persona, by context (onboarding, campaign_setup, report_generation, etc.)
- **Unit:** Count per user
- **Frequency:** Weekly aggregation

**Targets:**
- **Solo Podcaster:** <0.5 support requests per user (first 30 days)
- **Producer:** <1.0 support requests per user (first 30 days)
- **Agency:** <1.5 support requests per user (first 30 days)
- **Overall:** <10% of users contact support (first 30 days)

**Why It Matters:**
- Lower support = better UX = higher satisfaction
- High support indicates friction points
- Correlates with churn risk

**Validation:**
- **Hypothesis:** If support requests <0.5 per user, then satisfaction increases by 20%
- **Test:** Compare satisfaction scores for low-support vs. high-support users

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends by context
- **Action Threshold:** If >15% contact support, investigate friction points

**Context-Specific Targets:**
- **Onboarding Support:** <5% of users
- **Campaign Setup Support:** <3% of campaigns
- **Report Generation Support:** <2% of reports
- **Attribution Support:** <5% of campaigns

---

#### Indicator 2.2: Self-Service Completion Rate
**Definition:** Percentage of users who complete key actions without contacting support

**Measurement:**
- **Actions Tracked:**
  - Onboarding completion without support
  - Campaign setup without support
  - Attribution setup without support
  - Report generation without support
- **Calculation:** `(completed_without_support / total_attempts) * 100`
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Onboarding:** >70% complete without support
- **Campaign Setup:** >90% complete without support
- **Attribution Setup:** >90% complete without support
- **Report Generation:** >95% complete without support

**Why It Matters:**
- High self-service = product clarity
- Indicates product is intuitive
- Reduces support costs

**Validation:**
- **Hypothesis:** If self-service rate >90%, then activation rate increases by 15%
- **Test:** Compare activation for high vs. low self-service users

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track improvement trends
- **Action Threshold:** If <70% for any action, prioritize UX improvements

---

### Category 3: Campaign Success Indicators

#### Indicator 3.1: Sponsor Campaign Renewal Rate
**Definition:** Percentage of sponsor campaigns that renew within 90 days of campaign end

**Measurement:**
- **Event:** Campaign renewal (tracked via `campaign_created` with same sponsor + `renewal_tool_used`)
- **Calculation:** `(renewed_campaigns / ended_campaigns) * 100`
- **Time Window:** 90 days after campaign end
- **Unit:** Percentage
- **Frequency:** Monthly aggregation (rolling 90-day window)

**Targets:**
- **Baseline:** 60% (industry average)
- **Target:** 78% (+30% improvement)
- **Stretch:** 85%

**Why It Matters:**
- **North Star Metric:** Directly tied to revenue
- Proves value of analytics/attribution
- Indicates product-market fit

**Validation:**
- **Hypothesis:** If renewal rate increases to 78%, then creator revenue increases by 35%
- **Test:** Compare renewal rates for users who generate reports vs. don't

**Leading Indicator Value:**
- **Month 1-3:** Baseline measurement
- **Month 4-6:** Track improvement trends
- **Action Threshold:** If <70%, investigate renewal blockers

**Segmentation:**
- **By Report Generation:** Renewal rate for campaigns with reports vs. without
- **By ROI Inclusion:** Renewal rate for reports with ROI vs. without
- **By Persona:** Renewal rate by creator persona

---

#### Indicator 3.2: Campaign Launch On-Time Rate
**Definition:** Percentage of campaigns launched on or before scheduled launch date

**Measurement:**
- **Event:** `campaign_launched`
- **Calculation:** `(on_time_launches / total_launches) * 100`
- **On-Time Definition:** Launched on or before `scheduled_launch_date`
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Overall:** >95% of campaigns launched on time
- **By Persona:** >90% for all personas

**Why It Matters:**
- On-time launches = sponsor satisfaction
- Indicates tool efficiency
- Correlates with renewal rates

**Validation:**
- **Hypothesis:** If on-time rate >95%, then sponsor satisfaction increases by 15%
- **Test:** Compare sponsor satisfaction for on-time vs. late launches

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track improvement trends
- **Action Threshold:** If <90%, investigate launch blockers

---

### Category 4: Engagement Indicators

#### Indicator 4.1: Monthly Active Dashboards
**Definition:** Percentage of users who view their dashboard at least once per month

**Measurement:**
- **Event:** `dashboard_viewed`
- **Calculation:** `(unique_users_with_dashboard_view / total_active_users) * 100`
- **Time Window:** Rolling 30-day window
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Solo Podcaster:** >60% monthly active
- **Producer:** >70% monthly active
- **Agency:** >80% monthly active
- **Overall:** >65% monthly active

**Why It Matters:**
- High engagement = high value perception
- Correlates with retention
- Indicates habit formation

**Validation:**
- **Hypothesis:** If monthly active >65%, then 90-day retention increases by 25%
- **Test:** Compare retention for active vs. inactive users

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends
- **Action Threshold:** If <50%, investigate engagement blockers

---

#### Indicator 4.2: Report Generation Frequency
**Definition:** Average number of reports generated per active campaign

**Measurement:**
- **Event:** `report_generated`
- **Calculation:** `total_reports_generated / total_active_campaigns`
- **Time Window:** Rolling 30-day window
- **Unit:** Reports per campaign
- **Frequency:** Weekly aggregation

**Targets:**
- **Minimum:** 1 report per campaign (campaign-end report)
- **Target:** 1.5 reports per campaign (includes mid-campaign reports)
- **Stretch:** 2.0 reports per campaign

**Why It Matters:**
- More reports = more value delivered
- Indicates proactive sponsor communication
- Correlates with renewal rates

**Validation:**
- **Hypothesis:** If report frequency >1.5 per campaign, then renewal rate increases by 20%
- **Test:** Compare renewal rates for high vs. low report frequency

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends
- **Action Threshold:** If <1.0, investigate report generation blockers

---

### Category 5: Value Delivery Indicators

#### Indicator 5.1: Sponsor Report Export Rate
**Definition:** Percentage of campaigns with at least one report exported

**Measurement:**
- **Event:** `report_exported`
- **Calculation:** `(campaigns_with_exported_report / total_campaigns) * 100`
- **Time Window:** Per campaign lifecycle
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Overall:** >80% of campaigns have exported reports
- **By Persona:** >75% for all personas

**Why It Matters:**
- Export = intent to share with sponsor
- Indicates value delivery
- Key behavioral validation

**Validation:**
- **Hypothesis:** If export rate >80%, then renewal rate increases by 25%
- **Test:** Compare renewal rates for campaigns with exports vs. without

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends
- **Action Threshold:** If <70%, investigate export blockers

---

#### Indicator 5.2: Sponsor Report Share Rate
**Definition:** Percentage of exported reports that are shared with sponsors

**Measurement:**
- **Event:** `report_shared`
- **Calculation:** `(reports_shared / reports_exported) * 100`
- **Time Window:** Within 7 days of export
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Overall:** >80% of exported reports are shared
- **By Persona:** >75% for all personas

**Why It Matters:**
- Share = actual value delivery to sponsor
- Indicates report quality and usefulness
- Directly tied to renewal rates

**Validation:**
- **Hypothesis:** If share rate >80%, then renewal rate increases by 30%
- **Test:** Compare renewal rates for shared vs. unshared reports

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends
- **Action Threshold:** If <70%, investigate share blockers or report quality

---

#### Indicator 5.3: True Sponsor ROI Calculation Usage
**Definition:** Percentage of campaigns where ROI calculation is viewed or included in reports

**Measurement:**
- **Events:** `report_generated` with `includes_roi: true` OR `roi_calculation_viewed`
- **Calculation:** `(campaigns_with_roi / total_campaigns) * 100`
- **Time Window:** Per campaign lifecycle
- **Unit:** Percentage
- **Frequency:** Weekly aggregation

**Targets:**
- **Overall:** >90% of campaigns have ROI calculated
- **In Reports:** >85% of reports include ROI
- **By Persona:** >80% for all personas

**Why It Matters:**
- ROI = value proof to sponsors
- Correlates with renewal rates
- Indicates data-driven decision making

**Validation:**
- **Hypothesis:** If ROI usage >90%, then renewal rate increases by 25%
- **Test:** Compare renewal rates for campaigns with ROI vs. without

**Leading Indicator Value:**
- **Week 1:** Baseline measurement
- **Week 2-4:** Track trends
- **Action Threshold:** If <80%, investigate ROI calculation blockers

---

## Composite Leading Indicators

### Indicator 6.1: Activation Score
**Definition:** Composite score combining time-to-value, self-service completion, and first value delivery

**Calculation:**
```
activation_score = (
  (time_to_value < 30 min ? 1 : 0) * 0.4 +
  (self_service_rate > 0.9 ? 1 : 0) * 0.3 +
  (first_value_delivered ? 1 : 0) * 0.3
) * 100
```

**Targets:**
- **High Activation:** >80 score
- **Medium Activation:** 60-80 score
- **Low Activation:** <60 score

**Why It Matters:**
- Predicts long-term retention
- Indicates product clarity and value
- Enables early intervention

**Action Thresholds:**
- **<60:** High risk, prioritize improvements
- **60-80:** Medium risk, monitor closely
- **>80:** Low risk, maintain quality

---

### Indicator 6.2: Value Delivery Score
**Definition:** Composite score combining report generation, export, share, and ROI usage

**Calculation:**
```
value_delivery_score = (
  (report_generated ? 1 : 0) * 0.25 +
  (report_exported ? 1 : 0) * 0.25 +
  (report_shared ? 1 : 0) * 0.25 +
  (roi_included ? 1 : 0) * 0.25
) * 100
```

**Targets:**
- **High Value Delivery:** >80 score
- **Medium Value Delivery:** 60-80 score
- **Low Value Delivery:** <60 score

**Why It Matters:**
- Predicts renewal rates
- Indicates value delivery to sponsors
- Enables proactive optimization

**Action Thresholds:**
- **<60:** High risk, investigate blockers
- **60-80:** Medium risk, optimize workflows
- **>80:** Low risk, maintain quality

---

## Measurement Dashboard Requirements

### Dashboard 1: Time-to-Value Dashboard
**Metrics:**
- Time-to-onboard (distribution, percentiles)
- Time-to-first-value (distribution, percentiles)
- Completion rates by step
- Drop-off points

**Segmentation:**
- By persona
- By signup source
- By time period (week/month)

**Updates:** Real-time, daily aggregation

---

### Dashboard 2: Support & Friction Dashboard
**Metrics:**
- Support requests per user segment
- Self-service completion rates
- Support requests by context
- Friction point heatmap

**Segmentation:**
- By persona
- By context (onboarding, campaign_setup, etc.)
- By time period

**Updates:** Real-time, daily aggregation

---

### Dashboard 3: Campaign Success Dashboard
**Metrics:**
- Campaign renewal rate (90-day rolling)
- Campaign launch on-time rate
- Campaign performance distribution
- Renewal rate by persona

**Segmentation:**
- By persona
- By report generation (with/without)
- By ROI inclusion (with/without)
- By time period

**Updates:** Daily aggregation, 90-day rolling windows

---

### Dashboard 4: Engagement Dashboard
**Metrics:**
- Monthly active dashboards
- Report generation frequency
- Dashboard view frequency
- Feature adoption rates

**Segmentation:**
- By persona
- By user cohort (signup date)
- By time period

**Updates:** Daily aggregation, weekly summaries

---

### Dashboard 5: Value Delivery Dashboard
**Metrics:**
- Report export rate
- Report share rate
- ROI calculation usage
- Value delivery score

**Segmentation:**
- By persona
- By campaign type
- By time period

**Updates:** Daily aggregation, weekly summaries

---

### Dashboard 6: Composite Scores Dashboard
**Metrics:**
- Activation score (distribution)
- Value delivery score (distribution)
- User health score (combination)
- Risk segmentation (high/medium/low)

**Segmentation:**
- By persona
- By user cohort
- By time period

**Updates:** Daily aggregation, weekly summaries

---

## Alerting & Action Framework

### Alert 1: Low Activation Score
**Trigger:** Activation score <60 for >20% of new users (weekly)
**Action:**
- Review onboarding funnel
- Investigate drop-off points
- Prioritize UX improvements
- A/B test onboarding flows

### Alert 2: High Support Requests
**Trigger:** Support requests >15% of users (weekly)
**Action:**
- Identify top friction points
- Review support tickets by context
- Prioritize help content improvements
- Consider in-app guidance

### Alert 3: Low Renewal Rate
**Trigger:** Renewal rate <70% (monthly, 90-day rolling)
**Action:**
- Analyze renewal rate by persona
- Compare renewal for reports vs. no reports
- Review renewal tool usage
- Interview non-renewing users

### Alert 4: Low Value Delivery Score
**Trigger:** Value delivery score <60 for >30% of campaigns (weekly)
**Action:**
- Investigate report generation blockers
- Review export/share workflows
- Analyze ROI calculation usage
- Optimize value delivery flows

### Alert 5: Low Engagement
**Trigger:** Monthly active dashboards <50% (monthly)
**Action:**
- Review engagement patterns
- Identify inactive user segments
- Consider re-engagement campaigns
- Analyze feature adoption

---

## Success Criteria

### Phase 1: MVP Validation (Months 1-3)
**Targets:**
- Time-to-onboard: <30 min (90th percentile)
- Time-to-first-value: <30 min (90th percentile)
- Support requests: <10% of users
- Self-service completion: >70% for onboarding
- Activation score: >60

### Phase 2: Growth (Months 4-6)
**Targets:**
- Campaign renewal rate: >70% (90-day)
- Report export rate: >75%
- Report share rate: >75%
- ROI usage: >85%
- Value delivery score: >70

### Phase 3: Scale (Months 7-12)
**Targets:**
- Campaign renewal rate: >78% (90-day)
- Report export rate: >80%
- Report share rate: >80%
- ROI usage: >90%
- Value delivery score: >80
- Monthly active dashboards: >65%

---

## Next Steps

1. **Week 1:** Set up measurement infrastructure
2. **Week 2:** Implement event tracking for all indicators
3. **Week 3:** Build dashboards for all indicators
4. **Week 4:** Set up alerting system
5. **Ongoing:** Monitor indicators weekly, review monthly, act on alerts

---

*Last Updated: [Current Date]*
*Next Review: Weekly during active measurement phase*

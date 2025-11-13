# Custom Analytics Events & Feedback Loops: Prototype Validation

## Overview

This document defines custom analytics events and feedback loops for the prototype to enable real behavioral validation. Events track whether users complete key actions (e.g., export sponsor report, set up campaign without support) and measure actual usage patterns vs. stated intentions.

## Event Design Principles

### 1. Action-Oriented
- Track what users **do**, not just what they view
- Focus on completion of key jobs-to-be-done
- Measure success metrics, not just engagement

### 2. Journey-Mapped
- Events map to specific journey stages
- Enable journey completion analysis
- Identify drop-off points

### 3. Persona-Tagged
- All events include persona context
- Enable persona-specific analysis
- Compare behavior across personas

### 4. Outcome-Focused
- Track leading indicators of success
- Measure value delivery, not just usage
- Connect events to business outcomes

## Core Event Categories

### Category 1: Onboarding & Setup Events

#### Event: `onboarding_started`
**Trigger:** User clicks "Get Started" or creates account
**Properties:**
- `persona_segment`: solo_podcaster | producer | agency | brand | data_marketer | sponsor
- `source`: organic | referral | ad | other
- `timestamp`: ISO 8601

**Validation Question:** Do users start onboarding? What's the conversion rate?

#### Event: `podcast_connected`
**Trigger:** User successfully connects RSS feed or hosting platform
**Properties:**
- `persona_segment`: string
- `connection_method`: rss_feed | hosting_platform | api
- `hosting_platform`: buzzsprout | libsyn | anchor | other | none
- `time_to_connect`: seconds (from onboarding_started)
- `attempts`: number of attempts before success
- `timestamp`: ISO 8601

**Validation Question:** Can users connect their podcast? How long does it take?

#### Event: `platform_connected`
**Trigger:** User connects a podcast platform (Apple, Spotify, etc.)
**Properties:**
- `persona_segment`: string
- `platform`: apple_podcasts | spotify | google_podcasts | other
- `connection_successful`: boolean
- `time_to_connect`: seconds
- `timestamp`: ISO 8601

**Validation Question:** Can users connect platforms? Which platforms are most common?

#### Event: `onboarding_completed`
**Trigger:** User completes onboarding (connects podcast + at least one platform)
**Properties:**
- `persona_segment`: string
- `time_to_complete`: seconds (from onboarding_started)
- `platforms_connected`: number
- `skipped_steps`: array of skipped step names
- `support_contacted`: boolean (did they contact support?)
- `timestamp`: ISO 8601

**Validation Question:** Do users complete onboarding without support? How long does it take?

**Success Metric:** % completing onboarding without support (target: >70%)

---

### Category 2: Campaign Management Events

#### Event: `campaign_created`
**Trigger:** User creates a new sponsor campaign
**Properties:**
- `persona_segment`: string
- `campaign_name`: string (hashed for privacy)
- `sponsor_name`: string (hashed)
- `campaign_type`: single_episode | multi_episode | ongoing
- `time_to_create`: seconds (from campaign creation start)
- `used_template`: boolean
- `template_name`: string (if used)
- `timestamp`: ISO 8601

**Validation Question:** Can users create campaigns? How long does it take?

#### Event: `attribution_setup_started`
**Trigger:** User begins setting up attribution for a campaign
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `attribution_method`: promo_code | pixel | utm | other
- `timestamp`: ISO 8601

**Validation Question:** Do users attempt attribution setup?

#### Event: `attribution_setup_completed`
**Trigger:** User completes attribution setup
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `attribution_method`: string
- `time_to_setup`: seconds (from attribution_setup_started)
- `setup_successful`: boolean
- `support_contacted`: boolean
- `timestamp`: ISO 8601

**Validation Question:** Can users set up attribution without support? How long does it take?

**Success Metric:** % completing attribution setup without support (target: >90%)
**Success Metric:** Time to attribution setup <5 minutes (target: 90% of campaigns)

#### Event: `campaign_launched`
**Trigger:** User marks campaign as "live" or launches first ad
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `time_to_launch`: seconds (from campaign_created)
- `on_time`: boolean (launched on scheduled date)
- `timestamp`: ISO 8601

**Validation Question:** Do users launch campaigns? Are they on time?

**Success Metric:** % of campaigns launched on time (target: >95%)

---

### Category 3: Report Generation Events

#### Event: `report_generation_started`
**Trigger:** User clicks "Generate Report" or navigates to report section
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `report_type`: sponsor_report | performance_summary | roi_report | other
- `timestamp`: ISO 8601

**Validation Question:** Do users attempt to generate reports?

#### Event: `report_template_selected`
**Trigger:** User selects a report template
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `template_name`: string
- `template_category`: basic | detailed | roi_focused | other
- `timestamp`: ISO 8601

**Validation Question:** Which templates do users prefer?

#### Event: `report_customized`
**Trigger:** User customizes report (adds notes, changes sections, etc.)
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `customization_type`: added_notes | changed_sections | added_branding | other
- `timestamp`: ISO 8601

**Validation Question:** Do users customize reports? What do they customize?

#### Event: `report_generated`
**Trigger:** User successfully generates report (PDF/download)
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `report_type`: string
- `time_to_generate`: seconds (from report_generation_started)
- `report_size`: bytes
- `includes_roi`: boolean
- `includes_attribution`: boolean
- `timestamp`: ISO 8601

**Validation Question:** Can users generate reports? How long does it take?

**Success Metric:** Time to report generation <5 minutes (target: 90% of reports)
**Success Metric:** % of reports with ROI included (target: >90%)

#### Event: `report_exported`
**Trigger:** User exports/downloads report
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `export_format`: pdf | csv | excel | other
- `timestamp`: ISO 8601

**Validation Question:** Do users export reports? This is a key success indicator.

**Success Metric:** % of campaigns with report exported (target: >80%)

#### Event: `report_shared`
**Trigger:** User shares report (via email, link, etc.)
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `share_method`: email | link | download | other
- `recipient_type`: sponsor | team_member | other
- `timestamp`: ISO 8601

**Validation Question:** Do users share reports with sponsors? This validates value delivery.

**Success Metric:** % of reports shared with sponsors (target: >80%)

---

### Category 4: Performance Monitoring Events

#### Event: `dashboard_viewed`
**Trigger:** User views main dashboard
**Properties:**
- `persona_segment`: string
- `view_duration`: seconds
- `campaigns_visible`: number
- `timestamp`: ISO 8601

**Validation Question:** Do users check their dashboard? How often?

#### Event: `campaign_performance_viewed`
**Trigger:** User views detailed campaign performance
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `view_duration`: seconds
- `metrics_viewed`: array of metric names
- `timestamp`: ISO 8601

**Validation Question:** Which metrics do users care about?

#### Event: `attribution_data_viewed`
**Trigger:** User views attribution/conversion data
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `view_duration`: seconds
- `attribution_method`: string
- `conversions_shown`: number
- `timestamp`: ISO 8601

**Validation Question:** Do users check attribution data? This validates attribution value.

**Success Metric:** % of campaigns with attribution data viewed (target: >70%)

#### Event: `performance_alert_clicked`
**Trigger:** User clicks on performance alert/notification
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `alert_type`: underperformance | goal_met | anomaly | other
- `action_taken`: optimized | ignored | contacted_support | other
- `timestamp`: ISO 8601

**Validation Question:** Do users act on alerts? Do alerts drive value?

---

### Category 5: Optimization & Comparison Events

#### Event: `campaign_comparison_viewed`
**Trigger:** User views campaign comparison
**Properties:**
- `persona_segment`: string
- `campaigns_compared`: number
- `comparison_metrics`: array of metric names
- `timestamp`: ISO 8601

**Validation Question:** Do users compare campaigns? This validates comparison value.

#### Event: `campaign_optimized`
**Trigger:** User makes optimization action (changes creative, adjusts targeting, etc.)
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `optimization_type`: changed_creative | adjusted_targeting | changed_schedule | other
- `trigger`: alert | manual | recommendation | other
- `timestamp`: ISO 8601

**Validation Question:** Do users optimize campaigns? Do alerts drive optimization?

**Success Metric:** % of campaigns optimized after alerts (target: >50%)

---

### Category 6: Renewal & Revenue Events

#### Event: `renewal_insights_viewed`
**Trigger:** User views renewal insights/recommendations
**Properties:**
- `persona_segment`: string
- `campaign_id`: string
- `insights_shown`: array of insight types
- `timestamp`: ISO 8601

**Validation Question:** Do users check renewal insights?

#### Event: `renewal_tool_used`
**Trigger:** User uses renewal tool (rate calculator, justification tool, etc.)
**Properties:`
- `persona_segment`: string
- `campaign_id`: string
- `tool_type`: rate_calculator | justification_tool | comparison_tool | other
- `timestamp`: ISO 8601

**Validation Question:** Do users use renewal tools? This validates renewal value.

**Success Metric:** % of campaigns with renewal tool used (target: >60%)

#### Event: `rate_increase_calculated`
**Trigger:** User calculates potential rate increase
**Properties:`
- `persona_segment`: string
- `campaign_id`: string
- `current_rate`: number (anonymized)
- `proposed_rate`: number (anonymized)
- `increase_percentage`: number
- `timestamp`: ISO 8601

**Validation Question:** Do users calculate rate increases? This validates rate justification value.

---

### Category 7: Support & Friction Events

#### Event: `support_contacted`
**Trigger:** User contacts support (chat, email, help center)
**Properties:`
- `persona_segment`: string
- `support_method`: chat | email | help_center | phone | other
- `context`: onboarding | campaign_setup | report_generation | attribution | other
- `issue_type`: bug | question | feature_request | other
- `timestamp`: ISO 8601

**Validation Question:** Where do users need help? This identifies friction points.

**Success Metric:** Support requests per user segment (target: <10% of users)

#### Event: `help_article_viewed`
**Trigger:** User views help article/documentation
**Properties:`
- `persona_segment`: string
- `article_topic`: string
- `found_via`: search | link | suggestion | other
- `was_helpful`: boolean (if feedback collected)
- `timestamp`: ISO 8601

**Validation Question:** What do users need help with? Are help articles useful?

#### Event: `onboarding_abandoned`
**Trigger:** User starts onboarding but doesn't complete within 7 days
**Properties:`
- `persona_segment`: string
- `last_step_completed`: string
- `time_spent`: seconds
- `timestamp`: ISO 8601

**Validation Question:** Where do users drop off? This identifies friction points.

---

### Category 8: Value Delivery Events

#### Event: `first_value_delivered`
**Trigger:** User completes first key action (report generated, campaign launched, etc.)
**Properties:`
- `persona_segment`: string
- `value_type`: report_generated | campaign_launched | attribution_setup | other
- `time_to_value`: seconds (from onboarding_started)
- `timestamp`: ISO 8601

**Validation Question:** How quickly do users get value? This is a key success metric.

**Success Metric:** Time to first value <30 minutes (target: 90% of users)

#### Event: `sponsor_report_sent`
**Trigger:** User sends report to sponsor (via email or share link)
**Properties:`
- `persona_segment`: string
- `campaign_id`: string
- `report_type`: string
- `days_after_campaign_end`: number (if applicable)
- `timestamp`: ISO 8601

**Validation Question:** Do users send reports to sponsors? This validates value delivery.

**Success Metric:** % of campaigns with report sent to sponsor (target: >80%)

---

## Feedback Loops

### Loop 1: Onboarding Friction Detection
**Trigger:** `onboarding_abandoned` OR `support_contacted` during onboarding
**Action:** 
- Alert product team
- Trigger follow-up survey
- Offer help/support

**Validation:** Does this reduce abandonment?

### Loop 2: Attribution Setup Support
**Trigger:** `attribution_setup_started` but not `attribution_setup_completed` within 10 minutes
**Action:**
- Show contextual help
- Offer guided setup
- Trigger support offer

**Validation:** Does this improve completion rate?

### Loop 3: Report Generation Encouragement
**Trigger:** Campaign ends but no `report_generated` within 7 days
**Action:**
- Send reminder email
- Highlight report value
- Offer template suggestions

**Validation:** Does this increase report generation?

### Loop 4: Performance Alert Follow-Up
**Trigger:** `performance_alert_clicked` but no `campaign_optimized` within 48 hours
**Action:**
- Send optimization suggestions
- Offer best practices
- Provide examples

**Validation:** Does this drive optimization actions?

### Loop 5: Renewal Tool Promotion
**Trigger:** Campaign ends within 30 days, no `renewal_tool_used`
**Action:**
- Highlight renewal tools
- Show renewal insights
- Provide rate justification examples

**Validation:** Does this increase renewal tool usage?

---

## Persona Tagging Strategy

### Automatic Tagging
- **On Signup:** Based on signup form/questionnaire
- **On Usage:** Based on behavior patterns (e.g., multiple shows = producer)
- **On Update:** Re-evaluate based on new data

### Manual Tagging
- **Admin Override:** Allow manual persona assignment
- **User Self-Report:** Allow users to update their persona

### Persona Confidence Score
- **High (0.8-1.0):** Clear signals match persona
- **Medium (0.5-0.8):** Some signals match
- **Low (<0.5):** Unclear, needs review

---

## Analytics Implementation

### Event Tracking Library
- **Recommended:** Segment, Mixpanel, Amplitude, or PostHog
- **Requirements:**
  - Persona tagging on all events
  - Journey stage tracking
  - User properties (persona, signup date, etc.)
  - Custom event properties

### Dashboard Requirements
- **Real-time:** Event stream for monitoring
- **Aggregated:** Daily/weekly summaries
- **Persona-Segmented:** Views by persona
- **Journey-Mapped:** Views by journey stage

### Key Dashboards

#### Dashboard 1: Onboarding Funnel
- `onboarding_started` → `podcast_connected` → `platform_connected` → `onboarding_completed`
- **Metrics:** Conversion rates, time to complete, drop-off points
- **Segmented by:** Persona

#### Dashboard 2: Campaign Setup Funnel
- `campaign_created` → `attribution_setup_completed` → `campaign_launched`
- **Metrics:** Completion rates, time to launch, support requests
- **Segmented by:** Persona

#### Dashboard 3: Report Generation Funnel
- `report_generation_started` → `report_generated` → `report_exported` → `report_shared`
- **Metrics:** Completion rates, time to generate, share rate
- **Segmented by:** Persona

#### Dashboard 4: Value Delivery Tracking
- `first_value_delivered` by type and time
- **Metrics:** Time to value, value type distribution
- **Segmented by:** Persona

#### Dashboard 5: Support & Friction
- `support_contacted` by context and issue type
- **Metrics:** Support rate, issue types, friction points
- **Segmented by:** Persona

---

## Success Metrics Summary

### Leading Indicators (Track Weekly)
1. **Onboarding Completion Rate:** >70% without support
2. **Time to First Value:** <30 minutes (90% of users)
3. **Attribution Setup Rate:** >90% of campaigns
4. **Report Generation Rate:** >80% of campaigns
5. **Report Share Rate:** >80% of reports shared with sponsors
6. **Support Request Rate:** <10% of users

### Behavioral Validation Questions
1. **Do users export sponsor reports?** (Target: >80%)
2. **Do users set up campaigns without support?** (Target: >90%)
3. **Do users check attribution data?** (Target: >70%)
4. **Do users use renewal tools?** (Target: >60%)
5. **Do users optimize campaigns after alerts?** (Target: >50%)

---

## Next Steps

1. **Week 1:** Set up analytics infrastructure (Segment/Mixpanel/etc.)
2. **Week 2:** Implement event tracking in prototype
3. **Week 3:** Test event tracking, validate data collection
4. **Week 4:** Launch prototype with full tracking
5. **Ongoing:** Monitor dashboards, iterate on feedback loops

---

*Last Updated: [Current Date]*
*Next Review: Weekly during prototype testing*

# ROI Attribution Methodology & Validation Plan

## Overview

This document specifies the comprehensive ROI attribution methodology for podcast sponsorship campaigns, including views, listens, ad completion, cross-device matching, demographic lift, and validation strategies.

---

## Attribution Methods

### 1. Promo Code Attribution

**Method:** Track conversions using unique promo codes mentioned in podcast episodes.

**Implementation:**
- Generate unique promo codes per campaign (e.g., "PODCAST2024", "SPONSORXYZ")
- Sponsor includes promo code in conversion flow (checkout, signup, etc.)
- Track redemption events via API/webhook

**Attribution Window:** 30 days from episode publish date

**Accuracy:** High (direct link between podcast and conversion)

**Limitations:**
- Requires sponsor integration
- Users may forget to use code
- Not suitable for all conversion types

---

### 2. Pixel/UTM Attribution

**Method:** Track conversions using tracking pixels or UTM parameters in episode show notes/links.

**Implementation:**
- Generate unique tracking pixel per campaign
- Include UTM parameters in episode links
- Track pixel fires and UTM parameter usage

**Attribution Window:** 30 days from click/impression

**Accuracy:** Medium-High (requires user to click link)

**Limitations:**
- Requires user to click link
- Ad blockers may prevent pixel tracking
- Cross-device tracking challenges

---

### 3. Direct Attribution

**Method:** Direct API integration with sponsor's conversion system.

**Implementation:**
- Sponsor sends conversion events via API
- Match conversions to campaigns using campaign_id or tracking_id
- Real-time attribution

**Attribution Window:** Configurable (default: 30 days)

**Accuracy:** Very High (direct integration)

**Limitations:**
- Requires technical integration
- Not available for all sponsors

---

### 4. Cross-Device Matching

**Method:** Match conversions across devices using probabilistic and deterministic signals.

**Implementation:**

**Deterministic Signals:**
- User login IDs
- Email addresses
- Phone numbers
- Account IDs

**Probabilistic Signals:**
- IP address
- User agent
- Device fingerprint
- Behavioral patterns
- Time-based patterns

**Matching Algorithm:**
```python
def match_cross_device(listener_event, conversion_event):
    """
    Match listener event to conversion event across devices
    """
    score = 0.0
    
    # Deterministic matching (high confidence)
    if listener_event.user_id == conversion_event.user_id:
        score += 100.0
    if listener_event.email == conversion_event.email:
        score += 100.0
    
    # Probabilistic matching (lower confidence)
    if listener_event.ip_address == conversion_event.ip_address:
        score += 20.0
    if listener_event.device_fingerprint == conversion_event.device_fingerprint:
        score += 15.0
    
    # Time-based matching
    time_diff = abs((listener_event.timestamp - conversion_event.timestamp).total_seconds())
    if time_diff < 3600:  # Within 1 hour
        score += 10.0
    elif time_diff < 86400:  # Within 24 hours
        score += 5.0
    
    # Behavioral patterns
    if listener_event.country == conversion_event.country:
        score += 5.0
    
    return score >= 50.0  # Threshold for match
```

**Confidence Levels:**
- **High (90%+):** Deterministic match (user_id, email)
- **Medium (70-90%):** Multiple probabilistic signals
- **Low (50-70%):** Single probabilistic signal

---

### 5. Demographic Lift

**Method:** Calculate conversion lift by comparing campaign conversion rates to baseline demographics.

**Implementation:**

**Baseline Calculation:**
```python
def calculate_demographic_lift(campaign_id, demographic_segment):
    """
    Calculate conversion lift for demographic segment
    """
    # Get baseline conversion rate for demographic
    baseline_rate = get_baseline_conversion_rate(
        demographic_segment=demographic_segment,
        time_period="last_90_days"
    )
    
    # Get campaign conversion rate for demographic
    campaign_rate = get_campaign_conversion_rate(
        campaign_id=campaign_id,
        demographic_segment=demographic_segment
    )
    
    # Calculate lift
    lift = campaign_rate - baseline_rate
    lift_percentage = (lift / baseline_rate) * 100 if baseline_rate > 0 else 0
    
    return {
        "baseline_rate": baseline_rate,
        "campaign_rate": campaign_rate,
        "lift": lift,
        "lift_percentage": lift_percentage,
        "statistical_significance": calculate_statistical_significance(
            baseline_rate, campaign_rate, sample_size
        )
    }
```

**Demographic Segments:**
- Age groups (18-24, 25-34, 35-44, 45-54, 55+)
- Gender (male, female, other)
- Geographic regions (country, state, city)
- Device types (mobile, desktop, smart speaker)
- Platform (Apple Podcasts, Spotify, Google Podcasts)

**Statistical Significance:**
- Minimum sample size: 100 conversions per segment
- Confidence interval: 95%
- Use chi-square test for significance

---

## ROI Calculation Methodology

### ROI Formula

```python
def calculate_roi(campaign_id):
    """
    Calculate ROI for a campaign
    """
    campaign = get_campaign(campaign_id)
    attribution_events = get_attribution_events(campaign_id)
    
    # Calculate total conversion value
    total_conversion_value = sum(
        event.conversion_data.get("conversion_value", 0)
        for event in attribution_events
    )
    
    # Campaign cost (sponsorship fee)
    campaign_cost = campaign.campaign_value
    
    # Calculate ROI
    roi = ((total_conversion_value - campaign_cost) / campaign_cost) * 100
    roas = total_conversion_value / campaign_cost if campaign_cost > 0 else 0
    
    return {
        "campaign_id": campaign_id,
        "campaign_cost": campaign_cost,
        "total_conversion_value": total_conversion_value,
        "conversions": len(attribution_events),
        "roi_percentage": roi,
        "roas": roas,
        "net_profit": total_conversion_value - campaign_cost
    }
```

### ROAS (Return on Ad Spend)

```python
roas = total_conversion_value / campaign_cost
```

### Attribution Windows

- **Default:** 30 days from episode publish date
- **Configurable:** Per campaign (7, 14, 30, 60, 90 days)
- **Last-Touch:** Most recent attribution event wins
- **First-Touch:** First attribution event wins
- **Multi-Touch:** Distribute credit across touchpoints

---

## Ad Completion Tracking

### Ad Completion Metrics

**Completion Rate:**
```python
ad_completion_rate = (
    ad_complete_events / ad_start_events
) * 100
```

**Completion by Position:**
- Pre-roll (0-30 seconds)
- Mid-roll (30-70% of episode)
- Post-roll (70-100% of episode)

**Completion by Duration:**
- Full completion (100%)
- Partial completion (50-99%)
- Skip (<50%)

### Ad Completion Attribution

**Method:** Link ad completion events to conversion events

**Implementation:**
```python
def attribute_ad_completion_to_conversion(ad_completion_event, conversion_event):
    """
    Attribute conversion to ad completion
    """
    # Check if conversion occurred within attribution window
    time_diff = (conversion_event.timestamp - ad_completion_event.timestamp).total_seconds()
    
    if time_diff < attribution_window_seconds:
        # Check if same user/device
        if match_user(ad_completion_event, conversion_event):
            return {
                "attributed": True,
                "ad_completion_rate": ad_completion_event.completion_rate,
                "time_to_conversion": time_diff
            }
    
    return {"attributed": False}
```

**Weighting:**
- Full completion (100%): 1.0x weight
- Partial completion (50-99%): 0.7x weight
- Skip (<50%): 0.3x weight

---

## Validation Plan

### Phase 1: Internal Tests

**Objective:** Validate attribution accuracy in controlled environment

**Test Setup:**
1. Create test campaigns with known conversion events
2. Generate synthetic listener events
3. Generate synthetic attribution events
4. Run attribution matching algorithm
5. Compare results to ground truth

**Success Criteria:**
- Attribution accuracy: 95%+
- ROI calculation accuracy: 98%+
- Cross-device matching accuracy: 85%+

**Timeline:** 2 weeks

**Test Cases:**
1. **Promo Code Attribution:**
   - Test: 100 conversions with promo codes
   - Expected: 100% attribution accuracy
   
2. **Pixel Attribution:**
   - Test: 100 conversions with pixel tracking
   - Expected: 95%+ attribution accuracy
   
3. **Cross-Device Matching:**
   - Test: 50 conversions across devices
   - Expected: 85%+ matching accuracy
   
4. **Demographic Lift:**
   - Test: Calculate lift for 5 demographic segments
   - Expected: Statistical significance (p < 0.05)

---

### Phase 2: Pilot Runs

**Objective:** Validate attribution with real sponsors and limited user base

**Pilot Selection:**
- 5-10 sponsors
- Mix of attribution methods (promo codes, pixels, direct API)
- Various campaign sizes (small, medium, large)

**Pilot Setup:**
1. Onboard sponsors to platform
2. Set up attribution tracking
3. Run campaigns for 30 days
4. Collect conversion data
5. Calculate ROI
6. Compare to sponsor-reported ROI

**Success Criteria:**
- Attribution accuracy: 90%+ vs. sponsor-reported
- ROI calculation accuracy: 95%+ vs. sponsor-reported
- Sponsor satisfaction: 4+ out of 5

**Timeline:** 60 days

**Metrics to Track:**
- Attribution match rate
- Conversion tracking accuracy
- ROI calculation accuracy
- Sponsor feedback scores
- System performance (latency, errors)

---

### Phase 3: A/B Experiments

**Objective:** Validate attribution methodology at scale with statistical rigor

**Experiment Design:**

**Experiment 1: Attribution Window**
- **Hypothesis:** 30-day attribution window is optimal
- **Test:** Compare 7-day, 14-day, 30-day, 60-day windows
- **Metrics:** Conversion rate, ROI, sponsor satisfaction
- **Sample Size:** 100 campaigns per group
- **Duration:** 90 days

**Experiment 2: Cross-Device Matching**
- **Hypothesis:** Cross-device matching improves attribution accuracy
- **Test:** Compare with/without cross-device matching
- **Metrics:** Attribution match rate, ROI accuracy
- **Sample Size:** 200 campaigns per group
- **Duration:** 90 days

**Experiment 3: Demographic Lift**
- **Hypothesis:** Demographic lift provides actionable insights
- **Test:** Compare campaigns with/without demographic lift analysis
- **Metrics:** Sponsor satisfaction, renewal rate
- **Sample Size:** 50 campaigns per group
- **Duration:** 60 days

**Success Criteria:**
- Statistical significance (p < 0.05)
- Practical significance (meaningful difference)
- No negative impact on user experience

**Timeline:** 90 days

---

## Validation Metrics

### Attribution Accuracy

**Definition:** Percentage of conversions correctly attributed to campaigns

**Calculation:**
```python
attribution_accuracy = (
    correctly_attributed_conversions / total_conversions
) * 100
```

**Target:** 95%+

**Measurement:**
- Compare platform attribution to sponsor-reported conversions
- Manual verification of sample conversions
- Test campaigns with known conversion events

---

### ROI Calculation Accuracy

**Definition:** Percentage of ROI calculations within 5% of actual ROI

**Calculation:**
```python
roi_accuracy = (
    campaigns_within_5_percent / total_campaigns
) * 100
```

**Target:** 98%+

**Measurement:**
- Compare calculated ROI to sponsor-reported ROI
- Manual verification of ROI calculations
- Test campaigns with known ROI

---

### Cross-Device Matching Accuracy

**Definition:** Percentage of cross-device matches that are correct

**Calculation:**
```python
cross_device_accuracy = (
    correct_matches / total_matches
) * 100
```

**Target:** 85%+

**Measurement:**
- Manual verification of cross-device matches
- Test with known user journeys across devices
- Compare to deterministic matches (ground truth)

---

### Statistical Significance

**Definition:** P-value < 0.05 for demographic lift calculations

**Calculation:**
- Use chi-square test for conversion rate comparisons
- Use t-test for continuous metrics
- Minimum sample size: 100 conversions per segment

**Target:** 95%+ of lift calculations statistically significant

---

## Implementation Roadmap

### Week 1-2: Internal Tests
- Set up test environment
- Create test campaigns
- Run internal validation tests
- Fix identified issues

### Week 3-4: Pilot Preparation
- Select pilot sponsors
- Set up attribution tracking
- Create pilot dashboard
- Train support team

### Week 5-10: Pilot Runs
- Run pilot campaigns
- Collect conversion data
- Calculate ROI
- Gather sponsor feedback
- Iterate on methodology

### Week 11-14: A/B Experiments
- Design experiments
- Set up experiment infrastructure
- Run experiments
- Analyze results
- Document findings

### Week 15-16: Final Validation
- Review all validation results
- Update methodology based on findings
- Create validation report
- Get stakeholder approval

---

## Ongoing Validation

### Continuous Monitoring

**Daily:**
- Attribution match rate
- Conversion tracking accuracy
- System errors

**Weekly:**
- ROI calculation accuracy (sample)
- Cross-device matching accuracy (sample)
- Sponsor feedback scores

**Monthly:**
- Full validation report
- Methodology updates
- Sponsor satisfaction survey

### Quality Assurance

**Automated Tests:**
- Unit tests for attribution algorithms
- Integration tests for attribution pipeline
- End-to-end tests for ROI calculations

**Manual Reviews:**
- Sample attribution events (weekly)
- Sample ROI calculations (monthly)
- Sponsor-reported discrepancies (as needed)

---

## Documentation & Reporting

### Validation Reports

**Internal Tests Report:**
- Test results
- Accuracy metrics
- Issues identified and fixed

**Pilot Runs Report:**
- Pilot results
- Sponsor feedback
- Methodology improvements

**A/B Experiments Report:**
- Experiment results
- Statistical analysis
- Recommendations

### Sponsor Reporting

**Attribution Report:**
- Attribution method used
- Conversion count
- Attribution accuracy confidence

**ROI Report:**
- Campaign cost
- Conversion value
- ROI percentage
- ROAS
- Methodology notes

---

*Last Updated: [Current Date]*
*Version: 1.0*

# Customer Success Playbooks

## Overview

This document defines comprehensive customer success playbooks focusing on retention triggers, health metrics, escalation paths, and renewal signals to ensure long-term customer success and reduce churn.

---

## Customer Health Metrics

### Health Score Calculation

**Health Score Components:**

```python
def calculate_health_score(user_id):
    """
    Calculate customer health score (0-100)
    """
    user = get_user(user_id)
    usage = get_usage_metrics(user_id)
    support = get_support_metrics(user_id)
    
    health_score = 0.0
    
    # Engagement (40 points)
    if usage.dashboard_views >= 10:
        health_score += 20.0
    elif usage.dashboard_views >= 5:
        health_score += 10.0
    
    if usage.reports_generated >= 3:
        health_score += 20.0
    elif usage.reports_generated >= 1:
        health_score += 10.0
    
    # Value Realization (30 points)
    if usage.campaigns_created >= 2:
        health_score += 15.0
    elif usage.campaigns_created >= 1:
        health_score += 7.5
    
    if usage.attribution_events_tracked >= 10:
        health_score += 15.0
    elif usage.attribution_events_tracked >= 5:
        health_score += 7.5
    
    # Support Health (20 points)
    if support.ticket_count == 0:
        health_score += 20.0
    elif support.ticket_count <= 2:
        health_score += 10.0
    elif support.ticket_count > 5:
        health_score -= 10.0
    
    if support.satisfaction_score >= 4.0:
        health_score += 10.0
    elif support.satisfaction_score >= 3.0:
        health_score += 5.0
    else:
        health_score -= 5.0
    
    # Payment Health (10 points)
    if support.payment_failures == 0:
        health_score += 10.0
    else:
        health_score -= 10.0
    
    return {
        "user_id": user_id,
        "health_score": min(max(health_score, 0), 100),
        "health_level": "healthy" if health_score >= 70 else "at_risk" if health_score >= 40 else "critical"
    }
```

**Health Levels:**
- **Healthy (70-100):** No action needed, monitor
- **At Risk (40-69):** Proactive outreach recommended
- **Critical (0-39):** Immediate intervention required

---

## Retention Triggers

### Trigger 1: Low Engagement

**Definition:** User has <5 dashboard views in last 30 days

**Risk Level:** Medium

**Actions:**
1. **Day 1:** Send email with "Getting Started" guide
2. **Day 7:** Send email with feature highlights
3. **Day 14:** In-app notification with personalized tips
4. **Day 21:** Proactive outreach from CS team

**Email Templates:**
- **Subject:** "Get more from your podcast analytics"
- **Content:** Highlight unused features, show success stories
- **CTA:** "Explore Dashboard" or "Schedule Demo"

**Success Criteria:**
- 30%+ of users increase engagement within 7 days
- 20%+ of users respond to outreach

---

### Trigger 2: No Reports Generated

**Definition:** User has not generated any reports in last 30 days

**Risk Level:** High

**Actions:**
1. **Day 1:** Send email with report generation tutorial
2. **Day 5:** In-app notification with report generation prompt
3. **Day 10:** Proactive outreach from CS team
4. **Day 15:** Offer personalized report generation assistance

**Email Templates:**
- **Subject:** "Generate your first sponsor report in minutes"
- **Content:** Step-by-step guide, video tutorial
- **CTA:** "Generate Report" or "Watch Tutorial"

**Success Criteria:**
- 40%+ of users generate report within 14 days
- 25%+ of users respond to outreach

---

### Trigger 3: No Campaigns Created

**Definition:** User has not created any campaigns in last 60 days

**Risk Level:** High

**Actions:**
1. **Day 1:** Send email with campaign creation guide
2. **Day 7:** In-app notification with campaign creation prompt
3. **Day 14:** Proactive outreach from CS team
4. **Day 21:** Offer personalized campaign setup assistance

**Email Templates:**
- **Subject:** "Start tracking your first sponsorship campaign"
- **Content:** Campaign creation guide, success stories
- **CTA:** "Create Campaign" or "Schedule Demo"

**Success Criteria:**
- 35%+ of users create campaign within 14 days
- 20%+ of users respond to outreach

---

### Trigger 4: Payment Failure

**Definition:** User has payment failure on subscription

**Risk Level:** Critical

**Actions:**
1. **Immediate:** Send email with payment update link
2. **Day 1:** In-app notification with payment update prompt
3. **Day 2:** Proactive outreach from CS team
4. **Day 3:** Phone call if still unresolved

**Email Templates:**
- **Subject:** "Update your payment method to continue"
- **Content:** Payment update link, support contact
- **CTA:** "Update Payment" or "Contact Support"

**Success Criteria:**
- 80%+ of users update payment within 3 days
- 90%+ of users resolve payment issue within 7 days

---

### Trigger 5: Support Tickets Increasing

**Definition:** User has >3 support tickets in last 30 days

**Risk Level:** Medium-High

**Actions:**
1. **Immediate:** Assign dedicated CS representative
2. **Day 1:** Proactive outreach to understand issues
3. **Day 3:** Offer personalized training session
4. **Day 7:** Follow-up to ensure issues resolved

**Success Criteria:**
- 70%+ of users have issues resolved within 7 days
- 50%+ of users report improved satisfaction

---

### Trigger 6: Feature Requests Denied

**Definition:** User requests feature not available in their tier

**Risk Level:** Medium

**Actions:**
1. **Immediate:** Acknowledge feature request
2. **Day 1:** Explain tier limitations
3. **Day 3:** Offer upgrade with feature benefits
4. **Day 7:** Follow-up with upgrade offer

**Email Templates:**
- **Subject:** "Unlock [Feature] with [Tier] upgrade"
- **Content:** Feature benefits, upgrade pricing
- **CTA:** "Upgrade Now" or "Learn More"

**Success Criteria:**
- 15%+ of users upgrade within 30 days
- 30%+ of users engage with upgrade offer

---

## Escalation Paths

### Level 1: Automated Triggers

**Triggers:**
- Low engagement
- No reports generated
- No campaigns created
- Payment failure

**Actions:**
- Automated emails
- In-app notifications
- Self-service resources

**Response Time:** Immediate

**Success Criteria:**
- 30%+ of users self-resolve
- 20%+ of users engage with automated content

---

### Level 2: Proactive Outreach

**Triggers:**
- Health score <40
- Multiple retention triggers
- High-value customer at risk

**Actions:**
- Personalized email from CS team
- In-app chat support
- Scheduled demo/training

**Response Time:** <24 hours

**Success Criteria:**
- 40%+ of users respond to outreach
- 25%+ of users improve health score within 14 days

---

### Level 3: Dedicated Support

**Triggers:**
- Critical health score (<20)
- Enterprise customers
- Escalated support issues

**Actions:**
- Dedicated CS representative
- Phone call
- Custom solution development

**Response Time:** <4 hours

**Success Criteria:**
- 80%+ of users have issues resolved
- 70%+ of users report improved satisfaction

---

### Level 4: Executive Escalation

**Triggers:**
- Enterprise customer churn risk
- Critical product issues
- Contract renewal discussions

**Actions:**
- Executive involvement
- Custom contract terms
- Product roadmap alignment

**Response Time:** <2 hours

**Success Criteria:**
- 90%+ of enterprise customers retained
- 80%+ of customers report improved satisfaction

---

## Renewal Signals

### Positive Renewal Signals

**High Engagement:**
- Dashboard views >20/month
- Reports generated >5/month
- Campaigns created >3/month
- Attribution events tracked >50/month

**Value Realization:**
- ROI calculations >200%
- Campaign renewal rate >80%
- Sponsor satisfaction >4.5/5.0
- Revenue increase >20%

**Product Adoption:**
- Using advanced features
- API access (if Professional tier)
- White-label reports (if Professional tier)
- Team collaboration (if Enterprise tier)

**Support Health:**
- No support tickets
- High satisfaction scores (>4.5/5.0)
- Positive feedback
- Referrals to other users

---

### Negative Renewal Signals

**Low Engagement:**
- Dashboard views <5/month
- No reports generated in 30 days
- No campaigns created in 60 days
- No attribution events tracked

**Value Not Realized:**
- ROI calculations <100%
- Campaign renewal rate <50%
- Sponsor dissatisfaction
- No revenue increase

**Product Issues:**
- Multiple support tickets
- Low satisfaction scores (<3.0/5.0)
- Feature requests denied
- Technical issues unresolved

**Payment Issues:**
- Payment failures
- Billing disputes
- Refund requests
- Downgrade requests

---

## Renewal Playbook

### 90 Days Before Renewal

**Actions:**
1. Review customer health score
2. Identify renewal risks
3. Create renewal plan
4. Schedule renewal discussion

**Success Criteria:**
- 100% of customers reviewed
- Renewal plan created for at-risk customers
- Renewal discussion scheduled for 80%+ of customers

---

### 60 Days Before Renewal

**Actions:**
1. Send renewal reminder email
2. Highlight value delivered
3. Offer renewal incentives (if applicable)
4. Schedule renewal call (if at risk)

**Email Templates:**
- **Subject:** "Your subscription renews in 60 days"
- **Content:** Value summary, renewal benefits, incentives
- **CTA:** "Renew Now" or "Schedule Call"

**Success Criteria:**
- 50%+ of customers engage with renewal email
- 30%+ of customers renew early

---

### 30 Days Before Renewal

**Actions:**
1. Send final renewal reminder
2. Proactive outreach to at-risk customers
3. Offer personalized renewal terms (if needed)
4. Address any outstanding issues

**Email Templates:**
- **Subject:** "Renew your subscription - 30 days remaining"
- **Content:** Urgency, value reminder, support contact
- **CTA:** "Renew Now" or "Contact Support"

**Success Criteria:**
- 70%+ of customers renew
- 80%+ of at-risk customers contacted

---

### Day of Renewal

**Actions:**
1. Automatic renewal processing
2. Confirmation email
3. Thank you message
4. Onboarding to new features (if upgraded)

**Success Criteria:**
- 95%+ of renewals process successfully
- 90%+ of customers receive confirmation

---

### Post-Renewal

**Actions:**
1. Thank you email
2. Request feedback
3. Offer upgrade (if applicable)
4. Request referral

**Success Criteria:**
- 80%+ of customers satisfied with renewal
- 20%+ of customers provide feedback
- 10%+ of customers refer others

---

## Churn Prevention

### Early Warning System

**Monitoring:**
- Daily health score updates
- Weekly engagement reviews
- Monthly churn risk analysis

**Alerts:**
- Health score drops below 40
- Multiple retention triggers active
- Payment failure
- Support tickets increasing

---

### Intervention Strategies

**Low Engagement:**
- Re-engagement campaigns
- Feature education
- Success story sharing
- Personalized tips

**Value Not Realized:**
- ROI optimization assistance
- Campaign performance review
- Best practices sharing
- Training sessions

**Product Issues:**
- Technical support escalation
- Feature request prioritization
- Bug fix communication
- Workaround solutions

**Payment Issues:**
- Payment update assistance
- Billing dispute resolution
- Payment plan options
- Refund processing

---

## Success Metrics

### Retention Metrics

**Monthly Retention Rate:**
- **Target:** >95% for Starter, >97% for Professional, >99% for Enterprise
- **Measurement:** (Users at end of month - New users) / Users at start of month

**Annual Retention Rate:**
- **Target:** >80% for Starter, >85% for Professional, >90% for Enterprise
- **Measurement:** Users retained after 12 months / Users at start

**Churn Rate:**
- **Target:** <5% monthly for Starter, <3% for Professional, <1% for Enterprise
- **Measurement:** Users churned / Total users

---

### Health Metrics

**Average Health Score:**
- **Target:** >70
- **Measurement:** Average health score across all users

**At-Risk Users:**
- **Target:** <10% of users
- **Measurement:** Users with health score <40

**Critical Users:**
- **Target:** <2% of users
- **Measurement:** Users with health score <20

---

### Engagement Metrics

**Dashboard Views:**
- **Target:** >10 views/month per user
- **Measurement:** Average dashboard views per user per month

**Reports Generated:**
- **Target:** >3 reports/month per user
- **Measurement:** Average reports generated per user per month

**Campaigns Created:**
- **Target:** >2 campaigns/month per user
- **Measurement:** Average campaigns created per user per month

---

### Support Metrics

**Support Ticket Rate:**
- **Target:** <5% of users submit tickets/month
- **Measurement:** Users with tickets / Total users

**Satisfaction Score:**
- **Target:** >4.5/5.0
- **Measurement:** Average satisfaction score from support interactions

**Resolution Time:**
- **Target:** <24 hours (p95)
- **Measurement:** Time from ticket creation to resolution

---

## Playbook Implementation

### Automation

**Automated Triggers:**
- Low engagement emails
- Payment failure notifications
- Renewal reminders
- Health score alerts

**Tools:**
- Email automation (SendGrid, Mailchimp)
- In-app notifications
- Support ticket system
- Analytics dashboard

---

### Manual Intervention

**CS Team Actions:**
- Proactive outreach
- Personalized training
- Renewal discussions
- Escalation handling

**Tools:**
- CRM system
- Support ticket system
- Video conferencing
- Analytics dashboard

---

### Reporting

**Daily Reports:**
- Health score updates
- New at-risk users
- Critical users
- Support ticket trends

**Weekly Reports:**
- Retention metrics
- Engagement trends
- Churn analysis
- Intervention effectiveness

**Monthly Reports:**
- Retention rate
- Churn rate
- Health score distribution
- Support metrics
- Renewal rate

---

*Last Updated: [Current Date]*
*Version: 1.0*

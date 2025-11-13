# Integration Guide: Modular System Components

## Overview

This guide explains how all system components integrate together, showing the data flow and interaction patterns between modules.

## Component Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
│  (User Actions → Events → API Calls)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ User Manager │  │Campaign Mgr  │  │Report Gen     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                  │            │
│         └─────────────────┴──────────────────┘            │
│                        │                                  │
└────────────────────────┼──────────────────────────────────┘
                         │
         ┌────────────────┴────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────┐
│ Analytics Store │              │  Pricing Manager │
│  (Data Storage) │              │ (Monetization)   │
└─────────────────┘              └──────────────────┘
         │                                  │
         └────────────────┬─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              TELEMETRY & MEASUREMENT                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Metrics    │  │   Events     │  │ Measurement   │   │
│  │  Collector   │  │   Logger     │  │  Framework    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                                  │
         └────────────────┬─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            BACKGROUND AGENTS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ RSS Ingest   │  │ Update Agent │  │Alert Agent    │   │
│  │   Service    │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Integration Patterns

### 1. User Onboarding Flow

```
User Signup
    ↓
UserManager.create_user()
    ↓
EventLogger.log_event("user_created")
    ↓
MetricsCollector.increment_counter("user_created")
    ↓
PricingManager.check_freemium_conversion() [background]
    ↓
RSSIngestService.poll_feed() [scheduled]
    ↓
AnalyticsStore.store_listener_metric()
```

**Telemetry Captured:**
- User creation latency
- Onboarding completion time
- Feed connection success rate
- Time to first value

### 2. Campaign Creation Flow

```
User creates campaign
    ↓
CampaignManager.create_campaign()
    ↓
PricingManager.check_limit() [check tier limits]
    ↓
EventLogger.log_event("campaign_created")
    ↓
MetricsCollector.increment_counter("campaign_created")
    ↓
ContinuousMeasurement.start_task("campaign_setup")
    ↓
[User completes attribution setup]
    ↓
ContinuousMeasurement.complete_task("campaign_setup")
    ↓
CampaignManager.launch_campaign()
    ↓
BackgroundTaskManager.check_campaign_performance() [scheduled]
```

**Telemetry Captured:**
- Campaign creation latency
- Attribution setup time
- Campaign launch success rate
- Tier limit checks

### 3. Report Generation Flow

```
User requests report
    ↓
ReportGenerator.generate_report()
    ↓
PricingManager.check_limit() [check report limit]
    ↓
AnalyticsStore.calculate_campaign_performance()
    ↓
ReportGenerator.calculate_roi()
    ↓
ReportGenerator._generate_pdf()
    ↓
EventLogger.log_event("report_generated")
    ↓
MetricsCollector.record_histogram("report_generation_time")
    ↓
ContinuousMeasurement.record_satisfaction() [optional]
```

**Telemetry Captured:**
- Report generation time
- PDF file size
- ROI calculation accuracy
- User satisfaction score

### 4. Anomaly Detection Flow

```
BackgroundTaskManager.check_campaign_performance()
    ↓
AnomalyDetector.detect_campaign_anomalies()
    ↓
[Anomaly detected]
    ↓
AlertAgent.process_alerts()
    ↓
AlertAgent._send_notification()
    ↓
EventLogger.log_event("alert_generated")
    ↓
MetricsCollector.increment_counter("alerts_generated")
```

**Telemetry Captured:**
- Anomaly detection latency
- Alert generation time
- Alert accuracy rate
- Notification delivery success

### 5. Pricing Conversion Flow

```
User hits tier limit OR shows high engagement
    ↓
PricingManager.check_limit() [returns limit exceeded]
    ↓
PricingManager.check_upsell_opportunity()
    ↓
EventLogger.log_event("conversion_triggered")
    ↓
[Show upsell notification]
    ↓
User upgrades
    ↓
UserManager.update_user(subscription_tier)
    ↓
EventLogger.log_event("subscription_upgraded")
    ↓
MetricsCollector.increment_counter("subscription_upgrade")
```

**Telemetry Captured:**
- Conversion trigger events
- Upgrade completion rate
- Time to upgrade
- Revenue impact

## Data Flow Examples

### Example 1: RSS Feed Polling → Analytics Storage

```python
# Scheduled every 15 minutes
FeedPollScheduler.start()
    ↓
RSSIngestService.poll_feed(feed_url, podcast_id)
    ↓
[Fetch and parse RSS feed]
    ↓
RSSIngestService._extract_feed_metadata()
    ↓
[Extract episode metadata]
    ↓
AnalyticsStore.store_listener_metric(ListenerMetric(...))
    ↓
MetricsCollector.record_histogram("ingestion_latency")
    ↓
EventLogger.log_event("feed_polled")
```

### Example 2: User Action → Event Logging → Support Trigger

```python
# User clicks help button after error
EventLogger.log_friction_signal(
    user_id="user123",
    signal_type="error_retry",
    page="/campaigns/create",
    feature="attribution_setup"
)
    ↓
EventLogger._detect_friction() [detects confusion]
    ↓
EventLogger._trigger_support_flow()
    ↓
EventLogger.log_event("support_triggered")
    ↓
[Show contextual help widget]
    ↓
MetricsCollector.increment_counter("support_flows_triggered")
```

### Example 3: Feature Usage → Measurement → NPS Calculation

```python
# User completes report generation
ContinuousMeasurement.start_task("report_generation")
    ↓
[User generates report]
    ↓
ContinuousMeasurement.complete_task("report_generation", SUCCESS)
    ↓
[Show satisfaction survey]
    ↓
ContinuousMeasurement.record_satisfaction(
    user_id="user123",
    score=9,
    feature="report_generation"
)
    ↓
ContinuousMeasurement.calculate_nps(feature="report_generation")
    ↓
MetricsCollector.record_gauge("nps_score", nps_value)
```

## Telemetry Integration Points

### All Modules Integrate With:

1. **MetricsCollector**
   - Record operational metrics (latency, errors, throughput)
   - Track business metrics (KPIs)
   - Monitor system health

2. **EventLogger**
   - Log user actions
   - Track feature usage
   - Detect friction signals
   - Trigger support flows

3. **ContinuousMeasurement**
   - Track task completion times
   - Measure success/failure rates
   - Record satisfaction scores
   - Calculate NPS

4. **PricingManager**
   - Check tier limits
   - Track usage for conversion
   - Trigger upsell opportunities

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db
TIMESERIES_DB_URL=influxdb://localhost:8086/analytics

# Telemetry
METRICS_ENABLED=true
EVENTS_ENABLED=true
MEASUREMENT_ENABLED=true

# Pricing
STRIPE_API_KEY=sk_test_...
PRICING_ENABLED=true

# Background Tasks
FEED_POLL_INTERVAL=900  # 15 minutes
UPDATE_INTERVAL=900
```

## Testing Integration

### Unit Tests
Each module has unit tests that mock dependencies:
- `test_rss_ingest.py` - Tests RSS ingestion with mocked HTTP
- `test_campaign_manager.py` - Tests campaign CRUD with mocked storage
- `test_pricing.py` - Tests pricing logic with mocked usage metrics

### Integration Tests
Integration tests verify component interactions:
- `test_campaign_creation_flow.py` - Full campaign creation flow
- `test_report_generation_flow.py` - Report generation with real data
- `test_conversion_flow.py` - Pricing conversion logic

### End-to-End Tests
E2E tests verify complete user journeys:
- `test_onboarding_journey.py` - User signup to first report
- `test_campaign_lifecycle.py` - Campaign creation to completion
- `test_upsell_flow.py` - Free tier to paid conversion

## Monitoring Integration

### Dashboards

1. **Operational Dashboard**
   - Service health (uptime, latency, errors)
   - Background task status
   - Database performance

2. **Business Dashboard**
   - User KPIs (time to value, renewal rate)
   - Conversion metrics (freemium → paid)
   - Revenue metrics (MRR, ARPU)

3. **Product Dashboard**
   - Feature usage
   - Task completion rates
   - NPS scores
   - Friction signals

### Alerts

- **Critical**: Service downtime, high error rates
- **High**: Campaign anomalies, conversion failures
- **Medium**: Performance degradation, limit approaching
- **Low**: Usage trends, satisfaction changes

## Best Practices

1. **Always log events** for user actions
2. **Record metrics** for all operations
3. **Track tasks** for key workflows
4. **Check limits** before resource creation
5. **Detect friction** and trigger support
6. **Measure satisfaction** after value delivery
7. **Monitor conversion** opportunities

---

*Last Updated: [Current Date]*
*Version: 1.0*

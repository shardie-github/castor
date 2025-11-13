# System Architecture: Podcast Analytics & Sponsorship Platform

## Overview

This document describes the system architecture for the podcast analytics and sponsorship platform, showing data flow from ingestion through processing, analytics, frontend, partner APIs, and reporting endpoints. It also identifies where user KPIs and operational telemetry (latency, uptime, support flows) are captured.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL DATA SOURCES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  RSS Feeds  │  Apple Podcasts  │  Spotify  │  Google Podcasts  │  Others   │
└──────┬──────┴────────┬──────────┴─────┬─────┴────────┬──────────┴─────┬─────┘
       │               │                 │              │                │
       └───────────────┴─────────────────┴──────────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  RSS/Feed Ingest Service                                             │  │
│  │  - RSS feed polling (every 15 min)                                   │  │
│  │  - Episode metadata extraction                                       │  │
│  │  - Feed validation & normalization                                   │  │
│  │  📊 Telemetry: ingestion_latency, feed_errors, poll_success_rate     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Platform API Integrations                                           │  │
│  │  - Apple Podcasts Connect API                                        │  │
│  │  - Spotify for Podcasters API                                        │  │
│  │  - Google Podcasts Manager API                                       │  │
│  │  📊 Telemetry: api_latency, api_error_rate, rate_limit_hits          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Webhook Receivers                                                   │  │
│  │  - Real-time episode publish events                                  │  │
│  │  - Platform analytics updates                                        │  │
│  │  📊 Telemetry: webhook_volume, processing_latency                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Data Processing Pipeline                                            │  │
│  │  - Episode metadata normalization                                    │  │
│  │  - Listener data aggregation                                         │  │
│  │  - Attribution event processing                                      │  │
│  │  - Data deduplication & validation                                  │  │
│  │  📊 Telemetry: processing_latency, data_quality_score, error_rate   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Attribution Engine                                                  │  │
│  │  - Promo code tracking                                               │  │
│  │  - Pixel/UTM parameter attribution                                   │  │
│  │  - Conversion event matching                                         │  │
│  │  - Multi-touch attribution models                                    │  │
│  │  📊 Telemetry: attribution_accuracy, match_rate, processing_time     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Background Task Agents                                               │  │
│  │  - Feed update scheduler (every 15 min)                             │  │
│  │  - Analytics aggregation (hourly)                                    │  │
│  │  - Anomaly detection (real-time)                                      │  │
│  │  - Alert generation                                                  │  │
│  │  - Report generation queue                                           │  │
│  │  📊 Telemetry: task_success_rate, task_duration, queue_depth         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANALYTICS STORE                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Time-Series Database (InfluxDB/TimescaleDB)                        │  │
│  │  - Listener metrics (downloads, streams, completion rates)          │  │
│  │  - Attribution events                                                │  │
│  │  - Campaign performance data                                         │  │
│  │  📊 Telemetry: query_latency, storage_usage, retention_policy        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Relational Database (PostgreSQL)                                   │  │
│  │  - Users, podcasts, campaigns                                        │  │
│  │  - Sponsor information                                               │  │
│  │  - Report templates & configurations                                 │  │
│  │  📊 Telemetry: query_performance, connection_pool_usage, db_size     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Data Warehouse (BigQuery/Redshift)                                  │  │
│  │  - Historical analytics                                              │  │
│  │  - Cross-campaign analysis                                           │  │
│  │  - Business intelligence queries                                      │  │
│  │  📊 Telemetry: query_cost, data_freshness, warehouse_size           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANALYTICS & COMPUTATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Analytics Computation Service                                       │  │
│  │  - KPI calculations (downloads, engagement, ROI)                      │  │
│  │  - Aggregations & rollups                                            │  │
│  │  - Benchmark comparisons                                            │  │
│  │  - Predictive analytics                                              │  │
│  │  📊 Telemetry: computation_latency, cache_hit_rate, cpu_usage        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Campaign Management Service                                          │  │
│  │  - Campaign CRUD operations                                          │  │
│  │  - Sponsor relationship management                                   │  │
│  │  - Campaign lifecycle management                                     │  │
│  │  📊 Telemetry: api_latency, error_rate, operation_duration          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Reporting Service                                                   │  │
│  │  - Report template management                                        │  │
│  │  - PDF generation                                                    │  │
│  │  - Report scheduling & automation                                     │  │
│  │  📊 Telemetry: report_generation_time, pdf_size, generation_success  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API LAYER                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  REST API Gateway                                                     │  │
│  │  - Authentication & authorization                                    │  │
│  │  - Rate limiting                                                     │  │
│  │  - Request routing                                                   │  │
│  │  📊 Telemetry: api_latency, error_rate, rate_limit_hits, throughput │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Partner API                                                          │  │
│  │  - External integrations (hosting platforms, ad networks)            │  │
│  │  - Webhook endpoints                                                 │  │
│  │  - OAuth token management                                            │  │
│  │  📊 Telemetry: partner_api_latency, integration_health, token_refresh │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Reporting Endpoints                                                  │  │
│  │  - Report generation API                                              │  │
│  │  - Report sharing/export endpoints                                    │  │
│  │  - Scheduled report delivery                                         │  │
│  │  📊 Telemetry: endpoint_latency, report_delivery_success            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Web Application (React/Next.js)                                      │  │
│  │  - Dashboard & analytics views                                       │  │
│  │  - Campaign management UI                                            │  │
│  │  - Report builder & preview                                          │  │
│  │  - User settings & billing                                           │  │
│  │  📊 Telemetry: page_load_time, js_error_rate, user_interactions       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Mobile App (React Native)                                            │  │
│  │  - Dashboard views                                                    │  │
│  │  - Push notifications                                                 │  │
│  │  📊 Telemetry: app_crash_rate, session_duration, engagement          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TELEMETRY & OBSERVABILITY                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Event Logging Service                                               │  │
│  │  - User action events (page views, clicks, form submissions)         │  │
│  │  - Feature usage tracking                                            │  │
│  │  - Friction/confusion signals                                        │  │
│  │  - Support flow triggers                                             │  │
│  │  📊 Metrics: event_volume, event_processing_latency                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Metrics Collection (Prometheus)                                      │  │
│  │  - Application metrics (latency, throughput, errors)                 │  │
│  │  - Infrastructure metrics (CPU, memory, disk)                        │  │
│  │  - Business metrics (KPIs)                                          │  │
│  │  📊 Metrics: metric_collection_rate, metric_cardinality              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Distributed Tracing (Jaeger/Zipkin)                                 │  │
│  │  - Request tracing across services                                    │  │
│  │  - Latency breakdown by service                                      │  │
│  │  - Error correlation                                                 │  │
│  │  📊 Metrics: trace_volume, trace_processing_time                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Log Aggregation (ELK Stack)                                         │  │
│  │  - Application logs                                                   │  │
│  │  - Error logs                                                        │  │
│  │  - Audit logs                                                         │  │
│  │  📊 Metrics: log_volume, log_processing_latency                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  User KPI Tracking                                                   │  │
│  │  - Time to first value                                               │  │
│  │  - Campaign renewal rate                                             │  │
│  │  - Report generation rate                                            │  │
│  │  - Attribution setup completion                                      │  │
│  │  - Support request rate                                               │  │
│  │  📊 Metrics: kpi_calculation_latency, kpi_accuracy                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Operational Telemetry                                                │  │
│  │  - Service uptime & availability                                      │  │
│  │  - Latency percentiles (p50, p95, p99)                               │  │
│  │  - Error rates by service                                            │  │
│  │  - Support flow metrics (ticket volume, resolution time)              │  │
│  │  - Background task health                                            │  │
│  │  📊 Metrics: telemetry_collection_rate, alert_accuracy               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING & ALERTING                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Monitoring Dashboard (Grafana)                                       │  │
│  │  - Real-time service health                                          │  │
│  │  - KPI dashboards                                                    │  │
│  │  - User journey funnels                                              │  │
│  │  - Business metrics                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Alerting System (Alertmanager)                                       │  │
│  │  - Service downtime alerts                                            │  │
│  │  - Latency threshold alerts                                          │  │
│  │  - Error rate alerts                                                 │  │
│  │  - Anomaly detection alerts                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ingestion Flow
```
External Sources → Ingestion Layer → Processing Layer → Analytics Store
```

**Telemetry Capture Points:**
- Feed polling latency
- API response times
- Webhook processing time
- Data validation errors

### 2. Processing Flow
```
Analytics Store → Analytics Computation → API Layer → Frontend
```

**Telemetry Capture Points:**
- Query latency
- Computation time
- Cache hit rates
- API response times

### 3. User Action Flow
```
Frontend → API Layer → Analytics Computation → Analytics Store
         ↓
    Event Logging → Telemetry System
```

**Telemetry Capture Points:**
- Page load times
- API latency
- User action events
- Friction signals

### 4. Reporting Flow
```
Frontend → Reporting Service → Analytics Store → PDF Generation → Delivery
```

**Telemetry Capture Points:**
- Report generation time
- PDF size
- Delivery success rate
- User satisfaction (NPS)

## Key Telemetry Metrics

### User KPIs
- **Time to First Value**: Time from signup to first report/campaign
- **Campaign Renewal Rate**: % of campaigns renewed within 90 days
- **Report Generation Rate**: % of campaigns with reports generated
- **Attribution Setup Completion**: % of campaigns with attribution configured
- **Support Request Rate**: Support tickets per user
- **Feature Adoption Rate**: % of users using each feature
- **NPS Score**: Net Promoter Score
- **Time to Complete Tasks**: Time to complete key workflows

### Operational Telemetry
- **Service Uptime**: Availability percentage per service
- **Latency Percentiles**: p50, p95, p99 response times
- **Error Rates**: Errors per service per time period
- **Throughput**: Requests per second
- **Queue Depth**: Background task queue sizes
- **Database Performance**: Query times, connection pool usage
- **Cache Performance**: Hit rates, eviction rates

### Support Flow Metrics
- **Support Ticket Volume**: Tickets per day/week
- **Resolution Time**: Average time to resolve tickets
- **First Response Time**: Time to first response
- **Ticket Categories**: Distribution by issue type
- **Self-Service Success Rate**: % resolved without support
- **Friction Detection**: Confusion signals per page/feature

## Technology Stack

### Backend
- **Language**: Python 3.11+ (FastAPI), TypeScript/Node.js
- **API Framework**: FastAPI, Express.js
- **Database**: PostgreSQL (relational), InfluxDB/TimescaleDB (time-series)
- **Cache**: Redis
- **Message Queue**: RabbitMQ/Apache Kafka
- **Background Jobs**: Celery, Bull Queue

### Frontend
- **Framework**: Next.js (React)
- **State Management**: Zustand/Redux
- **UI Library**: Tailwind CSS, shadcn/ui
- **Analytics**: PostHog/Mixpanel (client-side)

### Infrastructure
- **Containerization**: Docker, Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger
- **Alerting**: Alertmanager, PagerDuty

### Third-Party Services
- **PDF Generation**: Puppeteer/Playwright
- **Email**: SendGrid/AWS SES
- **File Storage**: AWS S3/Cloudflare R2
- **CDN**: Cloudflare

## Security Considerations

- **Authentication**: OAuth 2.0, JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: TLS in transit, encryption at rest
- **API Security**: Rate limiting, input validation, CORS
- **Audit Logging**: All sensitive operations logged
- **Data Privacy**: GDPR compliance, data retention policies

## Scalability Considerations

- **Horizontal Scaling**: Stateless API services
- **Database Scaling**: Read replicas, connection pooling
- **Caching Strategy**: Multi-layer caching (Redis, CDN)
- **Queue Processing**: Distributed task queues
- **CDN**: Static asset delivery
- **Load Balancing**: Round-robin, least connections

## Disaster Recovery

- **Backups**: Daily database backups, point-in-time recovery
- **Replication**: Multi-region database replication
- **Failover**: Automated failover for critical services
- **Monitoring**: 24/7 monitoring and alerting

## Data Contracts

### Ingestion Data Contracts

**RSS Feed Data Contract**
```json
{
  "feed_url": "string (required, validated URL)",
  "podcast_id": "string (required, UUID)",
  "episode_id": "string (required, UUID)",
  "title": "string (required, max 500 chars)",
  "description": "string (optional, max 5000 chars)",
  "published_at": "datetime (required, ISO 8601)",
  "duration_seconds": "integer (optional, >= 0)",
  "audio_url": "string (required, validated URL)",
  "metadata": {
    "author": "string (optional)",
    "category": "string (optional)",
    "tags": "array[string] (optional)"
  }
}
```

**Platform API Data Contract (Apple Podcasts)**
```json
{
  "platform": "apple_podcasts",
  "podcast_id": "string (required)",
  "episode_id": "string (required)",
  "downloads": "integer (required, >= 0)",
  "listeners": "integer (required, >= 0)",
  "completion_rate": "float (optional, 0.0-1.0)",
  "date_range": {
    "start_date": "datetime (required)",
    "end_date": "datetime (required)"
  },
  "demographics": {
    "countries": "object (country_code: count)",
    "devices": "object (device_type: count)",
    "age_groups": "object (age_group: count)"
  }
}
```

**Attribution Event Data Contract**
```json
{
  "event_id": "string (required, UUID)",
  "campaign_id": "string (required, UUID)",
  "podcast_id": "string (required, UUID)",
  "episode_id": "string (optional, UUID)",
  "timestamp": "datetime (required, ISO 8601)",
  "attribution_method": "enum (required: promo_code, pixel, utm, direct)",
  "attribution_data": {
    "promo_code": "string (optional)",
    "utm_source": "string (optional)",
    "utm_medium": "string (optional)",
    "utm_campaign": "string (optional)",
    "pixel_id": "string (optional)"
  },
  "conversion_data": {
    "conversion_type": "string (optional: purchase, signup, download)",
    "conversion_value": "float (optional, >= 0)",
    "user_id": "string (optional)",
    "session_id": "string (optional)"
  }
}
```

### API Data Contracts

**Campaign Performance Response Contract**
```json
{
  "campaign_id": "string (required, UUID)",
  "podcast_id": "string (required, UUID)",
  "start_date": "datetime (required)",
  "end_date": "datetime (required)",
  "metrics": {
    "total_downloads": "integer (required, >= 0)",
    "total_streams": "integer (required, >= 0)",
    "total_listeners": "integer (required, >= 0)",
    "attribution_events": "integer (required, >= 0)",
    "conversions": "integer (required, >= 0)",
    "conversion_value": "float (required, >= 0)",
    "roi": "float (optional)",
    "roas": "float (optional)"
  },
  "data_quality": {
    "completeness": "float (required, 0.0-1.0)",
    "accuracy": "float (required, 0.0-1.0)",
    "freshness_hours": "float (required, >= 0)"
  },
  "timestamp": "datetime (required)"
}
```

**Report Generation Request Contract**
```json
{
  "campaign_id": "string (required, UUID)",
  "report_template": "string (required, enum: standard, executive, detailed)",
  "date_range": {
    "start_date": "datetime (required)",
    "end_date": "datetime (required)"
  },
  "customization": {
    "include_roi": "boolean (default: true)",
    "include_benchmarks": "boolean (default: true)",
    "branding": {
      "logo_url": "string (optional)",
      "primary_color": "string (optional, hex)",
      "company_name": "string (optional)"
    }
  },
  "format": "enum (required: pdf, html, json)"
}
```

### Data Quality Contracts

**Data Completeness Requirements**
- **Campaign Data:** 100% of campaigns must have: campaign_id, podcast_id, start_date, end_date
- **Attribution Data:** 95%+ of campaigns must have attribution configured
- **Performance Data:** 90%+ of campaigns must have complete metrics (downloads, streams, listeners)
- **ROI Data:** 85%+ of campaigns must have ROI calculations (if conversion data available)

**Data Accuracy Requirements**
- **Attribution Accuracy:** 95%+ validated accuracy (test campaigns)
- **ROI Calculation Accuracy:** 98%+ validated accuracy (manual verification)
- **Metric Accuracy:** 99%+ accuracy vs. source platforms (cross-validation)

**Data Freshness Requirements**
- **Real-time Data:** <1 hour latency from event to availability
- **Daily Aggregates:** Available by 2 AM UTC next day
- **Historical Data:** Available within 24 hours of request

## Service Level Agreements (SLAs)

### Availability SLAs

**System Uptime**
- **Target:** 99.9% uptime (43 minutes downtime/month)
- **Measurement:** (Total Time - Downtime) / Total Time
- **Exclusions:** Scheduled maintenance (with 48h notice), force majeure
- **Remediation:** Service credits for violations (10% credit per 0.1% below target)

**API Uptime**
- **Target:** 99.95% uptime (22 minutes downtime/month)
- **Measurement:** API endpoint availability monitoring
- **Endpoints:** All REST API endpoints
- **Remediation:** Service credits for violations (10% credit per 0.05% below target)

**Data Ingestion Uptime**
- **Target:** 99.9% uptime
- **Measurement:** Successful ingestion rate
- **Remediation:** Automatic retry, manual intervention if needed

### Performance SLAs

**API Response Time**
- **Target:** p50 <200ms, p95 <500ms, p99 <1s
- **Measurement:** Response time percentiles across all endpoints
- **Exclusions:** Large data exports, bulk operations
- **Remediation:** Performance optimization, caching improvements

**Report Generation Time**
- **Target:** p50 <5s, p95 <30s, p99 <60s
- **Measurement:** Time from request to PDF availability
- **Exclusions:** Reports with >1 year of data
- **Remediation:** Optimization, queue prioritization

**Data Processing Latency**
- **Target:** <1 hour from event to data availability
- **Measurement:** Timestamp difference (event - availability)
- **Remediation:** Processing optimization, parallel processing

### Data Quality SLAs

**Attribution Accuracy**
- **Target:** 95%+ accuracy (validated)
- **Measurement:** Test campaigns, manual verification
- **Remediation:** Attribution model improvements, validation enhancements

**Data Completeness**
- **Target:** 90%+ of campaigns have complete data
- **Measurement:** % of campaigns with all required metrics
- **Remediation:** Data pipeline improvements, error handling

**ROI Calculation Accuracy**
- **Target:** 98%+ accuracy (validated)
- **Measurement:** Manual verification, comparison to ground truth
- **Remediation:** Calculation improvements, validation enhancements

### Support SLAs

**First Response Time**
- **Target:** <4 hours (business hours), <24 hours (after hours)
- **Measurement:** Time from ticket creation to first response
- **Remediation:** Support team scaling, automation

**Resolution Time**
- **Target:** <24 hours (p50), <48 hours (p95)
- **Measurement:** Time from ticket creation to resolution
- **Remediation:** Knowledge base improvements, self-service tools

**Critical Issue Resolution**
- **Target:** <2 hours response, <8 hours resolution
- **Definition:** System downtime, data loss, security issues
- **Remediation:** On-call rotation, escalation procedures

## Telemetry Specifications

### Telemetry Collection Points

**Application Telemetry (Prometheus)**
- **Metrics Type:** Counters, Gauges, Histograms
- **Collection Frequency:** Every 15 seconds
- **Retention:** 30 days (raw), 1 year (aggregated)

**Key Application Metrics:**
```yaml
# API Metrics
api_requests_total{method, endpoint, status_code}
api_request_duration_seconds{method, endpoint, quantile="0.5|0.95|0.99"}
api_errors_total{method, endpoint, error_type}

# Business Metrics
campaigns_created_total{persona, plan_tier}
reports_generated_total{persona, template_type}
attribution_events_total{campaign_id, method}

# User Metrics
users_active_total{persona, plan_tier}
time_to_first_value_seconds{persona, quantile="0.5|0.9|0.95"}
feature_adoption_total{feature_name, persona}
```

**Infrastructure Telemetry (Prometheus + Node Exporter)**
- **Metrics Type:** System metrics (CPU, memory, disk, network)
- **Collection Frequency:** Every 15 seconds
- **Retention:** 30 days

**Key Infrastructure Metrics:**
```yaml
# System Metrics
cpu_usage_percent{host, service}
memory_usage_bytes{host, service}
disk_usage_bytes{host, mountpoint}
network_bytes_total{host, interface, direction}

# Database Metrics
db_connections_active{db_name}
db_query_duration_seconds{db_name, query_type, quantile="0.5|0.95|0.99"}
db_errors_total{db_name, error_type}

# Cache Metrics
cache_hits_total{cache_name}
cache_misses_total{cache_name}
cache_size_bytes{cache_name}

# Queue Metrics
queue_depth{queue_name}
queue_processing_duration_seconds{queue_name, quantile="0.5|0.95|0.99"}
queue_errors_total{queue_name, error_type}
```

**Event Telemetry (Event Logger)**
- **Metrics Type:** User events, business events, system events
- **Collection Frequency:** Real-time (async)
- **Retention:** 90 days (raw), 1 year (aggregated)

**Key Event Types:**
```yaml
# User Events
user_signed_up{user_id, persona, acquisition_channel}
user_logged_in{user_id, persona}
feature_used{user_id, feature_name, persona}
report_generated{user_id, campaign_id, template_type}
campaign_created{user_id, campaign_id, persona}

# Business Events
campaign_started{campaign_id, podcast_id}
campaign_ended{campaign_id, podcast_id}
attribution_event{event_id, campaign_id, method}
conversion_event{event_id, campaign_id, conversion_type, value}

# System Events
data_ingested{source, record_count, latency_ms}
data_processed{source, record_count, latency_ms}
error_occurred{error_type, service, severity}
```

**Distributed Tracing (Jaeger)**
- **Trace Collection:** All API requests, background jobs
- **Sampling Rate:** 100% for errors, 10% for successful requests
- **Retention:** 7 days

**Trace Spans:**
- API request spans (method, endpoint, duration, status)
- Database query spans (query, duration, result)
- External API call spans (service, endpoint, duration, status)
- Background job spans (job_type, duration, status)

### Telemetry Dashboard (Grafana)

**Real-Time Dashboard**
- **Refresh Rate:** 30 seconds
- **Sections:**
  1. System Health (uptime, error rates, latency)
  2. API Performance (requests/sec, latency, errors)
  3. Business Metrics (campaigns, reports, users)
  4. Infrastructure (CPU, memory, disk, network)
  5. Alerts (active alerts, recent incidents)

**Operational Dashboard**
- **Refresh Rate:** 1 minute
- **Sections:**
  1. Service Health (all services, uptime, errors)
  2. Database Performance (queries, connections, latency)
  3. Queue Performance (depth, processing time, errors)
  4. Cache Performance (hits, misses, eviction)
  5. Data Pipeline (ingestion rate, processing latency, errors)

**Business Dashboard**
- **Refresh Rate:** 5 minutes
- **Sections:**
  1. User Metrics (MAU, WAU, activation, retention)
  2. Campaign Metrics (created, active, completed, renewal rate)
  3. Report Metrics (generated, generation time, satisfaction)
  4. Attribution Metrics (events, accuracy, coverage)
  5. Financial Metrics (LTV, CAC, revenue)

### Alerting Rules

**Critical Alerts (PagerDuty)**
- System downtime (>5 minutes)
- API error rate >1%
- Database connection failures
- Data ingestion failures (>10% failure rate)
- Security incidents

**Warning Alerts (Email/Slack)**
- API latency p95 >1s
- Error rate >0.5%
- Queue depth >1000
- Disk usage >80%
- Memory usage >85%

**Info Alerts (Slack)**
- High traffic (>2x normal)
- Feature adoption milestones
- Business metric thresholds

### Telemetry Data Retention

**Raw Metrics:** 30 days
**Aggregated Metrics:** 1 year (daily aggregates)
**Events:** 90 days (raw), 1 year (aggregated)
**Traces:** 7 days
**Logs:** 30 days (hot), 90 days (cold)

---

*Last Updated: [Current Date]*
*Version: 2.0*

# Sprint Metrics Definitions

**Last Updated**: 2024-11-13  
**Sprint Goal**: Validate core product loop and measure success metrics

---

## PRIMARY SPRINT METRICS

### 1. Time to First Value (TTFV)

**Definition**: Time from user signup (`user.registered` event) to first campaign created (`campaign.created` event).

**Calculation**:
```
TTFV = campaign.created.timestamp - user.registered.timestamp
```

**Target**: <15 minutes for 80% of users

**How to Measure**:
1. Track `user.registered` event with timestamp in `src/api/auth.py`
2. Track `campaign.created` event with timestamp in `src/api/campaigns.py`
3. Calculate TTFV in analytics store: `src/analytics/analytics_store.py`
4. Store TTFV per user in database or metrics system
5. Query TTFV distribution (histogram) for dashboard

**Decision It Informs**:
- If TTFV >15 minutes: Onboarding is too complex, simplify campaign creation
- If TTFV <5 minutes: Users may not understand the product, add guidance
- If TTFV varies widely: Identify user segments with different experiences

**Files to Instrument**:
- `src/api/auth.py` - Log `user.registered` event
- `src/api/campaigns.py` - Log `campaign.created` event
- `src/analytics/analytics_store.py` - Calculate and store TTFV

---

### 2. Campaign Completion Rate

**Definition**: Percentage of campaigns that progress from "created" to "completed" (with report generated).

**Calculation**:
```
Completion Rate = (campaigns with status='completed') / (total campaigns created) * 100
```

**Target**: >70%

**How to Measure**:
1. Track campaign status changes:
   - `campaign.created` → status = 'created'
   - `report.generated` → status = 'completed'
2. Calculate completion rate:
   - Count campaigns with status='completed'
   - Divide by total campaigns created
   - Store in analytics store
3. Query completion rate for dashboard

**Decision It Informs**:
- If completion rate <70%: Users are dropping off, identify drop-off point
- If completion rate varies by user segment: Different experiences for different users
- If completion rate improves over time: Product is getting better

**Files to Instrument**:
- `src/api/campaigns.py` - Track campaign status changes
- `src/api/reports.py` - Update campaign status to 'completed' when report generated
- `src/analytics/analytics_store.py` - Calculate completion rate

---

### 3. Attribution Event Processing Latency

**Definition**: Time from attribution event recorded to visible in analytics dashboard.

**Calculation**:
```
Latency = analytics_query.timestamp - attribution_event.timestamp
```

**Target**: <5 seconds (p95)

**How to Measure**:
1. Track timestamp when attribution event is recorded in `src/api/attribution.py`
2. Track timestamp when event appears in analytics query
3. Calculate difference
4. Store latency metric in telemetry system
5. Query latency distribution (p50, p95, p99) for dashboard

**Decision It Informs**:
- If latency >5 seconds: Attribution tracking is too slow, optimize processing
- If latency varies by event type: Some events are slower, optimize those
- If latency improves over time: System is getting faster

**Files to Instrument**:
- `src/api/attribution.py` - Track event recording timestamp
- `src/analytics/analytics_store.py` - Track query timestamp
- `src/telemetry/metrics.py` - Store latency metric

---

## SECONDARY METRICS

### 4. Campaign Creation Rate

**Definition**: Number of campaigns created per day/week/month.

**Target**: Track growth over time

**How to Measure**:
- Count `campaign.created` events by time period
- Query from event log or analytics store

**Files**: `src/api/campaigns.py`, `src/telemetry/events.py`

---

### 5. Report Generation Rate

**Definition**: Number of reports generated per day/week/month.

**Target**: Track growth over time

**How to Measure**:
- Count `report.generated` events by time period
- Query from event log or analytics store

**Files**: `src/api/reports.py`, `src/telemetry/events.py`

---

### 6. API Error Rate

**Definition**: Percentage of API requests that return error status codes (4xx, 5xx).

**Target**: <2%

**How to Measure**:
- Count API errors by endpoint and status code
- Divide by total API requests
- Query from metrics collector

**Files**: `src/telemetry/metrics.py`, `src/main.py` (middleware)

---

### 7. Attribution Event Data Loss Rate

**Definition**: Percentage of attribution events that are recorded but don't appear in analytics.

**Target**: <5%

**How to Measure**:
- Count attribution events recorded
- Count attribution events in analytics queries
- Calculate difference
- Store data loss rate metric

**Files**: `src/api/attribution.py`, `src/analytics/analytics_store.py`

---

## DASHBOARD METRICS

### Sprint Metrics Dashboard (`frontend/app/admin/sprint-metrics/page.tsx`)

**Metrics to Display**:

1. **TTFV Distribution**
   - Histogram showing TTFV distribution
   - Percentiles: p50, p75, p95, p99
   - Target line: 15 minutes

2. **Campaign Completion Rate**
   - Gauge showing completion rate percentage
   - Target line: 70%
   - Trend over time

3. **Error Rate**
   - Line chart showing error rate over time
   - Target line: 2%
   - Breakdown by endpoint

4. **Attribution Event Processing Latency**
   - Line chart showing latency over time
   - Target line: 5 seconds
   - Percentiles: p50, p95, p99

5. **Campaign Creation Rate**
   - Line chart showing campaigns created over time
   - Growth trend

6. **Report Generation Rate**
   - Line chart showing reports generated over time
   - Growth trend

---

## METRICS STORAGE

### Where Metrics Are Stored

1. **Event Logs**: `src/telemetry/events.py`
   - Raw events with timestamps
   - Queryable via event log API

2. **Analytics Store**: `src/analytics/analytics_store.py`
   - Aggregated metrics
   - Time-series data in TimescaleDB

3. **Metrics Collector**: `src/telemetry/metrics.py`
   - Prometheus-compatible metrics
   - Counters, histograms, gauges

4. **Database**: PostgreSQL/TimescaleDB
   - User TTFV per user
   - Campaign completion status
   - Attribution event timestamps

---

## METRICS QUERIES

### Example Queries

**TTFV Distribution**:
```sql
SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttfv_seconds) as p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ttfv_seconds) as p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ttfv_seconds) as p99
FROM user_ttfv
WHERE created_at >= NOW() - INTERVAL '30 days';
```

**Campaign Completion Rate**:
```sql
SELECT 
    COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as completion_rate
FROM campaigns
WHERE created_at >= NOW() - INTERVAL '30 days';
```

**Attribution Event Processing Latency**:
```sql
SELECT 
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_latency_ms) as p95_latency_ms
FROM attribution_events
WHERE created_at >= NOW() - INTERVAL '24 hours';
```

---

## METRICS ALERTS

### Alert Thresholds

1. **TTFV >20 minutes** (p95)
   - Alert: High TTFV detected
   - Action: Investigate onboarding flow

2. **Completion Rate <60%**
   - Alert: Low completion rate
   - Action: Identify drop-off point

3. **Error Rate >5%**
   - Alert: High error rate
   - Action: Investigate errors

4. **Attribution Latency >10 seconds** (p95)
   - Alert: Slow attribution processing
   - Action: Optimize event processing

---

*Last Updated: 2024-11-13*

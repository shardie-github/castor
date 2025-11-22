# API Documentation

## Base URL
```
https://api.example.com/api/v1
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Campaigns

#### List Campaigns
```
GET /campaigns
```

Returns a list of campaigns for the authenticated user.

**Response:**
```json
[
  {
    "campaign_id": "uuid",
    "podcast_id": "uuid",
    "sponsor_id": "uuid",
    "name": "Campaign Name",
    "status": "active",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "campaign_value": 5000.0
  }
]
```

#### Get Campaign Analytics
```
GET /campaigns/{campaign_id}/analytics
```

Returns analytics data for a specific campaign.

**Response:**
```json
{
  "campaign_id": "uuid",
  "impressions": 10000,
  "clicks": 500,
  "conversions": 50,
  "revenue": 10000.0,
  "roi": 1.0,
  "total_downloads": 5000,
  "total_streams": 8000,
  "total_listeners": 3000,
  "attribution_events": 500
}
```

### Attribution Events

#### Get Attribution Events
```
GET /attribution/events/{campaign_id}?limit=100&offset=0
```

Returns attribution events for a campaign.

**Query Parameters:**
- `limit` (optional): Number of events to return (default: 100)
- `offset` (optional): Number of events to skip (default: 0)

**Response:**
```json
[
  {
    "event_id": "uuid",
    "campaign_id": "uuid",
    "event_type": "impression|click|conversion",
    "timestamp": "2024-01-01T12:00:00Z",
    "promo_code": "PODCAST2024",
    "conversion_type": "purchase",
    "conversion_value": 100.0,
    "attribution_method": "promo_code",
    "page_url": "https://example.com/product",
    "referrer": "https://podcast.com",
    "utm_source": "podcast",
    "utm_medium": "audio",
    "utm_campaign": "campaign_name"
  }
]
```

#### Record Attribution Event
```
POST /attribution/events
```

Records a new attribution event from the tracking pixel.

**Request Body:**
```json
{
  "campaign_id": "uuid",
  "event_type": "impression|click|conversion",
  "timestamp": "2024-01-01T12:00:00Z",
  "promo_code": "PODCAST2024",
  "conversion_type": "purchase",
  "conversion_value": 100.0,
  "page_url": "https://example.com/product",
  "referrer": "https://podcast.com",
  "utm_source": "podcast",
  "utm_medium": "audio",
  "utm_campaign": "campaign_name"
}
```

### Reports

#### Generate Report
```
POST /reports/generate
```

Generates a new report for a campaign.

**Request Body:**
```json
{
  "campaign_id": "uuid",
  "report_type": "sponsor_report|performance_summary|roi_report",
  "format": "pdf|csv|excel",
  "template_id": "basic_sponsor",
  "include_roi": true,
  "include_attribution": true,
  "include_benchmarks": false,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z"
}
```

**Response:**
```json
{
  "report_id": "uuid",
  "campaign_id": "uuid",
  "template_id": "basic_sponsor",
  "report_type": "sponsor_report",
  "format": "pdf",
  "generated_at": "2024-01-15T10:00:00Z",
  "file_size_bytes": 51200,
  "file_url": "/api/v1/reports/filename.pdf",
  "includes_roi": true,
  "includes_attribution": true
}
```

#### List Reports
```
GET /reports?campaign_id={campaign_id}
```

Returns a list of reports for the authenticated user.

**Query Parameters:**
- `campaign_id` (optional): Filter by campaign ID

**Response:**
```json
[
  {
    "report_id": "uuid",
    "campaign_id": "uuid",
    "template_id": "basic_sponsor",
    "report_type": "sponsor_report",
    "format": "pdf",
    "generated_at": "2024-01-15T10:00:00Z",
    "file_size_bytes": 51200,
    "file_url": "/api/v1/reports/filename.pdf",
    "includes_roi": true,
    "includes_attribution": true
  }
]
```

#### Download Report
```
GET /reports/{report_id}/download
```

Downloads a generated report file.

**Response:** File download (PDF, CSV, or Excel)

### Sprint Metrics

#### Get Sprint Metrics Dashboard
```
GET /sprint-metrics/dashboard?start_date=2024-01-01&end_date=2024-01-31
```

Returns sprint metrics dashboard data (admin only).

**Response:**
```json
{
  "ttfv_distribution": {
    "p50": 3600.0,
    "p75": 7200.0,
    "p95": 14400.0,
    "mean": 5400.0,
    "count": 100
  },
  "completion_rate": {
    "rate": 0.75,
    "total_campaigns": 100,
    "completed_campaigns": 75
  },
  "error_rate": null,
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### Analytics

#### Get Dashboard Analytics
```
GET /analytics/dashboard
```

Returns dashboard analytics summary for the authenticated user.

**Response:**
```json
{
  "total_campaigns": 10,
  "active_campaigns": 5,
  "total_revenue": 50000.0,
  "total_conversions": 500,
  "average_roi": 1.5,
  "recent_performance": [
    {
      "campaign_id": "uuid",
      "conversions": 50,
      "revenue": 5000.0,
      "roi": 1.0
    }
  ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "campaign_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API requests are rate-limited:
- 100 requests per minute per user
- 1000 requests per hour per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## Pagination

Endpoints that return lists support pagination via query parameters:
- `limit`: Number of items per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

## Webhooks

Webhooks can be configured to receive events:
- `campaign.created`
- `campaign.completed`
- `report.generated`
- `attribution.conversion`

See `/settings/webhooks` for webhook configuration.

# API Documentation

Complete API reference for the Podcast Analytics & Sponsorship Platform.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.castor.app`

## Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### Health & Status

#### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Connection successful",
      "latency_ms": 5
    }
  ]
}
```

#### GET `/metrics`

Prometheus metrics endpoint.

**Response:** Prometheus metrics format

---

### Multi-Tenant Management

#### GET `/api/v1/tenants`

List all tenants (admin only).

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)

**Response:**
```json
{
  "tenants": [
    {
      "tenant_id": "uuid",
      "name": "Example Tenant",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

#### POST `/api/v1/tenants`

Create a new tenant.

**Request Body:**
```json
{
  "name": "New Tenant",
  "metadata": {}
}
```

**Response:**
```json
{
  "tenant_id": "uuid",
  "name": "New Tenant",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### Attribution Tracking

#### GET `/api/v1/attribution/events`

Get attribution events.

**Query Parameters:**
- `campaign_id` (uuid): Filter by campaign
- `start_date` (datetime): Start date filter
- `end_date` (datetime): End date filter
- `page` (int): Page number
- `limit` (int): Items per page

**Response:**
```json
{
  "events": [
    {
      "event_id": "uuid",
      "campaign_id": "uuid",
      "timestamp": "2024-01-15T10:00:00Z",
      "attribution_method": "promo_code",
      "conversion_value": 99.99
    }
  ],
  "total": 1000,
  "page": 1,
  "limit": 20
}
```

#### POST `/api/v1/attribution/events`

Create an attribution event.

**Request Body:**
```json
{
  "campaign_id": "uuid",
  "attribution_method": "promo_code",
  "attribution_data": {
    "promo_code": "PODCAST2024"
  },
  "conversion_data": {
    "conversion_type": "purchase",
    "conversion_value": 99.99
  }
}
```

**Response:**
```json
{
  "event_id": "uuid",
  "status": "created"
}
```

#### GET `/api/v1/attribution/roi/{campaign_id}`

Calculate ROI for a campaign.

**Response:**
```json
{
  "campaign_id": "uuid",
  "total_investment": 5000.00,
  "total_revenue": 15000.00,
  "roi": 200.00,
  "roi_percentage": 200.0,
  "attribution_count": 150,
  "average_order_value": 100.00
}
```

---

### AI Features

#### POST `/api/v1/ai/analyze-content`

Analyze podcast content.

**Request Body:**
```json
{
  "episode_id": "uuid",
  "analysis_type": "sentiment|topics|keywords"
}
```

**Response:**
```json
{
  "episode_id": "uuid",
  "analysis": {
    "sentiment": "positive",
    "topics": ["technology", "business"],
    "keywords": ["AI", "machine learning"]
  }
}
```

#### POST `/api/v1/ai/generate-recommendations`

Generate content recommendations.

**Request Body:**
```json
{
  "podcast_id": "uuid",
  "recommendation_type": "sponsors|topics|guests"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "sponsor",
      "name": "Example Sponsor",
      "match_score": 0.95,
      "reason": "High audience overlap"
    }
  ]
}
```

---

### Security

#### POST `/api/v1/security/auth/login`

Authenticate user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "user"
  }
}
```

#### POST `/api/v1/security/auth/refresh`

Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "refresh-token"
}
```

**Response:**
```json
{
  "access_token": "new-jwt-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Cost Tracking

#### GET `/api/v1/cost/tracking`

Get cost tracking data.

**Query Parameters:**
- `start_date` (datetime): Start date
- `end_date` (datetime): End date
- `category` (string): Cost category

**Response:**
```json
{
  "costs": [
    {
      "date": "2024-01-15",
      "category": "infrastructure",
      "amount": 1000.00,
      "currency": "USD"
    }
  ],
  "total": 5000.00,
  "period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

---

### Optimization

#### GET `/api/v1/optimization/churn-prediction`

Get churn prediction scores.

**Response:**
```json
{
  "predictions": [
    {
      "user_id": "uuid",
      "churn_probability": 0.75,
      "risk_level": "high",
      "factors": ["low_engagement", "no_recent_activity"]
    }
  ]
}
```

#### POST `/api/v1/optimization/ab-test`

Create an A/B test.

**Request Body:**
```json
{
  "name": "Homepage CTA Test",
  "variants": [
    {"name": "control", "traffic_percentage": 50},
    {"name": "variant_a", "traffic_percentage": 50}
  ],
  "metrics": ["conversion_rate", "click_through_rate"]
}
```

**Response:**
```json
{
  "test_id": "uuid",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

API requests are rate-limited:

- **Per minute**: 60 requests
- **Per hour**: 1000 requests
- **Per day**: 10000 requests

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 1000,
  "page": 1,
  "limit": 20,
  "pages": 50
}
```

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: `/api/docs`
- **ReDoc**: `/api/redoc`
- **OpenAPI JSON**: `/api/openapi.json`

---

## SDKs & Client Libraries

### Python

```python
from castor_sdk import CastorClient

client = CastorClient(api_key="your-api-key")
events = client.attribution.get_events(campaign_id="uuid")
```

### JavaScript/TypeScript

```typescript
import { CastorClient } from '@castor/sdk'

const client = new CastorClient({ apiKey: 'your-api-key' })
const events = await client.attribution.getEvents({ campaignId: 'uuid' })
```

---

*Last Updated: 2024-01-15*
*API Version: 1.0.0*

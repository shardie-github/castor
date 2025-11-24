# API Documentation

**Last Updated:** 2024-12  
**API Version:** v1  
**Base URL:** `https://api.castor.app/api/v1` (production) or `http://localhost:8000/api/v1` (local)

---

## Overview

The Podcast Analytics & Sponsorship Platform API is a RESTful API built with FastAPI. All endpoints return JSON and follow standard HTTP status codes.

### Authentication

Most endpoints require authentication via JWT Bearer tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-access-token>
```

### Base Endpoints

- **Production:** `https://api.castor.app/api/v1`
- **Staging:** `https://api-staging.castor.app/api/v1`
- **Local:** `http://localhost:8000/api/v1`

### OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `/api/docs`
- **ReDoc:** `/api/redoc`
- **OpenAPI JSON:** `/api/openapi.json`

---

## Core Endpoints

### Health & Status

#### `GET /health`

Health check endpoint with comprehensive system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T12:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Connection successful",
      "latency_ms": 5
    },
    {
      "name": "redis",
      "status": "healthy",
      "message": "Connection successful",
      "latency_ms": 2
    }
  ]
}
```

**Status Codes:**
- `200` - Healthy or degraded
- `503` - Unhealthy

#### `GET /metrics`

Prometheus metrics endpoint.

**Response:** Prometheus metrics format

---

## Authentication Endpoints

### `POST /api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "accept_terms": true,
  "accept_privacy": true
}
```

**Response:** `201 Created`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": false
}
```

**Validation:**
- Password: Minimum 8 characters, must contain uppercase, lowercase, and number
- Email: Valid email format
- Terms and privacy acceptance required

### `POST /api/v1/auth/login`

Login and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `POST /api/v1/auth/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh-token"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "new-jwt-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `GET /api/v1/auth/me`

Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": true,
  "created_at": "2024-12-01T12:00:00Z"
}
```

### `POST /api/v1/auth/logout`

Logout and invalidate tokens.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

---

## Podcasts Endpoints

### `GET /api/v1/podcasts`

List all podcasts for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "My Podcast",
    "description": "Podcast description",
    "rss_feed_url": "https://example.com/feed.xml",
    "website_url": "https://example.com",
    "created_at": "2024-12-01T12:00:00Z"
  }
]
```

### `POST /api/v1/podcasts`

Create a new podcast.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "My Podcast",
  "description": "Podcast description",
  "rss_feed_url": "https://example.com/feed.xml",
  "website_url": "https://example.com"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "My Podcast",
  "description": "Podcast description",
  "rss_feed_url": "https://example.com/feed.xml",
  "website_url": "https://example.com",
  "created_at": "2024-12-01T12:00:00Z"
}
```

### `GET /api/v1/podcasts/{podcast_id}`

Get podcast details.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "My Podcast",
  "description": "Podcast description",
  "rss_feed_url": "https://example.com/feed.xml",
  "website_url": "https://example.com",
  "created_at": "2024-12-01T12:00:00Z",
  "updated_at": "2024-12-01T12:00:00Z"
}
```

### `PUT /api/v1/podcasts/{podcast_id}`

Update podcast.

**Headers:** `Authorization: Bearer <token>`

**Request Body:** (all fields optional)
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "rss_feed_url": "https://example.com/new-feed.xml",
  "website_url": "https://example.com/new"
}
```

**Response:** `200 OK` (updated podcast object)

### `DELETE /api/v1/podcasts/{podcast_id}`

Delete podcast.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

---

## Episodes Endpoints

### `GET /api/v1/episodes`

List episodes for a podcast.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `podcast_id` (required): Podcast UUID
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "podcast_id": "uuid",
    "title": "Episode Title",
    "description": "Episode description",
    "published_at": "2024-12-01T12:00:00Z",
    "duration_seconds": 3600,
    "audio_url": "https://example.com/episode.mp3"
  }
]
```

### `POST /api/v1/episodes`

Create a new episode.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "podcast_id": "uuid",
  "title": "Episode Title",
  "description": "Episode description",
  "published_at": "2024-12-01T12:00:00Z",
  "duration_seconds": 3600,
  "audio_url": "https://example.com/episode.mp3"
}
```

**Response:** `201 Created` (episode object)

---

## Campaigns Endpoints

### `GET /api/v1/campaigns`

List all campaigns.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `paused`, `completed`)
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Campaign Name",
    "status": "active",
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "budget": 10000.00,
    "spent": 5000.00
  }
]
```

### `POST /api/v1/campaigns`

Create a new campaign.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Campaign Name",
  "start_date": "2024-12-01",
  "end_date": "2024-12-31",
  "budget": 10000.00,
  "target_audience": "tech-savvy professionals"
}
```

**Response:** `201 Created` (campaign object)

---

## Analytics Endpoints

### `GET /api/v1/analytics/listener-events`

Get listener events for time-series analysis.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `podcast_id` (optional): Filter by podcast
- `episode_id` (optional): Filter by episode
- `start_date` (required): ISO 8601 date
- `end_date` (required): ISO 8601 date
- `granularity` (optional): `hour`, `day`, `week`, `month` (default: `day`)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "timestamp": "2024-12-01T00:00:00Z",
      "listeners": 150,
      "plays": 200,
      "completions": 120
    }
  ],
  "summary": {
    "total_listeners": 150,
    "total_plays": 200,
    "completion_rate": 0.6
  }
}
```

### `GET /api/v1/analytics/attribution`

Get attribution analytics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `campaign_id` (required): Campaign UUID
- `start_date` (required): ISO 8601 date
- `end_date` (required): ISO 8601 date

**Response:** `200 OK`
```json
{
  "campaign_id": "uuid",
  "impressions": 10000,
  "clicks": 500,
  "conversions": 50,
  "roi": 2.5,
  "attribution_events": [...]
}
```

---

## Sponsors Endpoints

### `GET /api/v1/sponsors`

List all sponsors.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Sponsor Name",
    "company": "Company Name",
    "email": "sponsor@example.com",
    "created_at": "2024-12-01T12:00:00Z"
  }
]
```

### `POST /api/v1/sponsors`

Create a new sponsor.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Sponsor Name",
  "company": "Company Name",
  "email": "sponsor@example.com",
  "phone": "+1234567890"
}
```

**Response:** `201 Created` (sponsor object)

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field": "field_name" // Optional, for validation errors
}
```

### Common Status Codes

- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unavailable

### Rate Limiting

Rate limits are applied per API key/user:
- **Default:** 60 requests per minute
- **Authenticated:** 1000 requests per hour
- **Headers:** Rate limit info is included in response headers:
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

---

## Webhooks

Webhooks are available for real-time event notifications. Configure webhook URLs in the dashboard.

**Supported Events:**
- `campaign.created`
- `campaign.updated`
- `episode.published`
- `attribution.event`
- `sponsor.created`

**Webhook Payload:**
```json
{
  "event": "campaign.created",
  "timestamp": "2024-12-01T12:00:00Z",
  "data": {
    "campaign_id": "uuid",
    "name": "Campaign Name"
  }
}
```

---

## SDKs & Client Libraries

### Python

```python
import httpx

client = httpx.Client(
    base_url="https://api.castor.app/api/v1",
    headers={"Authorization": f"Bearer {token}"}
)

response = client.get("/podcasts")
podcasts = response.json()
```

### JavaScript/TypeScript

```typescript
const response = await fetch('https://api.castor.app/api/v1/podcasts', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const podcasts = await response.json();
```

---

## Changelog

### v1.0.0 (2024-12)
- Initial API release
- Authentication endpoints
- Podcasts, episodes, campaigns endpoints
- Analytics endpoints
- Sponsors endpoints

---

## Support

For API support:
- **Email:** api-support@castor.app
- **Documentation:** https://docs.castor.app/api
- **Status Page:** https://status.castor.app

---

**Documentation Generated By:** Unified Background Agent  
**Last Updated:** 2024-12

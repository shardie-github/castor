# API Documentation

**Base URL:** `http://localhost:8000` (development)  
**Production URL:** Configure via `NEXT_PUBLIC_API_URL`

This document provides a comprehensive reference for all API endpoints.

## Authentication

All endpoints (except `/api/v1/auth/*`) require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

## Response Format

### Success Response
```json
{
  "data": { ... },
  "message": "Success message"
}
```

### Error Response
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully created
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

---

## Authentication Endpoints

### POST `/api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
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
  "message": "Registration successful. Please verify your email."
}
```

### POST `/api/v1/auth/login`

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### POST `/api/v1/auth/logout`

Logout current user (invalidate refresh token).

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### POST `/api/v1/auth/verify-email`

Verify email address with verification token.

**Request Body:**
```json
{
  "token": "verification_token"
}
```

**Response:** `200 OK`

### POST `/api/v1/auth/reset-password-request`

Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`

### POST `/api/v1/auth/reset-password`

Reset password with reset token.

**Request Body:**
```json
{
  "token": "reset_token",
  "new_password": "NewSecurePass123"
}
```

**Response:** `200 OK`

### POST `/api/v1/auth/change-password`

Change password (requires authentication).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewSecurePass123"
}
```

**Response:** `200 OK`

### POST `/api/v1/auth/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "new_jwt_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### GET `/api/v1/auth/me`

Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "tenant_id": "uuid",
  "email_verified": true
}
```

---

## Tenant Management

### POST `/api/v1/tenants/`

Create a new tenant (organization).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "domain": "acme.example.com",
  "subscription_tier": "free",
  "billing_email": "billing@acme.com"
}
```

**Response:** `201 Created`
```json
{
  "tenant_id": "uuid",
  "name": "Acme Corp",
  "slug": "acme-corp",
  "subscription_tier": "free",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET `/api/v1/tenants/{tenant_id}`

Get tenant information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/tenants/{tenant_id}`

Update tenant information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Updated Name",
  "subscription_tier": "pro"
}
```

**Response:** `200 OK`

### GET `/api/v1/tenants/{tenant_id}/quota/{quota_type}`

Get tenant quota information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "quota_type": "max_users",
  "current": 5,
  "limit": 10
}
```

---

## Podcast Management

### POST `/api/v1/podcasts`

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
  "podcast_id": "uuid",
  "name": "My Podcast",
  "rss_feed_url": "https://example.com/feed.xml",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET `/api/v1/podcasts`

List all podcasts for current tenant.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "podcast_id": "uuid",
    "name": "My Podcast",
    "rss_feed_url": "https://example.com/feed.xml"
  }
]
```

### GET `/api/v1/podcasts/{podcast_id}`

Get podcast details.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/podcasts/{podcast_id}`

Update podcast information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Updated Podcast Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`

### DELETE `/api/v1/podcasts/{podcast_id}`

Delete a podcast.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

---

## Episode Management

### POST `/api/v1/episodes`

Create a new episode.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "podcast_id": "uuid",
  "title": "Episode Title",
  "description": "Episode description",
  "episode_number": 1,
  "published_at": "2024-01-01T00:00:00Z",
  "duration_seconds": 3600,
  "audio_url": "https://example.com/episode.mp3"
}
```

**Response:** `201 Created`

### GET `/api/v1/episodes`

List episodes.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `podcast_id` (optional): Filter by podcast
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:** `200 OK`

### GET `/api/v1/episodes/{episode_id}`

Get episode details.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/episodes/{episode_id}`

Update episode information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### DELETE `/api/v1/episodes/{episode_id}`

Delete an episode.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

---

## Campaign Management

### POST `/api/v1/campaigns`

Create a new campaign.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "sponsor_id": "uuid",
  "name": "Campaign Name",
  "description": "Campaign description",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "stage": "draft"
}
```

**Response:** `201 Created`

### GET `/api/v1/campaigns`

List campaigns.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `sponsor_id` (optional): Filter by sponsor
- `stage` (optional): Filter by stage (draft, active, paused, completed, cancelled)
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:** `200 OK`

### GET `/api/v1/campaigns/{campaign_id}`

Get campaign details.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/campaigns/{campaign_id}`

Update campaign.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### DELETE `/api/v1/campaigns/{campaign_id}`

Delete a campaign.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

### POST `/api/v1/campaigns/{campaign_id}/duplicate`

Duplicate a campaign.

**Headers:** `Authorization: Bearer <token>`

**Response:** `201 Created`

### GET `/api/v1/campaigns/{campaign_id}/analytics`

Get campaign analytics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start_date` (optional): Start date for analytics
- `end_date` (optional): End date for analytics

**Response:** `200 OK`
```json
{
  "campaign_id": "uuid",
  "total_listeners": 1000,
  "total_impressions": 5000,
  "conversion_rate": 0.05,
  "roi": 2.5
}
```

---

## Sponsor Management

### POST `/api/v1/sponsors`

Create a new sponsor.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Sponsor Name",
  "website_url": "https://sponsor.com",
  "logo_url": "https://sponsor.com/logo.png"
}
```

**Response:** `201 Created`

### GET `/api/v1/sponsors`

List sponsors.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### GET `/api/v1/sponsors/{sponsor_id}`

Get sponsor details.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/sponsors/{sponsor_id}`

Update sponsor information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### DELETE `/api/v1/sponsors/{sponsor_id}`

Delete a sponsor.

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

---

## Analytics Endpoints

### GET `/api/v1/analytics/listeners`

Get listener analytics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `episode_id` (optional): Filter by episode
- `start_date` (required): Start date (ISO 8601)
- `end_date` (required): End date (ISO 8601)
- `granularity` (optional): daily, hourly, weekly (default: daily)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "listeners": 100,
      "unique_listeners": 80,
      "completion_rate": 0.75
    }
  ]
}
```

### GET `/api/v1/analytics/attribution`

Get attribution analytics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `campaign_id` (required): Campaign ID
- `start_date` (required): Start date
- `end_date` (required): End date
- `model` (optional): first_touch, last_touch, linear, time_decay, position_based

**Response:** `200 OK`

---

## Attribution Endpoints

### POST `/api/v1/attribution/track`

Track an attribution event.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "campaign_id": "uuid",
  "episode_id": "uuid",
  "listener_id": "listener_123",
  "attribution_type": "click",
  "attribution_data": {
    "url": "https://example.com",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Response:** `201 Created`

### GET `/api/v1/attribution/roi`

Calculate ROI for a campaign.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `campaign_id` (required): Campaign ID
- `start_date` (required): Start date
- `end_date` (required): End date
- `model` (optional): Attribution model

**Response:** `200 OK`
```json
{
  "campaign_id": "uuid",
  "total_revenue": 10000,
  "total_cost": 5000,
  "roi": 2.0,
  "roi_percentage": 100
}
```

---

## Cost Tracking

### POST `/api/v1/cost/allocate`

Allocate cost to a tenant/resource.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "tenant_id": "uuid",
  "resource_type": "api_calls",
  "amount": 100,
  "unit": "requests"
}
```

**Response:** `201 Created`

### GET `/api/v1/cost/`

Get cost tracking information.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `tenant_id` (optional): Filter by tenant
- `start_date` (optional): Start date
- `end_date` (optional): End date

**Response:** `200 OK`

---

## Feature Flags

### GET `/api/v1/features`

List all feature flags.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "name": "enable_matchmaking",
    "enabled": false,
    "description": "Enable matchmaking feature"
  }
]
```

### GET `/api/v1/features/{feature_name}`

Get feature flag status.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### PUT `/api/v1/features/{feature_name}`

Update feature flag.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "enabled": true
}
```

**Response:** `200 OK`

---

## Monitoring & Health

### GET `/health`

Health check endpoint (no authentication required).

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "latency_ms": 5
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency_ms": 2
    }
  ]
}
```

### GET `/metrics`

Prometheus metrics endpoint (no authentication required).

**Response:** `200 OK` (Prometheus format)

---

## Rate Limiting

API endpoints are rate-limited:
- **Per minute:** 60 requests
- **Per hour:** 1,000 requests
- **Per day:** 10,000 requests

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

---

## Pagination

List endpoints support pagination via query parameters:
- `limit`: Number of results per page (default: 50, max: 100)
- `offset`: Number of results to skip (default: 0)

**Example:**
```
GET /api/v1/podcasts?limit=20&offset=40
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

Common error codes:
- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_REQUIRED` - Authentication token missing or invalid
- `AUTHORIZATION_FAILED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Requested resource does not exist
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `INTERNAL_ERROR` - Internal server error

---

## Webhooks

Webhook endpoints are available for:
- Campaign events
- Attribution events
- User events

Configure webhooks via `/api/v1/settings/webhooks`.

---

**Last Updated:** 2024-12-XX  
**API Version:** 1.0.0

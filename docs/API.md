# API Documentation

Complete API reference for the Podcast Analytics & Sponsorship Platform.

## Base URL

- **Production**: `https://api.castor.app`
- **Staging**: `https://staging-api.castor.app`
- **Local**: `http://localhost:8000`

## Authentication

Most endpoints require authentication using JWT tokens.

### Getting an Access Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### Using the Access Token

Include the token in the Authorization header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Rate Limiting

API requests are rate-limited:
- **Per minute**: 60 requests
- **Per hour**: 1000 requests
- **Per day**: 10000 requests

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Error Responses

All errors follow a standardized format:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Field-specific error",
      "code": "error_code"
    }
  ],
  "timestamp": "2024-12-XXT00:00:00Z",
  "path": "/api/v1/endpoint",
  "request_id": "request-id"
}
```

### Error Types

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (resource conflict)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable

## Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
```

#### Login
```http
POST /api/v1/auth/login
```

#### Logout
```http
POST /api/v1/auth/logout
```

#### Get Current User
```http
GET /api/v1/auth/me
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

#### Request Password Reset
```http
POST /api/v1/auth/password/reset/request
```

#### Reset Password
```http
POST /api/v1/auth/password/reset
```

### Campaigns

#### List Campaigns
```http
GET /api/v1/campaigns
```

#### Get Campaign
```http
GET /api/v1/campaigns/{campaign_id}
```

#### Create Campaign
```http
POST /api/v1/campaigns
```

#### Update Campaign
```http
PUT /api/v1/campaigns/{campaign_id}
```

#### Delete Campaign
```http
DELETE /api/v1/campaigns/{campaign_id}
```

#### Get Campaign Analytics
```http
GET /api/v1/campaigns/{campaign_id}/analytics
```

### Podcasts

#### List Podcasts
```http
GET /api/v1/podcasts
```

#### Get Podcast
```http
GET /api/v1/podcasts/{podcast_id}
```

#### Create Podcast
```http
POST /api/v1/podcasts
```

#### Update Podcast
```http
PUT /api/v1/podcasts/{podcast_id}
```

### Episodes

#### List Episodes
```http
GET /api/v1/episodes
```

#### Get Episode
```http
GET /api/v1/episodes/{episode_id}
```

#### Create Episode
```http
POST /api/v1/episodes
```

### Analytics

#### Get Analytics
```http
GET /api/v1/analytics
```

Query Parameters:
- `start_date` - Start date (ISO 8601)
- `end_date` - End date (ISO 8601)
- `podcast_id` - Filter by podcast
- `episode_id` - Filter by episode

### Attribution

#### Track Attribution Event
```http
POST /api/v1/attribution/events
```

#### Get Attribution Data
```http
GET /api/v1/attribution/campaigns/{campaign_id}
```

### Feature Flags

#### List Feature Flags
```http
GET /api/v1/flags
```

#### Get Feature Flag
```http
GET /api/v1/flags/{flag_name}
```

#### Check Feature Flag
```http
GET /api/v1/flags/{flag_name}/check
```

### Health Check

#### System Health
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-XXT00:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "latency_ms": 5.2
    }
  ]
}
```

## OpenAPI Specification

The complete OpenAPI specification is available at:
- `/api/openapi.json` - JSON format
- `/api/docs` - Interactive Swagger UI
- `/api/redoc` - ReDoc documentation

To export the OpenAPI spec:
```bash
python scripts/export_openapi.py --output docs/openapi.json
```

## SDKs

### JavaScript/TypeScript

```typescript
import { api } from '@/lib/api'

// Get campaigns
const campaigns = await api.getCampaigns()

// Create campaign
const campaign = await api.createCampaign({
  name: 'My Campaign',
  start_date: '2024-01-01',
  end_date: '2024-12-31'
})
```

### Python

```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Get campaigns
response = requests.get(
    'https://api.castor.app/api/v1/campaigns',
    headers=headers
)
campaigns = response.json()
```

## Examples

### Complete Campaign Creation Flow

```bash
# 1. Login
curl -X POST https://api.castor.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# 2. Create Campaign
curl -X POST https://api.castor.app/api/v1/campaigns \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 Campaign",
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "podcast_id": "podcast-uuid"
  }'

# 3. Get Analytics
curl -X GET https://api.castor.app/api/v1/campaigns/{campaign_id}/analytics \
  -H "Authorization: Bearer {token}"
```

## Support

For API support:
- **Email**: api-support@castor.app
- **Documentation**: https://docs.castor.app/api
- **Status Page**: https://status.castor.app

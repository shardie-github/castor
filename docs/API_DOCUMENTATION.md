# API Documentation

Complete API reference with examples, authentication, and best practices.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)
6. [Examples](#examples)

## Authentication

The API uses OAuth 2.0 / OIDC for authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Getting an Access Token

1. **OAuth 2.0 Flow**:
   ```
   POST /api/v1/security/oauth/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&code=CODE&redirect_uri=REDIRECT_URI
   ```

2. **API Key Authentication** (for programmatic access):
   ```http
   X-API-Key: YOUR_API_KEY
   ```

### Multi-Factor Authentication

For enhanced security, MFA can be enabled:

```http
POST /api/v1/security/mfa/enable
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Base URL

- **Production**: `https://api.example.com`
- **Staging**: `https://api-staging.example.com`
- **Development**: `http://localhost:8000`

## Rate Limiting

Rate limits are applied per API key or user:

- **Per Minute**: 60 requests
- **Per Hour**: 1,000 requests
- **Per Day**: 10,000 requests

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": true,
  "message": "User-friendly error message",
  "code": "ERROR_CODE",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format",
      "code": "INVALID_EMAIL"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "path": "/api/v1/endpoint"
}
```

### Common Error Codes

- `VALIDATION_ERROR` (400): Invalid input
- `AUTHENTICATION_REQUIRED` (401): Missing or invalid token
- `AUTHORIZATION_FAILED` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

## Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "latency_ms": 5
    }
  ]
}
```

### Risk Management

#### Create Risk

```http
POST /api/v1/risks
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "category": "security",
  "title": "Data Breach Risk",
  "description": "Risk of unauthorized data access",
  "impact": 5,
  "probability": 3,
  "owner": "security-team",
  "mitigation_strategies": [
    "Implement encryption",
    "Add access controls"
  ]
}
```

**Response:**
```json
{
  "risk_id": "uuid",
  "category": "security",
  "title": "Data Breach Risk",
  "risk_score": 15,
  "severity": "high",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### List Risks

```http
GET /api/v1/risks?category=security&severity=high&limit=10
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Partnership Tools

#### Create Referral

```http
POST /api/v1/partners/referrals
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "referrer_id": "partner-123",
  "first_year_rate": 0.20,
  "recurring_rate": 0.10
}
```

**Response:**
```json
{
  "referral_id": "uuid",
  "referral_code": "REF12345",
  "referral_link": "https://app.example.com/signup?ref=REF12345",
  "status": "pending"
}
```

#### Track Referral Conversion

```http
POST /api/v1/partners/referrals/convert
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "referral_code": "REF12345",
  "customer_id": "customer-456",
  "customer_revenue": 1000.00
}
```

### Business Analytics

#### Get Business Dashboard

```http
GET /api/v1/business/dashboard
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "revenue": {
    "total": 50000.00,
    "recurring": 45000.00,
    "one_time": 5000.00,
    "growth_rate": 15.5,
    "avg_per_user": 100.00,
    "lifetime_value": 1200.00
  },
  "customers": {
    "total": 500,
    "active": 450,
    "new": 50,
    "churned": 10,
    "churn_rate": 2.0,
    "growth_rate": 10.0
  }
}
```

## Examples

### Python

```python
import requests

# Set up authentication
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

# Create a risk
response = requests.post(
    "https://api.example.com/api/v1/risks",
    headers=headers,
    json={
        "category": "security",
        "title": "Test Risk",
        "description": "Test description",
        "impact": 5,
        "probability": 3,
        "owner": "team-lead"
    }
)

risk = response.json()
print(f"Created risk: {risk['risk_id']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.example.com',
  headers: {
    'Authorization': `Bearer ${process.env.ACCESS_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Create a referral
async function createReferral(referrerId) {
  const response = await api.post('/api/v1/partners/referrals', {
    referrer_id: referrerId,
    first_year_rate: 0.20,
    recurring_rate: 0.10
  });
  
  return response.data;
}
```

### cURL

```bash
# Create a risk
curl -X POST https://api.example.com/api/v1/risks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "security",
    "title": "Test Risk",
    "description": "Test description",
    "impact": 5,
    "probability": 3,
    "owner": "team-lead"
  }'

# Get business dashboard
curl -X GET https://api.example.com/api/v1/business/dashboard \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** - never commit to version control
3. **Handle rate limits** - implement exponential backoff
4. **Validate input** - check data before sending requests
5. **Use pagination** - for list endpoints, use limit and offset
6. **Monitor errors** - track and handle error responses
7. **Cache responses** - when appropriate, cache GET requests

## SDKs

Official SDKs are available:

- **Python**: `pip install podcast-analytics-sdk`
- **JavaScript**: `npm install @podcast-analytics/sdk`
- **Ruby**: `gem install podcast_analytics`

## Support

For API support:
- **Email**: api-support@example.com
- **Documentation**: https://docs.example.com
- **Status Page**: https://status.example.com

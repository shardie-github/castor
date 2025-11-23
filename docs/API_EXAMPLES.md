# API Usage Examples

Practical examples for common API operations.

## Authentication Examples

### Register and Login

```python
import requests

# Register
register_response = requests.post(
    'https://api.castor.app/api/v1/auth/register',
    json={
        'email': 'user@example.com',
        'password': 'SecurePassword123!',
        'name': 'John Doe',
        'accept_terms': True,
        'accept_privacy': True
    }
)

# Login
login_response = requests.post(
    'https://api.castor.app/api/v1/auth/login',
    json={
        'email': 'user@example.com',
        'password': 'SecurePassword123!'
    }
)

token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
```

## Campaign Management Examples

### Create Campaign with Attribution

```python
# Create campaign
campaign = requests.post(
    'https://api.castor.app/api/v1/campaigns',
    headers=headers,
    json={
        'name': 'Summer Promotion',
        'start_date': '2024-06-01',
        'end_date': '2024-08-31',
        'podcast_id': 'podcast-uuid',
        'sponsor_id': 'sponsor-uuid'
    }
).json()

campaign_id = campaign['campaign_id']

# Track attribution event
requests.post(
    'https://api.castor.app/api/v1/attribution/events',
    headers=headers,
    json={
        'event_type': 'click',
        'campaign_id': campaign_id,
        'properties': {
            'source': 'podcast',
            'episode_id': 'episode-uuid'
        }
    }
)
```

### Get Campaign Analytics

```python
# Get analytics with date range
analytics = requests.get(
    f'https://api.castor.app/api/v1/campaigns/{campaign_id}/analytics',
    headers=headers,
    params={
        'start_date': '2024-06-01',
        'end_date': '2024-08-31'
    }
).json()

print(f"Revenue: ${analytics['revenue']}")
print(f"Conversions: {analytics['conversions']}")
print(f"ROI: {analytics['roi']}%")
```

## Podcast Management Examples

### Add Podcast and Episodes

```python
# Create podcast
podcast = requests.post(
    'https://api.castor.app/api/v1/podcasts',
    headers=headers,
    json={
        'name': 'My Podcast',
        'rss_feed_url': 'https://example.com/feed.xml'
    }
).json()

podcast_id = podcast['podcast_id']

# Add episode
episode = requests.post(
    'https://api.castor.app/api/v1/episodes',
    headers=headers,
    json={
        'podcast_id': podcast_id,
        'title': 'Episode 1',
        'published_at': '2024-01-01T00:00:00Z'
    }
).json()
```

## Analytics Examples

### Get Time-Series Analytics

```python
analytics = requests.get(
    'https://api.castor.app/api/v1/analytics',
    headers=headers,
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'podcast_id': 'podcast-uuid',
        'granularity': 'day'
    }
).json()

# Process time-series data
for data_point in analytics['time_series']:
    print(f"{data_point['date']}: {data_point['listeners']} listeners")
```

## Feature Flags Examples

### Check Feature Flag

```python
# Check if feature is enabled
flag_check = requests.get(
    'https://api.castor.app/api/v1/flags/new-dashboard/check',
    headers=headers,
    params={
        'tenant_id': 'tenant-uuid',
        'user_id': 'user-uuid'
    }
).json()

if flag_check['enabled']:
    # Use new dashboard
    pass
```

### Manage Feature Flags (Admin)

```python
# Create feature flag
requests.post(
    'https://api.castor.app/api/v1/flags',
    headers=headers,
    json={
        'flag_name': 'new-feature',
        'status': 'gradual_rollout',
        'rollout_percentage': 25
    }
)

# Update feature flag
requests.put(
    'https://api.castor.app/api/v1/flags/new-feature',
    headers=headers,
    json={
        'status': 'enabled',
        'rollout_percentage': 100
    }
)
```

## Error Handling Examples

### Handle API Errors

```python
try:
    response = requests.get(
        'https://api.castor.app/api/v1/campaigns/invalid-id',
        headers=headers
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f"Error: {error_data['error']}")
    print(f"Message: {error_data['message']}")
    
    if error_data.get('details'):
        for detail in error_data['details']:
            print(f"  - {detail['field']}: {detail['message']}")
```

## Rate Limiting Examples

### Handle Rate Limits

```python
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limited
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = reset_time - int(time.time())
            if wait_time > 0:
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
        
        response.raise_for_status()
        return response.json()
    
    raise Exception("Max retries exceeded")
```

## Webhook Examples

### Set Up Webhook

```python
webhook = requests.post(
    'https://api.castor.app/api/v1/webhooks',
    headers=headers,
    json={
        'url': 'https://your-app.com/webhooks',
        'events': ['campaign.created', 'campaign.updated'],
        'secret': 'webhook-secret-key'
    }
).json()
```

### Verify Webhook Signature

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

## Batch Operations Examples

### Batch Create Campaigns

```python
campaigns_data = [
    {'name': 'Campaign 1', 'start_date': '2024-01-01', 'end_date': '2024-03-31'},
    {'name': 'Campaign 2', 'start_date': '2024-04-01', 'end_date': '2024-06-30'},
]

created_campaigns = []
for campaign_data in campaigns_data:
    response = requests.post(
        'https://api.castor.app/api/v1/campaigns',
        headers=headers,
        json=campaign_data
    )
    created_campaigns.append(response.json())
```

## Pagination Examples

### Paginate Through Results

```python
def get_all_campaigns(headers, page_size=50):
    all_campaigns = []
    page = 1
    
    while True:
        response = requests.get(
            'https://api.castor.app/api/v1/campaigns',
            headers=headers,
            params={'page': page, 'page_size': page_size}
        ).json()
        
        campaigns = response.get('items', [])
        if not campaigns:
            break
        
        all_campaigns.extend(campaigns)
        page += 1
    
    return all_campaigns
```

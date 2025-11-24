# Seed Data Guide

**Last Updated:** 2024-12  
**Purpose:** Guide for seeding demo/development data

---

## Overview

Seed data helps with:
- **Development:** Quick setup for local development
- **Demo:** Pre-populated data for demos
- **Testing:** Consistent test data

---

## Seed Script

**Location:** `scripts/seed-demo-data.py`

**Usage:**
```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/podcast_analytics"
export JWT_SECRET="test_secret_key_min_32_chars_long_for_seeding"
export ENCRYPTION_KEY="test_encryption_key_min_32_chars_long_for_seeding"

# Run seed script
python scripts/seed-demo-data.py
```

---

## What Gets Seeded

### 1. Tenants
- **Count:** 3 demo tenants
- **Data:** Sample organizations with different sizes

### 2. Users
- **Count:** 10 users (distributed across tenants)
- **Data:** 
  - Admin users
  - Regular users
  - Test accounts

### 3. Podcasts
- **Count:** 5 podcasts per tenant
- **Data:**
  - Podcast metadata
  - RSS feed URLs (sample)
  - Descriptions

### 4. Episodes
- **Count:** 10 episodes per podcast
- **Data:**
  - Episode titles
  - Published dates
  - Duration
  - Audio URLs (sample)

### 5. Campaigns
- **Count:** 3 campaigns per tenant
- **Data:**
  - Campaign names
  - Start/end dates
  - Budgets
  - Status (active, paused, completed)

### 6. Sponsors
- **Count:** 5 sponsors per tenant
- **Data:**
  - Sponsor names
  - Company information
  - Contact details

### 7. Listener Events (Optional)
- **Count:** 1000 events (if enabled)
- **Data:**
  - Timestamped listener events
  - Episode plays
  - Completion rates
  - Geographic data

### 8. Attribution Events (Optional)
- **Count:** 500 events (if enabled)
- **Data:**
  - Campaign attribution
  - Conversion events
  - ROI calculations

---

## Seed Data Structure

### Tenant Structure
```
Tenant 1: "Acme Podcast Network"
  - Users: 3 (1 admin, 2 regular)
  - Podcasts: 5
  - Campaigns: 3
  - Sponsors: 5

Tenant 2: "Tech Talk Media"
  - Users: 4 (1 admin, 3 regular)
  - Podcasts: 5
  - Campaigns: 3
  - Sponsors: 5

Tenant 3: "Indie Creator Studio"
  - Users: 3 (1 admin, 2 regular)
  - Podcasts: 5
  - Campaigns: 3
  - Sponsors: 5
```

---

## Customization

### Modify Seed Data

Edit `scripts/seed-demo-data.py` to customize:
- Number of records
- Data values
- Relationships
- Optional data (listener events, etc.)

### Add Custom Seed Data

```python
# Example: Add custom podcast
async def seed_custom_podcast(db, tenant_id):
    podcast = await db.fetchrow(
        """
        INSERT INTO podcasts (tenant_id, name, description, rss_feed_url)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        tenant_id,
        "My Custom Podcast",
        "Custom description",
        "https://example.com/feed.xml"
    )
    return podcast
```

---

## Production Considerations

### ⚠️ Never Run Seed Script in Production

The seed script is designed for development and demo environments only.

**Why:**
- Creates test/demo data
- May overwrite existing data
- Not designed for production use

### Production Data

For production:
1. Use real user data (from registration)
2. Import actual podcast feeds
3. Use real campaign data
4. Never seed test data

---

## Verification

After seeding, verify data:

```sql
-- Check tenant count
SELECT COUNT(*) FROM tenants;

-- Check user count
SELECT COUNT(*) FROM users;

-- Check podcasts per tenant
SELECT tenant_id, COUNT(*) 
FROM podcasts 
GROUP BY tenant_id;

-- Check episodes per podcast
SELECT podcast_id, COUNT(*) 
FROM episodes 
GROUP BY podcast_id;
```

---

## Reset Seed Data

To reset and re-seed:

```bash
# Option 1: Drop and recreate database
dropdb podcast_analytics
createdb podcast_analytics
./scripts/db-migrate-local.sh
python scripts/seed-demo-data.py

# Option 2: Truncate tables (careful!)
psql $DATABASE_URL -c "TRUNCATE TABLE episodes, campaigns, podcasts, users, tenants CASCADE;"
python scripts/seed-demo-data.py
```

---

## CI/CD Integration

### Testing with Seed Data

Seed data can be used in CI/CD for integration tests:

```yaml
# .github/workflows/test.yml
- name: Seed test data
  run: |
    python scripts/seed-demo-data.py
  env:
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check `DATABASE_URL` is set correctly
   - Verify database is running
   - Check network connectivity

2. **Migration Not Applied**
   - Run migrations first: `./scripts/db-migrate-local.sh`
   - Verify schema exists

3. **Duplicate Key Errors**
   - Seed script may have been run before
   - Reset database or skip existing records

4. **Missing Dependencies**
   - Install requirements: `pip install -r requirements.txt`
   - Check Python version (3.11+)

---

## Best Practices

1. **Always Run Migrations First**
   ```bash
   ./scripts/db-migrate-local.sh
   python scripts/seed-demo-data.py
   ```

2. **Use Separate Databases**
   - Development: `podcast_analytics_dev`
   - Testing: `podcast_analytics_test`
   - Production: Never seed

3. **Version Control Seed Script**
   - Keep seed script in version control
   - Document changes
   - Review seed data regularly

4. **Document Custom Seed Data**
   - Document any custom seed data
   - Explain why it's needed
   - Keep it minimal

---

## Related Documentation

- `docs/db-migrations-and-schema.md` - Database schema documentation
- `scripts/seed-demo-data.py` - Seed script source
- `docs/local-dev.md` - Local development setup

---

**Documentation Generated By:** Unified Background Agent  
**Last Updated:** 2024-12

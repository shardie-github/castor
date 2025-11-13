# Operations Notes
**RUN-ID:** 20251113T114706Z

## Migration Execution

### Run Migration

```bash
# Set database URL
export PGURL="postgresql://user:pass@host:5432/db?sslmode=require"

# Run migration
./scripts/db_migrate.sh migrations/20251113T114706Z

# Verify migration
psql "$PGURL" -f scripts/verify_run.sql
```

### Dry-Run Migration

```bash
./scripts/db_migrate.sh migrations/20251113T114706Z --dry-run
```

### Rollback Migration

```bash
./scripts/db_rollback.sh migrations/20251113T114706Z
```

**⚠️ Warning:** Rollback only removes objects added by this migration pack. Existing tables/columns are preserved.

---

## CSV Import

### Upload CSV File

```bash
curl -X POST http://localhost:8000/api/v1/etl/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/metrics_daily.csv"
```

### Check Import Status

```bash
curl http://localhost:8000/api/v1/etl/status/{import_id} \
  -H "Authorization: Bearer $TOKEN"
```

### View Import History

```bash
curl http://localhost:8000/api/v1/etl/history \
  -H "Authorization: Bearer $TOKEN"
```

### Notes
- CSV imports to `listener_metrics` table
- `metrics_daily` is a materialized view (refresh required)
- To refresh view: `SELECT refresh_metrics_daily();`

---

## Re-run ETL

### Manual Refresh

```sql
-- Refresh metrics_daily materialized view
SELECT refresh_metrics_daily();
```

### Automated Refresh

Schedule via cron or scheduled_tasks table:
```sql
-- Example: Run daily at 2 AM UTC
SELECT cron.schedule('refresh-metrics-daily', '0 2 * * *', 'SELECT refresh_metrics_daily();');
```

---

## Recalculate Matches

### Single Match

```bash
curl -X POST "http://localhost:8000/api/match/recalculate?advertiser_id={adv_id}&podcast_id={pod_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### All Matches for Advertiser

```bash
curl -X POST "http://localhost:8000/api/match/recalculate?advertiser_id={adv_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### All Matches for Podcast

```bash
curl -X POST "http://localhost:8000/api/match/recalculate?podcast_id={pod_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Toggle Feature Flags

### Enable Features

```bash
# ETL CSV Upload
export ENABLE_ETL_CSV_UPLOAD=true

# Matchmaking
export ENABLE_MATCHMAKING=true

# IO Bookings
export ENABLE_IO_BOOKINGS=true

# Deal Pipeline
export ENABLE_DEAL_PIPELINE=true

# Dashboard Cards
export ENABLE_NEW_DASHBOARD_CARDS=true
```

### Restart Services

After setting flags, restart API server:
```bash
# If using systemd
sudo systemctl restart podcast-analytics-api

# If using docker-compose
docker-compose restart api

# If running directly
# Stop and restart uvicorn process
```

---

## Troubleshoot ETL Errors

### Check Import Logs

```bash
# View recent imports
curl http://localhost:8000/api/v1/etl/history \
  -H "Authorization: Bearer $TOKEN"

# Check database logs
psql "$PGURL" -c "SELECT * FROM etl_imports ORDER BY started_at DESC LIMIT 10;"
```

### Common Issues

1. **CSV Validation Errors**
   - Check CSV format matches expected schema
   - Verify date format: `YYYY-MM-DD`
   - Verify UUID format for `episode_id`

2. **Duplicate Key Errors**
   - Check unique index `ux_metrics_daily_day_ep_source` exists
   - Verify no duplicate rows in CSV

3. **View Not Refreshing**
   - Manually refresh: `SELECT refresh_metrics_daily();`
   - Check if view refresh is scheduled

4. **Feature Flag Not Working**
   - Verify environment variable is set
   - Restart API server after setting flag
   - Check flag name matches (case-sensitive)

---

## Monitoring

### Check Event Emissions

```sql
SELECT event_type, COUNT(*) 
FROM events 
WHERE event_type IN ('io.delivered', 'io.scheduled', 'deal.stage_changed', 'match.recalculated', 'etl.import_completed')
GROUP BY event_type;
```

### Check IO Status Changes

```sql
SELECT io_id, status, updated_at 
FROM io_bookings 
WHERE updated_at >= NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;
```

### Check Match Scores

```sql
SELECT advertiser_id, podcast_id, score, updated_at 
FROM matches 
ORDER BY score DESC 
LIMIT 10;
```

---

## Backup & Recovery

### Before Migration

```bash
# Backup database
pg_dump "$PGURL" > backup_before_20251113T114706Z.sql
```

### After Migration

```bash
# Verify backup
psql "$PGURL" -f scripts/verify_run.sql
```

### Rollback Procedure

1. **Stop API server** (if running)
2. **Run rollback script:**
   ```bash
   ./scripts/db_rollback.sh migrations/20251113T114706Z
   ```
3. **Verify rollback:**
   ```sql
   -- Check index dropped
   SELECT 1 FROM pg_class WHERE relname='ux_metrics_daily_day_ep_source';
   ```
4. **Restore from backup if needed:**
   ```bash
   psql "$PGURL" < backup_before_20251113T114706Z.sql
   ```

---

## Support

For issues or questions:
1. Check run logs: `docs/run-logs/20251113T114706Z_*.md`
2. Review migration README: `migrations/20251113T114706Z/README.md`
3. Check verification script: `scripts/verify_run.sql`

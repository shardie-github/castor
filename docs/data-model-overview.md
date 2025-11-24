# Data Model Overview

**Generated:** 2024-12-XX  
**Purpose:** Document the intended final database schema inferred from all migrations.

---

## Schema Summary

**Total Tables:** ~50+ tables  
**Database:** PostgreSQL 15+ with TimescaleDB extension  
**Key Features:** Multi-tenant (RLS), time-series data (hypertables), JSONB metadata, UUID primary keys

---

## Core Domain Tables

### Users & Authentication

#### `users`
**Purpose:** User accounts and profiles  
**Key Columns:**
- `user_id` (UUID, PK)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `name`, `role`, `subscription_tier`
- `tenant_id` (UUID, FK → tenants)
- `stripe_customer_id`, `stripe_subscription_id`
- `email_verified` (BOOLEAN)
- `created_at`, `updated_at`, `last_login`

**Relationships:**
- Belongs to `tenants`
- Has many `podcasts`, `campaigns`, `sponsors`, `reports`

#### `email_verification_tokens`
**Purpose:** Email verification tokens  
**Key Columns:** `token_id`, `user_id`, `token_hash`, `expires_at`

#### `password_reset_tokens`
**Purpose:** Password reset tokens  
**Key Columns:** `token_id`, `user_id`, `token_hash`, `expires_at`, `used_at`

#### `refresh_tokens`
**Purpose:** JWT refresh tokens  
**Key Columns:** `token_id`, `user_id`, `token_hash`, `expires_at`, `last_used_at`

#### `user_email_preferences`
**Purpose:** User email notification preferences  
**Key Columns:** `user_id` (PK), `email_notifications`, `sponsorship_alerts`, `weekly_reports`

#### `user_metrics`
**Purpose:** Calculated user-level metrics (TTFV, completion rates)  
**Key Columns:** `user_id`, `metric_name`, `metric_value`, `recorded_at`

---

### Multi-Tenancy

#### `tenants`
**Purpose:** Tenant/organization isolation  
**Key Columns:**
- `tenant_id` (UUID, PK)
- `name`, `slug` (UNIQUE), `domain`
- `subscription_tier`, `status`
- `billing_email`
- `created_at`, `updated_at`

**Relationships:**
- Has many `users`, `podcasts`, `campaigns`, etc.

#### `tenant_settings`
**Purpose:** Tenant-specific configuration  
**Key Columns:** `tenant_id`, `setting_key`, `setting_value` (JSONB)

#### `tenant_quotas`
**Purpose:** Resource quotas per tenant  
**Key Columns:** `tenant_id`, `quota_type`, `limit_value`, `current_usage`, `reset_period`

---

### Content Management

#### `podcasts`
**Purpose:** Podcast shows  
**Key Columns:**
- `podcast_id` (UUID, PK)
- `user_id`, `tenant_id` (FKs)
- `title`, `description`, `feed_url`, `website_url`
- `platform_configs` (JSONB)
- `ingestion_status`, `last_ingested_at`

**Relationships:**
- Belongs to `users`, `tenants`
- Has many `episodes`, `campaigns`

#### `episodes`
**Purpose:** Individual podcast episodes  
**Key Columns:**
- `episode_id` (UUID, PK)
- `podcast_id` (FK)
- `guid` (UNIQUE per podcast), `title`, `description`
- `audio_url`, `duration_seconds`
- `publish_date`, `transcript_status`
- `ad_slots` (JSONB)

**Relationships:**
- Belongs to `podcasts`
- Has many `transcripts`, `listener_events`

#### `transcripts`
**Purpose:** Episode transcripts  
**Key Columns:**
- `transcript_id` (UUID, PK)
- `episode_id` (FK)
- `status`, `source`, `language`
- `transcript_text`, `transcript_json` (JSONB)
- `word_count`, `duration_seconds`

---

### Sponsors & Campaigns

#### `sponsors`
**Purpose:** Sponsor/advertiser entities  
**Key Columns:**
- `sponsor_id` (UUID, PK)
- `user_id`, `tenant_id` (FKs)
- `name`, `company`, `email`, `contact_name`
- `website`, `logo_url`, `industry`

**Relationships:**
- Belongs to `users`, `tenants`
- Has many `campaigns`

#### `campaigns`
**Purpose:** Advertising campaigns  
**Key Columns:**
- `campaign_id` (UUID, PK)
- `user_id`, `podcast_id`, `sponsor_id`, `tenant_id` (FKs)
- `name`, `status`, `start_date`, `end_date`
- `campaign_value`, `episode_ids` (UUID[])
- `attribution_config` (JSONB)

**Relationships:**
- Belongs to `users`, `podcasts`, `sponsors`, `tenants`
- Has many `attribution_events`, `reports`

---

### Analytics & Attribution

#### `listener_events` (TimescaleDB Hypertable)
**Purpose:** Time-series listener behavior events  
**Key Columns:**
- `event_id` (UUID, PK)
- `timestamp` (TIMESTAMP, partition key)
- `podcast_id`, `episode_id`, `campaign_id`, `tenant_id`
- `event_type` (download, stream, listen_start, etc.)
- `platform`, `country_code`, `device_type`
- `listen_duration_seconds`, `completion_rate`
- `session_id`, `ip_address`, `user_agent`

**Features:**
- TimescaleDB hypertable for time-series optimization
- Continuous aggregates: `listener_events_hourly`, `listener_events_daily`
- Retention policy: 90 days

#### `attribution_events` (TimescaleDB Hypertable)
**Purpose:** Attribution/conversion events  
**Key Columns:**
- `event_id` (UUID, PK)
- `timestamp` (TIMESTAMP, partition key)
- `campaign_id`, `podcast_id`, `episode_id`, `tenant_id` (FKs)
- `attribution_method` (promo_code, pixel, utm, etc.)
- `attribution_data`, `conversion_data` (JSONB)
- `user_id`, `session_id`, `device_id`
- `cross_device_match_id`

**Features:**
- TimescaleDB hypertable
- Retention policy: 2 years

#### `attribution_event_metadata`
**Purpose:** Additional metadata for attribution pixel events  
**Key Columns:**
- `event_id` (UUID, PK, FK → attribution_events)
- `page_url`, `referrer`, `user_agent`
- `utm_source`, `utm_medium`, `utm_campaign`, etc.
- `metadata` (JSONB)

#### `listener_metrics` (TimescaleDB Hypertable)
**Purpose:** Aggregated listener metrics  
**Key Columns:**
- `timestamp` (TIMESTAMP, partition key)
- `podcast_id`, `episode_id`, `tenant_id`
- `metric_type`, `value`
- `platform`, `country`, `device`

**Features:**
- TimescaleDB hypertable
- Retention policy: 90 days

---

### Advanced Attribution

#### `attribution_models`
**Purpose:** Attribution model configurations  
**Key Columns:**
- `model_id` (UUID, PK)
- `tenant_id`, `campaign_id` (FKs)
- `model_type` (first_touch, last_touch, linear, time_decay, position_based)
- `configuration` (JSONB), `is_active`

#### `attribution_paths`
**Purpose:** Multi-touch attribution paths  
**Key Columns:**
- `path_id` (UUID, PK)
- `tenant_id`, `campaign_id` (FKs)
- `user_id`, `session_id`, `device_id`
- `touchpoints` (JSONB), `conversion_value`
- `first_touch_at`, `last_touch_at`, `conversion_at`

#### `attribution_validations`
**Purpose:** Attribution model validation results  
**Key Columns:**
- `validation_id` (UUID, PK)
- `campaign_id`, `model_id` (FKs)
- `validation_type`, `ground_truth_value`, `predicted_value`
- `accuracy_score`, `confidence_interval`

#### `attribution_analytics`
**Purpose:** Pre-computed attribution analytics  
**Key Columns:**
- `analytics_id` (UUID, PK)
- `campaign_id`, `model_id` (FKs)
- `date`, `metric_type`, `metric_value`
- `breakdown` (JSONB)

---

### Cross-Platform Attribution

#### `conversion_events`
**Purpose:** Unified conversion tracking across platforms  
**Key Columns:**
- `conversion_id` (UUID, PK)
- `tenant_id`, `campaign_id` (FKs)
- `timestamp`, `platform` (web, mobile_ios, mobile_android, offline)
- `conversion_type`, `conversion_value`, `currency`
- `user_id`, `session_id`, `device_id`
- `referrer_url`, `landing_page_url`

#### `user_journeys`
**Purpose:** Cross-device user journey tracking  
**Key Columns:**
- `journey_id` (UUID, PK)
- `tenant_id` (FK)
- `user_id`, `unified_user_id`
- `first_seen_at`, `last_seen_at`
- `devices`, `sessions`, `touchpoints`, `conversions` (JSONB arrays)

#### `device_fingerprints`
**Purpose:** Device fingerprinting for cross-device matching  
**Key Columns:**
- `fingerprint_id` (UUID, PK)
- `tenant_id` (FK)
- `device_id`, `fingerprint_hash` (UNIQUE)
- `device_type`, `device_os`, `browser`
- `unified_user_id`

#### `offline_conversions`
**Purpose:** Imported offline conversion data  
**Key Columns:**
- `offline_conversion_id` (UUID, PK)
- `tenant_id`, `campaign_id` (FKs)
- `conversion_date`, `conversion_time`
- `customer_id`, `order_id`, `store_location`
- `matched_to_attribution`, `matched_at`

---

### AI & Insights

#### `ai_insights`
**Purpose:** AI-generated insights and analysis  
**Key Columns:**
- `insight_id` (UUID, PK)
- `tenant_id`, `campaign_id`, `episode_id` (FKs)
- `insight_type` (content_analysis, performance_prediction, etc.)
- `content`, `summary`, `sentiment_score`
- `topics`, `keywords`, `recommendations` (JSONB)
- `confidence_score`, `model_version`

#### `predictions`
**Purpose:** ML predictions (campaign performance, ROI, etc.)  
**Key Columns:**
- `prediction_id` (UUID, PK)
- `tenant_id`, `campaign_id` (FKs)
- `prediction_type`, `predicted_value`
- `confidence_interval_lower`, `confidence_interval_upper`
- `actual_value`, `accuracy_score`
- `input_features` (JSONB)

#### `recommendations`
**Purpose:** AI-generated recommendations  
**Key Columns:**
- `recommendation_id` (UUID, PK)
- `tenant_id`, `campaign_id`, `user_id` (FKs)
- `recommendation_type`, `title`, `description`
- `action_items` (JSONB), `expected_impact`
- `priority`, `status`
- `accepted_at`, `implemented_at`

---

### Authorization & Security

#### `roles`
**Purpose:** RBAC roles  
**Key Columns:**
- `role_id` (UUID, PK)
- `tenant_id` (FK)
- `role_name` (UNIQUE per tenant), `role_type` (system/custom)
- `permissions` (JSONB)

#### `user_roles`
**Purpose:** User-role assignments (many-to-many)  
**Key Columns:**
- `user_role_id` (UUID, PK)
- `tenant_id`, `user_id`, `role_id` (FKs)
- `assigned_at`, `assigned_by`, `expires_at`

#### `permissions`
**Purpose:** Fine-grained permissions  
**Key Columns:**
- `permission_id` (UUID, PK)
- `tenant_id` (FK)
- `permission_name` (UNIQUE per tenant)
- `resource_type`, `action` (create, read, update, delete, execute, manage)
- `conditions` (JSONB)

#### `role_permissions`
**Purpose:** Role-permission assignments (many-to-many)  
**Key Columns:**
- `role_permission_id` (UUID, PK)
- `tenant_id`, `role_id`, `permission_id` (FKs)
- `conditions` (JSONB)

#### `access_control_policies`
**Purpose:** ABAC policies  
**Key Columns:**
- `policy_id` (UUID, PK)
- `tenant_id` (FK)
- `policy_name`, `policy_type` (rbac/abac/hybrid)
- `resource_type`, `action`, `conditions` (JSONB)
- `effect` (allow/deny), `priority`, `enabled`

#### `access_logs`
**Purpose:** Authorization audit logs  
**Key Columns:**
- `log_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `resource_type`, `resource_id`, `action`
- `allowed`, `policy_applied`
- `ip_address`, `user_agent`

#### `api_keys`
**Purpose:** API key management  
**Key Columns:**
- `key_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `key_hash`, `key_prefix`, `name`
- `permissions` (JSONB), `rate_limit_per_hour`
- `last_used_at`, `expires_at`, `revoked`

#### `audit_logs`
**Purpose:** General audit logging  
**Key Columns:**
- `log_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `action`, `resource_type`, `resource_id`
- `ip_address`, `user_agent`
- `request_method`, `request_path`, `request_body` (JSONB)
- `response_status`, `success`, `error_message`

#### `security_events`
**Purpose:** Security event tracking  
**Key Columns:**
- `event_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `event_type` (failed_login, suspicious_activity, etc.)
- `severity` (low, medium, high, critical)
- `ip_address`, `user_agent`, `description`
- `resolved`, `resolved_at`, `resolved_by`

#### `gdpr_requests`
**Purpose:** GDPR data requests  
**Key Columns:**
- `request_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `request_type` (data_export, data_deletion, etc.)
- `status`, `requested_at`, `processed_at`
- `data_export_url`, `notes`

---

### Integrations

#### `integrations`
**Purpose:** Third-party integrations  
**Key Columns:**
- `integration_id` (UUID, PK)
- `tenant_id` (FK)
- `integration_name` (UNIQUE per tenant)
- `integration_type` (hosting, ecommerce, marketing, etc.)
- `status`, `configuration` (JSONB)
- `last_synced_at`, `last_error`, `error_count`

#### `integration_tokens`
**Purpose:** OAuth tokens for integrations  
**Key Columns:**
- `token_id` (UUID, PK)
- `tenant_id` (FK)
- `integration_name` (UNIQUE per tenant)
- `token_value`, `refresh_token` (encrypted)
- `token_type`, `expires_at`, `scopes` (TEXT[])

#### `webhooks`
**Purpose:** Webhook configurations  
**Key Columns:**
- `webhook_id` (UUID, PK)
- `tenant_id` (FK)
- `integration_name`, `webhook_url`
- `webhook_secret`, `events` (TEXT[])
- `status`, `last_triggered_at`, `failure_count`

#### `integration_sync_logs`
**Purpose:** Integration sync history  
**Key Columns:**
- `log_id` (UUID, PK)
- `tenant_id` (FK)
- `integration_name`, `sync_type` (full/incremental/manual)
- `status`, `records_synced`, `records_failed`
- `started_at`, `completed_at`, `error_message`

---

### Monetization (from dated migrations)

#### `agencies`
**Purpose:** Agency/consultancy management  
**Key Columns:**
- `agency_id` (UUID, PK)
- `tenant_id` (FK)
- `name`, `slug` (UNIQUE per tenant)
- `commission_rate_percent`, `status`

#### `affiliates`
**Purpose:** Affiliate marketing  
**Key Columns:**
- `affiliate_id` (UUID, PK)
- `tenant_id`, `agency_id` (FKs)
- `name`, `email`, `referral_code` (UNIQUE)
- `commission_rate_percent`, `total_referrals`, `total_commission_cents`

#### `referrals` (duplicate? See partnerships section)
**Purpose:** Referral tracking  
**Key Columns:**
- `referral_id` (UUID, PK)
- `tenant_id`, `affiliate_id`, `referred_tenant_id` (FKs)
- `referral_code`, `conversion_status`
- `conversion_value_cents`, `commission_cents`

#### `ai_token_usage`
**Purpose:** AI token consumption tracking  
**Key Columns:**
- `usage_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `feature_type`, `tokens_used`, `cost_cents`
- `request_id`, `created_at`

#### `ai_token_balances`
**Purpose:** AI token balances per tenant  
**Key Columns:**
- `balance_id` (UUID, PK)
- `tenant_id` (FK, UNIQUE)
- `tokens_purchased`, `tokens_used`, `tokens_remaining`
- `last_purchase_at`, `last_usage_at`

#### `api_usage`
**Purpose:** API usage tracking for billing  
**Key Columns:**
- `usage_id` (UUID, PK)
- `tenant_id`, `api_key_id` (FKs)
- `endpoint`, `method`, `status_code`
- `response_time_ms`, `cost_cents`

#### `white_label_settings`
**Purpose:** White-label configuration  
**Key Columns:**
- `setting_id` (UUID, PK)
- `tenant_id` (FK, UNIQUE)
- `brand_name`, `logo_url`
- `primary_color`, `secondary_color`
- `custom_domain`, `custom_css`
- `email_from_name`, `email_from_address`

#### `subscription_tiers`
**Purpose:** Subscription tier details  
**Key Columns:**
- `tier_id` (UUID, PK)
- `tenant_id` (FK)
- `tier_name`, `monthly_price_cents`
- `ai_tokens_included`, `api_calls_included`
- `advanced_analytics_enabled`, `white_label_enabled`
- `max_podcasts`, `max_episodes_per_month`, `max_users`
- `features` (JSONB), `starts_at`, `ends_at`

#### `billing_transactions`
**Purpose:** All monetization transactions  
**Key Columns:**
- `transaction_id` (UUID, PK)
- `tenant_id` (FK)
- `transaction_type` (subscription, ai_tokens, api_usage, commission, etc.)
- `amount_cents`, `currency`, `status`
- `payment_method`, `payment_provider`
- `external_transaction_id`, `description`
- `created_at`, `completed_at`

---

### Partnerships

#### `partners`
**Purpose:** Partner entities  
**Key Columns:**
- `partner_id` (UUID, PK)
- `partner_name`, `partner_type` (technology, distribution, etc.)
- `contact_email`, `status`
- `partnership_start_date`, `partnership_end_date`

#### `partner_integrations`
**Purpose:** Partner integration configurations  
**Key Columns:**
- `integration_id` (UUID, PK)
- `partner_id` (FK)
- `integration_type`, `integration_status`
- `api_credentials` (JSONB), `webhook_url`

#### `marketplace_listings`
**Purpose:** Marketplace app listings  
**Key Columns:**
- `listing_id` (UUID, PK)
- `marketplace_type` (shopify, woocommerce, etc.)
- `app_id`, `app_name`, `app_description`
- `status`, `revenue_share_rate`
- `total_revenue`, `total_installs`

#### `marketplace_revenue`
**Purpose:** Marketplace revenue tracking  
**Key Columns:**
- `revenue_id` (UUID, PK)
- `listing_id`, `customer_id` (FKs)
- `total_revenue`, `marketplace_share`, `our_revenue`
- `revenue_share_rate`

---

### Operations & Monitoring

#### `reports`
**Purpose:** Generated reports  
**Key Columns:**
- `report_id` (UUID, PK)
- `user_id`, `campaign_id`, `tenant_id` (FKs)
- `template_id`, `report_type`, `format`
- `file_url`, `file_size_bytes`
- `includes_roi`, `includes_attribution`, `includes_benchmarks`
- `date_range_start`, `date_range_end`, `generated_at`

#### `cost_allocations`
**Purpose:** Cost tracking per tenant  
**Key Columns:**
- `allocation_id` (UUID, PK)
- `tenant_id` (FK)
- `date`, `cost_type`, `service_name`
- `amount`, `currency`, `unit`, `quantity`

#### `resource_usage`
**Purpose:** Resource usage metrics  
**Key Columns:**
- `usage_id` (UUID, PK)
- `tenant_id` (FK)
- `timestamp`, `resource_type`, `resource_id`
- `metric_name`, `metric_value`, `unit`

#### `cost_alerts`
**Purpose:** Cost threshold alerts  
**Key Columns:**
- `alert_id` (UUID, PK)
- `tenant_id` (FK)
- `alert_type`, `threshold_percentage`, `threshold_amount`
- `current_amount`, `budget_period`, `status`
- `triggered_at`, `acknowledged_at`

#### `backup_records`
**Purpose:** Backup tracking  
**Key Columns:**
- `backup_id` (UUID, PK)
- `tenant_id` (FK, nullable)
- `backup_type`, `backup_source`, `backup_location`
- `backup_size_bytes`, `backup_format`
- `status`, `started_at`, `completed_at`, `verified_at`
- `retention_until`

#### `replication_status`
**Purpose:** Database replication status  
**Key Columns:**
- `replication_id` (UUID, PK)
- `source_region`, `target_region`
- `replication_type`, `status`
- `lag_seconds`, `last_synced_at`, `last_verified_at`

#### `failover_events`
**Purpose:** Failover event history  
**Key Columns:**
- `event_id` (UUID, PK)
- `failover_type`, `source_region`, `target_region`
- `trigger_reason`, `status`
- `initiated_at`, `completed_at`, `verified_at`
- `duration_seconds`, `affected_tenants` (UUID[])

#### `recovery_procedures`
**Purpose:** Disaster recovery procedures  
**Key Columns:**
- `procedure_id` (UUID, PK)
- `procedure_name`, `procedure_type`
- `description`, `steps` (JSONB)
- `estimated_rto_minutes`, `estimated_rpo_minutes`
- `last_tested_at`, `test_status`

#### `risks`
**Purpose:** Risk tracking  
**Key Columns:**
- `risk_id` (UUID, PK)
- `tenant_id` (FK)
- `category`, `title`, `description`
- `impact` (1-5), `probability` (1-5)
- `risk_score` (computed: impact * probability)
- `severity`, `status`, `owner`
- `mitigation_strategies` (JSONB), `next_review_date`

#### `risk_mitigations`
**Purpose:** Risk mitigation actions  
**Key Columns:**
- `mitigation_id` (UUID, PK)
- `risk_id` (FK)
- `description`, `mitigation_type`, `status`
- `due_date`, `owner`, `completed_at`

#### `risk_reviews`
**Purpose:** Risk review history  
**Key Columns:**
- `review_id` (UUID, PK)
- `risk_id` (FK)
- `review_date`, `reviewer`, `review_notes`
- `impact_updated`, `probability_updated`, `status_updated`
- `next_review_date`

---

### Optimization & Growth

#### `experiments`
**Purpose:** A/B testing experiments  
**Key Columns:**
- `experiment_id` (UUID, PK)
- `tenant_id` (FK)
- `experiment_name`, `experiment_type`
- `status`, `hypothesis`
- `variants` (JSONB), `traffic_allocation`
- `start_date`, `end_date`, `winner_variant`
- `statistical_significance`

#### `experiment_assignments`
**Purpose:** User-to-variant assignments  
**Key Columns:**
- `assignment_id` (UUID, PK)
- `tenant_id`, `experiment_id`, `user_id` (FKs)
- `variant`, `assigned_at`

#### `experiment_events`
**Purpose:** Experiment event tracking  
**Key Columns:**
- `event_id` (UUID, PK)
- `tenant_id`, `experiment_id`, `assignment_id` (FKs)
- `event_type`, `event_value`, `timestamp`

#### `churn_events`
**Purpose:** Churn tracking  
**Key Columns:**
- `churn_id` (UUID, PK)
- `tenant_id`, `user_id` (FKs)
- `churn_type`, `churn_date`, `churn_reason`
- `predicted_probability`, `predicted_at`
- `intervention_applied`, `intervention_type`, `intervention_result`

#### `onboarding_steps`
**Purpose:** Onboarding step definitions  
**Key Columns:**
- `step_id` (UUID, PK)
- `tenant_id` (FK)
- `step_name`, `step_order` (UNIQUE per tenant)
- `step_type`, `required`, `completion_criteria` (JSONB)
- `enabled`

#### `onboarding_progress`
**Purpose:** User onboarding progress  
**Key Columns:**
- `progress_id` (UUID, PK)
- `tenant_id`, `user_id`, `step_id` (FKs)
- `status`, `started_at`, `completed_at`
- `time_spent_seconds`, `dropoff_reason`

#### `scheduled_tasks`
**Purpose:** Background task scheduling  
**Key Columns:**
- `task_id` (UUID, PK)
- `task_name`, `task_type`
- `schedule_cron`, `schedule_interval_seconds`
- `next_run_at`, `last_run_at`
- `status`, `priority`, `max_retries`, `retry_count`
- `error_message`

---

## Key Relationships

### Core Hierarchy
```
tenants
  ├── users
  │   ├── podcasts
  │   │   └── episodes
  │   │       └── transcripts
  │   ├── campaigns
  │   ├── sponsors
  │   └── reports
  └── [all other tenant-scoped tables]
```

### Attribution Flow
```
campaigns
  ├── attribution_events (hypertable)
  ├── attribution_models
  ├── attribution_paths
  └── conversion_events
```

### Time-Series Data (TimescaleDB Hypertables)
- `listener_events` - Partitioned by `timestamp`
- `attribution_events` - Partitioned by `timestamp`
- `listener_metrics` - Partitioned by `timestamp`

---

## Indexes & Performance

**Key Indexes:**
- All foreign keys indexed
- `tenant_id` indexed on all tenant-scoped tables (for RLS)
- Time-series tables: Composite indexes on `(podcast_id, timestamp DESC)`
- Unique constraints: `(tenant_id, slug)`, `(tenant_id, integration_name)`, etc.

**Materialized Views:**
- `listener_events_hourly` - Continuous aggregate (1-hour buckets)
- `listener_events_daily` - Continuous aggregate (1-day buckets)

---

## Row-Level Security (RLS)

**All tenant-scoped tables** have RLS enabled with policies:
```sql
CREATE POLICY tenant_isolation_<table> ON <table>
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
```

**Context Function:**
```sql
CREATE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_uuid::TEXT, TRUE);
END;
$$ LANGUAGE plpgsql;
```

---

## Notes

1. **Duplicate Tables:** Some tables appear in multiple migrations (e.g., `referrals` in both partnerships and monetization migrations). The master migration should consolidate these.

2. **Migration Order:** Migrations have dependencies:
   - `001_initial_schema.sql` must run first
   - `002_timescale_hypertables.sql` requires tables from `001`
   - `003_multi_tenant_schema.sql` adds `tenant_id` to existing tables
   - All subsequent migrations depend on `003`

3. **Idempotency:** Most migrations use `IF NOT EXISTS` clauses, making them safe to re-run.

4. **TimescaleDB Requirements:** The database must have TimescaleDB extension installed before running migrations.

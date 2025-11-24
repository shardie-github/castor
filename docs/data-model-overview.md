# Data Model Overview

This document provides a high-level overview of the database schema, including all tables, their purposes, key columns, and relationships.

## Schema Architecture

The database uses **PostgreSQL 15 with TimescaleDB extension** and implements a **multi-tenant architecture** with Row-Level Security (RLS) for tenant isolation.

### Key Design Patterns

1. **Multi-Tenancy**: All tenant-scoped tables include `tenant_id` foreign key to `tenants` table
2. **Time-Series Data**: Event tables (`listener_events`, `attribution_events`, `listener_metrics`) are TimescaleDB hypertables
3. **UUID Primary Keys**: All tables use UUID primary keys generated via `uuid_generate_v4()`
4. **Soft Deletes**: Some tables use `deleted_at` timestamps (not shown in all tables)
5. **Audit Fields**: Most tables include `created_at` and `updated_at` timestamps

## Core Tables

### Multi-Tenancy Foundation

#### `tenants`
- **Purpose**: Root table for multi-tenant isolation
- **Key Columns**: `id` (UUID), `name`, `slug` (unique)
- **Relationships**: Referenced by all tenant-scoped tables via `tenant_id`

#### `tenant_settings`
- **Purpose**: Per-tenant configuration storage
- **Key Columns**: `tenant_id` (FK to tenants), `settings` (JSONB)
- **Relationships**: One-to-one with `tenants`

#### `tenant_quotas`
- **Purpose**: Resource limits per tenant
- **Key Columns**: `tenant_id` (FK to tenants), `max_users`, `max_podcasts`, `max_campaigns`
- **Relationships**: One-to-one with `tenants`

### User Management

#### `users`
- **Purpose**: User accounts
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `email` (unique), `password_hash`, `email_verified`, `stripe_customer_id`, `stripe_subscription_id`
- **Relationships**: 
  - Belongs to `tenants`
  - Has many `user_roles`, `user_email_preferences`, `user_metrics`

#### `user_email_preferences`
- **Purpose**: Email notification preferences per user
- **Key Columns**: `user_id` (FK to users), `marketing_emails`, `product_updates`, `security_alerts`
- **Relationships**: One-to-one with `users`

#### `user_metrics`
- **Purpose**: User-level analytics metrics
- **Key Columns**: `user_id` (FK to users), `metric_name`, `metric_value`, `metric_data` (JSONB)
- **Relationships**: Many-to-one with `users`
- **Primary Key**: Composite (`user_id`, `metric_name`)

### Content Management

#### `podcasts`
- **Purpose**: Podcast entities
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `description`, `rss_feed_url`, `website_url`
- **Relationships**: 
  - Belongs to `tenants`
  - Has many `episodes`, `marketplace_listings`

#### `episodes`
- **Purpose**: Individual podcast episodes
- **Key Columns**: `id` (UUID), `podcast_id` (FK), `title`, `description`, `episode_number`, `published_at`, `duration_seconds`, `audio_url`
- **Relationships**: 
  - Belongs to `podcasts`
  - Has many `listener_events`, `attribution_events`, `listener_metrics`, `transcripts`, `ad_units`

#### `transcripts`
- **Purpose**: Episode transcript storage
- **Key Columns**: `episode_id` (FK to episodes), `content`, `language`, `confidence_score`
- **Relationships**: One-to-one with `episodes`

### Campaign Management

#### `sponsors`
- **Purpose**: Advertiser/sponsor entities
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `website_url`, `logo_url`
- **Relationships**: 
  - Belongs to `tenants`
  - Has many `campaigns`, `io_bookings`

#### `campaigns`
- **Purpose**: Marketing campaigns
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `sponsor_id` (FK), `name`, `description`, `start_date`, `end_date`, `stage`, `stage_changed_at`
- **Relationships**: 
  - Belongs to `tenants` and `sponsors`
  - Has many `attribution_events`, `attribution_paths`, `attribution_analytics`, `ad_units`, `io_bookings`, `matches`

#### `ad_units`
- **Purpose**: Ad placement within episodes
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `campaign_id` (FK), `episode_id` (FK), `unit_type`, `position_seconds`, `duration_seconds`
- **Relationships**: Belongs to `campaigns` and `episodes`

#### `io_bookings`
- **Purpose**: Insertion order bookings
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `campaign_id` (FK), `sponsor_id` (FK), `booking_date`, `promo_code`, `vanity_url`
- **Relationships**: Belongs to `campaigns` and `sponsors`

#### `matches`
- **Purpose**: AI-powered sponsor-podcast matching
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `advertiser_id`, `campaign_id` (FK), `score`, `rationale`, `signals` (JSONB)
- **Relationships**: Belongs to `campaigns`

## Time-Series Tables (TimescaleDB Hypertables)

### `listener_events`
- **Purpose**: Raw listener interaction events
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `episode_id` (FK), `listener_id`, `event_type`, `event_data` (JSONB), `occurred_at`
- **Hypertable**: Partitioned by `occurred_at` (1-day chunks)
- **Retention**: 2 years
- **Relationships**: Belongs to `episodes`

### `attribution_events`
- **Purpose**: Campaign attribution events
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `campaign_id` (FK), `episode_id` (FK), `listener_id`, `attribution_type`, `attribution_data` (JSONB), `occurred_at`
- **Hypertable**: Partitioned by `occurred_at` (1-day chunks)
- **Relationships**: Belongs to `campaigns` and `episodes`
- **Related**: `attribution_event_metadata` (one-to-one)

### `attribution_event_metadata`
- **Purpose**: Detailed metadata for attribution events
- **Key Columns**: `event_id` (FK to attribution_events), `metadata` (JSONB)
- **Relationships**: One-to-one with `attribution_events`

### `listener_metrics`
- **Purpose**: Aggregated listener metrics
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `episode_id` (FK), `metric_date`, `metric_name`, `metric_value`, `metric_data` (JSONB)
- **Hypertable**: Partitioned by `metric_date` (1-day chunks)
- **Relationships**: Belongs to `episodes`

## Continuous Aggregates (Materialized Views)

### `listener_events_hourly`
- **Purpose**: Hourly aggregated listener events
- **Aggregation**: Groups by hour, tenant, episode, event type
- **Metrics**: `event_count`, `unique_listeners`
- **Refresh Policy**: Every 1 hour, 3-hour lookback

### `listener_events_daily`
- **Purpose**: Daily aggregated listener events
- **Aggregation**: Groups by day, tenant, episode, event type
- **Metrics**: `event_count`, `unique_listeners`
- **Refresh Policy**: Every 1 day, 3-day lookback

### `metrics_daily`
- **Purpose**: Daily aggregated metrics from listener_metrics and attribution_events
- **Aggregation**: Groups by day, tenant, episode, metric_name
- **Metrics**: `total_value`, `avg_value`, `record_count`

## Authentication & Authorization

### Authentication Tables

#### `email_verification_tokens`
- **Purpose**: Email verification token storage
- **Key Columns**: `id` (UUID), `user_id` (FK), `token` (unique), `expires_at`, `used_at`

#### `password_reset_tokens`
- **Purpose**: Password reset token storage
- **Key Columns**: `id` (UUID), `user_id` (FK), `token` (unique), `expires_at`, `used_at`

#### `refresh_tokens`
- **Purpose**: JWT refresh token storage
- **Key Columns**: `id` (UUID), `user_id` (FK), `token` (unique), `expires_at`, `revoked_at`

### Authorization Tables (RBAC/ABAC)

#### `roles`
- **Purpose**: Role definitions
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `description`
- **Relationships**: Has many `user_roles`, `role_permissions`

#### `permissions`
- **Purpose**: Permission definitions
- **Key Columns**: `id` (UUID), `name` (unique), `description`, `resource_type`, `action`

#### `user_roles`
- **Purpose**: User-role assignments
- **Key Columns**: `user_id` (FK), `role_id` (FK), `assigned_at`, `assigned_by` (FK to users)
- **Primary Key**: Composite (`user_id`, `role_id`)

#### `role_permissions`
- **Purpose**: Role-permission grants
- **Key Columns**: `role_id` (FK), `permission_id` (FK), `granted_at`
- **Primary Key**: Composite (`role_id`, `permission_id`)

#### `resource_ownership`
- **Purpose**: Resource ownership tracking (ABAC)
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `resource_type`, `resource_id` (UUID), `owner_id` (FK to users)
- **Unique**: (`resource_type`, `resource_id`)

#### `access_control_policies`
- **Purpose**: ABAC policy definitions
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `description`, `policy_definition` (JSONB), `enabled`

#### `access_logs`
- **Purpose**: Access attempt logging
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `resource_type`, `resource_id`, `action`, `allowed`, `reason`, `ip_address`, `user_agent`, `occurred_at`

## Advanced Attribution

#### `attribution_models`
- **Purpose**: Attribution model configurations
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `model_type`, `configuration` (JSONB), `enabled`

#### `attribution_paths`
- **Purpose**: Multi-touch attribution paths
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `campaign_id` (FK), `listener_id`, `touchpoints` (JSONB), `conversion_event_id` (FK)

#### `attribution_validations`
- **Purpose**: Attribution event validation results
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `attribution_event_id` (FK), `validation_type`, `passed`, `details` (JSONB)

#### `attribution_analytics`
- **Purpose**: Daily attribution analytics
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `campaign_id` (FK), `analysis_date`, `metrics` (JSONB)
- **Unique**: (`tenant_id`, `campaign_id`, `analysis_date`)

## Security & Compliance

#### `audit_logs`
- **Purpose**: Audit trail for all data changes
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `action`, `resource_type`, `resource_id`, `changes` (JSONB), `ip_address`, `user_agent`, `occurred_at`

#### `security_events`
- **Purpose**: Security event logging
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `event_type`, `severity`, `details` (JSONB), `ip_address`, `user_agent`, `occurred_at`

#### `gdpr_requests`
- **Purpose**: GDPR compliance request tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `request_type`, `status`, `requested_at`, `completed_at`, `notes`

#### `api_keys`
- **Purpose**: API key management
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `key_hash` (unique), `name`, `scopes` (array), `last_used_at`, `expires_at`, `revoked_at`

## Integrations

#### `integrations`
- **Purpose**: Third-party integration configurations
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `integration_type`, `status`, `configuration` (JSONB)

#### `integration_tokens`
- **Purpose**: Encrypted integration tokens
- **Key Columns**: `id` (UUID), `integration_id` (FK), `token_type`, `token_value_encrypted`, `expires_at`

#### `webhooks`
- **Purpose**: Webhook endpoint configurations
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `integration_id` (FK), `url`, `event_types` (array), `secret`, `enabled`

#### `integration_sync_logs`
- **Purpose**: Integration synchronization logs
- **Key Columns**: `id` (UUID), `integration_id` (FK), `sync_type`, `status`, `records_synced`, `error_message`, `started_at`, `completed_at`

## Monetization

#### `agencies`
- **Purpose**: Agency partner management
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `contact_email`, `commission_rate`

#### `affiliates`
- **Purpose**: Affiliate partner management
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `contact_email`, `commission_rate`

#### `referrals`
- **Purpose**: User referral tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `referrer_id` (FK to users), `referred_email`, `status`

#### `referral_commissions`
- **Purpose**: Referral commission tracking
- **Key Columns**: `id` (UUID), `referral_id` (FK), `amount`, `status`, `paid_at`

#### `ai_token_usage`
- **Purpose**: AI token consumption tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `token_count`, `usage_type`

#### `ai_token_balances`
- **Purpose**: AI token balance per user
- **Key Columns**: `tenant_id` (FK), `user_id` (FK), `balance`
- **Primary Key**: Composite (`tenant_id`, `user_id`)

#### `api_usage`
- **Purpose**: API usage tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `api_key_id` (FK), `endpoint`, `method`, `status_code`, `response_time_ms`, `occurred_at`

#### `white_label_settings`
- **Purpose**: White-label branding configuration
- **Key Columns**: `tenant_id` (FK), `brand_name`, `logo_url`, `primary_color`, `custom_domain`

#### `subscription_tiers`
- **Purpose**: Subscription tier definitions
- **Key Columns**: `id` (UUID), `name` (unique), `description`, `price_monthly`, `price_yearly`, `features` (JSONB)

#### `billing_transactions`
- **Purpose**: Billing transaction history
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `subscription_tier_id` (FK), `amount`, `currency`, `status`, `stripe_transaction_id`, `occurred_at`

## Optimization

#### `experiments`
- **Purpose**: A/B test experiment definitions
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `description`, `status`, `start_date`, `end_date`

#### `experiment_assignments`
- **Purpose**: User experiment variant assignments
- **Key Columns**: `experiment_id` (FK), `user_id` (FK), `variant`, `assigned_at`
- **Primary Key**: Composite (`experiment_id`, `user_id`)

#### `experiment_events`
- **Purpose**: Experiment event tracking
- **Key Columns**: `id` (UUID), `experiment_id` (FK), `user_id` (FK), `event_type`, `event_data` (JSONB), `occurred_at`

#### `churn_events`
- **Purpose**: User churn event tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `user_id` (FK), `churn_reason`, `churn_data` (JSONB), `occurred_at`

#### `onboarding_steps`
- **Purpose**: Onboarding step definitions
- **Key Columns**: `id` (UUID), `step_key` (unique), `step_name`, `description`, `order_index`, `required`

#### `onboarding_progress`
- **Purpose**: User onboarding progress tracking
- **Key Columns**: `user_id` (FK), `step_id` (FK), `completed_at`, `skipped_at`
- **Primary Key**: Composite (`user_id`, `step_id`)

## ETL & Business Domain

#### `etl_imports`
- **Purpose**: ETL import job tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `import_type`, `source`, `status`, `records_imported`, `error_message`, `started_at`, `completed_at`

## Partnerships

#### `partners`
- **Purpose**: Partner entity management
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `name`, `partner_type`, `contact_email`

#### `partner_integrations`
- **Purpose**: Partner integration configurations
- **Key Columns**: `id` (UUID), `partner_id` (FK), `integration_type`, `configuration` (JSONB), `status`

#### `marketplace_listings`
- **Purpose**: Marketplace podcast listings
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `podcast_id` (FK), `listing_type`, `status`, `pricing` (JSONB)

#### `marketplace_revenue`
- **Purpose**: Marketplace revenue tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `listing_id` (FK), `amount`, `currency`, `transaction_date`

## Disaster Recovery

#### `backup_records`
- **Purpose**: Database backup tracking
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `backup_type`, `backup_location`, `size_bytes`, `status`, `started_at`, `completed_at`

#### `replication_status`
- **Purpose**: Database replication status
- **Key Columns**: `id` (UUID), `replica_name` (unique), `status`, `lag_seconds`, `last_sync_at`

#### `failover_events`
- **Purpose**: Failover event tracking
- **Key Columns**: `id` (UUID), `event_type`, `source_node`, `target_node`, `status`, `occurred_at`, `completed_at`

#### `recovery_procedures`
- **Purpose**: Disaster recovery procedure definitions
- **Key Columns**: `id` (UUID), `procedure_name` (unique), `description`, `steps` (JSONB), `last_tested_at`

## Reports

#### `reports`
- **Purpose**: Generated report storage
- **Key Columns**: `id` (UUID), `tenant_id` (FK), `report_type`, `report_data` (JSONB), `generated_at`, `created_by` (FK to users)

## Database Functions

### `set_tenant_context(tenant_uuid UUID)`
- **Purpose**: Sets tenant context for Row-Level Security (RLS)
- **Usage**: Called before queries to enable tenant isolation

### `refresh_metrics_daily()`
- **Purpose**: Refreshes the `metrics_daily` materialized view
- **Usage**: Called by scheduled jobs to update daily metrics

## Row-Level Security (RLS)

All tenant-scoped tables have RLS enabled with `tenant_isolation` policies that filter rows based on `current_setting('app.current_tenant', TRUE)::UUID` or `current_setting('app.current_tenant_id', TRUE)::UUID`.

System-level tables (`replication_status`, `failover_events`) have open policies for system access.

## Indexes

The schema includes indexes on:
- Foreign keys (for join performance)
- Frequently queried columns (`email`, `slug`, `status`, `stage`)
- Time-series columns (`occurred_at`, `metric_date`)
- Composite indexes for common query patterns

## Extensions

- `uuid-ossp`: UUID generation
- `pg_trgm`: Trigram text search
- `pgcrypto`: Cryptographic functions
- `timescaledb`: Time-series database extension

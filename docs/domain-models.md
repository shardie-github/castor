# Domain Models

This document describes the core domain models and business logic of the Podcast Analytics & Sponsorship Platform.

## Core Entities

### Tenant

**Purpose:** Multi-tenant isolation foundation

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (String) - Organization name
- `slug` (String) - URL-friendly identifier
- `domain` (String, optional) - Custom domain
- `subscription_tier` (Enum) - free, pro, enterprise
- `status` (Enum) - active, suspended, cancelled
- `billing_email` (String, optional) - Billing contact
- `metadata` (JSONB) - Flexible configuration
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Each tenant is completely isolated
- Tenant context required for all operations
- Quotas enforced per tenant
- Settings scoped to tenant

**Related Entities:**
- Users (many-to-one)
- Podcasts (many-to-one)
- Campaigns (many-to-one)
- Sponsors (many-to-one)

---

### User

**Purpose:** User accounts within tenants

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `email` (String) - Unique email address
- `password_hash` (String) - Bcrypt hash
- `name` (String) - Display name
- `email_verified` (Boolean) - Email verification status
- `stripe_customer_id` (String, optional) - Stripe customer
- `stripe_subscription_id` (String, optional) - Stripe subscription
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Users belong to exactly one tenant
- Email must be unique across system
- Password requirements enforced
- Email verification required for some operations
- Stripe integration for billing

**Related Entities:**
- Tenant (many-to-one)
- Roles (many-to-many via user_roles)
- Email Preferences (one-to-one)
- User Metrics (one-to-many)

---

### Podcast

**Purpose:** Podcast definitions

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `name` (String) - Podcast name
- `description` (Text, optional) - Description
- `rss_feed_url` (String, optional) - RSS feed URL
- `website_url` (String, optional) - Website URL
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Belongs to exactly one tenant
- RSS feed URL used for ingestion
- Episodes linked to podcast

**Related Entities:**
- Tenant (many-to-one)
- Episodes (one-to-many)
- Campaigns (many-to-many via campaign_episodes)

---

### Episode

**Purpose:** Individual podcast episodes

**Attributes:**
- `id` (UUID) - Unique identifier
- `podcast_id` (UUID) - Parent podcast
- `title` (String) - Episode title
- `description` (Text, optional) - Episode description
- `episode_number` (Integer, optional) - Episode number
- `published_at` (Timestamp, optional) - Publication date
- `duration_seconds` (Integer, optional) - Duration
- `audio_url` (String, optional) - Audio file URL
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Belongs to exactly one podcast
- Used for analytics and attribution
- Published date affects analytics queries

**Related Entities:**
- Podcast (many-to-one)
- Listener Events (one-to-many)
- Attribution Events (one-to-many)

---

### Sponsor

**Purpose:** Advertiser/sponsor information

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `name` (String) - Sponsor name
- `website_url` (String, optional) - Website
- `logo_url` (String, optional) - Logo image URL
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Belongs to exactly one tenant
- Used in campaigns
- Can be matched with podcasts

**Related Entities:**
- Tenant (many-to-one)
- Campaigns (one-to-many)

---

### Campaign

**Purpose:** Advertising campaigns

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `sponsor_id` (UUID, optional) - Associated sponsor
- `name` (String) - Campaign name
- `description` (Text, optional) - Description
- `start_date` (Date, optional) - Start date
- `end_date` (Date, optional) - End date
- `stage` (Enum) - draft, active, paused, completed, cancelled
- `stage_changed_at` (Timestamp, optional) - Last stage change
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Belongs to exactly one tenant
- Can be associated with sponsor
- Stage transitions tracked
- Used for attribution tracking

**Related Entities:**
- Tenant (many-to-one)
- Sponsor (many-to-one)
- Attribution Events (one-to-many)
- IO Bookings (one-to-many)

---

## Time-Series Entities

### Listener Event

**Purpose:** Raw listener interaction events

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `episode_id` (UUID) - Associated episode
- `listener_id` (String) - Listener identifier
- `event_type` (String) - play, pause, complete, skip, etc.
- `event_data` (JSONB) - Additional event data
- `occurred_at` (Timestamp) - Event timestamp

**Business Rules:**
- Stored in TimescaleDB hypertable
- Partitioned by time (daily chunks)
- Used for analytics aggregation
- Retention policy: 2 years

**Related Entities:**
- Tenant (many-to-one)
- Episode (many-to-one)

---

### Attribution Event

**Purpose:** Attribution tracking events

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `campaign_id` (UUID) - Associated campaign
- `episode_id` (UUID) - Associated episode
- `listener_id` (String) - Listener identifier
- `attribution_type` (String) - click, conversion, etc.
- `attribution_data` (JSONB) - Attribution details
- `occurred_at` (Timestamp) - Event timestamp

**Business Rules:**
- Stored in TimescaleDB hypertable
- Used for ROI calculations
- Supports multiple attribution models

**Related Entities:**
- Tenant (many-to-one)
- Campaign (many-to-one)
- Episode (many-to-one)

---

## Security Entities

### Role

**Purpose:** User roles for RBAC

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `name` (String) - Role name
- `description` (String, optional) - Description
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Scoped to tenant
- Permissions assigned via role_permissions

**Related Entities:**
- Tenant (many-to-one)
- Permissions (many-to-many via role_permissions)
- Users (many-to-many via user_roles)

---

### Permission

**Purpose:** Granular permissions

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (String) - Permission name
- `resource` (String) - Resource type
- `action` (String) - Action (create, read, update, delete)
- `description` (String, optional) - Description
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- System-wide permissions
- Assigned to roles
- Checked via permission engine

**Related Entities:**
- Roles (many-to-many via role_permissions)

---

## Workflow Entities

### Workflow

**Purpose:** Automated workflow definitions

**Attributes:**
- `id` (UUID) - Unique identifier
- `tenant_id` (UUID) - Parent tenant
- `name` (String) - Workflow name
- `description` (String, optional) - Description
- `trigger_event` (String) - Event that triggers workflow
- `steps` (JSONB) - Workflow step definitions
- `enabled` (Boolean) - Whether workflow is active
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Scoped to tenant
- Triggered by events
- Steps executed sequentially
- Can be enabled/disabled

**Related Entities:**
- Tenant (many-to-one)
- Workflow Executions (one-to-many)

---

## Feature Flag Entity

### Feature Flag

**Purpose:** Feature flag configuration

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (String) - Flag name
- `description` (String, optional) - Description
- `enabled` (Boolean) - Default enabled state
- `tenant_id` (UUID, optional) - Tenant-specific override
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Business Rules:**
- Can be global or tenant-specific
- Tenant-specific overrides global
- Used to control feature availability

---

## Business Logic Patterns

### Multi-Tenancy

All entities are tenant-scoped:
- Every query includes tenant_id filter
- Row-level security (RLS) enforced
- Tenant context required for all operations

### Time-Series Data

Listener events and attribution events:
- Stored in TimescaleDB hypertables
- Partitioned by time
- Continuous aggregates for performance
- Retention policies for data lifecycle

### Attribution Models

Supported models:
- First Touch
- Last Touch
- Linear
- Time Decay
- Position Based

### Workflow Automation

- Event-driven workflows
- Step-by-step execution
- Error handling and retries
- Tenant-scoped execution

---

## Data Relationships

```
Tenant
├── Users
│   ├── Roles (via user_roles)
│   └── Permissions (via roles)
├── Podcasts
│   └── Episodes
│       └── Listener Events
├── Sponsors
│   └── Campaigns
│       └── Attribution Events
├── Workflows
│   └── Workflow Executions
└── Feature Flags
```

---

**Last Updated:** 2024-12-XX

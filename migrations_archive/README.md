# Legacy Migrations Archive

This directory contains the original migration files from the project's development history. These migrations have been consolidated into a single master migration file for easier database bootstrapping.

## Current Migration Strategy

**For new database setups**, use the master migration file:
- `db/migrations/99999999999999_master_schema.sql`

This master migration consolidates all schema changes into a single, idempotent file that can bootstrap a fresh database from zero to the complete schema state.

## Why Archive These?

The original migrations were created incrementally during development. While they represent the historical evolution of the schema, they can be complex to apply in order and may have dependencies or conflicts. The master migration provides:

1. **Simplicity**: One file to apply instead of many
2. **Idempotency**: Safe to run multiple times
3. **Clarity**: Complete schema in one place
4. **Reliability**: No dependency ordering issues

## When to Reference This Archive

- **Historical context**: Understanding how the schema evolved
- **Debugging**: Investigating when specific features were added
- **Migration analysis**: Reviewing the original migration logic
- **Documentation**: Understanding the development timeline

## Migration Files Included

- `001_initial_schema.sql` - Initial core tables
- `002_timescale_hypertables.sql` - TimescaleDB integration
- `003_multi_tenant_schema.sql` - Multi-tenancy foundation
- `004_advanced_attribution.sql` - Attribution models
- `005_ai_features.sql` - AI-related features
- `006_cost_tracking.sql` - Cost tracking tables
- `007_security_compliance.sql` - Security and compliance
- `008_disaster_recovery.sql` - Disaster recovery features
- `009_cross_platform_attribution.sql` - Cross-platform tracking
- `010_integrations.sql` - Third-party integrations
- `011_authorization.sql` - RBAC/ABAC authorization
- `012_optimization.sql` - Optimization features
- `013_risk_management.sql` - Risk management
- `014_partnerships.sql` - Partnership features
- `015_automation_self_service.sql` - Automation features
- `016_auth_tables.sql` - Authentication tables
- `017_stripe_fields.sql` - Stripe integration fields
- `018_email_preferences.sql` - Email preferences
- `029_user_metrics_table.sql` - User metrics
- `030_attribution_event_metadata_table.sql` - Attribution metadata
- `20251113_064143/` - Timestamped migration batch
- `20251113T114706Z/` - Timestamped migration batch

## Important Notes

- **Do not apply these migrations directly** to a fresh database
- Use the master migration (`db/migrations/99999999999999_master_schema.sql`) instead
- These files are preserved for reference only
- If you need to modify the schema, update the master migration file

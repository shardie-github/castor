# PR Backend Validation Workflow

This GitHub Actions workflow automatically runs backend validation scripts on every PR commit to ensure code quality, schema integrity, and system health without requiring CLI access.

## Overview

The `pr-backend-validation.yml` workflow runs automatically on pull requests to `main` or `develop` branches and executes the following validation checks:

1. **Migration Validation** - Validates migration file structure and syntax
2. **Environment Validation** - Checks that required environment variables are configured
3. **Schema Validation** - Validates database schema against expected structure
4. **Schema Health Check** - Checks for schema inconsistencies and issues
5. **Schema Drift Detection** - Compares local migrations with live Supabase schema
6. **Health Check** - Verifies infrastructure services are healthy
7. **Security Audit** - Runs security checks on the codebase
8. **Setup Validation** - Validates overall project setup

## Required GitHub Secrets

Ensure the following secrets are configured in your GitHub repository settings:

### Database Secrets
- `SUPABASE_DATABASE_URL` or `DATABASE_URL` - Full PostgreSQL connection string
- `STAGING_DATABASE_URL` - (Optional) Staging database URL for test migrations

### Supabase Secrets
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for admin operations)
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_SUPABASE_URL` - Public Supabase URL (for frontend)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Public Supabase anonymous key

### Application Secrets
- `JWT_SECRET` - JWT signing secret
- `ENCRYPTION_KEY` - Encryption key for sensitive data

### Optional Secrets
- `REDIS_URL` - Redis connection string
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Individual PostgreSQL connection variables
- `REDIS_HOST`, `REDIS_PORT` - Individual Redis connection variables

## How to Configure Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name listed above

## Running Migrations on PR

By default, migrations are **not** automatically run on PR commits. To trigger migrations:

### Option 1: PR Title
Include `[migrate]` in your PR title:
```
feat: Add new user table [migrate]
```

### Option 2: PR Label
Add the `run-migrations` label to your PR

When migrations are triggered, they will run against the staging database (configured via `STAGING_DATABASE_URL` secret or fallback to `SUPABASE_DATABASE_URL`).

## Workflow Behavior

### Automatic Execution
The workflow runs automatically when:
- A PR is opened targeting `main` or `develop`
- New commits are pushed to an existing PR
- Files in `src/`, `db/`, `scripts/`, or `requirements.txt` are changed

### Graceful Degradation
The workflow is designed to handle missing secrets gracefully:
- If database credentials are missing, schema checks are skipped with a warning
- If Supabase credentials are missing, drift detection is skipped
- Health checks continue with available services

### Job Dependencies
Jobs run in parallel where possible, with dependencies:
- Schema validation depends on migration validation
- Health checks depend on environment validation
- Migration execution depends on both migration and environment validation

## Viewing Results

1. Go to your PR on GitHub
2. Click on the **Checks** tab
3. View individual job results and logs
4. A summary is generated at the end showing all validation results

## Troubleshooting

### Workflow Not Running
- Ensure the workflow file is in `.github/workflows/` directory
- Check that your PR targets `main` or `develop` branch
- Verify that changed files match the path filters

### Schema Validation Failing
- Check that `DATABASE_URL` or `SUPABASE_DATABASE_URL` secret is set correctly
- Verify the database is accessible from GitHub Actions
- Review migration files for syntax errors

### Migrations Not Running
- Ensure PR title contains `[migrate]` or PR has `run-migrations` label
- Check that `STAGING_DATABASE_URL` or `SUPABASE_DATABASE_URL` is configured
- Verify database credentials have necessary permissions

### Health Check Failing
- Review service connection strings in secrets
- Check that services (PostgreSQL, Redis) are accessible
- Verify network/firewall settings allow GitHub Actions IPs

## Manual Workflow Trigger

You can also trigger the workflow manually:
1. Go to **Actions** tab in GitHub
2. Select **PR Backend Validation** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Best Practices

1. **Always review migration validation** before merging PRs with database changes
2. **Use staging database** for test migrations to avoid affecting production
3. **Monitor schema drift** regularly to catch inconsistencies early
4. **Keep secrets updated** when rotating credentials
5. **Review security audit results** for any vulnerabilities

## Related Documentation

- [Database Migrations](../db/README.md)
- [Environment Setup](../ENVIRONMENT.md)
- [CI/CD Pipeline](../.github/workflows/ci.yml)

# Aurora Prime — Full Stack Autopilot

Aurora Prime is an autonomous full-stack orchestrator responsible for validating, healing, and deploying the entire application stack end-to-end across **GitHub → Supabase → Vercel → Expo**.

## Overview

Aurora Prime operates as a comprehensive system health checker and self-healing agent that:

- ✅ Verifies environment integrity across all services
- ✅ Repairs broken links and configuration mismatches
- ✅ Syncs database schema and runs migrations
- ✅ Validates deployments across all platforms
- ✅ Ensures secrets alignment from GitHub Secrets
- ✅ Detects and fixes schema drift
- ✅ Provides comprehensive status reports

## Architecture

```
GitHub Secrets (Source of Truth)
    ↓
Aurora Prime Orchestrator
    ├──→ Supabase (Database & Backend)
    ├──→ Vercel (Frontend Deployment)
    ├──→ Expo (Mobile App)
    └──→ GitHub Actions (CI/CD)
```

## Required GitHub Secrets

Aurora Prime expects the following secrets to be configured in your GitHub repository:

### Supabase Secrets
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for admin operations
- `SUPABASE_ANON_KEY` - Anonymous/public key for client access
- `NEXT_PUBLIC_SUPABASE_URL` - Public Supabase URL (for frontend)
- `EXPO_PUBLIC_SUPABASE_URL` - Public Supabase URL (for mobile)

### Vercel Secrets
- `VERCEL_TOKEN` - Vercel API token
- `VERCEL_ORG_ID` - Vercel organization ID (optional)
- `VERCEL_PROJECT_ID` - Vercel project ID (optional)

### Database Secrets
- `PRODUCTION_DATABASE_URL` - Production database connection string
- `DATABASE_URL` - Default database connection string

## Usage

### Manual Execution

Run Aurora Prime manually:

```bash
python scripts/aurora_prime.py
```

### Automated Execution

Aurora Prime runs automatically via GitHub Actions:

1. **Scheduled**: Every 6 hours via `aurora-doctor.yml`
2. **On Push**: Runs on pushes to `main` or `develop` branches
3. **Manual Trigger**: Can be triggered via `workflow_dispatch`

### GitHub Actions Integration

The Aurora Prime Doctor workflow (`.github/workflows/aurora-doctor.yml`) automatically:

- Checks environment secrets alignment
- Validates Supabase schema
- Verifies Vercel deployment
- Checks Expo configuration
- Reports status

## Features

### 1. Environment Verification

Aurora Prime verifies that:

- All GitHub Actions workflows use `${{ secrets.SECRET_NAME }}` format
- No hardcoded secrets exist in workflow files
- Frontend configuration references environment variables correctly
- No `.env` files are committed to the repository

**Auto-fixes:**
- Updates workflow files to use GitHub Secrets
- Adds missing environment variables to `next.config.js`
- Warns about committed `.env` files

### 2. Supabase Migration & Schema Health

Aurora Prime checks:

- Supabase CLI availability
- Migration files exist and are valid
- Schema drift detection (dry-run)
- RLS policies compilation
- Edge Functions deployment readiness

**Auto-fixes:**
- Creates Supabase configuration directory if missing
- Generates `supabase/config.toml` template
- Validates migration file structure

### 3. Vercel Frontend Deployment

Aurora Prime validates:

- Vercel project linkage
- Environment variables sync from GitHub Secrets
- Frontend build configuration
- Deployment branch alignment

**Auto-fixes:**
- Creates `vercel.json` if missing
- Updates Vercel environment variables
- Verifies project linkage

### 4. Expo Mobile App

Aurora Prime checks:

- Expo project configuration (`app.json`)
- EAS build configuration (`eas.json`)
- Environment variables for mobile
- OTA updates configuration

**Auto-fixes:**
- Creates `app.json` if missing
- Creates `eas.json` if missing
- Updates Expo environment variables

### 5. CI/CD Pipeline Autopilot

Aurora Prime validates:

- All GitHub Actions workflows
- Workflow permissions
- Secret usage patterns
- Error handling in workflows

**Auto-fixes:**
- Creates Aurora Prime Doctor workflow
- Adds missing permissions
- Fixes secret references

### 6. Self-Healing Logic

Aurora Prime automatically fixes:

- ✅ Missing configuration files
- ✅ Incorrect secret references
- ✅ Missing environment variables
- ✅ Workflow permission issues
- ✅ Configuration mismatches

## Status Report Format

Every run outputs a comprehensive status report:

```
AURORA PRIME — FULL SYSTEM STATUS
================================================================================

Supabase: [Healthy / FIXED / Needs Attention]
Vercel Deployment: [Healthy / FIXED / Needs Attention]
Expo (iOS/Android): [Healthy / FIXED / Needs Attention]
GitHub Actions: [Healthy / FIXED / Needs Attention]
Secrets Alignment: [Healthy / FIXED / Needs Attention]
Schema Drift: [None / Auto-repaired / Needs Manual Review]

Issues Found:
  - [List of detected issues]

Fixes Applied:
  ✓ [List of auto-applied fixes]

Recommended Next Actions:
  - [Actionable recommendations]
```

## Configuration Files

Aurora Prime creates/updates the following configuration files:

### Supabase
- `supabase/config.toml` - Supabase project configuration
- `supabase/.gitignore` - Git ignore rules

### Vercel
- `vercel.json` - Vercel deployment configuration

### Frontend
- `frontend/next.config.js` - Next.js configuration (updated with Supabase env vars)

### GitHub Actions
- `.github/workflows/aurora-doctor.yml` - Aurora Prime Doctor workflow

## Troubleshooting

### Aurora Prime reports "Needs Attention"

1. Check GitHub Secrets are configured correctly
2. Verify Supabase project is accessible
3. Ensure Vercel project is linked
4. Review the detailed logs for specific issues

### Schema Drift Detected

1. Review the drift report
2. Generate migration file for differences
3. Run migrations manually if needed
4. Re-run Aurora Prime to verify

### Secrets Not Aligned

1. Verify all secrets exist in GitHub repository settings
2. Check workflow files use `${{ secrets.SECRET_NAME }}` format
3. Ensure no hardcoded values exist
4. Re-run Aurora Prime

## Best Practices

1. **Never commit `.env` files** - All secrets should come from GitHub Secrets
2. **Use consistent naming** - Follow the secret naming convention
3. **Review auto-fixes** - Always review what Aurora Prime changes
4. **Monitor Doctor runs** - Check Aurora Prime Doctor workflow results regularly
5. **Keep migrations clean** - Use `IF NOT EXISTS` in migrations to avoid conflicts

## Integration with Existing Workflows

Aurora Prime integrates seamlessly with existing CI/CD:

- **Pre-deployment**: Runs before production deployments
- **Post-deployment**: Validates deployment success
- **Scheduled**: Continuous health monitoring
- **On-demand**: Manual execution when needed

## Exit Codes

- `0` - All systems healthy
- `1` - Critical issues detected (Supabase, Vercel, or Secrets misaligned)

## Development

### Adding New Checks

To add new health checks:

1. Add check method to `AuroraPrime` class
2. Call from `run_full_system_check()`
3. Update status report format
4. Add to Doctor workflow if needed

### Testing

```bash
# Run locally (without actual API calls)
python scripts/aurora_prime.py

# Run with actual API calls (requires secrets)
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/aurora_prime.py
```

## License

Part of the Podcast Analytics & Sponsorship Platform.

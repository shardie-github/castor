# Aurora Prime Setup Guide

## Quick Start

Aurora Prime is now configured and ready to use. Follow these steps to complete setup:

## 1. Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id (optional)
VERCEL_PROJECT_ID=your-project-id (optional)
PRODUCTION_DATABASE_URL=postgresql://... (if using)
DATABASE_URL=postgresql://... (optional, for tests)
```

## 2. Verify Configuration

Run Aurora Prime locally to verify setup:

```bash
# Install dependencies
pip install httpx pyyaml

# Run Aurora Prime
python scripts/aurora_prime.py
```

## 3. Enable Aurora Prime Doctor

The Aurora Prime Doctor workflow is automatically configured to run:

- **Every 6 hours** (scheduled)
- **On push** to `main` or `develop` branches
- **Manually** via GitHub Actions UI

## 4. Review Created Files

Aurora Prime has created/updated the following files:

### Configuration Files
- `supabase/config.toml` - Supabase configuration template
- `vercel.json` - Vercel deployment configuration
- `frontend/next.config.js` - Updated with Supabase env vars

### Workflows
- `.github/workflows/aurora-doctor.yml` - Aurora Prime Doctor workflow
- `.github/workflows/deploy.yml` - Updated with Supabase migrations and Vercel deployment
- `.github/workflows/ci.yml` - Updated to use GitHub Secrets
- `.github/workflows/ci-cd.yml` - Updated to use GitHub Secrets

### Scripts
- `scripts/aurora_prime.py` - Main Aurora Prime orchestrator
- `scripts/check_schema_drift.py` - Schema drift detection script

## 5. Test the Setup

### Test Aurora Prime Locally

```bash
# Set environment variables (for testing)
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your-key
export SUPABASE_ANON_KEY=your-key

# Run Aurora Prime
python scripts/aurora_prime.py
```

### Test GitHub Actions

1. Push a commit to `main` or `develop` branch
2. Check GitHub Actions tab
3. Verify Aurora Prime Doctor runs successfully

## 6. Monitor Status

Aurora Prime will output status reports showing:

- ✅ **Healthy** - System is working correctly
- 🔧 **FIXED** - Issues were detected and auto-fixed
- ⚠️ **Needs Attention** - Manual intervention required

## Next Steps

1. **Link Vercel Project**: Run `vercel link` in the frontend directory
2. **Configure Supabase**: Update `supabase/config.toml` with your project ID
3. **Set up Expo** (if needed): Configure `app.json` and `eas.json`
4. **Review Workflows**: Ensure all workflows use GitHub Secrets correctly

## Troubleshooting

### "Secrets not found" error

- Verify secrets are set in GitHub repository settings
- Check secret names match exactly (case-sensitive)
- Ensure secrets are available to the workflow

### "Supabase CLI not found"

- Install Supabase CLI: `npm install -g supabase`
- Or use Supabase API directly (Aurora Prime supports both)

### "Vercel project not linked"

- Run `vercel link` in the frontend directory
- Or set `VERCEL_PROJECT_ID` secret in GitHub

### Schema drift detected

- Review the drift report
- Generate migration file for differences
- Run migrations manually if needed

## Documentation

See [docs/AURORA_PRIME.md](docs/AURORA_PRIME.md) for complete documentation.

## Support

For issues or questions:
1. Check Aurora Prime Doctor workflow logs
2. Review `docs/AURORA_PRIME.md`
3. Check GitHub Actions workflow status

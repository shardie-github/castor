# GitHub Secrets Setup Guide

**Last Updated:** 2024  
**Purpose:** Step-by-step guide for setting up GitHub Secrets for CI/CD

---

## Quick Setup

### Using GitHub CLI (Recommended)

```bash
# Install GitHub CLI if not installed
# macOS: brew install gh
# Linux: See https://cli.github.com/

# Authenticate
gh auth login

# Set required secrets
gh secret set PRODUCTION_DATABASE_URL
gh secret set STAGING_DATABASE_URL
gh secret set JWT_SECRET
gh secret set ENCRYPTION_KEY

# Set optional secrets (if needed)
gh secret set VERCEL_TOKEN
gh secret set SUPABASE_SERVICE_ROLE_KEY
```

### Using GitHub Web UI

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`
2. Click "New repository secret"
3. Enter name and value
4. Click "Add secret"
5. Repeat for all required secrets

---

## Required Secrets

### 1. Database URLs

**PRODUCTION_DATABASE_URL**
- Format: `postgresql://user:password@host:port/database`
- Get from: Supabase dashboard, AWS RDS console, or database provider
- Example: `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`

**STAGING_DATABASE_URL**
- Same format as production
- Use separate database for staging
- Example: `postgresql://postgres:password@db-staging.xxx.supabase.co:5432/postgres`

### 2. Security Secrets

**JWT_SECRET**
- Generate: `openssl rand -base64 32`
- Minimum 32 characters
- Use different secrets for staging and production
- Example: `aBc123XyZ456...` (32+ characters)

**ENCRYPTION_KEY**
- Generate: `openssl rand -base64 32`
- Minimum 32 characters
- Use different keys for staging and production
- Example: `xYz789AbC012...` (32+ characters)

---

## Optional Secrets

### Vercel (Frontend Deployment)

**VERCEL_TOKEN**
- Get from: Vercel Dashboard → Settings → Tokens
- Create token with "Full Account" scope
- Used for: Frontend deployment in CI

**VERCEL_ORG_ID** (Optional)
- Get from: Vercel Dashboard → Settings → General
- Used for: Organization-specific deployments

**VERCEL_PROJECT_ID** (Optional)
- Get from: Vercel project settings
- Used for: Project-specific deployments

### Supabase (If Using Supabase)

**SUPABASE_URL**
- Format: `https://[PROJECT-REF].supabase.co`
- Get from: Supabase Dashboard → Settings → API

**SUPABASE_SERVICE_ROLE_KEY**
- Get from: Supabase Dashboard → Settings → API → Service Role Key
- ⚠️ Keep secret - has admin access

**SUPABASE_ANON_KEY**
- Get from: Supabase Dashboard → Settings → API → Anon/Public Key
- Used for: Frontend Supabase client

### Frontend Environment Variables

**NEXT_PUBLIC_API_URL**
- Production: `https://api.yourdomain.com`
- Staging: `https://api-staging.yourdomain.com`
- Used in: Frontend build

**NEXT_PUBLIC_SUPABASE_URL**
- Same as `SUPABASE_URL` above
- Used in: Frontend Supabase client

### Redis (If Using Hosted Redis)

**PRODUCTION_REDIS_URL**
- Format: `redis://:password@host:port`
- Get from: Upstash, Redis Cloud, or Redis provider

**STAGING_REDIS_URL**
- Same format as production
- Use separate Redis instance for staging

### External Services

**STRIPE_SECRET_KEY**
- Get from: Stripe Dashboard → Developers → API Keys
- Format: `sk_live_...` (production) or `sk_test_...` (staging)

**SENDGRID_API_KEY**
- Get from: SendGrid Dashboard → Settings → API Keys

### Container Registry (If Using Docker)

**CONTAINER_REGISTRY**
- Example: `ghcr.io`, `docker.io`, `registry.example.com`

**REGISTRY_USERNAME**
- Docker Hub username, GitHub username, etc.

**REGISTRY_PASSWORD**
- Docker Hub password, GitHub token, etc.

---

## Environment-Specific Secrets

For production/staging environments, set secrets in:
**Settings → Secrets and variables → Actions → Environments**

### Production Environment

Set these secrets in the `production` environment:
- `PRODUCTION_DATABASE_URL`
- `PRODUCTION_REDIS_URL`
- Production `JWT_SECRET`
- Production `ENCRYPTION_KEY`
- Production API keys (Stripe, SendGrid, etc.)

### Staging Environment

Set these secrets in the `staging` environment:
- `STAGING_DATABASE_URL`
- `STAGING_REDIS_URL`
- Staging `JWT_SECRET`
- Staging `ENCRYPTION_KEY`
- Test API keys (Stripe test, SendGrid test, etc.)

---

## Validation Script

Run the validation script to check secrets:

```bash
./scripts/setup-github-secrets.sh --check
```

Or use GitHub CLI:

```bash
gh secret list
```

---

## Security Best Practices

1. **Never commit secrets** - Already in `.gitignore`
2. **Use different secrets** for staging and production
3. **Rotate secrets regularly** - Quarterly recommended
4. **Limit access** - Use GitHub Environments for production secrets
5. **Audit access** - Review who has access to secrets
6. **Use strong secrets** - Generate with `openssl rand -base64 32`

---

## Troubleshooting

### Secret Not Available in Workflow

**Issue:** Secret not found in GitHub Actions workflow

**Solutions:**
1. Verify secret name matches exactly (case-sensitive)
2. Check if secret is set in correct environment
3. Ensure workflow has access to environment
4. Check workflow syntax: `${{ secrets.SECRET_NAME }}`

### Secret Value Incorrect

**Issue:** Secret value is wrong or outdated

**Solutions:**
1. Update secret value in GitHub settings
2. Re-run workflow to pick up new value
3. Verify secret format (no extra spaces, correct encoding)

### Permission Denied

**Issue:** Cannot set secrets (permission denied)

**Solutions:**
1. Verify you have admin access to repository
2. Check organization settings (if org repo)
3. Use GitHub CLI with proper authentication

---

## Quick Reference

### Generate Secrets

```bash
# JWT Secret
openssl rand -base64 32

# Encryption Key
openssl rand -base64 32

# Database Password
openssl rand -base64 24
```

### Set Secrets (GitHub CLI)

```bash
# Required
echo "value" | gh secret set SECRET_NAME

# Or interactive
gh secret set SECRET_NAME
```

### List Secrets

```bash
gh secret list
```

### Delete Secret

```bash
gh secret delete SECRET_NAME
```

---

## Next Steps

1. Set all required secrets
2. Set optional secrets as needed
3. Configure environment-specific secrets
4. Run validation script: `./scripts/setup-github-secrets.sh --check`
5. Test CI/CD workflows

For detailed variable documentation, see: `docs/env-and-secrets.md`

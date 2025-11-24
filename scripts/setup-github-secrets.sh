#!/usr/bin/env bash
# GitHub Secrets Setup Script
#
# This script helps you set up GitHub Secrets for CI/CD.
# It validates that required secrets are documented and provides
# instructions for setting them in GitHub.
#
# Usage:
#   ./scripts/setup-github-secrets.sh
#   ./scripts/setup-github-secrets.sh --check  # Only check, don't prompt

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required secrets (from docs/env-and-secrets.md)
REQUIRED_SECRETS=(
    "PRODUCTION_DATABASE_URL"
    "STAGING_DATABASE_URL"
    "JWT_SECRET"
    "ENCRYPTION_KEY"
)

OPTIONAL_SECRETS=(
    "VERCEL_TOKEN"
    "VERCEL_ORG_ID"
    "VERCEL_PROJECT_ID"
    "NEXT_PUBLIC_API_URL"
    "NEXT_PUBLIC_SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_URL"
    "SUPABASE_SERVICE_ROLE_KEY"
    "PRODUCTION_REDIS_URL"
    "STAGING_REDIS_URL"
    "STRIPE_SECRET_KEY"
    "SENDGRID_API_KEY"
    "CONTAINER_REGISTRY"
    "REGISTRY_USERNAME"
    "REGISTRY_PASSWORD"
)

CHECK_ONLY="${1:-}"

echo -e "${BLUE}== GitHub Secrets Setup ==${NC}"
echo ""

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI (gh) is installed${NC}"
    
    # Check if authenticated
    if gh auth status &> /dev/null; then
        echo -e "${GREEN}✓ GitHub CLI is authenticated${NC}"
        USE_GH_CLI=true
    else
        echo -e "${YELLOW}⚠ GitHub CLI is not authenticated${NC}"
        echo "  Run: gh auth login"
        USE_GH_CLI=false
    fi
else
    echo -e "${YELLOW}⚠ GitHub CLI (gh) is not installed${NC}"
    echo "  Install: https://cli.github.com/"
    USE_GH_CLI=false
fi

echo ""
echo -e "${BLUE}Required Secrets:${NC}"
echo ""

for secret in "${REQUIRED_SECRETS[@]}"; do
    if [ "$USE_GH_CLI" = true ]; then
        if gh secret list | grep -q "^${secret}"; then
            echo -e "  ${GREEN}✓${NC} ${secret} (set)"
        else
            echo -e "  ${RED}✗${NC} ${secret} (missing)"
        fi
    else
        echo -e "  ${YELLOW}?${NC} ${secret} (check manually)"
    fi
done

echo ""
echo -e "${BLUE}Optional Secrets:${NC}"
echo ""

for secret in "${OPTIONAL_SECRETS[@]}"; do
    if [ "$USE_GH_CLI" = true ]; then
        if gh secret list | grep -q "^${secret}"; then
            echo -e "  ${GREEN}✓${NC} ${secret} (set)"
        else
            echo -e "  ${YELLOW}○${NC} ${secret} (optional)"
        fi
    else
        echo -e "  ${YELLOW}○${NC} ${secret} (optional)"
    fi
done

echo ""
echo -e "${BLUE}Setup Instructions:${NC}"
echo ""
echo "1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo ""
echo "2. Click 'New repository secret' for each required secret:"
echo ""

for secret in "${REQUIRED_SECRETS[@]}"; do
    echo "   - ${secret}"
done

echo ""
echo "3. Or use GitHub CLI (if authenticated):"
echo ""
echo "   gh secret set PRODUCTION_DATABASE_URL"
echo "   gh secret set STAGING_DATABASE_URL"
echo "   gh secret set JWT_SECRET"
echo "   gh secret set ENCRYPTION_KEY"
echo ""

if [ "$CHECK_ONLY" != "--check" ]; then
    echo -e "${BLUE}Generate Secrets:${NC}"
    echo ""
    echo "Generate JWT_SECRET:"
    echo "  openssl rand -base64 32"
    echo ""
    echo "Generate ENCRYPTION_KEY:"
    echo "  openssl rand -base64 32"
    echo ""
    echo "Get DATABASE_URL from your database provider:"
    echo "  - Supabase: Project Settings → Database → Connection string"
    echo "  - AWS RDS: RDS Console → Connect → Connection string"
    echo "  - DigitalOcean: Databases → Connection details"
    echo ""
fi

echo -e "${BLUE}Environment-Specific Secrets:${NC}"
echo ""
echo "For production/staging environments, set secrets in:"
echo "  Settings → Secrets and variables → Actions → Environments"
echo ""
echo "Environments:"
echo "  - production (for main branch)"
echo "  - staging (for develop branch)"
echo ""

if [ "$USE_GH_CLI" = true ] && [ "$CHECK_ONLY" != "--check" ]; then
    echo -e "${BLUE}Quick Setup (Interactive):${NC}"
    echo ""
    read -p "Do you want to set secrets interactively? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for secret in "${REQUIRED_SECRETS[@]}"; do
            if ! gh secret list | grep -q "^${secret}"; then
                echo ""
                echo "Setting ${secret}..."
                read -sp "Enter value for ${secret}: " value
                echo ""
                echo "$value" | gh secret set "$secret"
                echo -e "${GREEN}✓ Set ${secret}${NC}"
            fi
        done
    fi
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "For detailed documentation, see: docs/env-and-secrets.md"

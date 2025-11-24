#!/usr/bin/env bash
# Local Database Migration Script
# Applies the master migration to a local PostgreSQL database
#
# Usage:
#   ./scripts/db-migrate-local.sh
#   DATABASE_URL=postgresql://user:pass@localhost:5432/db ./scripts/db-migrate-local.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get database connection string
if [[ -n "${DATABASE_URL:-}" ]]; then
    PGURL="$DATABASE_URL"
elif [[ -n "${POSTGRES_HOST:-}" ]]; then
    # Build connection string from individual variables
    POSTGRES_USER="${POSTGRES_USER:-postgres}"
    POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
    POSTGRES_DATABASE="${POSTGRES_DATABASE:-podcast_analytics}"
    POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    PGURL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}"
else
    # Default local connection
    PGURL="postgresql://postgres:postgres@localhost:5432/podcast_analytics"
fi

# Migration file
MIGRATION_FILE="db/migrations/99999999999999_master_schema.sql"

# Check if migration file exists
if [[ ! -f "$MIGRATION_FILE" ]]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}" >&2
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client tools.${NC}" >&2
    exit 1
fi

echo -e "${GREEN}== Local Database Migration ==${NC}"
echo "Migration file: $MIGRATION_FILE"
echo "Database: $(echo "$PGURL" | sed 's/:[^:]*@/:***@/')"
echo ""

# Test database connection
echo "Testing database connection..."
if ! psql "$PGURL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to database. Please check your connection settings.${NC}" >&2
    echo "Connection string: $(echo "$PGURL" | sed 's/:[^:]*@/:***@/')"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Check if TimescaleDB extension is available
echo "Checking TimescaleDB extension..."
if psql "$PGURL" -c "SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';" | grep -q timescaledb; then
    echo -e "${GREEN}✓ TimescaleDB extension available${NC}"
else
    echo -e "${YELLOW}⚠ Warning: TimescaleDB extension not found. Some features may not work.${NC}"
    echo "  Install TimescaleDB: https://docs.timescale.com/install/latest/"
fi
echo ""

# Apply migration
echo "Applying migration..."
if psql "$PGURL" -v ON_ERROR_STOP=1 -f "$MIGRATION_FILE"; then
    echo ""
    echo -e "${GREEN}✓ Migration applied successfully${NC}"
    
    # Verify migration
    echo ""
    echo "Verifying migration..."
    TABLE_COUNT=$(psql "$PGURL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
    echo "Tables created: $TABLE_COUNT"
    
    # Check for key tables
    KEY_TABLES=("tenants" "users" "podcasts" "episodes" "campaigns" "listener_events")
    MISSING_TABLES=()
    for table in "${KEY_TABLES[@]}"; do
        if ! psql "$PGURL" -t -c "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table';" | grep -q 1; then
            MISSING_TABLES+=("$table")
        fi
    done
    
    if [[ ${#MISSING_TABLES[@]} -eq 0 ]]; then
        echo -e "${GREEN}✓ All key tables present${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: Some tables missing: ${MISSING_TABLES[*]}${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}✗ Migration failed${NC}" >&2
    exit 1
fi

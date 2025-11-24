#!/usr/bin/env bash
# Hosted Database Migration Script
# Applies the master migration to a hosted PostgreSQL database (Supabase, AWS RDS, etc.)
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:5432/db ./scripts/db-migrate-hosted.sh
#   POSTGRES_HOST=host POSTGRES_USER=user POSTGRES_PASSWORD=pass POSTGRES_DATABASE=db ./scripts/db-migrate-hosted.sh
#
# Safety: This script includes confirmation prompts for production databases

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${RED}Error: DATABASE_URL or POSTGRES_HOST must be set${NC}" >&2
    exit 1
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

# Extract hostname from connection string for display
DB_HOST=$(echo "$PGURL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_NAME=$(echo "$PGURL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${BLUE}== Hosted Database Migration ==${NC}"
echo "Migration file: $MIGRATION_FILE"
echo "Database host: $DB_HOST"
echo "Database name: $DB_NAME"
echo "Connection: $(echo "$PGURL" | sed 's/:[^:]*@/:***@/')"
echo ""

# Safety confirmation
if [[ "${SKIP_CONFIRMATION:-}" != "true" ]]; then
    echo -e "${YELLOW}⚠ WARNING: This will modify the database schema.${NC}"
    echo "Are you sure you want to proceed? (yes/no)"
    read -r CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "Migration cancelled."
        exit 0
    fi
    echo ""
fi

# Test database connection
echo "Testing database connection..."
if ! psql "$PGURL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to database. Please check your connection settings.${NC}" >&2
    echo "Connection string: $(echo "$PGURL" | sed 's/:[^:]*@/:***@/')"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Check PostgreSQL version
PG_VERSION=$(psql "$PGURL" -t -c "SELECT version();" | head -n 1)
echo "PostgreSQL version: $PG_VERSION"
echo ""

# Check if TimescaleDB extension is available
echo "Checking TimescaleDB extension..."
if psql "$PGURL" -c "SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';" | grep -q timescaledb; then
    echo -e "${GREEN}✓ TimescaleDB extension available${NC}"
else
    echo -e "${YELLOW}⚠ Warning: TimescaleDB extension not found.${NC}"
    echo "  Some features (hypertables, continuous aggregates) may not work."
    echo "  For Supabase: Contact support to enable TimescaleDB extension"
    echo "  For AWS RDS: Enable TimescaleDB via parameter groups"
    echo ""
    echo "Do you want to continue anyway? (yes/no)"
    read -r CONTINUE
    if [[ "$CONTINUE" != "yes" ]]; then
        echo "Migration cancelled."
        exit 0
    fi
fi
echo ""

# Check existing tables
EXISTING_TABLES=$(psql "$PGURL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
if [[ "$EXISTING_TABLES" -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Warning: Database already contains $EXISTING_TABLES tables.${NC}"
    echo "The migration is idempotent and safe to run, but please ensure you have a backup."
    echo ""
    if [[ "${SKIP_CONFIRMATION:-}" != "true" ]]; then
        echo "Do you have a backup? (yes/no)"
        read -r HAS_BACKUP
        if [[ "$HAS_BACKUP" != "yes" ]]; then
            echo -e "${RED}Please create a backup before proceeding. Migration cancelled.${NC}"
            exit 1
        fi
    fi
    echo ""
fi

# Apply migration
echo "Applying migration..."
echo -e "${BLUE}This may take a few minutes...${NC}"
echo ""

if psql "$PGURL" -v ON_ERROR_STOP=1 -f "$MIGRATION_FILE" 2>&1 | tee /tmp/migration_output.log; then
    echo ""
    echo -e "${GREEN}✓ Migration applied successfully${NC}"
    
    # Verify migration
    echo ""
    echo "Verifying migration..."
    TABLE_COUNT=$(psql "$PGURL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
    echo "Total tables: $TABLE_COUNT"
    
    # Check for key tables
    KEY_TABLES=("tenants" "users" "podcasts" "episodes" "campaigns" "listener_events" "attribution_events")
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
    
    # Check for TimescaleDB hypertables
    if psql "$PGURL" -c "SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';" | grep -q timescaledb; then
        HYPERTABLE_COUNT=$(psql "$PGURL" -t -c "SELECT COUNT(*) FROM _timescaledb_catalog.hypertable;" 2>/dev/null | tr -d ' ' || echo "0")
        if [[ "$HYPERTABLE_COUNT" -gt 0 ]]; then
            echo -e "${GREEN}✓ TimescaleDB hypertables created: $HYPERTABLE_COUNT${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Migration complete!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Migration failed${NC}" >&2
    echo "Check the output above for errors."
    echo "Migration log saved to: /tmp/migration_output.log"
    exit 1
fi

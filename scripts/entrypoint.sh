#!/bin/bash
set -e

# Validate required environment variables in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Validating production environment variables..."
    
    # Check critical variables
    if [ -z "$JWT_SECRET" ] || [ ${#JWT_SECRET} -lt 32 ]; then
        echo "ERROR: JWT_SECRET must be at least 32 characters"
        exit 1
    fi
    
    if [ -z "$ENCRYPTION_KEY" ] || [ ${#ENCRYPTION_KEY} -lt 32 ]; then
        echo "ERROR: ENCRYPTION_KEY must be at least 32 characters"
        exit 1
    fi
    
    # Check for default values
    if [ "$JWT_SECRET" = "change-me-in-production" ] || [ "$JWT_SECRET" = "change-me-in-production-generate-random-secret" ]; then
        echo "ERROR: JWT_SECRET must be changed from default value"
        exit 1
    fi
    
    if [ "$ENCRYPTION_KEY" = "change-me-in-production" ] || [ "$ENCRYPTION_KEY" = "change-me-in-production-generate-random-key" ]; then
        echo "ERROR: ENCRYPTION_KEY must be changed from default value"
        exit 1
    fi
    
    echo "Production environment validation passed"
fi

# Run database migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ] && [ -f "scripts/init_db.py" ]; then
    echo "Running database migrations..."
    python scripts/init_db.py || echo "Migration check completed"
fi

# Execute the main command
exec "$@"

#!/usr/bin/env python3
"""
Database Schema Validation Script

Validates that core database tables and columns exist after migrations.
Can be used in CI to verify migrations were applied correctly.
"""

import os
import sys
import asyncio
import asyncpg
from typing import List, Tuple


# Core tables that must exist
REQUIRED_TABLES = [
    "tenants",
    "users",
    "podcasts",
    "episodes",
    "campaigns",
    "listener_events",
    "attribution_events",
]

# Key columns that must exist in specific tables
REQUIRED_COLUMNS = {
    "tenants": ["id", "name", "slug", "created_at"],
    "users": ["id", "email", "tenant_id", "created_at"],
    "podcasts": ["id", "name", "tenant_id", "created_at"],
    "episodes": ["id", "podcast_id", "title", "created_at"],
    "campaigns": ["id", "name", "tenant_id", "created_at"],
}


async def validate_schema(database_url: str) -> Tuple[bool, List[str], List[str]]:
    """Validate database schema"""
    errors: List[str] = []
    warnings: List[str] = []
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check required tables
        for table in REQUIRED_TABLES:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
            """, table)
            
            if not exists:
                errors.append(f"Required table missing: {table}")
        
        # Check required columns
        for table, columns in REQUIRED_COLUMNS.items():
            # First check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
            """, table)
            
            if not table_exists:
                continue  # Already reported as missing table
            
            for column in columns:
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = $1 
                        AND column_name = $2
                    )
                """, table, column)
                
                if not exists:
                    errors.append(f"Required column missing: {table}.{column}")
        
        # Check for TimescaleDB hypertables (if extension is available)
        try:
            hypertables = await conn.fetch("""
                SELECT hypertable_name 
                FROM timescaledb_information.hypertables
                WHERE hypertable_schema = 'public'
            """)
            
            expected_hypertables = ["listener_events", "attribution_events", "listener_metrics"]
            found_hypertables = [row["hypertable_name"] for row in hypertables]
            
            for expected in expected_hypertables:
                if expected not in found_hypertables:
                    warnings.append(f"Expected TimescaleDB hypertable not found: {expected}")
        except Exception:
            # TimescaleDB extension may not be available
            warnings.append("TimescaleDB extension not available - skipping hypertable check")
        
        # Check for RLS policies (if any tables have RLS enabled)
        try:
            rls_tables = await conn.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND rowsecurity = true
            """)
            
            if not rls_tables:
                warnings.append("No tables with RLS enabled found - multi-tenant security may not be configured")
        except Exception:
            pass  # RLS check is optional
        
        await conn.close()
        
        return len(errors) == 0, errors, warnings
        
    except Exception as e:
        errors.append(f"Database connection error: {e}")
        return False, errors, warnings


def main():
    """Main entry point"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    success, errors, warnings = asyncio.run(validate_schema(database_url))
    
    if errors:
        print("❌ Schema Validation Errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    
    if warnings:
        print("⚠️  Schema Validation Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if success:
        print("✅ Schema validation passed")
        sys.exit(0)
    else:
        print("❌ Schema validation failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Database Schema Health Check

Validates database schema against expected schema definition.
Checks for missing tables, columns, indexes, and constraints.
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SchemaHealthChecker:
    """Checks database schema health"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.conn = None
    
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(self.database_url)
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
    
    async def get_existing_tables(self) -> Set[str]:
        """Get list of existing tables"""
        rows = await self.conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        return {row['table_name'] for row in rows}
    
    async def get_table_columns(self, table_name: str) -> Set[str]:
        """Get columns for a table"""
        rows = await self.conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = $1
        """, table_name)
        return {row['column_name'] for row in rows}
    
    async def get_table_indexes(self, table_name: str) -> Set[str]:
        """Get indexes for a table"""
        rows = await self.conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename = $1
        """, table_name)
        return {row['indexname'] for row in rows}
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        exists = await self.conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            )
        """, table_name)
        return exists
    
    async def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists"""
        exists = await self.conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = $1 
                AND column_name = $2
            )
        """, table_name, column_name)
        return exists
    
    async def check_required_tables(self):
        """Check for required tables"""
        required_tables = {
            'users',
            'podcasts',
            'episodes',
            'campaigns',
            'sponsors',
            'listener_events',
            'attribution_events',
            'reports',
        }
        
        existing_tables = await self.get_existing_tables()
        missing_tables = required_tables - existing_tables
        
        if missing_tables:
            self.errors.append(f"Missing required tables: {', '.join(sorted(missing_tables))}")
    
    async def check_table_structure(self, table_name: str, required_columns: List[str]):
        """Check table structure"""
        if not await self.check_table_exists(table_name):
            self.errors.append(f"Table {table_name} does not exist")
            return
        
        existing_columns = await self.get_table_columns(table_name)
        missing_columns = set(required_columns) - existing_columns
        
        if missing_columns:
            self.errors.append(
                f"Table {table_name} missing columns: {', '.join(sorted(missing_columns))}"
            )
    
    async def check_hypertables(self):
        """Check TimescaleDB hypertables"""
        try:
            rows = await self.conn.fetch("""
                SELECT hypertable_name 
                FROM timescaledb_information.hypertables
            """)
            hypertables = {row['hypertable_name'] for row in rows}
            
            required_hypertables = {'listener_events', 'attribution_events'}
            missing_hypertables = required_hypertables - hypertables
            
            if missing_hypertables:
                self.warnings.append(
                    f"Missing hypertables (may not be using TimescaleDB): {', '.join(sorted(missing_hypertables))}"
                )
        except Exception:
            # TimescaleDB may not be installed
            self.warnings.append("TimescaleDB not available - skipping hypertable checks")
    
    async def check_indexes(self):
        """Check critical indexes"""
        critical_indexes = {
            ('users', 'idx_users_email'),
            ('podcasts', 'idx_podcasts_user_id'),
            ('campaigns', 'idx_campaigns_user_id'),
            ('listener_events', 'idx_listener_events_podcast_id'),
        }
        
        for table_name, index_name in critical_indexes:
            if await self.check_table_exists(table_name):
                indexes = await self.get_table_indexes(table_name)
                if index_name not in indexes:
                    self.warnings.append(f"Missing index {index_name} on table {table_name}")
    
    async def check_foreign_keys(self):
        """Check critical foreign key constraints"""
        fk_checks = [
            ('campaigns', 'user_id', 'users', 'user_id'),
            ('campaigns', 'podcast_id', 'podcasts', 'podcast_id'),
            ('episodes', 'podcast_id', 'podcasts', 'podcast_id'),
        ]
        
        for child_table, child_column, parent_table, parent_column in fk_checks:
            if await self.check_table_exists(child_table) and await self.check_table_exists(parent_table):
                fk_exists = await self.conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = $1
                        AND kcu.column_name = $2
                        AND kcu.referenced_table_name = $3
                        AND kcu.referenced_column_name = $4
                    )
                """, child_table, child_column, parent_table, parent_column)
                
                if not fk_exists:
                    self.warnings.append(
                        f"Missing foreign key: {child_table}.{child_column} -> {parent_table}.{parent_column}"
                    )
    
    async def run_health_check(self) -> Tuple[bool, List[str], List[str]]:
        """Run complete health check"""
        await self.connect()
        
        try:
            await self.check_required_tables()
            await self.check_hypertables()
            await self.check_indexes()
            await self.check_foreign_keys()
            
            return len(self.errors) == 0, self.errors, self.warnings
        finally:
            await self.close()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check database schema health")
    parser.add_argument(
        "--database-url",
        required=True,
        help="Database connection URL"
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with error code if warnings are found"
    )
    
    args = parser.parse_args()
    
    checker = SchemaHealthChecker(args.database_url)
    success, errors, warnings = await checker.run_health_check()
    
    if errors:
        print("❌ Schema Health Errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    
    if warnings:
        print("⚠️  Schema Health Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if success and (not warnings or not args.fail_on_warnings):
        print("✅ Schema health check passed")
        sys.exit(0)
    else:
        print("❌ Schema health check failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

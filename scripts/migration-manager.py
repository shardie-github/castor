#!/usr/bin/env python3
"""
Incremental Migration Manager

Manages database migrations incrementally with versioning and rollback support.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import asyncpg
import asyncio


class Migration:
    """Represents a database migration"""
    
    def __init__(self, version: str, name: str, file_path: Path):
        self.version = version
        self.name = name
        self.file_path = file_path
        self.up_sql: Optional[str] = None
        self.down_sql: Optional[str] = None
    
    def load(self):
        """Load migration SQL from file"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Migration file not found: {self.file_path}")
        
        content = self.file_path.read_text()
        
        # Split into up and down migrations
        parts = re.split(r'--\s*DOWN\s+MIGRATION', content, flags=re.IGNORECASE)
        self.up_sql = parts[0].strip()
        
        if len(parts) > 1:
            self.down_sql = parts[1].strip()
        else:
            # If no down migration, create a warning
            self.down_sql = f"-- No rollback migration defined for {self.name}"


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, migrations_dir: Path, connection_string: str):
        self.migrations_dir = migrations_dir
        self.connection_string = connection_string
        self.migrations: List[Migration] = []
    
    def discover_migrations(self) -> List[Migration]:
        """Discover all migration files"""
        migrations = []
        
        if not self.migrations_dir.exists():
            self.migrations_dir.mkdir(parents=True, exist_ok=True)
            return migrations
        
        # Pattern: YYYYMMDDHHMMSS_description.sql
        pattern = re.compile(r'^(\d{14})_(.+)\.sql$')
        
        for file_path in sorted(self.migrations_dir.glob('*.sql')):
            match = pattern.match(file_path.name)
            if match:
                version = match.group(1)
                name = match.group(2)
                migration = Migration(version, name, file_path)
                migration.load()
                migrations.append(migration)
        
        return migrations
    
    async def ensure_migrations_table(self, conn):
        """Ensure migrations table exists"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(14) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                checksum VARCHAR(64)
            );
        """)
    
    async def get_applied_migrations(self, conn) -> List[str]:
        """Get list of applied migration versions"""
        rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
        return [row['version'] for row in rows]
    
    async def apply_migration(self, conn, migration: Migration):
        """Apply a single migration"""
        print(f"Applying migration {migration.version}: {migration.name}")
        
        # Calculate checksum
        import hashlib
        checksum = hashlib.md5(migration.up_sql.encode()).hexdigest()
        
        # Execute migration in a transaction
        async with conn.transaction():
            await conn.execute(migration.up_sql)
            await conn.execute("""
                INSERT INTO schema_migrations (version, name, checksum)
                VALUES ($1, $2, $3)
                ON CONFLICT (version) DO NOTHING
            """, migration.version, migration.name, checksum)
        
        print(f"✅ Applied {migration.version}")
    
    async def rollback_migration(self, conn, migration: Migration):
        """Rollback a single migration"""
        if not migration.down_sql or migration.down_sql.startswith("-- No rollback"):
            print(f"⚠️  No rollback migration for {migration.version}: {migration.name}")
            return False
        
        print(f"Rolling back migration {migration.version}: {migration.name}")
        
        async with conn.transaction():
            await conn.execute(migration.down_sql)
            await conn.execute("DELETE FROM schema_migrations WHERE version = $1", migration.version)
        
        print(f"✅ Rolled back {migration.version}")
        return True
    
    async def migrate(self, target_version: Optional[str] = None):
        """Apply pending migrations"""
        conn = await asyncpg.connect(self.connection_string)
        
        try:
            await self.ensure_migrations_table(conn)
            applied = await self.get_applied_migrations(conn)
            
            migrations = self.discover_migrations()
            pending = [m for m in migrations if m.version not in applied]
            
            if not pending:
                print("✅ No pending migrations")
                return
            
            # Sort by version
            pending.sort(key=lambda m: m.version)
            
            # Apply up to target version if specified
            if target_version:
                pending = [m for m in pending if m.version <= target_version]
            
            print(f"Found {len(pending)} pending migration(s)")
            
            for migration in pending:
                await self.apply_migration(conn, migration)
            
            print(f"✅ Applied {len(pending)} migration(s)")
            
        finally:
            await conn.close()
    
    async def rollback(self, count: int = 1):
        """Rollback last N migrations"""
        conn = await asyncpg.connect(self.connection_string)
        
        try:
            await self.ensure_migrations_table(conn)
            applied = await self.get_applied_migrations(conn)
            
            if not applied:
                print("No migrations to rollback")
                return
            
            migrations = self.discover_migrations()
            migration_map = {m.version: m for m in migrations}
            
            # Get last N migrations in reverse order
            to_rollback = applied[-count:]
            to_rollback.reverse()
            
            for version in to_rollback:
                if version in migration_map:
                    await self.rollback_migration(conn, migration_map[version])
                else:
                    print(f"⚠️  Migration {version} not found in files")
            
        finally:
            await conn.close()
    
    async def status(self):
        """Show migration status"""
        conn = await asyncpg.connect(self.connection_string)
        
        try:
            await self.ensure_migrations_table(conn)
            applied = await self.get_applied_migrations(conn)
            
            migrations = self.discover_migrations()
            
            print("Migration Status:")
            print("=" * 80)
            
            for migration in migrations:
                status = "✅ Applied" if migration.version in applied else "⏳ Pending"
                print(f"{status} {migration.version}: {migration.name}")
            
            if not migrations:
                print("No migrations found")
            
        finally:
            await conn.close()


def create_migration(name: str):
    """Create a new migration file"""
    migrations_dir = Path("db/migrations")
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Sanitize name
    safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower())
    
    filename = f"{timestamp}_{safe_name}.sql"
    file_path = migrations_dir / filename
    
    template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}
-- Version: {timestamp}

-- UP MIGRATION
-- Add your migration SQL here
BEGIN;

-- Example: CREATE TABLE example_table (...);
-- Example: ALTER TABLE existing_table ADD COLUMN new_column TYPE;

COMMIT;

-- DOWN MIGRATION
-- Add rollback SQL here
BEGIN;

-- Example: DROP TABLE IF EXISTS example_table;
-- Example: ALTER TABLE existing_table DROP COLUMN IF EXISTS new_column;

COMMIT;
"""
    
    file_path.write_text(template)
    print(f"✅ Created migration: {file_path}")
    print(f"   Edit the file to add your migration SQL")


async def main():
    """Main CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration manager")
    parser.add_argument("--connection-string", help="Database connection string", 
                       default=os.getenv("DATABASE_URL"))
    parser.add_argument("--migrations-dir", default="db/migrations", 
                       help="Migrations directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply pending migrations")
    migrate_parser.add_argument("--to", help="Target migration version")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument("--count", type=int, default=1, 
                                help="Number of migrations to rollback")
    
    # Status command
    subparsers.add_parser("status", help="Show migration status")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("name", help="Migration name")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_migration(args.name)
        return
    
    if not args.connection_string:
        print("Error: DATABASE_URL environment variable or --connection-string required")
        sys.exit(1)
    
    manager = MigrationManager(Path(args.migrations_dir), args.connection_string)
    
    if args.command == "migrate":
        await manager.migrate(args.to)
    elif args.command == "rollback":
        await manager.rollback(args.count)
    elif args.command == "status":
        await manager.status()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

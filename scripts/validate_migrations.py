#!/usr/bin/env python3
"""
Migration Validation Script

Validates database migrations for:
- Syntax errors
- Missing rollback scripts
- Schema consistency
- Migration ordering
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
import asyncpg
import asyncio


class MigrationValidator:
    """Validates database migrations"""
    
    def __init__(self, migrations_dir: str = "migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_migration_files(self) -> bool:
        """Validate migration file structure and naming"""
        if not self.migrations_dir.exists():
            self.errors.append(f"Migrations directory not found: {self.migrations_dir}")
            return False
        
        migration_files = list(self.migrations_dir.glob("*.sql"))
        migration_dirs = [d for d in self.migrations_dir.iterdir() if d.is_dir()]
        
        if not migration_files and not migration_dirs:
            self.warnings.append("No migration files found")
            return True
        
        # Validate numbered migrations
        numbered_migrations = {}
        for file in migration_files:
            match = re.match(r"^(\d+)_(.+)\.sql$", file.name)
            if match:
                num = int(match.group(1))
                if num in numbered_migrations:
                    self.errors.append(f"Duplicate migration number: {num}")
                numbered_migrations[num] = file
        
        # Check for gaps in numbering
        if numbered_migrations:
            expected = set(range(1, max(numbered_migrations.keys()) + 1))
            actual = set(numbered_migrations.keys())
            missing = expected - actual
            if missing:
                self.warnings.append(f"Missing migration numbers: {sorted(missing)}")
        
        # Validate timestamped migrations
        for dir_path in migration_dirs:
            sql_files = list(dir_path.glob("*.sql"))
            rollback_files = list(dir_path.glob("*rollback*.sql"))
            
            if not sql_files:
                self.errors.append(f"Migration directory has no SQL files: {dir_path}")
            
            if not rollback_files:
                self.warnings.append(f"Migration directory has no rollback script: {dir_path}")
        
        return len(self.errors) == 0
    
    def validate_sql_syntax(self, file_path: Path) -> List[str]:
        """Basic SQL syntax validation"""
        errors = []
        
        try:
            content = file_path.read_text()
            
            # Check for common SQL issues
            if "DROP TABLE" in content.upper() and "IF EXISTS" not in content.upper():
                errors.append(f"DROP TABLE without IF EXISTS in {file_path.name}")
            
            if "DROP COLUMN" in content.upper() and "IF EXISTS" not in content.upper():
                errors.append(f"DROP COLUMN without IF EXISTS in {file_path.name}")
            
            # Check for missing semicolons (basic check)
            statements = [s.strip() for s in content.split(';') if s.strip()]
            if len(statements) > 1:
                # Multiple statements should all end with semicolon
                for i, stmt in enumerate(statements[:-1]):
                    if not stmt.rstrip().endswith(';'):
                        errors.append(f"Statement {i+1} missing semicolon in {file_path.name}")
            
        except Exception as e:
            errors.append(f"Error reading {file_path.name}: {e}")
        
        return errors
    
    def validate_all_sql_files(self) -> bool:
        """Validate all SQL files"""
        sql_files = list(self.migrations_dir.rglob("*.sql"))
        
        for sql_file in sql_files:
            errors = self.validate_sql_syntax(sql_file)
            self.errors.extend(errors)
        
        return len(self.errors) == 0
    
    async def validate_schema_consistency(self, database_url: str) -> bool:
        """Validate schema consistency against database"""
        try:
            conn = await asyncpg.connect(database_url)
            
            # Check if migrations table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'schema_migrations'
                )
            """)
            
            if not table_exists:
                self.warnings.append("schema_migrations table not found - migrations may not have been run")
            
            await conn.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Database connection error: {e}")
            return False
    
    def validate(self, database_url: str = None) -> Tuple[bool, List[str], List[str]]:
        """Run all validations"""
        self.validate_migration_files()
        self.validate_all_sql_files()
        
        if database_url:
            asyncio.run(self.validate_schema_consistency(database_url))
        
        return len(self.errors) == 0, self.errors, self.warnings


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate database migrations")
    parser.add_argument(
        "--migrations-dir",
        default="migrations",
        help="Path to migrations directory"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL for schema consistency check"
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with error code if warnings are found"
    )
    
    args = parser.parse_args()
    
    validator = MigrationValidator(args.migrations_dir)
    success, errors, warnings = validator.validate(args.database_url)
    
    if errors:
        print("❌ Migration Validation Errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    
    if warnings:
        print("⚠️  Migration Validation Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if success and (not warnings or not args.fail_on_warnings):
        print("✅ Migration validation passed")
        sys.exit(0)
    else:
        print("❌ Migration validation failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Database Schema Validator

Validates database schema integrity, checks for missing tables/columns/indexes,
and ensures migrations are applied correctly.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.database.postgres import PostgresConnection


class SchemaStatus(str, Enum):
    """Schema validation status"""
    VALID = "valid"
    INVALID = "invalid"
    DEGRADED = "degraded"


@dataclass
class SchemaIssue:
    """Represents a schema validation issue"""
    severity: str  # 'error', 'warning', 'info'
    table: Optional[str]
    column: Optional[str]
    index: Optional[str]
    constraint: Optional[str]
    message: str
    fix_suggestion: Optional[str] = None


@dataclass
class SchemaValidationResult:
    """Result of schema validation"""
    status: SchemaStatus
    issues: List[SchemaIssue]
    tables_checked: int
    indexes_checked: int
    constraints_checked: int


class SchemaValidator:
    """Validates database schema integrity"""
    
    def __init__(self, postgres_conn: PostgresConnection):
        self.postgres_conn = postgres_conn
        self.logger = logging.getLogger(__name__)
    
    async def validate_schema(self) -> SchemaValidationResult:
        """
        Validate the database schema.
        
        Returns:
            SchemaValidationResult with validation status and issues
        """
        issues: List[SchemaIssue] = []
        
        # Expected core tables
        expected_tables = [
            "users", "podcasts", "episodes", "sponsors", "campaigns",
            "listener_metrics", "attribution_events", "tenants"
        ]
        
        # Check for missing tables
        existing_tables = await self._get_existing_tables()
        tables_checked = len(existing_tables)
        
        for table in expected_tables:
            if table not in existing_tables:
                issues.append(SchemaIssue(
                    severity="error",
                    table=table,
                    column=None,
                    index=None,
                    constraint=None,
                    message=f"Required table '{table}' is missing",
                    fix_suggestion=f"Run migration to create table '{table}'"
                ))
        
        # Check for missing indexes on critical columns
        indexes_checked = await self._validate_indexes(issues)
        
        # Check for missing constraints
        constraints_checked = await self._validate_constraints(issues)
        
        # Determine status
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        if error_count > 0:
            status = SchemaStatus.INVALID
        elif warning_count > 0:
            status = SchemaStatus.DEGRADED
        else:
            status = SchemaStatus.VALID
        
        return SchemaValidationResult(
            status=status,
            issues=issues,
            tables_checked=tables_checked,
            indexes_checked=indexes_checked,
            constraints_checked=constraints_checked
        )
    
    async def _get_existing_tables(self) -> List[str]:
        """Get list of existing tables"""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        rows = await self.postgres_conn.fetch(query)
        # Handle asyncpg.Record objects - access by index or convert to dict
        return [row[0] if isinstance(row, tuple) or hasattr(row, '__getitem__') else getattr(row, 'table_name', str(row)) for row in rows]
    
    async def _validate_indexes(self, issues: List[SchemaIssue]) -> int:
        """Validate critical indexes exist"""
        # Critical indexes that should exist
        critical_indexes = [
            ("users", "email"),
            ("podcasts", "user_id"),
            ("episodes", "podcast_id"),
            ("campaigns", "podcast_id"),
            ("campaigns", "sponsor_id"),
        ]
        
        indexes_checked = 0
        for table, column in critical_indexes:
            index_name = f"idx_{table}_{column}"
            exists = await self._index_exists(table, column)
            indexes_checked += 1
            
            if not exists:
                issues.append(SchemaIssue(
                    severity="warning",
                    table=table,
                    column=column,
                    index=index_name,
                    constraint=None,
                    message=f"Index '{index_name}' on {table}.{column} is missing",
                    fix_suggestion=f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});"
                ))
        
        return indexes_checked
    
    async def _validate_constraints(self, issues: List[SchemaIssue]) -> int:
        """Validate critical constraints exist"""
        # Critical foreign key constraints
        critical_fks = [
            ("podcasts", "user_id", "users", "user_id"),
            ("episodes", "podcast_id", "podcasts", "podcast_id"),
            ("campaigns", "podcast_id", "podcasts", "podcast_id"),
            ("campaigns", "sponsor_id", "sponsors", "sponsor_id"),
        ]
        
        constraints_checked = 0
        for table, column, ref_table, ref_column in critical_fks:
            constraint_name = f"{table}_{column}_fkey"
            exists = await self._constraint_exists(table, constraint_name)
            constraints_checked += 1
            
            if not exists:
                issues.append(SchemaIssue(
                    severity="error",
                    table=table,
                    column=column,
                    index=None,
                    constraint=constraint_name,
                    message=f"Foreign key constraint '{constraint_name}' is missing",
                    fix_suggestion=f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column});"
                ))
        
        return constraints_checked
    
    async def _index_exists(self, table: str, column: str) -> bool:
        """Check if an index exists on a column"""
        query = """
            SELECT COUNT(*)::int as count
            FROM pg_indexes
            WHERE tablename = $1
            AND indexdef LIKE '%' || $2 || '%';
        """
        result = await self.postgres_conn.fetchval(query, table, column)
        return (result or 0) > 0
    
    async def _constraint_exists(self, table: str, constraint_name: str) -> bool:
        """Check if a constraint exists"""
        query = """
            SELECT COUNT(*)::int as count
            FROM information_schema.table_constraints
            WHERE table_name = $1
            AND constraint_name = $2;
        """
        result = await self.postgres_conn.fetchval(query, table, constraint_name)
        return (result or 0) > 0
    
    async def generate_migration_suggestions(self, validation_result: SchemaValidationResult) -> List[str]:
        """
        Generate SQL migration suggestions based on validation issues.
        
        Args:
            validation_result: Schema validation result
        
        Returns:
            List of SQL statements to fix issues
        """
        suggestions = []
        
        for issue in validation_result.issues:
            if issue.fix_suggestion:
                suggestions.append(issue.fix_suggestion)
        
        return suggestions

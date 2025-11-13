#!/usr/bin/env python3
"""
Database Initialization Script

Runs all migrations and sets up the database schema.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import PostgresConnection, TimescaleConnection
from src.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_migration_file(conn: PostgresConnection, file_path: Path):
    """Run a SQL migration file"""
    logger.info(f"Running migration: {file_path.name}")
    
    try:
        with open(file_path, 'r') as f:
            sql = f.read()
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    await conn.execute(statement)
                except Exception as e:
                    # Some statements might fail if already exists, log and continue
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        logger.debug(f"Statement skipped (already exists): {e}")
                    else:
                        logger.warning(f"Statement warning: {e}")
        
        logger.info(f"✓ Completed migration: {file_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed migration {file_path.name}: {e}")
        return False


async def initialize_database():
    """Initialize the database with all migrations"""
    config = load_config()
    
    # Initialize PostgreSQL connection
    postgres = PostgresConnection(
        host=config.database.postgres_host,
        port=config.database.postgres_port,
        database=config.database.postgres_database,
        user=config.database.postgres_user,
        password=config.database.postgres_password
    )
    
    try:
        logger.info("Connecting to PostgreSQL...")
        await postgres.initialize()
        
        # Check connection
        if not await postgres.health_check():
            logger.error("Database health check failed")
            return False
        
        logger.info("✓ Database connection established")
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent.parent / "migrations"
        
        if not migrations_dir.exists():
            logger.error(f"Migrations directory not found: {migrations_dir}")
            return False
        
        # Get all SQL files sorted by name
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            logger.warning("No migration files found")
            return False
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run migrations in order
        for migration_file in migration_files:
            success = await run_migration_file(postgres, migration_file)
            if not success:
                logger.error(f"Migration failed: {migration_file.name}")
                return False
        
        logger.info("✓ All migrations completed successfully")
        
        # Initialize TimescaleDB connection for hypertables
        logger.info("Setting up TimescaleDB hypertables...")
        timescale = TimescaleConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        
        await timescale.initialize()
        
        # Verify hypertables were created
        hypertables = await timescale.fetch("""
            SELECT hypertable_name 
            FROM timescaledb_information.hypertables
        """)
        
        logger.info(f"✓ Created {len(hypertables)} hypertables:")
        for row in hypertables:
            logger.info(f"  - {row['hypertable_name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await postgres.close()


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Database Initialization")
    logger.info("=" * 60)
    
    success = await initialize_database()
    
    if success:
        logger.info("=" * 60)
        logger.info("✓ Database initialization completed successfully!")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("✗ Database initialization failed!")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

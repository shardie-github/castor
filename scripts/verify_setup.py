#!/usr/bin/env python3
"""
Setup Verification Script

Verifies that all infrastructure components are properly configured.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def verify_database_schema():
    """Verify database schema is set up correctly"""
    from src.database import PostgresConnection, TimescaleConnection
    from src.config import load_config
    
    config = load_config()
    
    print("Verifying database schema...")
    
    try:
        postgres = PostgresConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        await postgres.initialize()
        
        # Check tables exist
        tables = await postgres.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        expected_tables = [
            'users', 'podcasts', 'episodes', 'sponsors', 
            'campaigns', 'transcripts', 'reports',
            'listener_events', 'attribution_events', 'listener_metrics'
        ]
        
        existing_tables = [row['table_name'] for row in tables]
        missing_tables = set(expected_tables) - set(existing_tables)
        
        if missing_tables:
            print(f"  ✗ Missing tables: {', '.join(missing_tables)}")
            return False
        
        print(f"  ✓ All {len(expected_tables)} tables exist")
        
        # Check TimescaleDB hypertables
        timescale = TimescaleConnection(
            host=config.database.postgres_host,
            port=config.database.postgres_port,
            database=config.database.postgres_database,
            user=config.database.postgres_user,
            password=config.database.postgres_password
        )
        await timescale.initialize()
        
        hypertables = await timescale.fetch("""
            SELECT hypertable_name 
            FROM timescaledb_information.hypertables
        """)
        
        expected_hypertables = ['listener_events', 'attribution_events', 'listener_metrics']
        existing_hypertables = [row['hypertable_name'] for row in hypertables]
        missing_hypertables = set(expected_hypertables) - set(existing_hypertables)
        
        if missing_hypertables:
            print(f"  ✗ Missing hypertables: {', '.join(missing_hypertables)}")
            return False
        
        print(f"  ✓ All {len(expected_hypertables)} hypertables exist")
        
        await postgres.close()
        await timescale.close()
        
        return True
        
    except Exception as e:
        print(f"  ✗ Database verification failed: {e}")
        return False


async def verify_redis():
    """Verify Redis is accessible"""
    from src.database import RedisConnection
    from src.config import load_config
    
    config = load_config()
    
    print("Verifying Redis...")
    
    try:
        redis = RedisConnection(
            host=config.database.redis_host,
            port=config.database.redis_port,
            password=config.database.redis_password
        )
        await redis.initialize()
        
        # Test set/get
        await redis.set("test_key", "test_value", ex=10)
        value = await redis.get("test_key")
        
        if value == "test_value":
            await redis.delete("test_key")
            print("  ✓ Redis is accessible and working")
            await redis.close()
            return True
        else:
            print("  ✗ Redis test failed")
            await redis.close()
            return False
            
    except Exception as e:
        print(f"  ✗ Redis verification failed: {e}")
        return False


async def verify_config():
    """Verify configuration is loaded correctly"""
    from src.config import load_config
    
    print("Verifying configuration...")
    
    try:
        config = load_config()
        
        # Check required config values
        required = [
            ('database.postgres_host', config.database.postgres_host),
            ('database.postgres_database', config.database.postgres_database),
            ('database.redis_host', config.database.redis_host),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            print(f"  ✗ Missing configuration: {', '.join(missing)}")
            return False
        
        print("  ✓ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration verification failed: {e}")
        return False


async def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Infrastructure Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Configuration", verify_config()),
        ("Database Schema", verify_database_schema()),
        ("Redis", verify_redis()),
    ]
    
    results = []
    for name, check in checks:
        print(f"\n{name}:")
        result = await check
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ All checks passed! Infrastructure is ready.")
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

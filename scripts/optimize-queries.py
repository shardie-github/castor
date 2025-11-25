#!/usr/bin/env python3
"""
Database Query Optimizer

Analyzes and optimizes database queries for performance.
"""

import asyncio
import asyncpg
import os
from pathlib import Path
from typing import List, Dict


async def analyze_slow_queries(conn, limit: int = 10):
    """Analyze slow queries from pg_stat_statements"""
    try:
        # Check if pg_stat_statements is enabled
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements';
        """)
        
        if result == 0:
            print("⚠️  pg_stat_statements extension not enabled")
            print("   Enable with: CREATE EXTENSION pg_stat_statements;")
            return []
        
        # Get slow queries
        queries = await conn.fetch("""
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                max_exec_time,
                stddev_exec_time
            FROM pg_stat_statements
            WHERE mean_exec_time > 100  -- Queries taking > 100ms on average
            ORDER BY mean_exec_time DESC
            LIMIT $1;
        """, limit)
        
        return queries
        
    except Exception as e:
        print(f"❌ Error analyzing queries: {e}")
        return []


async def check_missing_indexes(conn):
    """Check for missing indexes on foreign keys and common query patterns"""
    missing_indexes = []
    
    # Check foreign keys without indexes
    fk_queries = await conn.fetch("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public';
    """)
    
    for fk in fk_queries:
        table = fk['table_name']
        column = fk['column_name']
        
        # Check if index exists
        index_exists = await conn.fetchval("""
            SELECT COUNT(*) > 0
            FROM pg_indexes
            WHERE tablename = $1
                AND indexdef LIKE $2;
        """, table, f"%{column}%")
        
        if not index_exists:
            missing_indexes.append({
                'type': 'foreign_key',
                'table': table,
                'column': column,
                'recommendation': f"CREATE INDEX idx_{table}_{column} ON {table}({column});"
            })
    
    # Check tenant_id indexes (critical for multi-tenancy)
    tenant_tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name IN (
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND column_name = 'tenant_id'
            );
    """)
    
    for table_info in tenant_tables:
        table = table_info['table_name']
        index_exists = await conn.fetchval("""
            SELECT COUNT(*) > 0
            FROM pg_indexes
            WHERE tablename = $1
                AND indexdef LIKE '%tenant_id%';
        """, table)
        
        if not index_exists:
            missing_indexes.append({
                'type': 'tenant_isolation',
                'table': table,
                'column': 'tenant_id',
                'recommendation': f"CREATE INDEX idx_{table}_tenant_id ON {table}(tenant_id);"
            })
    
    return missing_indexes


async def analyze_table_statistics(conn):
    """Analyze table statistics for optimization opportunities"""
    stats = await conn.fetch("""
        SELECT
            schemaname,
            tablename,
            n_live_tup AS row_count,
            n_dead_tup AS dead_rows,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
    """)
    
    recommendations = []
    
    for stat in stats:
        table = stat['tablename']
        row_count = stat['row_count']
        dead_rows = stat['n_dead_tup']
        
        # Check for tables needing VACUUM
        if dead_rows > 0 and row_count > 0:
            dead_ratio = dead_rows / row_count
            if dead_ratio > 0.1:  # More than 10% dead rows
                recommendations.append({
                    'type': 'vacuum',
                    'table': table,
                    'dead_rows': dead_rows,
                    'dead_ratio': dead_ratio,
                    'recommendation': f"VACUUM ANALYZE {table};"
                })
        
        # Check for tables needing ANALYZE
        if not stat['last_autoanalyze'] and row_count > 10000:
            recommendations.append({
                'type': 'analyze',
                'table': table,
                'row_count': row_count,
                'recommendation': f"ANALYZE {table};"
            })
    
    return recommendations


async def main():
    """Main analysis function"""
    connection_string = os.getenv("DATABASE_URL") or \
        f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE', 'podcast_analytics')}"
    
    print("🔍 Database Query Optimization Analysis\n")
    print(f"Connecting to database...\n")
    
    conn = await asyncpg.connect(connection_string)
    
    try:
        # Analyze slow queries
        print("1. Analyzing slow queries...")
        slow_queries = await analyze_slow_queries(conn)
        
        if slow_queries:
            print(f"   Found {len(slow_queries)} slow queries:\n")
            for i, query in enumerate(slow_queries, 1):
                print(f"   {i}. Mean execution time: {query['mean_exec_time']:.2f}ms")
                print(f"      Calls: {query['calls']}")
                print(f"      Query: {query['query'][:100]}...")
                print()
        else:
            print("   ✅ No slow queries detected\n")
        
        # Check missing indexes
        print("2. Checking for missing indexes...")
        missing_indexes = await check_missing_indexes(conn)
        
        if missing_indexes:
            print(f"   Found {len(missing_indexes)} missing indexes:\n")
            for idx in missing_indexes:
                print(f"   - {idx['table']}.{idx['column']} ({idx['type']})")
                print(f"     {idx['recommendation']}\n")
        else:
            print("   ✅ All critical indexes present\n")
        
        # Analyze table statistics
        print("3. Analyzing table statistics...")
        table_recommendations = await analyze_table_statistics(conn)
        
        if table_recommendations:
            print(f"   Found {len(table_recommendations)} optimization opportunities:\n")
            for rec in table_recommendations:
                if rec['type'] == 'vacuum':
                    print(f"   - {rec['table']}: {rec['dead_ratio']:.1%} dead rows")
                elif rec['type'] == 'analyze':
                    print(f"   - {rec['table']}: Needs ANALYZE ({rec['row_count']} rows)")
                print(f"     {rec['recommendation']}\n")
        else:
            print("   ✅ Tables are well-maintained\n")
        
        # Summary
        print("📊 Summary:\n")
        print(f"   Slow queries: {len(slow_queries)}")
        print(f"   Missing indexes: {len(missing_indexes)}")
        print(f"   Table optimizations: {len(table_recommendations)}")
        
        if slow_queries or missing_indexes or table_recommendations:
            print("\n💡 Recommendations:")
            if slow_queries:
                print("   - Review and optimize slow queries")
                print("   - Add indexes for frequently queried columns")
                print("   - Consider query rewriting")
            if missing_indexes:
                print("   - Add missing indexes (especially foreign keys)")
                print("   - Ensure tenant_id indexes exist for multi-tenancy")
            if table_recommendations:
                print("   - Run VACUUM ANALYZE on tables with high dead row ratio")
                print("   - Schedule regular ANALYZE for large tables")
        else:
            print("\n✅ Database is well-optimized!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

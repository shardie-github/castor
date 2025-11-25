#!/usr/bin/env ts-node
/**
 * Database Schema Validator
 * 
 * Validates database schema against expected structure.
 * Checks for missing tables, columns, indexes, and constraints.
 */

import * as pg from 'pg';

interface SchemaCheck {
  name: string;
  type: 'table' | 'column' | 'index' | 'constraint' | 'extension';
  expected: boolean;
  found: boolean;
  details?: string;
}

interface ValidationResult {
  checks: SchemaCheck[];
  issues: string[];
  warnings: string[];
}

const EXPECTED_TABLES = [
  'tenants',
  'tenant_settings',
  'tenant_quotas',
  'users',
  'user_email_preferences',
  'user_metrics',
  'podcasts',
  'episodes',
  'sponsors',
  'campaigns',
  'listener_events',
  'attribution_events',
  'attribution_event_metadata',
  'listener_metrics',
  'roles',
  'permissions',
  'user_roles',
  'role_permissions',
  'access_control_policies',
  'api_keys',
  'email_verification_tokens',
  'password_reset_tokens',
  'refresh_tokens',
  'workflows',
  'workflow_executions',
  'feature_flags',
  'io_bookings',
  'deals',
  'matches',
  'metrics_daily',
];

const EXPECTED_EXTENSIONS = [
  'uuid-ossp',
  'pg_trgm',
  'pgcrypto',
  'timescaledb',
];

const EXPECTED_HYPERTABLES = [
  'listener_events',
  'attribution_events',
  'listener_metrics',
];

async function validateSchema(connectionString: string): Promise<ValidationResult> {
  const client = new pg.Client({ connectionString });
  await client.connect();
  
  const result: ValidationResult = {
    checks: [],
    issues: [],
    warnings: []
  };
  
  try {
    // Check extensions
    const extensionsResult = await client.query(`
      SELECT extname FROM pg_extension;
    `);
    const installedExtensions = extensionsResult.rows.map(r => r.extname);
    
    for (const ext of EXPECTED_EXTENSIONS) {
      const found = installedExtensions.includes(ext);
      result.checks.push({
        name: ext,
        type: 'extension',
        expected: true,
        found,
        details: found ? 'Installed' : 'Missing'
      });
      
      if (!found) {
        result.issues.push(`Extension ${ext} is not installed`);
      }
    }
    
    // Check tables
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    `);
    const existingTables = tablesResult.rows.map(r => r.table_name);
    
    for (const table of EXPECTED_TABLES) {
      const found = existingTables.includes(table);
      result.checks.push({
        name: table,
        type: 'table',
        expected: true,
        found,
        details: found ? 'Exists' : 'Missing'
      });
      
      if (!found) {
        result.issues.push(`Table ${table} is missing`);
      }
    }
    
    // Check for unexpected tables
    for (const table of existingTables) {
      if (!EXPECTED_TABLES.includes(table) && !table.startsWith('_')) {
        result.warnings.push(`Unexpected table found: ${table}`);
      }
    }
    
    // Check TimescaleDB hypertables
    if (installedExtensions.includes('timescaledb')) {
      const hypertablesResult = await client.query(`
        SELECT hypertable_name 
        FROM timescaledb_information.hypertables;
      `);
      const existingHypertables = hypertablesResult.rows.map(r => r.hypertable_name);
      
      for (const hypertable of EXPECTED_HYPERTABLES) {
        const found = existingHypertables.includes(hypertable);
        result.checks.push({
          name: hypertable,
          type: 'table',
          expected: true,
          found,
          details: found ? 'Hypertable exists' : 'Not converted to hypertable'
        });
        
        if (!found && existingTables.includes(hypertable)) {
          result.warnings.push(`Table ${hypertable} exists but is not a hypertable`);
        }
      }
    } else {
      result.warnings.push('TimescaleDB extension not installed - cannot validate hypertables');
    }
    
    // Check critical indexes
    const indexesResult = await client.query(`
      SELECT tablename, indexname 
      FROM pg_indexes 
      WHERE schemaname = 'public';
    `);
    const existingIndexes = indexesResult.rows.map(r => ({
      table: r.tablename,
      index: r.indexname
    }));
    
    // Check for tenant_id indexes (critical for multi-tenancy)
    const tenantTables = ['users', 'podcasts', 'campaigns', 'sponsors', 'listener_events', 'attribution_events'];
    for (const table of tenantTables) {
      if (existingTables.includes(table)) {
        const hasTenantIndex = existingIndexes.some(
          idx => idx.table === table && idx.index.includes('tenant')
        );
        
        if (!hasTenantIndex) {
          result.warnings.push(`Table ${table} may be missing tenant_id index`);
        }
      }
    }
    
    // Check for foreign key constraints
    const fkResult = await client.query(`
      SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public';
    `);
    
    // Verify critical foreign keys exist
    const criticalFKs = [
      { table: 'users', column: 'tenant_id', refTable: 'tenants' },
      { table: 'podcasts', column: 'tenant_id', refTable: 'tenants' },
      { table: 'campaigns', column: 'tenant_id', refTable: 'tenants' },
      { table: 'episodes', column: 'podcast_id', refTable: 'podcasts' },
    ];
    
    for (const fk of criticalFKs) {
      const found = fkResult.rows.some(
        r => r.table_name === fk.table && 
             r.column_name === fk.column &&
             r.foreign_table_name === fk.refTable
      );
      
      if (!found && existingTables.includes(fk.table)) {
        result.warnings.push(`Missing foreign key: ${fk.table}.${fk.column} -> ${fk.refTable}.id`);
      }
    }
    
  } finally {
    await client.end();
  }
  
  return result;
}

async function main() {
  const connectionString = process.env.DATABASE_URL || 
    `postgresql://${process.env.POSTGRES_USER || 'postgres'}:${process.env.POSTGRES_PASSWORD || 'postgres'}@${process.env.POSTGRES_HOST || 'localhost'}:${process.env.POSTGRES_PORT || '5432'}/${process.env.POSTGRES_DATABASE || 'podcast_analytics'}`;
  
  console.log('🔍 Database Schema Validator\n');
  console.log(`📊 Connecting to database...\n`);
  
  try {
    const result = await validateSchema(connectionString);
    
    console.log('📋 Validation Results:\n');
    
    // Group checks by type
    const byType = result.checks.reduce((acc, check) => {
      if (!acc[check.type]) acc[check.type] = [];
      acc[check.type].push(check);
      return acc;
    }, {} as Record<string, SchemaCheck[]>);
    
    for (const [type, checks] of Object.entries(byType)) {
      console.log(`${type.toUpperCase()}:\n`);
      for (const check of checks) {
        const status = check.found ? '✅' : '❌';
        console.log(`  ${status} ${check.name}${check.details ? ` - ${check.details}` : ''}`);
      }
      console.log('');
    }
    
    if (result.issues.length > 0) {
      console.log('❌ Issues:\n');
      for (const issue of result.issues) {
        console.log(`  - ${issue}`);
      }
      console.log('');
    }
    
    if (result.warnings.length > 0) {
      console.log('⚠️  Warnings:\n');
      for (const warning of result.warnings) {
        console.log(`  - ${warning}`);
      }
      console.log('');
    }
    
    console.log('📈 Summary:\n');
    console.log(`  Total checks: ${result.checks.length}`);
    console.log(`  Passed: ${result.checks.filter(c => c.found).length}`);
    console.log(`  Failed: ${result.checks.filter(c => !c.found).length}`);
    console.log(`  Issues: ${result.issues.length}`);
    console.log(`  Warnings: ${result.warnings.length}\n`);
    
    if (result.issues.length > 0) {
      console.log('❌ Schema validation failed. Please fix the issues above.');
      process.exit(1);
    } else if (result.warnings.length > 0) {
      console.log('⚠️  Schema validation passed with warnings.');
      process.exit(0);
    } else {
      console.log('✅ Schema validation passed!');
      process.exit(0);
    }
    
  } catch (error) {
    console.error('❌ Error validating schema:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { validateSchema, EXPECTED_TABLES, EXPECTED_EXTENSIONS };

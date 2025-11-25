#!/usr/bin/env ts-node
/**
 * Environment Parity Checker
 * 
 * Ensures environment variables are consistent across DEV, STAGING, and PROD.
 */

import * as fs from 'fs';
import * as path from 'path';

interface EnvComparison {
  key: string;
  dev: string | undefined;
  staging: string | undefined;
  prod: string | undefined;
  status: 'match' | 'missing' | 'mismatch';
}

function loadEnvFile(filePath: string): Record<string, string> {
  const env: Record<string, string> = {};
  
  if (!fs.existsSync(filePath)) {
    return env;
  }
  
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const match = trimmed.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim().replace(/^["']|["']$/g, '');
        env[key] = value;
      }
    }
  }
  
  return env;
}

function getAllEnvKeys(...envs: Record<string, string>[]): Set<string> {
  const keys = new Set<string>();
  for (const env of envs) {
    for (const key of Object.keys(env)) {
      keys.add(key);
    }
  }
  return keys;
}

function compareEnvironments(): EnvComparison[] {
  const devEnv = loadEnvFile('.env');
  const stagingEnv = loadEnvFile('.env.staging');
  const prodEnv = loadEnvFile('.env.production');
  
  const allKeys = getAllEnvKeys(devEnv, stagingEnv, prodEnv);
  const comparisons: EnvComparison[] = [];
  
  for (const key of allKeys) {
    const dev = devEnv[key];
    const staging = stagingEnv[key];
    const prod = prodEnv[key];
    
    let status: 'match' | 'missing' | 'mismatch' = 'match';
    
    // Check if all present and match
    if (dev && staging && prod) {
      if (dev !== staging || staging !== prod) {
        status = 'mismatch';
      }
    } else if (!dev && !staging && !prod) {
      status = 'missing';
    } else {
      // Some missing
      status = 'missing';
    }
    
    comparisons.push({
      key,
      dev,
      staging,
      prod,
      status
    });
  }
  
  return comparisons;
}

function main() {
  console.log('🔍 Environment Parity Checker\n');
  
  const comparisons = compareEnvironments();
  
  const mismatches = comparisons.filter(c => c.status === 'mismatch');
  const missing = comparisons.filter(c => c.status === 'missing');
  const matches = comparisons.filter(c => c.status === 'match');
  
  if (mismatches.length > 0) {
    console.log('❌ Mismatched Variables:\n');
    for (const comp of mismatches) {
      console.log(`   ${comp.key}:`);
      if (comp.dev) console.log(`     DEV:     ${comp.dev.substring(0, 50)}${comp.dev.length > 50 ? '...' : ''}`);
      if (comp.staging) console.log(`     STAGING: ${comp.staging.substring(0, 50)}${comp.staging.length > 50 ? '...' : ''}`);
      if (comp.prod) console.log(`     PROD:    ${comp.prod.substring(0, 50)}${comp.prod.length > 50 ? '...' : ''}`);
      console.log('');
    }
  }
  
  if (missing.length > 0) {
    console.log('⚠️  Missing Variables:\n');
    for (const comp of missing) {
      const missingEnvs: string[] = [];
      if (!comp.dev) missingEnvs.push('DEV');
      if (!comp.staging) missingEnvs.push('STAGING');
      if (!comp.prod) missingEnvs.push('PROD');
      
      console.log(`   ${comp.key}: Missing in ${missingEnvs.join(', ')}`);
    }
    console.log('');
  }
  
  console.log('📊 Summary:\n');
  console.log(`   Total variables: ${comparisons.length}`);
  console.log(`   ✅ Matching: ${matches.length}`);
  console.log(`   ❌ Mismatched: ${mismatches.length}`);
  console.log(`   ⚠️  Missing: ${missing.length}\n`);
  
  if (mismatches.length > 0 || missing.length > 0) {
    console.log('💡 Recommendations:');
    if (mismatches.length > 0) {
      console.log('   - Align environment variable values across environments');
      console.log('   - Use environment-specific values only when necessary');
      console.log('   - Document why values differ');
    }
    if (missing.length > 0) {
      console.log('   - Add missing variables to all environments');
      console.log('   - Use .env.example as the canonical source');
    }
    process.exit(1);
  } else {
    console.log('✅ All environments are in parity!');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

export { compareEnvironments, loadEnvFile };

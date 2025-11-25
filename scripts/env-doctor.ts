#!/usr/bin/env ts-node
/**
 * Environment Variable Doctor
 * 
 * Validates environment variables, detects drift, and ensures consistency
 * across development, staging, and production environments.
 */

import * as fs from 'fs';
import * as path from 'path';

interface EnvVar {
  name: string;
  required: boolean;
  description: string;
  defaultValue?: string;
  validation?: (value: string) => boolean | string;
}

// Canonical environment variable definitions
const ENV_VARS: EnvVar[] = [
  // Database
  {
    name: 'DATABASE_URL',
    required: false,
    description: 'PostgreSQL connection string (preferred over individual vars)',
    validation: (v) => v.startsWith('postgresql://') || 'Must start with postgresql://'
  },
  {
    name: 'POSTGRES_HOST',
    required: false,
    description: 'PostgreSQL host (required if DATABASE_URL not set)',
    defaultValue: 'localhost'
  },
  {
    name: 'POSTGRES_PORT',
    required: false,
    description: 'PostgreSQL port',
    defaultValue: '5432',
    validation: (v) => {
      const port = parseInt(v);
      return (port >= 1 && port <= 65535) || 'Must be between 1 and 65535';
    }
  },
  {
    name: 'POSTGRES_DATABASE',
    required: true,
    description: 'PostgreSQL database name'
  },
  {
    name: 'POSTGRES_USER',
    required: true,
    description: 'PostgreSQL username'
  },
  {
    name: 'POSTGRES_PASSWORD',
    required: true,
    description: 'PostgreSQL password'
  },
  {
    name: 'POSTGRES_READ_REPLICA_HOST',
    required: false,
    description: 'PostgreSQL read replica host (optional)'
  },
  {
    name: 'POSTGRES_READ_REPLICA_PORT',
    required: false,
    description: 'PostgreSQL read replica port',
    defaultValue: '5432'
  },
  
  // Redis
  {
    name: 'REDIS_HOST',
    required: true,
    description: 'Redis host',
    defaultValue: 'localhost'
  },
  {
    name: 'REDIS_PORT',
    required: false,
    description: 'Redis port',
    defaultValue: '6379',
    validation: (v) => {
      const port = parseInt(v);
      return (port >= 1 && port <= 65535) || 'Must be between 1 and 65535';
    }
  },
  {
    name: 'REDIS_PASSWORD',
    required: false,
    description: 'Redis password (optional)'
  },
  
  // Security
  {
    name: 'JWT_SECRET',
    required: true,
    description: 'JWT secret key (minimum 32 characters)',
    validation: (v) => v.length >= 32 || 'Must be at least 32 characters'
  },
  {
    name: 'ENCRYPTION_KEY',
    required: true,
    description: 'Encryption key (minimum 32 characters)',
    validation: (v) => v.length >= 32 || 'Must be at least 32 characters'
  },
  
  // API Configuration
  {
    name: 'API_URL',
    required: false,
    description: 'Backend API URL',
    defaultValue: 'http://localhost:8000'
  },
  {
    name: 'API_KEY',
    required: false,
    description: 'API key (optional)'
  },
  {
    name: 'API_SECRET_KEY',
    required: false,
    description: 'API secret key (optional)'
  },
  
  // Stripe
  {
    name: 'STRIPE_SECRET_KEY',
    required: false,
    description: 'Stripe secret key (required for payments)'
  },
  {
    name: 'STRIPE_PUBLISHABLE_KEY',
    required: false,
    description: 'Stripe publishable key (required for payments)'
  },
  
  // Email
  {
    name: 'SENDGRID_API_KEY',
    required: false,
    description: 'SendGrid API key (required for email)'
  },
  
  // AWS
  {
    name: 'AWS_ACCESS_KEY_ID',
    required: false,
    description: 'AWS access key ID'
  },
  {
    name: 'AWS_SECRET_ACCESS_KEY',
    required: false,
    description: 'AWS secret access key'
  },
  {
    name: 'AWS_REGION',
    required: false,
    description: 'AWS region',
    defaultValue: 'us-east-1'
  },
  
  // Supabase
  {
    name: 'SUPABASE_URL',
    required: false,
    description: 'Supabase project URL'
  },
  {
    name: 'SUPABASE_SERVICE_ROLE_KEY',
    required: false,
    description: 'Supabase service role key'
  },
  {
    name: 'SUPABASE_ANON_KEY',
    required: false,
    description: 'Supabase anonymous key'
  },
  
  // Frontend
  {
    name: 'NEXT_PUBLIC_API_URL',
    required: true,
    description: 'Public API URL for frontend'
  },
  {
    name: 'NEXT_PUBLIC_SUPABASE_URL',
    required: false,
    description: 'Public Supabase URL'
  },
  {
    name: 'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    required: false,
    description: 'Public Supabase anonymous key'
  },
  {
    name: 'NEXT_PUBLIC_SITE_URL',
    required: false,
    description: 'Public site URL',
    defaultValue: 'https://castor.app'
  },
  
  // Environment
  {
    name: 'ENVIRONMENT',
    required: false,
    description: 'Environment (development, staging, production)',
    defaultValue: 'development',
    validation: (v) => ['development', 'staging', 'production'].includes(v) || 'Must be development, staging, or production'
  },
  {
    name: 'DEBUG',
    required: false,
    description: 'Debug mode',
    defaultValue: 'false',
    validation: (v) => ['true', 'false'].includes(v.toLowerCase()) || 'Must be true or false'
  },
  
  // CORS
  {
    name: 'CORS_ALLOWED_ORIGINS',
    required: false,
    description: 'Comma-separated list of allowed CORS origins',
    defaultValue: 'http://localhost:3000'
  },
  {
    name: 'CORS_ALLOWED_METHODS',
    required: false,
    description: 'Comma-separated list of allowed HTTP methods',
    defaultValue: 'GET,POST,PUT,DELETE,OPTIONS'
  },
  {
    name: 'CORS_ALLOW_CREDENTIALS',
    required: false,
    description: 'Allow credentials in CORS',
    defaultValue: 'true'
  },
  {
    name: 'CORS_MAX_AGE',
    required: false,
    description: 'CORS max age in seconds',
    defaultValue: '3600'
  },
  
  // Security Headers
  {
    name: 'ENABLE_SECURITY_HEADERS',
    required: false,
    description: 'Enable security headers',
    defaultValue: 'true'
  },
  {
    name: 'FORCE_HTTPS',
    required: false,
    description: 'Force HTTPS',
    defaultValue: 'true'
  },
  {
    name: 'HSTS_ENABLED',
    required: false,
    description: 'Enable HSTS',
    defaultValue: 'true'
  },
  
  // Rate Limiting
  {
    name: 'RATE_LIMIT_ENABLED',
    required: false,
    description: 'Enable rate limiting',
    defaultValue: 'true'
  },
  {
    name: 'RATE_LIMIT_PER_MINUTE',
    required: false,
    description: 'Requests per minute',
    defaultValue: '60'
  },
  {
    name: 'RATE_LIMIT_PER_HOUR',
    required: false,
    description: 'Requests per hour',
    defaultValue: '1000'
  },
  {
    name: 'RATE_LIMIT_PER_DAY',
    required: false,
    description: 'Requests per day',
    defaultValue: '10000'
  },
  
  // Feature Flags
  {
    name: 'ENABLE_ETL_CSV_UPLOAD',
    required: false,
    description: 'Enable ETL CSV upload feature',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_MATCHMAKING',
    required: false,
    description: 'Enable matchmaking feature',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_IO_BOOKINGS',
    required: false,
    description: 'Enable IO bookings feature',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_DEAL_PIPELINE',
    required: false,
    description: 'Enable deal pipeline feature',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_NEW_DASHBOARD_CARDS',
    required: false,
    description: 'Enable new dashboard cards',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_ORCHESTRATION',
    required: false,
    description: 'Enable orchestration features',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_MONETIZATION',
    required: false,
    description: 'Enable monetization features',
    defaultValue: 'false'
  },
  {
    name: 'ENABLE_AUTOMATION_JOBS',
    required: false,
    description: 'Enable automation jobs',
    defaultValue: 'false'
  },
  
  // Monitoring
  {
    name: 'PROMETHEUS_PORT',
    required: false,
    description: 'Prometheus metrics port',
    defaultValue: '9090'
  },
  {
    name: 'GRAFANA_URL',
    required: false,
    description: 'Grafana URL'
  },
  
  // Disaster Recovery
  {
    name: 'PRIMARY_REGION',
    required: false,
    description: 'Primary AWS region',
    defaultValue: 'us-east-1'
  },
  {
    name: 'SECONDARY_REGION',
    required: false,
    description: 'Secondary AWS region',
    defaultValue: 'us-west-2'
  },
  {
    name: 'BACKUP_STORAGE_PATH',
    required: false,
    description: 'Backup storage path',
    defaultValue: '/backups'
  },
  
  // OAuth
  {
    name: 'OAUTH_CLIENT_ID',
    required: false,
    description: 'OAuth client ID',
    defaultValue: 'default_client'
  },
  {
    name: 'OAUTH_CLIENT_SECRET',
    required: false,
    description: 'OAuth client secret',
    defaultValue: 'default_secret'
  },
  {
    name: 'OAUTH_REDIRECT_URI',
    required: false,
    description: 'OAuth redirect URI',
    defaultValue: 'http://localhost:8000/callback'
  },
  
  // AI Providers
  {
    name: 'OPENAI_API_KEY',
    required: false,
    description: 'OpenAI API key'
  },
  {
    name: 'ANTHROPIC_API_KEY',
    required: false,
    description: 'Anthropic API key'
  },
];

interface EnvCheckResult {
  var: EnvVar;
  present: boolean;
  value?: string;
  issues: string[];
  warnings: string[];
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

function checkEnvVar(envVar: EnvVar, env: Record<string, string>): EnvCheckResult {
  const result: EnvCheckResult = {
    var: envVar,
    present: envVar.name in env,
    value: env[envVar.name],
    issues: [],
    warnings: []
  };
  
  // Check if required
  if (envVar.required && !result.present) {
    result.issues.push(`Required variable ${envVar.name} is missing`);
  }
  
  // Check if using default value
  if (!result.present && envVar.defaultValue) {
    result.warnings.push(`Using default value: ${envVar.defaultValue}`);
  }
  
  // Validate value if present
  if (result.present && result.value && envVar.validation) {
    const validationResult = envVar.validation(result.value);
    if (validationResult !== true) {
      result.issues.push(`Validation failed: ${validationResult}`);
    }
  }
  
  // Check for default/placeholder values in production
  if (result.present && result.value) {
    const env = process.env.ENVIRONMENT || 'development';
    if (env === 'production') {
      if (result.value.includes('change-me') || result.value.includes('default_')) {
        result.issues.push(`Production environment contains placeholder value`);
      }
      if (result.value.length < 8 && envVar.name.includes('SECRET') || envVar.name.includes('KEY')) {
        result.issues.push(`Security key appears too short for production`);
      }
    }
  }
  
  return result;
}

function main() {
  const envFile = process.argv[2] || '.env';
  const envPath = path.resolve(process.cwd(), envFile);
  
  console.log(`🔍 Environment Variable Doctor`);
  console.log(`📁 Checking: ${envPath}\n`);
  
  const env = loadEnvFile(envPath);
  const results: EnvCheckResult[] = [];
  
  // Check all defined variables
  for (const envVar of ENV_VARS) {
    results.push(checkEnvVar(envVar, env));
  }
  
  // Find unused variables
  const definedVarNames = new Set(ENV_VARS.map(v => v.name));
  const unusedVars: string[] = [];
  for (const key in env) {
    if (!definedVarNames.has(key) && !key.startsWith('#')) {
      unusedVars.push(key);
    }
  }
  
  // Print results
  let issueCount = 0;
  let warningCount = 0;
  
  console.log('📊 Results:\n');
  
  for (const result of results) {
    if (result.issues.length > 0 || result.warnings.length > 0 || !result.present) {
      const status = result.issues.length > 0 ? '❌' : result.warnings.length > 0 ? '⚠️' : 'ℹ️';
      console.log(`${status} ${result.var.name}`);
      
      if (!result.present) {
        if (result.var.required) {
          console.log(`   Missing (REQUIRED)`);
          issueCount++;
        } else {
          console.log(`   Missing (optional, default: ${result.var.defaultValue || 'none'})`);
        }
      } else {
        console.log(`   Value: ${result.value?.substring(0, 50)}${result.value && result.value.length > 50 ? '...' : ''}`);
      }
      
      if (result.var.description) {
        console.log(`   ${result.var.description}`);
      }
      
      for (const issue of result.issues) {
        console.log(`   ❌ ${issue}`);
        issueCount++;
      }
      
      for (const warning of result.warnings) {
        console.log(`   ⚠️  ${warning}`);
        warningCount++;
      }
      
      console.log('');
    }
  }
  
  if (unusedVars.length > 0) {
    console.log('⚠️  Unused Variables (not in canonical list):\n');
    for (const unused of unusedVars) {
      console.log(`   - ${unused}`);
      warningCount++;
    }
    console.log('');
  }
  
  // Summary
  console.log('📈 Summary:\n');
  console.log(`   Total variables checked: ${ENV_VARS.length}`);
  console.log(`   Variables present: ${results.filter(r => r.present).length}`);
  console.log(`   Issues found: ${issueCount}`);
  console.log(`   Warnings: ${warningCount}`);
  console.log(`   Unused variables: ${unusedVars.length}\n`);
  
  if (issueCount > 0) {
    console.log('❌ Environment validation failed. Please fix the issues above.');
    process.exit(1);
  } else if (warningCount > 0) {
    console.log('⚠️  Environment validation passed with warnings.');
    process.exit(0);
  } else {
    console.log('✅ Environment validation passed!');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

export { ENV_VARS, checkEnvVar, loadEnvFile };

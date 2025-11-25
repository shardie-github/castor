#!/usr/bin/env ts-node
/**
 * Documentation Sync Engine
 * 
 * Automatically synchronizes documentation with code changes.
 */

import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

interface DocCheck {
  file: string;
  status: 'synced' | 'outdated' | 'missing';
  lastModified: Date;
  lastCodeChange?: Date;
}

function getGitLastModified(filePath: string): Date | null {
  try {
    const result = execSync(`git log -1 --format=%ci -- "${filePath}"`, { encoding: 'utf-8' });
    if (result.trim()) {
      return new Date(result.trim());
    }
  } catch (e) {
    // File might not be in git
  }
  return null;
}

function checkAPIDocs(): DocCheck[] {
  const checks: DocCheck[] = [];
  
  // Check if API docs are up to date
  const apiDocPath = 'docs/api.md';
  const apiRoutesPath = 'src/api';
  
  if (fs.existsSync(apiDocPath)) {
    const docModified = getGitLastModified(apiDocPath);
    const routesModified = getGitLastModified(apiRoutesPath);
    
    checks.push({
      file: apiDocPath,
      status: routesModified && docModified && routesModified > docModified ? 'outdated' : 'synced',
      lastModified: docModified || new Date(),
      lastCodeChange: routesModified || undefined
    });
  } else {
    checks.push({
      file: apiDocPath,
      status: 'missing',
      lastModified: new Date(0)
    });
  }
  
  return checks;
}

function checkReadme(): DocCheck[] {
  const checks: DocCheck[] = [];
  
  const readmePath = 'README.md';
  const packageJsonPath = 'frontend/package.json';
  const requirementsPath = 'requirements.txt';
  
  if (fs.existsSync(readmePath)) {
    const readmeModified = getGitLastModified(readmePath);
    const packageModified = getGitLastModified(packageJsonPath);
    const requirementsModified = getGitLastModified(requirementsPath);
    
    const latestCodeChange = [packageModified, requirementsModified]
      .filter(d => d !== null)
      .sort((a, b) => b!.getTime() - a!.getTime())[0];
    
    checks.push({
      file: readmePath,
      status: latestCodeChange && readmeModified && latestCodeChange > readmeModified ? 'outdated' : 'synced',
      lastModified: readmeModified || new Date(),
      lastCodeChange: latestCodeChange || undefined
    });
  }
  
  return checks;
}

function checkOnboardingDocs(): DocCheck[] {
  const checks: DocCheck[] = [];
  
  const onboardingPath = 'docs/onboarding.md';
  const makefilePath = 'Makefile';
  const envExamplePath = '.env.example';
  
  if (fs.existsSync(onboardingPath)) {
    const onboardingModified = getGitLastModified(onboardingPath);
    const makefileModified = getGitLastModified(makefilePath);
    const envExampleModified = getGitLastModified(envExamplePath);
    
    const latestCodeChange = [makefileModified, envExampleModified]
      .filter(d => d !== null)
      .sort((a, b) => b!.getTime() - a!.getTime())[0];
    
    checks.push({
      file: onboardingPath,
      status: latestCodeChange && onboardingModified && latestCodeChange > onboardingModified ? 'outdated' : 'synced',
      lastModified: onboardingModified || new Date(),
      lastCodeChange: latestCodeChange || undefined
    });
  }
  
  return checks;
}

function main() {
  console.log('📚 Documentation Sync Check\n');
  
  const allChecks: DocCheck[] = [
    ...checkAPIDocs(),
    ...checkReadme(),
    ...checkOnboardingDocs()
  ];
  
  let outdatedCount = 0;
  let missingCount = 0;
  
  for (const check of allChecks) {
    const statusIcon = check.status === 'synced' ? '✅' : check.status === 'outdated' ? '⚠️' : '❌';
    console.log(`${statusIcon} ${check.file}`);
    
    if (check.status === 'outdated') {
      console.log(`   Last modified: ${check.lastModified.toISOString()}`);
      if (check.lastCodeChange) {
        console.log(`   Code changed: ${check.lastCodeChange.toISOString()}`);
      }
      outdatedCount++;
    } else if (check.status === 'missing') {
      missingCount++;
    }
  }
  
  console.log('\n📊 Summary:');
  console.log(`   Synced: ${allChecks.filter(c => c.status === 'synced').length}`);
  console.log(`   Outdated: ${outdatedCount}`);
  console.log(`   Missing: ${missingCount}`);
  
  if (outdatedCount > 0 || missingCount > 0) {
    console.log('\n💡 Recommendations:');
    if (outdatedCount > 0) {
      console.log('   - Run: python scripts/generate-api-docs.py');
      console.log('   - Update README.md with latest changes');
      console.log('   - Review and update onboarding docs');
    }
    if (missingCount > 0) {
      console.log('   - Generate missing documentation files');
    }
    process.exit(1);
  } else {
    console.log('\n✅ All documentation is up to date!');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

export { checkAPIDocs, checkReadme, checkOnboardingDocs };

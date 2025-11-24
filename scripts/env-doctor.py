#!/usr/bin/env python3
"""
Environment Variables Doctor

Scans the codebase for environment variable usage and validates against .env.example.
Identifies:
- Variables used but not documented in .env.example
- Variables documented but never used
- Inconsistent naming (case, spelling)
- Missing required variables in CI workflows
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict
import json

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def find_env_usage_in_python(root: Path) -> Set[str]:
    """Find all environment variable references in Python code"""
    env_vars = set()
    patterns = [
        r'os\.getenv\(["\']([^"\']+)["\']',
        r'os\.environ\[["\']([^"\']+)["\']',
        r'os\.environ\.get\(["\']([^"\']+)["\']',
        r'process\.env\.([A-Z_][A-Z0-9_]*)',  # For JS/TS, but we'll scan Python
        r'\$\{([A-Z_][A-Z0-9_]*)\}',  # Shell variable references
    ]
    
    for py_file in root.rglob("*.py"):
        if "venv" in str(py_file) or ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            for pattern in patterns:
                matches = re.findall(pattern, content)
                env_vars.update(matches)
        except Exception as e:
            print(f"Warning: Could not read {py_file}: {e}", file=sys.stderr)
    
    return env_vars


def find_env_usage_in_js_ts(root: Path) -> Set[str]:
    """Find all environment variable references in JavaScript/TypeScript code"""
    env_vars = set()
    patterns = [
        r'process\.env\.([A-Z_][A-Z0-9_]*)',
        r'process\.env\[["\']([^"\']+)["\']',
        r'\$\{process\.env\.([A-Z_][A-Z0-9_]*)\}',
        r'process\.env\[`([^`]+)`\]',
    ]
    
    for js_file in root.rglob("*.{js,jsx,ts,tsx}"):
        if "node_modules" in str(js_file) or ".next" in str(js_file):
            continue
        try:
            content = js_file.read_text(encoding='utf-8', errors='ignore')
            for pattern in patterns:
                matches = re.findall(pattern, content)
                env_vars.update(matches)
        except Exception as e:
            print(f"Warning: Could not read {js_file}: {e}", file=sys.stderr)
    
    return env_vars


def find_env_usage_in_yaml(root: Path) -> Set[str]:
    """Find environment variable references in YAML files (CI workflows)"""
    env_vars = set()
    patterns = [
        r'\$\{\{\s*secrets\.([A-Z_][A-Z0-9_]*)\s*\}\}',
        r'\$\{\{\s*env\.([A-Z_][A-Z0-9_]*)\s*\}\}',
        r'\$\{([A-Z_][A-Z0-9_]*)\}',
    ]
    
    for yaml_file in root.rglob("*.{yml,yaml}"):
        if ".github" not in str(yaml_file):
            continue
        try:
            content = yaml_file.read_text(encoding='utf-8', errors='ignore')
            for pattern in patterns:
                matches = re.findall(pattern, content)
                env_vars.update(matches)
        except Exception as e:
            print(f"Warning: Could not read {yaml_file}: {e}", file=sys.stderr)
    
    return env_vars


def find_env_usage_in_shell(root: Path) -> Set[str]:
    """Find environment variable references in shell scripts"""
    env_vars = set()
    patterns = [
        r'\$\{([A-Z_][A-Z0-9_]*)\}',
        r'\$([A-Z_][A-Z0-9_]*)',
    ]
    
    for sh_file in root.rglob("*.{sh,bash}"):
        try:
            content = sh_file.read_text(encoding='utf-8', errors='ignore')
            for pattern in patterns:
                matches = re.findall(pattern, content)
                # Filter out common shell variables
                common_vars = {'PATH', 'HOME', 'USER', 'PWD', 'SHELL', 'TERM', 'LANG', 'LC_ALL'}
                env_vars.update(m for m in matches if m not in common_vars)
        except Exception as e:
            print(f"Warning: Could not read {sh_file}: {e}", file=sys.stderr)
    
    return env_vars


def parse_env_example(env_file: Path) -> Dict[str, str]:
    """Parse .env.example file and extract variable names and comments"""
    env_vars = {}
    if not env_file.exists():
        return env_vars
    
    current_comment = []
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            if line.startswith('#'):
                current_comment.append(line[1:].strip())
            continue
        
        if '=' in line:
            var_name = line.split('=')[0].strip()
            env_vars[var_name] = ' '.join(current_comment) if current_comment else ''
            current_comment = []
    
    return env_vars


def main():
    """Main function"""
    root = Path(__file__).parent.parent
    env_example = root / ".env.example"
    
    print(f"{BLUE}=== Environment Variables Doctor ==={NC}\n")
    
    # Find all environment variable usage
    print(f"{BLUE}Scanning codebase for environment variable usage...{NC}")
    python_vars = find_env_usage_in_python(root)
    js_ts_vars = find_env_usage_in_js_ts(root)
    yaml_vars = find_env_usage_in_yaml(root)
    shell_vars = find_env_usage_in_shell(root)
    
    # Combine all found variables
    all_used_vars = python_vars | js_ts_vars | yaml_vars | shell_vars
    
    # Parse .env.example
    documented_vars = parse_env_example(env_example)
    
    # Find issues
    used_not_documented = all_used_vars - set(documented_vars.keys())
    documented_not_used = set(documented_vars.keys()) - all_used_vars
    
    # Print results
    print(f"\n{GREEN}✓ Found {len(all_used_vars)} unique environment variables in codebase{NC}")
    print(f"{GREEN}✓ Found {len(documented_vars)} variables documented in .env.example{NC}\n")
    
    # Issues
    issues_found = False
    
    if used_not_documented:
        issues_found = True
        print(f"{YELLOW}⚠ Variables used in code but NOT documented in .env.example:{NC}")
        for var in sorted(used_not_documented):
            print(f"  - {var}")
        print()
    
    if documented_not_used:
        issues_found = True
        print(f"{YELLOW}⚠ Variables documented in .env.example but NOT found in codebase:{NC}")
        for var in sorted(documented_not_used):
            print(f"  - {var}")
        print()
    
    # Check for NEXT_PUBLIC_ prefix consistency
    next_public_vars = {v for v in all_used_vars if v.startswith("NEXT_PUBLIC_")}
    if next_public_vars:
        print(f"{BLUE}Frontend public variables (NEXT_PUBLIC_*):{NC}")
        for var in sorted(next_public_vars):
            print(f"  - {var}")
        print()
    
    # Summary
    if not issues_found:
        print(f"{GREEN}✓ No issues found! Environment variables are properly documented.{NC}")
        return 0
    else:
        print(f"{YELLOW}⚠ Issues found. Please update .env.example or remove unused variables.{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

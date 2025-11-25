#!/usr/bin/env python3
"""
Environment Variable Validation Script

Validates that all required environment variables are set.
"""

import os
import sys
from typing import List, Tuple


# Required environment variables
REQUIRED_VARS = [
    "DATABASE_URL",  # Or POSTGRES_HOST, POSTGRES_PORT, etc.
    "JWT_SECRET",
    "ENCRYPTION_KEY",
]

# Optional but recommended variables
RECOMMENDED_VARS = [
    "REDIS_HOST",
    "REDIS_PORT",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
]

# Database connection options (either DATABASE_URL or individual vars)
DATABASE_VARS = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DATABASE",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]


def check_required_vars() -> Tuple[List[str], bool]:
    """Check required environment variables"""
    missing = []
    all_present = True
    
    for var in REQUIRED_VARS:
        if var == "DATABASE_URL":
            # Check if DATABASE_URL is set OR all individual POSTGRES vars are set
            if not os.getenv("DATABASE_URL"):
                db_vars_present = all(os.getenv(v) for v in DATABASE_VARS)
                if not db_vars_present:
                    missing.append(f"{var} (or {', '.join(DATABASE_VARS)})")
                    all_present = False
        elif not os.getenv(var):
            missing.append(var)
            all_present = False
    
    return missing, all_present


def check_recommended_vars() -> List[str]:
    """Check recommended environment variables"""
    missing = []
    
    for var in RECOMMENDED_VARS:
        if not os.getenv(var):
            missing.append(var)
    
    return missing


def main():
    """Main validation function"""
    print("🔍 Validating environment variables...\n")
    
    # Check required vars
    missing_required, all_required_present = check_required_vars()
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print()
    
    # Check recommended vars
    missing_recommended = check_recommended_vars()
    
    if missing_recommended:
        print("⚠️  Missing recommended environment variables:")
        for var in missing_recommended:
            print(f"   - {var}")
        print()
    
    # Summary
    if all_required_present:
        print("✅ All required environment variables are set!")
        if missing_recommended:
            print(f"⚠️  {len(missing_recommended)} recommended variables are missing (non-blocking)")
        return 0
    else:
        print(f"❌ {len(missing_required)} required environment variables are missing!")
        print("\nPlease set the missing variables and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Security Audit Script

Performs comprehensive security checks on the codebase.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import json


class SecurityAuditor:
    """Security audit tool"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.warnings = []
    
    def audit(self) -> Dict:
        """Run all security audits"""
        print("🔒 Running Security Audit...")
        print("=" * 60)
        
        self.check_hardcoded_secrets()
        self.check_weak_passwords()
        self.check_sql_injection_risks()
        self.check_xss_risks()
        self.check_dependency_vulnerabilities()
        self.check_env_file_security()
        self.check_ssl_tls_config()
        self.check_authentication_security()
        self.check_authorization_security()
        self.check_input_validation()
        
        return {
            "issues": self.issues,
            "warnings": self.warnings,
            "score": self.calculate_security_score()
        }
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets"""
        print("\n📋 Checking for hardcoded secrets...")
        
        secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', "Hardcoded password"),
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', "Hardcoded API key"),
            (r'secret[_-]?key\s*=\s*["\']([^"\']+)["\']', "Hardcoded secret key"),
            (r'jwt[_-]?secret\s*=\s*["\']([^"\']+)["\']', "Hardcoded JWT secret"),
            (r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\']([^"\']+)["\']', "Hardcoded AWS key"),
            (r'stripe[_-]?secret[_-]?key\s*=\s*["\']([^"\']+)["\']', "Hardcoded Stripe key"),
        ]
        
        for file_path in self.root_dir.rglob("*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                for pattern, issue_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1)
                        # Skip if it's clearly a placeholder
                        if any(x in value.lower() for x in ["change-me", "placeholder", "example", "test"]):
                            continue
                        # Skip if it's an environment variable reference
                        if value.startswith("${") or value.startswith("$"):
                            continue
                        
                        self.issues.append({
                            "type": "hardcoded_secret",
                            "severity": "critical",
                            "file": str(file_path.relative_to(self.root_dir)),
                            "line": content[:match.start()].count("\n") + 1,
                            "message": f"{issue_type} found"
                        })
            except Exception as e:
                self.warnings.append(f"Could not read {file_path}: {e}")
    
    def check_weak_passwords(self):
        """Check for weak password patterns"""
        print("📋 Checking for weak passwords...")
        
        weak_patterns = [
            (r'password\s*=\s*["\'](password|123456|admin|test)["\']', "Weak password"),
            (r'POSTGRES_PASSWORD\s*=\s*["\']postgres["\']', "Default PostgreSQL password"),
        ]
        
        for file_path in self.root_dir.rglob("*.{py,yml,yaml,env}"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                for pattern, issue_type in weak_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.warnings.append({
                            "type": "weak_password",
                            "severity": "high",
                            "file": str(file_path.relative_to(self.root_dir)),
                            "message": issue_type
                        })
            except Exception:
                pass
    
    def check_sql_injection_risks(self):
        """Check for SQL injection risks"""
        print("📋 Checking for SQL injection risks...")
        
        for file_path in self.root_dir.rglob("*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                # Check for string concatenation in SQL queries
                if re.search(r'query\s*[+=].*%[sd]', content) or re.search(r'f["\'].*SELECT.*{.*}', content):
                    # Check if it's using parameterized queries
                    if "execute" in content or "fetch" in content:
                        # Check if parameters are used properly
                        if not re.search(r'\$\d+', content):  # PostgreSQL parameterized queries
                            self.warnings.append({
                                "type": "sql_injection_risk",
                                "severity": "high",
                                "file": str(file_path.relative_to(self.root_dir)),
                                "message": "Potential SQL injection risk - use parameterized queries"
                            })
            except Exception:
                pass
    
    def check_xss_risks(self):
        """Check for XSS risks"""
        print("📋 Checking for XSS risks...")
        
        # This would check frontend code for XSS vulnerabilities
        frontend_dir = self.root_dir / "frontend"
        if frontend_dir.exists():
            for file_path in frontend_dir.rglob("*.{tsx,ts,jsx,js}"):
                try:
                    content = file_path.read_text()
                    # Check for dangerous innerHTML usage
                    if "dangerouslySetInnerHTML" in content:
                        self.warnings.append({
                            "type": "xss_risk",
                            "severity": "medium",
                            "file": str(file_path.relative_to(self.root_dir)),
                            "message": "dangerouslySetInnerHTML usage - ensure content is sanitized"
                        })
                except Exception:
                    pass
    
    def check_dependency_vulnerabilities(self):
        """Check for known vulnerabilities in dependencies"""
        print("📋 Checking dependency vulnerabilities...")
        
        requirements_file = self.root_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                # Use safety or pip-audit if available
                result = subprocess.run(
                    ["pip-audit", "--requirement", str(requirements_file), "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    vulnerabilities = json.loads(result.stdout)
                    for vuln in vulnerabilities.get("vulnerabilities", []):
                        self.issues.append({
                            "type": "dependency_vulnerability",
                            "severity": vuln.get("severity", "unknown"),
                            "package": vuln.get("name", "unknown"),
                            "message": vuln.get("description", "Known vulnerability")
                        })
            except FileNotFoundError:
                self.warnings.append("pip-audit not installed - skipping dependency check")
            except Exception as e:
                self.warnings.append(f"Dependency check failed: {e}")
    
    def check_env_file_security(self):
        """Check .env file security"""
        print("📋 Checking .env file security...")
        
        env_file = self.root_dir / ".env"
        if env_file.exists():
            try:
                content = env_file.read_text()
                # Check if .env is in .gitignore
                gitignore = self.root_dir / ".gitignore"
                if gitignore.exists():
                    gitignore_content = gitignore.read_text()
                    if ".env" not in gitignore_content:
                        self.issues.append({
                            "type": "env_file_not_ignored",
                            "severity": "critical",
                            "message": ".env file not in .gitignore"
                        })
                
                # Check for default/weak secrets
                if "change-me-in-production" in content.lower():
                    self.warnings.append({
                        "type": "default_secrets",
                        "severity": "high",
                        "message": "Default secrets found in .env file"
                    })
            except Exception:
                pass
    
    def check_ssl_tls_config(self):
        """Check SSL/TLS configuration"""
        print("📋 Checking SSL/TLS configuration...")
        
        # Check if HTTPS is enforced
        main_file = self.root_dir / "src" / "main.py"
        if main_file.exists():
            content = main_file.read_text()
            if "force_https" in content.lower():
                # Good - HTTPS enforcement is configured
                pass
            else:
                self.warnings.append({
                    "type": "https_not_enforced",
                    "severity": "high",
                    "message": "HTTPS enforcement not configured"
                })
    
    def check_authentication_security(self):
        """Check authentication security"""
        print("📋 Checking authentication security...")
        
        auth_files = list(self.root_dir.rglob("**/auth*.py"))
        for file_path in auth_files:
            try:
                content = file_path.read_text()
                # Check for password hashing
                if "password" in content.lower() and "bcrypt" not in content.lower() and "hash" not in content.lower():
                    self.warnings.append({
                        "type": "password_hashing",
                        "severity": "high",
                        "file": str(file_path.relative_to(self.root_dir)),
                        "message": "Password hashing not detected"
                    })
            except Exception:
                pass
    
    def check_authorization_security(self):
        """Check authorization security"""
        print("📋 Checking authorization security...")
        
        # Check for proper RBAC/ABAC implementation
        auth_files = list(self.root_dir.rglob("**/authorization*.py"))
        if not auth_files:
            self.warnings.append({
                "type": "authorization_missing",
                "severity": "medium",
                "message": "Authorization module not found"
            })
    
    def check_input_validation(self):
        """Check input validation"""
        print("📋 Checking input validation...")
        
        api_files = list((self.root_dir / "src" / "api").rglob("*.py"))
        for file_path in api_files:
            try:
                content = file_path.read_text()
                # Check for Pydantic models (good validation)
                if "BaseModel" in content or "Field" in content:
                    # Good - using Pydantic for validation
                    continue
                
                # Check if endpoints have validation
                if "@router." in content or "@app." in content:
                    # Check if there's any validation
                    if "Request" in content and "Body" not in content:
                        self.warnings.append({
                            "type": "missing_input_validation",
                            "severity": "medium",
                            "file": str(file_path.relative_to(self.root_dir)),
                            "message": "API endpoint may be missing input validation"
                        })
            except Exception:
                pass
    
    def calculate_security_score(self) -> int:
        """Calculate security score (0-100)"""
        critical_issues = sum(1 for i in self.issues if i.get("severity") == "critical")
        high_issues = sum(1 for i in self.issues if i.get("severity") == "high")
        medium_issues = sum(1 for i in self.issues if i.get("severity") == "medium")
        high_warnings = sum(1 for w in self.warnings if isinstance(w, dict) and w.get("severity") == "high")
        
        score = 100
        score -= critical_issues * 20
        score -= high_issues * 10
        score -= medium_issues * 5
        score -= high_warnings * 2
        
        return max(0, score)
    
    def print_report(self):
        """Print security audit report"""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AUDIT REPORT")
        print("=" * 60)
        
        print(f"\n📊 Security Score: {self.calculate_security_score()}/100")
        
        if self.issues:
            print(f"\n❌ Issues Found: {len(self.issues)}")
            for issue in self.issues:
                severity = issue.get("severity", "unknown").upper()
                print(f"  [{severity}] {issue.get('message', 'Unknown issue')}")
                if "file" in issue:
                    print(f"    File: {issue['file']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings[:10]:  # Limit to first 10
                if isinstance(warning, dict):
                    severity = warning.get("severity", "unknown").upper()
                    print(f"  [{severity}] {warning.get('message', 'Unknown warning')}")
                    if "file" in warning:
                        print(f"    File: {warning['file']}")
                else:
                    print(f"  {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ No security issues found!")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    auditor = SecurityAuditor()
    results = auditor.audit()
    auditor.print_report()
    
    # Exit with error code if critical issues found
    critical_issues = sum(1 for i in results["issues"] if i.get("severity") == "critical")
    if critical_issues > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

"""
Web Application Firewall (WAF)

Enterprise-grade WAF with:
- SQL injection detection
- XSS detection
- Path traversal detection
- Rate limiting per IP
- Request size limits
- Suspicious pattern detection
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class WAFRule:
    """WAF Rule definition"""
    
    def __init__(
        self,
        name: str,
        pattern: str,
        severity: str = "medium",
        action: str = "block",  # block, log, challenge
        description: str = "",
    ):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.severity = severity
        self.action = action
        self.description = description
    
    def matches(self, text: str) -> bool:
        """Check if rule matches text"""
        return bool(self.pattern.search(text))


class WAF:
    """
    Web Application Firewall
    
    Detects and blocks common web attacks:
    - SQL injection
    - XSS attacks
    - Path traversal
    - Command injection
    - Suspicious patterns
    """
    
    def __init__(
        self,
        enabled: bool = True,
        block_on_match: bool = True,
        log_only: bool = False,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        rate_limit_per_minute: int = 60,
    ):
        self.enabled = enabled
        self.block_on_match = block_on_match and not log_only
        self.log_only = log_only
        self.max_request_size = max_request_size
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Rate limiting tracking
        self.request_counts: Dict[str, List[datetime]] = defaultdict(list)
        
        # Initialize rules
        self.rules = self._initialize_rules()
        
        # Blocked IPs (in production, use Redis)
        self.blocked_ips: Dict[str, datetime] = {}
    
    def _initialize_rules(self) -> List[WAFRule]:
        """Initialize WAF rules"""
        rules = []
        
        # SQL Injection patterns
        sql_patterns = [
            r"(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|update\s+.*\s+set)",
            r"(\bor\s+1\s*=\s*1\b|\band\s+1\s*=\s*1\b)",
            r"('|\"|;|--|\/\*|\*\/)",
            r"(exec\s*\(|execute\s*\(|sp_executesql)",
            r"(xp_cmdshell|xp_regread)",
        ]
        
        for pattern in sql_patterns:
            rules.append(WAFRule(
                name="sql_injection",
                pattern=pattern,
                severity="high",
                action="block",
                description="SQL injection attempt detected",
            ))
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",  # onclick=, onerror=, etc.
            r"<iframe[^>]*>",
            r"<img[^>]*src\s*=\s*['\"]?javascript:",
            r"eval\s*\(",
            r"expression\s*\(",
        ]
        
        for pattern in xss_patterns:
            rules.append(WAFRule(
                name="xss",
                pattern=pattern,
                severity="high",
                action="block",
                description="XSS attack attempt detected",
            ))
        
        # Path traversal
        rules.append(WAFRule(
            name="path_traversal",
            pattern=r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
            severity="high",
            action="block",
            description="Path traversal attempt detected",
        ))
        
        # Command injection
        cmd_patterns = [
            r"[;&|`]\s*(rm|del|cat|ls|pwd|whoami|id|uname)",
            r"\$\{.*\}",
            r"`.*`",
        ]
        
        for pattern in cmd_patterns:
            rules.append(WAFRule(
                name="command_injection",
                pattern=pattern,
                severity="high",
                action="block",
                description="Command injection attempt detected",
            ))
        
        # Suspicious patterns
        rules.append(WAFRule(
            name="suspicious_pattern",
            pattern=r"(\.\.\/|\.\.\\|\.\.%2f)",
            severity="medium",
            action="log",
            description="Suspicious pattern detected",
        ))
        
        return rules
    
    def check_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check request against WAF rules.
        
        Returns:
            (allowed, rule_name, reason)
        """
        if not self.enabled:
            return True, None, None
        
        # Check if IP is blocked
        if client_ip and client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if datetime.utcnow() < block_until:
                return False, "ip_blocked", f"IP {client_ip} is blocked until {block_until}"
            else:
                del self.blocked_ips[client_ip]
        
        # Rate limiting
        if client_ip:
            if not self._check_rate_limit(client_ip):
                # Block IP for 15 minutes
                self.blocked_ips[client_ip] = datetime.utcnow() + timedelta(minutes=15)
                return False, "rate_limit", f"Rate limit exceeded for IP {client_ip}"
        
        # Check request size
        if body and len(body.encode()) > self.max_request_size:
            return False, "request_too_large", f"Request exceeds {self.max_request_size} bytes"
        
        # Check path
        for rule in self.rules:
            if rule.matches(path):
                if self.block_on_match and rule.action == "block":
                    logger.warning(
                        f"WAF blocked request: {rule.name}",
                        extra={
                            "rule": rule.name,
                            "path": path,
                            "method": method,
                            "client_ip": client_ip,
                            "severity": rule.severity,
                        }
                    )
                    return False, rule.name, rule.description
                else:
                    logger.info(
                        f"WAF detected: {rule.name}",
                        extra={
                            "rule": rule.name,
                            "path": path,
                            "method": method,
                            "client_ip": client_ip,
                        }
                    )
        
        # Check headers
        header_string = " ".join(f"{k}:{v}" for k, v in headers.items())
        for rule in self.rules:
            if rule.matches(header_string):
                if self.block_on_match and rule.action == "block":
                    logger.warning(
                        f"WAF blocked request: {rule.name} in headers",
                        extra={
                            "rule": rule.name,
                            "client_ip": client_ip,
                            "severity": rule.severity,
                        }
                    )
                    return False, rule.name, f"{rule.description} (in headers)"
        
        # Check body
        if body:
            for rule in self.rules:
                if rule.matches(body):
                    if self.block_on_match and rule.action == "block":
                        logger.warning(
                            f"WAF blocked request: {rule.name} in body",
                            extra={
                                "rule": rule.name,
                                "client_ip": client_ip,
                                "severity": rule.severity,
                            }
                        )
                        return False, rule.name, f"{rule.description} (in body)"
        
        return True, None, None
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit for IP"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts[client_ip]
            if ts > minute_ago
        ]
        
        # Check limit
        if len(self.request_counts[client_ip]) >= self.rate_limit_per_minute:
            return False
        
        # Add current request
        self.request_counts[client_ip].append(now)
        return True
    
    def get_stats(self) -> Dict[str, any]:
        """Get WAF statistics"""
        return {
            "enabled": self.enabled,
            "rules_count": len(self.rules),
            "blocked_ips_count": len(self.blocked_ips),
            "active_rate_limits": len([
                ip for ip, timestamps in self.request_counts.items()
                if len(timestamps) > 0
            ]),
        }


# Global WAF instance
_waf: Optional[WAF] = None


def init_waf(
    enabled: bool = True,
    block_on_match: bool = True,
    log_only: bool = False,
    max_request_size: int = 10 * 1024 * 1024,
    rate_limit_per_minute: int = 60,
) -> WAF:
    """Initialize global WAF"""
    global _waf
    
    _waf = WAF(
        enabled=enabled,
        block_on_match=block_on_match,
        log_only=log_only,
        max_request_size=max_request_size,
        rate_limit_per_minute=rate_limit_per_minute,
    )
    
    return _waf


def get_waf() -> Optional[WAF]:
    """Get global WAF instance"""
    return _waf

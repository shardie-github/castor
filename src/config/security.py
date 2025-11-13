"""
Production Security Configuration

CORS, security headers, WAF rules, and security middleware.
"""

from typing import List, Optional
from pydantic import BaseModel
import os


class SecurityConfig(BaseModel):
    """Security configuration"""
    
    # CORS Configuration
    cors_allowed_origins: List[str] = []
    cors_allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allowed_headers: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_max_age: int = 3600
    
    # Security Headers
    enable_security_headers: bool = True
    content_security_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # WAF Rules
    waf_enabled: bool = True
    block_sql_injection: bool = True
    block_xss: bool = True
    block_path_traversal: bool = True
    block_command_injection: bool = True
    
    # HTTPS/TLS
    force_https: bool = True
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000
    
    # API Security
    api_key_required: bool = False  # Set to True for production
    api_rate_limit_per_key: int = 1000  # Requests per hour per API key
    
    # Session Security
    session_timeout_minutes: int = 30
    session_secure: bool = True
    session_httponly: bool = True
    session_samesite: str = "Lax"
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Load security configuration from environment variables"""
        return cls(
            cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("CORS_ALLOWED_ORIGINS") else [],
            cors_allowed_methods=os.getenv("CORS_ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(","),
            cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            cors_max_age=int(os.getenv("CORS_MAX_AGE", "3600")),
            enable_security_headers=os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true",
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            rate_limit_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "10000")),
            waf_enabled=os.getenv("WAF_ENABLED", "true").lower() == "true",
            force_https=os.getenv("FORCE_HTTPS", "true").lower() == "true",
            hsts_enabled=os.getenv("HSTS_ENABLED", "true").lower() == "true",
            api_key_required=os.getenv("API_KEY_REQUIRED", "false").lower() == "true",
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
            session_secure=os.getenv("SESSION_SECURE", "true").lower() == "true",
        )


# Global security config instance
security_config = SecurityConfig.from_env()

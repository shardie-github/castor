"""
Unified Configuration Settings

Single entry point for application configuration.
Uses Pydantic-based validation from validation.py.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from src.config.validation import (
    load_and_validate_env,
    EnvironmentSettings,
    DatabaseSettings,
    SecuritySettings,
    ExternalServicesSettings,
    CORSSettings,
    RateLimitSettings,
)

# Load environment variables from .env file
load_dotenv()

# Global settings instance (lazy loaded)
_settings: Optional[EnvironmentSettings] = None


def get_settings() -> EnvironmentSettings:
    """
    Get application settings (singleton pattern).
    
    Returns:
        EnvironmentSettings: Validated environment settings
    """
    global _settings
    if _settings is None:
        # Skip validation in test environment
        if os.getenv("SKIP_ENV_VALIDATION", "false").lower() == "true":
            # Create minimal settings for testing
            _settings = _create_test_settings()
        else:
            _settings = load_and_validate_env()
    return _settings


def _create_test_settings() -> EnvironmentSettings:
    """Create minimal settings for testing"""
    from src.config.validation import (
        DatabaseSettings,
        SecuritySettings,
        ExternalServicesSettings,
        CORSSettings,
        RateLimitSettings,
    )
    
    return EnvironmentSettings(
        database=DatabaseSettings(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_database=os.getenv("POSTGRES_DATABASE", "test_db"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
        ),
        security=SecuritySettings(
            jwt_secret=os.getenv("JWT_SECRET", "test_secret_key_min_32_chars_long_for_testing"),
            encryption_key=os.getenv("ENCRYPTION_KEY", "test_encryption_key_min_32_chars_long_for_testing"),
        ),
        external_services=ExternalServicesSettings(),
        cors=CORSSettings(),
        rate_limit=RateLimitSettings(),
    )


# Backward compatibility: provide 'config' object similar to old __init__.py
class _ConfigCompat:
    """Backward compatibility wrapper for old config object"""
    
    def __init__(self, settings: EnvironmentSettings):
        self._settings = settings
    
    @property
    def database(self):
        """Database config (backward compat)"""
        db = self._settings.database
        return type('DatabaseConfig', (), {
            'postgres_host': db.postgres_host,
            'postgres_port': db.postgres_port,
            'postgres_database': db.postgres_database,
            'postgres_user': db.postgres_user,
            'postgres_password': db.postgres_password,
            'redis_host': db.redis_host,
            'redis_port': db.redis_port,
            'redis_password': db.redis_password,
        })()
    
    @property
    def api(self):
        """API config (backward compat)"""
        ext = self._settings.external_services
        return type('APIConfig', (), {
            'api_url': os.getenv("API_URL", "http://localhost:8000"),
            'api_key': None,
            'secret_key': None,
        })()
    
    @property
    def jwt_secret(self) -> str:
        return self._settings.security.jwt_secret
    
    @property
    def encryption_key(self) -> str:
        return self._settings.security.encryption_key
    
    @property
    def stripe_secret_key(self) -> Optional[str]:
        return self._settings.external_services.stripe_secret_key
    
    @property
    def stripe_publishable_key(self) -> Optional[str]:
        return self._settings.external_services.stripe_publishable_key
    
    @property
    def sendgrid_api_key(self) -> Optional[str]:
        return self._settings.external_services.sendgrid_api_key
    
    @property
    def prometheus_port(self) -> int:
        return self._settings.prometheus_port
    
    @property
    def grafana_url(self) -> Optional[str]:
        return self._settings.grafana_url
    
    @property
    def environment(self) -> str:
        return self._settings.environment
    
    @property
    def debug(self) -> bool:
        return self._settings.debug


# Global config instance (backward compatibility)
settings = get_settings()
config = _ConfigCompat(settings)

# Export for convenience
__all__ = [
    'get_settings',
    'settings',
    'config',
    'EnvironmentSettings',
    'DatabaseSettings',
    'SecuritySettings',
    'ExternalServicesSettings',
    'CORSSettings',
    'RateLimitSettings',
]

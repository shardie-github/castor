"""
Configuration Module

DEPRECATED: Use src.config.settings instead.

This module is kept for backward compatibility but redirects to the new settings module.
"""

# Import from new settings module for backward compatibility
from src.config.settings import (
    get_settings,
    settings,
    config,
    EnvironmentSettings,
    DatabaseSettings,
    SecuritySettings,
    ExternalServicesSettings,
    CORSSettings,
    RateLimitSettings,
)

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

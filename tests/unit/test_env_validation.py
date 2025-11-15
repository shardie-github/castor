"""
Tests for environment variable validation
"""

import pytest
import os
from unittest.mock import patch
from src.config.validation import (
    load_and_validate_env,
    DatabaseSettings,
    SecuritySettings,
    ValidationError
)


class TestDatabaseSettings:
    """Test database settings validation"""
    
    def test_valid_database_settings(self):
        """Test valid database settings"""
        settings = DatabaseSettings(
            postgres_database="test_db",
            postgres_user="test_user",
            postgres_password="test_password"
        )
        assert settings.postgres_database == "test_db"
        assert settings.postgres_user == "test_user"
        assert settings.postgres_password == "test_password"
        assert settings.postgres_host == "localhost"  # default
        assert settings.postgres_port == 5432  # default
    
    def test_invalid_port_range(self):
        """Test invalid port range"""
        with pytest.raises(ValidationError):
            DatabaseSettings(
                postgres_database="test_db",
                postgres_user="test_user",
                postgres_password="test_password",
                postgres_port=70000  # Invalid port
            )


class TestSecuritySettings:
    """Test security settings validation"""
    
    def test_valid_security_settings(self):
        """Test valid security settings"""
        settings = SecuritySettings(
            jwt_secret="a" * 32,  # Min 32 chars
            encryption_key="b" * 32
        )
        assert len(settings.jwt_secret) >= 32
        assert len(settings.encryption_key) >= 32
    
    def test_secret_too_short(self):
        """Test secret too short"""
        with pytest.raises(ValidationError):
            SecuritySettings(
                jwt_secret="short",
                encryption_key="b" * 32
            )
    
    def test_default_secret_rejected(self):
        """Test that default secrets are rejected"""
        with pytest.raises(ValidationError):
            SecuritySettings(
                jwt_secret="change-me-in-production",
                encryption_key="b" * 32
            )


class TestEnvironmentValidation:
    """Test complete environment validation"""
    
    @patch.dict(os.environ, {
        "POSTGRES_DATABASE": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "JWT_SECRET": "a" * 32,
        "ENCRYPTION_KEY": "b" * 32,
    })
    def test_load_valid_env(self):
        """Test loading valid environment"""
        settings = load_and_validate_env()
        assert settings.database.postgres_database == "test_db"
        assert settings.security.jwt_secret == "a" * 32
    
    @patch.dict(os.environ, {
        "POSTGRES_DATABASE": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "JWT_SECRET": "short",  # Too short
        "ENCRYPTION_KEY": "b" * 32,
    })
    def test_load_invalid_env(self):
        """Test loading invalid environment"""
        with pytest.raises(ValueError):
            load_and_validate_env()

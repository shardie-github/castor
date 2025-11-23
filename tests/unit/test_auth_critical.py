"""
Critical Authentication Tests

Tests for authentication flows including registration, login, password reset, and JWT handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from src.api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)


@pytest.fixture
def pwd_context():
    """Password context for hashing/verification"""
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def jwt_secret():
    """JWT secret for testing"""
    return "test_secret_key_min_32_chars_long_for_testing"


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self, pwd_context):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert pwd_context.verify(password, hashed)
    
    def test_verify_password_correct(self, pwd_context):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, pwd_context):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self, jwt_secret):
        """Test creating access token"""
        user_id = "user-123"
        tenant_id = "tenant-456"
        
        token = create_access_token(user_id, tenant_id, jwt_secret)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        assert decoded["user_id"] == user_id
        assert decoded["tenant_id"] == tenant_id
        assert "exp" in decoded
    
    def test_create_refresh_token(self, jwt_secret):
        """Test creating refresh token"""
        user_id = "user-123"
        
        token = create_refresh_token(user_id, jwt_secret)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        assert decoded["user_id"] == user_id
        assert "exp" in decoded
    
    def test_verify_token_valid(self, jwt_secret):
        """Test verifying valid token"""
        user_id = "user-123"
        tenant_id = "tenant-456"
        
        token = create_access_token(user_id, tenant_id, jwt_secret)
        decoded = verify_token(token, jwt_secret)
        
        assert decoded is not None
        assert decoded["user_id"] == user_id
        assert decoded["tenant_id"] == tenant_id
    
    def test_verify_token_expired(self, jwt_secret):
        """Test verifying expired token"""
        user_id = "user-123"
        tenant_id = "tenant-456"
        
        # Create token with very short expiration
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "exp": datetime.utcnow() - timedelta(seconds=1)
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        # Should raise exception for expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(token, jwt_secret)
    
    def test_verify_token_invalid(self, jwt_secret):
        """Test verifying invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(invalid_token, jwt_secret)


class TestPasswordValidation:
    """Test password validation rules"""
    
    def test_password_too_short(self):
        """Test password validation - too short"""
        from src.api.auth import UserRegister
        
        with pytest.raises(ValueError, match="at least 8 characters"):
            UserRegister(
                email="test@example.com",
                password="Short1!",
                name="Test User",
                accept_terms=True,
                accept_privacy=True
            )
    
    def test_password_no_uppercase(self):
        """Test password validation - no uppercase"""
        from src.api.auth import UserRegister
        
        with pytest.raises(ValueError, match="uppercase"):
            UserRegister(
                email="test@example.com",
                password="lowercase123!",
                name="Test User",
                accept_terms=True,
                accept_privacy=True
            )
    
    def test_password_no_lowercase(self):
        """Test password validation - no lowercase"""
        from src.api.auth import UserRegister
        
        with pytest.raises(ValueError, match="lowercase"):
            UserRegister(
                email="test@example.com",
                password="UPPERCASE123!",
                name="Test User",
                accept_terms=True,
                accept_privacy=True
            )
    
    def test_password_no_number(self):
        """Test password validation - no number"""
        from src.api.auth import UserRegister
        
        with pytest.raises(ValueError, match="number"):
            UserRegister(
                email="test@example.com",
                password="NoNumbers!",
                name="Test User",
                accept_terms=True,
                accept_privacy=True
            )
    
    def test_password_valid(self):
        """Test password validation - valid password"""
        from src.api.auth import UserRegister
        
        user = UserRegister(
            email="test@example.com",
            password="ValidPassword123!",
            name="Test User",
            accept_terms=True,
            accept_privacy=True
        )
        
        assert user.password == "ValidPassword123!"


class TestEmailValidation:
    """Test email validation"""
    
    def test_invalid_email(self):
        """Test invalid email format"""
        from src.api.auth import UserRegister
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserRegister(
                email="invalid-email",
                password="ValidPassword123!",
                name="Test User",
                accept_terms=True,
                accept_privacy=True
            )
    
    def test_valid_email(self):
        """Test valid email format"""
        from src.api.auth import UserRegister
        
        user = UserRegister(
            email="test@example.com",
            password="ValidPassword123!",
            name="Test User",
            accept_terms=True,
            accept_privacy=True
        )
        
        assert user.email == "test@example.com"

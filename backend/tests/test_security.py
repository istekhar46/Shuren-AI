"""
Tests for security utilities.

Validates password hashing, JWT token generation/validation, and Google OAuth token verification.
"""

import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from unittest.mock import patch, MagicMock

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_google_token
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing and verification."""
    
    def test_hash_password_returns_bcrypt_hash(self):
        """Test that hash_password returns a valid bcrypt hash."""
        password = "mySecurePassword123"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ and have specific length
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # Standard bcrypt hash length
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (salt)."""
        password = "mySecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "mySecurePassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = "mySecurePassword123"
        wrong_password = "wrongPassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_password(self):
        """Test that verify_password handles empty passwords."""
        password = "mySecurePassword123"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and validation."""
    
    def test_create_access_token_contains_user_data(self):
        """Test that created token contains the provided user data."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token({"user_id": user_id})
        
        # Decode without verification to inspect payload
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["user_id"] == user_id
    
    def test_create_access_token_includes_expiration(self):
        """Test that created token includes expiration claim."""
        token = create_access_token({"user_id": "123"})
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_default_expiration(self):
        """Test that token uses default 24-hour expiration."""
        token = create_access_token({"user_id": "123"})
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Calculate expected expiration (approximately 24 hours from now)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be approximately 24 hours (within 1 minute tolerance)
        assert 23.98 <= time_diff.total_seconds() / 3600 <= 24.02
    
    def test_create_access_token_custom_expiration(self):
        """Test that token can use custom expiration time."""
        custom_delta = timedelta(hours=1)
        token = create_access_token({"user_id": "123"}, expires_delta=custom_delta)
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Calculate expected expiration (approximately 1 hour from now)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be approximately 1 hour (within 1 minute tolerance)
        assert 0.98 <= time_diff.total_seconds() / 3600 <= 1.02
    
    def test_decode_access_token_valid_token(self):
        """Test that decode_access_token successfully decodes valid token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token({"user_id": user_id})
        
        payload = decode_access_token(token)
        
        assert payload["user_id"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_access_token_expired_token(self):
        """Test that decode_access_token raises error for expired token."""
        # Create token that expires immediately
        token = create_access_token(
            {"user_id": "123"},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(JWTError):
            decode_access_token(token)
    
    def test_decode_access_token_invalid_signature(self):
        """Test that decode_access_token raises error for invalid signature."""
        # Create token with different secret
        token = jwt.encode(
            {"user_id": "123", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret-key",
            algorithm="HS256"
        )
        
        with pytest.raises(JWTError):
            decode_access_token(token)
    
    def test_decode_access_token_malformed_token(self):
        """Test that decode_access_token raises error for malformed token."""
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token")


class TestGoogleOAuth:
    """Tests for Google OAuth token verification."""
    
    @pytest.mark.asyncio
    async def test_verify_google_token_valid_token(self):
        """Test that verify_google_token returns user info for valid token."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True,
            'picture': 'https://example.com/photo.jpg'
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-google-token')
            
            assert result['email'] == 'user@example.com'
            assert result['name'] == 'Test User'
            assert result['sub'] == '1234567890'
            assert result['email_verified'] is True
            assert result['picture'] == 'https://example.com/photo.jpg'
    
    @pytest.mark.asyncio
    async def test_verify_google_token_invalid_issuer(self):
        """Test that verify_google_token raises error for invalid issuer."""
        mock_idinfo = {
            'iss': 'invalid-issuer.com',
            'email': 'user@example.com',
            'sub': '1234567890'
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            with pytest.raises(ValueError, match="Invalid token issuer"):
                await verify_google_token('invalid-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_verification_fails(self):
        """Test that verify_google_token raises error when Google verification fails."""
        with patch('app.core.security.id_token.verify_oauth2_token', side_effect=ValueError("Token expired")):
            with pytest.raises(ValueError, match="Invalid Google token"):
                await verify_google_token('expired-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_missing_fields(self):
        """Test that verify_google_token handles missing optional fields."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': '1234567890'
            # Missing email_verified and picture
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-token')
            
            assert result['email'] == 'user@example.com'
            assert result['name'] == 'Test User'
            assert result['sub'] == '1234567890'
            assert result['email_verified'] is False  # Default value
            assert result['picture'] is None

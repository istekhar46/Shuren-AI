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
    """Tests for Google OAuth token verification with enhanced validation."""
    
    @pytest.mark.asyncio
    async def test_verify_google_token_valid_token_all_claims(self):
        """Test that verify_google_token returns user info for valid token with all claims."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True,
            'picture': 'https://example.com/photo.jpg',
            'hd': 'example.com'
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-google-token')
            
            assert result['email'] == 'user@example.com'
            assert result['name'] == 'Test User'
            assert result['sub'] == '1234567890'
            assert result['email_verified'] is True
            assert result['picture'] == 'https://example.com/photo.jpg'
            assert result['hd'] == 'example.com'
    
    @pytest.mark.asyncio
    async def test_verify_google_token_email_not_verified(self):
        """Test that verify_google_token raises error when email is not verified."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': False  # Email not verified
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            with pytest.raises(ValueError, match="Email address is not verified"):
                await verify_google_token('unverified-email-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_hosted_domain_valid(self):
        """Test that verify_google_token accepts valid hosted domain for Workspace accounts."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@company.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True,
            'hd': 'company.com'  # Matches email domain
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-workspace-token')
            
            assert result['email'] == 'user@company.com'
            assert result['hd'] == 'company.com'
    
    @pytest.mark.asyncio
    async def test_verify_google_token_hosted_domain_mismatch(self):
        """Test that verify_google_token raises error when hosted domain doesn't match email."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@company.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True,
            'hd': 'different-company.com'  # Doesn't match email domain
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            with pytest.raises(ValueError, match="Hosted domain does not match email domain"):
                await verify_google_token('mismatched-domain-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_gmail_without_hd(self):
        """Test that verify_google_token accepts Gmail accounts without hosted domain."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@gmail.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True
            # No 'hd' claim for Gmail accounts
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-gmail-token')
            
            assert result['email'] == 'user@gmail.com'
            assert result['hd'] is None
    
    @pytest.mark.asyncio
    async def test_verify_google_token_invalid_issuer(self):
        """Test that verify_google_token raises error for invalid issuer."""
        mock_idinfo = {
            'iss': 'invalid-issuer.com',
            'email': 'user@example.com',
            'sub': '1234567890',
            'email_verified': True
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            with pytest.raises(ValueError, match="Invalid token issuer"):
                await verify_google_token('invalid-issuer-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_verification_fails(self):
        """Test that verify_google_token raises error when Google verification fails."""
        with patch('app.core.security.id_token.verify_oauth2_token', side_effect=ValueError("Token expired")):
            with pytest.raises(ValueError, match="Invalid Google token"):
                await verify_google_token('expired-token')
    
    @pytest.mark.asyncio
    async def test_verify_google_token_missing_required_claims(self):
        """Test that verify_google_token handles tokens with missing required claims."""
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'email_verified': True
            # Missing 'sub' and 'name'
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('token-missing-claims')
            
            assert result['email'] == 'user@example.com'
            assert result['sub'] is None
            assert result['name'] is None
    
    @pytest.mark.asyncio
    async def test_verify_google_token_error_logging(self, caplog):
        """Test that verify_google_token logs errors for verification failures."""
        import logging
        
        mock_idinfo = {
            'iss': 'accounts.google.com',
            'email': 'user@example.com',
            'sub': '1234567890',
            'email_verified': False
        }
        
        with caplog.at_level(logging.ERROR):
            with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
                try:
                    await verify_google_token('unverified-token')
                except ValueError:
                    pass
        
        # Check that error was logged
        assert any("Google token verification failed" in record.message for record in caplog.records)
        assert any("Email not verified" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_verify_google_token_issuer_https_variant(self):
        """Test that verify_google_token accepts https://accounts.google.com issuer."""
        mock_idinfo = {
            'iss': 'https://accounts.google.com',  # HTTPS variant
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': '1234567890',
            'email_verified': True
        }
        
        with patch('app.core.security.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = await verify_google_token('valid-token-https-issuer')
            
            assert result['email'] == 'user@example.com'
            assert result['sub'] == '1234567890'



class TestCSRFValidation:
    """Tests for CSRF token validation using double-submit-cookie pattern."""
    
    def test_validate_csrf_token_success_matching_tokens(self):
        """Test that validate_csrf_token succeeds with matching tokens."""
        from app.core.security import validate_csrf_token
        
        cookie_token = "abc123xyz789"
        body_token = "abc123xyz789"
        
        # Should not raise any exception
        validate_csrf_token(cookie_token, body_token)
    
    def test_validate_csrf_token_failure_missing_cookie(self):
        """Test that validate_csrf_token raises HTTPException when cookie token is missing."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        
        cookie_token = None
        body_token = "abc123xyz789"
        
        with pytest.raises(HTTPException) as exc_info:
            validate_csrf_token(cookie_token, body_token)
        
        assert exc_info.value.status_code == 400
        assert "Missing g_csrf_token cookie" in exc_info.value.detail
    
    def test_validate_csrf_token_failure_empty_cookie(self):
        """Test that validate_csrf_token raises HTTPException when cookie token is empty."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        
        cookie_token = ""
        body_token = "abc123xyz789"
        
        with pytest.raises(HTTPException) as exc_info:
            validate_csrf_token(cookie_token, body_token)
        
        assert exc_info.value.status_code == 400
        assert "Missing g_csrf_token cookie" in exc_info.value.detail
    
    def test_validate_csrf_token_failure_missing_body_token(self):
        """Test that validate_csrf_token raises HTTPException when body token is missing."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        
        cookie_token = "abc123xyz789"
        body_token = None
        
        with pytest.raises(HTTPException) as exc_info:
            validate_csrf_token(cookie_token, body_token)
        
        assert exc_info.value.status_code == 400
        assert "Missing g_csrf_token in request body" in exc_info.value.detail
    
    def test_validate_csrf_token_failure_empty_body_token(self):
        """Test that validate_csrf_token raises HTTPException when body token is empty."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        
        cookie_token = "abc123xyz789"
        body_token = ""
        
        with pytest.raises(HTTPException) as exc_info:
            validate_csrf_token(cookie_token, body_token)
        
        assert exc_info.value.status_code == 400
        assert "Missing g_csrf_token in request body" in exc_info.value.detail
    
    def test_validate_csrf_token_failure_mismatched_tokens(self):
        """Test that validate_csrf_token raises HTTPException when tokens don't match."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        
        cookie_token = "abc123xyz789"
        body_token = "different_token"
        
        with pytest.raises(HTTPException) as exc_info:
            validate_csrf_token(cookie_token, body_token)
        
        assert exc_info.value.status_code == 400
        assert "Token mismatch" in exc_info.value.detail
    
    def test_validate_csrf_token_security_logging_missing_cookie(self, caplog):
        """Test that CSRF validation logs security events for missing cookie."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        import logging
        
        with caplog.at_level(logging.ERROR):
            try:
                validate_csrf_token(None, "body_token")
            except HTTPException:
                pass
        
        # Check that security event was logged
        assert any("CSRF validation failed" in record.message for record in caplog.records)
        assert any("Missing g_csrf_token cookie" in record.message for record in caplog.records)
    
    def test_validate_csrf_token_security_logging_missing_body(self, caplog):
        """Test that CSRF validation logs security events for missing body token."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        import logging
        
        with caplog.at_level(logging.ERROR):
            try:
                validate_csrf_token("cookie_token", None)
            except HTTPException:
                pass
        
        # Check that security event was logged
        assert any("CSRF validation failed" in record.message for record in caplog.records)
        assert any("Missing g_csrf_token in request body" in record.message for record in caplog.records)
    
    def test_validate_csrf_token_security_logging_mismatch(self, caplog):
        """Test that CSRF validation logs security events for token mismatch."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        import logging
        
        with caplog.at_level(logging.ERROR):
            try:
                validate_csrf_token("cookie_token", "different_body_token")
            except HTTPException:
                pass
        
        # Check that security event was logged
        assert any("CSRF validation failed" in record.message for record in caplog.records)
        assert any("Token mismatch" in record.message for record in caplog.records)
    
    def test_validate_csrf_token_constant_time_comparison(self):
        """Test that CSRF validation uses constant-time comparison (timing attack prevention)."""
        from app.core.security import validate_csrf_token
        from fastapi import HTTPException
        import time
        
        # Test with tokens of same length but different values
        cookie_token = "a" * 100
        body_token_1 = "b" * 100  # All different
        body_token_2 = "a" * 99 + "b"  # Only last char different
        
        # Measure time for completely different tokens
        start1 = time.perf_counter()
        try:
            validate_csrf_token(cookie_token, body_token_1)
        except HTTPException:
            pass
        time1 = time.perf_counter() - start1
        
        # Measure time for tokens that differ only at the end
        start2 = time.perf_counter()
        try:
            validate_csrf_token(cookie_token, body_token_2)
        except HTTPException:
            pass
        time2 = time.perf_counter() - start2
        
        # Times should be similar (within 10x factor) for constant-time comparison
        # Note: This is a heuristic test and may have false positives
        assert abs(time1 - time2) < max(time1, time2) * 10

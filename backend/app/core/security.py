"""
Security utilities for authentication and authorization.

This module provides functions for:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Google OAuth token verification
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import bcrypt
import hmac
import logging
from jose import jwt, JWTError
from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi import HTTPException

from app.core.config import settings

# Configure logger for security events
logger = logging.getLogger(__name__)


# Bcrypt cost factor (rounds)
# Cost factor of 12 provides strong security while maintaining reasonable performance
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt with cost factor 12.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string suitable for database storage
        
    Example:
        >>> hashed = hash_password("mySecurePassword123")
        >>> print(hashed)
        $2b$12$...
    """
    # Convert password to bytes and hash with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("myPassword")
        >>> verify_password("myPassword", hashed)
        True
        >>> verify_password("wrongPassword", hashed)
        False
    """
    # Convert both to bytes for bcrypt
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def validate_csrf_token(cookie_token: Optional[str], body_token: Optional[str]) -> None:
    """
    Validate CSRF tokens using double-submit-cookie pattern.
    
    This function implements CSRF protection by verifying that the token from the cookie
    matches the token from the request body. Uses constant-time comparison to prevent
    timing attacks.
    
    Args:
        cookie_token: g_csrf_token from cookie
        body_token: g_csrf_token from request body
        
    Raises:
        HTTPException(400): If tokens are missing or don't match
        
    Security:
        - Uses hmac.compare_digest for constant-time comparison
        - Logs all validation failures for security monitoring
        - Does not expose token values in error messages
        
    Example:
        >>> validate_csrf_token("abc123", "abc123")  # Success, no exception
        >>> validate_csrf_token("abc123", "xyz789")  # Raises HTTPException
        >>> validate_csrf_token(None, "abc123")      # Raises HTTPException
    """
    # Check if cookie token is present
    if not cookie_token:
        logger.error(
            "CSRF validation failed: Missing g_csrf_token cookie",
            extra={"security_event": "csrf_validation_failure", "reason": "missing_cookie"}
        )
        raise HTTPException(
            status_code=400,
            detail="CSRF validation failed: Missing g_csrf_token cookie"
        )
    
    # Check if body token is present
    if not body_token:
        logger.error(
            "CSRF validation failed: Missing g_csrf_token in request body",
            extra={"security_event": "csrf_validation_failure", "reason": "missing_body_token"}
        )
        raise HTTPException(
            status_code=400,
            detail="CSRF validation failed: Missing g_csrf_token in request body"
        )
    
    # Compare tokens using constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(cookie_token, body_token):
        logger.error(
            "CSRF validation failed: Token mismatch",
            extra={
                "security_event": "csrf_validation_failure",
                "reason": "token_mismatch",
                "cookie_token_length": len(cookie_token),
                "body_token_length": len(body_token)
            }
        )
        raise HTTPException(
            status_code=400,
            detail="CSRF validation failed: Token mismatch"
        )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with HS256 algorithm.
    
    The token includes:
    - User-provided data (typically user_id)
    - Expiration timestamp (default: 24 hours from now)
    - Issued at timestamp
    
    Args:
        data: Dictionary of claims to include in token (e.g., {"user_id": "123"})
        expires_delta: Optional custom expiration time. If None, uses JWT_ACCESS_TOKEN_EXPIRE_HOURS from settings
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"user_id": "550e8400-e29b-41d4-a716-446655440000"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    
    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })
    
    # Encode and return token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Validates:
    - Token signature using JWT_SECRET_KEY
    - Token expiration
    - Token algorithm matches JWT_ALGORITHM
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Dictionary containing token payload (claims)
        
    Raises:
        JWTError: If token is invalid, expired, or signature verification fails
        
    Example:
        >>> token = create_access_token({"user_id": "123"})
        >>> payload = decode_access_token(token)
        >>> print(payload["user_id"])
        123
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    return payload


async def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google ID token and extract user information.
    
    Performs comprehensive verification:
    - Signature verification using Google's public keys
    - Audience (aud) claim validation
    - Issuer (iss) claim validation
    - Expiration (exp) claim validation
    - Email verification status check
    - Hosted domain (hd) validation for Workspace accounts
    
    Args:
        token: Google ID token string
        
    Returns:
        Dictionary with verified user information:
        {
            'sub': str,  # Google user ID (unique, immutable)
            'email': str,
            'email_verified': bool,
            'name': str,
            'picture': str,  # Optional
            'hd': str  # Optional, for Workspace accounts
        }
        
    Raises:
        ValueError: If token verification fails
        
    Example:
        >>> user_info = await verify_google_token(google_id_token)
        >>> print(user_info["email"])
        user@example.com
        >>> print(user_info["sub"])
        1234567890
    """
    try:
        # Verify the token using Google's verification endpoint
        # This automatically validates signature, expiration, and audience
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.error(
                "Google token verification failed: Invalid issuer",
                extra={
                    "security_event": "google_token_verification_failure",
                    "reason": "invalid_issuer",
                    "issuer": idinfo.get('iss')
                }
            )
            raise ValueError('Invalid token issuer')
        
        # Verify email is verified
        email_verified = idinfo.get('email_verified', False)
        if not email_verified:
            logger.error(
                "Google token verification failed: Email not verified",
                extra={
                    "security_event": "google_token_verification_failure",
                    "reason": "email_not_verified",
                    "email": idinfo.get('email')
                }
            )
            raise ValueError('Email address is not verified')
        
        # Validate hosted domain for Workspace accounts
        hd = idinfo.get('hd')
        email = idinfo.get('email')
        if hd and email:
            # Extract domain from email
            email_domain = email.split('@')[1] if '@' in email else None
            if email_domain and hd != email_domain:
                logger.error(
                    "Google token verification failed: Hosted domain mismatch",
                    extra={
                        "security_event": "google_token_verification_failure",
                        "reason": "hosted_domain_mismatch",
                        "hd_claim": hd,
                        "email_domain": email_domain
                    }
                )
                raise ValueError('Hosted domain does not match email domain')
        
        # Return user information with all required claims
        return {
            'sub': idinfo.get('sub'),  # Google user ID (unique, immutable)
            'email': email,
            'email_verified': email_verified,
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
            'hd': hd  # Hosted domain for Workspace accounts
        }
        
    except ValueError as e:
        # Token verification failed - log with sanitized information
        logger.error(
            f"Google token verification failed: {str(e)}",
            extra={
                "security_event": "google_token_verification_failure",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise ValueError(f"Invalid Google token: {str(e)}")

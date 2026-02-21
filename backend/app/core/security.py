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
from jose import jwt, JWTError
from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


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
    Verify a Google ID token and extract user information.
    
    Uses Google's official token verification to validate:
    - Token signature
    - Token expiration
    - Token audience (matches GOOGLE_CLIENT_ID)
    - Token issuer (Google)
    
    Args:
        token: Google ID token string from client
        
    Returns:
        Dictionary containing user information:
        - email: User's email address
        - name: User's full name
        - sub: Google user ID (unique identifier)
        - email_verified: Whether email is verified
        - picture: URL to user's profile picture (optional)
        
    Raises:
        ValueError: If token is invalid or verification fails
        
    Example:
        >>> user_info = await verify_google_token(google_id_token)
        >>> print(user_info["email"])
        user@example.com
        >>> print(user_info["sub"])
        1234567890
    """
    try:
        # Verify the token using Google's verification endpoint
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid token issuer')
        
        # Return user information
        return {
            'email': idinfo.get('email'),
            'name': idinfo.get('name'),
            'sub': idinfo.get('sub'),  # Google user ID
            'email_verified': idinfo.get('email_verified', False),
            'picture': idinfo.get('picture')
        }
        
    except ValueError as e:
        # Token verification failed
        raise ValueError(f"Invalid Google token: {str(e)}")

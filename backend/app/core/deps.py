"""
FastAPI dependencies for authentication and authorization.

This module provides dependency injection functions for:
- Extracting and validating JWT tokens from Authorization headers
- Fetching authenticated users from the database
- Checking for soft-deleted users
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


# HTTPBearer security scheme for Authorization header parsing
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    FastAPI dependency that extracts and validates JWT token, then fetches the user.
    
    This dependency:
    1. Extracts the JWT token from the Authorization header (Bearer scheme)
    2. Decodes and validates the token signature and expiration
    3. Extracts the user_id from the token payload
    4. Fetches the user from the database
    5. Checks that the user exists and is not soft-deleted
    
    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer security scheme
        db: AsyncSession database connection from get_db dependency
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException(401): If token is invalid, expired, missing user_id, 
                           user not found, or user is soft-deleted
        
    Example:
        @app.get("/api/v1/auth/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email, "name": current_user.full_name}
    """
    # Extract token from credentials
    token = credentials.credentials
    
    # Decode and validate JWT token
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("user_id")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Convert user_id string to UUID
        try:
            user_id = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: malformed user_id",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Fetch user from database with eager loading of onboarding_state
    # Use select() with where clause to filter by id and check for soft-delete
    from sqlalchemy.orm import selectinload
    
    stmt = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).options(
        selectinload(User.onboarding_state)  # Eagerly load onboarding_state to avoid lazy loading issues
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or has been deleted",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

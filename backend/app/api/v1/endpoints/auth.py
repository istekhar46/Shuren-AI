"""
Authentication endpoints for user registration, login, and OAuth.

This module provides REST API endpoints for:
- Email/password registration
- Email/password login
- Google OAuth authentication
- Current user retrieval
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_google_token
)
from app.db.session import get_db
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse
)


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Register a new user with email and password.
    
    Creates a new user account with:
    - Hashed password (bcrypt with cost factor 12)
    - Initial onboarding state at step 0
    - JWT access token for immediate authentication
    
    Args:
        user_data: UserRegister schema with email, password, and full_name
        db: Database session from dependency injection
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException(400): If email already exists
        HTTPException(422): If validation fails (handled by FastAPI)
    """
    # Check if email already exists
    stmt = select(User).where(
        User.email == user_data.email,
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        oauth_provider=None,
        oauth_provider_user_id=None,
        is_active=True
    )
    
    db.add(new_user)
    await db.flush()  # Flush to get user.id
    
    # Create onboarding state at step 0
    onboarding_state = OnboardingState(
        user_id=new_user.id,
        current_step=0,
        is_complete=False,
        step_data={}
    )
    
    db.add(onboarding_state)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(data={"user_id": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(new_user.id)
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate user with email and password.
    
    Validates credentials and returns JWT access token for authenticated requests.
    
    Args:
        credentials: UserLogin schema with email and password
        db: Database session from dependency injection
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException(401): If credentials are invalid or user not found
    """
    # Fetch user by email
    stmt = select(User).where(
        User.email == credentials.email,
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Check if user exists and has a password (not OAuth-only user)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"user_id": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id)
    )


@router.post("/google", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate user with Google OAuth.
    
    Verifies Google ID token and either:
    - Returns JWT for existing user
    - Creates new user account and returns JWT
    
    Args:
        auth_request: GoogleAuthRequest schema with Google ID token
        db: Database session from dependency injection
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException(401): If Google token is invalid
        HTTPException(422): If validation fails
    """
    # Verify Google ID token
    try:
        user_info = await verify_google_token(auth_request.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Extract user information from token
    email = user_info.get('email')
    name = user_info.get('name')
    google_user_id = user_info.get('sub')
    
    if not email or not google_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token: missing required fields"
        )
    
    # Check if user exists by email or OAuth provider credentials
    stmt = select(User).where(
        (
            (User.email == email) |
            (
                (User.oauth_provider == 'google') &
                (User.oauth_provider_user_id == google_user_id)
            )
        ),
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # If user doesn't exist, create new user
    if not user:
        new_user = User(
            email=email,
            hashed_password=None,  # OAuth users don't have passwords
            full_name=name or email.split('@')[0],  # Use email prefix if name not provided
            oauth_provider='google',
            oauth_provider_user_id=google_user_id,
            is_active=True
        )
        
        db.add(new_user)
        await db.flush()  # Flush to get user.id
        
        # Create onboarding state for new user
        onboarding_state = OnboardingState(
            user_id=new_user.id,
            current_step=0,
            is_complete=False,
            step_data={}
        )
        
        db.add(onboarding_state)
        await db.commit()
        await db.refresh(new_user)
        
        user = new_user
    
    # Generate JWT token
    access_token = create_access_token(data={"user_id": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id)
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        UserResponse with user data (id, email, full_name, oauth_provider, is_active, created_at)
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        oauth_provider=current_user.oauth_provider,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

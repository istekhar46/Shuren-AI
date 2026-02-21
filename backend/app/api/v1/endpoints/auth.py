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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_google_token,
    validate_csrf_token
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
    
    # Create onboarding state at step 1
    onboarding_state = OnboardingState(
        user_id=new_user.id,
        current_step=1,
        is_complete=False
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
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate user with Google OAuth using Google Identity Services.
    
    Implements secure OAuth flow with:
    - CSRF protection via double-submit-cookie pattern
    - Comprehensive Google ID token verification
    - User account creation or lookup using immutable Google sub claim
    
    Verifies Google ID token and either:
    - Returns JWT for existing user
    - Creates new user account with onboarding state and returns JWT
    
    Args:
        auth_request: GoogleAuthRequest schema with credential (ID token) and g_csrf_token
        request: FastAPI Request object for cookie access
        db: Database session from dependency injection
        
    Returns:
        TokenResponse with access_token, token_type, and user_id
        
    Raises:
        HTTPException(400): If CSRF validation fails
        HTTPException(401): If Google token is invalid or email not verified
        HTTPException(422): If validation fails
    """
    # Step 1: Validate CSRF token using double-submit-cookie pattern
    # Note: CSRF token is optional for button-only flow (not One Tap)
    # Google Identity Services only sets g_csrf_token cookie for One Tap flow
    cookie_token = request.cookies.get("g_csrf_token")
    body_token = auth_request.g_csrf_token
    
    # Only validate CSRF if both tokens are present
    # If button flow is used (no cookie), skip CSRF validation
    if cookie_token or body_token:
        validate_csrf_token(cookie_token, body_token)
    
    # Step 2: Verify Google ID token
    try:
        user_info = await verify_google_token(auth_request.credential)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Step 3: Extract user information from verified token
    email = user_info.get('email')
    name = user_info.get('name')
    google_sub = user_info.get('sub')  # Immutable Google user ID
    picture = user_info.get('picture')
    
    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token: missing required fields"
        )
    
    # Step 4: Query user by OAuth provider credentials only (not email)
    # This ensures we use the immutable sub claim for identification
    stmt = select(User).where(
        (User.oauth_provider == 'google') &
        (User.oauth_provider_user_id == google_sub),
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Step 5: If no OAuth user found, check if email exists (for account linking)
    if not user:
        # Check if user with this email already exists
        email_stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None)
        )
        email_result = await db.execute(email_stmt)
        existing_user = email_result.scalar_one_or_none()
        
        if existing_user:
            # Link Google OAuth to existing account
            existing_user.oauth_provider = 'google'
            existing_user.oauth_provider_user_id = google_sub
            await db.commit()
            await db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            new_user = User(
                email=email,
                hashed_password=None,  # OAuth users don't have passwords
                full_name=name or email.split('@')[0],  # Use email prefix if name not provided
                oauth_provider='google',
                oauth_provider_user_id=google_sub,  # Use sub claim (not email)
                is_active=True
            )
            
            db.add(new_user)
            await db.flush()  # Flush to get user.id
            
            # Create onboarding state for new user
            onboarding_state = OnboardingState(
                user_id=new_user.id,
                current_step=1,
                is_complete=False
            )
            
            db.add(onboarding_state)
            await db.commit()
            await db.refresh(new_user)
            
            user = new_user
    
    # Step 6: Generate JWT token
    access_token = create_access_token(data={"user_id": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id)
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """
    Get current authenticated user information with access control.
    
    Requires valid JWT token in Authorization header.
    Returns user data including access control information based on
    onboarding completion status.
    
    Args:
        current_user: User object from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        UserResponse with user data, onboarding_completed status, and access_control
    """
    from app.schemas.auth import AccessControl
    from app.services.onboarding_service import OnboardingService
    
    # Build access control object based on onboarding status
    if current_user.onboarding_completed:
        # All features unlocked for completed users
        access_control = AccessControl(
            can_access_dashboard=True,
            can_access_workouts=True,
            can_access_meals=True,
            can_access_chat=True,
            can_access_profile=True,
            locked_features=[],
            unlock_message=None,
            onboarding_progress=None
        )
    else:
        # Get onboarding progress for incomplete users
        onboarding_service = OnboardingService(db)
        try:
            progress = await onboarding_service.get_progress(current_user.id)
            onboarding_progress = {
                "current_state": progress.current_state,
                "total_states": progress.total_states,
                "completion_percentage": progress.completion_percentage
            }
        except Exception:
            # If progress can't be loaded, provide minimal info
            onboarding_progress = {
                "current_state": 0,
                "total_states": 9,
                "completion_percentage": 0
            }
        
        # Only chat is accessible during onboarding
        access_control = AccessControl(
            can_access_dashboard=False,
            can_access_workouts=False,
            can_access_meals=False,
            can_access_chat=True,  # Always true
            can_access_profile=False,
            locked_features=["dashboard", "workouts", "meals", "profile"],
            unlock_message="Complete onboarding to unlock all features",
            onboarding_progress=onboarding_progress
        )
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        oauth_provider=current_user.oauth_provider,
        is_active=current_user.is_active,
        onboarding_completed=current_user.onboarding_completed,
        access_control=access_control,
        created_at=current_user.created_at
    )

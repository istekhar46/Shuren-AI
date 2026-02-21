"""Authentication Pydantic schemas"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration with email/password"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class UserLogin(BaseModel):
    """Schema for user login with email/password"""
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication request using Google Identity Services"""
    credential: str = Field(
        ...,
        min_length=1,
        description="Google ID token (credential) from OAuth flow"
    )
    g_csrf_token: str = Field(
        default="",
        description="CSRF token for double-submit-cookie validation (optional for button flow)"
    )


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class AccessControl(BaseModel):
    """Schema for user access control based on onboarding status"""
    can_access_dashboard: bool
    can_access_workouts: bool
    can_access_meals: bool
    can_access_chat: bool
    can_access_profile: bool
    locked_features: list[str]
    unlock_message: str | None = None
    onboarding_progress: dict[str, Any] | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "can_access_dashboard": False,
                "can_access_workouts": False,
                "can_access_meals": False,
                "can_access_chat": True,
                "can_access_profile": False,
                "locked_features": ["dashboard", "workouts", "meals", "profile"],
                "unlock_message": "Complete onboarding to unlock all features",
                "onboarding_progress": {
                    "current_state": 3,
                    "total_states": 9,
                    "completion_percentage": 33
                }
            }
        }


class UserResponse(BaseModel):
    """Schema for user data response"""
    id: str
    email: str
    full_name: str
    oauth_provider: Optional[str] = None
    is_active: bool
    onboarding_completed: bool
    access_control: AccessControl
    created_at: datetime
    
    class Config:
        from_attributes = True

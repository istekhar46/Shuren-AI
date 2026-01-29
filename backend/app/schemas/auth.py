"""Authentication Pydantic schemas"""

from datetime import datetime
from typing import Optional

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
    """Schema for Google OAuth authentication"""
    id_token: str = Field(..., description="Google ID token from OAuth flow")


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
    """Schema for user data response"""
    id: str
    email: str
    full_name: str
    oauth_provider: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

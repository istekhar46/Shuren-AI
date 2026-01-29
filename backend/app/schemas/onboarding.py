"""Onboarding Pydantic schemas"""

from typing import Any

from pydantic import BaseModel


class OnboardingStateResponse(BaseModel):
    """Schema for onboarding state response"""
    id: str
    user_id: str
    current_step: int
    is_complete: bool
    step_data: dict[str, Any]
    
    class Config:
        from_attributes = True


class OnboardingStepRequest(BaseModel):
    """Schema for submitting onboarding step data"""
    step: int
    data: dict[str, Any]


class OnboardingStepResponse(BaseModel):
    """Schema for onboarding step submission response"""
    current_step: int
    is_complete: bool
    message: str

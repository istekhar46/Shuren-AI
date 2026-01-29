"""Pydantic schemas package"""

from .auth import (
    GoogleAuthRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from .onboarding import (
    OnboardingStateResponse,
    OnboardingStepRequest,
    OnboardingStepResponse,
)
from .profile import (
    DietaryPreferenceSchema,
    FitnessGoalSchema,
    HydrationPreferenceSchema,
    LifestyleBaselineSchema,
    MealPlanSchema,
    MealScheduleSchema,
    PhysicalConstraintSchema,
    ProfileUpdateRequest,
    UserProfileResponse,
    WorkoutScheduleSchema,
)

__all__ = [
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "GoogleAuthRequest",
    "TokenResponse",
    "UserResponse",
    # Onboarding schemas
    "OnboardingStateResponse",
    "OnboardingStepRequest",
    "OnboardingStepResponse",
    # Profile schemas
    "FitnessGoalSchema",
    "PhysicalConstraintSchema",
    "DietaryPreferenceSchema",
    "MealPlanSchema",
    "MealScheduleSchema",
    "WorkoutScheduleSchema",
    "HydrationPreferenceSchema",
    "LifestyleBaselineSchema",
    "UserProfileResponse",
    "ProfileUpdateRequest",
]

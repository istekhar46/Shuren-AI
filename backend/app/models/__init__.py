"""Database models package"""

from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile, UserProfileVersion
from app.models.preferences import (
    FitnessGoal,
    PhysicalConstraint,
    DietaryPreference,
    MealPlan,
    MealSchedule,
    WorkoutSchedule,
    HydrationPreference,
    LifestyleBaseline,
)

__all__ = [
    "User",
    "OnboardingState",
    "UserProfile",
    "UserProfileVersion",
    "FitnessGoal",
    "PhysicalConstraint",
    "DietaryPreference",
    "MealPlan",
    "MealSchedule",
    "WorkoutSchedule",
    "HydrationPreference",
    "LifestyleBaseline",
]

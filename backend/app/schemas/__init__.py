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
from .workout import (
    ExerciseLibraryBase,
    ExerciseUpdate,
    WorkoutDayResponse,
    WorkoutDayUpdate,
    WorkoutExerciseResponse,
    WorkoutPlanResponse,
    WorkoutPlanUpdate,
    WorkoutScheduleResponse,
    WorkoutScheduleUpdate,
)
from .meal import (
    MealPlanResponse,
    MealPlanUpdate,
    MealScheduleItemResponse,
    MealScheduleItemUpdate,
    MealScheduleResponse,
    MealScheduleUpdate,
)
from .chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatHistoryResponse,
)
from .error import (
    ErrorResponse,
    ValidationErrorDetail,
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
    # Workout schemas
    "ExerciseLibraryBase",
    "WorkoutExerciseResponse",
    "WorkoutDayResponse",
    "WorkoutPlanResponse",
    "WorkoutScheduleResponse",
    "ExerciseUpdate",
    "WorkoutDayUpdate",
    "WorkoutPlanUpdate",
    "WorkoutScheduleUpdate",
    # Meal schemas
    "MealPlanResponse",
    "MealPlanUpdate",
    "MealScheduleItemResponse",
    "MealScheduleItemUpdate",
    "MealScheduleResponse",
    "MealScheduleUpdate",
    # Chat schemas
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatHistoryResponse",
    # Error schemas
    "ErrorResponse",
    "ValidationErrorDetail",
]

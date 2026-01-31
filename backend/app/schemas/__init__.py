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
from .dish import (
    DishBase,
    DishIngredientResponse,
    DishResponse,
    DishSummaryResponse,
    IngredientBase,
    IngredientResponse,
)
from .meal_template import (
    DayMealsResponse,
    DishSwapRequest,
    MealSlotResponse,
    MealTemplateResponse,
    NextMealResponse,
    TemplateRegenerateRequest,
    TemplateMealResponse,
    TodayMealsResponse,
)
from .shopping_list import (
    ShoppingListCategory,
    ShoppingListIngredient,
    ShoppingListResponse,
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
    # Dish schemas
    "IngredientBase",
    "IngredientResponse",
    "DishIngredientResponse",
    "DishBase",
    "DishResponse",
    "DishSummaryResponse",
    # Meal template schemas
    "TemplateMealResponse",
    "MealSlotResponse",
    "DayMealsResponse",
    "MealTemplateResponse",
    "TodayMealsResponse",
    "NextMealResponse",
    "TemplateRegenerateRequest",
    "DishSwapRequest",
    # Shopping list schemas
    "ShoppingListIngredient",
    "ShoppingListCategory",
    "ShoppingListResponse",
    # Error schemas
    "ErrorResponse",
    "ValidationErrorDetail",
]

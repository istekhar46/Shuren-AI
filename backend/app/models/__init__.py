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
from app.models.workout import (
    WorkoutPlan,
    WorkoutDay,
    WorkoutExercise,
    ExerciseLibrary,
)
from app.models.chat import (
    ChatSession,
    ChatMessage,
)
from app.models.conversation import ConversationMessage
from app.models.dish import (
    Dish,
    Ingredient,
    DishIngredient,
)
from app.models.meal_template import (
    MealTemplate,
    TemplateMeal,
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
    "WorkoutPlan",
    "WorkoutDay",
    "WorkoutExercise",
    "ExerciseLibrary",
    "ChatSession",
    "ChatMessage",
    "ConversationMessage",
    "Dish",
    "Ingredient",
    "DishIngredient",
    "MealTemplate",
    "TemplateMeal",
]

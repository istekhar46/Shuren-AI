"""Onboarding service for managing user onboarding flow."""

import logging
from datetime import time
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.onboarding import OnboardingState
from app.models.preferences import (
    DietaryPreference,
    FitnessGoal,
    HydrationPreference,
    LifestyleBaseline,
    MealPlan,
    MealSchedule,
    PhysicalConstraint,
    WorkoutSchedule,
)
from app.models.profile import UserProfile, UserProfileVersion
from app.schemas.onboarding import StateInfo
from app.services.agent_orchestrator import AgentType

logger = logging.getLogger(__name__)


# State metadata for 9-state onboarding flow
# Provides rich metadata for each onboarding state including name, description,
# agent type, and required fields. Used by progress endpoint and UI rendering.
# This consolidates the previous 11-step flow into 9 states:
# - Old step 1 (basic info) removed (moved to registration)
# - Old steps 4 & 5 merged into new state 3
# - Remaining steps renumbered 1-9
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="workout_planning",
        description="Tell us about your current fitness level",
        required_fields=["fitness_level"]
    ),
    2: StateInfo(
        state_number=2,
        name="Primary Fitness Goals",
        agent="workout_planning",
        description="What are your fitness goals?",
        required_fields=["goals"]
    ),
    3: StateInfo(
        state_number=3,
        name="Workout Preferences & Constraints",
        agent="workout_planning",
        description="Tell us about your equipment, injuries, and limitations",
        required_fields=["equipment", "injuries", "limitations"]
    ),
    4: StateInfo(
        state_number=4,
        name="Diet Preferences & Restrictions",
        agent="diet_planning",
        description="Share your dietary preferences and restrictions",
        required_fields=["diet_type", "allergies", "intolerances", "dislikes"]
    ),
    5: StateInfo(
        state_number=5,
        name="Fixed Meal Plan Selection",
        agent="diet_planning",
        description="Set your daily calorie and macro targets",
        required_fields=["daily_calorie_target", "protein_percentage", "carbs_percentage", "fats_percentage"]
    ),
    6: StateInfo(
        state_number=6,
        name="Meal Timing Schedule",
        agent="scheduler",
        description="When do you want to eat your meals?",
        required_fields=["meals"]
    ),
    7: StateInfo(
        state_number=7,
        name="Workout Schedule",
        agent="scheduler",
        description="When do you want to work out?",
        required_fields=["workouts"]
    ),
    8: StateInfo(
        state_number=8,
        name="Hydration Schedule",
        agent="scheduler",
        description="Set your daily water intake goals",
        required_fields=["daily_water_target_ml"]
    ),
    9: StateInfo(
        state_number=9,
        name="Supplement Preferences",
        agent="supplement",
        description="Tell us about your supplement preferences (optional)",
        required_fields=["interested_in_supplements"]
    ),
}


# State to Agent mapping for onboarding chat routing
# Maps each onboarding state (1-9) to the specialized agent that handles it.
# Used by POST /api/v1/chat/onboarding endpoint to route messages to the correct agent.
STATE_TO_AGENT_MAP = {
    1: AgentType.WORKOUT,      # State 1: Fitness Level Assessment
    2: AgentType.WORKOUT,      # State 2: Primary Fitness Goals
    3: AgentType.WORKOUT,      # State 3: Workout Preferences & Constraints (merged from old steps 4 & 5)
    4: AgentType.DIET,         # State 4: Diet Preferences & Restrictions
    5: AgentType.DIET,         # State 5: Fixed Meal Plan Selection
    6: AgentType.SCHEDULER,    # State 6: Meal Timing Schedule
    7: AgentType.SCHEDULER,    # State 7: Workout Schedule
    8: AgentType.SCHEDULER,    # State 8: Hydration Schedule
    9: AgentType.SUPPLEMENT,   # State 9: Supplement Preferences (optional)
}


class OnboardingValidationError(Exception):
    """Exception raised when onboarding step validation fails.
    
    This exception is raised by OnboardingService validators when
    step data doesn't meet validation requirements. It includes
    both a human-readable message and the field that caused the error.
    
    Attributes:
        message: Human-readable error message
        field: Name of the field that failed validation (optional)
    """
    
    def __init__(self, message: str, field: str | None = None):
        """Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Name of the field that failed validation (optional)
        """
        self.message = message
        self.field = field
        super().__init__(self.message)


class OnboardingService:
    """Service for managing user onboarding flow.
    
    Handles step-by-step onboarding process with validation,
    state management, and profile creation upon completion.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize onboarding service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_onboarding_state(self, user_id: UUID) -> OnboardingState | None:
        """Retrieve current onboarding state for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            OnboardingState if found, None otherwise
        """
        result = await self.db.execute(
            select(OnboardingState)
            .where(
                OnboardingState.user_id == user_id,
                OnboardingState.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_progress(self, user_id: UUID) -> "OnboardingProgress":
        """Get rich progress metadata for UI.
        
        Calculates completed states from step_data JSONB, retrieves state
        metadata, calculates completion percentage, and determines if
        onboarding can be completed.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            OnboardingProgress with current state, completed states,
            state metadata, and completion percentage
            
        Raises:
            OnboardingValidationError: If onboarding state not found
        """
        from app.schemas.onboarding import OnboardingProgress
        
        # Load onboarding state
        state = await self.get_onboarding_state(user_id)
        if not state:
            raise OnboardingValidationError("Onboarding state not found")
        
        # Extract completed states from step_data (states 1-9)
        completed = []
        if state.step_data:
            for i in range(1, 10):
                if f"step_{i}" in state.step_data:
                    completed.append(i)
        
        # Get current and next state metadata
        current_info = STATE_METADATA[state.current_step]
        next_state = state.current_step + 1 if state.current_step < 9 else None
        next_info = STATE_METADATA.get(next_state) if next_state else None
        
        # Calculate completion percentage
        percentage = int((len(completed) / 9) * 100)
        
        # Check if can complete (all 9 states done)
        can_complete = len(completed) == 9
        
        return OnboardingProgress(
            current_state=state.current_step,
            total_states=9,
            completed_states=completed,
            current_state_info=current_info,
            next_state_info=next_info,
            is_complete=state.is_complete,
            completion_percentage=percentage,
            can_complete=can_complete
        )
    
    async def can_complete_onboarding(self, user_id: UUID) -> bool:
        """Check if all required states are complete.
        
        Verifies that all 9 states have data in step_data JSONB field.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if all 9 states have data, False otherwise
            
        Raises:
            OnboardingValidationError: If onboarding state not found
        """
        state = await self.get_onboarding_state(user_id)
        if not state:
            raise OnboardingValidationError("Onboarding state not found")
        
        # Check if all 9 states have data
        if not state.step_data:
            return False
        
        for i in range(1, 10):
            if f"step_{i}" not in state.step_data:
                return False
        
        return True
    
    async def save_onboarding_step(
        self,
        user_id: UUID,
        step: int,
        data: dict[str, Any],
        agent_type: str | None = None
    ) -> OnboardingState:
        """Save onboarding step data with validation.
        
        Validates step data according to step-specific rules,
        saves to step_data JSONB field, and advances current_step.
        Tracks agent routing history for analytics and debugging.
        
        Args:
            user_id: User's unique identifier
            step: Step number (1-11)
            data: Step data to validate and save
            agent_type: Optional agent type that handled this state (for tracking)
            
        Returns:
            Updated OnboardingState
            
        Raises:
            OnboardingValidationError: If step data is invalid
        """
        # Get current onboarding state
        onboarding_state = await self.get_onboarding_state(user_id)
        if not onboarding_state:
            raise OnboardingValidationError("Onboarding state not found")
        
        # Validate step number
        if step < 1 or step > 11:
            raise OnboardingValidationError(f"Invalid step number: {step}")
        
        # Validate step data
        self._validate_step_data(step, data)
        
        # Update step_data
        if not onboarding_state.step_data:
            onboarding_state.step_data = {}
        
        onboarding_state.step_data[f"step_{step}"] = data
        
        # Track state change in agent_history if state is advancing
        old_step = onboarding_state.current_step
        if step > onboarding_state.current_step:
            onboarding_state.current_step = step
            
            # Record agent routing history
            if agent_type:
                if not onboarding_state.agent_history:
                    onboarding_state.agent_history = []
                
                # Add history entry
                from datetime import datetime, timezone
                history_entry = {
                    "state": step,
                    "agent": agent_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "previous_state": old_step
                }
                onboarding_state.agent_history.append(history_entry)
                
                # Mark as modified for SQLAlchemy to detect JSONB change
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(onboarding_state, "agent_history")
                
                logger.info(
                    f"Agent routing history updated: state {old_step} -> {step} via {agent_type}",
                    extra={
                        "user_id": str(user_id),
                        "agent": agent_type,
                        "old_state": old_step,
                        "new_state": step
                    }
                )
        
        # Mark step_data as modified for SQLAlchemy to detect JSONB change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(onboarding_state, "step_data")
        
        await self.db.commit()
        await self.db.refresh(onboarding_state)
        
        return onboarding_state
    
    def _validate_step_data(self, step: int, data: dict[str, Any]) -> None:
        """Validate step-specific data for 9-state onboarding.
        
        Args:
            step: Step number (1-9)
            data: Step data to validate
            
        Raises:
            OnboardingValidationError: If validation fails
        """
        validators = {
            1: self._validate_step_2_fitness_level,           # State 1: Fitness Level
            2: self._validate_step_3_fitness_goals,            # State 2: Fitness Goals
            3: self._validate_state_3_workout_constraints,     # State 3: Workout Constraints (merged)
            4: self._validate_step_6_dietary_preferences,      # State 4: Dietary Preferences
            5: self._validate_step_7_meal_planning,            # State 5: Meal Plan
            6: self._validate_step_8_meal_schedule,            # State 6: Meal Schedule
            7: self._validate_step_9_workout_schedule,         # State 7: Workout Schedule
            8: self._validate_step_10_hydration,               # State 8: Hydration
            9: self._validate_state_9_supplements,             # State 9: Supplements (NEW)
        }
        
        validator = validators.get(step)
        if validator:
            validator(data)
    
    def _validate_step_1_basic_info(self, data: dict[str, Any]) -> None:
        """Validate step 1: Basic info (age, gender, height, weight)."""
        required_fields = ["age", "gender", "height_cm", "weight_kg"]
        for field in required_fields:
            if field not in data:
                raise OnboardingValidationError(f"Missing required field: {field}", field)
        
        # Validate age
        age = data["age"]
        if not isinstance(age, int) or age < 13 or age > 100:
            raise OnboardingValidationError("Age must be between 13 and 100", "age")
        
        # Validate gender
        valid_genders = ["male", "female", "other"]
        if data["gender"] not in valid_genders:
            raise OnboardingValidationError(
                f"Gender must be one of: {', '.join(valid_genders)}",
                "gender"
            )
        
        # Validate height
        height = data["height_cm"]
        if not isinstance(height, (int, float)) or height < 100 or height > 250:
            raise OnboardingValidationError("Height must be between 100 and 250 cm", "height_cm")
        
        # Validate weight
        weight = data["weight_kg"]
        if not isinstance(weight, (int, float)) or weight < 30 or weight > 300:
            raise OnboardingValidationError("Weight must be between 30 and 300 kg", "weight_kg")
    
    def _validate_step_2_fitness_level(self, data: dict[str, Any]) -> None:
        """Validate step 2: Fitness level."""
        if "fitness_level" not in data:
            raise OnboardingValidationError("Missing required field: fitness_level", "fitness_level")
        
        valid_levels = ["beginner", "intermediate", "advanced"]
        if data["fitness_level"] not in valid_levels:
            raise OnboardingValidationError(
                f"Fitness level must be one of: {', '.join(valid_levels)}",
                "fitness_level"
            )
    
    def _validate_step_3_fitness_goals(self, data: dict[str, Any]) -> None:
        """Validate step 3: Fitness goals."""
        if "goals" not in data or not isinstance(data["goals"], list):
            raise OnboardingValidationError("Goals must be a list", "goals")
        
        if len(data["goals"]) == 0:
            raise OnboardingValidationError("At least one goal is required", "goals")
        
        valid_goal_types = ["fat_loss", "muscle_gain", "general_fitness"]
        for i, goal in enumerate(data["goals"]):
            if not isinstance(goal, dict):
                raise OnboardingValidationError(f"Goal {i} must be an object", f"goals[{i}]")
            
            if "goal_type" not in goal:
                raise OnboardingValidationError(
                    f"Goal {i} missing goal_type",
                    f"goals[{i}].goal_type"
                )
            
            if goal["goal_type"] not in valid_goal_types:
                raise OnboardingValidationError(
                    f"Goal type must be one of: {', '.join(valid_goal_types)}",
                    f"goals[{i}].goal_type"
                )
    
    def _validate_state_3_workout_constraints(self, data: dict[str, Any]) -> None:
        """Validate state 3: Workout constraints (merged from steps 4 & 5).
        
        Combines target metrics and physical constraints validation.
        Validates equipment, injuries, limitations (required lists) and
        optional target_weight_kg and target_body_fat_percentage.
        """
        # Validate equipment (required)
        if "equipment" not in data or not isinstance(data["equipment"], list):
            raise OnboardingValidationError("Equipment must be a list", "equipment")
        
        # Validate injuries (required, can be empty)
        if "injuries" not in data or not isinstance(data["injuries"], list):
            raise OnboardingValidationError("Injuries must be a list", "injuries")
        
        # Validate limitations (required, can be empty)
        if "limitations" not in data or not isinstance(data["limitations"], list):
            raise OnboardingValidationError("Limitations must be a list", "limitations")
        
        # Validate optional target metrics
        if "target_weight_kg" in data and data["target_weight_kg"] is not None:
            weight = data["target_weight_kg"]
            if not isinstance(weight, (int, float)) or weight < 30 or weight > 300:
                raise OnboardingValidationError(
                    "Target weight must be between 30 and 300 kg",
                    "target_weight_kg"
                )
        
        if "target_body_fat_percentage" in data and data["target_body_fat_percentage"] is not None:
            bf = data["target_body_fat_percentage"]
            if not isinstance(bf, (int, float)) or bf < 1 or bf > 50:
                raise OnboardingValidationError(
                    "Target body fat percentage must be between 1 and 50",
                    "target_body_fat_percentage"
                )
    
    def _validate_step_4_target_metrics(self, data: dict[str, Any]) -> None:
        """Validate step 4: Target metrics (optional weight and body fat targets)."""
        # Target metrics are optional, but if provided must be valid
        if "target_weight_kg" in data and data["target_weight_kg"] is not None:
            weight = data["target_weight_kg"]
            if not isinstance(weight, (int, float)) or weight < 30 or weight > 300:
                raise OnboardingValidationError(
                    "Target weight must be between 30 and 300 kg",
                    "target_weight_kg"
                )
        
        if "target_body_fat_percentage" in data and data["target_body_fat_percentage"] is not None:
            bf = data["target_body_fat_percentage"]
            if not isinstance(bf, (int, float)) or bf < 1 or bf > 50:
                raise OnboardingValidationError(
                    "Target body fat percentage must be between 1 and 50",
                    "target_body_fat_percentage"
                )
    
    def _validate_step_5_physical_constraints(self, data: dict[str, Any]) -> None:
        """Validate step 5: Physical constraints (equipment, injuries, limitations)."""
        if "constraints" not in data or not isinstance(data["constraints"], list):
            raise OnboardingValidationError("Constraints must be a list", "constraints")
        
        # Constraints can be empty list
        valid_constraint_types = ["equipment", "injury", "limitation"]
        valid_severities = ["low", "medium", "high"]
        
        for i, constraint in enumerate(data["constraints"]):
            if not isinstance(constraint, dict):
                raise OnboardingValidationError(
                    f"Constraint {i} must be an object",
                    f"constraints[{i}]"
                )
            
            if "constraint_type" not in constraint:
                raise OnboardingValidationError(
                    f"Constraint {i} missing constraint_type",
                    f"constraints[{i}].constraint_type"
                )
            
            if constraint["constraint_type"] not in valid_constraint_types:
                raise OnboardingValidationError(
                    f"Constraint type must be one of: {', '.join(valid_constraint_types)}",
                    f"constraints[{i}].constraint_type"
                )
            
            if "description" not in constraint or not constraint["description"]:
                raise OnboardingValidationError(
                    f"Constraint {i} missing description",
                    f"constraints[{i}].description"
                )
            
            if "severity" in constraint and constraint["severity"] is not None:
                if constraint["severity"] not in valid_severities:
                    raise OnboardingValidationError(
                        f"Severity must be one of: {', '.join(valid_severities)}",
                        f"constraints[{i}].severity"
                    )
    
    def _validate_step_6_dietary_preferences(self, data: dict[str, Any]) -> None:
        """Validate step 6: Dietary preferences."""
        if "diet_type" not in data:
            raise OnboardingValidationError("Missing required field: diet_type", "diet_type")
        
        valid_diet_types = ["omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo"]
        if data["diet_type"] not in valid_diet_types:
            raise OnboardingValidationError(
                f"Diet type must be one of: {', '.join(valid_diet_types)}",
                "diet_type"
            )
        
        # Validate optional list fields
        for field in ["allergies", "intolerances", "dislikes"]:
            if field in data and not isinstance(data[field], list):
                raise OnboardingValidationError(f"{field} must be a list", field)
    
    def _validate_step_7_meal_planning(self, data: dict[str, Any]) -> None:
        """Validate step 7: Meal planning (calories and macros)."""
        required_fields = [
            "daily_calorie_target",
            "protein_percentage",
            "carbs_percentage",
            "fats_percentage"
        ]
        
        for field in required_fields:
            if field not in data:
                raise OnboardingValidationError(f"Missing required field: {field}", field)
        
        # Validate calorie target
        calories = data["daily_calorie_target"]
        if not isinstance(calories, int) or calories < 1000 or calories > 5000:
            raise OnboardingValidationError(
                "Daily calorie target must be between 1000 and 5000",
                "daily_calorie_target"
            )
        
        # Validate macro percentages
        protein = data["protein_percentage"]
        carbs = data["carbs_percentage"]
        fats = data["fats_percentage"]
        
        for name, value in [("protein", protein), ("carbs", carbs), ("fats", fats)]:
            if not isinstance(value, (int, float)) or value < 0 or value > 100:
                raise OnboardingValidationError(
                    f"{name.capitalize()} percentage must be between 0 and 100",
                    f"{name}_percentage"
                )
        
        # Validate macro sum equals 100
        total = protein + carbs + fats
        if abs(total - 100) > 0.01:  # Allow small floating point errors
            raise OnboardingValidationError(
                f"Macro percentages must sum to 100 (current sum: {total})",
                "macros"
            )
    
    def _validate_step_8_meal_schedule(self, data: dict[str, Any]) -> None:
        """Validate step 8: Meal schedule."""
        if "meals" not in data or not isinstance(data["meals"], list):
            raise OnboardingValidationError("Meals must be a list", "meals")
        
        if len(data["meals"]) == 0:
            raise OnboardingValidationError("At least one meal is required", "meals")
        
        for i, meal in enumerate(data["meals"]):
            if not isinstance(meal, dict):
                raise OnboardingValidationError(f"Meal {i} must be an object", f"meals[{i}]")
            
            if "meal_name" not in meal or not meal["meal_name"]:
                raise OnboardingValidationError(
                    f"Meal {i} missing meal_name",
                    f"meals[{i}].meal_name"
                )
            
            if "scheduled_time" not in meal:
                raise OnboardingValidationError(
                    f"Meal {i} missing scheduled_time",
                    f"meals[{i}].scheduled_time"
                )
            
            # Validate time format (HH:MM or HH:MM:SS)
            time_str = meal["scheduled_time"]
            if not isinstance(time_str, str):
                raise OnboardingValidationError(
                    f"Meal {i} scheduled_time must be a string",
                    f"meals[{i}].scheduled_time"
                )
            
            try:
                # Try to parse time string
                parts = time_str.split(":")
                if len(parts) < 2 or len(parts) > 3:
                    raise ValueError("Invalid time format")
                
                hour = int(parts[0])
                minute = int(parts[1])
                
                if hour < 0 or hour > 23:
                    raise ValueError("Hour must be 0-23")
                if minute < 0 or minute > 59:
                    raise ValueError("Minute must be 0-59")
                
            except (ValueError, AttributeError) as e:
                raise OnboardingValidationError(
                    f"Meal {i} scheduled_time must be in HH:MM format",
                    f"meals[{i}].scheduled_time"
                )
    
    def _validate_step_9_workout_schedule(self, data: dict[str, Any]) -> None:
        """Validate step 9: Workout schedule."""
        if "workouts" not in data or not isinstance(data["workouts"], list):
            raise OnboardingValidationError("Workouts must be a list", "workouts")
        
        if len(data["workouts"]) == 0:
            raise OnboardingValidationError("At least one workout is required", "workouts")
        
        for i, workout in enumerate(data["workouts"]):
            if not isinstance(workout, dict):
                raise OnboardingValidationError(
                    f"Workout {i} must be an object",
                    f"workouts[{i}]"
                )
            
            if "day_of_week" not in workout:
                raise OnboardingValidationError(
                    f"Workout {i} missing day_of_week",
                    f"workouts[{i}].day_of_week"
                )
            
            day = workout["day_of_week"]
            if not isinstance(day, int) or day < 0 or day > 6:
                raise OnboardingValidationError(
                    f"Workout {i} day_of_week must be 0-6 (Monday-Sunday)",
                    f"workouts[{i}].day_of_week"
                )
            
            if "scheduled_time" not in workout:
                raise OnboardingValidationError(
                    f"Workout {i} missing scheduled_time",
                    f"workouts[{i}].scheduled_time"
                )
            
            # Validate time format
            time_str = workout["scheduled_time"]
            if not isinstance(time_str, str):
                raise OnboardingValidationError(
                    f"Workout {i} scheduled_time must be a string",
                    f"workouts[{i}].scheduled_time"
                )
            
            try:
                parts = time_str.split(":")
                if len(parts) < 2 or len(parts) > 3:
                    raise ValueError("Invalid time format")
                
                hour = int(parts[0])
                minute = int(parts[1])
                
                if hour < 0 or hour > 23:
                    raise ValueError("Hour must be 0-23")
                if minute < 0 or minute > 59:
                    raise ValueError("Minute must be 0-59")
                
            except (ValueError, AttributeError):
                raise OnboardingValidationError(
                    f"Workout {i} scheduled_time must be in HH:MM format",
                    f"workouts[{i}].scheduled_time"
                )
    
    def _validate_step_10_hydration(self, data: dict[str, Any]) -> None:
        """Validate step 10: Hydration preferences."""
        if "daily_water_target_ml" not in data:
            raise OnboardingValidationError(
                "Missing required field: daily_water_target_ml",
                "daily_water_target_ml"
            )
        
        water_target = data["daily_water_target_ml"]
        if not isinstance(water_target, int) or water_target < 500 or water_target > 10000:
            raise OnboardingValidationError(
                "Daily water target must be between 500 and 10000 ml",
                "daily_water_target_ml"
            )
        
        # Validate optional reminder frequency
        if "reminder_frequency_minutes" in data:
            freq = data["reminder_frequency_minutes"]
            if not isinstance(freq, int) or freq < 15 or freq > 480:
                raise OnboardingValidationError(
                    "Reminder frequency must be between 15 and 480 minutes",
                    "reminder_frequency_minutes"
                )
    
    def _validate_step_11_lifestyle_baseline(self, data: dict[str, Any]) -> None:
        """Validate step 11: Lifestyle baseline (OLD - for backward compatibility).
        
        This validator is kept for backward compatibility with old 11-step data.
        New 9-state onboarding uses _validate_state_9_supplements instead.
        """
        required_fields = ["energy_level", "stress_level", "sleep_quality"]
        
        for field in required_fields:
            if field not in data:
                raise OnboardingValidationError(f"Missing required field: {field}", field)
            
            value = data[field]
            if not isinstance(value, int) or value < 1 or value > 10:
                raise OnboardingValidationError(
                    f"{field.replace('_', ' ').capitalize()} must be between 1 and 10",
                    field
                )
    
    def _validate_state_9_supplements(self, data: dict[str, Any]) -> None:
        """Validate state 9: Supplement preferences (NEW 9-state structure).
        
        State 9 is optional but validates supplement interest and current supplements.
        
        Args:
            data: Step data containing supplement preferences
            
        Raises:
            OnboardingValidationError: If validation fails
        """
        # interested_in_supplements is required
        if "interested_in_supplements" not in data:
            raise OnboardingValidationError(
                "Missing required field: interested_in_supplements",
                "interested_in_supplements"
            )
        
        interested = data["interested_in_supplements"]
        if not isinstance(interested, bool):
            raise OnboardingValidationError(
                "interested_in_supplements must be a boolean",
                "interested_in_supplements"
            )
        
        # current_supplements is optional but must be a list if provided
        if "current_supplements" in data:
            supplements = data["current_supplements"]
            if not isinstance(supplements, list):
                raise OnboardingValidationError(
                    "current_supplements must be a list",
                    "current_supplements"
                )
            
            # Validate each supplement is a string
            for i, supplement in enumerate(supplements):
                if not isinstance(supplement, str):
                    raise OnboardingValidationError(
                        f"Supplement at index {i} must be a string",
                        f"current_supplements[{i}]"
                    )

    async def complete_onboarding(self, user_id: UUID) -> UserProfile:
        """Complete onboarding and create locked user profile.
        
        Verifies all 9 states are complete, creates UserProfile with all
        related entities, creates initial ProfileVersion, and marks
        onboarding as complete.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Created UserProfile with all relationships loaded
            
        Raises:
            OnboardingValidationError: If onboarding is incomplete
        """
        # Get onboarding state
        onboarding_state = await self.get_onboarding_state(user_id)
        if not onboarding_state:
            raise OnboardingValidationError("Onboarding state not found")
        
        # Verify all 9 states are complete
        if onboarding_state.current_step < 9:
            raise OnboardingValidationError(
                f"Onboarding incomplete. Current step: {onboarding_state.current_step}, required: 9"
            )
        
        # Verify all step data exists
        step_data = onboarding_state.step_data
        for step_num in range(1, 10):
            if f"step_{step_num}" not in step_data:
                raise OnboardingValidationError(f"Missing data for step {step_num}")
        
        # Start transaction
        try:
            # Create UserProfile
            # State 1: Fitness Level
            profile = UserProfile(
                user_id=user_id,
                is_locked=True,
                fitness_level=step_data["step_1"]["fitness_level"]
            )
            self.db.add(profile)
            await self.db.flush()  # Get profile.id
            
            # State 2: Fitness Goals
            goals_data = step_data["step_2"]["goals"]
            
            for i, goal_data in enumerate(goals_data):
                goal = FitnessGoal(
                    profile_id=profile.id,
                    goal_type=goal_data["goal_type"],
                    target_weight_kg=None,  # Will be set from state 3 if provided
                    target_body_fat_percentage=None,  # Will be set from state 3 if provided
                    priority=i + 1
                )
                self.db.add(goal)
            
            # State 3: Workout Constraints (merged from old steps 4 & 5)
            constraints_data = step_data["step_3"]
            
            # Update goals with target metrics if provided
            if "target_weight_kg" in constraints_data or "target_body_fat_percentage" in constraints_data:
                # Flush to get goal IDs
                await self.db.flush()
                
                # Update first goal with targets
                result = await self.db.execute(
                    select(FitnessGoal)
                    .where(FitnessGoal.profile_id == profile.id)
                    .order_by(FitnessGoal.priority)
                )
                goals = result.scalars().all()
                if goals:
                    first_goal = goals[0]
                    if "target_weight_kg" in constraints_data:
                        first_goal.target_weight_kg = constraints_data["target_weight_kg"]
                    if "target_body_fat_percentage" in constraints_data:
                        first_goal.target_body_fat_percentage = constraints_data["target_body_fat_percentage"]
            
            # Create PhysicalConstraints from equipment, injuries, limitations
            equipment_list = constraints_data.get("equipment", [])
            for equipment in equipment_list:
                constraint = PhysicalConstraint(
                    profile_id=profile.id,
                    constraint_type="equipment",
                    description=equipment,
                    severity=None
                )
                self.db.add(constraint)
            
            injuries_list = constraints_data.get("injuries", [])
            for injury in injuries_list:
                constraint = PhysicalConstraint(
                    profile_id=profile.id,
                    constraint_type="injury",
                    description=injury,
                    severity="moderate"  # Default severity
                )
                self.db.add(constraint)
            
            limitations_list = constraints_data.get("limitations", [])
            for limitation in limitations_list:
                constraint = PhysicalConstraint(
                    profile_id=profile.id,
                    constraint_type="limitation",
                    description=limitation,
                    severity="moderate"  # Default severity
                )
                self.db.add(constraint)
            
            # State 4: Dietary Preferences
            diet_data = step_data["step_4"]
            dietary_pref = DietaryPreference(
                profile_id=profile.id,
                diet_type=diet_data["diet_type"],
                allergies=diet_data.get("allergies", []),
                intolerances=diet_data.get("intolerances", []),
                dislikes=diet_data.get("dislikes", [])
            )
            self.db.add(dietary_pref)
            
            # State 5: Meal Plan
            meal_plan_data = step_data["step_5"]
            meal_plan = MealPlan(
                profile_id=profile.id,
                daily_calorie_target=meal_plan_data["daily_calorie_target"],
                protein_percentage=Decimal(str(meal_plan_data["protein_percentage"])),
                carbs_percentage=Decimal(str(meal_plan_data["carbs_percentage"])),
                fats_percentage=Decimal(str(meal_plan_data["fats_percentage"]))
            )
            self.db.add(meal_plan)
            
            # State 6: Meal Schedule
            meals_data = step_data["step_6"]["meals"]
            for meal_data in meals_data:
                # Parse time string to time object
                time_str = meal_data["scheduled_time"]
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                
                meal_schedule = MealSchedule(
                    profile_id=profile.id,
                    meal_name=meal_data["meal_name"],
                    scheduled_time=time(hour, minute, second),
                    enable_notifications=meal_data.get("enable_notifications", True)
                )
                self.db.add(meal_schedule)
            
            # State 7: Workout Schedule
            workouts_data = step_data["step_7"]["workouts"]
            for workout_data in workouts_data:
                # Parse time string to time object
                time_str = workout_data["scheduled_time"]
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                
                workout_schedule = WorkoutSchedule(
                    profile_id=profile.id,
                    day_of_week=workout_data["day_of_week"],
                    scheduled_time=time(hour, minute, second),
                    enable_notifications=workout_data.get("enable_notifications", True)
                )
                self.db.add(workout_schedule)
            
            # State 8: Hydration
            hydration_data = step_data["step_8"]
            hydration_pref = HydrationPreference(
                profile_id=profile.id,
                daily_water_target_ml=hydration_data["daily_water_target_ml"],
                reminder_frequency_minutes=hydration_data.get("reminder_frequency_minutes", 60),
                enable_notifications=hydration_data.get("enable_notifications", True)
            )
            self.db.add(hydration_pref)
            
            # State 9: Supplements (optional - no database entity, just stored in step_data)
            # Supplements data is stored in step_data but doesn't create database entities
            # It's used by the Supplement Guidance Agent for recommendations
            
            # Flush to ensure all entities are created
            await self.db.flush()
            
            # Generate meal templates for weeks 1-4
            await self._generate_initial_meal_templates(profile.id)
            
            # Create initial ProfileVersion
            snapshot = await self._create_profile_snapshot(profile)
            profile_version = UserProfileVersion(
                profile_id=profile.id,
                version_number=1,
                change_reason="Onboarding completed",
                snapshot=snapshot
            )
            self.db.add(profile_version)
            
            # Mark onboarding as complete
            onboarding_state.is_complete = True
            
            # Commit transaction
            await self.db.commit()
            
            # Reload profile with all relationships
            await self.db.refresh(profile)
            result = await self.db.execute(
                select(UserProfile)
                .where(UserProfile.id == profile.id)
                .options(
                    selectinload(UserProfile.fitness_goals),
                    selectinload(UserProfile.physical_constraints),
                    selectinload(UserProfile.dietary_preferences),
                    selectinload(UserProfile.meal_plan),
                    selectinload(UserProfile.meal_schedules),
                    selectinload(UserProfile.workout_schedules),
                    selectinload(UserProfile.hydration_preferences),
                    selectinload(UserProfile.lifestyle_baseline),
                    selectinload(UserProfile.versions)
                )
            )
            profile = result.scalar_one()
            
            return profile
            
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def _generate_initial_meal_templates(self, profile_id: UUID) -> None:
        """Generate initial meal templates for weeks 1-4 during onboarding.
        
        This method attempts to generate meal templates but does not fail
        the onboarding process if template generation fails. Errors are
        logged for monitoring.
        
        Args:
            profile_id: UUID of the user profile
        """
        try:
            # Import here to avoid circular dependency
            from app.services.meal_template_service import MealTemplateService
            
            template_service = MealTemplateService(self.db)
            
            logger.info(f"Starting meal template generation for profile {profile_id}")
            
            # Temporarily unlock profile for template generation
            # (profile is locked by default during onboarding completion)
            result = await self.db.execute(
                select(UserProfile).where(UserProfile.id == profile_id)
            )
            profile = result.scalar_one()
            original_lock_state = profile.is_locked
            profile.is_locked = False
            await self.db.flush()
            
            # Generate templates for all 4 weeks
            for week in [1, 2, 3, 4]:
                try:
                    await template_service.generate_template(
                        profile_id=profile_id,
                        week_number=week,
                        preferences="Initial onboarding template"
                    )
                    logger.info(f"Generated meal template for week {week}, profile {profile_id}")
                except Exception as week_error:
                    logger.error(
                        f"Failed to generate meal template for week {week}, profile {profile_id}: {week_error}",
                        exc_info=True
                    )
                    # Continue with next week even if one fails
                    continue
            
            # Restore original lock state
            profile.is_locked = original_lock_state
            await self.db.flush()
            
            logger.info(f"Completed meal template generation for profile {profile_id}")
            
        except Exception as e:
            logger.error(
                f"Meal template generation failed for profile {profile_id}: {e}",
                exc_info=True
            )
            # Don't raise - allow onboarding to complete even if template generation fails
    
    async def _create_profile_snapshot(self, profile: UserProfile) -> dict[str, Any]:
        """Create a complete snapshot of profile state for versioning.
        
        Args:
            profile: UserProfile to snapshot
            
        Returns:
            Dictionary containing complete profile state
        """
        # Reload profile with all relationships
        result = await self.db.execute(
            select(UserProfile)
            .where(UserProfile.id == profile.id)
            .options(
                selectinload(UserProfile.fitness_goals),
                selectinload(UserProfile.physical_constraints),
                selectinload(UserProfile.dietary_preferences),
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_schedules),
                selectinload(UserProfile.workout_schedules),
                selectinload(UserProfile.hydration_preferences),
                selectinload(UserProfile.lifestyle_baseline)
            )
        )
        profile = result.scalar_one()
        
        snapshot = {
            "fitness_level": profile.fitness_level,
            "is_locked": profile.is_locked,
            "fitness_goals": [
                {
                    "goal_type": goal.goal_type,
                    "target_weight_kg": float(goal.target_weight_kg) if goal.target_weight_kg else None,
                    "target_body_fat_percentage": float(goal.target_body_fat_percentage) if goal.target_body_fat_percentage else None,
                    "priority": goal.priority
                }
                for goal in profile.fitness_goals
            ],
            "physical_constraints": [
                {
                    "constraint_type": constraint.constraint_type,
                    "description": constraint.description,
                    "severity": constraint.severity
                }
                for constraint in profile.physical_constraints
            ],
            "dietary_preferences": {
                "diet_type": profile.dietary_preferences.diet_type,
                "allergies": profile.dietary_preferences.allergies,
                "intolerances": profile.dietary_preferences.intolerances,
                "dislikes": profile.dietary_preferences.dislikes
            } if profile.dietary_preferences else None,
            "meal_plan": {
                "daily_calorie_target": profile.meal_plan.daily_calorie_target,
                "protein_percentage": float(profile.meal_plan.protein_percentage),
                "carbs_percentage": float(profile.meal_plan.carbs_percentage),
                "fats_percentage": float(profile.meal_plan.fats_percentage)
            } if profile.meal_plan else None,
            "meal_schedules": [
                {
                    "meal_name": schedule.meal_name,
                    "scheduled_time": schedule.scheduled_time.isoformat(),
                    "enable_notifications": schedule.enable_notifications
                }
                for schedule in profile.meal_schedules
            ],
            "workout_schedules": [
                {
                    "day_of_week": schedule.day_of_week,
                    "scheduled_time": schedule.scheduled_time.isoformat(),
                    "enable_notifications": schedule.enable_notifications
                }
                for schedule in profile.workout_schedules
            ],
            "hydration_preferences": {
                "daily_water_target_ml": profile.hydration_preferences.daily_water_target_ml,
                "reminder_frequency_minutes": profile.hydration_preferences.reminder_frequency_minutes,
                "enable_notifications": profile.hydration_preferences.enable_notifications
            } if profile.hydration_preferences else None,
            "lifestyle_baseline": {
                "energy_level": profile.lifestyle_baseline.energy_level,
                "stress_level": profile.lifestyle_baseline.stress_level,
                "sleep_quality": profile.lifestyle_baseline.sleep_quality
            } if profile.lifestyle_baseline else None
        }
        
        return snapshot

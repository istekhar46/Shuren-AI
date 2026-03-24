"""Onboarding service for managing user onboarding flow."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingState
from app.schemas.onboarding import StateInfo
from app.services.agent_orchestrator import AgentType

logger = logging.getLogger(__name__)


# State metadata for 4-step onboarding flow
# Provides rich metadata for each onboarding step including name, description,
# agent type, and required fields. Used by progress endpoint and UI rendering.
# This consolidates the previous 9-step flow into 4 steps:
# - Step 1: Fitness Assessment (includes fitness level AND goals)
# - Step 2: Workout Planning (plan generation and approval)
# - Step 3: Diet Planning (meal plan generation and approval)
# - Step 4: Scheduling (hydration and supplement preferences)
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Assessment",
        agent="fitness_assessment",
        description="Tell us about your fitness level and goals",
        required_fields=["fitness_level", "primary_goal"]
    ),
    2: StateInfo(
        state_number=2,
        name="Workout Planning",
        agent="workout_planning",
        description="Let's create your personalized workout plan",
        required_fields=["workout_plan", "workout_schedule"]
    ),
    3: StateInfo(
        state_number=3,
        name="Diet Planning",
        agent="diet_planning",
        description="Build your personalized meal plan",
        required_fields=["meal_plan", "meal_schedule"]
    ),
    4: StateInfo(
        state_number=4,
        name="Hydration & Supplements",
        agent="scheduling",
        description="Set up hydration reminders and supplement preferences",
        required_fields=["hydration_preferences", "supplement_preferences"]
    ),
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
    
    async def get_onboarding_state(self, user_id: UUID, auto_create: bool = True) -> OnboardingState | None:
        """Retrieve current onboarding state for a user.
        
        Args:
            user_id: User's unique identifier
            auto_create: Whether to automatically create a new state if none exists
            
        Returns:
            OnboardingState if found (or created), None otherwise only if auto_create is False
        """
        result = await self.db.execute(
            select(OnboardingState)
            .where(
                OnboardingState.user_id == user_id,
                OnboardingState.deleted_at.is_(None)
            )
        )
        state = result.scalar_one_or_none()
        
        if not state and auto_create:
            state = OnboardingState(
                user_id=user_id,
                current_step=1,
                is_complete=False
            )
            self.db.add(state)
            await self.db.commit()
            await self.db.refresh(state)
            logger.info(f"Auto-created onboarding state for user {user_id}")
            
        return state
    
    async def get_progress(self, user_id: UUID) -> "OnboardingProgress":
        """Get rich progress metadata for UI.
        
        Calculates completed states from agent_context and step_data JSONB,
        retrieves state metadata, calculates completion percentage, and
        determines if onboarding can be completed.
        
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
        
        # Extract completed states from step completion flags
        # In the 4-step flow, agents set step_X_complete flags
        completed = []
        
        if state.step_1_complete:
            completed.append(1)
        if state.step_2_complete:
            completed.append(2)
        if state.step_3_complete:
            completed.append(3)
        if state.step_4_complete:
            completed.append(4)
        
        # Get current and next state metadata
        current_info = STATE_METADATA[state.current_step] if 1 <= state.current_step <= 4 else STATE_METADATA[1]
        next_state = state.current_step + 1 if state.current_step < 4 else None
        next_info = STATE_METADATA.get(next_state) if next_state else None
        
        # Calculate completion percentage
        percentage = int((len(completed) / 4) * 100)
        
        # Check if can complete (all 4 steps done)
        can_complete = len(completed) == 4
        
        return OnboardingProgress(
            current_state=state.current_step,
            total_states=4,
            completed_states=completed,
            current_state_info=current_info,
            next_state_info=next_info,
            is_complete=state.is_complete,
            completion_percentage=percentage,
            can_complete=can_complete
        )
    
    async def can_complete_onboarding(self, user_id: UUID) -> bool:
        """Check if all required steps are complete.
        
        Verifies that all 4 steps have been completed by checking step completion flags.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if all 4 steps are complete, False otherwise
            
        Raises:
            OnboardingValidationError: If onboarding state not found
        """
        state = await self.get_onboarding_state(user_id)
        if not state:
            raise OnboardingValidationError("Onboarding state not found")
        
        # Check if all 4 steps are complete
        return (
            state.step_1_complete and
            state.step_2_complete and
            state.step_3_complete and
            state.step_4_complete
        )
    
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


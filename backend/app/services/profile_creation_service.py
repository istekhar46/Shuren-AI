"""
Profile creation service for creating UserProfile from agent_context.

This module provides the ProfileCreationService class that extracts data
from the agent_context collected during onboarding and creates a complete
UserProfile with all related entities in an atomic transaction.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    PhysicalConstraint,
    DietaryPreference,
    MealPlan,
    MealSchedule,
    WorkoutSchedule,
    HydrationPreference,
)
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.dish import Dish, DishIngredient
from app.services.onboarding_completion import verify_onboarding_completion, OnboardingIncompleteError
from app.utils.schedule_validation import day_name_to_number, time_str_to_time

logger = logging.getLogger(__name__)


class ProfileCreationService:
    """
    Service for creating UserProfile from agent_context data.
    
    This service extracts data from the agent_context collected during
    onboarding and creates a complete UserProfile with all related entities
    in an atomic database transaction.
    
    Attributes:
        db: AsyncSession for database operations
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize ProfileCreationService.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
    
    async def create_profile_from_agent_context(
        self,
        user_id: UUID,
        agent_context: dict
    ) -> UserProfile:
        """
        Create UserProfile and all related entities from agent_context.
        
        This method performs the following steps:
        1. Verify all required agent data is present
        2. Extract and validate data from agent_context
        3. Create UserProfile entity
        4. Create all related entities
        5. Execute in atomic transaction
        6. Return profile with relationships loaded
        
        Args:
            user_id: User ID
            agent_context: Complete agent_context from OnboardingState
        
        Returns:
            Created UserProfile with all relationships loaded
        
        Raises:
            OnboardingIncompleteError: If required agent data is missing
            ValueError: If data validation fails
            SQLAlchemyError: If transaction fails
        """
        # Verify all required agent data is present
        verify_onboarding_completion(agent_context)
        
        try:
            # Extract data from agent_context
            fitness_data = self._extract_fitness_data(agent_context)
            goal_data = self._extract_goal_data(agent_context)
            workout_data = self._extract_workout_data(agent_context)
            diet_data = self._extract_diet_data(agent_context)
            schedule_data = self._extract_schedule_data(agent_context)
            
            # Begin transaction (will be committed by caller)
            # Create UserProfile with is_locked=True
            profile = self._create_profile_entity(user_id, fitness_data["fitness_level"])
            self.db.add(profile)
            await self.db.flush()  # Get profile.id
            
            # Create all related entities
            fitness_goals = self._create_fitness_goals(profile.id, goal_data)
            for goal in fitness_goals:
                self.db.add(goal)
            
            physical_constraints = self._create_physical_constraints(
                profile.id, 
                fitness_data.get("limitations", [])
            )
            for constraint in physical_constraints:
                self.db.add(constraint)
            
            dietary_pref = self._create_dietary_preference(profile.id, diet_data)
            self.db.add(dietary_pref)
            
            meal_plan = self._create_meal_plan(profile.id, diet_data["meal_plan"])
            self.db.add(meal_plan)
            
            meal_schedules = self._create_meal_schedules(
                profile.id,
                schedule_data["meal_schedule"]
            )
            for schedule in meal_schedules:
                self.db.add(schedule)
            await self.db.flush() # Need schedule IDs immediately
            
            meal_template = await self._create_meal_template(profile.id, diet_data, meal_schedules)
            if meal_template:
                self.db.add(meal_template)
            
            workout_plan = await self._create_workout_plan(user_id, workout_data)
            self.db.add(workout_plan)
            
            workout_schedules = self._create_workout_schedules(
                profile.id,
                schedule_data["workout_schedule"]
            )
            for schedule in workout_schedules:
                self.db.add(schedule)
            
            hydration_pref = self._create_hydration_preference(
                profile.id,
                schedule_data["hydration_preferences"]
            )
            self.db.add(hydration_pref)
            
            # Commit transaction
            await self.db.commit()
            
            # Refresh profile to load relationships
            await self.db.refresh(profile)
            
            logger.info(f"Successfully created profile for user {user_id}")
            return profile
            
        except (OnboardingIncompleteError, ValueError) as e:
            # Re-raise validation errors
            await self.db.rollback()
            logger.error(f"Profile creation validation error for user {user_id}: {e}")
            raise
        except SQLAlchemyError as e:
            # Rollback transaction on database error
            await self.db.rollback()
            logger.error(f"Profile creation database error for user {user_id}: {e}")
            raise
        except Exception as e:
            # Rollback on any other error
            await self.db.rollback()
            logger.error(f"Profile creation unexpected error for user {user_id}: {e}")
            raise

    def _extract_fitness_data(self, agent_context: dict) -> dict:
        """
        Extract fitness assessment data from agent_context.
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing fitness_level and limitations
        
        Raises:
            ValueError: If required fitness data is missing
        """
        fitness_assessment = agent_context.get("fitness_assessment", {})
        
        fitness_level = fitness_assessment.get("fitness_level")
        if not fitness_level:
            raise ValueError("Missing required field: fitness_assessment.fitness_level")
        
        limitations = fitness_assessment.get("limitations", [])
        if not isinstance(limitations, list):
            limitations = []
        
        return {
            "fitness_level": fitness_level,
            "limitations": limitations
        }
    
    def _extract_goal_data(self, agent_context: dict) -> dict:
        """
        Extract goal data from agent_context (now part of fitness_assessment).
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing primary_goal, secondary_goal (optional),
            target_weight_kg (optional), target_body_fat_percentage (optional)
        
        Raises:
            ValueError: If required goal data is missing
        """
        # Goals are now collected in fitness_assessment (Step 1)
        fitness_assessment = agent_context.get("fitness_assessment", {})
        
        primary_goal = fitness_assessment.get("primary_goal")
        if not primary_goal:
            raise ValueError("Missing required field: fitness_assessment.primary_goal")
        
        return {
            "primary_goal": primary_goal,
            "secondary_goal": fitness_assessment.get("secondary_goal"),
            "target_weight_kg": fitness_assessment.get("target_weight_kg"),
            "target_body_fat_percentage": fitness_assessment.get("target_body_fat_percentage")
        }
    
    def _extract_workout_data(self, agent_context: dict) -> dict:
        """
        Extract workout planning data from agent_context.
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing workout plan data including frequency,
            duration_minutes, training_split, exercises, and rationale
        
        Raises:
            ValueError: If required workout data is missing
        """
        workout_planning = agent_context.get("workout_planning", {})
        plan_data = workout_planning.get("plan", {})
        
        frequency = plan_data.get("frequency")
        if not frequency:
            raise ValueError("Missing required field: workout_planning.plan.frequency")
        
        duration_minutes = plan_data.get("duration_minutes")
        if not duration_minutes:
            raise ValueError("Missing required field: workout_planning.plan.duration_minutes")
        
        training_split = plan_data.get("training_split")
        if not training_split:
            raise ValueError("Missing required field: workout_planning.plan.training_split")
            
        workout_days = plan_data.get("workout_days")
        if not workout_days:
            raise ValueError("Missing required field: workout_planning.plan.workout_days")
        
        return {
            "frequency": frequency,
            "duration_minutes": duration_minutes,
            "training_split": training_split,
            "workout_days": workout_days,
            "rationale": plan_data.get("progression_strategy", "Standard progression")
        }
    
    def _extract_diet_data(self, agent_context: dict) -> dict:
        """
        Extract diet planning data from agent_context.
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing dietary preferences and meal plan data
        
        Raises:
            ValueError: If required diet data is missing
        """
        diet_planning = agent_context.get("diet_planning", {})
        
        # Extract dietary preferences
        diet_type = diet_planning.get("diet_type")
        if not diet_type:
            raise ValueError("Missing required field: diet_planning.diet_type")
        
        # Extract meal plan data 
        plan_data = diet_planning.get("plan", {})
        
        daily_calories = plan_data.get("daily_calories")
        protein_g = plan_data.get("protein_g")
        carbs_g = plan_data.get("carbs_g")
        fats_g = plan_data.get("fats_g")
        
        if any(x is None for x in [daily_calories, protein_g, carbs_g, fats_g]):
            raise ValueError("Missing required macronutrient data in diet_planning.plan")
        
        return {
            "diet_type": diet_type,
            "allergies": diet_planning.get("allergies", []),
            "intolerances": diet_planning.get("intolerances", []),
            "dislikes": diet_planning.get("dislikes", []),
            "meal_plan": {
                "daily_calories": int(daily_calories),
                "protein_g": int(protein_g),
                "carbs_g": int(carbs_g),
                "fats_g": int(fats_g),
                "meal_frequency": plan_data.get("meal_frequency", 3)
            },
            "sample_meals": plan_data.get("sample_meals", [])
        }
    
    def _extract_schedule_data(self, agent_context: dict) -> dict:
        """
        Extract scheduling data from agent_context.
        
        In the new 4-step flow:
        - Workout schedule is collected in Step 2 (workout_planning)
        - Meal schedule is collected in Step 3 (diet_planning)
        - Hydration preferences are collected in Step 4 (scheduling)
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing workout_schedule, meal_schedule,
            and hydration_preferences
        
        Raises:
            ValueError: If required schedule data is missing
        """
        workout_planning = agent_context.get("workout_planning", {})
        diet_planning = agent_context.get("diet_planning", {})
        scheduling = agent_context.get("scheduling", {})
        
        # Workout schedule from Step 2
        workout_schedule = workout_planning.get("schedule")
        if not workout_schedule:
            raise ValueError("Missing required field: workout_planning.schedule")
        
        # Meal schedule from Step 3
        meal_schedule = diet_planning.get("schedule")
        if not meal_schedule:
            raise ValueError("Missing required field: diet_planning.schedule")
        
        # Hydration preferences from Step 4
        # New structure uses nested "hydration" dict
        hydration_data = scheduling.get("hydration", {})
        target_ml = hydration_data.get("target_ml")
        frequency_hours = hydration_data.get("frequency_hours")
        
        if not target_ml or not frequency_hours:
            raise ValueError("Missing required fields: scheduling.hydration.target_ml or frequency_hours")
        
        hydration_preferences = {
            "target_ml": target_ml,
            "frequency_hours": frequency_hours
        }
        
        return {
            "workout_schedule": workout_schedule,
            "meal_schedule": meal_schedule,
            "hydration_preferences": hydration_preferences
        }

    def _create_profile_entity(self, user_id: UUID, fitness_level: str) -> UserProfile:
        """
        Create UserProfile entity.
        
        Args:
            user_id: User ID
            fitness_level: Fitness level from fitness assessment
        
        Returns:
            UserProfile entity (not yet added to session)
        """
        return UserProfile(
            user_id=user_id,
            fitness_level=fitness_level,
            is_locked=True
        )
    
    def _create_fitness_goals(self, profile_id: UUID, goal_data: dict) -> List[FitnessGoal]:
        """
        Create FitnessGoal entities from goal data.
        
        Args:
            profile_id: Profile ID
            goal_data: Dictionary containing primary_goal, secondary_goal (optional),
                      target_weight_kg (optional), target_body_fat_percentage (optional)
        
        Returns:
            List of FitnessGoal entities
        """
        goals = []
        
        # Create primary goal
        primary_goal = FitnessGoal(
            profile_id=profile_id,
            goal_type=goal_data["primary_goal"],
            target_weight_kg=goal_data.get("target_weight_kg"),
            target_body_fat_percentage=goal_data.get("target_body_fat_percentage"),
            priority=1
        )
        goals.append(primary_goal)
        
        # Create secondary goal if present
        if goal_data.get("secondary_goal"):
            secondary_goal = FitnessGoal(
                profile_id=profile_id,
                goal_type=goal_data["secondary_goal"],
                priority=2
            )
            goals.append(secondary_goal)
        
        return goals
    
    def _create_physical_constraints(
        self,
        profile_id: UUID,
        limitations: List[str]
    ) -> List[PhysicalConstraint]:
        """
        Create PhysicalConstraint entities from limitations list.
        
        Args:
            profile_id: Profile ID
            limitations: List of limitation descriptions
        
        Returns:
            List of PhysicalConstraint entities (empty list if no limitations)
        """
        constraints = []
        
        for limitation in limitations:
            constraint = PhysicalConstraint(
                profile_id=profile_id,
                constraint_type="limitation",
                description=limitation
            )
            constraints.append(constraint)
        
        return constraints
    
    def _create_dietary_preference(
        self,
        profile_id: UUID,
        diet_data: dict
    ) -> DietaryPreference:
        """
        Create DietaryPreference entity from diet data.
        
        Args:
            profile_id: Profile ID
            diet_data: Dictionary containing diet_type, allergies, intolerances, dislikes
        
        Returns:
            DietaryPreference entity
        """
        return DietaryPreference(
            profile_id=profile_id,
            diet_type=diet_data["diet_type"],
            allergies=diet_data.get("allergies", []),
            intolerances=diet_data.get("intolerances", []),
            dislikes=diet_data.get("dislikes", [])
        )
    
    def _create_meal_plan(self, profile_id: UUID, meal_plan_data: dict) -> MealPlan:
        """
        Create MealPlan entity from meal plan data.
        
        Args:
            profile_id: Profile ID
            meal_plan_data: Dictionary containing daily_calories, protein_g, carbs_g, fats_g
        
        Returns:
            MealPlan entity
        """
        return MealPlan(
            profile_id=profile_id,
            daily_calorie_target=meal_plan_data["daily_calories"],
            protein_grams=meal_plan_data["protein_g"],
            carbs_grams=meal_plan_data["carbs_g"],
            fats_grams=meal_plan_data["fats_g"]
        )
    
    def _create_meal_schedules(
        self,
        profile_id: UUID,
        meal_schedule_data: dict | list
    ) -> List[MealSchedule]:
        """
        Create MealSchedule entities from meal schedule data.
        
        Args:
            profile_id: Profile ID
            meal_schedule_data: Dictionary mapping meal names to times, or list of Dicts.
        
        Returns:
            List of MealSchedule entities
        """
        schedules = []
        
        # Support old dict schema format
        if isinstance(meal_schedule_data, dict):
            for meal_name, time_str in meal_schedule_data.items():
                schedule = MealSchedule(
                    profile_id=profile_id,
                    meal_name=meal_name,
                    scheduled_time=time_str_to_time(time_str),
                    enable_notifications=True
                )
                schedules.append(schedule)
                
        # Support new robust list schema format
        elif isinstance(meal_schedule_data, list):
            for item in meal_schedule_data:
                meal_type = item.get("meal_type", "snack")
                time_str = item.get("time")
                if not time_str:
                    continue
                schedule = MealSchedule(
                    profile_id=profile_id,
                    meal_name=meal_type,
                    scheduled_time=time_str_to_time(time_str),
                    enable_notifications=True
                )
                schedules.append(schedule)
        
        return schedules
    
    async def _create_workout_plan(self, user_id: UUID, workout_data: dict) -> WorkoutPlan:
        """
        Create WorkoutPlan entity from workout data.
        
        Args:
            user_id: User ID
            workout_data: Dictionary containing frequency, duration_minutes,
                         duration_weeks, training_split, rationale
        
        Returns:
            WorkoutPlan entity with WorkoutDay children
        """
        # Create workout plan
        workout_plan = WorkoutPlan(
            user_id=user_id,
            plan_name=f"Personalized {workout_data['frequency']}-Day Plan",
            plan_description=workout_data.get("rationale", ""),
            duration_weeks=workout_data.get("duration_weeks", 12),
            days_per_week=workout_data["frequency"],
            plan_rationale=workout_data.get("rationale", ""),
            is_locked=True,
            locked_at=datetime.utcnow()
        )
        
        # Create workout days from training split
        workout_days_data = workout_data.get("workout_days", [])

        for day_num, day_data in enumerate(workout_days_data, start=1):
            day_name = day_data.get("day_name", f"Day {day_num}")
            day_desc = f"{day_name} ({workout_data.get('training_split', '')})"
            workout_type = "strength"
            exercises_data = day_data.get("exercises", [])

            workout_day = WorkoutDay(
                workout_plan=workout_plan,
                day_number=day_num,
                day_name=day_name[:100],  # safety trim length
                muscle_groups=[], # Safely skip deep parsing for now
                workout_type=workout_type,
                description=day_desc,
                estimated_duration_minutes=workout_data.get("duration_minutes", 60)
            )
            self.db.add(workout_day)
            
            # Map exercises and query library
            from sqlalchemy import select
            from app.models.workout import ExerciseLibrary, WorkoutExercise
            
            for index, ex_data in enumerate(exercises_data, start=1):
                if not isinstance(ex_data, dict):
                    continue
                    
                ex_name = ex_data.get("name") or ex_data.get("exercise") or "Unknown Exercise"
                
                # Try to find exactly matching or closely matching exercise in library
                stmt = select(ExerciseLibrary).where(ExerciseLibrary.exercise_name.ilike(f"%{ex_name}%"))
                result = await self.db.execute(stmt)
                ex_lib = result.scalars().first()
                
                if not ex_lib:
                    # Create a default stub so the user doesn't lose data on LLM hallucinations
                    import re
                    ex_slug = re.sub(r'[^a-z0-9]+', '-', ex_name.lower()).strip('-')
                    
                    # Map workout generator exercise types to valid DB exercise_type values
                    # DB allows: 'strength', 'cardio', 'flexibility', 'plyometric', 'olympic'
                    # Generator produces: 'compound', 'isolation', 'cardio', 'flexibility'
                    raw_type = ex_data.get("type", "strength").lower()
                    exercise_type_map = {
                        "compound": "strength",
                        "isolation": "strength",
                        "cardio": "cardio",
                        "flexibility": "flexibility",
                        "plyometric": "plyometric",
                        "olympic": "olympic",
                    }
                    mapped_exercise_type = exercise_type_map.get(raw_type, "strength")
                    
                    ex_lib = ExerciseLibrary(
                        exercise_name=ex_name[:255],
                        exercise_slug=ex_slug[:255],
                        exercise_type=mapped_exercise_type,
                        primary_muscle_group="full_body",
                        difficulty_level="intermediate",
                        description=f"AI-generated exercise: {ex_name}",
                        instructions="Follow standard form.",
                    )
                    self.db.add(ex_lib)
                    await self.db.flush() # Need the ID immediately
                
                # Parse Reps String (e.g. "8-12", "to failure", "AMRAP", "12-15 per arm")
                reps_str = str(ex_data.get("reps", ""))
                reps_min = reps_max = reps_target = None
                try:
                    import re as _re
                    # Extract all numeric values from the string
                    all_nums = _re.findall(r'\d+', reps_str)
                    
                    if "-" in reps_str and len(all_nums) >= 2:
                        # Range format: "8-12", "12-15 per arm"
                        reps_min = int(all_nums[0])
                        reps_max = int(all_nums[1])
                    elif all_nums:
                        # Single number: "10", "15 reps"
                        reps_target = int(all_nums[0])
                    else:
                        # Non-numeric: "to failure", "AMRAP" → default to 1
                        reps_target = 1
                except Exception:
                    # Absolute safety net: constraint requires at least reps_target
                    reps_target = 1
                
                we = WorkoutExercise(
                    workout_day=workout_day,
                    exercise_library_id=ex_lib.id,
                    exercise_order=index,
                    sets=int(ex_data.get("sets", 3)),
                    reps_min=reps_min,
                    reps_max=reps_max,
                    reps_target=reps_target,
                    rest_seconds=int(ex_data.get("rest_seconds", 60)),
                    notes=ex_data.get("notes", "")
                )
                self.db.add(we)
        
        # Store complete training split in plan_data for reference
        workout_plan.plan_data = {
            "training_split": workout_data.get("training_split", ""),
            "frequency": workout_data.get("frequency", 3),
            "duration_minutes": workout_data.get("duration_minutes", 60)
        }
        
        return workout_plan
    
    def _create_workout_schedules(
        self,
        profile_id: UUID,
        workout_schedule_data: dict
    ) -> List[WorkoutSchedule]:
        """
        Create WorkoutSchedule entities from workout schedule data.
        
        Args:
            profile_id: Profile ID
            workout_schedule_data: Dictionary containing days and times lists
                                  (e.g., {"days": ["Monday", "Wednesday"], "times": ["07:00", "18:00"]})
        
        Returns:
            List of WorkoutSchedule entities
        """
        schedules = []
        
        days = workout_schedule_data.get("days", [])
        times = workout_schedule_data.get("times", [])
        
        for day_name, time_str in zip(days, times):
            schedule = WorkoutSchedule(
                profile_id=profile_id,
                day_of_week=day_name_to_number(day_name),
                scheduled_time=time_str_to_time(time_str),
                enable_notifications=True
            )
            schedules.append(schedule)
        
        return schedules
    
    def _create_hydration_preference(
        self,
        profile_id: UUID,
        hydration_data: dict
    ) -> HydrationPreference:
        """
        Create HydrationPreference entity from hydration data.
        
        Args:
            profile_id: Profile ID
            hydration_data: Dictionary containing frequency_hours and target_ml
        
        Returns:
            HydrationPreference entity
        """
        return HydrationPreference(
            profile_id=profile_id,
            daily_water_target_ml=hydration_data["target_ml"],
            reminder_frequency_minutes=hydration_data["frequency_hours"] * 60,
            enable_notifications=True
        )

    async def _create_meal_template(
        self,
        profile_id: UUID,
        diet_data: dict,
        meal_schedules: List[MealSchedule]
    ) -> Optional[MealTemplate]:
        """
        Create MealTemplate with Dish entities from onboarding sample_meals.
        
        Reads the sample_meals list (each entry has name, meal_type, ingredients,
        approximate_calories, etc.) from the MealPlan structured output and creates
        real Dish + TemplateMeal rows for a 7-day weekly template.
        
        Args:
            profile_id: Profile identifier
            diet_data: Diet data dict containing sample_meals list
            meal_schedules: Saved MealSchedule list for cross-referencing timeslots
            
        Returns:
            MealTemplate entity, or None if no sample meals available
        """
        sample_meals = diet_data.get("sample_meals", [])
        if not sample_meals:
            logger.warning("No sample_meals found in diet_data, skipping meal template creation")
            return None
            
        plan_data = diet_data.get("meal_plan", {})
        
        # Create the weekly template
        template = MealTemplate(
            profile_id=profile_id,
            is_active=True,
            plan_name="Getting Started Protocol",
            daily_calorie_target=plan_data.get("daily_calories", 2000),
            protein_grams=plan_data.get("protein_g", 150),
            carbs_grams=plan_data.get("carbs_g", 200),
            fats_grams=plan_data.get("fats_g", 50),
            generated_by='onboarding_agent',
            generation_reason="Initial meal plan from onboarding"
        )
        self.db.add(template)
        await self.db.flush()
        
        # Valid meal_type values per DB constraint
        # Group sample meals by meal_type
        from collections import defaultdict
        meals_by_type: Dict[str, list] = defaultdict(list)
        
        for meal in sample_meals:
            if isinstance(meal, dict):
                raw_type = meal.get("meal_type", "snack")
            else:
                continue
            
            # Use raw_type since MealPlan generator uses strictly typed Enums
            meal_type_key = raw_type.lower().strip()
            if hasattr(raw_type, "value"):
                meal_type_key = raw_type.value
                
            meals_by_type[meal_type_key].append(meal)
            
        try:
            # Create Dish entities and TemplateMeals for each day
            for day_index in range(7):
                # Iterate by schedule slots, not by meal types! This correctly handles duplicates (like 2 snacks)
                for idx, target_schedule in enumerate(meal_schedules):
                    meal_type = target_schedule.meal_name.lower().strip()
                    type_meals = meals_by_type.get(meal_type)
                    
                    if not type_meals:
                        # Fallback if no matching sample meals exist for this type
                        if meal_type in ["pre_workout", "post_workout"]:
                            type_meals = meals_by_type.get("snack")
                        if not type_meals:
                            continue
                    
                    # Rotate meals deterministically: day plus idx varies it across multiple same-day slots
                    meal_data = type_meals[(day_index + idx) % len(type_meals)]
                    
                    meal_name = meal_data.get("name", "Unknown Dish")
                    
                    # Check if dish already exists (may have been created for a previous day)
                    from sqlalchemy import select
                    stmt = select(Dish).where(
                        Dish.name == meal_name[:199]
                    ).filter(Dish.deleted_at.is_(None))
                    result = await self.db.execute(stmt)
                    target_dish = result.scalars().first()
                    
                    if not target_dish:
                        # Clamp calories to valid range (DB constraint: > 0 AND < 2000)
                        raw_cal = meal_data.get("approximate_calories", 500)
                        calories = max(1, min(1999, int(raw_cal)))
                        
                        target_dish = Dish(
                            name=meal_name[:199],
                            cuisine_type="Global",
                            meal_type=meal_type,
                            serving_size_g=250,
                            calories=calories,
                            protein_g=max(0, int(meal_data.get("approximate_protein_g", 20))),
                            carbs_g=max(0, int(meal_data.get("approximate_carbs_g", 30))),
                            fats_g=max(0, int(meal_data.get("approximate_fats_g", 10))),
                            prep_time_minutes=min(180, max(0, int(meal_data.get("prep_time_minutes", 15)))),
                            cook_time_minutes=0,
                            difficulty_level="medium",
                            is_vegetarian=(diet_data.get("diet_type", "") in ("vegetarian", "vegan")),
                            is_vegan=(diet_data.get("diet_type", "") == "vegan"),
                        )
                        self.db.add(target_dish)
                        await self.db.flush()
                    
                    # Create TemplateMeal linking template → schedule → dish
                    tm = TemplateMeal(
                        template_id=template.id,
                        meal_schedule_id=target_schedule.id,
                        dish_id=target_dish.id,
                        day_of_week=day_index,
                        is_primary=True,
                        alternative_order=1
                    )
                    self.db.add(tm)
                    
        except Exception as e:
            logger.error(f"Failed to assemble meal template: {e}", exc_info=True)
            
        return template


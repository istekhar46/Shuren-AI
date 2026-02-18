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
        Extract goal setting data from agent_context.
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing primary_goal, secondary_goal (optional),
            target_weight_kg (optional), target_body_fat_percentage (optional)
        
        Raises:
            ValueError: If required goal data is missing
        """
        goal_setting = agent_context.get("goal_setting", {})
        
        primary_goal = goal_setting.get("primary_goal")
        if not primary_goal:
            raise ValueError("Missing required field: goal_setting.primary_goal")
        
        return {
            "primary_goal": primary_goal,
            "secondary_goal": goal_setting.get("secondary_goal"),
            "target_weight_kg": goal_setting.get("target_weight_kg"),
            "target_body_fat_percentage": goal_setting.get("target_body_fat_percentage")
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
        proposed_plan = workout_planning.get("proposed_plan", {})
        
        frequency = proposed_plan.get("frequency")
        if not frequency:
            raise ValueError("Missing required field: workout_planning.proposed_plan.frequency")
        
        duration_minutes = proposed_plan.get("duration_minutes")
        if not duration_minutes:
            raise ValueError("Missing required field: workout_planning.proposed_plan.duration_minutes")
        
        training_split = proposed_plan.get("training_split", [])
        if not training_split:
            raise ValueError("Missing required field: workout_planning.proposed_plan.training_split")
        
        return {
            "frequency": frequency,
            "duration_minutes": duration_minutes,
            "duration_weeks": proposed_plan.get("duration_weeks", 12),
            "training_split": training_split,
            "rationale": proposed_plan.get("rationale", "")
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
        preferences = diet_planning.get("preferences", {})
        proposed_plan = diet_planning.get("proposed_plan", {})
        
        # Extract dietary preferences
        diet_type = preferences.get("diet_type")
        if not diet_type:
            raise ValueError("Missing required field: diet_planning.preferences.diet_type")
        
        # Extract meal plan data
        daily_calories = proposed_plan.get("daily_calories")
        if not daily_calories:
            raise ValueError("Missing required field: diet_planning.proposed_plan.daily_calories")
        
        protein_g = proposed_plan.get("protein_g")
        carbs_g = proposed_plan.get("carbs_g")
        fats_g = proposed_plan.get("fats_g")
        
        if protein_g is None or carbs_g is None or fats_g is None:
            raise ValueError("Missing required macronutrient data in diet_planning.proposed_plan")
        
        return {
            "diet_type": diet_type,
            "allergies": preferences.get("allergies", []),
            "intolerances": preferences.get("intolerances", []),
            "dislikes": preferences.get("dislikes", []),
            "meal_plan": {
                "daily_calories": daily_calories,
                "protein_g": protein_g,
                "carbs_g": carbs_g,
                "fats_g": fats_g,
                "meal_frequency": proposed_plan.get("meal_frequency", 3)
            }
        }
    
    def _extract_schedule_data(self, agent_context: dict) -> dict:
        """
        Extract scheduling data from agent_context.
        
        Args:
            agent_context: Complete agent_context dictionary
        
        Returns:
            Dictionary containing workout_schedule, meal_schedule,
            and hydration_preferences
        
        Raises:
            ValueError: If required schedule data is missing
        """
        scheduling = agent_context.get("scheduling", {})
        
        workout_schedule = scheduling.get("workout_schedule")
        if not workout_schedule:
            raise ValueError("Missing required field: scheduling.workout_schedule")
        
        meal_schedule = scheduling.get("meal_schedule")
        if not meal_schedule:
            raise ValueError("Missing required field: scheduling.meal_schedule")
        
        hydration_preferences = scheduling.get("hydration_preferences")
        if not hydration_preferences:
            raise ValueError("Missing required field: scheduling.hydration_preferences")
        
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
        meal_schedule_data: dict
    ) -> List[MealSchedule]:
        """
        Create MealSchedule entities from meal schedule data.
        
        Args:
            profile_id: Profile ID
            meal_schedule_data: Dictionary mapping meal names to times
                              (e.g., {"breakfast": "08:00", "lunch": "13:00"})
        
        Returns:
            List of MealSchedule entities
        """
        schedules = []
        
        for meal_name, time_str in meal_schedule_data.items():
            schedule = MealSchedule(
                profile_id=profile_id,
                meal_name=meal_name,
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
        for day_num, day_data in enumerate(workout_data["training_split"], start=1):
            workout_day = WorkoutDay(
                workout_plan=workout_plan,
                day_number=day_num,
                day_name=day_data.get("name", f"Day {day_num}"),
                muscle_groups=day_data.get("muscle_groups", []),
                workout_type=day_data.get("type", "strength"),
                description=day_data.get("description"),
                estimated_duration_minutes=workout_data["duration_minutes"]
            )
            
            # Note: WorkoutExercise creation would require exercise_library_id lookups
            # For now, we store the exercise data in plan_data JSONB field
            # This can be expanded later when exercise library is populated
        
        # Store complete training split in plan_data for reference
        workout_plan.plan_data = {
            "training_split": workout_data["training_split"],
            "frequency": workout_data["frequency"],
            "duration_minutes": workout_data["duration_minutes"]
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

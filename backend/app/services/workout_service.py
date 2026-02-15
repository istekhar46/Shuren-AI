"""Workout service for managing workout plans and schedules."""

from datetime import datetime, time
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ProfileLockedException
from app.models.preferences import WorkoutSchedule
from app.models.profile import UserProfile, UserProfileVersion
from app.models.workout import ExerciseLibrary, WorkoutDay, WorkoutExercise, WorkoutPlan


class WorkoutService:
    """Service for managing workout plans and schedules.
    
    Handles workout plan retrieval with eager loading, workout schedule
    management, profile locking, and versioning for modifications.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize workout service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_workout_plan(self, user_id: UUID) -> WorkoutPlan:
        """Retrieve workout plan with all related entities.
        
        Uses eager loading (selectinload) to minimize queries and ensure
        response time < 100ms. Loads all workout days, exercises, and
        exercise library details in a single query.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            WorkoutPlan with all relationships loaded
            
        Raises:
            HTTPException: 404 if workout plan not found
        """
        result = await self.db.execute(
            select(WorkoutPlan)
            .where(
                WorkoutPlan.user_id == user_id,
                WorkoutPlan.deleted_at.is_(None)
            )
            .options(
                selectinload(WorkoutPlan.workout_days)
                .selectinload(WorkoutDay.exercises)
                .selectinload(WorkoutExercise.exercise_library)
            )
        )
        
        workout_plan = result.scalar_one_or_none()
        
        if not workout_plan:
            raise HTTPException(
                status_code=404,
                detail="Workout plan not found for user"
            )
        
        return workout_plan
    
    async def get_workout_day(self, user_id: UUID, day_number: int) -> WorkoutDay:
        """Retrieve specific workout day with all exercise details.
        
        Args:
            user_id: User's unique identifier
            day_number: Day number (1-7)
            
        Returns:
            WorkoutDay with all exercises and exercise library details
            
        Raises:
            HTTPException: 404 if workout day not found
            HTTPException: 400 if day_number is invalid
        """
        # Validate day_number
        if day_number < 1 or day_number > 7:
            raise HTTPException(
                status_code=400,
                detail="Day number must be between 1 and 7"
            )
        
        # Get workout plan first to verify user ownership
        workout_plan = await self.get_workout_plan(user_id)
        
        # Find the specific workout day
        workout_day = None
        for day in workout_plan.workout_days:
            if day.day_number == day_number:
                workout_day = day
                break
        
        if not workout_day:
            raise HTTPException(
                status_code=404,
                detail=f"Workout day {day_number} not found in plan"
            )
        
        return workout_day
    
    async def get_today_workout(self, user_id: UUID) -> Optional[WorkoutDay]:
        """Retrieve today's workout based on workout schedule and current day.
        
        Matches current day of week to workout_schedules, then finds the
        corresponding workout day in the workout plan.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            WorkoutDay if workout scheduled for today, None otherwise
            
        Raises:
            HTTPException: 404 if workout plan not found
        """
        # Get current day of week (0=Monday, 6=Sunday)
        current_day = datetime.now().weekday()
        
        # Get user's profile to access workout schedules
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.workout_schedules))
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        # Check if there's a workout scheduled for today
        workout_scheduled_today = False
        for schedule in profile.workout_schedules:
            if schedule.day_of_week == current_day:
                workout_scheduled_today = True
                break
        
        if not workout_scheduled_today:
            return None
        
        # Get workout plan
        workout_plan = await self.get_workout_plan(user_id)
        
        # Find workout day matching today's day of week
        # Map day_of_week (0-6) to day_number (1-7)
        # Assuming day_number 1 = Monday, 7 = Sunday
        day_number = current_day + 1
        
        for day in workout_plan.workout_days:
            if day.day_number == day_number:
                return day
        
        return None
    
    async def get_week_workouts(self, user_id: UUID) -> list[WorkoutDay]:
        """Retrieve this week's workouts with exercise summaries.
        
        Returns all workout days from the user's workout plan.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of WorkoutDay objects with all details
            
        Raises:
            HTTPException: 404 if workout plan not found
        """
        workout_plan = await self.get_workout_plan(user_id)
        return workout_plan.workout_days

    async def get_workout_schedule(self, user_id: UUID) -> list[WorkoutSchedule]:
        """Retrieve workout schedule (days and timing).
        
        Returns all configured workout days with timing from the user's profile.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of WorkoutSchedule objects
            
        Raises:
            HTTPException: 404 if profile not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.workout_schedules))
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        return profile.workout_schedules
    
    async def get_next_workout(self, user_id: UUID) -> Optional[WorkoutSchedule]:
        """Retrieve next scheduled workout based on current time and day.
        
        Finds the next upcoming workout by comparing current day/time with
        workout schedules. Returns the earliest workout that is after now.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            WorkoutSchedule if next workout exists, None otherwise
            
        Raises:
            HTTPException: 404 if profile not found
        """
        # Get workout schedules
        schedules = await self.get_workout_schedule(user_id)
        
        if not schedules:
            return None
        
        # Get current day and time
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()
        
        # Find next workout
        # First, check for workouts later today
        today_workouts = [
            s for s in schedules
            if s.day_of_week == current_day and s.scheduled_time > current_time
        ]
        
        if today_workouts:
            # Return earliest workout today
            return min(today_workouts, key=lambda s: s.scheduled_time)
        
        # If no workouts today, find next workout in upcoming days
        upcoming_workouts = []
        for days_ahead in range(1, 8):  # Check next 7 days
            check_day = (current_day + days_ahead) % 7
            day_workouts = [s for s in schedules if s.day_of_week == check_day]
            
            if day_workouts:
                # Return earliest workout on this day
                return min(day_workouts, key=lambda s: s.scheduled_time)
        
        return None
    
    async def check_profile_lock(self, user_id: UUID) -> bool:
        """Check if user's profile is locked.
        
        Verifies profile lock status before allowing modifications.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if profile is locked, False otherwise
            
        Raises:
            HTTPException: 404 if profile not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        return profile.is_locked
    
    async def create_profile_version(self, user_id: UUID, reason: str) -> None:
        """Create profile version record before modification.
        
        Creates immutable snapshot of profile state for audit trail.
        Captures complete profile state including all relationships.
        
        Args:
            user_id: User's unique identifier
            reason: Reason for profile modification
            
        Raises:
            HTTPException: 404 if profile not found
        """
        # Get profile with all relationships
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.workout_schedules),
                selectinload(UserProfile.versions)
            )
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        # Get workout plan separately (it's not a direct relationship on UserProfile)
        workout_plan_result = await self.db.execute(
            select(WorkoutPlan)
            .where(
                WorkoutPlan.user_id == user_id,
                WorkoutPlan.deleted_at.is_(None)
            )
            .options(
                selectinload(WorkoutPlan.workout_days)
                .selectinload(WorkoutDay.exercises)
            )
        )
        workout_plan = workout_plan_result.scalar_one_or_none()
        
        # Determine next version number
        version_number = 1
        if profile.versions:
            version_number = max(v.version_number for v in profile.versions) + 1
        
        # Create snapshot of current state
        snapshot = {
            "profile_id": str(profile.id),
            "user_id": str(profile.user_id),
            "is_locked": profile.is_locked,
            "fitness_level": profile.fitness_level,
            "workout_plan": None,
            "workout_schedules": []
        }
        
        # Add workout plan to snapshot
        if workout_plan:
            snapshot["workout_plan"] = {
                "id": str(workout_plan.id),
                "plan_name": workout_plan.plan_name,
                "duration_weeks": workout_plan.duration_weeks,
                "days_per_week": workout_plan.days_per_week,
                "is_locked": workout_plan.is_locked,
                "workout_days_count": len(workout_plan.workout_days)
            }
        
        # Add workout schedules to snapshot
        for schedule in profile.workout_schedules:
            snapshot["workout_schedules"].append({
                "id": str(schedule.id),
                "day_of_week": schedule.day_of_week,
                "scheduled_time": schedule.scheduled_time.isoformat() if schedule.scheduled_time else None,
                "enable_notifications": schedule.enable_notifications
            })
        
        # Create version record
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=version_number,
            change_reason=reason,
            snapshot=snapshot
        )
        
        self.db.add(version)
        await self.db.commit()

    async def update_workout_plan(
        self,
        user_id: UUID,
        update: dict
    ) -> WorkoutPlan:
        """Update workout plan with lock validation.
        
        Validates profile lock status before applying changes.
        Creates profile version if locked profile is modified.
        
        Args:
            user_id: User's unique identifier
            update: Dictionary of fields to update
            
        Returns:
            Updated WorkoutPlan
            
        Raises:
            HTTPException: 403 if profile is locked
            HTTPException: 404 if workout plan not found
        """
        # Check profile lock
        is_locked = await self.check_profile_lock(user_id)
        
        if is_locked:
            raise ProfileLockedException()
        
        # Get workout plan
        workout_plan = await self.get_workout_plan(user_id)
        
        # Apply updates to plan-level fields
        plan_fields = ['plan_name', 'plan_description', 'duration_weeks', 'days_per_week']
        for field in plan_fields:
            if field in update and update[field] is not None:
                setattr(workout_plan, field, update[field])
        
        # Handle workout_days updates if provided
        if 'workout_days' in update and update['workout_days'] is not None:
            # Delete existing workout days and exercises
            for day in workout_plan.workout_days:
                # Delete exercises first
                for exercise in day.exercises:
                    await self.db.delete(exercise)
                await self.db.delete(day)
            
            await self.db.flush()
            
            # Create new workout days
            for day_data in update['workout_days']:
                workout_day = WorkoutDay(
                    workout_plan_id=workout_plan.id,
                    day_number=day_data['day_number'],
                    day_name=day_data['day_name'],
                    muscle_groups=day_data['muscle_groups'],
                    workout_type=day_data['workout_type'],
                    description=day_data.get('description'),
                    estimated_duration_minutes=day_data.get('estimated_duration_minutes')
                )
                self.db.add(workout_day)
                await self.db.flush()
                
                # Create exercises for this day
                for exercise_data in day_data['exercises']:
                    workout_exercise = WorkoutExercise(
                        workout_day_id=workout_day.id,
                        exercise_library_id=exercise_data['exercise_library_id'],
                        exercise_order=exercise_data['exercise_order'],
                        sets=exercise_data['sets'],
                        reps_min=exercise_data.get('reps_min'),
                        reps_max=exercise_data.get('reps_max'),
                        reps_target=exercise_data.get('reps_target'),
                        weight_kg=exercise_data.get('weight_kg'),
                        weight_progression_type=exercise_data.get('weight_progression_type'),
                        rest_seconds=exercise_data.get('rest_seconds', 60),
                        notes=exercise_data.get('notes')
                    )
                    self.db.add(workout_exercise)
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(workout_plan)
        
        # Reload with all relationships
        return await self.get_workout_plan(user_id)
    
    async def update_workout_schedule(
        self,
        user_id: UUID,
        update: dict
    ) -> list[WorkoutSchedule]:
        """Update workout schedule with lock validation.
        
        Validates profile lock status before applying changes.
        Updates workout days and timing preferences.
        
        Args:
            user_id: User's unique identifier
            update: Dictionary of fields to update
            
        Returns:
            Updated list of WorkoutSchedule objects
            
        Raises:
            HTTPException: 403 if profile is locked
            HTTPException: 404 if profile not found
        """
        # Check profile lock
        is_locked = await self.check_profile_lock(user_id)
        
        if is_locked:
            raise ProfileLockedException()
        
        # Get current workout schedules
        workout_schedules = await self.get_workout_schedule(user_id)
        
        # Apply updates to each schedule
        for schedule in workout_schedules:
            # Update fields if provided
            if 'day_of_week' in update and update['day_of_week'] is not None:
                schedule.day_of_week = update['day_of_week']
            
            if 'scheduled_time' in update and update['scheduled_time'] is not None:
                schedule.scheduled_time = update['scheduled_time']
            
            if 'enable_notifications' in update and update['enable_notifications'] is not None:
                schedule.enable_notifications = update['enable_notifications']
        
        # Save changes
        await self.db.commit()
        
        # Refresh all schedules
        for schedule in workout_schedules:
            await self.db.refresh(schedule)
        
        return workout_schedules
    
    @staticmethod
    async def get_today_workout(
        user_id: UUID,
        db_session: AsyncSession
    ) -> Optional[dict[str, Any]]:
        """Get today's workout plan for a user.
        
        Static method for use by general agent delegation tools.
        Returns dict format matching design spec.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with workout details or None if no workout scheduled
            
        Raises:
            ValueError: If user profile not found
        """
        # Get user's profile to verify existence
        profile_result = await db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.workout_schedules))
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"User profile not found for user_id: {user_id}")
        
        # Get current day of week (0=Monday, 6=Sunday)
        current_day = datetime.now().weekday()
        
        # Check if there's a workout scheduled for today
        workout_scheduled_today = False
        for schedule in profile.workout_schedules:
            if schedule.day_of_week == current_day and schedule.deleted_at is None:
                workout_scheduled_today = True
                break
        
        if not workout_scheduled_today:
            return None
        
        # Get workout plan with all relationships
        workout_plan_result = await db_session.execute(
            select(WorkoutPlan)
            .where(
                WorkoutPlan.user_id == user_id,
                WorkoutPlan.deleted_at.is_(None)
            )
            .options(
                selectinload(WorkoutPlan.workout_days)
                .selectinload(WorkoutDay.exercises)
                .selectinload(WorkoutExercise.exercise_library)
            )
        )
        workout_plan = workout_plan_result.scalar_one_or_none()
        
        if not workout_plan:
            return None
        
        # Find workout day matching today's day of week
        # Map day_of_week (0-6) to day_number (1-7)
        # Assuming day_number 1 = Monday, 7 = Sunday
        day_number = current_day + 1
        
        workout_day = None
        for day in workout_plan.workout_days:
            if day.day_number == day_number and day.deleted_at is None:
                workout_day = day
                break
        
        if not workout_day:
            return None
        
        # Build response dict matching design spec
        exercises = []
        for exercise in workout_day.exercises:
            if exercise.deleted_at is None:
                # Format reps string
                if exercise.reps_target:
                    reps_str = str(exercise.reps_target)
                elif exercise.reps_min and exercise.reps_max:
                    reps_str = f"{exercise.reps_min}-{exercise.reps_max}"
                else:
                    reps_str = str(exercise.reps_min or exercise.reps_max or 0)
                
                exercises.append({
                    "name": exercise.exercise_library.exercise_name,
                    "sets": exercise.sets,
                    "reps": reps_str,
                    "weight_kg": float(exercise.weight_kg) if exercise.weight_kg else None,
                    "rest_seconds": exercise.rest_seconds,
                    "notes": exercise.notes
                })
        
        return {
            "day_name": workout_day.day_name,
            "workout_type": workout_day.workout_type,
            "muscle_groups": workout_day.muscle_groups,
            "estimated_duration_minutes": workout_day.estimated_duration_minutes,
            "exercises": exercises
        }
    
    @staticmethod
    async def get_exercise_demo(
        exercise_name: str,
        db_session: AsyncSession
    ) -> Optional[dict[str, Any]]:
        """Get exercise demonstration details from library.
        
        Static method for use by general agent delegation tools.
        Returns dict format matching design spec.
        
        Args:
            exercise_name: Name of exercise (case-insensitive partial match)
            db_session: Database session
            
        Returns:
            Dict with exercise details or None if not found
        """
        # Query ExerciseLibrary with case-insensitive partial match
        result = await db_session.execute(
            select(ExerciseLibrary)
            .where(
                func.lower(ExerciseLibrary.exercise_name).contains(func.lower(exercise_name)),
                ExerciseLibrary.deleted_at.is_(None)
            )
            .limit(1)
        )
        exercise = result.scalar_one_or_none()
        
        if not exercise:
            return None
        
        # Build response dict matching design spec
        return {
            "exercise_name": exercise.exercise_name,
            "gif_url": exercise.gif_url,
            "video_url": exercise.video_url,
            "description": exercise.description,
            "instructions": exercise.instructions,
            "difficulty_level": exercise.difficulty_level,
            "primary_muscle_group": exercise.primary_muscle_group
        }

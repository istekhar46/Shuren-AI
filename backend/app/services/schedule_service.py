"""Schedule service for managing workout and meal schedules."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.preferences import MealSchedule, WorkoutSchedule
from app.models.profile import UserProfile


class ScheduleService:
    """Service for schedule-related database operations."""
    
    @staticmethod
    async def get_upcoming_schedule(
        user_id: UUID,
        db_session: AsyncSession
    ) -> dict[str, Any]:
        """Get upcoming workout and meal schedules for a user.
        
        Queries WorkoutSchedule and MealSchedule tables to retrieve all
        configured schedules with timing and notification settings.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with workout and meal schedules
            
        Raises:
            ValueError: If user profile not found
        """
        # Get user's profile to verify existence and load schedules
        profile_result = await db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.workout_schedules),
                selectinload(UserProfile.meal_schedules)
            )
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"User profile not found for user_id: {user_id}")
        
        # Map day_of_week integer to day name
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Build workout schedules list
        workouts = []
        for schedule in profile.workout_schedules:
            if schedule.deleted_at is None:
                workouts.append({
                    "id": str(schedule.id),
                    "day": day_names[schedule.day_of_week],
                    "day_of_week": schedule.day_of_week,
                    "time": schedule.scheduled_time.isoformat() if schedule.scheduled_time else None,
                    "notifications_enabled": schedule.enable_notifications
                })
        
        # Build meal schedules list
        meals = []
        for schedule in profile.meal_schedules:
            if schedule.deleted_at is None:
                meals.append({
                    "id": str(schedule.id),
                    "meal_name": schedule.meal_name,
                    "time": schedule.scheduled_time.isoformat() if schedule.scheduled_time else None,
                    "notifications_enabled": schedule.enable_notifications
                })
        
        # Build response dict matching design spec
        return {
            "workouts": workouts,
            "meals": meals
        }

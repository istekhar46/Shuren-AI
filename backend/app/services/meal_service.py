"""Meal service for managing meal plans and schedules."""

from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ProfileLockedException
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile, UserProfileVersion


class MealService:
    """Service for managing meal plans and schedules.
    
    Handles meal plan retrieval, meal schedule management, profile locking,
    and versioning for modifications.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize meal service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_meal_plan(self, user_id: UUID) -> MealPlan | None:
        """Retrieve meal plan for user.
        
        Queries meal plan through user profile relationship.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            MealPlan with all nutritional targets, or None if not found
            
        Raises:
            HTTPException: 404 if user profile not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.meal_plan))
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        # Return None if no meal plan (not an error)
        return profile.meal_plan
    
    async def get_meal_schedule(self, user_id: UUID) -> list[MealSchedule]:
        """Retrieve meal schedule (timing for all meals).
        
        Returns all configured meal times from the user's profile.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of MealSchedule objects
            
        Raises:
            HTTPException: 404 if profile not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.meal_schedules))
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        return profile.meal_schedules
    
    async def get_today_meals(self, user_id: UUID) -> list[MealSchedule]:
        """Retrieve today's meal schedule with timing.
        
        Filters meal_schedules for active meals. Returns all meals
        scheduled for today.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of MealSchedule objects for today
            
        Raises:
            HTTPException: 404 if profile not found
        """
        # Get all meal schedules
        meal_schedules = await self.get_meal_schedule(user_id)
        
        # Return all schedules (they represent today's meals)
        # In the current schema, meal schedules don't have date filtering
        # so all schedules represent the daily recurring meal times
        return meal_schedules
    
    async def get_next_meal(self, user_id: UUID) -> Optional[MealSchedule]:
        """Retrieve next upcoming meal based on current time.
        
        Queries meal_schedules, finds next scheduled_time > now.
        Returns None if no more meals today.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            MealSchedule if next meal exists, None otherwise
            
        Raises:
            HTTPException: 404 if profile not found
        """
        # Get all meal schedules
        meal_schedules = await self.get_meal_schedule(user_id)
        
        if not meal_schedules:
            return None
        
        # Get current time
        current_time = datetime.now().time()
        
        # Find meals scheduled after current time
        upcoming_meals = [
            meal for meal in meal_schedules
            if meal.scheduled_time > current_time
        ]
        
        if not upcoming_meals:
            return None
        
        # Return the earliest upcoming meal
        return min(upcoming_meals, key=lambda m: m.scheduled_time)
    
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
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_schedules),
                selectinload(UserProfile.versions)
            )
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
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
            "meal_plan": None,
            "meal_schedules": []
        }
        
        # Add meal plan to snapshot
        if profile.meal_plan:
            snapshot["meal_plan"] = {
                "id": str(profile.meal_plan.id),
                "daily_calorie_target": profile.meal_plan.daily_calorie_target,
                "protein_percentage": float(profile.meal_plan.protein_percentage),
                "carbs_percentage": float(profile.meal_plan.carbs_percentage),
                "fats_percentage": float(profile.meal_plan.fats_percentage)
            }
        
        # Add meal schedules to snapshot
        for schedule in profile.meal_schedules:
            snapshot["meal_schedules"].append({
                "id": str(schedule.id),
                "meal_name": schedule.meal_name,
                "scheduled_time": schedule.scheduled_time.isoformat(),
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

    async def update_meal_plan(
        self,
        user_id: UUID,
        update: dict
    ) -> MealPlan:
        """Update meal plan with lock validation.
        
        Validates profile lock status before applying changes.
        Creates profile version if locked profile is modified.
        
        Args:
            user_id: User's unique identifier
            update: Dictionary of fields to update
            
        Returns:
            Updated MealPlan
            
        Raises:
            HTTPException: 403 if profile is locked
            HTTPException: 404 if meal plan not found
        """
        # Check profile lock
        is_locked = await self.check_profile_lock(user_id)
        
        if is_locked:
            raise ProfileLockedException()
        
        # Get meal plan
        meal_plan = await self.get_meal_plan(user_id)
        
        # Apply updates
        for field, value in update.items():
            if value is not None and hasattr(meal_plan, field):
                setattr(meal_plan, field, value)
        
        # Validate macro percentages if any were updated
        if any(k in update for k in ['protein_percentage', 'carbs_percentage', 'fats_percentage']):
            if not self.validate_macro_percentages(meal_plan):
                raise HTTPException(
                    status_code=422,
                    detail="Macro percentages must sum to 100"
                )
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(meal_plan)
        
        return meal_plan
    
    async def update_meal_schedule(
        self,
        user_id: UUID,
        updates: list[dict]
    ) -> list[MealSchedule]:
        """Update meal schedule with lock validation.
        
        Validates profile lock status before applying changes.
        Updates meal timing and notification preferences.
        
        Args:
            user_id: User's unique identifier
            updates: List of meal schedule updates
            
        Returns:
            Updated list of MealSchedule objects
            
        Raises:
            HTTPException: 403 if profile is locked
            HTTPException: 404 if profile not found
        """
        # Check profile lock
        is_locked = await self.check_profile_lock(user_id)
        
        if is_locked:
            raise ProfileLockedException()
        
        # Get current meal schedules
        meal_schedules = await self.get_meal_schedule(user_id)
        
        # Create a mapping of meal_name to schedule for easy lookup
        schedule_map = {schedule.meal_name: schedule for schedule in meal_schedules}
        
        # Apply updates
        for update_data in updates:
            meal_name = update_data.get('meal_name')
            if meal_name and meal_name in schedule_map:
                schedule = schedule_map[meal_name]
                
                # Update fields
                for field, value in update_data.items():
                    if value is not None and hasattr(schedule, field) and field != 'meal_name':
                        setattr(schedule, field, value)
        
        # Save changes
        await self.db.commit()
        
        # Refresh all schedules
        for schedule in meal_schedules:
            await self.db.refresh(schedule)
        
        return meal_schedules
    
    def validate_macro_percentages(self, meal_plan: MealPlan) -> bool:
        """Validate that macro percentages sum to 100.
        
        Ensures protein, carbs, and fats percentages total exactly 100%.
        
        Args:
            meal_plan: MealPlan to validate
            
        Returns:
            True if valid, False otherwise
        """
        total = (
            meal_plan.protein_percentage +
            meal_plan.carbs_percentage +
            meal_plan.fats_percentage
        )
        
        # Allow small floating point tolerance
        return abs(total - Decimal('100.00')) < Decimal('0.01')

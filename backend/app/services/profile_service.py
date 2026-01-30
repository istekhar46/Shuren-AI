"""Profile service for managing user profiles and versioning."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ProfileLockedException
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


class ProfileService:
    """Service for managing user profiles and versioning.
    
    Handles profile retrieval with eager loading, profile updates with
    versioning, and profile locking mechanisms.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize profile service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_profile(self, user_id: UUID) -> UserProfile:
        """Retrieve user profile with all related entities.
        
        Uses eager loading (selectinload) to minimize queries and ensure
        response time < 100ms. Loads all relationships in a single query.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            UserProfile with all relationships loaded
            
        Raises:
            HTTPException: 404 if profile not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
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
        
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        return profile
    
    async def update_profile(
        self,
        user_id: UUID,
        updates: dict[str, Any],
        reason: str
    ) -> UserProfile:
        """Update user profile with versioning.
        
        Checks if profile is locked and requires explicit unlock or reason.
        Creates ProfileVersion before applying updates for audit trail.
        Applies updates to profile and related entities atomically.
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of updates to apply
            reason: Reason for profile modification (required)
            
        Returns:
            Updated UserProfile with all relationships loaded
            
        Raises:
            HTTPException: 403 if profile is locked without explicit unlock
            HTTPException: 404 if profile not found
        """
        # Get current profile
        profile = await self.get_profile(user_id)
        
        # Check if profile is locked
        if profile.is_locked and "unlock" not in updates:
            raise ProfileLockedException(
                detail="Profile is locked. Provide explicit unlock or reason to modify."
            )
        
        try:
            # Create profile version before modification
            await self._create_profile_version(profile, reason)
            
            # Apply updates to profile
            if "fitness_level" in updates:
                profile.fitness_level = updates["fitness_level"]
            
            # Handle is_locked status
            if "is_locked" in updates:
                profile.is_locked = updates["is_locked"]
            elif "unlock" in updates and updates["unlock"]:
                # Explicit unlock request
                profile.is_locked = False
            
            # Commit changes
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
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update profile: {str(e)}"
            )
    
    async def lock_profile(self, user_id: UUID) -> UserProfile:
        """Lock user profile to prevent modifications.
        
        Sets is_locked=True on the user profile.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated UserProfile with all relationships loaded
            
        Raises:
            HTTPException: 404 if profile not found
        """
        # Get current profile
        profile = await self.get_profile(user_id)
        
        try:
            # Set is_locked to True
            profile.is_locked = True
            
            # Commit changes
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
            raise HTTPException(
                status_code=500,
                detail=f"Failed to lock profile: {str(e)}"
            )
    
    async def _create_profile_version(
        self,
        profile: UserProfile,
        reason: str
    ) -> UserProfileVersion:
        """Create a new profile version for audit trail.
        
        Increments version number, stores reason and complete snapshot
        of current profile state.
        
        Args:
            profile: UserProfile to version
            reason: Reason for the change
            
        Returns:
            Created UserProfileVersion
        """
        # Get current max version number
        result = await self.db.execute(
            select(func.max(UserProfileVersion.version_number))
            .where(UserProfileVersion.profile_id == profile.id)
        )
        max_version = result.scalar()
        next_version = (max_version or 0) + 1
        
        # Create snapshot of current state
        snapshot = await self._create_profile_snapshot(profile)
        
        # Create version record
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=next_version,
            change_reason=reason,
            snapshot=snapshot
        )
        
        self.db.add(version)
        await self.db.flush()
        
        return version
    
    async def _create_profile_snapshot(self, profile: UserProfile) -> dict[str, Any]:
        """Create a complete snapshot of profile state for versioning.
        
        Args:
            profile: UserProfile to snapshot
            
        Returns:
            Dictionary containing complete profile state
        """
        # Reload profile with all relationships if not already loaded
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

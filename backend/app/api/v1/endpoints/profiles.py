"""
Profile endpoints for managing user profiles.

This module provides REST API endpoints for:
- Retrieving user profile with all related entities
- Updating user profile with versioning
- Locking user profile
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileUpdateRequest, UserProfileResponse
from app.services.profile_service import ProfileService


router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserProfileResponse:
    """
    Get current user's profile with all related entities.
    
    Retrieves the complete user profile including fitness goals, physical constraints,
    dietary preferences, meal plan, meal schedules, workout schedules, hydration
    preferences, and lifestyle baseline. Uses eager loading for optimal performance
    (< 100ms response time).
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        UserProfileResponse with complete profile data including all relationships
        
    Raises:
        HTTPException(404): If profile not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize profile service
    profile_service = ProfileService(db)
    
    # Get profile with all relationships
    profile = await profile_service.get_profile(current_user.id)
    
    # Build response with all relationships
    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        is_locked=profile.is_locked,
        fitness_level=profile.fitness_level,
        fitness_goals=[
            {
                "goal_type": goal.goal_type,
                "target_weight_kg": float(goal.target_weight_kg) if goal.target_weight_kg else None,
                "target_body_fat_percentage": float(goal.target_body_fat_percentage) if goal.target_body_fat_percentage else None,
                "priority": goal.priority
            }
            for goal in profile.fitness_goals
        ],
        physical_constraints=[
            {
                "constraint_type": constraint.constraint_type,
                "description": constraint.description,
                "severity": constraint.severity
            }
            for constraint in profile.physical_constraints
        ],
        dietary_preferences={
            "diet_type": profile.dietary_preferences.diet_type,
            "allergies": profile.dietary_preferences.allergies or [],
            "intolerances": profile.dietary_preferences.intolerances or [],
            "dislikes": profile.dietary_preferences.dislikes or []
        } if profile.dietary_preferences else None,
        meal_plan={
            "daily_calorie_target": profile.meal_plan.daily_calorie_target,
            "protein_percentage": float(profile.meal_plan.protein_percentage),
            "carbs_percentage": float(profile.meal_plan.carbs_percentage),
            "fats_percentage": float(profile.meal_plan.fats_percentage)
        } if profile.meal_plan else None,
        meal_schedules=[
            {
                "meal_name": schedule.meal_name,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.meal_schedules
        ],
        workout_schedules=[
            {
                "day_of_week": schedule.day_of_week,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.workout_schedules
        ],
        hydration_preferences={
            "daily_water_target_ml": profile.hydration_preferences.daily_water_target_ml,
            "reminder_frequency_minutes": profile.hydration_preferences.reminder_frequency_minutes,
            "enable_notifications": profile.hydration_preferences.enable_notifications
        } if profile.hydration_preferences else None,
        lifestyle_baseline={
            "energy_level": profile.lifestyle_baseline.energy_level,
            "stress_level": profile.lifestyle_baseline.stress_level,
            "sleep_quality": profile.lifestyle_baseline.sleep_quality
        } if profile.lifestyle_baseline else None
    )



@router.patch("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    update_request: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserProfileResponse:
    """
    Update current user's profile with versioning.
    
    Updates the user profile with the provided changes. Creates a profile version
    for audit trail before applying updates. If the profile is locked, requires
    explicit unlock or reason for modification.
    
    Args:
        update_request: ProfileUpdateRequest with reason and updates dictionary
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        UserProfileResponse with updated profile data including all relationships
        
    Raises:
        HTTPException(403): If profile is locked without explicit unlock
        HTTPException(404): If profile not found
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize profile service
    profile_service = ProfileService(db)
    
    # Update profile with versioning
    profile = await profile_service.update_profile(
        user_id=current_user.id,
        updates=update_request.updates,
        reason=update_request.reason
    )
    
    # Build response with all relationships
    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        is_locked=profile.is_locked,
        fitness_level=profile.fitness_level,
        fitness_goals=[
            {
                "goal_type": goal.goal_type,
                "target_weight_kg": float(goal.target_weight_kg) if goal.target_weight_kg else None,
                "target_body_fat_percentage": float(goal.target_body_fat_percentage) if goal.target_body_fat_percentage else None,
                "priority": goal.priority
            }
            for goal in profile.fitness_goals
        ],
        physical_constraints=[
            {
                "constraint_type": constraint.constraint_type,
                "description": constraint.description,
                "severity": constraint.severity
            }
            for constraint in profile.physical_constraints
        ],
        dietary_preferences={
            "diet_type": profile.dietary_preferences.diet_type,
            "allergies": profile.dietary_preferences.allergies or [],
            "intolerances": profile.dietary_preferences.intolerances or [],
            "dislikes": profile.dietary_preferences.dislikes or []
        } if profile.dietary_preferences else None,
        meal_plan={
            "daily_calorie_target": profile.meal_plan.daily_calorie_target,
            "protein_percentage": float(profile.meal_plan.protein_percentage),
            "carbs_percentage": float(profile.meal_plan.carbs_percentage),
            "fats_percentage": float(profile.meal_plan.fats_percentage)
        } if profile.meal_plan else None,
        meal_schedules=[
            {
                "meal_name": schedule.meal_name,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.meal_schedules
        ],
        workout_schedules=[
            {
                "day_of_week": schedule.day_of_week,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.workout_schedules
        ],
        hydration_preferences={
            "daily_water_target_ml": profile.hydration_preferences.daily_water_target_ml,
            "reminder_frequency_minutes": profile.hydration_preferences.reminder_frequency_minutes,
            "enable_notifications": profile.hydration_preferences.enable_notifications
        } if profile.hydration_preferences else None,
        lifestyle_baseline={
            "energy_level": profile.lifestyle_baseline.energy_level,
            "stress_level": profile.lifestyle_baseline.stress_level,
            "sleep_quality": profile.lifestyle_baseline.sleep_quality
        } if profile.lifestyle_baseline else None
    )



@router.post("/me/lock", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def lock_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserProfileResponse:
    """
    Lock current user's profile to prevent modifications.
    
    Sets is_locked=True on the user profile. A locked profile requires explicit
    unlock or reason for any modifications.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        UserProfileResponse with updated profile data including all relationships
        
    Raises:
        HTTPException(404): If profile not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize profile service
    profile_service = ProfileService(db)
    
    # Lock profile
    profile = await profile_service.lock_profile(current_user.id)
    
    # Build response with all relationships
    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        is_locked=profile.is_locked,
        fitness_level=profile.fitness_level,
        fitness_goals=[
            {
                "goal_type": goal.goal_type,
                "target_weight_kg": float(goal.target_weight_kg) if goal.target_weight_kg else None,
                "target_body_fat_percentage": float(goal.target_body_fat_percentage) if goal.target_body_fat_percentage else None,
                "priority": goal.priority
            }
            for goal in profile.fitness_goals
        ],
        physical_constraints=[
            {
                "constraint_type": constraint.constraint_type,
                "description": constraint.description,
                "severity": constraint.severity
            }
            for constraint in profile.physical_constraints
        ],
        dietary_preferences={
            "diet_type": profile.dietary_preferences.diet_type,
            "allergies": profile.dietary_preferences.allergies or [],
            "intolerances": profile.dietary_preferences.intolerances or [],
            "dislikes": profile.dietary_preferences.dislikes or []
        } if profile.dietary_preferences else None,
        meal_plan={
            "daily_calorie_target": profile.meal_plan.daily_calorie_target,
            "protein_percentage": float(profile.meal_plan.protein_percentage),
            "carbs_percentage": float(profile.meal_plan.carbs_percentage),
            "fats_percentage": float(profile.meal_plan.fats_percentage)
        } if profile.meal_plan else None,
        meal_schedules=[
            {
                "meal_name": schedule.meal_name,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.meal_schedules
        ],
        workout_schedules=[
            {
                "day_of_week": schedule.day_of_week,
                "scheduled_time": schedule.scheduled_time,
                "enable_notifications": schedule.enable_notifications
            }
            for schedule in profile.workout_schedules
        ],
        hydration_preferences={
            "daily_water_target_ml": profile.hydration_preferences.daily_water_target_ml,
            "reminder_frequency_minutes": profile.hydration_preferences.reminder_frequency_minutes,
            "enable_notifications": profile.hydration_preferences.enable_notifications
        } if profile.hydration_preferences else None,
        lifestyle_baseline={
            "energy_level": profile.lifestyle_baseline.energy_level,
            "stress_level": profile.lifestyle_baseline.stress_level,
            "sleep_quality": profile.lifestyle_baseline.sleep_quality
        } if profile.lifestyle_baseline else None
    )

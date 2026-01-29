"""
Onboarding endpoints for managing user onboarding flow.

This module provides REST API endpoints for:
- Retrieving current onboarding state
- Submitting onboarding step data
- Completing onboarding and creating user profile
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingStateResponse,
    OnboardingStepRequest,
    OnboardingStepResponse
)
from app.schemas.profile import UserProfileResponse
from app.services.onboarding_service import OnboardingService, OnboardingValidationError


router = APIRouter()


@router.get("/state", response_model=OnboardingStateResponse, status_code=status.HTTP_200_OK)
async def get_onboarding_state(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingStateResponse:
    """
    Get current onboarding state for authenticated user.
    
    Retrieves the user's current progress through the onboarding flow,
    including current step number, completion status, and all saved step data.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        OnboardingStateResponse with id, user_id, current_step, is_complete, step_data
        
    Raises:
        HTTPException(404): If onboarding state not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Get onboarding state
    onboarding_state = await onboarding_service.get_onboarding_state(current_user.id)
    
    if not onboarding_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding state not found"
        )
    
    return OnboardingStateResponse(
        id=str(onboarding_state.id),
        user_id=str(onboarding_state.user_id),
        current_step=onboarding_state.current_step,
        is_complete=onboarding_state.is_complete,
        step_data=onboarding_state.step_data or {}
    )


@router.post("/step", response_model=OnboardingStepResponse, status_code=status.HTTP_200_OK)
async def save_onboarding_step(
    step_request: OnboardingStepRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingStepResponse:
    """
    Save onboarding step data with validation.
    
    Validates step data according to step-specific requirements,
    saves to the onboarding state, and advances the current step.
    
    Args:
        step_request: OnboardingStepRequest with step number and data
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        OnboardingStepResponse with current_step, is_complete, and success message
        
    Raises:
        HTTPException(400): If step data is invalid
        HTTPException(422): If request validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Save onboarding step with validation
    try:
        onboarding_state = await onboarding_service.save_onboarding_step(
            user_id=current_user.id,
            step=step_request.step,
            data=step_request.data
        )
    except OnboardingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    return OnboardingStepResponse(
        current_step=onboarding_state.current_step,
        is_complete=onboarding_state.is_complete,
        message=f"Step {step_request.step} saved successfully"
    )


@router.post("/complete", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserProfileResponse:
    """
    Complete onboarding and create locked user profile.
    
    Verifies all 11 onboarding steps are complete, creates a UserProfile
    with all related entities (goals, constraints, preferences, schedules),
    creates initial profile version, and marks onboarding as complete.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        UserProfileResponse with complete profile data including all relationships
        
    Raises:
        HTTPException(400): If onboarding is incomplete
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Complete onboarding and create profile
    try:
        profile = await onboarding_service.complete_onboarding(current_user.id)
    except OnboardingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
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

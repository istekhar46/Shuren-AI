"""
Workout endpoints for managing workout plans and schedules.

This module provides REST API endpoints for:
- Retrieving workout plans with all exercises
- Accessing specific workout days
- Getting today's workout
- Viewing weekly workout schedule
- Updating workout plans and schedules
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.workout import (
    WorkoutDayResponse,
    WorkoutPlanResponse,
    WorkoutPlanUpdate,
    WorkoutScheduleResponse,
    WorkoutScheduleUpdate
)
from app.services.workout_service import WorkoutService


router = APIRouter()


@router.get(
    "/plan",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workout plan",
    responses={
        200: {
            "description": "Workout plan retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "plan_name": "Beginner Full Body",
                        "plan_description": "4-day full body workout for beginners",
                        "duration_weeks": 12,
                        "days_per_week": 4,
                        "plan_rationale": "Balanced approach for building strength foundation",
                        "is_locked": True,
                        "workout_days": [
                            {
                                "id": "223e4567-e89b-12d3-a456-426614174001",
                                "day_number": 1,
                                "day_name": "Upper Body Push",
                                "muscle_groups": ["chest", "shoulders", "triceps"],
                                "workout_type": "strength",
                                "description": "Focus on pushing movements",
                                "estimated_duration_minutes": 60,
                                "exercises": [
                                    {
                                        "id": "323e4567-e89b-12d3-a456-426614174002",
                                        "exercise_order": 1,
                                        "sets": 3,
                                        "reps_target": 10,
                                        "weight_kg": 60.0,
                                        "rest_seconds": 90,
                                        "exercise": {
                                            "id": "423e4567-e89b-12d3-a456-426614174003",
                                            "exercise_name": "Barbell Bench Press",
                                            "exercise_type": "strength",
                                            "primary_muscle_group": "chest",
                                            "gif_url": "https://example.com/bench-press.gif"
                                        }
                                    }
                                ]
                            }
                        ],
                        "created_at": "2026-01-15T10:00:00Z",
                        "updated_at": "2026-01-15T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Workout plan not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workout plan not found for user",
                        "error_code": "WORKOUT_PLAN_NOT_FOUND"
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        }
    }
)
async def get_workout_plan(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> WorkoutPlanResponse:
    """
    Get current user's complete workout plan.
    
    Retrieves the complete workout plan including all workout days and exercises
    with exercise library details (name, GIF URL, instructions). Uses eager loading
    for optimal performance (< 100ms response time).
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        WorkoutPlanResponse with complete workout plan including all days and exercises
        
    Raises:
        HTTPException(404): If workout plan not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Get workout plan with all relationships
    workout_plan = await workout_service.get_workout_plan(current_user.id)
    
    # Return response (Pydantic will handle serialization)
    return workout_plan


@router.get(
    "/plan/day/{day_number}",
    response_model=WorkoutDayResponse,
    status_code=status.HTTP_200_OK
)
async def get_workout_day(
    day_number: Annotated[int, Path(ge=1, le=7, description="Day number (1-7)")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> WorkoutDayResponse:
    """
    Get specific workout day with all exercises.
    
    Retrieves a specific workout day by day number (1-7) with all exercises
    and complete exercise library details.
    
    Args:
        day_number: Day number (1-7, validated by Path parameter)
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        WorkoutDayResponse with all exercises and exercise library details
        
    Raises:
        HTTPException(400): If day_number is invalid (handled by Path validation)
        HTTPException(404): If workout day not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Get workout day
    workout_day = await workout_service.get_workout_day(current_user.id, day_number)
    
    # Return response
    return workout_day


@router.get(
    "/today",
    response_model=WorkoutDayResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get today's workout",
    responses={
        200: {
            "description": "Today's workout retrieved successfully or null if no workout scheduled",
            "content": {
                "application/json": {
                    "examples": {
                        "with_workout": {
                            "summary": "Workout scheduled for today",
                            "value": {
                                "id": "223e4567-e89b-12d3-a456-426614174001",
                                "day_number": 1,
                                "day_name": "Upper Body Push",
                                "muscle_groups": ["chest", "shoulders", "triceps"],
                                "workout_type": "strength",
                                "description": "Focus on pushing movements",
                                "estimated_duration_minutes": 60,
                                "exercises": []
                            }
                        },
                        "no_workout": {
                            "summary": "No workout scheduled for today",
                            "value": None
                        }
                    }
                }
            }
        }
    }
)
async def get_today_workout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> WorkoutDayResponse | None:
    """
    Get today's workout based on workout schedule and current day.
    
    Returns the workout scheduled for today based on the user's workout schedule
    and the current day of the week. Returns null if no workout is scheduled today.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        WorkoutDayResponse with today's workout details, or None if no workout scheduled
        
    Raises:
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Get today's workout
    workout_day = await workout_service.get_today_workout(current_user.id)
    
    # Return workout or None (no 404 error)
    return workout_day


@router.get("/week", response_model=List[WorkoutDayResponse], status_code=status.HTTP_200_OK)
async def get_week_workouts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[WorkoutDayResponse]:
    """
    Get this week's workouts with exercise summaries.
    
    Returns all workout days from the user's workout plan with complete
    exercise details and summaries.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        List of WorkoutDayResponse objects with all workout days
        
    Raises:
        HTTPException(404): If workout plan not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Get week's workouts
    workout_days = await workout_service.get_week_workouts(current_user.id)
    
    # Return response
    return workout_days


@router.patch(
    "/plan",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workout plan",
    responses={
        200: {
            "description": "Workout plan updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "plan_name": "Updated Plan Name",
                        "duration_weeks": 16,
                        "is_locked": False
                    }
                }
            }
        },
        403: {
            "description": "Profile is locked",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Profile is locked. Unlock profile before making modifications.",
                        "error_code": "PROFILE_LOCKED"
                    }
                }
            }
        },
        404: {
            "description": "Workout plan not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workout plan not found for user"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "duration_weeks"],
                                "msg": "ensure this value is less than or equal to 52",
                                "type": "value_error.number.not_le"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def update_workout_plan(
    update_data: WorkoutPlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> WorkoutPlanResponse:
    """
    Update workout plan (requires unlocked profile).
    
    Updates the user's workout plan with the provided changes. Validates that
    the profile is unlocked before applying changes. Creates a profile version
    for audit trail if locked profile is modified.
    
    **Request Body Example:**
    ```json
    {
        "plan_name": "Advanced Strength Program",
        "duration_weeks": 16,
        "days_per_week": 5
    }
    ```
    
    Args:
        update_data: WorkoutPlanUpdate schema with fields to update
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        WorkoutPlanResponse with updated workout plan
        
    Raises:
        HTTPException(403): If profile is locked
        HTTPException(404): If workout plan not found
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Update workout plan (service handles lock validation)
    workout_plan = await workout_service.update_workout_plan(
        current_user.id,
        update_data.model_dump(exclude_unset=True)
    )
    
    # Return response
    return workout_plan


@router.get("/schedule", response_model=List[WorkoutScheduleResponse], status_code=status.HTTP_200_OK)
async def get_workout_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[WorkoutScheduleResponse]:
    """
    Get workout schedule (days and timing).
    
    Returns all configured workout days with timing from the user's profile.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        List of WorkoutScheduleResponse objects
        
    Raises:
        HTTPException(404): If profile not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Get workout schedule
    workout_schedules = await workout_service.get_workout_schedule(current_user.id)
    
    # Return response
    return workout_schedules


@router.patch("/schedule", response_model=List[WorkoutScheduleResponse], status_code=status.HTTP_200_OK)
async def update_workout_schedule(
    update_data: WorkoutScheduleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[WorkoutScheduleResponse]:
    """
    Update workout schedule (requires unlocked profile).
    
    Updates the user's workout schedule with the provided changes. Validates that
    the profile is unlocked before applying changes.
    
    Args:
        update_data: WorkoutScheduleUpdate schema with fields to update
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        List of WorkoutScheduleResponse objects with updated schedule
        
    Raises:
        HTTPException(403): If profile is locked
        HTTPException(404): If profile not found
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize workout service
    workout_service = WorkoutService(db)
    
    # Update workout schedule (service handles lock validation)
    workout_schedules = await workout_service.update_workout_schedule(
        current_user.id,
        update_data.model_dump(exclude_unset=True)
    )
    
    # Return response
    return workout_schedules

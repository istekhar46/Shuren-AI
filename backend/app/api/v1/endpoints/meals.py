"""
Meal endpoints for managing meal plans and schedules.

This module provides REST API endpoints for:
- Retrieving meal plans with nutritional targets
- Accessing meal schedules with timing
- Getting today's meals
- Getting next upcoming meal
- Updating meal plans and schedules
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal import (
    MealPlanResponse,
    MealPlanUpdate,
    MealScheduleItemResponse,
    MealScheduleResponse,
    MealScheduleUpdate
)
from app.services.meal_service import MealService


router = APIRouter()


@router.get(
    "/plan",
    response_model=MealPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get meal plan",
    responses={
        200: {
            "description": "Meal plan retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "meals_per_day": 4,
                        "daily_calories_target": 2500,
                        "daily_calories_min": 2300,
                        "daily_calories_max": 2700,
                        "protein_grams_target": 180.0,
                        "carbs_grams_target": 280.0,
                        "fats_grams_target": 70.0,
                        "protein_percentage": 30.0,
                        "carbs_percentage": 45.0,
                        "fats_percentage": 25.0,
                        "plan_rationale": "Balanced macros for muscle gain",
                        "is_locked": True,
                        "created_at": "2026-01-15T10:00:00Z",
                        "updated_at": "2026-01-15T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Meal plan not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Meal plan not found for user",
                        "error_code": "MEAL_PLAN_NOT_FOUND"
                    }
                }
            }
        }
    }
)
async def get_meal_plan(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealPlanResponse:
    """
    Get current user's meal plan.
    
    Retrieves the complete meal plan including calories, macros, and meal count.
    Uses the existing meal_plans table for optimal performance (< 100ms response time).
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealPlanResponse with complete nutritional targets
        
    Raises:
        HTTPException(404): If meal plan not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Get meal plan
    meal_plan = await meal_service.get_meal_plan(current_user.id)
    
    # Return response (Pydantic will handle serialization)
    return meal_plan


@router.patch(
    "/plan",
    response_model=MealPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update meal plan",
    responses={
        200: {
            "description": "Meal plan updated successfully"
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
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "daily_calories_target"],
                                "msg": "ensure this value is greater than or equal to 1000",
                                "type": "value_error.number.not_ge"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def update_meal_plan(
    update_data: MealPlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealPlanResponse:
    """
    Update meal plan (requires unlocked profile).
    
    Updates the user's meal plan with the provided changes. Validates that
    the profile is unlocked before applying changes. Creates a profile version
    for audit trail if locked profile is modified.
    
    **Request Body Example:**
    ```json
    {
        "daily_calories_target": 2800,
        "protein_grams_target": 200.0,
        "carbs_grams_target": 300.0,
        "fats_grams_target": 80.0
    }
    ```
    
    Args:
        update_data: MealPlanUpdate schema with fields to update
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealPlanResponse with updated meal plan
        
    Raises:
        HTTPException(403): If profile is locked
        HTTPException(404): If meal plan not found
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Update meal plan (service handles lock validation)
    meal_plan = await meal_service.update_meal_plan(
        current_user.id,
        update_data.model_dump(exclude_unset=True)
    )
    
    # Return response
    return meal_plan


@router.get("/schedule", response_model=MealScheduleResponse, status_code=status.HTTP_200_OK)
async def get_meal_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealScheduleResponse:
    """
    Get meal schedule (timing for all meals).
    
    Returns all configured meal times from the user's profile using the
    existing meal_schedules table.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealScheduleResponse with all meal timing information
        
    Raises:
        HTTPException(404): If profile not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Get meal schedule
    meal_schedules = await meal_service.get_meal_schedule(current_user.id)
    
    # Return response wrapped in MealScheduleResponse
    return MealScheduleResponse(meals=meal_schedules)


@router.patch("/schedule", response_model=MealScheduleResponse, status_code=status.HTTP_200_OK)
async def update_meal_schedule(
    update_data: MealScheduleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealScheduleResponse:
    """
    Update meal schedule (requires unlocked profile).
    
    Updates the user's meal schedule with the provided changes. Validates that
    the profile is unlocked before applying changes. Validates time format (HH:MM).
    
    Args:
        update_data: MealScheduleUpdate schema with fields to update
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealScheduleResponse with updated meal schedule
        
    Raises:
        HTTPException(403): If profile is locked
        HTTPException(404): If profile not found
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Convert Pydantic models to dictionaries for service layer
    updates = [meal.model_dump(exclude_unset=True) for meal in update_data.meals]
    
    # Update meal schedule (service handles lock validation)
    meal_schedules = await meal_service.update_meal_schedule(
        current_user.id,
        updates
    )
    
    # Return response wrapped in MealScheduleResponse
    return MealScheduleResponse(meals=meal_schedules)


@router.get("/today", response_model=List[MealScheduleItemResponse], status_code=status.HTTP_200_OK)
async def get_today_meals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[MealScheduleItemResponse]:
    """
    Get today's meals with timing.
    
    Returns all meals scheduled for the current day. Filters meal_schedules
    for active meals.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        List of MealScheduleItemResponse objects for today's meals
        
    Raises:
        HTTPException(404): If profile not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Get today's meals
    meal_schedules = await meal_service.get_today_meals(current_user.id)
    
    # Return response
    return meal_schedules


@router.get(
    "/next",
    response_model=MealScheduleItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get next meal",
    responses={
        200: {
            "description": "Next meal retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "meal_number": 2,
                        "meal_name": "Lunch",
                        "scheduled_time": "12:00:00",
                        "notification_offset_minutes": -15,
                        "earliest_time": "11:30:00",
                        "latest_time": "13:00:00",
                        "is_active": True
                    }
                }
            }
        },
        404: {
            "description": "No more meals scheduled today",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No more meals scheduled for today"
                    }
                }
            }
        }
    }
)
async def get_next_meal(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealScheduleItemResponse:
    """
    Get next upcoming meal based on current time.
    
    Returns the next upcoming meal based on current time. Queries meal_schedules,
    finds next scheduled_time > now. Returns 404 if no more meals today.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealScheduleItemResponse with next meal details
        
    Raises:
        HTTPException(404): If no more meals scheduled today
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal service
    meal_service = MealService(db)
    
    # Get next meal
    next_meal = await meal_service.get_next_meal(current_user.id)
    
    if not next_meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more meals scheduled for today"
        )
    
    # Return response
    return next_meal

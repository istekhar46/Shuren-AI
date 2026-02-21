"""
Meal template endpoints for managing weekly meal plans with dish recommendations.

This module provides REST API endpoints for:
- Retrieving today's meals with dish recommendations
- Getting next upcoming meal with dishes
- Accessing complete meal templates by week
- Regenerating meal templates with preferences
- Swapping dishes in templates
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal_template import (
    DishSwapRequest,
    MealTemplateResponse,
    NextMealResponse,
    TemplateRegenerateRequest,
    TodayMealsResponse
)
from app.services.meal_template_service import MealTemplateService


router = APIRouter()


@router.get(
    "/today",
    response_model=TodayMealsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get today's meals",
    responses={
        200: {
            "description": "Today's meals retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "date": "2026-01-30",
                        "day_of_week": 4,
                        "day_name": "Friday",
                        "meals": [
                            {
                                "meal_name": "Breakfast",
                                "scheduled_time": "08:00:00",
                                "day_of_week": 4,
                                "primary_dish": {
                                    "id": "223e4567-e89b-12d3-a456-426614174000",
                                    "name": "Egg Omelette with Multigrain Toast",
                                    "meal_type": "breakfast",
                                    "calories": 350,
                                    "protein_g": 25
                                },
                                "alternative_dishes": []
                            }
                        ],
                        "total_calories": 2200,
                        "total_protein_g": 165,
                        "total_carbs_g": 220,
                        "total_fats_g": 73
                    }
                }
            }
        },
        404: {
            "description": "No active meal template found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No active meal template found"
                    }
                }
            }
        }
    }
)
async def get_today_meals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TodayMealsResponse:
    """
    Get today's meals with dish recommendations.
    
    Returns all meals scheduled for today with primary and alternative dish options.
    Includes nutritional totals for the day based on primary dishes.
    
    The response includes:
    - Today's date and day of week
    - All scheduled meals with timing
    - Primary dish recommendation for each meal
    - Alternative dish options (typically 2-3 per meal)
    - Daily nutritional totals (calories, protein, carbs, fats)
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        TodayMealsResponse with complete meal plan for today
        
    Raises:
        HTTPException(404): If no active meal template is found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal template service
    service = MealTemplateService(db)
    profile = current_user.profile
    
    # Get today's meals from service
    meals_data = await service.get_today_meals(profile.id)
    
    # Return response (Pydantic will handle serialization)
    return TodayMealsResponse(**meals_data)


@router.get(
    "/next",
    response_model=NextMealResponse,
    status_code=status.HTTP_200_OK,
    summary="Get next meal",
    responses={
        200: {
            "description": "Next meal retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "meal_name": "Lunch",
                        "scheduled_time": "13:00:00",
                        "time_until_meal_minutes": 45,
                        "primary_dish": {
                            "id": "423e4567-e89b-12d3-a456-426614174000",
                            "name": "Grilled Chicken with Brown Rice",
                            "meal_type": "lunch",
                            "calories": 550,
                            "protein_g": 45
                        },
                        "alternative_dishes": []
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
) -> NextMealResponse:
    """
    Get next upcoming meal with dish recommendations.
    
    Returns the next meal after the current time with dish options and
    time until the meal. Useful for "What should I eat next?" queries.
    
    The response includes:
    - Meal name and scheduled time
    - Minutes until the meal
    - Primary dish recommendation
    - Alternative dish options
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        NextMealResponse with next meal details
        
    Raises:
        HTTPException(404): If no more meals scheduled for today
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal template service
    service = MealTemplateService(db)
    profile = current_user.profile
    
    # Get next meal from service
    next_meal = await service.get_next_meal(profile.id)
    
    if not next_meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more meals scheduled for today"
        )
    
    # Return response
    return NextMealResponse(**next_meal)


@router.get(
    "/template",
    response_model=MealTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get meal template",
    responses={
        200: {
            "description": "Meal template retrieved successfully"
        },
        404: {
            "description": "Meal template not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Meal template not found"
                    }
                }
            }
        }
    }
)
async def get_meal_template(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    week_number: Annotated[int | None, Query(ge=1, le=4, description="Week number (1-4) to retrieve. If not provided, returns currently active template")] = None
) -> MealTemplateResponse:
    """
    Get meal template for specified week.
    
    Returns a complete 7-day meal template with all meals and dishes.
    If week_number is not provided, returns the currently active template
    based on the 4-week rotation.
    
    The response includes:
    - Template metadata (id, week number, active status)
    - All 7 days with complete meal plans
    - Primary and alternative dishes for each meal
    - Daily nutritional totals
    
    Args:
        week_number: Optional week number (1-4). If None, returns active template
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealTemplateResponse with complete weekly meal plan
        
    Raises:
        HTTPException(404): If meal template not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize meal template service
    service = MealTemplateService(db)
    profile = current_user.profile
    
    # Get template by week or active template
    if week_number:
        template = await service.get_template_by_week(profile.id, week_number)
    else:
        template = await service.get_active_template(profile.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal template not found"
        )
    
    # Transform template to response format
    # Group template meals by day
    days_data = {}
    for day in range(7):
        day_meals = [tm for tm in template.template_meals if tm.day_of_week == day]
        
        # Group by meal schedule
        meals_by_schedule = {}
        for tm in day_meals:
            schedule_id = tm.meal_schedule_id
            if schedule_id not in meals_by_schedule:
                meals_by_schedule[schedule_id] = {
                    'meal_schedule': tm.meal_schedule,
                    'primary': None,
                    'alternatives': []
                }
            
            if tm.is_primary:
                meals_by_schedule[schedule_id]['primary'] = tm.dish
            else:
                meals_by_schedule[schedule_id]['alternatives'].append(tm.dish)
        
        # Build meal slots
        meal_slots = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for schedule_data in meals_by_schedule.values():
            primary_dish = schedule_data['primary']
            if primary_dish:
                meal_slots.append({
                    'meal_name': schedule_data['meal_schedule'].meal_name,
                    'scheduled_time': schedule_data['meal_schedule'].scheduled_time,
                    'day_of_week': day,
                    'primary_dish': primary_dish,
                    'alternative_dishes': schedule_data['alternatives']
                })
                
                total_calories += float(primary_dish.calories)
                total_protein += float(primary_dish.protein_g)
                total_carbs += float(primary_dish.carbs_g)
                total_fats += float(primary_dish.fats_g)
        
        # Sort meals by scheduled time
        meal_slots.sort(key=lambda m: m['scheduled_time'])
        
        # Get day name
        from datetime import date, timedelta
        today = date.today()
        day_offset = (day - today.weekday()) % 7
        target_date = today + timedelta(days=day_offset)
        day_name = target_date.strftime('%A')
        
        days_data[day] = {
            'day_of_week': day,
            'day_name': day_name,
            'meals': meal_slots,
            'total_calories': total_calories,
            'total_protein_g': total_protein,
            'total_carbs_g': total_carbs,
            'total_fats_g': total_fats
        }
    
    # Build response
    return MealTemplateResponse(
        id=template.id,
        week_number=template.week_number,
        is_active=template.is_active,
        days=[days_data[day] for day in range(7)],
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.post(
    "/template/regenerate",
    response_model=MealTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Regenerate meal template",
    responses={
        201: {
            "description": "Meal template regenerated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "week_number": 1,
                        "is_active": True,
                        "days": [
                            {
                                "day_of_week": 0,
                                "day_name": "Monday",
                                "meals": [],
                                "total_calories": 2200,
                                "total_protein_g": 165,
                                "total_carbs_g": 220,
                                "total_fats_g": 73
                            }
                        ],
                        "created_at": "2026-01-30T10:00:00Z",
                        "updated_at": "2026-01-30T10:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - missing required data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User must have meal plan and schedules configured"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - profile is locked",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Profile is locked. Unlock profile before making modifications.",
                        "error_code": "PROFILE_LOCKED"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error - could not find suitable dishes",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not find suitable dishes for Breakfast"
                    }
                }
            }
        }
    }
)
async def regenerate_meal_template(
    request: TemplateRegenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealTemplateResponse:
    """
    Regenerate meal template with new dishes.
    
    Creates a new meal template for the user with fresh dish recommendations.
    This allows users to get variety in their meal plans while maintaining
    the same nutritional targets and dietary preferences.
    
    The regeneration process:
    1. Validates that the profile is unlocked
    2. Determines which week to regenerate (current week if not specified)
    3. Deletes the existing template for that week (if any)
    4. Generates a new template with different dishes
    5. Maintains the same calorie and macro targets
    6. Respects dietary preferences and restrictions
    
    Users can optionally provide preferences to guide dish selection,
    such as "more chicken dishes" or "quick prep meals only".
    
    Args:
        request: Template regeneration request with optional preferences and week number
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        MealTemplateResponse with the newly generated template
        
    Raises:
        HTTPException(400): If user doesn't have meal plan or schedules configured
        HTTPException(403): If profile is locked
        HTTPException(500): If suitable dishes cannot be found
        HTTPException(401): If authentication fails (handled by dependency)
    
    Example:
        Request body:
        ```json
        {
            "preferences": "More chicken dishes, less spicy food",
            "week_number": 1
        }
        ```
        
        Response (201 Created):
        ```json
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "week_number": 1,
            "is_active": true,
            "days": [...],
            "created_at": "2026-01-30T10:00:00Z",
            "updated_at": "2026-01-30T10:00:00Z"
        }
        ```
    """
    from datetime import date
    from app.core.exceptions import ProfileLockedException
    
    # Initialize meal template service
    service = MealTemplateService(db)
    profile = current_user.profile
    
    # Determine week number to regenerate
    if request.week_number:
        week_number = request.week_number
    else:
        # Use current week in 4-week rotation
        week_of_year = date.today().isocalendar()[1]
        week_number = ((week_of_year - 1) % 4) + 1
    
    # Delete existing template for this week (soft delete)
    existing_template = await service.get_template_by_week(profile.id, week_number)
    if existing_template:
        existing_template.deleted_at = datetime.now()
        await db.commit()
    
    # Generate new template
    try:
        template = await service.generate_template(
            profile_id=profile.id,
            week_number=week_number,
            preferences=request.preferences
        )
    except ProfileLockedException:
        # Re-raise with proper error code
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile is locked. Unlock profile before making modifications."
        )
    
    # Transform template to response format
    # Group template meals by day
    days_data = {}
    for day in range(7):
        day_meals = [tm for tm in template.template_meals if tm.day_of_week == day]
        
        # Group by meal schedule
        meals_by_schedule = {}
        for tm in day_meals:
            schedule_id = tm.meal_schedule_id
            if schedule_id not in meals_by_schedule:
                meals_by_schedule[schedule_id] = {
                    'meal_schedule': tm.meal_schedule,
                    'primary': None,
                    'alternatives': []
                }
            
            if tm.is_primary:
                meals_by_schedule[schedule_id]['primary'] = tm.dish
            else:
                meals_by_schedule[schedule_id]['alternatives'].append(tm.dish)
        
        # Build meal slots
        meal_slots = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for schedule_data in meals_by_schedule.values():
            primary_dish = schedule_data['primary']
            if primary_dish:
                meal_slots.append({
                    'meal_name': schedule_data['meal_schedule'].meal_name,
                    'scheduled_time': schedule_data['meal_schedule'].scheduled_time,
                    'day_of_week': day,
                    'primary_dish': primary_dish,
                    'alternative_dishes': schedule_data['alternatives']
                })
                
                total_calories += float(primary_dish.calories)
                total_protein += float(primary_dish.protein_g)
                total_carbs += float(primary_dish.carbs_g)
                total_fats += float(primary_dish.fats_g)
        
        # Sort meals by scheduled time
        meal_slots.sort(key=lambda m: m['scheduled_time'])
        
        # Get day name
        today = date.today()
        day_offset = (day - today.weekday()) % 7
        target_date = today + timedelta(days=day_offset)
        day_name = target_date.strftime('%A')
        
        days_data[day] = {
            'day_of_week': day,
            'day_name': day_name,
            'meals': meal_slots,
            'total_calories': total_calories,
            'total_protein_g': total_protein,
            'total_carbs_g': total_carbs,
            'total_fats_g': total_fats
        }
    
    # Build response
    return MealTemplateResponse(
        id=template.id,
        week_number=template.week_number,
        is_active=template.is_active,
        days=[days_data[day] for day in range(7)],
        created_at=template.created_at,
        updated_at=template.updated_at
    )

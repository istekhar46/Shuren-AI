"""
Dish endpoints for searching and retrieving dish information.

This module provides REST API endpoints for:
- Searching dishes with various filters
- Getting detailed dish information with ingredients
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dish import DishResponse, DishSummaryResponse
from app.services.dish_service import DishService


router = APIRouter()


@router.get(
    "/search",
    response_model=List[DishSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Search dishes",
    responses={
        200: {
            "description": "Dishes retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Egg Omelette with Multigrain Toast",
                            "name_hindi": "अंडे का ऑमलेट",
                            "meal_type": "breakfast",
                            "cuisine_type": "north_indian",
                            "calories": 350,
                            "protein_g": 25,
                            "carbs_g": 30,
                            "fats_g": 15,
                            "prep_time_minutes": 5,
                            "cook_time_minutes": 10,
                            "total_time_minutes": 15,
                            "difficulty_level": "easy",
                            "is_vegetarian": True,
                            "is_vegan": False
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "limit must be between 1 and 100"
                    }
                }
            }
        }
    }
)
async def search_dishes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    meal_type: Annotated[
        str | None,
        Query(
            description="Filter by meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)"
        )
    ] = None,
    diet_type: Annotated[
        str | None,
        Query(
            description="Filter by diet type (vegetarian, vegan)"
        )
    ] = None,
    max_prep_time: Annotated[
        int | None,
        Query(
            ge=1,
            description="Maximum total preparation + cooking time in minutes"
        )
    ] = None,
    max_calories: Annotated[
        int | None,
        Query(
            ge=1,
            description="Maximum calories per serving"
        )
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of results to return (1-100)"
        )
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of results to skip for pagination"
        )
    ] = 0
) -> List[DishSummaryResponse]:
    """
    Search dishes with filters.
    
    Returns a paginated list of dishes matching the specified filters.
    Automatically applies the user's dietary preferences to exclude
    allergens from the results.
    
    The search supports:
    - Filtering by meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)
    - Filtering by diet type (vegetarian, vegan)
    - Maximum preparation time (prep + cook time)
    - Maximum calories per serving
    - Pagination with limit and offset
    
    Results are ordered by popularity score (most popular first).
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        meal_type: Optional meal type filter
        diet_type: Optional diet type filter
        max_prep_time: Optional maximum total time filter
        max_calories: Optional maximum calories filter
        limit: Maximum number of results (1-100, default 50)
        offset: Number of results to skip (default 0)
        
    Returns:
        List of DishSummaryResponse objects matching the filters
        
    Raises:
        HTTPException(400): If invalid parameters provided
        HTTPException(401): If authentication fails (handled by dependency)
    
    Example:
        GET /api/v1/dishes/search?meal_type=breakfast&diet_type=vegetarian&limit=10
        
        Response (200 OK):
        ```json
        [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Egg Omelette with Multigrain Toast",
                "meal_type": "breakfast",
                "calories": 350,
                "protein_g": 25,
                ...
            }
        ]
        ```
    """
    # Initialize dish service
    service = DishService(db)
    
    # Get user's dietary preferences to exclude allergens
    profile = current_user.profile
    exclude_allergens = []
    
    if profile and profile.dietary_preferences:
        # Get allergies from dietary preferences
        allergies = profile.dietary_preferences.allergies or []
        exclude_allergens = allergies
    
    # Search dishes with filters
    dishes = await service.search_dishes(
        meal_type=meal_type,
        diet_type=diet_type,
        max_prep_time=max_prep_time,
        max_calories=max_calories,
        exclude_allergens=exclude_allergens,
        limit=limit,
        offset=offset
    )
    
    # Return response (Pydantic will handle serialization)
    return [DishSummaryResponse.model_validate(dish) for dish in dishes]


@router.get(
    "/{dish_id}",
    response_model=DishResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dish details",
    responses={
        200: {
            "description": "Dish retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Egg Omelette with Multigrain Toast",
                        "name_hindi": "अंडे का ऑमलेट",
                        "description": "A protein-rich breakfast with eggs and whole grain bread",
                        "cuisine_type": "north_indian",
                        "meal_type": "breakfast",
                        "dish_category": "main_course",
                        "serving_size_g": 250,
                        "calories": 350,
                        "protein_g": 25,
                        "carbs_g": 30,
                        "fats_g": 15,
                        "fiber_g": 5,
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 10,
                        "total_time_minutes": 15,
                        "difficulty_level": "easy",
                        "is_vegetarian": True,
                        "is_vegan": False,
                        "is_gluten_free": False,
                        "is_dairy_free": True,
                        "is_nut_free": True,
                        "contains_allergens": ["eggs", "wheat"],
                        "is_active": True,
                        "popularity_score": 85,
                        "ingredients": [
                            {
                                "ingredient": {
                                    "id": "223e4567-e89b-12d3-a456-426614174001",
                                    "name": "eggs",
                                    "name_hindi": "अंडे",
                                    "category": "protein",
                                    "typical_unit": "piece",
                                    "is_allergen": True,
                                    "allergen_type": "eggs"
                                },
                                "quantity": 3,
                                "unit": "piece",
                                "preparation_note": "beaten",
                                "is_optional": False
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Dish not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Dish not found"
                    }
                }
            }
        }
    }
)
async def get_dish(
    dish_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> DishResponse:
    """
    Get detailed dish information with ingredients.
    
    Returns complete dish information including all nutritional data,
    preparation details, dietary tags, and the full ingredient list
    with quantities.
    
    This endpoint is useful for:
    - Viewing complete dish details before selection
    - Getting ingredient lists for meal preparation
    - Understanding nutritional breakdown
    - Checking allergen information
    
    Args:
        dish_id: UUID of the dish to retrieve
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        DishResponse with complete dish details and ingredients
        
    Raises:
        HTTPException(404): If dish not found
        HTTPException(401): If authentication fails (handled by dependency)
    
    Example:
        GET /api/v1/dishes/123e4567-e89b-12d3-a456-426614174000
        
        Response (200 OK):
        ```json
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Egg Omelette with Multigrain Toast",
            "calories": 350,
            "protein_g": 25,
            "ingredients": [
                {
                    "ingredient": {
                        "name": "eggs",
                        "category": "protein"
                    },
                    "quantity": 3,
                    "unit": "piece"
                }
            ]
        }
        ```
    """
    # Initialize dish service
    service = DishService(db)
    
    # Get dish with ingredients
    dish = await service.get_dish(dish_id, include_ingredients=True)
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found"
        )
    
    # Return response (Pydantic will handle serialization)
    return DishResponse.model_validate(dish)

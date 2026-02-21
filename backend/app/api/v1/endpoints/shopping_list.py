"""
Shopping list endpoints for generating ingredient lists from meal templates.

This module provides REST API endpoints for:
- Generating shopping lists from meal templates
- Aggregating ingredients by category
- Calculating quantities for multiple weeks
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.shopping_list import ShoppingListResponse
from app.services.shopping_list_service import ShoppingListService


router = APIRouter()


@router.get(
    "/",
    response_model=ShoppingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get shopping list",
    responses={
        200: {
            "description": "Shopping list generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "week_number": 1,
                        "start_date": "2026-01-31",
                        "end_date": "2026-02-06",
                        "categories": [
                            {
                                "category": "protein",
                                "ingredients": [
                                    {
                                        "ingredient_id": "123e4567-e89b-12d3-a456-426614174000",
                                        "name": "chicken_breast",
                                        "name_hindi": "चिकन ब्रेस्ट",
                                        "category": "protein",
                                        "total_quantity": 1400,
                                        "unit": "g",
                                        "is_optional": False,
                                        "used_in_dishes": ["Grilled Chicken Salad", "Chicken Tikka"]
                                    }
                                ]
                            },
                            {
                                "category": "vegetable",
                                "ingredients": [
                                    {
                                        "ingredient_id": "223e4567-e89b-12d3-a456-426614174001",
                                        "name": "tomato",
                                        "name_hindi": "टमाटर",
                                        "category": "vegetable",
                                        "total_quantity": 700,
                                        "unit": "g",
                                        "is_optional": False,
                                        "used_in_dishes": ["Chicken Tikka", "Mixed Vegetable Curry"]
                                    }
                                ]
                            }
                        ],
                        "total_items": 2
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid weeks parameter",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Weeks must be between 1 and 4"
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
async def get_shopping_list(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    weeks: Annotated[int, Query(ge=1, le=4, description="Number of weeks to generate shopping list for (1-4)")] = 1
) -> ShoppingListResponse:
    """
    Generate shopping list from user's meal template.
    
    Aggregates all ingredients from the user's active meal template and
    calculates total quantities needed for the specified number of weeks.
    Ingredients are organized by category for convenient shopping.
    
    The shopping list includes:
    - All ingredients from primary dishes in the meal template
    - Total quantities calculated for the specified number of weeks
    - Ingredients grouped by category (protein, vegetable, fruit, grain, dairy, spice, oil, other)
    - Information about which dishes use each ingredient
    - Optional ingredient markers
    
    The calculation is based on:
    - 7 days per week
    - Primary dishes only (alternatives are not included)
    - User's current active meal template (based on 4-week rotation)
    
    Args:
        weeks: Number of weeks to generate list for (1-4, default 1)
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        ShoppingListResponse with categorized ingredients and quantities
        
    Raises:
        HTTPException(400): If weeks parameter is invalid
        HTTPException(404): If no active meal template is found
        HTTPException(401): If authentication fails (handled by dependency)
    
    Example:
        Request:
        ```
        GET /api/v1/meals/shopping-list?weeks=2
        ```
        
        Response (200 OK):
        ```json
        {
            "week_number": 1,
            "start_date": "2026-01-31",
            "end_date": "2026-02-13",
            "categories": [
                {
                    "category": "protein",
                    "ingredients": [
                        {
                            "ingredient_id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "chicken_breast",
                            "name_hindi": "चिकन ब्रेस्ट",
                            "category": "protein",
                            "total_quantity": 2800,
                            "unit": "g",
                            "is_optional": false,
                            "used_in_dishes": ["Grilled Chicken Salad", "Chicken Tikka"]
                        }
                    ]
                }
            ],
            "total_items": 15
        }
        ```
    """
    # Initialize shopping list service
    service = ShoppingListService(db)
    profile = current_user.profile
    
    # Generate shopping list
    shopping_list = await service.generate_shopping_list(
        profile_id=profile.id,
        weeks=weeks
    )
    
    return shopping_list

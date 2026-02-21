"""Shopping list Pydantic schemas"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ShoppingListIngredient(BaseModel):
    """
    Schema for ingredient in shopping list.
    
    Represents an aggregated ingredient with total quantity needed
    and information about which dishes use it.
    """
    ingredient_id: UUID = Field(..., description="Unique identifier for the ingredient")
    name: str = Field(..., description="Ingredient name")
    name_hindi: Optional[str] = Field(None, description="Hindi name of the ingredient")
    category: str = Field(..., description="Ingredient category (vegetable, fruit, protein, grain, dairy, spice, oil, other)")
    total_quantity: Decimal = Field(..., description="Total quantity needed for the time period")
    unit: str = Field(..., description="Measurement unit (g, ml, piece, cup, tbsp, tsp)")
    is_optional: bool = Field(default=False, description="Whether this ingredient is optional in any dish")
    used_in_dishes: List[str] = Field(default_factory=list, description="List of dish names that use this ingredient")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredient_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "chicken_breast",
                "name_hindi": "चिकन ब्रेस्ट",
                "category": "protein",
                "total_quantity": 1400,
                "unit": "g",
                "is_optional": False,
                "used_in_dishes": ["Grilled Chicken Salad", "Chicken Tikka", "Chicken Stir Fry"]
            }
        }


class ShoppingListCategory(BaseModel):
    """
    Schema for shopping list category.
    
    Groups ingredients by their category for organized shopping.
    """
    category: str = Field(..., description="Category name (vegetable, fruit, protein, grain, dairy, spice, oil, other)")
    ingredients: List[ShoppingListIngredient] = Field(..., description="List of ingredients in this category")
    
    class Config:
        json_schema_extra = {
            "example": {
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
            }
        }


class ShoppingListResponse(BaseModel):
    """
    Schema for complete shopping list response.
    
    Provides a comprehensive shopping list with ingredients organized
    by category, covering the specified time period.
    """
    week_number: int = Field(..., description="Week number for this shopping list (1-4)")
    start_date: str = Field(..., description="Start date of the shopping period (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date of the shopping period (YYYY-MM-DD)")
    categories: List[ShoppingListCategory] = Field(..., description="Ingredients grouped by category")
    total_items: int = Field(..., description="Total number of unique ingredients in the list")
    
    class Config:
        json_schema_extra = {
            "example": {
                "week_number": 1,
                "start_date": "2026-02-01",
                "end_date": "2026-02-07",
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

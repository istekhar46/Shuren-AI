"""Meal template and related Pydantic schemas"""

from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.dish import DishSummaryResponse


# Response Schemas

class TemplateMealResponse(BaseModel):
    """
    Schema for template meal with dish assignment.
    
    Represents a specific dish assigned to a meal slot in the template,
    including whether it's the primary recommendation or an alternative.
    """
    id: UUID = Field(..., description="Unique identifier for this template meal")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    meal_name: str = Field(..., description="Meal name from schedule (e.g., 'Breakfast', 'Pre-workout')")
    scheduled_time: time = Field(..., description="Scheduled meal time")
    is_primary: bool = Field(..., description="Whether this is the primary recommendation")
    alternative_order: int = Field(..., ge=1, le=5, description="Order for alternative dishes (1-5)")
    dish: DishSummaryResponse = Field(..., description="Dish details")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "day_of_week": 0,
                "meal_name": "Breakfast",
                "scheduled_time": "08:00:00",
                "is_primary": True,
                "alternative_order": 1,
                "dish": {
                    "id": "223e4567-e89b-12d3-a456-426614174000",
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
                    "difficulty_level": "easy",
                    "is_vegetarian": True,
                    "is_vegan": False,
                    "total_time_minutes": 15
                }
            }
        }


class MealSlotResponse(BaseModel):
    """
    Schema for a meal slot with primary and alternative dishes.
    
    Groups a meal time with its primary dish recommendation and
    alternative options for user flexibility.
    """
    meal_name: str = Field(..., description="Meal name (e.g., 'Breakfast', 'Lunch')")
    scheduled_time: time = Field(..., description="Scheduled time for this meal")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    primary_dish: DishSummaryResponse = Field(..., description="Primary recommended dish")
    alternative_dishes: List[DishSummaryResponse] = Field(
        default_factory=list,
        description="Alternative dish options (typically 2-3 dishes)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "meal_name": "Breakfast",
                "scheduled_time": "08:00:00",
                "day_of_week": 0,
                "primary_dish": {
                    "id": "223e4567-e89b-12d3-a456-426614174000",
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
                    "difficulty_level": "easy",
                    "is_vegetarian": True,
                    "is_vegan": False,
                    "total_time_minutes": 15
                },
                "alternative_dishes": [
                    {
                        "id": "323e4567-e89b-12d3-a456-426614174000",
                        "name": "Poha with Peanuts",
                        "name_hindi": "पोहा",
                        "meal_type": "breakfast",
                        "cuisine_type": "north_indian",
                        "calories": 340,
                        "protein_g": 22,
                        "carbs_g": 32,
                        "fats_g": 14,
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 8,
                        "difficulty_level": "easy",
                        "is_vegetarian": True,
                        "is_vegan": True,
                        "total_time_minutes": 13
                    }
                ]
            }
        }


class DayMealsResponse(BaseModel):
    """
    Schema for all meals in a single day.
    
    Provides a complete view of a day's meal plan including
    all meal slots and daily nutritional totals.
    """
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    day_name: str = Field(..., description="Day name (Monday, Tuesday, etc.)")
    meals: List[MealSlotResponse] = Field(..., description="All meals for this day")
    total_calories: float = Field(..., description="Total calories for the day from primary dishes")
    total_protein_g: float = Field(..., description="Total protein for the day in grams")
    total_carbs_g: float = Field(..., description="Total carbohydrates for the day in grams")
    total_fats_g: float = Field(..., description="Total fats for the day in grams")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_of_week": 0,
                "day_name": "Monday",
                "meals": [
                    {
                        "meal_name": "Breakfast",
                        "scheduled_time": "08:00:00",
                        "day_of_week": 0,
                        "primary_dish": {
                            "id": "223e4567-e89b-12d3-a456-426614174000",
                            "name": "Egg Omelette with Multigrain Toast",
                            "meal_type": "breakfast",
                            "calories": 350,
                            "protein_g": 25,
                            "carbs_g": 30,
                            "fats_g": 15
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


class MealTemplateResponse(BaseModel):
    """
    Schema for complete meal template.
    
    Represents a full week's meal plan with all days and meals,
    including metadata about the template.
    """
    id: UUID = Field(..., description="Unique identifier for this template")
    week_number: int = Field(..., ge=1, le=4, description="Week number in 4-week rotation (1-4)")
    is_active: bool = Field(..., description="Whether this is the currently active template")
    days: List[DayMealsResponse] = Field(..., description="Meals for each day of the week (7 days)")
    created_at: datetime = Field(..., description="Timestamp when the template was created")
    updated_at: datetime = Field(..., description="Timestamp of last modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
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


class TodayMealsResponse(BaseModel):
    """
    Schema for today's meals with dish recommendations.
    
    Provides a focused view of today's meal plan with all
    scheduled meals and daily nutritional totals.
    """
    date: str = Field(..., description="Today's date in ISO format (YYYY-MM-DD)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    day_name: str = Field(..., description="Day name (Monday, Tuesday, etc.)")
    meals: List[MealSlotResponse] = Field(..., description="Today's meals with dish options")
    total_calories: float = Field(..., description="Total calories for today from primary dishes")
    total_protein_g: float = Field(..., description="Total protein for today in grams")
    total_carbs_g: float = Field(..., description="Total carbohydrates for today in grams")
    total_fats_g: float = Field(..., description="Total fats for today in grams")
    
    class Config:
        json_schema_extra = {
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


class NextMealResponse(BaseModel):
    """
    Schema for next upcoming meal.
    
    Provides information about the next scheduled meal including
    time until the meal and dish options.
    """
    meal_name: str = Field(..., description="Meal name (e.g., 'Lunch', 'Pre-workout')")
    scheduled_time: time = Field(..., description="Scheduled time for this meal")
    time_until_meal_minutes: int = Field(..., description="Minutes until meal time")
    primary_dish: DishSummaryResponse = Field(..., description="Primary recommended dish")
    alternative_dishes: List[DishSummaryResponse] = Field(
        default_factory=list,
        description="Alternative dish options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "meal_name": "Lunch",
                "scheduled_time": "13:00:00",
                "time_until_meal_minutes": 45,
                "primary_dish": {
                    "id": "423e4567-e89b-12d3-a456-426614174000",
                    "name": "Grilled Chicken with Brown Rice",
                    "name_hindi": "ग्रिल्ड चिकन",
                    "meal_type": "lunch",
                    "cuisine_type": "continental",
                    "calories": 550,
                    "protein_g": 45,
                    "carbs_g": 60,
                    "fats_g": 12,
                    "prep_time_minutes": 10,
                    "cook_time_minutes": 20,
                    "difficulty_level": "medium",
                    "is_vegetarian": False,
                    "is_vegan": False,
                    "total_time_minutes": 30
                },
                "alternative_dishes": []
            }
        }


# Request Schemas

class TemplateRegenerateRequest(BaseModel):
    """
    Schema for template regeneration request.
    
    Allows users to request a new meal template with optional
    preferences for customization.
    """
    preferences: Optional[str] = Field(
        None,
        description="User preferences for generation (e.g., 'More chicken dishes, less spicy food')",
        max_length=500
    )
    week_number: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="Specific week to regenerate (1-4). If not provided, regenerates current week"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferences": "More chicken dishes, less spicy food, quick prep meals only",
                "week_number": 1
            }
        }


class DishSwapRequest(BaseModel):
    """
    Schema for swapping a dish in the template.
    
    Allows users to replace a specific dish in their meal template
    with a different dish.
    """
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of week to swap (0=Monday, 6=Sunday)"
    )
    meal_name: str = Field(
        ...,
        description="Meal name to swap (e.g., 'Breakfast', 'Lunch')",
        min_length=1,
        max_length=100
    )
    new_dish_id: UUID = Field(
        ...,
        description="ID of the new dish to use"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_of_week": 0,
                "meal_name": "Breakfast",
                "new_dish_id": "523e4567-e89b-12d3-a456-426614174000"
            }
        }

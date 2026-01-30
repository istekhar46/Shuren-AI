"""Meal plan and schedule Pydantic schemas"""

from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Response Schemas

class MealPlanResponse(BaseModel):
    """
    Schema for meal plan response.
    
    Contains complete nutritional targets including calories, macronutrients,
    and meal frequency. This is the primary data structure for meal management.
    """
    id: UUID = Field(..., description="Unique identifier for this meal plan")
    meals_per_day: int = Field(..., description="Number of meals per day (2-8)")
    daily_calories_target: int = Field(..., description="Target daily calorie intake")
    daily_calories_min: int = Field(..., description="Minimum acceptable daily calories")
    daily_calories_max: int = Field(..., description="Maximum acceptable daily calories")
    protein_grams_target: Decimal = Field(..., description="Target daily protein in grams")
    carbs_grams_target: Decimal = Field(..., description="Target daily carbohydrates in grams")
    fats_grams_target: Decimal = Field(..., description="Target daily fats in grams")
    protein_percentage: Decimal = Field(..., description="Protein as percentage of total calories")
    carbs_percentage: Decimal = Field(..., description="Carbs as percentage of total calories")
    fats_percentage: Decimal = Field(..., description="Fats as percentage of total calories")
    plan_rationale: Optional[str] = Field(None, description="AI-generated explanation of why this plan suits the user")
    is_locked: bool = Field(..., description="Whether the plan is locked (requires unlock to modify)")
    created_at: datetime = Field(..., description="Timestamp when the plan was created")
    updated_at: datetime = Field(..., description="Timestamp of last modification")
    
    class Config:
        from_attributes = True


class MealScheduleItemResponse(BaseModel):
    """
    Schema for individual meal schedule item.
    
    Represents a single meal's timing and notification preferences within
    the daily meal schedule.
    """
    id: UUID = Field(..., description="Unique identifier for this meal schedule item")
    meal_number: int = Field(..., description="Meal number in the day (1-based)")
    meal_name: str = Field(..., description="Name of the meal (e.g., 'Breakfast', 'Lunch', 'Dinner')")
    scheduled_time: time = Field(..., description="Scheduled time for this meal (HH:MM:SS)")
    notification_offset_minutes: int = Field(..., description="Minutes before meal to send notification (-120 to 0)")
    earliest_time: Optional[time] = Field(None, description="Earliest acceptable time for this meal")
    latest_time: Optional[time] = Field(None, description="Latest acceptable time for this meal")
    is_active: bool = Field(..., description="Whether this meal is currently active in the schedule")
    
    class Config:
        from_attributes = True


class MealScheduleResponse(BaseModel):
    """
    Schema for complete meal schedule.
    
    Contains all meal timing information for the user's daily schedule.
    """
    meals: List[MealScheduleItemResponse] = Field(..., description="List of all scheduled meals for the day")


# Update Schemas

class MealPlanUpdate(BaseModel):
    """
    Schema for updating meal plan.
    
    All fields are optional to support partial updates. Profile must be
    unlocked before modifications are allowed. Macro percentages are
    automatically calculated from gram targets.
    """
    meals_per_day: Optional[int] = Field(None, ge=2, le=8, description="Number of meals per day (2-8)")
    daily_calories_target: Optional[int] = Field(None, ge=1000, le=5000, description="Target daily calories (1000-5000)")
    daily_calories_min: Optional[int] = Field(None, ge=1000, le=5000, description="Minimum daily calories (1000-5000)")
    daily_calories_max: Optional[int] = Field(None, ge=1000, le=5000, description="Maximum daily calories (1000-5000)")
    protein_grams_target: Optional[Decimal] = Field(None, gt=0, description="Target daily protein in grams (must be positive)")
    carbs_grams_target: Optional[Decimal] = Field(None, gt=0, description="Target daily carbs in grams (must be positive)")
    fats_grams_target: Optional[Decimal] = Field(None, gt=0, description="Target daily fats in grams (must be positive)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "daily_calories_target": 2800,
                "protein_grams_target": 200.0,
                "carbs_grams_target": 300.0,
                "fats_grams_target": 80.0
            }
        }


class MealScheduleItemUpdate(BaseModel):
    """
    Schema for updating individual meal schedule item.
    
    All fields except meal_number are optional to support partial updates.
    Profile must be unlocked before modifications are allowed.
    """
    meal_number: int = Field(..., ge=1, le=10, description="Meal number to update (1-10)")
    meal_name: Optional[str] = Field(None, description="New name for the meal")
    scheduled_time: Optional[time] = Field(None, description="New scheduled time (HH:MM:SS format)")
    notification_offset_minutes: Optional[int] = Field(None, ge=-120, le=0, description="Minutes before meal for notification (-120 to 0)")
    earliest_time: Optional[time] = Field(None, description="Earliest acceptable time for flexibility")
    latest_time: Optional[time] = Field(None, description="Latest acceptable time for flexibility")
    is_active: Optional[bool] = Field(None, description="Whether to activate or deactivate this meal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "meal_number": 1,
                "meal_name": "Breakfast",
                "scheduled_time": "08:00:00",
                "notification_offset_minutes": -15,
                "is_active": True
            }
        }


class MealScheduleUpdate(BaseModel):
    """
    Schema for updating meal schedule.
    
    Contains a list of meal schedule items to update. Profile must be
    unlocked before modifications are allowed.
    """
    meals: List[MealScheduleItemUpdate] = Field(..., description="List of meal schedule items to update")
    
    class Config:
        json_schema_extra = {
            "example": {
                "meals": [
                    {
                        "meal_number": 1,
                        "scheduled_time": "08:00:00",
                        "is_active": True
                    },
                    {
                        "meal_number": 2,
                        "scheduled_time": "12:00:00",
                        "is_active": True
                    }
                ]
            }
        }

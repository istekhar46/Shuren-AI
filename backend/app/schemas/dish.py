"""Dish and ingredient Pydantic schemas"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator





class DishBase(BaseModel):
    """Base schema for dish properties."""
    name: str = Field(..., description="Dish name")
    name_hindi: Optional[str] = Field(None, description="Hindi name of the dish")
    description: Optional[str] = Field(None, description="Dish description")
    meal_type: str = Field(..., description="Meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)")
    cuisine_type: str = Field(..., description="Cuisine type (north_indian, south_indian, continental, fusion)")


class DishResponse(DishBase):
    """
    Schema for dish response with complete details.
    
    Contains all dish information including nutritional data,
    preparation details, dietary tags, and optional ingredient list.
    """
    id: UUID = Field(..., description="Unique identifier for this dish")
    dish_category: Optional[str] = Field(None, description="Dish category (main_course, side_dish, beverage, dessert)")
    
    # Nutritional information (per serving)
    serving_size_g: float = Field(..., description="Serving size in grams")
    calories: float = Field(..., description="Calories per serving")
    protein_g: float = Field(..., description="Protein in grams per serving")
    carbs_g: float = Field(..., description="Carbohydrates in grams per serving")
    fats_g: float = Field(..., description="Fats in grams per serving")
    fiber_g: Optional[float] = Field(None, description="Fiber in grams per serving")
    
    # Preparation details
    prep_time_minutes: int = Field(..., description="Preparation time in minutes")
    cook_time_minutes: int = Field(..., description="Cooking time in minutes")
    difficulty_level: str = Field(..., description="Difficulty level (easy, medium, hard)")
    
    # Dietary tags
    is_vegetarian: bool = Field(..., description="Whether the dish is vegetarian")
    is_vegan: bool = Field(..., description="Whether the dish is vegan")
    is_gluten_free: bool = Field(..., description="Whether the dish is gluten-free")
    is_dairy_free: bool = Field(..., description="Whether the dish is dairy-free")
    is_nut_free: bool = Field(..., description="Whether the dish is nut-free")
    
    # Allergen information
    contains_allergens: List[str] = Field(default_factory=list, description="List of allergens present in the dish")
    
    # Metadata
    is_active: bool = Field(..., description="Whether this dish is currently active")
    popularity_score: int = Field(..., description="Popularity score for ranking")
    created_at: datetime = Field(..., description="Timestamp when the dish was created")
    updated_at: datetime = Field(..., description="Timestamp of last modification")
    
    @computed_field
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time from prep and cook time."""
        return self.prep_time_minutes + self.cook_time_minutes
    
    class Config:
        from_attributes = True
        populate_by_name = True


class DishSummaryResponse(BaseModel):
    """
    Schema for dish summary without ingredients.
    
    Provides essential dish information for list views and
    quick references without the overhead of ingredient details.
    """
    id: UUID = Field(..., description="Unique identifier for this dish")
    name: str = Field(..., description="Dish name")
    name_hindi: Optional[str] = Field(None, description="Hindi name of the dish")
    meal_type: str = Field(..., description="Meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)")
    cuisine_type: str = Field(..., description="Cuisine type (north_indian, south_indian, continental, fusion)")
    
    # Nutritional information
    calories: float = Field(..., description="Calories per serving")
    protein_g: float = Field(..., description="Protein in grams per serving")
    carbs_g: float = Field(..., description="Carbohydrates in grams per serving")
    fats_g: float = Field(..., description="Fats in grams per serving")
    
    # Preparation details
    prep_time_minutes: int = Field(..., description="Preparation time in minutes")
    cook_time_minutes: int = Field(..., description="Cooking time in minutes")
    difficulty_level: str = Field(..., description="Difficulty level (easy, medium, hard)")
    
    # Dietary tags
    is_vegetarian: bool = Field(..., description="Whether the dish is vegetarian")
    is_vegan: bool = Field(..., description="Whether the dish is vegan")
    
    @computed_field
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time from prep and cook time."""
        return self.prep_time_minutes + self.cook_time_minutes
    
    class Config:
        from_attributes = True

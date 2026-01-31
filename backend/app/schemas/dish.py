"""Dish and ingredient Pydantic schemas"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


# Base Schemas

class IngredientBase(BaseModel):
    """
    Base schema for ingredient information.
    
    Contains core ingredient identification fields.
    """
    name: str = Field(..., description="Ingredient name")
    name_hindi: Optional[str] = Field(None, description="Hindi name of the ingredient")
    category: str = Field(..., description="Ingredient category (vegetable, fruit, protein, grain, dairy, spice, oil, other)")


class DishBase(BaseModel):
    """
    Base schema for dish information.
    
    Contains core dish identification and classification fields.
    """
    name: str = Field(..., description="Dish name")
    name_hindi: Optional[str] = Field(None, description="Hindi name of the dish")
    description: Optional[str] = Field(None, description="Brief description of the dish")
    cuisine_type: str = Field(..., description="Cuisine type (north_indian, south_indian, continental, fusion)")
    meal_type: str = Field(..., description="Meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)")


# Response Schemas

class IngredientResponse(IngredientBase):
    """
    Schema for ingredient response with complete details.
    
    Includes all ingredient information including nutritional data
    and allergen information.
    """
    id: UUID = Field(..., description="Unique identifier for this ingredient")
    typical_unit: str = Field(..., description="Typical measurement unit (g, ml, piece, cup, tbsp, tsp)")
    calories_per_100g: Optional[Decimal] = Field(None, description="Calories per 100g")
    protein_per_100g: Optional[Decimal] = Field(None, description="Protein per 100g in grams")
    carbs_per_100g: Optional[Decimal] = Field(None, description="Carbohydrates per 100g in grams")
    fats_per_100g: Optional[Decimal] = Field(None, description="Fats per 100g in grams")
    is_allergen: bool = Field(..., description="Whether this ingredient is an allergen")
    allergen_type: Optional[str] = Field(None, description="Type of allergen if applicable (peanuts, tree_nuts, dairy, eggs, soy, wheat, fish, shellfish)")
    is_active: bool = Field(..., description="Whether this ingredient is currently active")
    created_at: datetime = Field(..., description="Timestamp when the ingredient was created")
    updated_at: datetime = Field(..., description="Timestamp of last modification")
    
    class Config:
        from_attributes = True


class DishIngredientResponse(BaseModel):
    """
    Schema for dish ingredient with quantity information.
    
    Represents an ingredient used in a dish with its specific
    quantity and preparation notes.
    """
    ingredient: IngredientResponse = Field(..., description="Complete ingredient details")
    quantity: Decimal = Field(..., description="Quantity required for this dish")
    unit: str = Field(..., description="Measurement unit (g, ml, piece, cup, tbsp, tsp)")
    preparation_note: Optional[str] = Field(None, description="Preparation instructions (e.g., 'finely chopped', 'soaked overnight')")
    is_optional: bool = Field(..., description="Whether this ingredient is optional")
    
    class Config:
        from_attributes = True


class DishResponse(DishBase):
    """
    Schema for dish response with complete details.
    
    Contains all dish information including nutritional data,
    preparation details, dietary tags, and optional ingredient list.
    """
    id: UUID = Field(..., description="Unique identifier for this dish")
    dish_category: Optional[str] = Field(None, description="Dish category (main_course, side_dish, beverage, dessert)")
    
    # Nutritional information (per serving)
    serving_size_g: Decimal = Field(..., description="Serving size in grams")
    calories: Decimal = Field(..., description="Calories per serving")
    protein_g: Decimal = Field(..., description="Protein in grams per serving")
    carbs_g: Decimal = Field(..., description="Carbohydrates in grams per serving")
    fats_g: Decimal = Field(..., description="Fats in grams per serving")
    fiber_g: Optional[Decimal] = Field(None, description="Fiber in grams per serving")
    
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
    
    # Ingredients (optional, loaded on demand)
    ingredients: Optional[List[DishIngredientResponse]] = Field(None, description="List of ingredients with quantities (loaded on demand)")
    
    @computed_field
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time from prep and cook time."""
        return self.prep_time_minutes + self.cook_time_minutes
    
    class Config:
        from_attributes = True


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
    calories: Decimal = Field(..., description="Calories per serving")
    protein_g: Decimal = Field(..., description="Protein in grams per serving")
    carbs_g: Decimal = Field(..., description="Carbohydrates in grams per serving")
    fats_g: Decimal = Field(..., description="Fats in grams per serving")
    
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

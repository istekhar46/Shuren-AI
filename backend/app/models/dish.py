"""Dish, Ingredient, and DishIngredient models for meal management.

Note: The Dish.template_meals relationship is commented out until the TemplateMeal
model is created in Task 2.3. It will be uncommented at that time.
"""

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Dish(BaseModel):
    """Dish entity representing a specific food item with nutritional info."""
    
    __tablename__ = "dishes"
    
    # Basic information
    name = Column(String(200), nullable=False)
    name_hindi = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Classification
    cuisine_type = Column(String(50), nullable=False)
    meal_type = Column(String(50), nullable=False)
    dish_category = Column(String(50), nullable=True)
    
    # Nutritional information (per serving)
    serving_size_g = Column(Numeric(6, 2), nullable=False)
    calories = Column(Numeric(6, 2), nullable=False)
    protein_g = Column(Numeric(5, 2), nullable=False)
    carbs_g = Column(Numeric(5, 2), nullable=False)
    fats_g = Column(Numeric(5, 2), nullable=False)
    fiber_g = Column(Numeric(4, 2), nullable=True)
    
    # Preparation details
    prep_time_minutes = Column(Integer, nullable=False)
    cook_time_minutes = Column(Integer, nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    
    # Dietary tags
    is_vegetarian = Column(Boolean, default=False, nullable=False)
    is_vegan = Column(Boolean, default=False, nullable=False)
    is_gluten_free = Column(Boolean, default=False, nullable=False)
    is_dairy_free = Column(Boolean, default=False, nullable=False)
    is_nut_free = Column(Boolean, default=False, nullable=False)
    
    # Allergen information
    contains_allergens = Column(ARRAY(Text), default=list, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    popularity_score = Column(Integer, default=0, nullable=False)
    
    # Relationships
    dish_ingredients = relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan"
    )
    
    template_meals = relationship(
        "TemplateMeal",
        back_populates="dish"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('calories > 0 AND calories < 2000', name='valid_calories'),
        CheckConstraint('protein_g >= 0 AND carbs_g >= 0 AND fats_g >= 0', name='valid_macros'),
        CheckConstraint('prep_time_minutes >= 0 AND prep_time_minutes <= 180', name='valid_prep_time'),
        CheckConstraint('cook_time_minutes >= 0 AND cook_time_minutes <= 240', name='valid_cook_time'),
        CheckConstraint(
            "difficulty_level IN ('easy', 'medium', 'hard')",
            name='valid_difficulty'
        ),
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout')",
            name='valid_meal_type'
        ),
        Index('idx_dishes_meal_type', 'meal_type', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
        Index('idx_dishes_dietary', 'is_vegetarian', 'is_vegan', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
        Index('idx_dishes_cuisine', 'cuisine_type', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
        Index('idx_dishes_nutrition', 'calories', 'protein_g', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
    )


class Ingredient(BaseModel):
    """Ingredient entity representing a food component."""
    
    __tablename__ = "ingredients"
    
    # Basic information
    name = Column(String(200), nullable=False, unique=True)
    name_hindi = Column(String(200), nullable=True)
    
    # Classification
    category = Column(String(50), nullable=False)
    
    # Nutritional information (per 100g)
    calories_per_100g = Column(Numeric(6, 2), nullable=True)
    protein_per_100g = Column(Numeric(5, 2), nullable=True)
    carbs_per_100g = Column(Numeric(5, 2), nullable=True)
    fats_per_100g = Column(Numeric(5, 2), nullable=True)
    
    # Measurement
    typical_unit = Column(String(20), nullable=False)
    
    # Allergen tags
    is_allergen = Column(Boolean, default=False, nullable=False)
    allergen_type = Column(String(50), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    dish_ingredients = relationship(
        "DishIngredient",
        back_populates="ingredient"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "category IN ('vegetable', 'fruit', 'protein', 'grain', 'dairy', 'spice', 'oil', 'other')",
            name='valid_category'
        ),
        Index('idx_ingredients_category', 'category', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
        Index('idx_ingredients_allergen', 'is_allergen', 'allergen_type', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
    )


class DishIngredient(BaseModel):
    """Junction table linking dishes to ingredients with quantities."""
    
    __tablename__ = "dish_ingredients"
    
    # Foreign keys
    dish_id = Column(UUID(as_uuid=True), ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    
    # Quantity information
    quantity = Column(Numeric(8, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Optional notes
    preparation_note = Column(String(200), nullable=True)
    
    # Metadata
    is_optional = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    dish = relationship("Dish", back_populates="dish_ingredients")
    ingredient = relationship("Ingredient", back_populates="dish_ingredients")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='valid_quantity'),
        UniqueConstraint('dish_id', 'ingredient_id', name='unique_dish_ingredient'),
        Index('idx_dish_ingredients_dish', 'dish_id'),
        Index('idx_dish_ingredients_ingredient', 'ingredient_id'),
    )

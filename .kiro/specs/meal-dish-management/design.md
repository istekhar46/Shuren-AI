# Meal Dish Management - Design Document

**Feature Name:** meal-dish-management  
**Created:** January 30, 2026  
**Status:** Draft  
**Version:** 1.0

---

## 1. Design Overview

### 1.1 Purpose
This document provides the technical design for implementing concrete dish recommendations within the existing meal plan system. It extends the abstract nutritional framework with specific, culturally-appropriate meal suggestions.

### 1.2 Design Principles
- **Extend, Don't Replace**: Build on existing meal_plans and meal_schedules
- **Maintain Consistency**: Respect profile locking and versioning mechanisms
- **Cultural Relevance**: Focus on Indian cuisine with regional variations
- **Flexibility Within Structure**: Provide alternatives while maintaining nutritional balance
- **Performance First**: Optimize for < 100ms query response times

### 1.3 Architecture Approach
- **Database-Driven**: Dish library stored in PostgreSQL with proper indexing
- **Template-Based**: Pre-generated weekly templates for fast retrieval
- **AI-Assisted**: Template generation uses AI for personalization
- **Cache-Friendly**: Templates cached in Redis with 24h TTL

---

## 2. Database Schema Design

### 2.1 Entity Relationship Diagram

```
┌─────────────────┐
│  user_profiles  │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────┐    ┌──────────────┐   ┌──────────────┐
│ meal_plans  │    │meal_schedules│   │dietary_prefs │
└──────┬──────┘    └──────┬───────┘   └──────────────┘
       │                  │
       │                  │
       │           ┌──────┴───────┐
       │           │              │
       ▼           ▼              ▼
┌─────────────┐  ┌──────────────────┐
│meal_templates│  │ template_meals   │
└──────┬──────┘  └────────┬─────────┘
       │                  │
       │                  │
       └──────────┬───────┘
                  │
                  ▼
           ┌─────────────┐
           │   dishes    │
           └──────┬──────┘
                  │
                  ▼
        ┌──────────────────┐
        │ dish_ingredients │
        └────────┬─────────┘
                 │
                 ▼
          ┌─────────────┐
          │ ingredients │
          └─────────────┘
```


### 2.2 Table Specifications

#### 2.2.1 dishes

**Purpose:** Master dish library with nutritional information

```sql
CREATE TABLE dishes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic information
    name VARCHAR(200) NOT NULL,
    name_hindi VARCHAR(200),
    description TEXT,
    
    -- Classification
    cuisine_type VARCHAR(50) NOT NULL,
        -- 'north_indian', 'south_indian', 'continental', 'fusion'
    meal_type VARCHAR(50) NOT NULL,
        -- 'breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'
    dish_category VARCHAR(50),
        -- 'main_course', 'side_dish', 'beverage', 'dessert'
    
    -- Nutritional information (per serving)
    serving_size_g DECIMAL(6,2) NOT NULL,
    calories DECIMAL(6,2) NOT NULL,
    protein_g DECIMAL(5,2) NOT NULL,
    carbs_g DECIMAL(5,2) NOT NULL,
    fats_g DECIMAL(5,2) NOT NULL,
    fiber_g DECIMAL(4,2),
    
    -- Preparation details
    prep_time_minutes INTEGER NOT NULL,
    cook_time_minutes INTEGER NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
        -- 'easy', 'medium', 'hard'
    
    -- Dietary tags
    is_vegetarian BOOLEAN DEFAULT FALSE NOT NULL,
    is_vegan BOOLEAN DEFAULT FALSE NOT NULL,
    is_gluten_free BOOLEAN DEFAULT FALSE NOT NULL,
    is_dairy_free BOOLEAN DEFAULT FALSE NOT NULL,
    is_nut_free BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Allergen information
    contains_allergens TEXT[],
        -- ['peanuts', 'tree_nuts', 'dairy', 'eggs', 'soy', 'wheat', 'fish', 'shellfish']
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    popularity_score INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_calories CHECK (calories > 0 AND calories < 2000),
    CONSTRAINT valid_macros CHECK (
        protein_g >= 0 AND carbs_g >= 0 AND fats_g >= 0
    ),
    CONSTRAINT valid_prep_time CHECK (
        prep_time_minutes >= 0 AND prep_time_minutes <= 180
    ),
    CONSTRAINT valid_cook_time CHECK (
        cook_time_minutes >= 0 AND cook_time_minutes <= 240
    ),
    CONSTRAINT valid_difficulty CHECK (
        difficulty_level IN ('easy', 'medium', 'hard')
    ),
    CONSTRAINT valid_meal_type CHECK (
        meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 
                     'pre_workout', 'post_workout')
    )
);

-- Indexes for performance
CREATE INDEX idx_dishes_meal_type ON dishes(meal_type) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_dishes_dietary ON dishes(is_vegetarian, is_vegan) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_dishes_cuisine ON dishes(cuisine_type) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_dishes_nutrition ON dishes(calories, protein_g) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_dishes_allergens ON dishes USING GIN (contains_allergens) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
```


#### 2.2.2 ingredients

**Purpose:** Master ingredient list for dish composition

```sql
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic information
    name VARCHAR(200) NOT NULL UNIQUE,
    name_hindi VARCHAR(200),
    
    -- Classification
    category VARCHAR(50) NOT NULL,
        -- 'vegetable', 'fruit', 'protein', 'grain', 'dairy', 'spice', 'oil', 'other'
    
    -- Nutritional information (per 100g)
    calories_per_100g DECIMAL(6,2),
    protein_per_100g DECIMAL(5,2),
    carbs_per_100g DECIMAL(5,2),
    fats_per_100g DECIMAL(5,2),
    
    -- Measurement
    typical_unit VARCHAR(20) NOT NULL,
        -- 'g', 'ml', 'piece', 'cup', 'tbsp', 'tsp'
    
    -- Allergen tags
    is_allergen BOOLEAN DEFAULT FALSE NOT NULL,
    allergen_type VARCHAR(50),
        -- 'peanuts', 'tree_nuts', 'dairy', 'eggs', 'soy', 'wheat', 'fish', 'shellfish'
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_category CHECK (
        category IN ('vegetable', 'fruit', 'protein', 'grain', 
                    'dairy', 'spice', 'oil', 'other')
    )
);

CREATE INDEX idx_ingredients_category ON ingredients(category) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_ingredients_allergen ON ingredients(is_allergen, allergen_type) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
```


#### 2.2.3 dish_ingredients

**Purpose:** Junction table linking dishes to ingredients with quantities

```sql
CREATE TABLE dish_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    dish_id UUID NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
    
    -- Quantity information
    quantity DECIMAL(8,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
        -- 'g', 'ml', 'piece', 'cup', 'tbsp', 'tsp'
    
    -- Optional notes
    preparation_note VARCHAR(200),
        -- e.g., "finely chopped", "soaked overnight"
    
    -- Metadata
    is_optional BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_quantity CHECK (quantity > 0),
    CONSTRAINT unique_dish_ingredient UNIQUE(dish_id, ingredient_id)
);

CREATE INDEX idx_dish_ingredients_dish ON dish_ingredients(dish_id);
CREATE INDEX idx_dish_ingredients_ingredient ON dish_ingredients(ingredient_id);
```


#### 2.2.4 meal_templates

**Purpose:** User's weekly meal template (4-week rotation)

```sql
CREATE TABLE meal_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to profile
    profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Template identification
    week_number INTEGER NOT NULL,
        -- 1, 2, 3, or 4 (for 4-week rotation)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Generation metadata
    generated_by VARCHAR(50) NOT NULL DEFAULT 'system',
        -- 'system', 'ai_agent', 'user'
    generation_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_week_number CHECK (week_number BETWEEN 1 AND 4),
    CONSTRAINT unique_profile_week UNIQUE(profile_id, week_number)
);

CREATE INDEX idx_meal_templates_profile ON meal_templates(profile_id) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_meal_templates_active ON meal_templates(profile_id, is_active) 
    WHERE deleted_at IS NULL AND is_active = TRUE;
```


#### 2.2.5 template_meals

**Purpose:** Specific dish assignments for each meal slot in the template

```sql
CREATE TABLE template_meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    template_id UUID NOT NULL REFERENCES meal_templates(id) ON DELETE CASCADE,
    meal_schedule_id UUID NOT NULL REFERENCES meal_schedules(id) ON DELETE CASCADE,
    dish_id UUID NOT NULL REFERENCES dishes(id) ON DELETE RESTRICT,
    
    -- Meal slot identification
    day_of_week INTEGER NOT NULL,
        -- 0=Monday, 6=Sunday
    
    -- Dish role
    is_primary BOOLEAN DEFAULT TRUE NOT NULL,
        -- TRUE = primary recommendation, FALSE = alternative option
    alternative_order INTEGER DEFAULT 1,
        -- For alternatives: 1, 2, 3 (display order)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT valid_alternative_order CHECK (alternative_order BETWEEN 1 AND 5)
);

CREATE INDEX idx_template_meals_template ON template_meals(template_id);
CREATE INDEX idx_template_meals_schedule ON template_meals(meal_schedule_id);
CREATE INDEX idx_template_meals_dish ON template_meals(dish_id);
CREATE INDEX idx_template_meals_day ON template_meals(template_id, day_of_week);
CREATE INDEX idx_template_meals_primary ON template_meals(template_id, is_primary) 
    WHERE is_primary = TRUE;
```

---

## 3. Data Models (SQLAlchemy)

### 3.1 Dish Model

```python
# backend/app/models/dish.py
from sqlalchemy import Boolean, CheckConstraint, Column, Index, Integer, Numeric, String, Text
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
```


### 3.2 Ingredient Model

```python
# backend/app/models/dish.py (continued)

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
```


### 3.3 Meal Template Models

```python
# backend/app/models/meal_template.py

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class MealTemplate(BaseModel):
    """Meal template entity representing a weekly meal plan."""
    
    __tablename__ = "meal_templates"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Template identification
    week_number = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Generation metadata
    generated_by = Column(String(50), default='system', nullable=False)
    generation_reason = Column(Text, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_templates")
    template_meals = relationship(
        "TemplateMeal",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('week_number BETWEEN 1 AND 4', name='valid_week_number'),
        UniqueConstraint('profile_id', 'week_number', name='unique_profile_week'),
        Index('idx_meal_templates_profile', 'profile_id', postgresql_where=(
            Column('deleted_at').is_(None)
        )),
        Index('idx_meal_templates_active', 'profile_id', 'is_active', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
    )


class TemplateMeal(BaseModel):
    """Template meal entity linking meal slots to specific dishes."""
    
    __tablename__ = "template_meals"
    
    # Foreign keys
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_templates.id", ondelete="CASCADE"),
        nullable=False
    )
    meal_schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_schedules.id", ondelete="CASCADE"),
        nullable=False
    )
    dish_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dishes.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Meal slot identification
    day_of_week = Column(Integer, nullable=False)
    
    # Dish role
    is_primary = Column(Boolean, default=True, nullable=False)
    alternative_order = Column(Integer, default=1, nullable=False)
    
    # Relationships
    template = relationship("MealTemplate", back_populates="template_meals")
    meal_schedule = relationship("MealSchedule")
    dish = relationship("Dish", back_populates="template_meals")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('day_of_week BETWEEN 0 AND 6', name='valid_day_of_week'),
        CheckConstraint('alternative_order BETWEEN 1 AND 5', name='valid_alternative_order'),
        Index('idx_template_meals_template', 'template_id'),
        Index('idx_template_meals_schedule', 'meal_schedule_id'),
        Index('idx_template_meals_dish', 'dish_id'),
        Index('idx_template_meals_day', 'template_id', 'day_of_week'),
        Index('idx_template_meals_primary', 'template_id', 'is_primary', postgresql_where=(
            Column('is_primary') == True
        )),
    )
```


### 3.4 Update UserProfile Model

```python
# backend/app/models/profile.py (add to existing relationships)

# Add to UserProfile class:
meal_templates = relationship(
    "MealTemplate",
    back_populates="profile",
    cascade="all, delete-orphan"
)
```

---

## 4. Pydantic Schemas

### 4.1 Dish Schemas

```python
# backend/app/schemas/dish.py

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IngredientBase(BaseModel):
    """Base schema for ingredient information."""
    name: str = Field(..., description="Ingredient name")
    name_hindi: Optional[str] = Field(None, description="Hindi name")
    category: str = Field(..., description="Ingredient category")


class IngredientResponse(IngredientBase):
    """Schema for ingredient response."""
    id: UUID = Field(..., description="Unique identifier")
    typical_unit: str = Field(..., description="Typical measurement unit")
    is_allergen: bool = Field(..., description="Whether this is an allergen")
    allergen_type: Optional[str] = Field(None, description="Type of allergen if applicable")
    
    class Config:
        from_attributes = True


class DishIngredientResponse(BaseModel):
    """Schema for dish ingredient with quantity."""
    ingredient: IngredientResponse = Field(..., description="Ingredient details")
    quantity: Decimal = Field(..., description="Quantity required")
    unit: str = Field(..., description="Measurement unit")
    preparation_note: Optional[str] = Field(None, description="Preparation instructions")
    is_optional: bool = Field(..., description="Whether ingredient is optional")
    
    class Config:
        from_attributes = True


class DishBase(BaseModel):
    """Base schema for dish information."""
    name: str = Field(..., description="Dish name")
    name_hindi: Optional[str] = Field(None, description="Hindi name")
    description: Optional[str] = Field(None, description="Dish description")
    cuisine_type: str = Field(..., description="Cuisine type")
    meal_type: str = Field(..., description="Meal type")


class DishResponse(DishBase):
    """Schema for dish response with full details."""
    id: UUID = Field(..., description="Unique identifier")
    dish_category: Optional[str] = Field(None, description="Dish category")
    
    # Nutritional information
    serving_size_g: Decimal = Field(..., description="Serving size in grams")
    calories: Decimal = Field(..., description="Calories per serving")
    protein_g: Decimal = Field(..., description="Protein in grams")
    carbs_g: Decimal = Field(..., description="Carbohydrates in grams")
    fats_g: Decimal = Field(..., description="Fats in grams")
    fiber_g: Optional[Decimal] = Field(None, description="Fiber in grams")
    
    # Preparation details
    prep_time_minutes: int = Field(..., description="Preparation time")
    cook_time_minutes: int = Field(..., description="Cooking time")
    total_time_minutes: int = Field(..., description="Total time")
    difficulty_level: str = Field(..., description="Difficulty level")
    
    # Dietary tags
    is_vegetarian: bool = Field(..., description="Is vegetarian")
    is_vegan: bool = Field(..., description="Is vegan")
    is_gluten_free: bool = Field(..., description="Is gluten-free")
    is_dairy_free: bool = Field(..., description="Is dairy-free")
    is_nut_free: bool = Field(..., description="Is nut-free")
    
    # Allergen information
    contains_allergens: List[str] = Field(..., description="List of allergens")
    
    # Ingredients (optional, loaded on demand)
    ingredients: Optional[List[DishIngredientResponse]] = Field(None, description="List of ingredients")
    
    class Config:
        from_attributes = True
    
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time from prep and cook time."""
        return self.prep_time_minutes + self.cook_time_minutes


class DishSummaryResponse(BaseModel):
    """Schema for dish summary (without ingredients)."""
    id: UUID = Field(..., description="Unique identifier")
    name: str = Field(..., description="Dish name")
    name_hindi: Optional[str] = Field(None, description="Hindi name")
    meal_type: str = Field(..., description="Meal type")
    calories: Decimal = Field(..., description="Calories per serving")
    protein_g: Decimal = Field(..., description="Protein in grams")
    carbs_g: Decimal = Field(..., description="Carbohydrates in grams")
    fats_g: Decimal = Field(..., description="Fats in grams")
    prep_time_minutes: int = Field(..., description="Preparation time")
    cook_time_minutes: int = Field(..., description="Cooking time")
    difficulty_level: str = Field(..., description="Difficulty level")
    is_vegetarian: bool = Field(..., description="Is vegetarian")
    is_vegan: bool = Field(..., description="Is vegan")
    
    class Config:
        from_attributes = True
```


### 4.2 Meal Template Schemas

```python
# backend/app/schemas/meal_template.py

from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.dish import DishSummaryResponse


class TemplateMealResponse(BaseModel):
    """Schema for template meal with dish assignment."""
    id: UUID = Field(..., description="Unique identifier")
    day_of_week: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    meal_name: str = Field(..., description="Meal name from schedule")
    scheduled_time: time = Field(..., description="Scheduled meal time")
    is_primary: bool = Field(..., description="Is primary recommendation")
    alternative_order: int = Field(..., description="Order for alternatives")
    dish: DishSummaryResponse = Field(..., description="Dish details")
    
    class Config:
        from_attributes = True


class MealSlotResponse(BaseModel):
    """Schema for a meal slot with primary and alternative dishes."""
    meal_name: str = Field(..., description="Meal name")
    scheduled_time: time = Field(..., description="Scheduled time")
    day_of_week: int = Field(..., description="Day of week")
    primary_dish: DishSummaryResponse = Field(..., description="Primary recommended dish")
    alternative_dishes: List[DishSummaryResponse] = Field(..., description="Alternative dish options")


class DayMealsResponse(BaseModel):
    """Schema for all meals in a single day."""
    day_of_week: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    day_name: str = Field(..., description="Day name (Monday, Tuesday, etc.)")
    meals: List[MealSlotResponse] = Field(..., description="All meals for this day")
    total_calories: float = Field(..., description="Total calories for the day")
    total_protein_g: float = Field(..., description="Total protein for the day")
    total_carbs_g: float = Field(..., description="Total carbs for the day")
    total_fats_g: float = Field(..., description="Total fats for the day")


class MealTemplateResponse(BaseModel):
    """Schema for complete meal template."""
    id: UUID = Field(..., description="Unique identifier")
    week_number: int = Field(..., description="Week number (1-4)")
    is_active: bool = Field(..., description="Is currently active template")
    days: List[DayMealsResponse] = Field(..., description="Meals for each day of the week")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class TodayMealsResponse(BaseModel):
    """Schema for today's meals with dish recommendations."""
    date: str = Field(..., description="Today's date (YYYY-MM-DD)")
    day_of_week: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    day_name: str = Field(..., description="Day name")
    meals: List[MealSlotResponse] = Field(..., description="Today's meals")
    total_calories: float = Field(..., description="Total calories for today")
    total_protein_g: float = Field(..., description="Total protein for today")


class NextMealResponse(BaseModel):
    """Schema for next upcoming meal."""
    meal_name: str = Field(..., description="Meal name")
    scheduled_time: time = Field(..., description="Scheduled time")
    time_until_meal_minutes: int = Field(..., description="Minutes until meal time")
    primary_dish: DishSummaryResponse = Field(..., description="Primary recommended dish")
    alternative_dishes: List[DishSummaryResponse] = Field(..., description="Alternative options")


class TemplateRegenerateRequest(BaseModel):
    """Schema for template regeneration request."""
    preferences: Optional[str] = Field(None, description="User preferences for generation")
    week_number: Optional[int] = Field(None, ge=1, le=4, description="Specific week to regenerate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferences": "More chicken dishes, less spicy food",
                "week_number": 1
            }
        }


class DishSwapRequest(BaseModel):
    """Schema for swapping a dish in the template."""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    meal_name: str = Field(..., description="Meal name to swap")
    new_dish_id: UUID = Field(..., description="New dish ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_of_week": 0,
                "meal_name": "Breakfast",
                "new_dish_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
```


### 4.3 Shopping List Schemas

```python
# backend/app/schemas/shopping_list.py

from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class ShoppingListIngredient(BaseModel):
    """Schema for ingredient in shopping list."""
    ingredient_id: UUID = Field(..., description="Ingredient ID")
    name: str = Field(..., description="Ingredient name")
    name_hindi: str | None = Field(None, description="Hindi name")
    category: str = Field(..., description="Ingredient category")
    total_quantity: Decimal = Field(..., description="Total quantity needed")
    unit: str = Field(..., description="Measurement unit")
    is_optional: bool = Field(..., description="Whether ingredient is optional")
    used_in_dishes: List[str] = Field(..., description="List of dish names using this ingredient")


class ShoppingListCategory(BaseModel):
    """Schema for shopping list category."""
    category: str = Field(..., description="Category name")
    ingredients: List[ShoppingListIngredient] = Field(..., description="Ingredients in this category")


class ShoppingListResponse(BaseModel):
    """Schema for complete shopping list."""
    week_number: int = Field(..., description="Week number for this list")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    categories: List[ShoppingListCategory] = Field(..., description="Ingredients grouped by category")
    total_items: int = Field(..., description="Total number of unique ingredients")
```

---

## 5. Service Layer Design

### 5.1 Dish Service

```python
# backend/app/services/dish_service.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishIngredient, Ingredient


class DishService:
    """Service for managing dishes and ingredients."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dish(self, dish_id: UUID, include_ingredients: bool = False) -> Optional[Dish]:
        """Get dish by ID with optional ingredients."""
        query = select(Dish).where(
            Dish.id == dish_id,
            Dish.deleted_at.is_(None),
            Dish.is_active == True
        )
        
        if include_ingredients:
            query = query.options(
                selectinload(Dish.dish_ingredients).selectinload(DishIngredient.ingredient)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_dishes(
        self,
        meal_type: Optional[str] = None,
        diet_type: Optional[str] = None,
        max_prep_time: Optional[int] = None,
        max_calories: Optional[int] = None,
        exclude_allergens: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dish]:
        """Search dishes with filters."""
        query = select(Dish).where(
            Dish.deleted_at.is_(None),
            Dish.is_active == True
        )
        
        # Apply filters
        if meal_type:
            query = query.where(Dish.meal_type == meal_type)
        
        if diet_type == 'vegetarian':
            query = query.where(Dish.is_vegetarian == True)
        elif diet_type == 'vegan':
            query = query.where(Dish.is_vegan == True)
        
        if max_prep_time:
            query = query.where(
                Dish.prep_time_minutes + Dish.cook_time_minutes <= max_prep_time
            )
        
        if max_calories:
            query = query.where(Dish.calories <= max_calories)
        
        if exclude_allergens:
            for allergen in exclude_allergens:
                query = query.where(~Dish.contains_allergens.contains([allergen]))
        
        # Order by popularity
        query = query.order_by(Dish.popularity_score.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_dishes_for_meal_slot(
        self,
        meal_type: str,
        target_calories: float,
        target_protein: float,
        dietary_preferences: dict,
        count: int = 3
    ) -> List[Dish]:
        """Get suitable dishes for a specific meal slot."""
        # Calculate acceptable ranges (±15% for calories, ±20% for protein)
        cal_min = target_calories * 0.85
        cal_max = target_calories * 1.15
        protein_min = target_protein * 0.80
        protein_max = target_protein * 1.20
        
        query = select(Dish).where(
            Dish.deleted_at.is_(None),
            Dish.is_active == True,
            Dish.meal_type == meal_type,
            Dish.calories.between(cal_min, cal_max),
            Dish.protein_g.between(protein_min, protein_max)
        )
        
        # Apply dietary filters
        diet_type = dietary_preferences.get('diet_type')
        if diet_type == 'vegetarian':
            query = query.where(Dish.is_vegetarian == True)
        elif diet_type == 'vegan':
            query = query.where(Dish.is_vegan == True)
        
        # Exclude allergens
        allergies = dietary_preferences.get('allergies', [])
        for allergen in allergies:
            query = query.where(~Dish.contains_allergens.contains([allergen]))
        
        # Order by popularity and limit
        query = query.order_by(Dish.popularity_score.desc()).limit(count)
        
        result = await self.db.execute(query)
        return result.scalars().all()
```


### 5.2 Meal Template Service

```python
# backend/app/services/meal_template_service.py

from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ProfileLockedException
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealSchedule
from app.models.profile import UserProfile
from app.services.dish_service import DishService


class MealTemplateService:
    """Service for managing meal templates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dish_service = DishService(db)
    
    async def get_active_template(self, profile_id: UUID) -> Optional[MealTemplate]:
        """Get user's currently active meal template."""
        # Determine current week number (1-4 rotation)
        week_of_year = date.today().isocalendar()[1]
        current_week = ((week_of_year - 1) % 4) + 1
        
        result = await self.db.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile_id,
                MealTemplate.week_number == current_week,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish),
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.meal_schedule)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_today_meals(self, profile_id: UUID) -> dict:
        """Get today's meals with dish recommendations."""
        template = await self.get_active_template(profile_id)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active meal template found"
            )
        
        # Get today's day of week (0=Monday, 6=Sunday)
        today = date.today()
        day_of_week = today.weekday()
        
        # Filter template meals for today
        today_meals = [
            tm for tm in template.template_meals
            if tm.day_of_week == day_of_week
        ]
        
        # Group by meal schedule
        meals_by_schedule = {}
        for tm in today_meals:
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
        
        # Build response
        meals = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for schedule_data in meals_by_schedule.values():
            primary_dish = schedule_data['primary']
            if primary_dish:
                meals.append({
                    'meal_name': schedule_data['meal_schedule'].meal_name,
                    'scheduled_time': schedule_data['meal_schedule'].scheduled_time,
                    'day_of_week': day_of_week,
                    'primary_dish': primary_dish,
                    'alternative_dishes': schedule_data['alternatives']
                })
                
                total_calories += float(primary_dish.calories)
                total_protein += float(primary_dish.protein_g)
                total_carbs += float(primary_dish.carbs_g)
                total_fats += float(primary_dish.fats_g)
        
        # Sort by scheduled time
        meals.sort(key=lambda m: m['scheduled_time'])
        
        return {
            'date': today.isoformat(),
            'day_of_week': day_of_week,
            'day_name': today.strftime('%A'),
            'meals': meals,
            'total_calories': total_calories,
            'total_protein_g': total_protein,
            'total_carbs_g': total_carbs,
            'total_fats_g': total_fats
        }
    
    async def get_next_meal(self, profile_id: UUID) -> Optional[dict]:
        """Get next upcoming meal with dish recommendations."""
        today_meals_data = await self.get_today_meals(profile_id)
        current_time = datetime.now().time()
        
        # Find next meal after current time
        for meal in today_meals_data['meals']:
            if meal['scheduled_time'] > current_time:
                # Calculate time until meal
                now = datetime.now()
                meal_datetime = datetime.combine(date.today(), meal['scheduled_time'])
                time_diff = meal_datetime - now
                minutes_until = int(time_diff.total_seconds() / 60)
                
                return {
                    'meal_name': meal['meal_name'],
                    'scheduled_time': meal['scheduled_time'],
                    'time_until_meal_minutes': minutes_until,
                    'primary_dish': meal['primary_dish'],
                    'alternative_dishes': meal['alternative_dishes']
                }
        
        return None
    
    async def get_template_by_week(
        self,
        profile_id: UUID,
        week_number: int
    ) -> Optional[MealTemplate]:
        """Get specific week template."""
        result = await self.db.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile_id,
                MealTemplate.week_number == week_number,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish),
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.meal_schedule)
            )
        )
        return result.scalar_one_or_none()
```


    async def generate_template(
        self,
        profile_id: UUID,
        week_number: int,
        preferences: Optional[str] = None
    ) -> MealTemplate:
        """Generate new meal template for user."""
        # Check profile lock
        profile = await self._get_profile(profile_id)
        if profile.is_locked:
            raise ProfileLockedException()
        
        # Get user's meal plan and schedules
        meal_plan = profile.meal_plan
        meal_schedules = profile.meal_schedules
        dietary_prefs = profile.dietary_preferences
        
        if not meal_plan or not meal_schedules:
            raise HTTPException(
                status_code=400,
                detail="User must have meal plan and schedules configured"
            )
        
        # Calculate per-meal targets
        meals_per_day = len(meal_schedules)
        daily_calories = meal_plan.daily_calorie_target
        daily_protein = float(meal_plan.protein_percentage) / 100 * daily_calories / 4  # 4 cal/g
        
        # Create template
        template = MealTemplate(
            profile_id=profile_id,
            week_number=week_number,
            is_active=True,
            generated_by='ai_agent',
            generation_reason=preferences or 'Initial template generation'
        )
        self.db.add(template)
        await self.db.flush()
        
        # Generate meals for each day of the week
        for day in range(7):  # 0=Monday to 6=Sunday
            for schedule in meal_schedules:
                # Determine meal type and targets
                meal_type = self._determine_meal_type(schedule.meal_name)
                cal_target, protein_target = self._calculate_meal_targets(
                    schedule.meal_name,
                    daily_calories,
                    daily_protein,
                    meals_per_day
                )
                
                # Get suitable dishes (1 primary + 2 alternatives)
                dishes = await self.dish_service.get_dishes_for_meal_slot(
                    meal_type=meal_type,
                    target_calories=cal_target,
                    target_protein=protein_target,
                    dietary_preferences={
                        'diet_type': dietary_prefs.diet_type,
                        'allergies': dietary_prefs.allergies
                    },
                    count=3
                )
                
                if not dishes:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Could not find suitable dishes for {schedule.meal_name}"
                    )
                
                # Create template meals
                for idx, dish in enumerate(dishes):
                    template_meal = TemplateMeal(
                        template_id=template.id,
                        meal_schedule_id=schedule.id,
                        dish_id=dish.id,
                        day_of_week=day,
                        is_primary=(idx == 0),
                        alternative_order=idx + 1
                    )
                    self.db.add(template_meal)
        
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def swap_dish(
        self,
        profile_id: UUID,
        day_of_week: int,
        meal_name: str,
        new_dish_id: UUID
    ) -> MealTemplate:
        """Swap a dish in the template."""
        # Check profile lock
        profile = await self._get_profile(profile_id)
        if profile.is_locked:
            raise ProfileLockedException()
        
        # Get active template
        template = await self.get_active_template(profile_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active template found"
            )
        
        # Find meal schedule by name
        meal_schedule = next(
            (s for s in profile.meal_schedules if s.meal_name == meal_name),
            None
        )
        if not meal_schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Meal schedule '{meal_name}' not found"
            )
        
        # Verify new dish exists and is suitable
        new_dish = await self.dish_service.get_dish(new_dish_id)
        if not new_dish:
            raise HTTPException(
                status_code=404,
                detail="Dish not found"
            )
        
        # Find and update primary template meal
        result = await self.db.execute(
            select(TemplateMeal)
            .where(
                TemplateMeal.template_id == template.id,
                TemplateMeal.meal_schedule_id == meal_schedule.id,
                TemplateMeal.day_of_week == day_of_week,
                TemplateMeal.is_primary == True
            )
        )
        template_meal = result.scalar_one_or_none()
        
        if not template_meal:
            raise HTTPException(
                status_code=404,
                detail="Template meal not found"
            )
        
        # Update dish
        template_meal.dish_id = new_dish_id
        
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    def _determine_meal_type(self, meal_name: str) -> str:
        """Determine meal type from meal name."""
        meal_name_lower = meal_name.lower()
        
        if 'pre' in meal_name_lower and 'workout' in meal_name_lower:
            return 'pre_workout'
        elif 'post' in meal_name_lower and 'workout' in meal_name_lower:
            return 'post_workout'
        elif 'breakfast' in meal_name_lower:
            return 'breakfast'
        elif 'lunch' in meal_name_lower:
            return 'lunch'
        elif 'dinner' in meal_name_lower:
            return 'dinner'
        else:
            return 'snack'
    
    def _calculate_meal_targets(
        self,
        meal_name: str,
        daily_calories: int,
        daily_protein: float,
        meals_per_day: int
    ) -> tuple[float, float]:
        """Calculate calorie and protein targets for a meal."""
        meal_type = self._determine_meal_type(meal_name)
        
        # Distribution percentages
        distributions = {
            'pre_workout': (0.10, 0.10),  # 10% calories, 10% protein
            'post_workout': (0.15, 0.20),  # 15% calories, 20% protein
            'breakfast': (0.30, 0.30),     # 30% calories, 30% protein
            'lunch': (0.35, 0.30),         # 35% calories, 30% protein
            'dinner': (0.30, 0.25),        # 30% calories, 25% protein
            'snack': (0.10, 0.10)          # 10% calories, 10% protein
        }
        
        cal_pct, protein_pct = distributions.get(meal_type, (1.0 / meals_per_day, 1.0 / meals_per_day))
        
        return (
            daily_calories * cal_pct,
            daily_protein * protein_pct
        )
    
    async def _get_profile(self, profile_id: UUID) -> UserProfile:
        """Get user profile with relationships."""
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.id == profile_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_schedules),
                selectinload(UserProfile.dietary_preferences)
            )
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        return profile
```


### 5.3 Shopping List Service

```python
# backend/app/services/shopping_list_service.py

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import DishIngredient, Ingredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.services.meal_template_service import MealTemplateService


class ShoppingListService:
    """Service for generating shopping lists."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = MealTemplateService(db)
    
    async def generate_shopping_list(
        self,
        profile_id: UUID,
        weeks: int = 1
    ) -> dict:
        """Generate shopping list for specified number of weeks."""
        # Get active template
        template = await self.template_service.get_active_template(profile_id)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active meal template found"
            )
        
        # Collect all dishes from template
        dish_ids = list(set(tm.dish_id for tm in template.template_meals if tm.is_primary))
        
        # Get dish ingredients
        result = await self.db.execute(
            select(DishIngredient)
            .where(DishIngredient.dish_id.in_(dish_ids))
            .options(
                selectinload(DishIngredient.ingredient),
                selectinload(DishIngredient.dish)
            )
        )
        dish_ingredients = result.scalars().all()
        
        # Aggregate ingredients by category
        ingredient_totals: Dict[UUID, dict] = defaultdict(lambda: {
            'ingredient': None,
            'total_quantity': Decimal('0'),
            'unit': None,
            'is_optional': False,
            'used_in_dishes': []
        })
        
        for di in dish_ingredients:
            ing_id = di.ingredient_id
            ingredient_totals[ing_id]['ingredient'] = di.ingredient
            ingredient_totals[ing_id]['total_quantity'] += di.quantity * weeks * 7  # 7 days
            ingredient_totals[ing_id]['unit'] = di.unit
            ingredient_totals[ing_id]['is_optional'] = ingredient_totals[ing_id]['is_optional'] or di.is_optional
            ingredient_totals[ing_id]['used_in_dishes'].append(di.dish.name)
        
        # Group by category
        categories = defaultdict(list)
        for ing_data in ingredient_totals.values():
            ingredient = ing_data['ingredient']
            categories[ingredient.category].append({
                'ingredient_id': ingredient.id,
                'name': ingredient.name,
                'name_hindi': ingredient.name_hindi,
                'category': ingredient.category,
                'total_quantity': ing_data['total_quantity'],
                'unit': ing_data['unit'],
                'is_optional': ing_data['is_optional'],
                'used_in_dishes': list(set(ing_data['used_in_dishes']))
            })
        
        # Sort categories
        category_order = ['protein', 'vegetable', 'fruit', 'grain', 'dairy', 'spice', 'oil', 'other']
        sorted_categories = []
        for cat in category_order:
            if cat in categories:
                sorted_categories.append({
                    'category': cat,
                    'ingredients': sorted(categories[cat], key=lambda x: x['name'])
                })
        
        # Calculate date range
        today = date.today()
        end_date = today + timedelta(days=weeks * 7 - 1)
        
        return {
            'week_number': template.week_number,
            'start_date': today.isoformat(),
            'end_date': end_date.isoformat(),
            'categories': sorted_categories,
            'total_items': len(ingredient_totals)
        }
```

---

## 6. API Endpoints

### 6.1 Meal Template Endpoints

```python
# backend/app/api/v1/endpoints/meal_templates.py

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
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


@router.get("/today", response_model=TodayMealsResponse, status_code=status.HTTP_200_OK)
async def get_today_meals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TodayMealsResponse:
    """
    Get today's meals with dish recommendations.
    
    Returns all meals scheduled for today with primary and alternative dish options.
    Includes nutritional totals for the day.
    """
    service = MealTemplateService(db)
    profile = current_user.profile
    
    meals_data = await service.get_today_meals(profile.id)
    return TodayMealsResponse(**meals_data)


@router.get("/next", response_model=NextMealResponse, status_code=status.HTTP_200_OK)
async def get_next_meal(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> NextMealResponse:
    """
    Get next upcoming meal with dish recommendations.
    
    Returns the next meal after current time with dish options and time until meal.
    """
    service = MealTemplateService(db)
    profile = current_user.profile
    
    next_meal = await service.get_next_meal(profile.id)
    
    if not next_meal:
        raise HTTPException(
            status_code=404,
            detail="No more meals scheduled for today"
        )
    
    return NextMealResponse(**next_meal)


@router.get("/template", response_model=MealTemplateResponse, status_code=status.HTTP_200_OK)
async def get_meal_template(
    week_number: Annotated[int | None, Query(ge=1, le=4)] = None,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealTemplateResponse:
    """
    Get meal template for specified week.
    
    If week_number is not provided, returns currently active template.
    """
    service = MealTemplateService(db)
    profile = current_user.profile
    
    if week_number:
        template = await service.get_template_by_week(profile.id, week_number)
    else:
        template = await service.get_active_template(profile.id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Meal template not found"
        )
    
    # Transform to response format
    # (Implementation details for building DayMealsResponse objects)
    return MealTemplateResponse(...)


@router.post("/template/regenerate", response_model=MealTemplateResponse, status_code=status.HTTP_201_CREATED)
async def regenerate_template(
    request: TemplateRegenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealTemplateResponse:
    """
    Regenerate meal template with optional preferences.
    
    Requires unlocked profile. Creates new template with different dishes
    while maintaining nutritional targets.
    """
    service = MealTemplateService(db)
    profile = current_user.profile
    
    week_number = request.week_number or 1
    
    template = await service.generate_template(
        profile_id=profile.id,
        week_number=week_number,
        preferences=request.preferences
    )
    
    return MealTemplateResponse(...)


@router.patch("/template/swap", response_model=MealTemplateResponse, status_code=status.HTTP_200_OK)
async def swap_dish(
    request: DishSwapRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MealTemplateResponse:
    """
    Swap a dish in the meal template.
    
    Requires unlocked profile. Replaces primary dish for specified meal slot.
    """
    service = MealTemplateService(db)
    profile = current_user.profile
    
    template = await service.swap_dish(
        profile_id=profile.id,
        day_of_week=request.day_of_week,
        meal_name=request.meal_name,
        new_dish_id=request.new_dish_id
    )
    
    return MealTemplateResponse(...)
```


### 6.2 Shopping List Endpoint

```python
# backend/app/api/v1/endpoints/shopping_list.py

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.shopping_list import ShoppingListResponse
from app.services.shopping_list_service import ShoppingListService


router = APIRouter()


@router.get("", response_model=ShoppingListResponse, status_code=status.HTTP_200_OK)
async def get_shopping_list(
    weeks: Annotated[int, Query(ge=1, le=4)] = 1,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ShoppingListResponse:
    """
    Get shopping list for specified number of weeks.
    
    Aggregates all ingredients from meal template and calculates quantities.
    Organizes by category for easy shopping.
    """
    service = ShoppingListService(db)
    profile = current_user.profile
    
    shopping_list = await service.generate_shopping_list(profile.id, weeks)
    
    return ShoppingListResponse(**shopping_list)
```

### 6.3 Dish Search Endpoint

```python
# backend/app/api/v1/endpoints/dishes.py

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dish import DishResponse, DishSummaryResponse
from app.services.dish_service import DishService


router = APIRouter()


@router.get("/search", response_model=List[DishSummaryResponse], status_code=status.HTTP_200_OK)
async def search_dishes(
    meal_type: Annotated[str | None, Query()] = None,
    diet_type: Annotated[str | None, Query()] = None,
    max_prep_time: Annotated[int | None, Query(ge=0, le=240)] = None,
    max_calories: Annotated[int | None, Query(ge=0, le=2000)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[DishSummaryResponse]:
    """
    Search dishes with filters.
    
    Allows filtering by meal type, diet type, preparation time, and calories.
    Returns paginated results.
    """
    service = DishService(db)
    profile = current_user.profile
    
    # Get user's dietary preferences for allergen filtering
    dietary_prefs = profile.dietary_preferences
    exclude_allergens = dietary_prefs.allergies if dietary_prefs else []
    
    dishes = await service.search_dishes(
        meal_type=meal_type,
        diet_type=diet_type,
        max_prep_time=max_prep_time,
        max_calories=max_calories,
        exclude_allergens=exclude_allergens,
        limit=limit,
        offset=offset
    )
    
    return [DishSummaryResponse.from_orm(dish) for dish in dishes]


@router.get("/{dish_id}", response_model=DishResponse, status_code=status.HTTP_200_OK)
async def get_dish(
    dish_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> DishResponse:
    """
    Get detailed dish information including ingredients.
    
    Returns complete dish details with ingredient list and nutritional info.
    """
    service = DishService(db)
    
    dish = await service.get_dish(dish_id, include_ingredients=True)
    
    if not dish:
        raise HTTPException(
            status_code=404,
            detail="Dish not found"
        )
    
    return DishResponse.from_orm(dish)
```

---

## 7. Integration Points

### 7.1 Onboarding Integration

**Step 6.5: Meal Template Generation** (New sub-step after meal schedule configuration)

```python
# backend/app/services/onboarding_service.py

async def complete_meal_schedule_step(self, user_id: UUID, meal_schedules: List[dict]) -> dict:
    """Complete meal schedule step and generate initial meal template."""
    # ... existing meal schedule creation logic ...
    
    # Generate initial meal template (Week 1)
    template_service = MealTemplateService(self.db)
    
    try:
        template = await template_service.generate_template(
            profile_id=profile.id,
            week_number=1,
            preferences="Initial onboarding template"
        )
        
        # Generate remaining weeks (2, 3, 4)
        for week in [2, 3, 4]:
            await template_service.generate_template(
                profile_id=profile.id,
                week_number=week,
                preferences=f"Initial onboarding template - Week {week}"
            )
    except Exception as e:
        # Log error but don't fail onboarding
        logger.error(f"Failed to generate meal templates: {e}")
    
    return {
        "step": 6,
        "completed": True,
        "meal_schedules": meal_schedules,
        "template_generated": True
    }
```


### 7.2 AI Agent Integration

**Diet Planning Agent Enhancement**

```python
# backend/app/agents/diet_planner.py

from app.services.meal_template_service import MealTemplateService
from app.services.dish_service import DishService

class DietPlannerAgent(BaseAgent):
    """Enhanced diet planning agent with dish recommendations."""
    
    def get_tools(self) -> List:
        """Diet-specific tools including dish queries."""
        
        @tool
        async def get_todays_meals():
            """Get today's meal plan with specific dishes"""
            template_service = MealTemplateService(self.db)
            meals_data = await template_service.get_today_meals(self.context.profile_id)
            return meals_data
        
        @tool
        async def get_next_meal():
            """Get next upcoming meal with dish recommendations"""
            template_service = MealTemplateService(self.db)
            next_meal = await template_service.get_next_meal(self.context.profile_id)
            return next_meal
        
        @tool
        async def search_alternative_dishes(meal_type: str, dietary_requirements: str):
            """Search for alternative dishes matching requirements"""
            dish_service = DishService(self.db)
            dishes = await dish_service.search_dishes(
                meal_type=meal_type,
                diet_type=self.context.dietary_preferences.diet_type,
                exclude_allergens=self.context.dietary_preferences.allergies
            )
            return dishes
        
        @tool
        async def get_shopping_list():
            """Get shopping list for current week"""
            from app.services.shopping_list_service import ShoppingListService
            shopping_service = ShoppingListService(self.db)
            shopping_list = await shopping_service.generate_shopping_list(
                self.context.profile_id,
                weeks=1
            )
            return shopping_list
        
        return [
            get_todays_meals,
            get_next_meal,
            search_alternative_dishes,
            get_shopping_list
        ]
```

### 7.3 Profile Locking Integration

Meal templates respect the existing profile locking mechanism:

```python
# All template modification operations check profile lock:
# - generate_template()
# - swap_dish()
# - regenerate_template()

# Profile versions are created for template changes:
async def create_template_version(self, profile_id: UUID, reason: str):
    """Create profile version before template modification."""
    # Existing profile version logic
    # Snapshot includes meal_templates relationship
```

---

## 8. Caching Strategy

### 8.1 Redis Cache Keys

```python
# Cache key patterns
CACHE_KEYS = {
    'active_template': 'meal_template:profile:{profile_id}:active',
    'today_meals': 'meal_template:profile:{profile_id}:today:{date}',
    'shopping_list': 'shopping_list:profile:{profile_id}:weeks:{weeks}',
    'dish': 'dish:{dish_id}',
    'dish_search': 'dish:search:{hash}',
}

# TTL values
CACHE_TTL = {
    'active_template': 86400,  # 24 hours
    'today_meals': 3600,       # 1 hour
    'shopping_list': 3600,     # 1 hour
    'dish': 604800,            # 7 days (dishes rarely change)
    'dish_search': 1800,       # 30 minutes
}
```

### 8.2 Cache Invalidation

```python
# Invalidate cache on template changes
async def invalidate_template_cache(profile_id: UUID):
    """Invalidate all template-related cache for user."""
    await redis.delete(f'meal_template:profile:{profile_id}:active')
    await redis.delete_pattern(f'meal_template:profile:{profile_id}:today:*')
    await redis.delete_pattern(f'shopping_list:profile:{profile_id}:*')

# Invalidate on dish updates (admin only)
async def invalidate_dish_cache(dish_id: UUID):
    """Invalidate dish cache."""
    await redis.delete(f'dish:{dish_id}')
    await redis.delete_pattern('dish:search:*')
```

---

## 9. Performance Optimization

### 9.1 Database Query Optimization

**Eager Loading Strategy:**
```python
# Always use selectinload for relationships
query = select(MealTemplate).options(
    selectinload(MealTemplate.template_meals)
    .selectinload(TemplateMeal.dish),
    selectinload(MealTemplate.template_meals)
    .selectinload(TemplateMeal.meal_schedule)
)
```

**Index Usage:**
- All foreign keys have indexes
- Composite indexes on frequently queried combinations
- Partial indexes with WHERE clauses for active records

### 9.2 Query Performance Targets

| Query | Target | Strategy |
|-------|--------|----------|
| Get today's meals | < 100ms | Cache + eager loading |
| Get next meal | < 50ms | Cache + simple filter |
| Get shopping list | < 200ms | Cache + aggregation |
| Search dishes | < 150ms | Indexes + pagination |
| Generate template | < 2s | Async + batch insert |

---

## 10. Data Seeding Strategy

### 10.1 Dish Database Seeding

```python
# backend/seed_dishes.py

import asyncio
from decimal import Decimal

from app.db.session import async_session_maker
from app.models.dish import Dish, Ingredient, DishIngredient


INDIAN_DISHES = [
    {
        'name': 'Egg Omelette with Multigrain Toast',
        'name_hindi': 'अंडे का ऑमलेट',
        'cuisine_type': 'north_indian',
        'meal_type': 'breakfast',
        'calories': Decimal('350'),
        'protein_g': Decimal('25'),
        'carbs_g': Decimal('30'),
        'fats_g': Decimal('15'),
        'prep_time_minutes': 5,
        'cook_time_minutes': 10,
        'difficulty_level': 'easy',
        'is_vegetarian': True,
        'ingredients': [
            {'name': 'eggs', 'quantity': 3, 'unit': 'piece'},
            {'name': 'multigrain_bread', 'quantity': 2, 'unit': 'slice'},
            {'name': 'onion', 'quantity': 50, 'unit': 'g'},
            {'name': 'tomato', 'quantity': 50, 'unit': 'g'},
        ]
    },
    # ... more dishes
]


async def seed_dishes():
    """Seed dish database with Indian dishes."""
    async with async_session_maker() as db:
        for dish_data in INDIAN_DISHES:
            # Create dish
            dish = Dish(**{k: v for k, v in dish_data.items() if k != 'ingredients'})
            db.add(dish)
            await db.flush()
            
            # Create ingredients and link
            for ing_data in dish_data['ingredients']:
                # Get or create ingredient
                ingredient = await get_or_create_ingredient(db, ing_data['name'])
                
                # Create dish-ingredient link
                dish_ing = DishIngredient(
                    dish_id=dish.id,
                    ingredient_id=ingredient.id,
                    quantity=ing_data['quantity'],
                    unit=ing_data['unit']
                )
                db.add(dish_ing)
            
            await db.commit()


if __name__ == '__main__':
    asyncio.run(seed_dishes())
```

### 10.2 Minimum Dish Requirements

For MVP launch, seed database with:
- **50 breakfast dishes** (veg + non-veg)
- **50 lunch dishes** (veg + non-veg)
- **50 dinner dishes** (veg + non-veg)
- **30 snack dishes**
- **10 pre-workout snacks**
- **10 post-workout meals**

**Total: 200 dishes minimum**

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/test_meal_template_service.py

import pytest
from app.services.meal_template_service import MealTemplateService


@pytest.mark.asyncio
async def test_get_today_meals(db_session, test_user_with_template):
    """Test retrieving today's meals."""
    service = MealTemplateService(db_session)
    
    meals_data = await service.get_today_meals(test_user_with_template.profile.id)
    
    assert meals_data['day_of_week'] >= 0
    assert meals_data['day_of_week'] <= 6
    assert len(meals_data['meals']) > 0
    assert meals_data['total_calories'] > 0


@pytest.mark.asyncio
async def test_generate_template_respects_dietary_preferences(db_session, vegetarian_user):
    """Test template generation respects dietary preferences."""
    service = MealTemplateService(db_session)
    
    template = await service.generate_template(
        profile_id=vegetarian_user.profile.id,
        week_number=1
    )
    
    # Verify all dishes are vegetarian
    for tm in template.template_meals:
        assert tm.dish.is_vegetarian == True


@pytest.mark.asyncio
async def test_swap_dish_validates_profile_lock(db_session, locked_profile_user):
    """Test dish swap fails when profile is locked."""
    service = MealTemplateService(db_session)
    
    with pytest.raises(ProfileLockedException):
        await service.swap_dish(
            profile_id=locked_profile_user.profile.id,
            day_of_week=0,
            meal_name='Breakfast',
            new_dish_id=UUID('...')
        )
```


### 11.2 Property-Based Tests

```python
# tests/test_meal_template_properties.py

from hypothesis import given, strategies as st
from hypothesis import assume
import pytest

from app.services.meal_template_service import MealTemplateService


@pytest.mark.asyncio
@given(
    week_number=st.integers(min_value=1, max_value=4),
    daily_calories=st.integers(min_value=1500, max_value=3500)
)
async def test_template_meets_calorie_targets(db_session, test_user, week_number, daily_calories):
    """Property: Generated template always meets calorie targets within ±5%."""
    # Update user's meal plan
    test_user.profile.meal_plan.daily_calorie_target = daily_calories
    await db_session.commit()
    
    service = MealTemplateService(db_session)
    template = await service.generate_template(
        profile_id=test_user.profile.id,
        week_number=week_number
    )
    
    # Calculate total calories for each day
    for day in range(7):
        day_meals = [tm for tm in template.template_meals 
                    if tm.day_of_week == day and tm.is_primary]
        day_calories = sum(float(tm.dish.calories) for tm in day_meals)
        
        # Assert within ±5% of target
        assert abs(day_calories - daily_calories) <= daily_calories * 0.05


@pytest.mark.asyncio
@given(
    allergens=st.lists(
        st.sampled_from(['peanuts', 'tree_nuts', 'dairy', 'eggs', 'soy', 'wheat']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
async def test_template_excludes_allergens(db_session, test_user, allergens):
    """Property: Template never includes dishes with user's allergens."""
    # Set user's allergies
    test_user.profile.dietary_preferences.allergies = allergens
    await db_session.commit()
    
    service = MealTemplateService(db_session)
    template = await service.generate_template(
        profile_id=test_user.profile.id,
        week_number=1
    )
    
    # Verify no dishes contain allergens
    for tm in template.template_meals:
        dish_allergens = set(tm.dish.contains_allergens)
        user_allergens = set(allergens)
        assert dish_allergens.isdisjoint(user_allergens)


@pytest.mark.asyncio
@given(
    diet_type=st.sampled_from(['vegetarian', 'vegan', 'omnivore'])
)
async def test_template_respects_diet_type(db_session, test_user, diet_type):
    """Property: Template always respects dietary restrictions."""
    test_user.profile.dietary_preferences.diet_type = diet_type
    await db_session.commit()
    
    service = MealTemplateService(db_session)
    template = await service.generate_template(
        profile_id=test_user.profile.id,
        week_number=1
    )
    
    for tm in template.template_meals:
        if diet_type == 'vegetarian':
            assert tm.dish.is_vegetarian == True
        elif diet_type == 'vegan':
            assert tm.dish.is_vegan == True
```

### 11.3 Integration Tests

```python
# tests/test_meal_template_integration.py

import pytest
from fastapi.testclient import TestClient


def test_get_today_meals_endpoint(client: TestClient, auth_headers):
    """Test GET /meals/today endpoint."""
    response = client.get("/api/v1/meals/today", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'date' in data
    assert 'meals' in data
    assert len(data['meals']) > 0
    assert 'total_calories' in data


def test_regenerate_template_requires_unlock(client: TestClient, locked_user_headers):
    """Test template regeneration fails when profile is locked."""
    response = client.post(
        "/api/v1/meals/template/regenerate",
        headers=locked_user_headers,
        json={"preferences": "More chicken dishes"}
    )
    
    assert response.status_code == 403
    assert 'locked' in response.json()['detail'].lower()


def test_shopping_list_aggregates_correctly(client: TestClient, auth_headers):
    """Test shopping list aggregation."""
    response = client.get("/api/v1/meals/shopping-list?weeks=1", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'categories' in data
    assert len(data['categories']) > 0
    assert 'total_items' in data
    
    # Verify categories are organized
    category_names = [cat['category'] for cat in data['categories']]
    assert 'protein' in category_names or 'vegetable' in category_names
```

---

## 12. Migration Plan

### 12.1 Database Migrations

```sql
-- Migration 001: Create dishes table
CREATE TABLE dishes (
    -- ... (full schema from section 2.2.1)
);

-- Migration 002: Create ingredients table
CREATE TABLE ingredients (
    -- ... (full schema from section 2.2.2)
);

-- Migration 003: Create dish_ingredients junction table
CREATE TABLE dish_ingredients (
    -- ... (full schema from section 2.2.3)
);

-- Migration 004: Create meal_templates table
CREATE TABLE meal_templates (
    -- ... (full schema from section 2.2.4)
);

-- Migration 005: Create template_meals table
CREATE TABLE template_meals (
    -- ... (full schema from section 2.2.5)
);

-- Migration 006: Add indexes
CREATE INDEX idx_dishes_meal_type ON dishes(meal_type) WHERE deleted_at IS NULL;
-- ... (all indexes from schemas)

-- Migration 007: Seed initial dish data
-- Run seed_dishes.py script
```

### 12.2 Deployment Steps

1. **Phase 1: Database Setup**
   - Run migrations 001-006
   - Verify schema integrity
   - Run seed script (Migration 007)

2. **Phase 2: Code Deployment**
   - Deploy new models
   - Deploy services
   - Deploy API endpoints
   - Update API documentation

3. **Phase 3: Onboarding Integration**
   - Update onboarding flow
   - Test template generation
   - Monitor error rates

4. **Phase 4: Backfill Existing Users**
   - Generate templates for existing users
   - Run in batches (100 users at a time)
   - Monitor performance

```python
# Backfill script
async def backfill_meal_templates():
    """Generate meal templates for existing users."""
    async with async_session_maker() as db:
        # Get users without templates
        result = await db.execute(
            select(UserProfile)
            .outerjoin(MealTemplate)
            .where(MealTemplate.id.is_(None))
        )
        profiles = result.scalars().all()
        
        template_service = MealTemplateService(db)
        
        for profile in profiles:
            try:
                for week in [1, 2, 3, 4]:
                    await template_service.generate_template(
                        profile_id=profile.id,
                        week_number=week,
                        preferences="Backfill generation"
                    )
                print(f"Generated templates for profile {profile.id}")
            except Exception as e:
                print(f"Failed for profile {profile.id}: {e}")
```

---

## 13. Monitoring & Observability

### 13.1 Metrics to Track

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

# Template operations
template_generation_total = Counter(
    'meal_template_generation_total',
    'Total meal template generations',
    ['status']
)

template_generation_duration = Histogram(
    'meal_template_generation_duration_seconds',
    'Time to generate meal template'
)

# API endpoints
meals_today_requests = Counter(
    'meals_today_requests_total',
    'Total requests to /meals/today'
)

shopping_list_requests = Counter(
    'shopping_list_requests_total',
    'Total requests to /meals/shopping-list'
)

# Dish queries
dish_search_duration = Histogram(
    'dish_search_duration_seconds',
    'Time to search dishes'
)
```

### 13.2 Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Log template generation
logger.info(
    "Generated meal template",
    extra={
        'profile_id': str(profile_id),
        'week_number': week_number,
        'dish_count': len(template.template_meals),
        'duration_ms': duration
    }
)

# Log errors
logger.error(
    "Failed to generate template",
    extra={
        'profile_id': str(profile_id),
        'error': str(e),
        'dietary_preferences': dietary_prefs
    },
    exc_info=True
)
```

---

## 14. Security Considerations

### 14.1 Authorization

- Users can only access their own meal templates
- Dish database is read-only for regular users
- Admin role required for dish CRUD operations
- Profile lock enforcement on all modifications

### 14.2 Input Validation

- All API inputs validated via Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via proper response encoding
- Rate limiting on expensive operations (template generation)

### 14.3 Data Privacy

- Meal templates are user-specific
- No cross-user data leakage
- Dietary preferences remain private
- GDPR compliance: templates deleted with user account

---

## 15. Correctness Properties

### Property 1: Nutritional Balance
**Statement:** For any generated meal template, the sum of calories from all primary dishes in a day must be within ±5% of the user's daily calorie target.

**Validates:** Requirements 1.1, 2.2, FR-1

**Test Strategy:** Property-based test with varying calorie targets (1500-3500)

### Property 2: Dietary Restriction Compliance
**Statement:** For any generated meal template, no dish shall contain ingredients that match the user's allergies, intolerances, or dietary restrictions.

**Validates:** Requirements 6.1-6.5, FR-10, FR-11

**Test Strategy:** Property-based test with varying allergen combinations

### Property 3: Macro Percentage Consistency
**Statement:** For any meal template, the weighted average of macro percentages across all primary dishes must be within ±10% of the user's target macro distribution.

**Validates:** Requirements 2.2, FR-1

**Test Strategy:** Property-based test with varying macro distributions

### Property 4: Template Completeness
**Statement:** For any generated meal template, every meal schedule slot for every day of the week must have at least one primary dish and at least one alternative dish.

**Validates:** Requirements 2.1, 2.2, FR-3

**Test Strategy:** Structural property test on template generation

### Property 5: Shopping List Accuracy
**Statement:** For any shopping list, the total quantity of each ingredient must equal the sum of quantities required by all primary dishes in the template, multiplied by the number of weeks.

**Validates:** Requirements 4.1-4.3, FR-8, FR-9

**Test Strategy:** Property-based test with varying week counts

---

## 16. Open Questions & Decisions

### 16.1 Resolved Decisions

✅ **Use 4-week rotation** instead of infinite variety  
✅ **Store templates in database** instead of generating on-demand  
✅ **Provide 2-3 alternatives** per meal slot  
✅ **Focus on Indian cuisine** for MVP  
✅ **Use existing profile locking** mechanism  

### 16.2 Open Questions

❓ **How to handle seasonal ingredients?**  
- Option A: Mark dishes as seasonal, filter by current season
- Option B: Ignore seasonality for MVP
- **Decision needed:** Before dish database seeding

❓ **Should we support custom recipes?**  
- Option A: Allow users to add custom dishes (future phase)
- Option B: Admin-only dish management
- **Decision:** Admin-only for MVP, custom recipes in v2

❓ **How to handle portion sizes for different calorie targets?**  
- Option A: Scale ingredient quantities dynamically
- Option B: Create dish variants (small/medium/large)
- **Decision needed:** Before template generation implementation

---

## 17. Success Criteria

This design is considered successful when:

✅ All database tables created and indexed  
✅ All models and schemas implemented  
✅ All service methods functional  
✅ All API endpoints operational  
✅ Dish database seeded with 200+ dishes  
✅ Template generation < 2 seconds  
✅ API response times meet targets  
✅ All unit tests passing  
✅ All property-based tests passing  
✅ Integration with onboarding complete  
✅ Profile locking integration verified  
✅ Caching strategy implemented  
✅ Monitoring and logging in place  

---

**Document Status:** Ready for Implementation  
**Next Steps:** Create tasks.md with implementation breakdown

# Meal Dish Management - Implementation Tasks

**Feature:** meal-dish-management  
**Status:** Not Started  
**Created:** January 30, 2026  
**Estimated Timeline:** 4-6 weeks

---

## Overview

This document provides a detailed breakdown of implementation tasks for the meal dish management feature. Tasks are organized by phase with clear dependencies, acceptance criteria, and complexity estimates.

---

## Phase 1: Database Foundation (5 tasks)

### Task 1.1: Create Dishes Table Migration
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** None  
**Estimated Time:** 2-3 hours

Create Alembic migration for the `dishes` table.

**Acceptance Criteria:**
- [x] Migration file created: `backend/alembic/versions/XXX_create_dishes_table.py`
- [x] All columns defined (name, cuisine_type, meal_type, nutritional info, etc.)
- [x] CHECK constraints on calories, macros, prep_time, difficulty, meal_type
- [x] Indexes created: meal_type, dietary flags, cuisine, nutrition, allergens (GIN)
- [x] Migration runs: `poetry run alembic upgrade head`
- [x] Migration rolls back: `poetry run alembic downgrade -1`

**Implementation Notes:**
- Use ARRAY(Text) for contains_allergens
- Use Numeric for nutritional values
- Include partial indexes with WHERE deleted_at IS NULL

---

### Task 1.2: Create Ingredients Table Migration
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** None  
**Estimated Time:** 1-2 hours

Create Alembic migration for the `ingredients` table.

**Acceptance Criteria:**
- [x] Migration file created: `backend/alembic/versions/XXX_create_ingredients_table.py`
- [x] All columns defined (name, category, nutritional info per 100g, allergen tags)
- [x] UNIQUE constraint on name
- [x] CHECK constraint on category enum
- [x] Indexes created: category, allergen
- [x] Migration runs and rolls back successfully

---

### Task 1.3: Create Dish Ingredients Junction Table Migration
**Priority:** High  
**Complexity:** Low  
**Dependencies:** 1.1, 1.2  
**Estimated Time:** 1 hour

Create migration for `dish_ingredients` junction table.

**Acceptance Criteria:**
- [x] Migration file created: `backend/alembic/versions/5e89aa6e6fb3_create_dish_ingredients_table.py`
- [x] Foreign key to dishes: ON DELETE CASCADE
- [x] Foreign key to ingredients: ON DELETE RESTRICT
- [x] UNIQUE constraint on (dish_id, ingredient_id)
- [x] CHECK constraint: quantity > 0
- [x] Indexes on dish_id and ingredient_id
- [x] Migration runs and rolls back successfully

---

### Task 1.4: Create Meal Templates Table Migration
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** None  
**Estimated Time:** 1-2 hours

Create migration for `meal_templates` table.

**Acceptance Criteria:**
- [x] Migration file created: `backend/alembic/versions/43aeb196576c_create_meal_templates_table.py`
- [x] Foreign key to user_profiles: ON DELETE CASCADE
- [x] CHECK constraint: week_number BETWEEN 1 AND 4
- [x] UNIQUE constraint on (profile_id, week_number)
- [x] Indexes: profile_id, (profile_id, is_active)
- [x] Migration runs and rolls back successfully

---

### Task 1.5: Create Template Meals Table Migration
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 1.1, 1.4  
**Estimated Time:** 2 hours

Create migration for `template_meals` table.

**Acceptance Criteria:**
- [x] Migration file created: `backend/alembic/versions/582ee71d9305_create_template_meals_table.py`
- [x] Foreign key to meal_templates: ON DELETE CASCADE
- [x] Foreign key to meal_schedules: ON DELETE CASCADE (from Phase 1 core)
- [x] Foreign key to dishes: ON DELETE RESTRICT
- [x] CHECK constraint: day_of_week BETWEEN 0 AND 6
- [x] CHECK constraint: alternative_order BETWEEN 1 AND 5
- [x] Indexes: template_id, meal_schedule_id, dish_id, (template_id, day_of_week)
- [x] Migration runs and rolls back successfully

**Note:** Requires meal_schedules table from Phase 1 core endpoints.

---

## Phase 2: Data Models (5 tasks)

### Task 2.1: Create Dish Model
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 1.1  
**Estimated Time:** 2-3 hours

Implement SQLAlchemy Dish model.

**Acceptance Criteria:**
- [x] File created: `backend/app/models/dish.py`
- [ ] Dish class inherits from BaseModel
- [ ] All columns defined with correct SQLAlchemy types
- [ ] All CHECK constraints defined in __table_args__
- [ ] Relationships: dish_ingredients, template_meals
- [ ] Indexes defined in __table_args__
- [ ] Model imports without errors
- [ ] Can create instance: `dish = Dish(name="Test", ...)`

**Implementation Notes:**
- Use Column(ARRAY(Text)) for contains_allergens
- Use Column(Numeric(6,2)) for nutritional values
- Define relationships with back_populates

---

### Task 2.2: Create Ingredient and DishIngredient Models
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 1.2, 1.3, 2.1  
**Estimated Time:** 2 hours

Implement Ingredient and DishIngredient models.

**Acceptance Criteria:**
- [x] Ingredient class added to `backend/app/models/dish.py`
- [ ] DishIngredient class added to same file
- [ ] All columns and constraints defined
- [ ] Relationships configured: ingredient.dish_ingredients, dish.dish_ingredients
- [ ] Models import without errors
- [ ] Can create instances and link them

---

### Task 2.3: Create Meal Template Models
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 1.4, 1.5  
**Estimated Time:** 2-3 hours

Implement MealTemplate and TemplateMeal models.

**Acceptance Criteria:**
- [x] File created: `backend/app/models/meal_template.py`
- [ ] MealTemplate class defined with all columns
- [ ] TemplateMeal class defined with all columns
- [ ] Relationships: template.template_meals, template.profile
- [ ] Relationships: template_meal.template, template_meal.dish, template_meal.meal_schedule
- [ ] All constraints and indexes in __table_args__
- [ ] Models import without errors

---

### Task 2.4: Update UserProfile Model
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** 2.3  
**Estimated Time:** 30 minutes

Add meal_templates relationship to UserProfile.

**Acceptance Criteria:**
- [x] Relationship added to UserProfile in `backend/app/models/profile.py`
- [x] Cascade behavior: "all, delete-orphan"
- [x] back_populates="profile"
- [x] No import errors
- [x] Existing tests still pass

**Code:**
```python
meal_templates = relationship(
    "MealTemplate",
    back_populates="profile",
    cascade="all, delete-orphan"
)
```

---

### Task 2.5: Update Models __init__.py
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** 2.1, 2.2, 2.3  
**Estimated Time:** 15 minutes

Export new models from models package.

**Acceptance Criteria:**
- [x] Dish, Ingredient, DishIngredient exported from `backend/app/models/__init__.py`
- [x] MealTemplate, TemplateMeal exported
- [x] Can import: `from app.models import Dish, MealTemplate`

---

## Phase 3: Pydantic Schemas (4 tasks)

### Task 3.1: Create Dish Schemas
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 2.1, 2.2  
**Estimated Time:** 2-3 hours

Create Pydantic schemas for dish responses.

**Acceptance Criteria:**
- [x] File created: `backend/app/schemas/dish.py`
- [x] IngredientBase schema with name, category
- [x] IngredientResponse schema with all fields
- [x] DishIngredientResponse with ingredient, quantity, unit
- [x] DishBase schema with name, cuisine_type, meal_type
- [x] DishResponse with all fields + ingredients list
- [x] DishSummaryResponse (without ingredients)
- [x] All fields have Field(..., description="...")
- [x] Config.from_attributes = True
- [x] total_time_minutes computed property
- [x] Schemas validate correctly

**Example:**
```python
class DishResponse(DishBase):
    id: UUID
    calories: Decimal
    protein_g: Decimal
    # ... other fields
    ingredients: Optional[List[DishIngredientResponse]] = None
    
    @property
    def total_time_minutes(self) -> int:
        return self.prep_time_minutes + self.cook_time_minutes
```

---

### Task 3.2: Create Meal Template Schemas
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 2.3, 3.1  
**Estimated Time:** 3 hours

Create Pydantic schemas for meal template responses and requests.

**Acceptance Criteria:**
- [x] File created: `backend/app/schemas/meal_template.py`
- [x] TemplateMealResponse: id, day_of_week, meal_name, scheduled_time, is_primary, dish
- [x] MealSlotResponse: meal_name, scheduled_time, primary_dish, alternative_dishes
- [x] DayMealsResponse: day_of_week, day_name, meals, total_calories/protein/carbs/fats
- [x] MealTemplateResponse: id, week_number, is_active, days, timestamps
- [x] TodayMealsResponse: date, day_of_week, day_name, meals, totals
- [x] NextMealResponse: meal_name, scheduled_time, time_until_meal_minutes, dishes
- [x] TemplateRegenerateRequest: preferences (optional), week_number (optional)
- [x] DishSwapRequest: day_of_week, meal_name, new_dish_id
- [x] All schemas have json_schema_extra with examples
- [x] Schemas validate correctly

---

### Task 3.3: Create Shopping List Schemas
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** 3.1  
**Estimated Time:** 1 hour

Create Pydantic schemas for shopping list responses.

**Acceptance Criteria:**
- [x] File created: `backend/app/schemas/shopping_list.py`
- [x] ShoppingListIngredient: ingredient_id, name, category, total_quantity, unit, used_in_dishes
- [x] ShoppingListCategory: category, ingredients list
- [x] ShoppingListResponse: week_number, start_date, end_date, categories, total_items
- [x] All fields have descriptions
- [x] Schemas validate correctly

---

### Task 3.4: Update Schemas __init__.py
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** 3.1, 3.2, 3.3  
**Estimated Time:** 15 minutes

Export new schemas from schemas package.

**Acceptance Criteria:**
- [x] All dish schemas exported from `backend/app/schemas/__init__.py`
- [x] All meal template schemas exported
- [x] All shopping list schemas exported
- [x] Can import: `from app.schemas import DishResponse, MealTemplateResponse`

---

## Phase 4: Service Layer (5 tasks)

### Task 4.1: Create Dish Service
**Priority:** High  
**Complexity:** High  
**Dependencies:** 2.1, 2.2, 3.1  
**Estimated Time:** 4-5 hours

Implement DishService with search and filtering.

**Acceptance Criteria:**
- [x] File created: `backend/app/services/dish_service.py`
- [x] DishService class with __init__(self, db: AsyncSession)
- [x] get_dish(dish_id, include_ingredients=False) method
- [x] search_dishes(meal_type, diet_type, max_prep_time, max_calories, exclude_allergens, limit, offset) method
- [x] get_dishes_for_meal_slot(meal_type, target_calories, target_protein, dietary_preferences, count=3) method
- [x] Uses selectinload for eager loading
- [x] Proper async/await usage
- [x] All methods have docstrings
- [x] Service instantiates without errors

**Key Logic:**
- get_dishes_for_meal_slot: ±15% calories, ±20% protein tolerance
- Filter by diet_type (vegetarian/vegan)
- Exclude allergens using ~contains([allergen])
- Order by popularity_score

---

### Task 4.2: Create Meal Template Service - Read Operations
**Priority:** High  
**Complexity:** High  
**Dependencies:** 2.3, 3.2, 4.1  
**Estimated Time:** 5-6 hours

Implement MealTemplateService read operations.

**Acceptance Criteria:**
- [x] File created: `backend/app/services/meal_template_service.py`
- [x] MealTemplateService class with __init__(self, db: AsyncSession)
- [x] get_active_template(profile_id) - determines current week (1-4 rotation)
- [x] get_today_meals(profile_id) - returns today's meals with dishes
- [x] get_next_meal(profile_id) - finds next meal after current time
- [x] get_template_by_week(profile_id, week_number)
- [x] Uses selectinload for template_meals, dishes, meal_schedules
- [x] Calculates nutritional totals
- [x] Groups meals by schedule
- [x] All methods have docstrings

**Key Logic:**
- Current week: ((week_of_year - 1) % 4) + 1
- Today's day_of_week: date.today().weekday()
- Filter template_meals by day_of_week and is_primary

---

### Task 4.3: Create Meal Template Service - Write Operations
**Priority:** High  
**Complexity:** High  
**Dependencies:** 4.2  
**Estimated Time:** 6-8 hours

Implement MealTemplateService write operations.

**Acceptance Criteria:**
- [x] generate_template(profile_id, week_number, preferences) method
- [x] swap_dish(profile_id, day_of_week, meal_name, new_dish_id) method
- [x] _determine_meal_type(meal_name) helper
- [x] _calculate_meal_targets(meal_name, daily_calories, daily_protein, meals_per_day) helper
- [x] _get_profile(profile_id) helper with eager loading
- [x] Profile lock validation in all write methods
- [ ] Raises ProfileLockedException if locked
- [ ] Creates template with primary + 2 alternatives per meal slot
- [ ] All methods have docstrings

**Key Logic:**
- generate_template: Loop through 7 days × meal_schedules
- For each slot: get 3 dishes from DishService.get_dishes_for_meal_slot()
- First dish is primary (is_primary=True), others are alternatives
- Meal target distribution: pre_workout 10%, post_workout 15%, breakfast 30%, lunch 35%, dinner 30%, snack 10%

---

### Task 4.4: Create Shopping List Service
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** 4.2, 3.3  
**Estimated Time:** 3-4 hours

Implement ShoppingListService for ingredient aggregation.

**Acceptance Criteria:**
- [x] File created: `backend/app/services/shopping_list_service.py`
- [x] ShoppingListService class with __init__(self, db: AsyncSession)
- [ ] generate_shopping_list(profile_id, weeks=1) method
- [ ] Aggregates ingredients from all primary dishes in template
- [ ] Groups by ingredient category
- [ ] Calculates total quantities (× weeks × 7 days)
- [ ] Tracks which dishes use each ingredient
- [ ] Sorts categories in logical order
- [ ] All methods have docstrings

**Key Logic:**
- Use defaultdict to aggregate quantities
- Multiply quantities by weeks × 7
- Category order: protein, vegetable, fruit, grain, dairy, spice, oil, other

---

### Task 4.5: Update Services __init__.py
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** 4.1, 4.3, 4.4  
**Estimated Time:** 15 minutes

Export new services from services package.

**Acceptance Criteria:**
- [x] DishService exported from `backend/app/services/__init__.py`
- [x] MealTemplateService exported
- [ ] ShoppingListService exported
- [ ] Can import: `from app.services import DishService, MealTemplateService`

---

## Phase 5: API Endpoints (6 tasks)

### Task 5.1: Create Meal Template Endpoints - Read
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 4.2, 3.2  
**Estimated Time:** 3-4 hours

Implement read-only meal template endpoints.

**Acceptance Criteria:**
- [x] File created: `backend/app/api/v1/endpoints/meal_templates.py`
- [x] Router created with APIRouter()
- [x] GET /today endpoint - returns TodayMealsResponse
- [x] GET /next endpoint - returns NextMealResponse (404 if none)
- [x] GET /template endpoint - returns MealTemplateResponse (optional week_number query param)
- [x] Uses Depends(get_current_user) and Depends(get_db)
- [x] Response models specified in decorator
- [x] Error handling with HTTPException
- [x] Docstrings with description and examples

---

### Task 5.2: Create Meal Template Endpoints - Write
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 5.1, 4.3  
**Estimated Time:** 2-3 hours

Implement write meal template endpoints.

**Acceptance Criteria:**
- [x] POST /template/regenerate endpoint - returns MealTemplateResponse (201)
- [ ] PATCH /template/swap endpoint - returns MealTemplateResponse (200)
- [x] Request body validation with Pydantic
- [x] Profile lock validation (403 if locked)
- [x] Proper status codes
- [x] Error responses with detail and error_code
- [x] Docstrings with examples
- [ ] Error responses with detail and error_code
- [ ] Docstrings with examples

---

### Task 5.3: Create Shopping List Endpoint
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** 4.4, 3.3  
**Estimated Time:** 1-2 hours

Implement shopping list endpoint.

**Acceptance Criteria:**
- [x] File created: `backend/app/api/v1/endpoints/shopping_list.py`
- [x] Router created
- [x] GET / endpoint - returns ShoppingListResponse
- [x] Query param: weeks (1-4, default 1)
- [x] Uses Depends(get_current_user) and Depends(get_db)
- [x] Response model specified
- [x] Error handling
- [x] Docstring with example

---

### Task 5.4: Create Dish Endpoints
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** 4.1, 3.1  
**Estimated Time:** 2-3 hours

Implement dish search and detail endpoints.

**Acceptance Criteria:**
- [x] File created: `backend/app/api/v1/endpoints/dishes.py`
- [x] Router created
- [x] GET /search endpoint - returns List[DishSummaryResponse]
- [x] Query params: meal_type, diet_type, max_prep_time, max_calories, limit (1-100), offset
- [x] GET /{dish_id} endpoint - returns DishResponse with ingredients
- [x] Applies user's dietary preferences to search (exclude allergens)
- [x] Pagination support
- [x] Response models specified
- [x] Docstrings with examples

---

### Task 5.5: Update API Router
**Priority:** High  
**Complexity:** Low  
**Dependencies:** 5.1, 5.2, 5.3, 5.4  
**Estimated Time:** 30 minutes

Register new endpoints in API router.

**Acceptance Criteria:**
- [x] meal_templates router included in `backend/app/api/v1/__init__.py`
- [x] Prefix: "/meals", tags: ["Meal Templates"]
- [x] shopping_list router included
- [x] Prefix: "/meals/shopping-list", tags: ["Shopping List"]
- [x] dishes router included
- [x] Prefix: "/dishes", tags: ["Dishes"]
- [x] Routes accessible at /api/v1/meals/today, etc.

---

### Task 5.6: Enhance Existing Meals Endpoints (Optional)
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** 5.1  
**Estimated Time:** 1-2 hours

Update existing /meals endpoints to include dish data.

**Acceptance Criteria:**
- [ ] GET /meals/today in `backend/app/api/v1/endpoints/meals.py` enhanced
- [ ] GET /meals/next enhanced
- [ ] Backward compatible (dish fields optional)
- [ ] Existing response structure maintained
- [ ] Existing tests still pass

**Note:** This is optional - new endpoints provide dish data.

---

## Phase 6: Data Seeding (4 tasks)

### Task 6.1: Create Dish Seed Data
**Priority:** High  
**Complexity:** High  
**Dependencies:** 2.1, 2.2  
**Estimated Time:** 8-12 hours

Create comprehensive dish data for seeding.

**Acceptance Criteria:**
- [x] File created: `backend/seed_data/dishes.py`
- [ ] Minimum 50 breakfast dishes (veg + non-veg mix)
- [ ] Minimum 50 lunch dishes
- [ ] Minimum 50 dinner dishes
- [ ] Minimum 30 snack dishes
- [ ] Minimum 10 pre-workout dishes
- [ ] Minimum 10 post-workout dishes
- [ ] Each dish has: name, name_hindi, cuisine_type, meal_type, calories, protein/carbs/fats, prep/cook time, difficulty
- [ ] Each dish has ingredient list with quantities
- [ ] Accurate nutritional data
- [ ] Realistic preparation times
- [ ] Data structured as Python list of dicts

**Example Structure:**
```python
DISHES = [
    {
        'name': 'Egg Omelette with Multigrain Toast',
        'name_hindi': 'अंडे का ऑमलेट',
        'cuisine_type': 'north_indian',
        'meal_type': 'breakfast',
        'calories': 350,
        'protein_g': 25,
        'carbs_g': 30,
        'fats_g': 15,
        'prep_time_minutes': 5,
        'cook_time_minutes': 10,
        'difficulty_level': 'easy',
        'is_vegetarian': True,
        'ingredients': [
            {'name': 'eggs', 'quantity': 3, 'unit': 'piece'},
            {'name': 'multigrain_bread', 'quantity': 2, 'unit': 'slice'},
        ]
    },
]
```

---

### Task 6.2: Create Ingredient Seed Data
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 2.2  
**Estimated Time:** 3-4 hours

Create master ingredient list.

**Acceptance Criteria:**
- [x] File created: `backend/seed_data/ingredients.py`
- [ ] All common Indian ingredients included (100+ ingredients)
- [ ] Categories: vegetable, fruit, protein, grain, dairy, spice, oil, other
- [ ] Allergen tags set (peanuts, tree_nuts, dairy, eggs, soy, wheat, fish, shellfish)
- [ ] Nutritional data per 100g (optional but recommended)
- [ ] Typical units specified
- [ ] Data structured as Python list of dicts

---

### Task 6.3: Create Dish Seeding Script
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 6.1, 6.2  
**Estimated Time:** 3-4 hours

Create script to seed dish database.

**Acceptance Criteria:**
- [x] File created: `backend/seed_dishes.py`
- [ ] Imports dish and ingredient data
- [ ] get_or_create_ingredient(db, name) function
- [ ] Creates dishes with all fields
- [ ] Links ingredients via dish_ingredients
- [ ] Script is idempotent (checks if dish exists)
- [ ] Progress logging (print statements)
- [ ] Error handling with try/except
- [ ] Async implementation
- [ ] Can run: `poetry run python seed_dishes.py`

**Key Logic:**
```python
async def seed_dishes():
    async with async_session_maker() as db:
        for dish_data in DISHES:
            # Check if exists
            # Create dish
            # Create/get ingredients
            # Link via dish_ingredients
            await db.commit()
```

---

### Task 6.4: Run Dish Seeding
**Priority:** High  
**Complexity:** Low  
**Dependencies:** 6.3, Phase 1 (all migrations)  
**Estimated Time:** 30 minutes

Execute dish seeding script.

**Acceptance Criteria:**
- [x] All migrations applied: `poetry run alembic upgrade head`
- [ ] Seed script runs: `poetry run python seed_dishes.py`
- [ ] Minimum 200 dishes created
- [ ] All ingredients created
- [ ] All dish-ingredient relationships created
- [ ] Verify with SQL: `SELECT COUNT(*) FROM dishes;`
- [ ] Document any issues

---

## Phase 7: Onboarding Integration (2 tasks)

### Task 7.1: Update Onboarding Service
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 4.3  
**Estimated Time:** 2-3 hours

Add meal template generation to onboarding flow.

**Acceptance Criteria:**
- [x] Update `backend/app/services/onboarding_service.py`
- [x] Modify complete_meal_schedule_step() method
- [x] After meal schedules created, generate templates for weeks 1-4
- [x] Error handling doesn't fail onboarding (log error, continue)
- [x] Template generation logged
- [ ] Can optionally add template_generated flag to onboarding_state

**Implementation:**
```python
# After meal schedules created
template_service = MealTemplateService(self.db)
try:
    for week in [1, 2, 3, 4]:
        await template_service.generate_template(
            profile_id=profile.id,
            week_number=week,
            preferences="Initial onboarding template"
        )
except Exception as e:
    logger.error(f"Template generation failed: {e}")
```

---

### Task 7.2: Update Onboarding Tests
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** 7.1  
**Estimated Time:** 1-2 hours

Update onboarding tests to verify template generation.

**Acceptance Criteria:**
- [x] Update `backend/tests/test_onboarding_service.py`
- [x] Test verifies 4 templates created after onboarding
- [x] Test checks templates respect dietary preferences
- [x] Existing onboarding tests still pass
- [x] Run: `poetry run pytest backend/tests/test_onboarding_service.py`

---

## Phase 8: Caching (2 tasks)

### Task 8.1: Implement Template Caching
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** 4.2  
**Estimated Time:** 2-3 hours

Add Redis caching to meal template service.

**Acceptance Criteria:**
- [ ] Cache keys defined in service
- [ ] get_active_template() checks cache first
- [ ] get_today_meals() checks cache first
- [ ] TTL: 24h for active_template, 1h for today_meals
- [ ] Cache invalidation on template changes (generate, swap)
- [ ] Cache miss handling (fetch from DB, store in cache)
- [ ] Redis connection error handling (fallback to DB)

**Cache Keys:**
```python
f"meal_template:profile:{profile_id}:active"
f"meal_template:profile:{profile_id}:today:{date}"
```

---

### Task 8.2: Implement Dish Caching
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** 4.1  
**Estimated Time:** 1-2 hours

Add Redis caching to dish service.

**Acceptance Criteria:**
- [ ] get_dish() checks cache first
- [ ] search_dishes() uses cache with query hash
- [ ] TTL: 7 days for dishes (rarely change)
- [ ] Cache invalidation on dish updates (admin only)
- [ ] Redis connection error handling

---

## Phase 9: Testing (6 tasks)

### Task 9.1: Unit Tests - Dish Service
**Priority:** High  
**Complexity:** Medium  
**Dependencies:** 4.1  
**Estimated Time:** 3-4 hours

Create unit tests for DishService.

**Acceptance Criteria:**
- [x] File created: `backend/tests/test_dish_service.py`
- [x] Test get_dish() with and without ingredients
- [x] Test search_dishes() with various filters
- [x] Test get_dishes_for_meal_slot()
- [x] Test dietary preference filtering
- [x] Test allergen exclusion
- [x] All tests pass: `poetry run pytest backend/tests/test_dish_service.py`
- [x] Code coverage > 80%

---

### Task 9.2: Unit Tests - Meal Template Service
**Priority:** High  
**Complexity:** High  
**Dependencies:** 4.3  
**Estimated Time:** 4-5 hours

Create unit tests for MealTemplateService.

**Acceptance Criteria:**
- [x] File created: `backend/tests/test_meal_template_service.py`
- [x] Test get_active_template()
- [x] Test get_today_meals()
- [x] Test get_next_meal()
- [x] Test generate_template()
- [x] Test swap_dish()
- [x] Test profile lock validation
- [x] Test dietary preference enforcement
- [x] All tests pass
- [x] Code coverage > 80%

---

### Task 9.3: Unit Tests - Shopping List Service
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** 4.4  
**Estimated Time:** 2-3 hours

Create unit tests for ShoppingListService.

**Acceptance Criteria:**
- [x] File created: `backend/tests/test_shopping_list_service.py`
- [x] Test generate_shopping_list()
- [x] Test ingredient aggregation
- [x] Test category grouping
- [x] Test quantity calculations
- [x] All tests pass
- [x] Code coverage > 80%

---

### Task 9.4: API Integration Tests
**Priority:** High  
**Complexity:** High  
**Dependencies:** Phase 5 (all endpoints)  
**Estimated Time:** 4-5 hours

Create integration tests for all endpoints.

**Acceptance Criteria:**
- [x] Files created: `backend/tests/test_meal_template_endpoints.py`, `test_shopping_list_endpoints.py`, `test_dish_endpoints.py`
- [x] Test GET /meals/today
- [x] Test GET /meals/next
- [x] Test GET /meals/template
- [x] Test POST /meals/template/regenerate
- [ ] Test PATCH /meals/template/swap
- [x] Test GET /meals/shopping-list
- [x] Test GET /dishes/search
- [x] Test GET /dishes/{id}
- [x] Test authentication (401 without token)
- [x] Test profile lock enforcement (403 when locked)
- [ ] All tests pass

---

### Task 9.5: Property-Based Tests
**Priority:** Medium  
**Complexity:** High  
**Dependencies:** 4.3  
**Estimated Time:** 4-6 hours

Create property-based tests for correctness.

**Acceptance Criteria:**
- [x] File created: `backend/tests/test_meal_template_properties.py`
- [x] Install hypothesis: `poetry add --group dev hypothesis`
- [x] Property 1: Nutritional balance (±5% calories)
- [x] Property 2: Dietary restriction compliance
- [x] Property 3: Macro percentage consistency
- [x] Property 4: Template completeness
- [x] Property 5: Shopping list accuracy
- [x] All properties pass with 100+ examples
- [x] Run: `poetry run pytest backend/tests/test_meal_template_properties.py`

**Example:**
```python
@given(daily_calories=st.integers(min_value=1500, max_value=3500))
async def test_template_meets_calorie_targets(db, user, daily_calories):
    # Generate template
    # Calculate daily totals
    # Assert within ±5%
```

---

### Task 9.6: Update Test Fixtures
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** Phase 2 (all models)  
**Estimated Time:** 2-3 hours

Create test fixtures for dishes and templates.

**Acceptance Criteria:**
- [x] Update `backend/tests/conftest.py`
- [x] Fixture: sample_dishes (10-20 dishes)
- [x] Fixture: sample_ingredients
- [x] Fixture: user_with_meal_template
- [x] Fixture: vegetarian_user
- [x] Fixture: user_with_allergies
- [x] Fixtures can be reused: `def test_something(sample_dishes):`

---

## Phase 10: Documentation & Deployment (5 tasks)

### Task 10.1: Update API Documentation
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** Phase 5 (all endpoints)  
**Estimated Time:** 1-2 hours

Ensure OpenAPI documentation is complete.

**Acceptance Criteria:**
- [x] All endpoints have descriptions
- [ ] All request/response schemas documented
- [ ] Example requests/responses in docstrings
- [ ] Error responses documented (400, 401, 403, 404)
- [ ] Swagger UI displays correctly at /docs
- [ ] Test manually: visit http://localhost:8000/docs

---

### Task 10.2: Create Migration Guide
**Priority:** Medium  
**Complexity:** Low  
**Dependencies:** Phase 1 (all migrations)  
**Estimated Time:** 1 hour

Document migration process for deployment.

**Acceptance Criteria:**
- [ ] File created: `backend/docs/migrations/meal-dish-management.md`
- [ ] Migration order documented (1.1 → 1.2 → 1.3 → 1.4 → 1.5)
- [ ] Rollback procedures documented
- [x] Seeding instructions included
- [ ] Backfill script usage documented

---

### Task 10.3: Create Backfill Script
**Priority:** Medium  
**Complexity:** Medium  
**Dependencies:** 4.3  
**Estimated Time:** 2-3 hours

Create script to generate templates for existing users.

**Acceptance Criteria:**
- [ ] File created: `backend/backfill_meal_templates.py`
- [ ] Finds users without templates
- [ ] Generates all 4 weeks for each user
- [ ] Batch processing (100 users at a time)
- [ ] Progress logging
- [ ] Error handling and retry logic
- [ ] Dry-run mode: `--dry-run` flag
- [ ] Run: `poetry run python backfill_meal_templates.py`

---

### Task 10.4: Add Monitoring
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** Phase 4 (all services)  
**Estimated Time:** 1-2 hours

Add metrics and logging for observability.

**Acceptance Criteria:**
- [ ] Prometheus metrics for template generation
- [ ] Metrics for API endpoint calls
- [ ] Structured logging for template operations
- [ ] Error logging with context
- [ ] Performance logging for slow queries (>1s)

---

### Task 10.5: Update README
**Priority:** Low  
**Complexity:** Low  
**Dependencies:** None  
**Estimated Time:** 30 minutes

Update project README with feature information.

**Acceptance Criteria:**
- [x] Feature description added to `backend/README.md`
- [x] New API endpoints listed
- [ ] Seeding instructions included
- [x] Migration instructions included

---

## Task Summary

**Total Tasks:** 50  
**Estimated Timeline:** 4-6 weeks (1 developer)

### By Phase:
- Phase 1 (Database): 5 tasks, ~8 hours
- Phase 2 (Models): 5 tasks, ~8 hours
- Phase 3 (Schemas): 4 tasks, ~7 hours
- Phase 4 (Services): 5 tasks, ~20 hours
- Phase 5 (Endpoints): 6 tasks, ~12 hours
- Phase 6 (Seeding): 4 tasks, ~16 hours
- Phase 7 (Onboarding): 2 tasks, ~4 hours
- Phase 8 (Caching): 2 tasks, ~4 hours
- Phase 9 (Testing): 6 tasks, ~20 hours
- Phase 10 (Documentation): 5 tasks, ~7 hours

**Total Estimated Hours:** ~106 hours

### Critical Path:
1. Phase 1 (Database) → Phase 2 (Models) → Phase 6.1-6.2 (Seed Data)
2. Phase 3 (Schemas) → Phase 6.3-6.4 (Run Seeding)
3. Phase 4 (Services) → Phase 5 (Endpoints)
4. Phase 7 (Onboarding) → Phase 9 (Testing)
5. Phase 8 (Caching) and Phase 10 (Documentation) can be done in parallel

### Recommended Execution Order:
1. Complete Phase 1 entirely (database foundation)
2. Complete Phase 2 entirely (models)
3. Complete Phase 6.1-6.2 (create seed data files)
4. Complete Phase 3 (schemas)
5. Complete Phase 6.3-6.4 (run seeding)
6. Complete Phase 4 (services)
7. Complete Phase 5 (endpoints)
8. Complete Phase 7 (onboarding integration)
9. Complete Phase 8 (caching)
10. Complete Phase 9 (testing)
11. Complete Phase 10 (documentation)

---

## Getting Started

To begin implementation:

1. **Setup:**
   ```bash
   cd backend
   poetry install
   poetry shell
   ```

2. **Start with Phase 1, Task 1.1:**
   ```bash
   poetry run alembic revision --autogenerate -m "create dishes table"
   # Edit the generated migration file
   poetry run alembic upgrade head
   ```

3. **Track Progress:**
   - Check off tasks as completed
   - Update status in this file
   - Document any blockers or issues

---

**Ready for Implementation** ✅

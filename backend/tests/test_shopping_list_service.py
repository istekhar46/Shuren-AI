"""Tests for shopping list service."""

import pytest
import pytest_asyncio
from datetime import time
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.preferences import MealPlan, MealSchedule, DietaryPreference
from app.models.profile import UserProfile
from app.models.user import User
from app.models.meal_template import MealTemplate, TemplateMeal
from app.services.shopping_list_service import ShoppingListService
from app.core.security import hash_password


@pytest_asyncio.fixture
async def test_user_with_template(db_session: AsyncSession):
    """Create a test user with meal template and dishes with ingredients."""
    # Create user
    user = User(
        id=uuid4(),
        email="shoptest@example.com",
        hashed_password=hash_password("password123"),
        full_name="Shopping Test User",
        is_active=True
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="intermediate"
    )
    db_session.add(profile)
    
    # Create meal plan
    meal_plan = MealPlan(
        id=uuid4(),
        profile_id=profile.id,
        daily_calorie_target=2000,
        protein_percentage=30,
        carbs_percentage=45,
        fats_percentage=25
    )
    db_session.add(meal_plan)
    
    # Create meal schedules
    breakfast_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="Breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True
    )
    lunch_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="Lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True
    )
    db_session.add(breakfast_schedule)
    db_session.add(lunch_schedule)
    
    # Create dietary preferences
    dietary_prefs = DietaryPreference(
        id=uuid4(),
        profile_id=profile.id,
        diet_type="omnivore",
        allergies=[],
        intolerances=[],
        dislikes=[]
    )
    db_session.add(dietary_prefs)
    
    # Create ingredients
    chicken = Ingredient(
        id=uuid4(),
        name="chicken_breast",
        name_hindi="चिकन ब्रेस्ट",
        category="protein",
        typical_unit="g",
        is_allergen=False
    )
    rice = Ingredient(
        id=uuid4(),
        name="basmati_rice",
        name_hindi="बासमती चावल",
        category="grain",
        typical_unit="g",
        is_allergen=False
    )
    tomato = Ingredient(
        id=uuid4(),
        name="tomato",
        name_hindi="टमाटर",
        category="vegetable",
        typical_unit="g",
        is_allergen=False
    )
    db_session.add(chicken)
    db_session.add(rice)
    db_session.add(tomato)
    
    # Create dishes with ingredients
    breakfast_dish = Dish(
        id=uuid4(),
        name="Chicken Omelette",
        cuisine_type="north_indian",
        meal_type="breakfast",
        serving_size_g=300,
        calories=600,
        protein_g=45,
        carbs_g=70,
        fats_g=15,
        prep_time_minutes=10,
        cook_time_minutes=15,
        difficulty_level="easy",
        is_vegetarian=False,
        is_vegan=False,
        is_gluten_free=True,
        is_dairy_free=False,
        is_nut_free=True,
        contains_allergens=[],
        is_active=True,
        popularity_score=100
    )
    db_session.add(breakfast_dish)
    
    lunch_dish = Dish(
        id=uuid4(),
        name="Chicken Rice Bowl",
        cuisine_type="north_indian",
        meal_type="lunch",
        serving_size_g=400,
        calories=700,
        protein_g=45,
        carbs_g=80,
        fats_g=20,
        prep_time_minutes=15,
        cook_time_minutes=20,
        difficulty_level="medium",
        is_vegetarian=False,
        is_vegan=False,
        is_gluten_free=True,
        is_dairy_free=True,
        is_nut_free=True,
        contains_allergens=[],
        is_active=True,
        popularity_score=100
    )
    db_session.add(lunch_dish)
    
    await db_session.flush()
    
    # Link ingredients to dishes
    breakfast_chicken = DishIngredient(
        id=uuid4(),
        dish_id=breakfast_dish.id,
        ingredient_id=chicken.id,
        quantity=Decimal("100"),
        unit="g",
        is_optional=False
    )
    breakfast_tomato = DishIngredient(
        id=uuid4(),
        dish_id=breakfast_dish.id,
        ingredient_id=tomato.id,
        quantity=Decimal("50"),
        unit="g",
        is_optional=False
    )
    lunch_chicken = DishIngredient(
        id=uuid4(),
        dish_id=lunch_dish.id,
        ingredient_id=chicken.id,
        quantity=Decimal("150"),
        unit="g",
        is_optional=False
    )
    lunch_rice = DishIngredient(
        id=uuid4(),
        dish_id=lunch_dish.id,
        ingredient_id=rice.id,
        quantity=Decimal("100"),
        unit="g",
        is_optional=False
    )
    lunch_tomato = DishIngredient(
        id=uuid4(),
        dish_id=lunch_dish.id,
        ingredient_id=tomato.id,
        quantity=Decimal("75"),
        unit="g",
        is_optional=False
    )
    
    db_session.add(breakfast_chicken)
    db_session.add(breakfast_tomato)
    db_session.add(lunch_chicken)
    db_session.add(lunch_rice)
    db_session.add(lunch_tomato)
    
    # Create meal template
    template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        generation_reason="Test template"
    )
    db_session.add(template)
    await db_session.flush()
    
    # Create template meals (primary dishes only for 7 days)
    for day in range(7):
        # Breakfast
        breakfast_meal = TemplateMeal(
            id=uuid4(),
            template_id=template.id,
            meal_schedule_id=breakfast_schedule.id,
            dish_id=breakfast_dish.id,
            day_of_week=day,
            is_primary=True,
            alternative_order=1
        )
        db_session.add(breakfast_meal)
        
        # Lunch
        lunch_meal = TemplateMeal(
            id=uuid4(),
            template_id=template.id,
            meal_schedule_id=lunch_schedule.id,
            dish_id=lunch_dish.id,
            day_of_week=day,
            is_primary=True,
            alternative_order=1
        )
        db_session.add(lunch_meal)
    
    await db_session.commit()
    await db_session.refresh(profile)
    
    return profile


@pytest.mark.asyncio
async def test_generate_shopping_list_basic(
    db_session: AsyncSession,
    test_user_with_template: UserProfile
):
    """Test basic shopping list generation."""
    service = ShoppingListService(db_session)
    
    # Generate shopping list for 1 week
    shopping_list = await service.generate_shopping_list(
        profile_id=test_user_with_template.id,
        weeks=1
    )
    
    # Verify response structure
    assert shopping_list is not None
    assert shopping_list.week_number == 1
    assert shopping_list.start_date is not None
    assert shopping_list.end_date is not None
    assert len(shopping_list.categories) > 0
    assert shopping_list.total_items > 0
    
    # Verify categories are present
    category_names = [cat.category for cat in shopping_list.categories]
    assert "protein" in category_names
    assert "grain" in category_names
    assert "vegetable" in category_names
    
    # Find chicken ingredient
    protein_category = next(cat for cat in shopping_list.categories if cat.category == "protein")
    chicken_ingredient = next(
        ing for ing in protein_category.ingredients
        if ing.name == "chicken_breast"
    )
    
    # Verify chicken quantity
    # Breakfast: 100g × 7 days = 700g
    # Lunch: 150g × 7 days = 1050g
    # Total: 1750g
    assert chicken_ingredient.total_quantity == Decimal("1750")
    assert chicken_ingredient.unit == "g"
    assert len(chicken_ingredient.used_in_dishes) == 2
    assert "Chicken Omelette" in chicken_ingredient.used_in_dishes
    assert "Chicken Rice Bowl" in chicken_ingredient.used_in_dishes


@pytest.mark.asyncio
async def test_generate_shopping_list_multiple_weeks(
    db_session: AsyncSession,
    test_user_with_template: UserProfile
):
    """Test shopping list generation for multiple weeks."""
    service = ShoppingListService(db_session)
    
    # Generate shopping list for 2 weeks
    shopping_list = await service.generate_shopping_list(
        profile_id=test_user_with_template.id,
        weeks=2
    )
    
    # Find chicken ingredient
    protein_category = next(cat for cat in shopping_list.categories if cat.category == "protein")
    chicken_ingredient = next(
        ing for ing in protein_category.ingredients
        if ing.name == "chicken_breast"
    )
    
    # Verify chicken quantity for 2 weeks
    # (100g + 150g) × 7 days × 2 weeks = 3500g
    assert chicken_ingredient.total_quantity == Decimal("3500")


@pytest.mark.asyncio
async def test_generate_shopping_list_invalid_weeks(
    db_session: AsyncSession,
    test_user_with_template: UserProfile
):
    """Test that invalid weeks parameter raises error."""
    from fastapi import HTTPException
    
    service = ShoppingListService(db_session)
    
    # Test weeks < 1
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(
            profile_id=test_user_with_template.id,
            weeks=0
        )
    assert exc_info.value.status_code == 400
    
    # Test weeks > 4
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(
            profile_id=test_user_with_template.id,
            weeks=5
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_generate_shopping_list_no_template(
    db_session: AsyncSession
):
    """Test that missing template raises error."""
    from fastapi import HTTPException
    
    service = ShoppingListService(db_session)
    
    # Use non-existent profile ID
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(
            profile_id=uuid4(),
            weeks=1
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_category_ordering(
    db_session: AsyncSession,
    test_user_with_template: UserProfile
):
    """Test that categories are ordered correctly."""
    service = ShoppingListService(db_session)
    
    shopping_list = await service.generate_shopping_list(
        profile_id=test_user_with_template.id,
        weeks=1
    )
    
    # Verify category order follows CATEGORY_ORDER
    category_names = [cat.category for cat in shopping_list.categories]
    
    # Expected order: protein, vegetable, fruit, grain, dairy, spice, oil, other
    # We should have: protein, vegetable, grain (in that order)
    expected_order = ["protein", "vegetable", "grain"]
    actual_order = [name for name in expected_order if name in category_names]
    
    # Verify the categories appear in the correct order
    for i, expected_cat in enumerate(actual_order):
        actual_index = category_names.index(expected_cat)
        assert actual_index == i

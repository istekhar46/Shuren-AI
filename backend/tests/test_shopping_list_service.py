"""Unit tests for ShoppingListService."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.shopping_list_service import ShoppingListService
from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealSchedule
from app.models.profile import UserProfile
from app.models.user import User
from app.core.security import hash_password
from datetime import time


@pytest_asyncio.fixture
async def test_user_with_profile(db_session: AsyncSession):
    """Create a test user with profile."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level="intermediate"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest_asyncio.fixture
async def sample_ingredients(db_session: AsyncSession):
    """Create sample ingredients for testing."""
    ingredients = []
    
    ingredient_data = [
        {"name": "chicken_breast", "category": "protein", "allergen_type": None},
        {"name": "rice", "category": "grain", "allergen_type": None},
        {"name": "tomato", "category": "vegetable", "allergen_type": None},
        {"name": "onion", "category": "vegetable", "allergen_type": None},
        {"name": "olive_oil", "category": "oil", "allergen_type": None},
        {"name": "cumin", "category": "spice", "allergen_type": None},
        {"name": "paneer", "category": "dairy", "allergen_type": "dairy"},
        {"name": "spinach", "category": "vegetable", "allergen_type": None},
    ]
    
    for data in ingredient_data:
        ingredient = Ingredient(
            id=uuid4(),
            name=data["name"],
            name_hindi=f"{data['name']}_hindi",
            category=data["category"],
            typical_unit="g",
            is_allergen=data["allergen_type"] is not None,
            allergen_type=data["allergen_type"],
            is_active=True
        )
        db_session.add(ingredient)
        ingredients.append(ingredient)
    
    await db_session.commit()
    return ingredients


@pytest_asyncio.fixture
async def sample_dishes_with_ingredients(db_session: AsyncSession, sample_ingredients: list):
    """Create sample dishes with ingredients."""
    dishes = []
    
    # Dish 1: Chicken Rice Bowl
    dish1 = Dish(
        id=uuid4(),
        name="Chicken Rice Bowl",
        cuisine_type="north_indian",
        meal_type="lunch",
        serving_size_g=400,
        calories=Decimal("600"),
        protein_g=Decimal("45"),
        carbs_g=Decimal("60"),
        fats_g=Decimal("15"),
        prep_time_minutes=10,
        cook_time_minutes=20,
        difficulty_level="easy",
        is_vegetarian=False,
        is_vegan=False,
        is_active=True,
        popularity_score=100
    )
    db_session.add(dish1)
    dishes.append(dish1)
    
    # Add ingredients to dish1
    dish1_ingredients = [
        DishIngredient(
            id=uuid4(),
            dish_id=dish1.id,
            ingredient_id=sample_ingredients[0].id,  # chicken_breast
            quantity=Decimal("200"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish1.id,
            ingredient_id=sample_ingredients[1].id,  # rice
            quantity=Decimal("150"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish1.id,
            ingredient_id=sample_ingredients[2].id,  # tomato
            quantity=Decimal("50"),
            unit="g",
            is_optional=False
        ),
    ]
    for di in dish1_ingredients:
        db_session.add(di)
    
    # Dish 2: Vegetable Curry
    dish2 = Dish(
        id=uuid4(),
        name="Vegetable Curry",
        cuisine_type="north_indian",
        meal_type="dinner",
        serving_size_g=350,
        calories=Decimal("400"),
        protein_g=Decimal("15"),
        carbs_g=Decimal("50"),
        fats_g=Decimal("18"),
        prep_time_minutes=15,
        cook_time_minutes=25,
        difficulty_level="medium",
        is_vegetarian=True,
        is_vegan=True,
        is_active=True,
        popularity_score=95
    )
    db_session.add(dish2)
    dishes.append(dish2)
    
    # Add ingredients to dish2
    dish2_ingredients = [
        DishIngredient(
            id=uuid4(),
            dish_id=dish2.id,
            ingredient_id=sample_ingredients[2].id,  # tomato (shared with dish1)
            quantity=Decimal("100"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish2.id,
            ingredient_id=sample_ingredients[3].id,  # onion
            quantity=Decimal("80"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish2.id,
            ingredient_id=sample_ingredients[4].id,  # olive_oil
            quantity=Decimal("20"),
            unit="ml",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish2.id,
            ingredient_id=sample_ingredients[5].id,  # cumin
            quantity=Decimal("5"),
            unit="g",
            is_optional=True
        ),
    ]
    for di in dish2_ingredients:
        db_session.add(di)
    
    # Dish 3: Paneer Spinach
    dish3 = Dish(
        id=uuid4(),
        name="Paneer Spinach",
        cuisine_type="north_indian",
        meal_type="dinner",
        serving_size_g=300,
        calories=Decimal("450"),
        protein_g=Decimal("25"),
        carbs_g=Decimal("30"),
        fats_g=Decimal("25"),
        prep_time_minutes=10,
        cook_time_minutes=15,
        difficulty_level="easy",
        is_vegetarian=True,
        is_vegan=False,
        is_active=True,
        popularity_score=90
    )
    db_session.add(dish3)
    dishes.append(dish3)
    
    # Add ingredients to dish3
    dish3_ingredients = [
        DishIngredient(
            id=uuid4(),
            dish_id=dish3.id,
            ingredient_id=sample_ingredients[6].id,  # paneer
            quantity=Decimal("150"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish3.id,
            ingredient_id=sample_ingredients[7].id,  # spinach
            quantity=Decimal("200"),
            unit="g",
            is_optional=False
        ),
        DishIngredient(
            id=uuid4(),
            dish_id=dish3.id,
            ingredient_id=sample_ingredients[3].id,  # onion (shared)
            quantity=Decimal("50"),
            unit="g",
            is_optional=False
        ),
    ]
    for di in dish3_ingredients:
        db_session.add(di)
    
    await db_session.commit()
    
    # Refresh to load relationships
    for dish in dishes:
        await db_session.refresh(dish)
    
    return dishes


@pytest_asyncio.fixture
async def meal_template_with_dishes(
    db_session: AsyncSession,
    test_user_with_profile,
    sample_dishes_with_ingredients
):
    """Create a meal template with dishes assigned."""
    user, profile = test_user_with_profile
    dishes = sample_dishes_with_ingredients
    
    # Determine current week number
    week_of_year = date.today().isocalendar()[1]
    current_week = ((week_of_year - 1) % 4) + 1
    
    # Create meal schedule for the profile
    meal_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True
    )
    db_session.add(meal_schedule)
    await db_session.commit()
    await db_session.refresh(meal_schedule)
    
    # Create meal template
    template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=current_week,
        is_active=True,
        generated_by="system"
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    
    # Create template meals (primary dishes for 7 days)
    # Day 0: Chicken Rice Bowl
    # Day 1: Vegetable Curry
    # Day 2: Chicken Rice Bowl
    # Day 3: Paneer Spinach
    # Day 4: Vegetable Curry
    # Day 5: Chicken Rice Bowl
    # Day 6: Paneer Spinach
    
    meal_assignments = [
        (0, dishes[0]),  # Monday: Chicken Rice Bowl
        (1, dishes[1]),  # Tuesday: Vegetable Curry
        (2, dishes[0]),  # Wednesday: Chicken Rice Bowl
        (3, dishes[2]),  # Thursday: Paneer Spinach
        (4, dishes[1]),  # Friday: Vegetable Curry
        (5, dishes[0]),  # Saturday: Chicken Rice Bowl
        (6, dishes[2]),  # Sunday: Paneer Spinach
    ]
    
    for day_of_week, dish in meal_assignments:
        template_meal = TemplateMeal(
            id=uuid4(),
            template_id=template.id,
            meal_schedule_id=meal_schedule.id,  # Use the created meal schedule
            dish_id=dish.id,
            day_of_week=day_of_week,
            is_primary=True,
            alternative_order=1
        )
        db_session.add(template_meal)
    
    await db_session.commit()
    await db_session.refresh(template)
    
    return template, profile


@pytest.mark.asyncio
async def test_generate_shopping_list_one_week(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test generating shopping list for one week."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Verify response structure
    assert result.week_number == template.week_number
    assert result.start_date == date.today().isoformat()
    assert result.end_date == (date.today() + timedelta(days=6)).isoformat()
    assert len(result.categories) > 0
    assert result.total_items > 0
    
    # Verify categories are present
    category_names = [cat.category for cat in result.categories]
    assert "protein" in category_names
    assert "vegetable" in category_names
    assert "grain" in category_names


@pytest.mark.asyncio
async def test_generate_shopping_list_multiple_weeks(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test generating shopping list for multiple weeks."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=2)
    
    # Verify date range
    assert result.end_date == (date.today() + timedelta(days=13)).isoformat()
    
    # Find chicken_breast ingredient
    chicken_found = False
    for category in result.categories:
        if category.category == "protein":
            for ingredient in category.ingredients:
                if ingredient.name == "chicken_breast":
                    chicken_found = True
                    # Chicken appears 3 times per week (days 0, 2, 5)
                    # 200g per serving × 3 days × 2 weeks = 1200g
                    assert ingredient.total_quantity == Decimal("1200")
                    assert ingredient.unit == "g"
    
    assert chicken_found, "Chicken breast should be in the shopping list"


@pytest.mark.asyncio
async def test_ingredient_aggregation(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that ingredients are properly aggregated across dishes."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Find tomato ingredient (used in both Chicken Rice Bowl and Vegetable Curry)
    tomato_found = False
    for category in result.categories:
        if category.category == "vegetable":
            for ingredient in category.ingredients:
                if ingredient.name == "tomato":
                    tomato_found = True
                    # Chicken Rice Bowl: 50g × 3 times = 150g
                    # Vegetable Curry: 100g × 2 times = 200g
                    # Total: 350g
                    assert ingredient.total_quantity == Decimal("350")
                    assert len(ingredient.used_in_dishes) == 2
                    assert "Chicken Rice Bowl" in ingredient.used_in_dishes
                    assert "Vegetable Curry" in ingredient.used_in_dishes
    
    assert tomato_found, "Tomato should be aggregated from multiple dishes"


@pytest.mark.asyncio
async def test_category_grouping(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that ingredients are grouped by category."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Verify categories follow the predefined order
    category_names = [cat.category for cat in result.categories]
    
    # Check that categories appear in the correct order
    expected_order = ["protein", "vegetable", "grain", "dairy", "spice", "oil"]
    actual_order = [cat for cat in expected_order if cat in category_names]
    
    # Verify the order matches
    for i, expected_cat in enumerate(actual_order):
        assert category_names[i] == expected_cat
    
    # Verify each category has ingredients
    for category in result.categories:
        assert len(category.ingredients) > 0
        # Verify all ingredients in category have the same category
        for ingredient in category.ingredients:
            assert ingredient.category == category.category


@pytest.mark.asyncio
async def test_quantity_calculations(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that quantities are calculated correctly."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Find onion ingredient (used in Vegetable Curry and Paneer Spinach)
    onion_found = False
    for category in result.categories:
        if category.category == "vegetable":
            for ingredient in category.ingredients:
                if ingredient.name == "onion":
                    onion_found = True
                    # Vegetable Curry: 80g × 2 times = 160g
                    # Paneer Spinach: 50g × 2 times = 100g
                    # Total: 260g
                    assert ingredient.total_quantity == Decimal("260")
    
    assert onion_found, "Onion should be in the shopping list"


@pytest.mark.asyncio
async def test_optional_ingredients_marked(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that optional ingredients are marked correctly."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Find cumin ingredient (marked as optional in Vegetable Curry)
    cumin_found = False
    for category in result.categories:
        if category.category == "spice":
            for ingredient in category.ingredients:
                if ingredient.name == "cumin":
                    cumin_found = True
                    assert ingredient.is_optional is True
    
    assert cumin_found, "Cumin should be in the shopping list and marked as optional"


@pytest.mark.asyncio
async def test_no_active_template_raises_error(
    db_session: AsyncSession,
    test_user_with_profile
):
    """Test that error is raised when no active template exists."""
    user, profile = test_user_with_profile
    
    service = ShoppingListService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(profile.id, weeks=1)
    
    assert exc_info.value.status_code == 404
    assert "No active meal template found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_invalid_weeks_parameter(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that invalid weeks parameter raises error."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    
    # Test weeks < 1
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(profile.id, weeks=0)
    
    assert exc_info.value.status_code == 400
    assert "Weeks must be between 1 and 4" in exc_info.value.detail
    
    # Test weeks > 4
    with pytest.raises(HTTPException) as exc_info:
        await service.generate_shopping_list(profile.id, weeks=5)
    
    assert exc_info.value.status_code == 400
    assert "Weeks must be between 1 and 4" in exc_info.value.detail


@pytest.mark.asyncio
async def test_ingredients_sorted_alphabetically_within_category(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that ingredients are sorted alphabetically within each category."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Check that ingredients within each category are sorted
    for category in result.categories:
        ingredient_names = [ing.name for ing in category.ingredients]
        sorted_names = sorted(ingredient_names)
        assert ingredient_names == sorted_names, f"Ingredients in {category.category} should be sorted alphabetically"


@pytest.mark.asyncio
async def test_total_items_count(
    db_session: AsyncSession,
    meal_template_with_dishes
):
    """Test that total_items count is accurate."""
    template, profile = meal_template_with_dishes
    
    service = ShoppingListService(db_session)
    result = await service.generate_shopping_list(profile.id, weeks=1)
    
    # Count ingredients manually
    manual_count = sum(len(cat.ingredients) for cat in result.categories)
    
    assert result.total_items == manual_count
    assert result.total_items > 0

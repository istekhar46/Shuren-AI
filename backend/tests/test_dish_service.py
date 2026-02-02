"""Unit tests for DishService."""

import pytest
import pytest_asyncio
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dish_service import DishService
from app.models.dish import Dish, Ingredient, DishIngredient


@pytest_asyncio.fixture
async def sample_ingredients(db_session: AsyncSession):
    """Create sample ingredients for testing."""
    ingredients = []
    
    # Create various ingredients
    ingredient_data = [
        {"name": "eggs", "category": "protein", "allergen_type": "eggs"},
        {"name": "chicken_breast", "category": "protein", "allergen_type": None},
        {"name": "paneer", "category": "dairy", "allergen_type": "dairy"},
        {"name": "rice", "category": "grain", "allergen_type": None},
        {"name": "wheat_flour", "category": "grain", "allergen_type": "wheat"},
        {"name": "peanuts", "category": "protein", "allergen_type": "peanuts"},
        {"name": "spinach", "category": "vegetable", "allergen_type": None},
        {"name": "tomato", "category": "vegetable", "allergen_type": None},
    ]
    
    for data in ingredient_data:
        ingredient = Ingredient(
            id=uuid4(),
            name=data["name"],
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
async def sample_dishes(db_session: AsyncSession, sample_ingredients: list):
    """Create sample dishes for testing."""
    dishes = []
    
    # Breakfast dishes
    breakfast_dishes = [
        {
            "name": "Egg Omelette",
            "meal_type": "breakfast",
            "calories": 350,
            "protein_g": 25,
            "is_vegetarian": True,
            "is_vegan": False,
            "contains_allergens": ["eggs"],
            "prep_time": 5,
            "cook_time": 10,
        },
        {
            "name": "Paneer Paratha",
            "meal_type": "breakfast",
            "calories": 450,
            "protein_g": 20,
            "is_vegetarian": True,
            "is_vegan": False,
            "contains_allergens": ["dairy", "wheat"],
            "prep_time": 15,
            "cook_time": 15,
        },
        {
            "name": "Oats Porridge",
            "meal_type": "breakfast",
            "calories": 300,
            "protein_g": 15,
            "is_vegetarian": True,
            "is_vegan": True,
            "contains_allergens": [],
            "prep_time": 5,
            "cook_time": 5,
        },
    ]
    
    for i, data in enumerate(breakfast_dishes):
        dish = Dish(
            id=uuid4(),
            name=data["name"],
            cuisine_type="north_indian",
            meal_type=data["meal_type"],
            serving_size_g=300,
            calories=Decimal(str(data["calories"])),
            protein_g=Decimal(str(data["protein_g"])),
            carbs_g=Decimal("40"),
            fats_g=Decimal("15"),
            prep_time_minutes=data["prep_time"],
            cook_time_minutes=data["cook_time"],
            difficulty_level="easy",
            is_vegetarian=data["is_vegetarian"],
            is_vegan=data["is_vegan"],
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=data["contains_allergens"],
            is_active=True,
            popularity_score=100 - i
        )
        db_session.add(dish)
        dishes.append(dish)
    
    # Lunch dishes
    lunch_dishes = [
        {
            "name": "Chicken Curry with Rice",
            "meal_type": "lunch",
            "calories": 600,
            "protein_g": 45,
            "is_vegetarian": False,
            "is_vegan": False,
            "contains_allergens": [],
            "prep_time": 15,
            "cook_time": 30,
        },
        {
            "name": "Dal Tadka with Roti",
            "meal_type": "lunch",
            "calories": 500,
            "protein_g": 20,
            "is_vegetarian": True,
            "is_vegan": True,
            "contains_allergens": ["wheat"],
            "prep_time": 10,
            "cook_time": 25,
        },
    ]
    
    for i, data in enumerate(lunch_dishes):
        dish = Dish(
            id=uuid4(),
            name=data["name"],
            cuisine_type="north_indian",
            meal_type=data["meal_type"],
            serving_size_g=400,
            calories=Decimal(str(data["calories"])),
            protein_g=Decimal(str(data["protein_g"])),
            carbs_g=Decimal("60"),
            fats_g=Decimal("20"),
            prep_time_minutes=data["prep_time"],
            cook_time_minutes=data["cook_time"],
            difficulty_level="medium",
            is_vegetarian=data["is_vegetarian"],
            is_vegan=data["is_vegan"],
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=data["contains_allergens"],
            is_active=True,
            popularity_score=100 - i
        )
        db_session.add(dish)
        dishes.append(dish)
    
    # Snack with peanuts
    snack_dish = Dish(
        id=uuid4(),
        name="Peanut Butter Sandwich",
        cuisine_type="continental",
        meal_type="snack",
        serving_size_g=150,
        calories=Decimal("400"),
        protein_g=Decimal("18"),
        carbs_g=Decimal("35"),
        fats_g=Decimal("22"),
        prep_time_minutes=5,
        cook_time_minutes=0,
        difficulty_level="easy",
        is_vegetarian=True,
        is_vegan=False,
        is_gluten_free=False,
        is_dairy_free=True,
        is_nut_free=False,
        contains_allergens=["peanuts", "wheat"],
        is_active=True,
        popularity_score=80
    )
    db_session.add(snack_dish)
    dishes.append(snack_dish)
    
    await db_session.commit()
    
    # Add ingredients to first breakfast dish
    eggs_ingredient = next(i for i in sample_ingredients if i.name == "eggs")
    dish_ingredient = DishIngredient(
        id=uuid4(),
        dish_id=dishes[0].id,
        ingredient_id=eggs_ingredient.id,
        quantity=Decimal("3"),
        unit="piece",
        is_optional=False
    )
    db_session.add(dish_ingredient)
    await db_session.commit()
    
    return dishes


@pytest.mark.asyncio
async def test_get_dish_without_ingredients(db_session: AsyncSession, sample_dishes: list):
    """Test get_dish() without loading ingredients."""
    service = DishService(db_session)
    dish = sample_dishes[0]
    
    result = await service.get_dish(dish.id, include_ingredients=False)
    
    assert result is not None
    assert result.id == dish.id
    assert result.name == dish.name
    assert result.calories == dish.calories


@pytest.mark.asyncio
async def test_get_dish_with_ingredients(db_session: AsyncSession, sample_dishes: list):
    """Test get_dish() with ingredients loaded."""
    service = DishService(db_session)
    dish = sample_dishes[0]  # Egg Omelette with ingredients
    
    result = await service.get_dish(dish.id, include_ingredients=True)
    
    assert result is not None
    assert result.id == dish.id
    assert len(result.dish_ingredients) > 0
    assert result.dish_ingredients[0].ingredient.name == "eggs"
    assert result.dish_ingredients[0].quantity == Decimal("3")


@pytest.mark.asyncio
async def test_get_dish_not_found(db_session: AsyncSession):
    """Test get_dish() with non-existent dish ID."""
    service = DishService(db_session)
    
    result = await service.get_dish(uuid4())
    
    assert result is None


@pytest.mark.asyncio
async def test_search_dishes_no_filters(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() without any filters."""
    service = DishService(db_session)
    
    results = await service.search_dishes()
    
    assert len(results) == len(sample_dishes)
    # Should be ordered by popularity_score desc
    assert results[0].popularity_score >= results[-1].popularity_score


@pytest.mark.asyncio
async def test_search_dishes_by_meal_type(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() filtered by meal type."""
    service = DishService(db_session)
    
    results = await service.search_dishes(meal_type="breakfast")
    
    assert len(results) == 3
    assert all(dish.meal_type == "breakfast" for dish in results)


@pytest.mark.asyncio
async def test_search_dishes_vegetarian(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() filtered by vegetarian diet."""
    service = DishService(db_session)
    
    results = await service.search_dishes(diet_type="vegetarian")
    
    assert len(results) > 0
    assert all(dish.is_vegetarian for dish in results)


@pytest.mark.asyncio
async def test_search_dishes_vegan(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() filtered by vegan diet."""
    service = DishService(db_session)
    
    results = await service.search_dishes(diet_type="vegan")
    
    assert len(results) > 0
    assert all(dish.is_vegan for dish in results)
    # Vegan dishes should also be vegetarian
    assert all(dish.is_vegetarian for dish in results)


@pytest.mark.asyncio
async def test_search_dishes_max_prep_time(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() filtered by maximum preparation time."""
    service = DishService(db_session)
    
    results = await service.search_dishes(max_prep_time=15)
    
    assert len(results) > 0
    assert all(
        (dish.prep_time_minutes + dish.cook_time_minutes) <= 15
        for dish in results
    )


@pytest.mark.asyncio
async def test_search_dishes_max_calories(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() filtered by maximum calories."""
    service = DishService(db_session)
    
    results = await service.search_dishes(max_calories=400)
    
    assert len(results) > 0
    assert all(dish.calories <= 400 for dish in results)


@pytest.mark.asyncio
async def test_search_dishes_exclude_allergens(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() with allergen exclusion."""
    service = DishService(db_session)
    
    results = await service.search_dishes(exclude_allergens=["eggs"])
    
    assert len(results) > 0
    assert all("eggs" not in dish.contains_allergens for dish in results)


@pytest.mark.asyncio
async def test_search_dishes_exclude_multiple_allergens(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() excluding multiple allergens."""
    service = DishService(db_session)
    
    results = await service.search_dishes(exclude_allergens=["eggs", "dairy"])
    
    assert len(results) > 0
    for dish in results:
        assert "eggs" not in dish.contains_allergens
        assert "dairy" not in dish.contains_allergens


@pytest.mark.asyncio
async def test_search_dishes_combined_filters(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() with multiple filters combined."""
    service = DishService(db_session)
    
    results = await service.search_dishes(
        meal_type="breakfast",
        diet_type="vegetarian",
        max_calories=400,
        exclude_allergens=["eggs"]
    )
    
    assert len(results) > 0
    for dish in results:
        assert dish.meal_type == "breakfast"
        assert dish.is_vegetarian is True
        assert dish.calories <= 400
        assert "eggs" not in dish.contains_allergens


@pytest.mark.asyncio
async def test_search_dishes_pagination(db_session: AsyncSession, sample_dishes: list):
    """Test search_dishes() with pagination."""
    service = DishService(db_session)
    
    # Get first page
    page1 = await service.search_dishes(limit=2, offset=0)
    assert len(page1) == 2
    
    # Get second page
    page2 = await service.search_dishes(limit=2, offset=2)
    assert len(page2) == 2
    
    # Ensure different results
    assert page1[0].id != page2[0].id


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_basic(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() with basic parameters."""
    service = DishService(db_session)
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=350,
        target_protein=25,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    assert len(results) <= 3
    assert all(dish.meal_type == "breakfast" for dish in results)


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_calorie_range(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() respects calorie range (±15%)."""
    service = DishService(db_session)
    
    target_calories = 350
    cal_min = target_calories * 0.85  # 297.5
    cal_max = target_calories * 1.15  # 402.5
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=target_calories,
        target_protein=25,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    for dish in results:
        assert cal_min <= float(dish.calories) <= cal_max


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_protein_range(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() respects protein range (±20%)."""
    service = DishService(db_session)
    
    target_protein = 25
    protein_min = target_protein * 0.80  # 20
    protein_max = target_protein * 1.20  # 30
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=350,
        target_protein=target_protein,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    for dish in results:
        assert protein_min <= float(dish.protein_g) <= protein_max


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_vegetarian(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() with vegetarian preference."""
    service = DishService(db_session)
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=350,
        target_protein=25,
        dietary_preferences={"diet_type": "vegetarian", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    assert all(dish.is_vegetarian for dish in results)


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_vegan(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() with vegan preference."""
    service = DishService(db_session)
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=300,
        target_protein=15,
        dietary_preferences={"diet_type": "vegan", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    assert all(dish.is_vegan for dish in results)


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_exclude_allergies(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() excludes allergens."""
    service = DishService(db_session)
    
    # Use wider ranges to ensure we get results
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=400,  # Wider range to include more dishes
        target_protein=20,    # Wider range to include more dishes
        dietary_preferences={"diet_type": "omnivore", "allergies": ["eggs"]},
        count=3
    )
    
    # Should get dishes without eggs (Paneer Paratha and Oats Porridge)
    assert len(results) > 0
    for dish in results:
        assert "eggs" not in dish.contains_allergens


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_ordered_by_popularity(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() returns dishes ordered by popularity."""
    service = DishService(db_session)
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=350,
        target_protein=25,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=3
    )
    
    assert len(results) > 0
    # Check that results are ordered by popularity_score descending
    for i in range(len(results) - 1):
        assert results[i].popularity_score >= results[i + 1].popularity_score


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_respects_count(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() respects count parameter."""
    service = DishService(db_session)
    
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=350,
        target_protein=25,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=2
    )
    
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_get_dishes_for_meal_slot_no_matches(db_session: AsyncSession, sample_dishes: list):
    """Test get_dishes_for_meal_slot() when no dishes match criteria."""
    service = DishService(db_session)
    
    # Request impossible criteria
    results = await service.get_dishes_for_meal_slot(
        meal_type="breakfast",
        target_calories=50,  # Too low, no dishes will match
        target_protein=5,
        dietary_preferences={"diet_type": "omnivore", "allergies": []},
        count=3
    )
    
    assert len(results) == 0

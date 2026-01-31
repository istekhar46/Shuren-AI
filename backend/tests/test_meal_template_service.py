"""Tests for meal template service."""

import pytest
import pytest_asyncio
from datetime import time
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.preferences import MealPlan, MealSchedule, DietaryPreference
from app.models.profile import UserProfile
from app.models.user import User
from app.services.meal_template_service import MealTemplateService
from app.core.security import hash_password


@pytest_asyncio.fixture
async def test_user_with_meal_plan(db_session: AsyncSession):
    """Create a test user with meal plan and schedules."""
    # Create user
    user = User(
        id=uuid4(),
        email="mealtest@example.com",
        hashed_password=hash_password("password123"),
        full_name="Meal Test User",
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
    schedules = [
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Lunch",
            scheduled_time=time(13, 0),
            enable_notifications=True
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Dinner",
            scheduled_time=time(19, 0),
            enable_notifications=True
        )
    ]
    for schedule in schedules:
        db_session.add(schedule)
    
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
    
    await db_session.commit()
    await db_session.refresh(profile)
    
    return profile


@pytest_asyncio.fixture
async def sample_dishes(db_session: AsyncSession):
    """Create sample dishes for testing.
    
    Creates dishes that match the meal plan targets:
    - Daily calories: 2000
    - Breakfast (30%): 600 cal, 45g protein
    - Lunch (35%): 700 cal, 45g protein
    - Dinner (30%): 600 cal, 37.5g protein
    """
    dishes = []
    
    # Create breakfast dishes (target: 600 cal, 45g protein)
    # Acceptable range: 510-690 cal, 36-54g protein
    for i in range(3):
        dish = Dish(
            id=uuid4(),
            name=f"Breakfast Dish {i+1}",
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
            is_vegetarian=True,
            is_vegan=False,
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=[],
            is_active=True,
            popularity_score=100 - i
        )
        db_session.add(dish)
        dishes.append(dish)
    
    # Create lunch dishes (target: 700 cal, 45g protein)
    # Acceptable range: 595-805 cal, 36-54g protein
    for i in range(3):
        dish = Dish(
            id=uuid4(),
            name=f"Lunch Dish {i+1}",
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
            is_vegetarian=True,
            is_vegan=False,
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=[],
            is_active=True,
            popularity_score=100 - i
        )
        db_session.add(dish)
        dishes.append(dish)
    
    # Create dinner dishes (target: 600 cal, 37.5g protein)
    # Acceptable range: 510-690 cal, 30-45g protein
    for i in range(3):
        dish = Dish(
            id=uuid4(),
            name=f"Dinner Dish {i+1}",
            cuisine_type="north_indian",
            meal_type="dinner",
            serving_size_g=400,
            calories=600,
            protein_g=38,
            carbs_g=65,
            fats_g=18,
            prep_time_minutes=15,
            cook_time_minutes=25,
            difficulty_level="medium",
            is_vegetarian=True,
            is_vegan=False,
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=[],
            is_active=True,
            popularity_score=100 - i
        )
        db_session.add(dish)
        dishes.append(dish)
    
    await db_session.commit()
    
    return dishes


@pytest.mark.asyncio
async def test_generate_template_basic(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test basic template generation."""
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.meal_template import MealTemplate, TemplateMeal
    
    service = MealTemplateService(db_session)
    
    # Generate template
    template = await service.generate_template(
        profile_id=test_user_with_meal_plan.id,
        week_number=1,
        preferences="Test template generation"
    )
    
    # Verify template was created
    assert template is not None
    assert template.profile_id == test_user_with_meal_plan.id
    assert template.week_number == 1
    assert template.is_active is True
    assert template.generated_by == "ai_agent"
    assert template.generation_reason == "Test template generation"
    
    # Reload template with relationships
    result = await db_session.execute(
        select(MealTemplate)
        .where(MealTemplate.id == template.id)
        .options(
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.dish),
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.meal_schedule)
        )
    )
    template = result.scalar_one()
    
    # Verify template meals were created
    # 7 days × 3 meals × 3 dishes (1 primary + 2 alternatives) = 63 template meals
    assert len(template.template_meals) == 63
    
    # Verify each day has meals
    for day in range(7):
        day_meals = [tm for tm in template.template_meals if tm.day_of_week == day]
        assert len(day_meals) == 9  # 3 meals × 3 dishes each
        
        # Verify each meal has 1 primary and 2 alternatives
        for schedule in test_user_with_meal_plan.meal_schedules:
            schedule_meals = [
                tm for tm in day_meals
                if tm.meal_schedule_id == schedule.id
            ]
            assert len(schedule_meals) == 3
            
            primary_meals = [tm for tm in schedule_meals if tm.is_primary]
            alternative_meals = [tm for tm in schedule_meals if not tm.is_primary]
            
            assert len(primary_meals) == 1
            assert len(alternative_meals) == 2


@pytest.mark.asyncio
async def test_generate_template_locked_profile(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test that template generation fails when profile is locked."""
    from app.core.exceptions import ProfileLockedException
    
    # Lock the profile
    test_user_with_meal_plan.is_locked = True
    await db_session.commit()
    
    service = MealTemplateService(db_session)
    
    # Attempt to generate template should raise exception
    with pytest.raises(ProfileLockedException):
        await service.generate_template(
            profile_id=test_user_with_meal_plan.id,
            week_number=1
        )


@pytest.mark.asyncio
async def test_determine_meal_type(db_session: AsyncSession):
    """Test meal type determination from meal name."""
    service = MealTemplateService(db_session)
    
    assert service._determine_meal_type("Breakfast") == "breakfast"
    assert service._determine_meal_type("Lunch") == "lunch"
    assert service._determine_meal_type("Dinner") == "dinner"
    assert service._determine_meal_type("Pre-workout Snack") == "pre_workout"
    assert service._determine_meal_type("Post-workout Meal") == "post_workout"
    assert service._determine_meal_type("Evening Snack") == "snack"


@pytest.mark.asyncio
async def test_calculate_meal_targets(db_session: AsyncSession):
    """Test meal target calculations."""
    service = MealTemplateService(db_session)
    
    daily_calories = 2000
    daily_protein = 150.0  # grams
    meals_per_day = 3
    
    # Test breakfast
    cal_target, protein_target = service._calculate_meal_targets(
        "Breakfast",
        daily_calories,
        daily_protein,
        meals_per_day
    )
    assert cal_target == 600.0  # 30% of 2000
    assert protein_target == 45.0  # 30% of 150
    
    # Test lunch
    cal_target, protein_target = service._calculate_meal_targets(
        "Lunch",
        daily_calories,
        daily_protein,
        meals_per_day
    )
    assert cal_target == 700.0  # 35% of 2000
    assert protein_target == 45.0  # 30% of 150
    
    # Test dinner
    cal_target, protein_target = service._calculate_meal_targets(
        "Dinner",
        daily_calories,
        daily_protein,
        meals_per_day
    )
    assert cal_target == 600.0  # 30% of 2000
    assert protein_target == 37.5  # 25% of 150



@pytest.mark.asyncio
async def test_swap_dish_basic(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test basic dish swapping functionality."""
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.meal_template import MealTemplate, TemplateMeal
    
    service = MealTemplateService(db_session)
    
    # Generate template first
    template = await service.generate_template(
        profile_id=test_user_with_meal_plan.id,
        week_number=1,
        preferences="Test template"
    )
    
    # Reload template with relationships
    result = await db_session.execute(
        select(MealTemplate)
        .where(MealTemplate.id == template.id)
        .options(
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.dish),
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.meal_schedule)
        )
    )
    template = result.scalar_one()
    
    # Find the primary breakfast dish for Monday (day 0)
    monday_breakfast = next(
        tm for tm in template.template_meals
        if tm.day_of_week == 0
        and tm.meal_schedule.meal_name == "Breakfast"
        and tm.is_primary
    )
    original_dish_id = monday_breakfast.dish_id
    
    # Get a different breakfast dish to swap to
    new_dish = next(
        d for d in sample_dishes
        if d.meal_type == "breakfast" and d.id != original_dish_id
    )
    
    # Swap the dish
    updated_template = await service.swap_dish(
        profile_id=test_user_with_meal_plan.id,
        day_of_week=0,
        meal_name="Breakfast",
        new_dish_id=new_dish.id
    )
    
    # Reload template to verify change
    result = await db_session.execute(
        select(MealTemplate)
        .where(MealTemplate.id == template.id)
        .options(
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.dish),
            selectinload(MealTemplate.template_meals)
            .selectinload(TemplateMeal.meal_schedule)
        )
    )
    updated_template = result.scalar_one()
    
    # Find the updated breakfast meal
    updated_breakfast = next(
        tm for tm in updated_template.template_meals
        if tm.day_of_week == 0
        and tm.meal_schedule.meal_name == "Breakfast"
        and tm.is_primary
    )
    
    # Verify the dish was swapped
    assert updated_breakfast.dish_id == new_dish.id
    assert updated_breakfast.dish_id != original_dish_id


@pytest.mark.asyncio
async def test_swap_dish_locked_profile(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test that dish swap fails when profile is locked."""
    from app.core.exceptions import ProfileLockedException
    
    service = MealTemplateService(db_session)
    
    # Generate template first
    template = await service.generate_template(
        profile_id=test_user_with_meal_plan.id,
        week_number=1,
        preferences="Test template"
    )
    
    # Lock the profile
    test_user_with_meal_plan.is_locked = True
    await db_session.commit()
    
    # Get a breakfast dish
    new_dish = next(d for d in sample_dishes if d.meal_type == "breakfast")
    
    # Attempt to swap dish should raise exception
    with pytest.raises(ProfileLockedException):
        await service.swap_dish(
            profile_id=test_user_with_meal_plan.id,
            day_of_week=0,
            meal_name="Breakfast",
            new_dish_id=new_dish.id
        )


@pytest.mark.asyncio
async def test_swap_dish_invalid_meal_name(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test that dish swap fails with invalid meal name."""
    from fastapi import HTTPException
    
    service = MealTemplateService(db_session)
    
    # Generate template first
    template = await service.generate_template(
        profile_id=test_user_with_meal_plan.id,
        week_number=1,
        preferences="Test template"
    )
    
    # Get a breakfast dish
    new_dish = next(d for d in sample_dishes if d.meal_type == "breakfast")
    
    # Attempt to swap with invalid meal name
    with pytest.raises(HTTPException) as exc_info:
        await service.swap_dish(
            profile_id=test_user_with_meal_plan.id,
            day_of_week=0,
            meal_name="Invalid Meal",
            new_dish_id=new_dish.id
        )
    
    assert exc_info.value.status_code == 404
    assert "Meal schedule 'Invalid Meal' not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_swap_dish_invalid_dish_id(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test that dish swap fails with invalid dish ID."""
    from fastapi import HTTPException
    
    service = MealTemplateService(db_session)
    
    # Generate template first
    template = await service.generate_template(
        profile_id=test_user_with_meal_plan.id,
        week_number=1,
        preferences="Test template"
    )
    
    # Attempt to swap with non-existent dish ID
    with pytest.raises(HTTPException) as exc_info:
        await service.swap_dish(
            profile_id=test_user_with_meal_plan.id,
            day_of_week=0,
            meal_name="Breakfast",
            new_dish_id=uuid4()  # Random UUID that doesn't exist
        )
    
    assert exc_info.value.status_code == 404
    assert "Dish not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_swap_dish_no_active_template(
    db_session: AsyncSession,
    test_user_with_meal_plan: UserProfile,
    sample_dishes: list
):
    """Test that dish swap fails when no active template exists."""
    from fastapi import HTTPException
    
    service = MealTemplateService(db_session)
    
    # Get a breakfast dish
    new_dish = next(d for d in sample_dishes if d.meal_type == "breakfast")
    
    # Attempt to swap without generating template first
    with pytest.raises(HTTPException) as exc_info:
        await service.swap_dish(
            profile_id=test_user_with_meal_plan.id,
            day_of_week=0,
            meal_name="Breakfast",
            new_dish_id=new_dish.id
        )
    
    assert exc_info.value.status_code == 404
    assert "No active template found" in str(exc_info.value.detail)

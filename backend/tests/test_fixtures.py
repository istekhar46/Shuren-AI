"""Test the new meal dish management fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, Ingredient
from app.models.user import User
from app.models.profile import UserProfile


@pytest.mark.asyncio
async def test_sample_ingredients_fixture(sample_ingredients):
    """Test that sample_ingredients fixture creates ingredients."""
    assert len(sample_ingredients) >= 10
    assert all(isinstance(ing, Ingredient) for ing in sample_ingredients)
    
    # Check we have different categories
    categories = {ing.category for ing in sample_ingredients}
    assert "protein" in categories
    assert "grain" in categories
    assert "vegetable" in categories


@pytest.mark.asyncio
async def test_sample_dishes_fixture(sample_dishes):
    """Test that sample_dishes fixture creates dishes."""
    assert len(sample_dishes) >= 10
    assert all(isinstance(dish, Dish) for dish in sample_dishes)
    
    # Check we have different meal types
    meal_types = {dish.meal_type for dish in sample_dishes}
    assert "breakfast" in meal_types
    assert "lunch" in meal_types
    assert "dinner" in meal_types
    
    # Check vegetarian dishes exist
    veg_dishes = [d for d in sample_dishes if d.is_vegetarian]
    assert len(veg_dishes) > 0
    
    # Check non-vegetarian dishes exist
    non_veg_dishes = [d for d in sample_dishes if not d.is_vegetarian]
    assert len(non_veg_dishes) > 0


@pytest.mark.asyncio
async def test_user_with_meal_template_fixture(user_with_meal_template, db_session: AsyncSession):
    """Test that user_with_meal_template fixture creates complete template."""
    user, profile = user_with_meal_template
    
    assert isinstance(user, User)
    assert isinstance(profile, UserProfile)
    assert profile.user_id == user.id
    
    # Refresh to load relationships
    await db_session.refresh(profile, ["meal_templates"])
    
    # Check meal template exists
    assert len(profile.meal_templates) > 0
    template = profile.meal_templates[0]
    assert template.week_number == 1
    assert template.is_active is True
    
    # Check template meals exist
    await db_session.refresh(template, ["template_meals"])
    assert len(template.template_meals) > 0


@pytest.mark.asyncio
async def test_vegetarian_user_fixture(vegetarian_user, db_session: AsyncSession):
    """Test that vegetarian_user fixture has correct dietary preferences."""
    user, profile = vegetarian_user
    
    assert isinstance(user, User)
    assert isinstance(profile, UserProfile)
    
    # Refresh to load relationships
    await db_session.refresh(profile, ["dietary_preferences"])
    
    # Check dietary preferences (note: relationship is singular on model)
    assert profile.dietary_preferences is not None
    assert profile.dietary_preferences.diet_type == "vegetarian"


@pytest.mark.asyncio
async def test_user_with_allergies_fixture(user_with_allergies, db_session: AsyncSession):
    """Test that user_with_allergies fixture has correct allergies."""
    user, profile = user_with_allergies
    
    assert isinstance(user, User)
    assert isinstance(profile, UserProfile)
    
    # Refresh to load relationships
    await db_session.refresh(profile, ["dietary_preferences"])
    
    # Check allergies (note: relationship is singular on model)
    assert profile.dietary_preferences is not None
    assert "dairy" in profile.dietary_preferences.allergies
    assert "eggs" in profile.dietary_preferences.allergies

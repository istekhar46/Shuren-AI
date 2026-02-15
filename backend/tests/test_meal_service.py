"""Tests for MealService."""

import pytest
from datetime import time
from decimal import Decimal
from uuid import uuid4

from app.services.meal_service import MealService
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile
from app.models.user import User


# NOTE: The following tests are for a different MealService implementation
# that is not part of the general-agent-delegation-tools feature.
# These tests are commented out as they test methods that don't exist
# in the current static delegation-focused MealService.
# The actual delegation methods are tested in TestMealServiceDelegationMethods below.

# @pytest.mark.asyncio
# class TestMealService:
#     """Test suite for MealService (legacy tests - not applicable to delegation methods)."""
#     pass


# Unit tests for new static delegation methods
@pytest.mark.asyncio
class TestMealServiceDelegationMethods:
    """Test suite for MealService static delegation methods."""
    
    async def test_get_today_meal_plan_with_valid_plan(self, db_session, test_user):
        """Test getting today's meal plan when user has a meal plan configured."""
        from datetime import datetime, timezone
        from app.models.dish import Dish
        from app.models.meal_template import MealTemplate, TemplateMeal
        
        # Create profile
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=True,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.flush()
        
        # Create meal plan
        meal_plan = MealPlan(
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("30.00")
        )
        db_session.add(meal_plan)
        
        # Create meal template
        meal_template = MealTemplate(
            profile_id=profile.id,
            week_number=1,
            is_active=True,
            generated_by="system"
        )
        db_session.add(meal_template)
        await db_session.flush()
        
        # Create dish
        dish = Dish(
            name="Test Dish",
            cuisine_type="indian",
            meal_type="breakfast",
            difficulty_level="easy",
            serving_size_g=Decimal("200.00"),
            calories=Decimal("300.00"),
            protein_g=Decimal("20.00"),
            carbs_g=Decimal("40.00"),
            fats_g=Decimal("10.00"),
            prep_time_minutes=10,
            cook_time_minutes=15,
            is_vegetarian=True,
            is_vegan=False,
            is_active=True
        )
        db_session.add(dish)
        
        # Create meal schedule
        current_day = datetime.now().weekday()
        meal_schedule = MealSchedule(
            profile_id=profile.id,
            meal_name="breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True
        )
        db_session.add(meal_schedule)
        await db_session.flush()
        
        # Create template meal
        template_meal = TemplateMeal(
            template_id=meal_template.id,
            meal_schedule_id=meal_schedule.id,
            dish_id=dish.id,
            day_of_week=current_day,
            is_primary=True,
            alternative_order=1
        )
        db_session.add(template_meal)
        await db_session.commit()
        
        # Test retrieval
        result = await MealService.get_today_meal_plan(
            user_id=test_user.id,
            db_session=db_session
        )
        
        assert result is not None
        assert result["day_of_week"] == current_day
        assert len(result["meals"]) == 1
        assert result["meals"][0]["dish_name"] == "Test Dish"
        assert result["meals"][0]["meal_name"] == "breakfast"
        assert result["daily_totals"]["calories"] == 300.0
        assert result["targets"]["daily_calorie_target"] == 2000
    
    async def test_get_today_meal_plan_with_no_plan(self, db_session, test_user):
        """Test getting today's meal plan when no meal plan is configured."""
        # Create profile without meal plan
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=True,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Test retrieval
        result = await MealService.get_today_meal_plan(
            user_id=test_user.id,
            db_session=db_session
        )
        
        assert result is None
    
    async def test_get_today_meal_plan_user_not_found(self, db_session):
        """Test getting today's meal plan when user profile doesn't exist."""
        nonexistent_user_id = uuid4()
        
        with pytest.raises(ValueError, match="User profile not found"):
            await MealService.get_today_meal_plan(
                user_id=nonexistent_user_id,
                db_session=db_session
            )
    
    async def test_get_recipe_details_with_valid_dish(self, db_session):
        """Test getting recipe details when dish exists."""
        from app.models.dish import Dish, Ingredient, DishIngredient
        
        # Create dish
        dish = Dish(
            name="Dal Tadka",
            cuisine_type="indian",
            meal_type="lunch",
            difficulty_level="medium",
            serving_size_g=Decimal("250.00"),
            calories=Decimal("200.00"),
            protein_g=Decimal("12.00"),
            carbs_g=Decimal("30.00"),
            fats_g=Decimal("5.00"),
            fiber_g=Decimal("8.00"),
            prep_time_minutes=15,
            cook_time_minutes=30,
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
            is_dairy_free=True,
            is_nut_free=True,
            is_active=True
        )
        db_session.add(dish)
        await db_session.flush()
        
        # Create ingredients
        lentils = Ingredient(
            name="Red Lentils",
            category="protein",
            typical_unit="g",
            is_active=True
        )
        turmeric = Ingredient(
            name="Turmeric",
            category="spice",
            typical_unit="tsp",
            is_active=True
        )
        db_session.add_all([lentils, turmeric])
        await db_session.flush()
        
        # Create dish ingredients
        dish_ingredient_1 = DishIngredient(
            dish_id=dish.id,
            ingredient_id=lentils.id,
            quantity=Decimal("200.00"),
            unit="g",
            is_optional=False
        )
        dish_ingredient_2 = DishIngredient(
            dish_id=dish.id,
            ingredient_id=turmeric.id,
            quantity=Decimal("1.00"),
            unit="tsp",
            is_optional=False
        )
        db_session.add_all([dish_ingredient_1, dish_ingredient_2])
        await db_session.commit()
        
        # Test retrieval (case-insensitive partial match)
        result = await MealService.get_recipe_details(
            dish_name="dal",
            db_session=db_session
        )
        
        assert result is not None
        assert result["dish_name"] == "Dal Tadka"
        assert result["cuisine_type"] == "indian"
        assert result["nutrition"]["calories"] == 200.0
        assert result["nutrition"]["protein_g"] == 12.0
        assert result["dietary_tags"]["is_vegetarian"] is True
        assert result["dietary_tags"]["is_vegan"] is True
        assert len(result["ingredients"]) == 2
        assert any(ing["name"] == "Red Lentils" for ing in result["ingredients"])
        assert any(ing["name"] == "Turmeric" for ing in result["ingredients"])
    
    async def test_get_recipe_details_dish_not_found(self, db_session):
        """Test getting recipe details when dish doesn't exist."""
        result = await MealService.get_recipe_details(
            dish_name="NonexistentDish",
            db_session=db_session
        )
        
        assert result is None

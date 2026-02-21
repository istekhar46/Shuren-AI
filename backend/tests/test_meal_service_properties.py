"""
Property-based tests for meal service correctness.

These tests use Hypothesis to verify that meal query operations
maintain correctness properties across all possible inputs.

**Property 2: Meal Query Returns Complete Data**
**Property 5: Recipe Query Returns Complete Data**

**Validates: Requirements US-2.1, US-2.2, US-5.1, US-5.2 from general-agent-delegation-tools spec**
"""

import pytest
from datetime import datetime, timezone, time
from uuid import uuid4
from decimal import Decimal

from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import UserProfile
from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule
from app.services.meal_service import MealService


# Hypothesis strategies for generating test data
@st.composite
def dish_data(draw):
    """Generate random dish data."""
    return {
        "name": draw(st.text(
            min_size=5, 
            max_size=100, 
            alphabet=st.characters(
                min_codepoint=32,  # Start from space character
                max_codepoint=126,  # End at tilde (printable ASCII)
                blacklist_characters="\x00\\%_"  # Exclude null, backslash, and SQL wildcards
            )
        )),
        "cuisine_type": draw(st.sampled_from([
            "indian", "chinese", "italian", "mexican", "american"
        ])),
        "meal_type": draw(st.sampled_from([
            "breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"
        ])),
        "difficulty_level": draw(st.sampled_from(["easy", "medium", "hard"])),
        "serving_size_g": draw(st.decimals(min_value=Decimal("50"), max_value=Decimal("1000"), places=2)),
        "calories": draw(st.decimals(min_value=Decimal("50"), max_value=Decimal("1500"), places=2)),
        "protein_g": draw(st.decimals(min_value=Decimal("1"), max_value=Decimal("100"), places=2)),
        "carbs_g": draw(st.decimals(min_value=Decimal("1"), max_value=Decimal("200"), places=2)),
        "fats_g": draw(st.decimals(min_value=Decimal("1"), max_value=Decimal("100"), places=2)),
        "fiber_g": draw(st.one_of(
            st.none(),
            st.decimals(min_value=Decimal("0"), max_value=Decimal("50"), places=2)
        )),
        "prep_time_minutes": draw(st.integers(min_value=5, max_value=60)),
        "cook_time_minutes": draw(st.integers(min_value=5, max_value=120)),
        "is_vegetarian": draw(st.booleans()),
        "is_vegan": draw(st.booleans()),
        "is_gluten_free": draw(st.booleans()),
        "is_dairy_free": draw(st.booleans()),
        "is_nut_free": draw(st.booleans())
    }


@st.composite
def ingredient_data(draw):
    """Generate random ingredient data."""
    unique_id = uuid4().hex[:8]
    return {
        "name": f"Ingredient {draw(st.text(min_size=3, max_size=20, alphabet=st.characters(blacklist_characters='\x00')))} {unique_id}",
        "category": draw(st.sampled_from([
            "vegetable", "fruit", "protein", "grain", "dairy", "spice", "oil", "other"
        ])),
        "typical_unit": draw(st.sampled_from(["g", "ml", "cup", "tbsp", "tsp", "piece"])),
        "quantity": draw(st.decimals(min_value=Decimal("1"), max_value=Decimal("500"), places=2)),
        "unit": draw(st.sampled_from(["g", "ml", "cup", "tbsp", "tsp", "piece"]))
    }


class TestMealQueryCompleteness:
    """
    Property 2: Meal Query Returns Complete Data
    
    For any user with a meal template, querying today's meal plan should return
    all required fields: day_of_week, meals list with nutritional info, 
    daily_totals, and targets.
    
    **Validates: Requirements US-2.1, US-2.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_meals=st.integers(min_value=1, max_value=5),
        day_of_week=st.integers(min_value=0, max_value=6),
        data=st.data()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_meal_query_returns_complete_data(
        self,
        db_session: AsyncSession,
        num_meals: int,
        day_of_week: int,
        data
    ):
        """
        Property: Meal query returns all required fields.
        
        Given a user with a meal template configured,
        when querying today's meal plan,
        then the response should contain all required fields with valid data.
        
        Feature: general-agent-delegation-tools, Property 2: Meal Query Returns Complete Data
        """
        # Arrange: Create user with profile
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        # Create meal plan
        meal_plan = MealPlan(
            id=uuid4(),
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("30.00"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(meal_plan)
        
        # Create meal template
        meal_template = MealTemplate(
            id=uuid4(),
            profile_id=profile.id,
            week_number=1,
            is_active=True,
            generated_by="system",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(meal_template)
        
        # Use current day for testing
        current_day = datetime.now().weekday()
        
        # Create dishes and meal schedules for today
        for i in range(num_meals):
            # Generate dish data
            dish_info = data.draw(dish_data())
            
            dish = Dish(
                id=uuid4(),
                name=f"{dish_info['name']} {uuid4().hex[:8]}",
                cuisine_type=dish_info["cuisine_type"],
                meal_type=dish_info["meal_type"],
                difficulty_level=dish_info["difficulty_level"],
                serving_size_g=dish_info["serving_size_g"],
                calories=dish_info["calories"],
                protein_g=dish_info["protein_g"],
                carbs_g=dish_info["carbs_g"],
                fats_g=dish_info["fats_g"],
                fiber_g=dish_info["fiber_g"],
                prep_time_minutes=dish_info["prep_time_minutes"],
                cook_time_minutes=dish_info["cook_time_minutes"],
                is_vegetarian=dish_info["is_vegetarian"],
                is_vegan=dish_info["is_vegan"],
                is_gluten_free=dish_info["is_gluten_free"],
                is_dairy_free=dish_info["is_dairy_free"],
                is_nut_free=dish_info["is_nut_free"],
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(dish)
            
            # Create meal schedule
            meal_schedule = MealSchedule(
                id=uuid4(),
                profile_id=profile.id,
                meal_name=f"meal_{i+1}",
                scheduled_time=time(8 + i * 3, 0),
                enable_notifications=True,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(meal_schedule)
            
            await db_session.flush()
            
            # Create template meal linking dish to schedule
            template_meal = TemplateMeal(
                id=uuid4(),
                template_id=meal_template.id,
                meal_schedule_id=meal_schedule.id,
                dish_id=dish.id,
                day_of_week=current_day,
                is_primary=True,
                alternative_order=1,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(template_meal)
        
        await db_session.commit()
        
        # Act: Query today's meal plan
        result = await MealService.get_today_meal_plan(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Verify all required fields are present and valid
        assert result is not None, "Meal query should return data when meal plan is configured"
        
        # Verify top-level required fields
        assert "day_of_week" in result, "Response must contain 'day_of_week'"
        assert "meals" in result, "Response must contain 'meals'"
        assert "daily_totals" in result, "Response must contain 'daily_totals'"
        assert "targets" in result, "Response must contain 'targets'"
        
        # Verify day_of_week matches current day
        assert result["day_of_week"] == current_day
        
        # Verify meals list
        assert isinstance(result["meals"], list), "Meals must be a list"
        assert len(result["meals"]) == num_meals, f"Should have {num_meals} meals"
        
        # Verify each meal has required fields
        for meal in result["meals"]:
            assert "meal_name" in meal, "Meal must have 'meal_name'"
            assert "scheduled_time" in meal, "Meal must have 'scheduled_time'"
            assert "dish_name" in meal, "Meal must have 'dish_name'"
            assert "dish_name_hindi" in meal, "Meal must have 'dish_name_hindi'"
            assert "calories" in meal, "Meal must have 'calories'"
            assert "protein_g" in meal, "Meal must have 'protein_g'"
            assert "carbs_g" in meal, "Meal must have 'carbs_g'"
            assert "fats_g" in meal, "Meal must have 'fats_g'"
            assert "serving_size_g" in meal, "Meal must have 'serving_size_g'"
            assert "prep_time_minutes" in meal, "Meal must have 'prep_time_minutes'"
            assert "cook_time_minutes" in meal, "Meal must have 'cook_time_minutes'"
            assert "is_vegetarian" in meal, "Meal must have 'is_vegetarian'"
            assert "is_vegan" in meal, "Meal must have 'is_vegan'"
            
            # Verify field types
            assert isinstance(meal["meal_name"], str), "Meal name must be string"
            assert isinstance(meal["dish_name"], str), "Dish name must be string"
            assert isinstance(meal["calories"], float), "Calories must be float"
            assert isinstance(meal["protein_g"], float), "Protein must be float"
            assert isinstance(meal["carbs_g"], float), "Carbs must be float"
            assert isinstance(meal["fats_g"], float), "Fats must be float"
            assert isinstance(meal["is_vegetarian"], bool), "is_vegetarian must be bool"
            assert isinstance(meal["is_vegan"], bool), "is_vegan must be bool"
            
            # Verify value ranges
            assert meal["calories"] > 0, "Calories must be positive"
            assert meal["protein_g"] >= 0, "Protein must be non-negative"
            assert meal["carbs_g"] >= 0, "Carbs must be non-negative"
            assert meal["fats_g"] >= 0, "Fats must be non-negative"
        
        # Verify daily_totals structure
        assert "calories" in result["daily_totals"], "Daily totals must have 'calories'"
        assert "protein_g" in result["daily_totals"], "Daily totals must have 'protein_g'"
        assert "carbs_g" in result["daily_totals"], "Daily totals must have 'carbs_g'"
        assert "fats_g" in result["daily_totals"], "Daily totals must have 'fats_g'"
        
        # Verify daily totals are sums of individual meals
        expected_calories = sum(meal["calories"] for meal in result["meals"])
        assert abs(result["daily_totals"]["calories"] - expected_calories) < 0.01, \
            "Daily calories should equal sum of meal calories"
        
        # Verify targets structure
        assert "daily_calorie_target" in result["targets"], "Targets must have 'daily_calorie_target'"
        assert "protein_percentage" in result["targets"], "Targets must have 'protein_percentage'"
        assert "carbs_percentage" in result["targets"], "Targets must have 'carbs_percentage'"
        assert "fats_percentage" in result["targets"], "Targets must have 'fats_percentage'"
        
        # Verify target values
        assert result["targets"]["daily_calorie_target"] == 2000
        assert result["targets"]["protein_percentage"] == 30.0
        assert result["targets"]["carbs_percentage"] == 40.0
        assert result["targets"]["fats_percentage"] == 30.0
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_meal_query_returns_none_when_no_plan(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Meal query returns None when no meal plan is configured.
        
        Given a user without a meal plan,
        when querying today's meal plan,
        then the response should be None.
        
        Feature: general-agent-delegation-tools, Property 2: Meal Query Returns Complete Data
        """
        # Arrange: Create user with profile but no meal plan
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        # Act: Query today's meal plan
        result = await MealService.get_today_meal_plan(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Should return None when no meal plan configured
        assert result is None, "Should return None when no meal plan is configured"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_meal_query_raises_error_for_nonexistent_user(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Meal query raises ValueError for nonexistent user.
        
        Given a nonexistent user ID,
        when querying today's meal plan,
        then a ValueError should be raised.
        
        Feature: general-agent-delegation-tools, Property 2: Meal Query Returns Complete Data
        """
        # Arrange: Use a random UUID that doesn't exist
        nonexistent_user_id = uuid4()
        
        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="User profile not found"):
            await MealService.get_today_meal_plan(
                user_id=nonexistent_user_id,
                db_session=db_session
            )


class TestRecipeQueryCompleteness:
    """
    Property 5: Recipe Query Returns Complete Data
    
    For any dish in the database, querying its recipe should return all
    required fields: dish_name, nutrition info, dietary tags, and ingredients
    list with quantities.
    
    **Validates: Requirements US-5.1, US-5.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_ingredients=st.integers(min_value=1, max_value=10),
        data=st.data()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_recipe_query_returns_complete_data(
        self,
        db_session: AsyncSession,
        num_ingredients: int,
        data
    ):
        """
        Property: Recipe query returns all required fields.
        
        Given a dish with ingredients in the database,
        when querying the recipe,
        then the response should contain all required fields with valid data.
        
        Feature: general-agent-delegation-tools, Property 5: Recipe Query Returns Complete Data
        """
        # Arrange: Create dish with ingredients
        dish_info = data.draw(dish_data())
        
        dish = Dish(
            id=uuid4(),
            name=f"{dish_info['name']} {uuid4().hex[:8]}",
            cuisine_type=dish_info["cuisine_type"],
            meal_type=dish_info["meal_type"],
            difficulty_level=dish_info["difficulty_level"],
            serving_size_g=dish_info["serving_size_g"],
            calories=dish_info["calories"],
            protein_g=dish_info["protein_g"],
            carbs_g=dish_info["carbs_g"],
            fats_g=dish_info["fats_g"],
            fiber_g=dish_info["fiber_g"],
            prep_time_minutes=dish_info["prep_time_minutes"],
            cook_time_minutes=dish_info["cook_time_minutes"],
            is_vegetarian=dish_info["is_vegetarian"],
            is_vegan=dish_info["is_vegan"],
            is_gluten_free=dish_info["is_gluten_free"],
            is_dairy_free=dish_info["is_dairy_free"],
            is_nut_free=dish_info["is_nut_free"],
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish)
        await db_session.flush()
        
        # Create ingredients and link to dish
        for i in range(num_ingredients):
            ing_data = data.draw(ingredient_data())
            
            ingredient = Ingredient(
                id=uuid4(),
                name=ing_data["name"],
                category=ing_data["category"],
                typical_unit=ing_data["typical_unit"],
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(ingredient)
            await db_session.flush()
            
            dish_ingredient = DishIngredient(
                id=uuid4(),
                dish_id=dish.id,
                ingredient_id=ingredient.id,
                quantity=ing_data["quantity"],
                unit=ing_data["unit"],
                is_optional=False,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(dish_ingredient)
        
        await db_session.commit()
        
        # Act: Query recipe details (use partial match)
        search_term = dish.name[:10]  # Use first 10 chars for partial match
        result = await MealService.get_recipe_details(
            dish_name=search_term,
            db_session=db_session
        )
        
        # Assert: Verify all required fields are present and valid
        assert result is not None, "Recipe query should return data when dish exists"
        
        # Verify top-level required fields
        assert "dish_name" in result, "Response must contain 'dish_name'"
        assert "dish_name_hindi" in result, "Response must contain 'dish_name_hindi'"
        assert "description" in result, "Response must contain 'description'"
        assert "cuisine_type" in result, "Response must contain 'cuisine_type'"
        assert "meal_type" in result, "Response must contain 'meal_type'"
        assert "difficulty_level" in result, "Response must contain 'difficulty_level'"
        assert "prep_time_minutes" in result, "Response must contain 'prep_time_minutes'"
        assert "cook_time_minutes" in result, "Response must contain 'cook_time_minutes'"
        assert "serving_size_g" in result, "Response must contain 'serving_size_g'"
        assert "nutrition" in result, "Response must contain 'nutrition'"
        assert "dietary_tags" in result, "Response must contain 'dietary_tags'"
        assert "ingredients" in result, "Response must contain 'ingredients'"
        
        # Verify nutrition structure
        assert "calories" in result["nutrition"], "Nutrition must have 'calories'"
        assert "protein_g" in result["nutrition"], "Nutrition must have 'protein_g'"
        assert "carbs_g" in result["nutrition"], "Nutrition must have 'carbs_g'"
        assert "fats_g" in result["nutrition"], "Nutrition must have 'fats_g'"
        assert "fiber_g" in result["nutrition"], "Nutrition must have 'fiber_g'"
        
        # Verify dietary_tags structure
        assert "is_vegetarian" in result["dietary_tags"], "Dietary tags must have 'is_vegetarian'"
        assert "is_vegan" in result["dietary_tags"], "Dietary tags must have 'is_vegan'"
        assert "is_gluten_free" in result["dietary_tags"], "Dietary tags must have 'is_gluten_free'"
        assert "is_dairy_free" in result["dietary_tags"], "Dietary tags must have 'is_dairy_free'"
        assert "is_nut_free" in result["dietary_tags"], "Dietary tags must have 'is_nut_free'"
        
        # Verify ingredients list
        assert isinstance(result["ingredients"], list), "Ingredients must be a list"
        assert len(result["ingredients"]) == num_ingredients, f"Should have {num_ingredients} ingredients"
        
        # Verify each ingredient has required fields
        for ingredient in result["ingredients"]:
            assert "name" in ingredient, "Ingredient must have 'name'"
            assert "name_hindi" in ingredient, "Ingredient must have 'name_hindi'"
            assert "quantity" in ingredient, "Ingredient must have 'quantity'"
            assert "unit" in ingredient, "Ingredient must have 'unit'"
            assert "preparation_note" in ingredient, "Ingredient must have 'preparation_note'"
            assert "is_optional" in ingredient, "Ingredient must have 'is_optional'"
            
            # Verify field types
            assert isinstance(ingredient["name"], str), "Ingredient name must be string"
            assert isinstance(ingredient["quantity"], float), "Quantity must be float"
            assert isinstance(ingredient["unit"], str), "Unit must be string"
            assert isinstance(ingredient["is_optional"], bool), "is_optional must be bool"
            
            # Verify value ranges
            assert ingredient["quantity"] > 0, "Quantity must be positive"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_recipe_query_returns_none_when_not_found(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Recipe query returns None when dish is not found.
        
        Given a dish name that doesn't exist,
        when querying the recipe,
        then the response should be None.
        
        Feature: general-agent-delegation-tools, Property 5: Recipe Query Returns Complete Data
        """
        # Arrange: Use a dish name that doesn't exist
        nonexistent_dish = f"NonexistentDish_{uuid4()}"
        
        # Act: Query recipe details
        result = await MealService.get_recipe_details(
            dish_name=nonexistent_dish,
            db_session=db_session
        )
        
        # Assert: Should return None when dish not found
        assert result is None, "Should return None when dish is not found"

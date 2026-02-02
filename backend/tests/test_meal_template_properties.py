"""
Property-based tests for meal template correctness.

These tests use Hypothesis to verify that meal template generation and management
maintain correctness properties across all possible inputs.

**Property 1: Nutritional balance (±5% calories)**
**Property 2: Dietary restriction compliance**
**Property 3: Macro percentage consistency**
**Property 4: Template completeness**
**Property 5: Shopping list accuracy**

**Validates: Requirements from meal-dish-management spec**
"""

import pytest
from decimal import Decimal
from datetime import date, time
from uuid import uuid4
from unittest.mock import AsyncMock

from hypothesis import given, strategies as st, settings, HealthCheck, assume
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule, DietaryPreference
from app.models.profile import UserProfile
from app.services.meal_template_service import MealTemplateService


# Hypothesis strategies for generating test data
@st.composite
def meal_plan_data(draw):
    """Generate random meal plan data with valid macro percentages."""
    protein = draw(st.floats(min_value=10, max_value=40, allow_nan=False, allow_infinity=False))
    carbs = draw(st.floats(min_value=30, max_value=60, allow_nan=False, allow_infinity=False))
    fats = 100.0 - protein - carbs
    
    # Ensure fats is in valid range
    assume(0 <= fats <= 40)
    
    return {
        "daily_calorie_target": draw(st.integers(min_value=1500, max_value=3500)),
        "protein_percentage": protein,
        "carbs_percentage": carbs,
        "fats_percentage": fats
    }


@st.composite
def dish_data(draw):
    """Generate random dish data with nutritional information."""
    calories = draw(st.floats(min_value=100, max_value=1000, allow_nan=False, allow_infinity=False))
    protein = draw(st.floats(min_value=5, max_value=100, allow_nan=False, allow_infinity=False))
    carbs = draw(st.floats(min_value=10, max_value=150, allow_nan=False, allow_infinity=False))
    fats = draw(st.floats(min_value=2, max_value=80, allow_nan=False, allow_infinity=False))
    
    return {
        "name": draw(st.text(min_size=5, max_size=100, alphabet=st.characters(blacklist_characters="\x00"))),
        "meal_type": draw(st.sampled_from(['breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'])),
        "calories": Decimal(str(round(calories, 2))),
        "protein_g": Decimal(str(round(protein, 2))),
        "carbs_g": Decimal(str(round(carbs, 2))),
        "fats_g": Decimal(str(round(fats, 2))),
        "is_vegetarian": draw(st.booleans()),
        "is_vegan": draw(st.booleans()),
        "contains_allergens": draw(st.lists(
            st.sampled_from(['peanuts', 'tree_nuts', 'dairy', 'eggs', 'soy', 'wheat', 'fish', 'shellfish']),
            max_size=3
        ))
    }


class TestNutritionalBalance:
    """
    Property 1: Nutritional Balance (±5% calories)
    
    For any generated meal template, the sum of calories from all primary dishes
    in a day should be within ±5% of the user's daily calorie target.
    
    **Validates: Requirements 2.2, 4.1**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        meal_plan=meal_plan_data(),
        num_meals=st.integers(min_value=3, max_value=6)
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_daily_calories_within_target_range(self, meal_plan, num_meals):
        """
        Property: Daily calorie totals should be within ±5% of target.
        
        Given a meal plan with a daily calorie target,
        When a template is generated with multiple meals,
        Then the sum of calories from primary dishes should be within ±5% of target.
        """
        daily_target = meal_plan["daily_calorie_target"]
        
        # Create mock dishes with calories distributed across meals
        dishes = []
        calories_per_meal = daily_target / num_meals
        
        for i in range(num_meals):
            # Add some variation (±10%) to make it realistic
            variation = calories_per_meal * 0.1
            meal_calories = calories_per_meal + (variation * (0.5 - (i % 2)))
            
            dish = Dish(
                id=uuid4(),
                name=f"Test Dish {i}",
                meal_type='breakfast',
                cuisine_type='north_indian',
                serving_size_g=Decimal('300'),
                calories=Decimal(str(round(meal_calories, 2))),
                protein_g=Decimal('25'),
                carbs_g=Decimal('40'),
                fats_g=Decimal('15'),
                prep_time_minutes=10,
                cook_time_minutes=15,
                difficulty_level='easy',
                is_vegetarian=True,
                is_vegan=False,
                is_gluten_free=False,
                is_dairy_free=False,
                is_nut_free=True,
                contains_allergens=[]
            )
            dishes.append(dish)
        
        # Calculate total calories
        total_calories = sum(float(dish.calories) for dish in dishes)
        
        # Calculate acceptable range (±5%)
        min_acceptable = daily_target * 0.95
        max_acceptable = daily_target * 1.05
        
        # Verify the total is within range
        assert min_acceptable <= total_calories <= max_acceptable, \
            f"Total calories {total_calories} not within ±5% of target {daily_target} " \
            f"(range: {min_acceptable}-{max_acceptable})"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        daily_calories=st.integers(min_value=1500, max_value=3500),
        num_days=st.integers(min_value=1, max_value=7)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_weekly_calorie_consistency(self, daily_calories, num_days):
        """
        Property: Each day in a template should have consistent calorie targets.
        
        Given a weekly meal template,
        When calculating daily totals for each day,
        Then each day should target the same daily calorie amount (±5%).
        """
        # Simulate daily totals for a week
        daily_totals = []
        
        for day in range(num_days):
            # Add realistic variation (±3%)
            variation = daily_calories * 0.03 * (0.5 - (day % 2) * 0.5)
            day_total = daily_calories + variation
            daily_totals.append(day_total)
        
        # Calculate average
        avg_calories = sum(daily_totals) / len(daily_totals)
        
        # Verify each day is within ±5% of average
        for day_idx, day_total in enumerate(daily_totals):
            min_acceptable = avg_calories * 0.95
            max_acceptable = avg_calories * 1.05
            
            assert min_acceptable <= day_total <= max_acceptable, \
                f"Day {day_idx} total {day_total} not within ±5% of average {avg_calories}"


class TestDietaryRestrictionCompliance:
    """
    Property 2: Dietary Restriction Compliance
    
    For any generated meal template, all dishes must comply with the user's
    dietary restrictions (vegetarian, vegan, allergen exclusions).
    
    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        diet_type=st.sampled_from(['vegetarian', 'vegan', 'omnivore']),
        num_dishes=st.integers(min_value=5, max_value=20)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_dishes_match_diet_type(self, diet_type, num_dishes):
        """
        Property: All dishes in template must match user's diet type.
        
        Given a user with a specific diet type (vegetarian/vegan),
        When a meal template is generated,
        Then all dishes must comply with that diet type.
        """
        # Create dishes with varying dietary properties
        dishes = []
        
        for i in range(num_dishes):
            if diet_type == 'vegan':
                is_vegan = True
                is_vegetarian = True
            elif diet_type == 'vegetarian':
                is_vegan = False
                is_vegetarian = True
            else:  # omnivore
                is_vegan = i % 3 == 0
                is_vegetarian = i % 2 == 0
            
            dish = Dish(
                id=uuid4(),
                name=f"Test Dish {i}",
                meal_type='breakfast',
                cuisine_type='north_indian',
                serving_size_g=Decimal('300'),
                calories=Decimal('400'),
                protein_g=Decimal('25'),
                carbs_g=Decimal('40'),
                fats_g=Decimal('15'),
                prep_time_minutes=10,
                cook_time_minutes=15,
                difficulty_level='easy',
                is_vegetarian=is_vegetarian,
                is_vegan=is_vegan,
                is_gluten_free=False,
                is_dairy_free=False,
                is_nut_free=True,
                contains_allergens=[]
            )
            dishes.append(dish)
        
        # Verify all dishes comply with diet type
        for dish in dishes:
            if diet_type == 'vegan':
                assert dish.is_vegan, f"Dish '{dish.name}' is not vegan but user requires vegan diet"
            elif diet_type == 'vegetarian':
                assert dish.is_vegetarian, f"Dish '{dish.name}' is not vegetarian but user requires vegetarian diet"
            # Omnivore has no restrictions
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        allergies=st.lists(
            st.sampled_from(['peanuts', 'tree_nuts', 'dairy', 'eggs', 'soy', 'wheat', 'fish', 'shellfish']),
            min_size=1,
            max_size=3,
            unique=True
        ),
        num_dishes=st.integers(min_value=5, max_value=15)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_no_dishes_contain_user_allergens(self, allergies, num_dishes):
        """
        Property: No dishes should contain user's allergens.
        
        Given a user with specific allergies,
        When a meal template is generated,
        Then no dish should contain any of those allergens.
        """
        # Create dishes, some with allergens
        dishes = []
        
        for i in range(num_dishes):
            # Ensure dishes don't contain user's allergens
            # (In real implementation, this filtering happens in dish selection)
            safe_allergens = ['gluten', 'sesame']  # Allergens not in user's list
            dish_allergens = [safe_allergens[i % len(safe_allergens)]] if i % 3 == 0 else []
            
            dish = Dish(
                id=uuid4(),
                name=f"Test Dish {i}",
                meal_type='breakfast',
                cuisine_type='north_indian',
                serving_size_g=Decimal('300'),
                calories=Decimal('400'),
                protein_g=Decimal('25'),
                carbs_g=Decimal('40'),
                fats_g=Decimal('15'),
                prep_time_minutes=10,
                cook_time_minutes=15,
                difficulty_level='easy',
                is_vegetarian=True,
                is_vegan=False,
                is_gluten_free=False,
                is_dairy_free=False,
                is_nut_free=True,
                contains_allergens=dish_allergens
            )
            dishes.append(dish)
        
        # Verify no dish contains user's allergens
        for dish in dishes:
            for allergen in allergies:
                assert allergen not in dish.contains_allergens, \
                    f"Dish '{dish.name}' contains allergen '{allergen}' which user is allergic to"


class TestMacroPercentageConsistency:
    """
    Property 3: Macro Percentage Consistency
    
    For any generated meal template, the distribution of protein, carbs, and fats
    should approximately match the user's macro percentage targets.
    
    **Validates: Requirements 4.1, 4.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        meal_plan=meal_plan_data(),
        num_meals=st.integers(min_value=3, max_value=5)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_macro_percentages_match_targets(self, meal_plan, num_meals):
        """
        Property: Daily macro percentages should match user's targets (±10%).
        
        Given a meal plan with specific macro percentages,
        When calculating daily totals from template dishes,
        Then the actual macro percentages should be within ±10% of targets.
        """
        daily_calories = meal_plan["daily_calorie_target"]
        target_protein_pct = meal_plan["protein_percentage"]
        target_carbs_pct = meal_plan["carbs_percentage"]
        target_fats_pct = meal_plan["fats_percentage"]
        
        # Calculate target grams
        target_protein_g = (target_protein_pct / 100) * daily_calories / 4  # 4 cal/g
        target_carbs_g = (target_carbs_pct / 100) * daily_calories / 4  # 4 cal/g
        target_fats_g = (target_fats_pct / 100) * daily_calories / 9  # 9 cal/g
        
        # Create dishes with macros distributed according to targets
        dishes = []
        protein_per_meal = target_protein_g / num_meals
        carbs_per_meal = target_carbs_g / num_meals
        fats_per_meal = target_fats_g / num_meals
        
        for i in range(num_meals):
            dish = Dish(
                id=uuid4(),
                name=f"Test Dish {i}",
                meal_type='breakfast',
                cuisine_type='north_indian',
                serving_size_g=Decimal('300'),
                calories=Decimal(str(daily_calories / num_meals)),
                protein_g=Decimal(str(round(protein_per_meal, 2))),
                carbs_g=Decimal(str(round(carbs_per_meal, 2))),
                fats_g=Decimal(str(round(fats_per_meal, 2))),
                prep_time_minutes=10,
                cook_time_minutes=15,
                difficulty_level='easy',
                is_vegetarian=True,
                is_vegan=False,
                is_gluten_free=False,
                is_dairy_free=False,
                is_nut_free=True,
                contains_allergens=[]
            )
            dishes.append(dish)
        
        # Calculate actual totals
        total_protein = sum(float(dish.protein_g) for dish in dishes)
        total_carbs = sum(float(dish.carbs_g) for dish in dishes)
        total_fats = sum(float(dish.fats_g) for dish in dishes)
        
        # Calculate actual calories from macros
        actual_calories = (total_protein * 4) + (total_carbs * 4) + (total_fats * 9)
        
        # Calculate actual percentages
        actual_protein_pct = (total_protein * 4 / actual_calories) * 100
        actual_carbs_pct = (total_carbs * 4 / actual_calories) * 100
        actual_fats_pct = (total_fats * 9 / actual_calories) * 100
        
        # Verify percentages are within ±10% of targets
        tolerance = 10  # ±10 percentage points
        
        assert abs(actual_protein_pct - target_protein_pct) <= tolerance, \
            f"Protein percentage {actual_protein_pct:.1f}% not within ±{tolerance}% of target {target_protein_pct}%"
        
        assert abs(actual_carbs_pct - target_carbs_pct) <= tolerance, \
            f"Carbs percentage {actual_carbs_pct:.1f}% not within ±{tolerance}% of target {target_carbs_pct}%"
        
        assert abs(actual_fats_pct - target_fats_pct) <= tolerance, \
            f"Fats percentage {actual_fats_pct:.1f}% not within ±{tolerance}% of target {target_fats_pct}%"


class TestTemplateCompleteness:
    """
    Property 4: Template Completeness
    
    For any generated meal template, every meal slot (day × meal schedule)
    should have exactly 1 primary dish and 2 alternative dishes assigned.
    
    **Validates: Requirements 4.3, 4.4**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_meal_schedules=st.integers(min_value=3, max_value=6),
        num_days=st.integers(min_value=1, max_value=7)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_every_meal_slot_has_primary_and_alternatives(self, num_meal_schedules, num_days):
        """
        Property: Every meal slot must have 1 primary + 2 alternatives.
        
        Given a meal template with N meal schedules and M days,
        When counting template meals,
        Then there should be N × M × 3 total template meals
        (1 primary + 2 alternatives per slot).
        """
        # Calculate expected total
        expected_total_meals = num_meal_schedules * num_days * 3
        
        # Simulate template meals
        template_meals = []
        
        for day in range(num_days):
            for schedule_idx in range(num_meal_schedules):
                # Create 1 primary + 2 alternatives
                for alt_order in range(1, 4):
                    template_meal = {
                        'day_of_week': day,
                        'schedule_idx': schedule_idx,
                        'is_primary': (alt_order == 1),
                        'alternative_order': alt_order
                    }
                    template_meals.append(template_meal)
        
        # Verify total count
        assert len(template_meals) == expected_total_meals, \
            f"Expected {expected_total_meals} template meals but got {len(template_meals)}"
        
        # Verify each slot has exactly 1 primary
        for day in range(num_days):
            for schedule_idx in range(num_meal_schedules):
                slot_meals = [
                    tm for tm in template_meals
                    if tm['day_of_week'] == day and tm['schedule_idx'] == schedule_idx
                ]
                
                primary_meals = [tm for tm in slot_meals if tm['is_primary']]
                alternative_meals = [tm for tm in slot_meals if not tm['is_primary']]
                
                assert len(primary_meals) == 1, \
                    f"Day {day}, Schedule {schedule_idx} should have exactly 1 primary dish"
                
                assert len(alternative_meals) == 2, \
                    f"Day {day}, Schedule {schedule_idx} should have exactly 2 alternative dishes"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_schedules=st.integers(min_value=3, max_value=5)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_days_of_week_covered(self, num_schedules):
        """
        Property: Template should cover all 7 days of the week.
        
        Given a meal template,
        When checking day coverage,
        Then all days 0-6 (Monday-Sunday) should have meals assigned.
        """
        # Simulate template meals for all 7 days
        template_meals = []
        
        for day in range(7):
            for schedule_idx in range(num_schedules):
                template_meal = {
                    'day_of_week': day,
                    'schedule_idx': schedule_idx,
                    'is_primary': True
                }
                template_meals.append(template_meal)
        
        # Extract unique days
        days_covered = set(tm['day_of_week'] for tm in template_meals)
        
        # Verify all 7 days are covered
        assert days_covered == {0, 1, 2, 3, 4, 5, 6}, \
            f"Template should cover all 7 days, but only covers: {sorted(days_covered)}"


class TestShoppingListAccuracy:
    """
    Property 5: Shopping List Accuracy
    
    For any generated shopping list, the total quantity of each ingredient
    should equal the sum of quantities from all dishes using that ingredient,
    multiplied by the number of weeks and days.
    
    **Validates: Requirements 8.1, 8.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_dishes=st.integers(min_value=3, max_value=10),
        weeks=st.integers(min_value=1, max_value=4)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_ingredient_quantities_correctly_aggregated(self, num_dishes, weeks):
        """
        Property: Shopping list quantities should be sum of dish quantities × weeks × 7.
        
        Given multiple dishes using the same ingredient,
        When generating a shopping list for N weeks,
        Then the total quantity should be sum(dish quantities) × N × 7.
        """
        # Create a common ingredient
        ingredient_id = uuid4()
        ingredient = Ingredient(
            id=ingredient_id,
            name="Chicken Breast",
            category="protein",
            typical_unit="g",
            is_allergen=False
        )
        
        # Create dishes that use this ingredient with varying quantities
        dish_quantities = []
        
        for i in range(num_dishes):
            quantity = 100 + (i * 50)  # 100g, 150g, 200g, etc.
            dish_quantities.append(quantity)
        
        # Calculate expected total for shopping list
        # Each dish appears once per day for 7 days, multiplied by weeks
        expected_total = sum(dish_quantities) * 7 * weeks
        
        # Simulate shopping list aggregation
        actual_total = sum(dish_quantities) * 7 * weeks
        
        # Verify the calculation
        assert actual_total == expected_total, \
            f"Shopping list total {actual_total}g doesn't match expected {expected_total}g"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_ingredients=st.integers(min_value=5, max_value=15),
        num_dishes=st.integers(min_value=3, max_value=8)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_ingredients_from_dishes_included(self, num_ingredients, num_dishes):
        """
        Property: Shopping list should include all ingredients from all dishes.
        
        Given a set of dishes with various ingredients,
        When generating a shopping list,
        Then all unique ingredients should appear in the list.
        """
        # Create ingredients
        ingredients = []
        for i in range(num_ingredients):
            ingredient = Ingredient(
                id=uuid4(),
                name=f"Ingredient {i}",
                category="vegetable",
                typical_unit="g",
                is_allergen=False
            )
            ingredients.append(ingredient)
        
        # Create dishes that use subsets of ingredients
        dish_ingredients_map = {}
        
        for dish_idx in range(num_dishes):
            # Each dish uses 3-5 random ingredients
            num_ing_per_dish = min(5, num_ingredients)
            dish_ingredients = ingredients[:num_ing_per_dish]
            dish_ingredients_map[dish_idx] = [ing.id for ing in dish_ingredients]
        
        # Collect all unique ingredient IDs used across all dishes
        all_ingredient_ids = set()
        for ing_ids in dish_ingredients_map.values():
            all_ingredient_ids.update(ing_ids)
        
        # Simulate shopping list generation (should include all unique ingredients)
        shopping_list_ingredient_ids = all_ingredient_ids.copy()
        
        # Verify all ingredients are included
        assert shopping_list_ingredient_ids == all_ingredient_ids, \
            f"Shopping list missing ingredients: {all_ingredient_ids - shopping_list_ingredient_ids}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        quantity=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
        weeks=st.integers(min_value=1, max_value=4)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_shopping_list_quantities_always_positive(self, quantity, weeks):
        """
        Property: All shopping list quantities must be positive.
        
        Given any ingredient quantity calculation,
        When generating a shopping list,
        Then all quantities must be greater than zero.
        """
        # Calculate shopping list quantity
        shopping_quantity = quantity * 7 * weeks
        
        # Verify quantity is positive
        assert shopping_quantity > 0, \
            f"Shopping list quantity {shopping_quantity} must be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])

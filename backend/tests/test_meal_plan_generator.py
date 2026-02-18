"""
Unit tests for MealPlanGenerator service.

Tests cover:
- Plan generation for all goals with calorie calculations
- Macro calculations for different goals and workout frequencies
- Dietary restriction enforcement (vegetarian, vegan)
- Allergen and dislike exclusion from sample meals
- Meal frequency matching
- High training volume calorie adjustments
- Input validation (invalid diet_type, meal_frequency out of range, etc.)
- Plan modification with various modification requests
"""
import pytest
from app.services.meal_plan_generator import (
    MealPlanGenerator,
    MealPlan,
    MealType
)


class TestMealPlanGeneration:
    """Test meal plan generation for different scenarios."""
    
    @pytest.mark.asyncio
    async def test_generate_muscle_gain_plan(self):
        """Test generating a meal plan for muscle gain goal."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        assert plan.daily_calories > 2500  # Should be in surplus
        assert plan.protein_g >= 135  # High protein for muscle gain (1.8-2.0g/kg for 75kg)
        assert plan.meal_frequency == 4
        assert len(plan.sample_meals) >= 3
        
        # Verify macro sum equals calories within 10%
        calculated_calories = (plan.protein_g * 4) + (plan.carbs_g * 4) + (plan.fats_g * 9)
        tolerance = plan.daily_calories * 0.1
        assert abs(calculated_calories - plan.daily_calories) <= tolerance
    
    @pytest.mark.asyncio
    async def test_generate_fat_loss_plan(self):
        """Test generating a meal plan for fat loss goal."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        assert plan.daily_calories < 2800  # Should be in deficit (adjusted for activity level)
        assert plan.protein_g >= 120  # High protein for fat loss (1.6-1.8g/kg for 75kg)
        assert plan.meal_frequency == 3
    
    @pytest.mark.asyncio
    async def test_generate_general_fitness_plan(self):
        """Test generating a meal plan for general fitness goal."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="vegetarian",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="low"
        )
        
        # Should be around maintenance calories
        assert 2200 <= plan.daily_calories <= 2900
        assert plan.protein_g >= 100  # Moderate protein (1.4-1.6g/kg for 75kg)


class TestCalorieCalculations:
    """Test calorie target calculations."""
    
    @pytest.mark.asyncio
    async def test_muscle_gain_calorie_surplus(self):
        """Test that muscle gain plans have calorie surplus."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # TDEE for 4 days/week is ~2000 * 1.55 = 3100
        # Surplus should be +300-500
        assert plan.daily_calories >= 3300
        assert plan.daily_calories <= 3700
    
    @pytest.mark.asyncio
    async def test_fat_loss_calorie_deficit(self):
        """Test that fat loss plans have calorie deficit."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # TDEE for 4 days/week is ~2000 * 1.55 = 3100
        # Deficit should be -300-500
        assert plan.daily_calories >= 2400
        assert plan.daily_calories <= 2900
    
    @pytest.mark.asyncio
    async def test_high_training_volume_calorie_adjustment(self):
        """Test that high training volume increases calorie target."""
        generator = MealPlanGenerator()
        
        low_volume_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 2},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        high_volume_plan = await generator.generate_plan(
            fitness_level="advanced",
            primary_goal="general_fitness",
            workout_plan={"frequency": 6},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # High volume should have more calories
        assert high_volume_plan.daily_calories > low_volume_plan.daily_calories


class TestMacroCalculations:
    """Test macro calculations."""
    
    @pytest.mark.asyncio
    async def test_muscle_gain_high_protein(self):
        """Test that muscle gain plans have high protein."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Should be ~2.0g/kg for 75kg = 150g
        assert plan.protein_g >= 140
        assert plan.protein_g <= 160
    
    @pytest.mark.asyncio
    async def test_fat_loss_high_protein(self):
        """Test that fat loss plans have high protein."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # Should be ~1.8g/kg for 75kg = 135g
        assert plan.protein_g >= 125
        assert plan.protein_g <= 145
    
    @pytest.mark.asyncio
    async def test_macro_sum_equals_calories(self):
        """Test that macros sum to approximately daily calories."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Calculate calories from macros
        calculated_calories = (plan.protein_g * 4) + (plan.carbs_g * 4) + (plan.fats_g * 9)
        
        # Should be within 10% tolerance
        tolerance = plan.daily_calories * 0.1
        assert abs(calculated_calories - plan.daily_calories) <= tolerance


class TestDietaryRestrictions:
    """Test dietary restriction enforcement."""
    
    @pytest.mark.asyncio
    async def test_vegetarian_no_meat(self):
        """Test that vegetarian plans exclude meat and fish."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="vegetarian",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain meat or fish
        meat_fish_keywords = ["chicken", "beef", "pork", "fish", "salmon", "tuna", "turkey", "lamb"]
        
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in meat_fish_keywords:
                assert keyword not in " ".join(ingredients_lower), f"Vegetarian meal contains {keyword}"
    
    @pytest.mark.asyncio
    async def test_vegan_no_animal_products(self):
        """Test that vegan plans exclude all animal products."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="vegan",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain animal products
        animal_keywords = ["chicken", "beef", "pork", "fish", "eggs", "dairy", "milk", "cheese", "yogurt", "honey"]
        
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in animal_keywords:
                assert keyword not in " ".join(ingredients_lower), f"Vegan meal contains {keyword}"
    
    @pytest.mark.asyncio
    async def test_pescatarian_allows_fish_no_meat(self):
        """Test that pescatarian plans allow fish but exclude meat."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="pescatarian",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain meat (but fish is okay)
        meat_keywords = ["chicken", "beef", "pork", "turkey", "lamb"]
        
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in meat_keywords:
                assert keyword not in " ".join(ingredients_lower), f"Pescatarian meal contains {keyword}"


class TestAllergenExclusion:
    """Test allergen and dislike exclusion."""
    
    @pytest.mark.asyncio
    async def test_dairy_allergy_exclusion(self):
        """Test that dairy allergies are respected."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=["dairy"],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain dairy (excluding almond butter which is plant-based)
        dairy_keywords = ["dairy", "milk", "cheese", "yogurt", "paneer", "cream"]
        
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in dairy_keywords:
                assert keyword not in " ".join(ingredients_lower), f"Meal contains dairy allergen: {keyword}"
    
    @pytest.mark.asyncio
    async def test_egg_allergy_exclusion(self):
        """Test that egg allergies are respected."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="omnivore",
            allergies=["eggs"],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="low"
        )
        
        # Check that no sample meals contain eggs
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            assert "egg" not in " ".join(ingredients_lower), "Meal contains egg allergen"
    
    @pytest.mark.asyncio
    async def test_multiple_allergies_exclusion(self):
        """Test that multiple allergies are all respected."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            workout_plan={"frequency": 4},
            diet_type="vegetarian",
            allergies=["dairy", "eggs"],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain dairy or eggs
        allergen_keywords = ["dairy", "milk", "cheese", "yogurt", "egg", "paneer"]
        
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in allergen_keywords:
                assert keyword not in " ".join(ingredients_lower), f"Meal contains allergen: {keyword}"
    
    @pytest.mark.asyncio
    async def test_dislike_exclusion(self):
        """Test that disliked foods are excluded."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=["broccoli", "mushrooms"],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Check that no sample meals contain disliked foods
        for meal in plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            assert "broccoli" not in " ".join(ingredients_lower), "Meal contains disliked food: broccoli"
            assert "mushroom" not in " ".join(ingredients_lower), "Meal contains disliked food: mushrooms"


class TestMealFrequency:
    """Test meal frequency matching."""
    
    @pytest.mark.asyncio
    async def test_meal_frequency_2(self):
        """Test plan with 2 meals per day."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=2,
            meal_prep_level="low"
        )
        
        assert plan.meal_frequency == 2
        assert "Breakfast" in plan.meal_timing_suggestions
        assert "Dinner" in plan.meal_timing_suggestions
    
    @pytest.mark.asyncio
    async def test_meal_frequency_6(self):
        """Test plan with 6 meals per day."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="advanced",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 6},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=6,
            meal_prep_level="high"
        )
        
        assert plan.meal_frequency == 6
        # Should have detailed timing for 6 meals
        assert "7am" in plan.meal_timing_suggestions or "Breakfast" in plan.meal_timing_suggestions


class TestInputValidation:
    """Test input validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_diet_type(self):
        """Test that invalid diet type raises ValueError."""
        generator = MealPlanGenerator()
        
        with pytest.raises(ValueError, match="diet_type must be one of"):
            await generator.generate_plan(
                fitness_level="intermediate",
                primary_goal="muscle_gain",
                workout_plan={"frequency": 4},
                diet_type="paleo",  # Invalid
                allergies=[],
                dislikes=[],
                meal_frequency=4,
                meal_prep_level="medium"
            )
    
    @pytest.mark.asyncio
    async def test_meal_frequency_out_of_range_low(self):
        """Test that meal frequency below 2 raises ValueError."""
        generator = MealPlanGenerator()
        
        with pytest.raises(ValueError, match="meal_frequency must be between 2 and 6"):
            await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="general_fitness",
                workout_plan={"frequency": 3},
                diet_type="omnivore",
                allergies=[],
                dislikes=[],
                meal_frequency=1,  # Too low
                meal_prep_level="low"
            )
    
    @pytest.mark.asyncio
    async def test_meal_frequency_out_of_range_high(self):
        """Test that meal frequency above 6 raises ValueError."""
        generator = MealPlanGenerator()
        
        with pytest.raises(ValueError, match="meal_frequency must be between 2 and 6"):
            await generator.generate_plan(
                fitness_level="advanced",
                primary_goal="muscle_gain",
                workout_plan={"frequency": 6},
                diet_type="omnivore",
                allergies=[],
                dislikes=[],
                meal_frequency=8,  # Too high
                meal_prep_level="high"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_meal_prep_level(self):
        """Test that invalid meal prep level raises ValueError."""
        generator = MealPlanGenerator()
        
        with pytest.raises(ValueError, match="meal_prep_level must be one of"):
            await generator.generate_plan(
                fitness_level="intermediate",
                primary_goal="muscle_gain",
                workout_plan={"frequency": 4},
                diet_type="omnivore",
                allergies=[],
                dislikes=[],
                meal_frequency=4,
                meal_prep_level="expert"  # Invalid
            )


class TestPlanModification:
    """Test plan modification functionality."""
    
    @pytest.mark.asyncio
    async def test_modify_daily_calories(self):
        """Test modifying daily calorie target."""
        generator = MealPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Modify calories
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"daily_calories": 3000}
        )
        
        assert modified_plan.daily_calories == 3000
        # Macros should be adjusted proportionally
        assert modified_plan.protein_g != initial_plan.protein_g
    
    @pytest.mark.asyncio
    async def test_modify_protein(self):
        """Test modifying protein target."""
        generator = MealPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Modify protein
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"protein_g": 180}
        )
        
        assert modified_plan.protein_g == 180
    
    @pytest.mark.asyncio
    async def test_modify_meal_frequency(self):
        """Test modifying meal frequency."""
        generator = MealPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="vegetarian",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="low"
        )
        
        # Modify meal frequency
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"meal_frequency": 5}
        )
        
        assert modified_plan.meal_frequency == 5
        # Meal timing should be updated (just verify it's not empty)
        assert len(modified_plan.meal_timing_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_modify_invalid_calories(self):
        """Test that modifying to invalid calories raises ValueError."""
        generator = MealPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Try to modify to invalid calories
        with pytest.raises(ValueError, match="daily_calories must be between 1200 and 5000"):
            await generator.modify_plan(
                current_plan=initial_plan.model_dump(),
                modifications={"daily_calories": 800}  # Too low
            )
    
    @pytest.mark.asyncio
    async def test_modify_invalid_meal_frequency(self):
        """Test that modifying to invalid meal frequency raises ValueError."""
        generator = MealPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="low"
        )
        
        # Try to modify to invalid meal frequency
        with pytest.raises(ValueError, match="meal_frequency must be between 2 and 6"):
            await generator.modify_plan(
                current_plan=initial_plan.model_dump(),
                modifications={"meal_frequency": 10}  # Too high
            )


class TestSampleMeals:
    """Test sample meal generation."""
    
    @pytest.mark.asyncio
    async def test_sample_meals_generated(self):
        """Test that sample meals are generated."""
        generator = MealPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            workout_plan={"frequency": 4},
            diet_type="omnivore",
            allergies=[],
            dislikes=[],
            meal_frequency=4,
            meal_prep_level="medium"
        )
        
        # Should have at least 3 sample meals
        assert len(plan.sample_meals) >= 3
        
        # Each meal should have required fields
        for meal in plan.sample_meals:
            assert meal.name
            assert len(meal.ingredients) > 0
            assert meal.approximate_calories > 0
            assert meal.approximate_protein_g >= 0
            assert meal.prep_time_minutes > 0
    
    @pytest.mark.asyncio
    async def test_sample_meals_respect_diet_type(self):
        """Test that sample meals respect diet type."""
        generator = MealPlanGenerator()
        
        vegan_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="general_fitness",
            workout_plan={"frequency": 3},
            diet_type="vegan",
            allergies=[],
            dislikes=[],
            meal_frequency=3,
            meal_prep_level="medium"
        )
        
        # Vegan meals should not contain animal products
        animal_keywords = ["chicken", "beef", "pork", "fish", "eggs", "dairy", "milk", "cheese"]
        
        for meal in vegan_plan.sample_meals:
            ingredients_lower = [ing.lower() for ing in meal.ingredients]
            for keyword in animal_keywords:
                assert keyword not in " ".join(ingredients_lower)

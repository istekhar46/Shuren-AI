"""Tests for onboarding service."""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_service import OnboardingService, OnboardingValidationError


class TestOnboardingServiceValidation:
    """Tests for onboarding step validation logic."""
    
    def test_validate_step_1_basic_info_valid(self):
        """Test that valid step 1 data passes validation."""
        service = OnboardingService(None)  # No DB needed for validation
        
        data = {
            "age": 25,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70
        }
        
        # Should not raise exception
        service._validate_step_1_basic_info(data)
    
    def test_validate_step_1_age_too_young(self):
        """Test that age below 13 fails validation."""
        service = OnboardingService(None)
        
        data = {
            "age": 12,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_1_basic_info(data)
        
        assert "age" in str(exc_info.value.message).lower()
    
    def test_validate_step_1_invalid_gender(self):
        """Test that invalid gender fails validation."""
        service = OnboardingService(None)
        
        data = {
            "age": 25,
            "gender": "invalid",
            "height_cm": 175,
            "weight_kg": 70
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_1_basic_info(data)
        
        assert "gender" in str(exc_info.value.message).lower()
    
    def test_validate_step_2_fitness_level_valid(self):
        """Test that valid fitness level passes validation."""
        service = OnboardingService(None)
        
        for level in ["beginner", "intermediate", "advanced"]:
            data = {"fitness_level": level}
            service._validate_step_2_fitness_level(data)
    
    def test_validate_step_2_invalid_fitness_level(self):
        """Test that invalid fitness level fails validation."""
        service = OnboardingService(None)
        
        data = {"fitness_level": "expert"}
        
        with pytest.raises(OnboardingValidationError):
            service._validate_step_2_fitness_level(data)
    
    def test_validate_step_3_fitness_goals_valid(self):
        """Test that valid fitness goals pass validation."""
        service = OnboardingService(None)
        
        data = {
            "goals": [
                {"goal_type": "fat_loss"},
                {"goal_type": "muscle_gain"}
            ]
        }
        
        service._validate_step_3_fitness_goals(data)
    
    def test_validate_step_3_empty_goals(self):
        """Test that empty goals list fails validation."""
        service = OnboardingService(None)
        
        data = {"goals": []}
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_3_fitness_goals(data)
        
        assert "at least one goal" in str(exc_info.value.message).lower()
    
    def test_validate_step_7_meal_planning_valid(self):
        """Test that valid meal planning data passes validation."""
        service = OnboardingService(None)
        
        data = {
            "daily_calorie_target": 2000,
            "protein_percentage": 30,
            "carbs_percentage": 40,
            "fats_percentage": 30
        }
        
        service._validate_step_7_meal_planning(data)
    
    def test_validate_step_7_macros_not_sum_to_100(self):
        """Test that macros not summing to 100 fails validation."""
        service = OnboardingService(None)
        
        data = {
            "daily_calorie_target": 2000,
            "protein_percentage": 30,
            "carbs_percentage": 40,
            "fats_percentage": 20  # Sum = 90, not 100
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_7_meal_planning(data)
        
        assert "sum to 100" in str(exc_info.value.message).lower()
    
    def test_validate_step_8_meal_schedule_valid(self):
        """Test that valid meal schedule passes validation."""
        service = OnboardingService(None)
        
        data = {
            "meals": [
                {"meal_name": "breakfast", "scheduled_time": "08:00"},
                {"meal_name": "lunch", "scheduled_time": "12:30"},
                {"meal_name": "dinner", "scheduled_time": "19:00"}
            ]
        }
        
        service._validate_step_8_meal_schedule(data)
    
    def test_validate_step_8_invalid_time_format(self):
        """Test that invalid time format fails validation."""
        service = OnboardingService(None)
        
        data = {
            "meals": [
                {"meal_name": "breakfast", "scheduled_time": "25:00"}  # Invalid hour
            ]
        }
        
        with pytest.raises(OnboardingValidationError):
            service._validate_step_8_meal_schedule(data)
    
    def test_validate_step_9_workout_schedule_valid(self):
        """Test that valid workout schedule passes validation."""
        service = OnboardingService(None)
        
        data = {
            "workouts": [
                {"day_of_week": 0, "scheduled_time": "06:00"},  # Monday
                {"day_of_week": 2, "scheduled_time": "18:00"},  # Wednesday
                {"day_of_week": 4, "scheduled_time": "06:00"}   # Friday
            ]
        }
        
        service._validate_step_9_workout_schedule(data)
    
    def test_validate_step_9_invalid_day_of_week(self):
        """Test that invalid day_of_week fails validation."""
        service = OnboardingService(None)
        
        data = {
            "workouts": [
                {"day_of_week": 7, "scheduled_time": "06:00"}  # Invalid, must be 0-6
            ]
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_9_workout_schedule(data)
        
        assert "day_of_week" in str(exc_info.value.message).lower()
    
    def test_validate_step_10_hydration_valid(self):
        """Test that valid hydration preferences pass validation."""
        service = OnboardingService(None)
        
        data = {
            "daily_water_target_ml": 2000,
            "reminder_frequency_minutes": 60
        }
        
        service._validate_step_10_hydration(data)
    
    def test_validate_step_10_water_target_too_low(self):
        """Test that water target below minimum fails validation."""
        service = OnboardingService(None)
        
        data = {
            "daily_water_target_ml": 400  # Below 500 minimum
        }
        
        with pytest.raises(OnboardingValidationError):
            service._validate_step_10_hydration(data)
    
    def test_validate_step_11_lifestyle_baseline_valid(self):
        """Test that valid lifestyle baseline passes validation."""
        service = OnboardingService(None)
        
        data = {
            "energy_level": 7,
            "stress_level": 5,
            "sleep_quality": 8
        }
        
        service._validate_step_11_lifestyle_baseline(data)
    
    def test_validate_step_11_value_out_of_range(self):
        """Test that lifestyle values outside 1-10 range fail validation."""
        service = OnboardingService(None)
        
        data = {
            "energy_level": 11,  # Above 10
            "stress_level": 5,
            "sleep_quality": 8
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_11_lifestyle_baseline(data)
        
        assert "1 and 10" in str(exc_info.value.message)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestOnboardingServiceIntegration:
    """Integration tests for onboarding service with meal template generation."""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_generates_meal_templates(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """Test that completing onboarding generates 4 meal templates."""
        from app.services.onboarding_service import OnboardingService
        from app.models.meal_template import MealTemplate, TemplateMeal
        from app.models.dish import Dish, Ingredient, DishIngredient
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Create sample dishes for template generation
        # We need at least 3 dishes per meal type for alternatives
        # Dishes need to match the calorie/protein targets from the meal plan
        # Daily target: 2500 calories, 30% protein = 750 cal from protein = 187.5g protein
        # Per meal (3 meals): ~833 calories, ~62.5g protein
        # Acceptable range: ±15% calories (708-958), ±20% protein (50-75g)
        
        dishes_data = []
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            for i in range(3):
                # Create dishes that fit within the acceptable ranges
                dish = Dish(
                    name=f"Test {meal_type.capitalize()} Dish {i+1}",
                    cuisine_type='north_indian',
                    meal_type=meal_type,
                    serving_size_g=300,
                    calories=800,  # Within 708-958 range
                    protein_g=60,  # Within 50-75g range
                    carbs_g=90,
                    fats_g=25,
                    prep_time_minutes=10,
                    cook_time_minutes=15,
                    difficulty_level='easy',
                    is_vegetarian=True,
                    is_vegan=False,
                    is_gluten_free=False,
                    is_dairy_free=False,
                    is_nut_free=True,
                    contains_allergens=[],
                    is_active=True,
                    popularity_score=50 + i  # Different popularity for variety
                )
                db_session.add(dish)
                dishes_data.append(dish)
        
        await db_session.flush()
        await db_session.commit()
        
        # Create onboarding service
        service = OnboardingService(db_session)
        
        # Get onboarding state
        onboarding_state = await service.get_onboarding_state(test_user.id)
        
        # Complete all onboarding steps
        complete_data = {
            "step_1": {
                "age": 28,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 75
            },
            "step_2": {
                "fitness_level": "intermediate"
            },
            "step_3": {
                "goals": [
                    {"goal_type": "muscle_gain"}
                ]
            },
            "step_4": {
                "target_weight_kg": 80,
                "target_body_fat_percentage": 15
            },
            "step_5": {
                "constraints": []
            },
            "step_6": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            "step_7": {
                "daily_calorie_target": 2500,
                "protein_percentage": 30,
                "carbs_percentage": 45,
                "fats_percentage": 25
            },
            "step_8": {
                "meals": [
                    {"meal_name": "breakfast", "scheduled_time": "08:00"},
                    {"meal_name": "lunch", "scheduled_time": "13:00"},
                    {"meal_name": "dinner", "scheduled_time": "19:00"}
                ]
            },
            "step_9": {
                "workouts": [
                    {"day_of_week": 1, "scheduled_time": "18:00"},
                    {"day_of_week": 3, "scheduled_time": "18:00"},
                    {"day_of_week": 5, "scheduled_time": "18:00"}
                ]
            },
            "step_10": {
                "daily_water_target_ml": 3000,
                "reminder_frequency_minutes": 60
            },
            "step_11": {
                "energy_level": 7,
                "stress_level": 5,
                "sleep_quality": 6
            }
        }
        
        # Save all steps
        for step_num in range(1, 12):
            await service.save_onboarding_step(
                test_user.id,
                step_num,
                complete_data[f"step_{step_num}"]
            )
        
        # Complete onboarding
        profile = await service.complete_onboarding(test_user.id)
        
        # Verify profile was created
        assert profile is not None
        assert profile.is_locked is True
        
        # Verify 4 meal templates were created
        result = await db_session.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile.id,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
            )
        )
        templates = result.scalars().all()
        
        assert len(templates) == 4, f"Expected 4 templates, got {len(templates)}"
        
        # Verify each week number is present
        week_numbers = sorted([t.week_number for t in templates])
        assert week_numbers == [1, 2, 3, 4], f"Expected weeks [1,2,3,4], got {week_numbers}"
        
        # Verify each template has meals (check count without accessing lazy-loaded relationship)
        for template in templates:
            meal_count = len(template.template_meals)
            assert meal_count > 0, f"Template week {template.week_number} has no meals (count: {meal_count})"
    
    @pytest.mark.asyncio
    async def test_meal_templates_respect_dietary_preferences(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """Test that meal templates respect user's dietary preferences."""
        from app.services.onboarding_service import OnboardingService
        from app.models.meal_template import MealTemplate, TemplateMeal
        from app.models.dish import Dish
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Create vegetarian and non-vegetarian dishes
        veg_dishes = []
        non_veg_dishes = []
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            # Create vegetarian dishes
            for i in range(3):
                dish = Dish(
                    name=f"Veg {meal_type.capitalize()} {i+1}",
                    cuisine_type='north_indian',
                    meal_type=meal_type,
                    serving_size_g=300,
                    calories=400,
                    protein_g=20,
                    carbs_g=50,
                    fats_g=15,
                    prep_time_minutes=10,
                    cook_time_minutes=15,
                    difficulty_level='easy',
                    is_vegetarian=True,
                    is_vegan=False,
                    is_gluten_free=False,
                    is_dairy_free=False,
                    is_nut_free=True,
                    contains_allergens=[],
                    is_active=True,
                    popularity_score=50
                )
                db_session.add(dish)
                veg_dishes.append(dish)
            
            # Create non-vegetarian dishes
            for i in range(3):
                dish = Dish(
                    name=f"Non-Veg {meal_type.capitalize()} {i+1}",
                    cuisine_type='north_indian',
                    meal_type=meal_type,
                    serving_size_g=300,
                    calories=450,
                    protein_g=30,
                    carbs_g=40,
                    fats_g=20,
                    prep_time_minutes=15,
                    cook_time_minutes=20,
                    difficulty_level='medium',
                    is_vegetarian=False,
                    is_vegan=False,
                    is_gluten_free=False,
                    is_dairy_free=False,
                    is_nut_free=True,
                    contains_allergens=[],
                    is_active=True,
                    popularity_score=60
                )
                db_session.add(dish)
                non_veg_dishes.append(dish)
        
        await db_session.flush()
        
        # Create onboarding service
        service = OnboardingService(db_session)
        
        # Complete onboarding with VEGETARIAN preference
        complete_data = {
            "step_1": {
                "age": 25,
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 60
            },
            "step_2": {
                "fitness_level": "beginner"
            },
            "step_3": {
                "goals": [
                    {"goal_type": "general_fitness"}
                ]
            },
            "step_4": {
                "target_weight_kg": None,
                "target_body_fat_percentage": None
            },
            "step_5": {
                "constraints": []
            },
            "step_6": {
                "diet_type": "vegetarian",  # VEGETARIAN
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            "step_7": {
                "daily_calorie_target": 1800,
                "protein_percentage": 25,
                "carbs_percentage": 50,
                "fats_percentage": 25
            },
            "step_8": {
                "meals": [
                    {"meal_name": "breakfast", "scheduled_time": "07:00"},
                    {"meal_name": "lunch", "scheduled_time": "12:00"},
                    {"meal_name": "dinner", "scheduled_time": "18:00"}
                ]
            },
            "step_9": {
                "workouts": [
                    {"day_of_week": 0, "scheduled_time": "06:00"}
                ]
            },
            "step_10": {
                "daily_water_target_ml": 2000,
                "reminder_frequency_minutes": 120
            },
            "step_11": {
                "energy_level": 5,
                "stress_level": 5,
                "sleep_quality": 5
            }
        }
        
        # Save all steps
        for step_num in range(1, 12):
            await service.save_onboarding_step(
                test_user.id,
                step_num,
                complete_data[f"step_{step_num}"]
            )
        
        # Complete onboarding
        profile = await service.complete_onboarding(test_user.id)
        
        # Get all templates with dishes
        result = await db_session.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile.id,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish)
            )
        )
        templates = result.scalars().all()
        
        # Verify all dishes in templates are vegetarian
        for template in templates:
            for template_meal in template.template_meals:
                dish = template_meal.dish
                assert dish.is_vegetarian is True, \
                    f"Non-vegetarian dish '{dish.name}' found in vegetarian user's template"
    
    @pytest.mark.asyncio
    async def test_meal_templates_exclude_allergens(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """Test that meal templates exclude dishes with user's allergens."""
        from app.services.onboarding_service import OnboardingService
        from app.models.meal_template import MealTemplate, TemplateMeal
        from app.models.dish import Dish
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Create dishes with and without peanuts
        safe_dishes = []
        peanut_dishes = []
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            # Create safe dishes (no peanuts)
            for i in range(3):
                dish = Dish(
                    name=f"Safe {meal_type.capitalize()} {i+1}",
                    cuisine_type='north_indian',
                    meal_type=meal_type,
                    serving_size_g=300,
                    calories=400,
                    protein_g=25,
                    carbs_g=45,
                    fats_g=15,
                    prep_time_minutes=10,
                    cook_time_minutes=15,
                    difficulty_level='easy',
                    is_vegetarian=True,
                    is_vegan=False,
                    is_gluten_free=False,
                    is_dairy_free=False,
                    is_nut_free=True,
                    contains_allergens=[],  # No allergens
                    is_active=True,
                    popularity_score=50
                )
                db_session.add(dish)
                safe_dishes.append(dish)
            
            # Create dishes with peanuts
            for i in range(2):
                dish = Dish(
                    name=f"Peanut {meal_type.capitalize()} {i+1}",
                    cuisine_type='north_indian',
                    meal_type=meal_type,
                    serving_size_g=300,
                    calories=450,
                    protein_g=28,
                    carbs_g=40,
                    fats_g=20,
                    prep_time_minutes=10,
                    cook_time_minutes=15,
                    difficulty_level='easy',
                    is_vegetarian=True,
                    is_vegan=False,
                    is_gluten_free=False,
                    is_dairy_free=False,
                    is_nut_free=False,
                    contains_allergens=['peanuts'],  # Contains peanuts
                    is_active=True,
                    popularity_score=60
                )
                db_session.add(dish)
                peanut_dishes.append(dish)
        
        await db_session.flush()
        
        # Create onboarding service
        service = OnboardingService(db_session)
        
        # Complete onboarding with PEANUT ALLERGY
        complete_data = {
            "step_1": {
                "age": 30,
                "gender": "male",
                "height_cm": 180,
                "weight_kg": 80
            },
            "step_2": {
                "fitness_level": "intermediate"
            },
            "step_3": {
                "goals": [
                    {"goal_type": "fat_loss"}
                ]
            },
            "step_4": {
                "target_weight_kg": 75,
                "target_body_fat_percentage": None
            },
            "step_5": {
                "constraints": []
            },
            "step_6": {
                "diet_type": "omnivore",
                "allergies": ["peanuts"],  # PEANUT ALLERGY
                "intolerances": [],
                "dislikes": []
            },
            "step_7": {
                "daily_calorie_target": 2200,
                "protein_percentage": 30,
                "carbs_percentage": 40,
                "fats_percentage": 30
            },
            "step_8": {
                "meals": [
                    {"meal_name": "breakfast", "scheduled_time": "07:30"},
                    {"meal_name": "lunch", "scheduled_time": "12:30"},
                    {"meal_name": "dinner", "scheduled_time": "19:00"}
                ]
            },
            "step_9": {
                "workouts": [
                    {"day_of_week": 1, "scheduled_time": "06:00"},
                    {"day_of_week": 3, "scheduled_time": "06:00"}
                ]
            },
            "step_10": {
                "daily_water_target_ml": 2500,
                "reminder_frequency_minutes": 90
            },
            "step_11": {
                "energy_level": 6,
                "stress_level": 6,
                "sleep_quality": 7
            }
        }
        
        # Save all steps
        for step_num in range(1, 12):
            await service.save_onboarding_step(
                test_user.id,
                step_num,
                complete_data[f"step_{step_num}"]
            )
        
        # Complete onboarding
        profile = await service.complete_onboarding(test_user.id)
        
        # Get all templates with dishes
        result = await db_session.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile.id,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish)
            )
        )
        templates = result.scalars().all()
        
        # Verify no dishes contain peanuts
        for template in templates:
            for template_meal in template.template_meals:
                dish = template_meal.dish
                assert 'peanuts' not in dish.contains_allergens, \
                    f"Dish '{dish.name}' contains peanuts but user is allergic"
    
    @pytest.mark.asyncio
    async def test_existing_onboarding_tests_still_pass(
        self,
        db_session: AsyncSession,
        test_user
    ):
        """Test that existing onboarding functionality still works."""
        from app.services.onboarding_service import OnboardingService
        
        service = OnboardingService(db_session)
        
        # Test basic step validation still works
        valid_step_1 = {
            "age": 25,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70
        }
        
        # Should not raise exception
        service._validate_step_1_basic_info(valid_step_1)
        
        # Test saving a step still works
        onboarding_state = await service.save_onboarding_step(
            test_user.id,
            1,
            valid_step_1
        )
        
        assert onboarding_state is not None
        assert onboarding_state.current_step == 1
        assert "step_1" in onboarding_state.step_data
        assert onboarding_state.step_data["step_1"]["age"] == 25

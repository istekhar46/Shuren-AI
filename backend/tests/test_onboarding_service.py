"""Tests for onboarding service."""

import pytest
from uuid import uuid4

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

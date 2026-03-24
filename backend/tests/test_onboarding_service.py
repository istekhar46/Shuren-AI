"""Tests for onboarding service."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.onboarding_service import OnboardingService, OnboardingValidationError

class TestOnboardingServiceValidation:
    """Tests for onboarding step validation logic."""

    def test_validate_step_2_fitness_level_valid(self):
        """Test that valid fitness level passes validation."""
        service = OnboardingService(None)
        for level in ['beginner', 'intermediate', 'advanced']:
            data = {'fitness_level': level}
            service._validate_step_2_fitness_level(data)

    def test_validate_step_2_invalid_fitness_level(self):
        """Test that invalid fitness level fails validation."""
        service = OnboardingService(None)
        data = {'fitness_level': 'expert'}
        with pytest.raises(OnboardingValidationError):
            service._validate_step_2_fitness_level(data)

    def test_validate_step_3_fitness_goals_valid(self):
        """Test that valid fitness goals pass validation."""
        service = OnboardingService(None)
        data = {'goals': [{'goal_type': 'fat_loss'}, {'goal_type': 'muscle_gain'}]}
        service._validate_step_3_fitness_goals(data)

    def test_validate_step_3_empty_goals(self):
        """Test that empty goals list fails validation."""
        service = OnboardingService(None)
        data = {'goals': []}
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_3_fitness_goals(data)
        assert 'at least one goal' in str(exc_info.value.message).lower()

    def test_validate_step_7_meal_planning_valid(self):
        """Test that valid meal planning data passes validation."""
        service = OnboardingService(None)
        data = {'daily_calorie_target': 2000, 'protein_percentage': 30, 'carbs_percentage': 40, 'fats_percentage': 30}
        service._validate_step_7_meal_planning(data)

    def test_validate_step_7_macros_not_sum_to_100(self):
        """Test that macros not summing to 100 fails validation."""
        service = OnboardingService(None)
        data = {'daily_calorie_target': 2000, 'protein_percentage': 30, 'carbs_percentage': 40, 'fats_percentage': 20}
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_7_meal_planning(data)
        assert 'sum to 100' in str(exc_info.value.message).lower()

    def test_validate_step_8_meal_schedule_valid(self):
        """Test that valid meal schedule passes validation."""
        service = OnboardingService(None)
        data = {'meals': [{'meal_name': 'breakfast', 'scheduled_time': '08:00'}, {'meal_name': 'lunch', 'scheduled_time': '12:30'}, {'meal_name': 'dinner', 'scheduled_time': '19:00'}]}
        service._validate_step_8_meal_schedule(data)

    def test_validate_step_8_invalid_time_format(self):
        """Test that invalid time format fails validation."""
        service = OnboardingService(None)
        data = {'meals': [{'meal_name': 'breakfast', 'scheduled_time': '25:00'}]}
        with pytest.raises(OnboardingValidationError):
            service._validate_step_8_meal_schedule(data)

    def test_validate_step_9_workout_schedule_valid(self):
        """Test that valid workout schedule passes validation."""
        service = OnboardingService(None)
        data = {'workouts': [{'day_of_week': 0, 'scheduled_time': '06:00'}, {'day_of_week': 2, 'scheduled_time': '18:00'}, {'day_of_week': 4, 'scheduled_time': '06:00'}]}
        service._validate_step_9_workout_schedule(data)

    def test_validate_step_9_invalid_day_of_week(self):
        """Test that invalid day_of_week fails validation."""
        service = OnboardingService(None)
        data = {'workouts': [{'day_of_week': 7, 'scheduled_time': '06:00'}]}
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_step_9_workout_schedule(data)
        assert 'day_of_week' in str(exc_info.value.message).lower()

    def test_validate_step_10_hydration_valid(self):
        """Test that valid hydration preferences pass validation."""
        service = OnboardingService(None)
        data = {'daily_water_target_ml': 2000, 'reminder_frequency_minutes': 60}
        service._validate_step_10_hydration(data)

    def test_validate_step_10_water_target_too_low(self):
        """Test that water target below minimum fails validation."""
        service = OnboardingService(None)
        data = {'daily_water_target_ml': 400}
        with pytest.raises(OnboardingValidationError):
            service._validate_step_10_hydration(data)
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

class TestOnboardingServiceIntegration:
    """Integration tests for onboarding service with meal template generation."""

    @pytest.mark.asyncio
    async def test_existing_onboarding_tests_still_pass(self, db_session: AsyncSession, test_user):
        """Test that existing onboarding functionality still works."""
        from app.services.onboarding_service import OnboardingService
        service = OnboardingService(db_session)
        valid_step_1 = {'age': 25, 'gender': 'male', 'height_cm': 175, 'weight_kg': 70}
        service._validate_step_1_basic_info(valid_step_1)
        onboarding_state = await service.save_onboarding_step(test_user.id, 1, valid_step_1)
        assert onboarding_state is not None
        assert onboarding_state.current_step == 1
        assert 'step_1' in onboarding_state.step_data
        assert onboarding_state.step_data['step_1']['age'] == 25
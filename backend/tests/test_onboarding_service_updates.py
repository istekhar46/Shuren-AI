"""Tests for OnboardingService updates (9-state onboarding flow).

This module tests the new methods and validators added for the 9-state
onboarding flow:
- get_progress: Progress tracking with completion percentage
- can_complete_onboarding: Validation that all states are complete
- _validate_state_3_workout_constraints: Merged validation for state 3
"""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_service import (
    OnboardingService,
    OnboardingValidationError,
    STATE_METADATA
)
from app.models.onboarding import OnboardingState
from app.models.user import User


class TestGetProgress:
    """Tests for OnboardingService.get_progress method."""
    
    @pytest.mark.asyncio
    async def test_get_progress_no_states_completed(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test get_progress when no states are completed.
        
        Note: When current_step is 0, we manually set it to 1 to get state 1 metadata.
        This is because STATE_METADATA only has keys 1-9, not 0.
        """
        service = OnboardingService(db_session)
        
        # Manually set current_step to 1 (first state) since state 0 doesn't exist in metadata
        state = await service.get_onboarding_state(test_user.id)
        state.current_step = 1
        await db_session.commit()
        
        # Get progress for user with no completed states
        progress = await service.get_progress(test_user.id)
        
        # Verify progress structure
        assert progress.current_state == 1
        assert progress.total_states == 9
        assert progress.completed_states == []
        assert progress.completion_percentage == 0
        assert progress.can_complete is False
        assert progress.is_complete is False
        
        # Verify state metadata
        assert progress.current_state_info.state_number == 1
        assert progress.current_state_info.name == "Fitness Level Assessment"
        assert progress.next_state_info is not None
        assert progress.next_state_info.state_number == 2
    
    @pytest.mark.asyncio
    async def test_get_progress_partial_completion(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test get_progress with some states completed."""
        service = OnboardingService(db_session)
        
        # Complete states 1, 2, and 3
        await service.save_onboarding_step(
            test_user.id,
            1,
            {"fitness_level": "intermediate"}
        )
        await service.save_onboarding_step(
            test_user.id,
            2,
            {"goals": [{"goal_type": "muscle_gain"}]}
        )
        await service.save_onboarding_step(
            test_user.id,
            3,
            {
                "equipment": ["dumbbells"],
                "injuries": [],
                "limitations": []
            }
        )
        
        # Get progress
        progress = await service.get_progress(test_user.id)
        
        # Verify progress
        assert progress.current_state == 3
        assert progress.total_states == 9
        assert progress.completed_states == [1, 2, 3]
        assert progress.completion_percentage == 33  # 3/9 * 100 = 33.33 -> 33
        assert progress.can_complete is False
        assert progress.is_complete is False
        
        # Verify current state info
        assert progress.current_state_info.state_number == 3
        assert progress.current_state_info.name == "Workout Preferences & Constraints"
        assert progress.current_state_info.agent == "workout_planning"
        
        # Verify next state info
        assert progress.next_state_info is not None
        assert progress.next_state_info.state_number == 4
        assert progress.next_state_info.name == "Diet Preferences & Restrictions"
    
    @pytest.mark.asyncio
    async def test_get_progress_all_states_completed(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test get_progress when all 9 states are completed."""
        service = OnboardingService(db_session)
        
        # Complete all 9 states with correct data format for each validator
        test_data = {
            1: {"fitness_level": "advanced"},
            2: {"goals": [{"goal_type": "fat_loss"}]},
            3: {
                "equipment": ["barbell", "dumbbells"],
                "injuries": ["knee"],
                "limitations": [],
                "target_weight_kg": 75.0
            },
            4: {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            5: {
                "daily_calorie_target": 2200,
                "protein_percentage": 30,
                "carbs_percentage": 40,
                "fats_percentage": 30
            },
            6: {
                "meals": [
                    {"meal_name": "breakfast", "scheduled_time": "08:00"},
                    {"meal_name": "lunch", "scheduled_time": "13:00"},
                    {"meal_name": "dinner", "scheduled_time": "19:00"}
                ]
            },
            7: {
                "workouts": [
                    {"day_of_week": 1, "scheduled_time": "18:00"},
                    {"day_of_week": 3, "scheduled_time": "18:00"}
                ]
            },
            8: {
                "daily_water_target_ml": 2500,
                "reminder_frequency_minutes": 90
            },
            9: {
                "interested_in_supplements": True,
                "current_supplements": ["protein powder", "creatine"]
            }
        }
        
        for step, data in test_data.items():
            await service.save_onboarding_step(test_user.id, step, data)
        
        # Get progress
        progress = await service.get_progress(test_user.id)
        
        # Verify progress
        assert progress.current_state == 9
        assert progress.total_states == 9
        assert progress.completed_states == [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert progress.completion_percentage == 100
        assert progress.can_complete is True
        assert progress.is_complete is False  # Not marked complete until complete_onboarding called
        
        # Verify current state info
        assert progress.current_state_info.state_number == 9
        assert progress.current_state_info.name == "Supplement Preferences"
        
        # Verify next state info is None (last state)
        assert progress.next_state_info is None
    
    @pytest.mark.asyncio
    async def test_get_progress_non_sequential_completion(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test get_progress with non-sequential state completion."""
        service = OnboardingService(db_session)
        
        # Get onboarding state and manually set step_data
        state = await service.get_onboarding_state(test_user.id)
        state.step_data = {
            "step_1": {"fitness_level": "beginner"},
            "step_3": {"equipment": [], "injuries": [], "limitations": []},
            "step_5": {
                "daily_calorie_target": 1800,
                "protein_percentage": 25,
                "carbs_percentage": 50,
                "fats_percentage": 25
            }
        }
        state.current_step = 5
        await db_session.commit()
        
        # Get progress
        progress = await service.get_progress(test_user.id)
        
        # Verify only completed states are counted
        assert progress.completed_states == [1, 3, 5]
        assert progress.completion_percentage == 33  # 3/9 * 100
        assert progress.can_complete is False
    
    @pytest.mark.asyncio
    async def test_get_progress_raises_error_if_state_not_found(
        self,
        db_session: AsyncSession
    ):
        """Test get_progress raises error if onboarding state doesn't exist."""
        service = OnboardingService(db_session)
        
        # Try to get progress for non-existent user
        non_existent_user_id = uuid4()
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            await service.get_progress(non_existent_user_id)
        
        assert "not found" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_get_progress_percentage_calculation(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test completion percentage calculation for various completion states."""
        service = OnboardingService(db_session)
        
        # Test different completion levels (skip 0 since STATE_METADATA doesn't have key 0)
        test_cases = [
            (1, 0),    # 0 completed, current_step=1 -> 0%
            (1, 11),   # 1/9 = 11.11% -> 11%
            (2, 22),   # 2/9 = 22.22% -> 22%
            (3, 33),   # 3/9 = 33.33% -> 33%
            (4, 44),   # 4/9 = 44.44% -> 44%
            (5, 55),   # 5/9 = 55.55% -> 55%
            (6, 66),   # 6/9 = 66.66% -> 66%
            (7, 77),   # 7/9 = 77.77% -> 77%
            (8, 88),   # 8/9 = 88.88% -> 88%
            (9, 100),  # 9/9 = 100%
        ]
        
        for current_step, expected_percentage in test_cases:
            # Reset state
            state = await service.get_onboarding_state(test_user.id)
            state.step_data = {}
            state.current_step = current_step
            
            # Add completed states (for current_step=1 with 0%, add no states)
            num_completed = 0 if expected_percentage == 0 else current_step
            for i in range(1, num_completed + 1):
                state.step_data[f"step_{i}"] = {"test": "data"}
            
            await db_session.commit()
            
            # Get progress and verify percentage
            progress = await service.get_progress(test_user.id)
            assert progress.completion_percentage == expected_percentage, \
                f"Expected {expected_percentage}% for current_step={current_step}, got {progress.completion_percentage}%"


class TestCanCompleteOnboarding:
    """Tests for OnboardingService.can_complete_onboarding method."""
    
    @pytest.mark.asyncio
    async def test_can_complete_with_all_states(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test can_complete_onboarding returns True when all states are complete."""
        service = OnboardingService(db_session)
        
        # Complete all 9 states with valid data
        test_data = {
            1: {"fitness_level": "intermediate"},
            2: {"goals": [{"goal_type": "muscle_gain"}]},
            3: {"equipment": [], "injuries": [], "limitations": []},
            4: {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
            5: {"daily_calorie_target": 2000, "protein_percentage": 30, "carbs_percentage": 40, "fats_percentage": 30},
            6: {"meals": [{"meal_name": "breakfast", "scheduled_time": "08:00"}]},
            7: {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00"}]},
            8: {"daily_water_target_ml": 2000, "reminder_frequency_minutes": 60},
            9: {"interested_in_supplements": False, "current_supplements": []}
        }
        
        for step, data in test_data.items():
            await service.save_onboarding_step(test_user.id, step, data)
        
        # Check if can complete
        can_complete = await service.can_complete_onboarding(test_user.id)
        
        assert can_complete is True
    
    @pytest.mark.asyncio
    async def test_can_complete_with_missing_states(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test can_complete_onboarding returns False when states are missing."""
        service = OnboardingService(db_session)
        
        # Complete only states 1-7 (missing 8 and 9) with valid data
        test_data = {
            1: {"fitness_level": "beginner"},
            2: {"goals": [{"goal_type": "fat_loss"}]},
            3: {"equipment": [], "injuries": [], "limitations": []},
            4: {"diet_type": "vegetarian", "allergies": [], "intolerances": [], "dislikes": []},
            5: {"daily_calorie_target": 1800, "protein_percentage": 25, "carbs_percentage": 50, "fats_percentage": 25},
            6: {"meals": [{"meal_name": "breakfast", "scheduled_time": "07:00"}]},
            7: {"workouts": [{"day_of_week": 0, "scheduled_time": "06:00"}]}
        }
        
        for step, data in test_data.items():
            await service.save_onboarding_step(test_user.id, step, data)
        
        # Check if can complete
        can_complete = await service.can_complete_onboarding(test_user.id)
        
        assert can_complete is False
    
    @pytest.mark.asyncio
    async def test_can_complete_with_no_states(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test can_complete_onboarding returns False when no states are complete."""
        service = OnboardingService(db_session)
        
        # Check if can complete with no states
        can_complete = await service.can_complete_onboarding(test_user.id)
        
        assert can_complete is False
    
    @pytest.mark.asyncio
    async def test_can_complete_with_empty_step_data(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test can_complete_onboarding handles empty step_data gracefully."""
        service = OnboardingService(db_session)
        
        # Manually set step_data to None
        state = await service.get_onboarding_state(test_user.id)
        state.step_data = None
        await db_session.commit()
        
        # Check if can complete
        can_complete = await service.can_complete_onboarding(test_user.id)
        
        assert can_complete is False
    
    @pytest.mark.asyncio
    async def test_can_complete_raises_error_if_state_not_found(
        self,
        db_session: AsyncSession
    ):
        """Test can_complete_onboarding raises error if state doesn't exist."""
        service = OnboardingService(db_session)
        
        # Try with non-existent user
        non_existent_user_id = uuid4()
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            await service.can_complete_onboarding(non_existent_user_id)
        
        assert "not found" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_can_complete_with_specific_missing_state(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test can_complete_onboarding with specific missing states."""
        service = OnboardingService(db_session)
        
        # Test missing each state individually
        for missing_state in range(1, 10):
            # Reset state
            state = await service.get_onboarding_state(test_user.id)
            state.step_data = {}
            
            # Add all states except the missing one
            for step in range(1, 10):
                if step != missing_state:
                    state.step_data[f"step_{step}"] = {"test": "data"}
            
            await db_session.commit()
            
            # Check if can complete
            can_complete = await service.can_complete_onboarding(test_user.id)
            
            assert can_complete is False, \
                f"Expected False when state {missing_state} is missing"


class TestValidateState3WorkoutConstraints:
    """Tests for merged state 3 validation (_validate_state_3_workout_constraints)."""
    
    def test_validate_state_3_valid_minimal(self):
        """Test state 3 validation with minimal valid data."""
        service = OnboardingService(None)
        
        data = {
            "equipment": ["dumbbells"],
            "injuries": [],
            "limitations": []
        }
        
        # Should not raise exception
        service._validate_state_3_workout_constraints(data)
    
    def test_validate_state_3_valid_with_targets(self):
        """Test state 3 validation with optional target metrics."""
        service = OnboardingService(None)
        
        data = {
            "equipment": ["barbell", "dumbbells", "pull_up_bar"],
            "injuries": ["knee"],
            "limitations": ["lower_back_pain"],
            "target_weight_kg": 75.5,
            "target_body_fat_percentage": 15.0
        }
        
        # Should not raise exception
        service._validate_state_3_workout_constraints(data)
    
    def test_validate_state_3_missing_equipment(self):
        """Test state 3 validation fails when equipment is missing."""
        service = OnboardingService(None)
        
        data = {
            "injuries": [],
            "limitations": []
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "equipment" in str(exc_info.value.field).lower()
    
    def test_validate_state_3_equipment_not_list(self):
        """Test state 3 validation fails when equipment is not a list."""
        service = OnboardingService(None)
        
        data = {
            "equipment": "dumbbells",  # Should be list
            "injuries": [],
            "limitations": []
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "equipment" in str(exc_info.value.field).lower()
        assert "list" in str(exc_info.value.message).lower()
    
    def test_validate_state_3_missing_injuries(self):
        """Test state 3 validation fails when injuries is missing."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "limitations": []
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "injuries" in str(exc_info.value.field).lower()
    
    def test_validate_state_3_injuries_not_list(self):
        """Test state 3 validation fails when injuries is not a list."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": "knee",  # Should be list
            "limitations": []
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "injuries" in str(exc_info.value.field).lower()
    
    def test_validate_state_3_missing_limitations(self):
        """Test state 3 validation fails when limitations is missing."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": []
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "limitations" in str(exc_info.value.field).lower()
    
    def test_validate_state_3_limitations_not_list(self):
        """Test state 3 validation fails when limitations is not a list."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": "back_pain"  # Should be list
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "limitations" in str(exc_info.value.field).lower()
    
    def test_validate_state_3_target_weight_too_low(self):
        """Test state 3 validation fails when target weight is below minimum."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": 25  # Below 30 minimum
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "target_weight_kg" in str(exc_info.value.field).lower()
        assert "30" in str(exc_info.value.message)
    
    def test_validate_state_3_target_weight_too_high(self):
        """Test state 3 validation fails when target weight is above maximum."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": 350  # Above 300 maximum
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "target_weight_kg" in str(exc_info.value.field).lower()
        assert "300" in str(exc_info.value.message)
    
    def test_validate_state_3_target_weight_boundary_values(self):
        """Test state 3 validation with boundary values for target weight."""
        service = OnboardingService(None)
        
        # Test minimum boundary (30 kg)
        data_min = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": 30
        }
        service._validate_state_3_workout_constraints(data_min)
        
        # Test maximum boundary (300 kg)
        data_max = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": 300
        }
        service._validate_state_3_workout_constraints(data_max)
    
    def test_validate_state_3_body_fat_too_low(self):
        """Test state 3 validation fails when body fat percentage is below minimum."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_body_fat_percentage": 0.5  # Below 1 minimum
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "target_body_fat_percentage" in str(exc_info.value.field).lower()
        assert "1" in str(exc_info.value.message)
    
    def test_validate_state_3_body_fat_too_high(self):
        """Test state 3 validation fails when body fat percentage is above maximum."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_body_fat_percentage": 55  # Above 50 maximum
        }
        
        with pytest.raises(OnboardingValidationError) as exc_info:
            service._validate_state_3_workout_constraints(data)
        
        assert "target_body_fat_percentage" in str(exc_info.value.field).lower()
        assert "50" in str(exc_info.value.message)
    
    def test_validate_state_3_body_fat_boundary_values(self):
        """Test state 3 validation with boundary values for body fat percentage."""
        service = OnboardingService(None)
        
        # Test minimum boundary (1%)
        data_min = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_body_fat_percentage": 1
        }
        service._validate_state_3_workout_constraints(data_min)
        
        # Test maximum boundary (50%)
        data_max = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_body_fat_percentage": 50
        }
        service._validate_state_3_workout_constraints(data_max)
    
    def test_validate_state_3_optional_targets_none(self):
        """Test state 3 validation allows None for optional target metrics."""
        service = OnboardingService(None)
        
        data = {
            "equipment": [],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": None,
            "target_body_fat_percentage": None
        }
        
        # Should not raise exception
        service._validate_state_3_workout_constraints(data)
    
    def test_validate_state_3_empty_lists_allowed(self):
        """Test state 3 validation allows empty lists for injuries and limitations."""
        service = OnboardingService(None)
        
        data = {
            "equipment": ["bodyweight"],  # Equipment can't be empty in practice
            "injuries": [],  # Empty is valid
            "limitations": []  # Empty is valid
        }
        
        # Should not raise exception
        service._validate_state_3_workout_constraints(data)
    
    def test_validate_state_3_with_all_fields(self):
        """Test state 3 validation with all fields populated."""
        service = OnboardingService(None)
        
        data = {
            "equipment": ["dumbbells", "barbell", "resistance_bands"],
            "injuries": ["knee", "shoulder"],
            "limitations": ["lower_back_pain", "limited_mobility"],
            "target_weight_kg": 80.5,
            "target_body_fat_percentage": 12.5
        }
        
        # Should not raise exception
        service._validate_state_3_workout_constraints(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

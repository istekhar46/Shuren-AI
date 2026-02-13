"""
Integration tests for agent function tools.

Tests that agent function tools correctly call onboarding endpoints:
- Each agent's tools call correct endpoints
- Validation errors are handled correctly
- Success responses include next state info

Validates: Requirements 2.3.1, 2.3.2, 2.3.5
Task: 10.2 - Write integration test for agent function tools
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.agents.onboarding_tools import call_onboarding_step


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentFunctionToolsIntegration:
    """Integration tests for agent function tools calling onboarding endpoints."""
    
    async def test_call_onboarding_step_helper_success(
        self,
        db_session: AsyncSession
    ):
        """Test that call_onboarding_step helper successfully saves data.
        
        Validates: Requirements 2.3.1 (Agent can call REST endpoints as function tools)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="tool_test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Tool Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=0,
            is_complete=False,
            step_data={},
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Call helper function (simulating agent tool call)
        result = await call_onboarding_step(
            db=db_session,
            user_id=user.id,
            step=1,
            data={"fitness_level": "intermediate"},
            agent_type="workout_planning"
        )
        
        # Verify success response
        assert result["success"] is True
        assert "saved successfully" in result["message"].lower()
        assert result["current_state"] == 1
        assert result["next_state"] == 2
        
        # Verify data was persisted
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 1
        assert "step_1" in onboarding_state.step_data
        assert onboarding_state.step_data["step_1"]["fitness_level"] == "intermediate"
    
    async def test_call_onboarding_step_validation_error(
        self,
        db_session: AsyncSession
    ):
        """Test that validation errors are returned in structured format.
        
        Validates: Requirements 2.3.2 (Agent receives validation errors in structured format)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="validation_test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Validation Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=0,
            is_complete=False,
            step_data={},
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Call with invalid data (missing required field)
        result = await call_onboarding_step(
            db=db_session,
            user_id=user.id,
            step=1,
            data={},  # Missing fitness_level
            agent_type="workout_planning"
        )
        
        # Verify error response structure
        assert result["success"] is False
        assert "error" in result
        assert "field" in result
        assert result["error_code"] == "VALIDATION_ERROR"
        
        # Verify data was NOT persisted
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 0
        assert "step_1" not in onboarding_state.step_data
    
    async def test_agent_tools_call_correct_endpoints(
        self,
        db_session: AsyncSession
    ):
        """Test that different agent tools call their correct endpoints.
        
        Validates: Requirements 2.3.1, 2.3.5 (Tools call correct endpoints, receive success confirmation)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="multi_tool_test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Multi Tool Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=0,
            is_complete=False,
            step_data={},
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Test workout planning agent tools (states 1-3)
        workout_tools = [
            (1, {"fitness_level": "beginner"}, "workout_planning"),
            (2, {"goals": [{"goal_type": "fat_loss", "priority": 1}]}, "workout_planning"),
            (3, {"equipment": ["dumbbells"], "injuries": [], "limitations": []}, "workout_planning"),
        ]
        
        for step, data, agent_type in workout_tools:
            result = await call_onboarding_step(
                db=db_session,
                user_id=user.id,
                step=step,
                data=data,
                agent_type=agent_type
            )
            
            assert result["success"] is True
            assert result["current_state"] == step
            if step < 9:
                assert result["next_state"] == step + 1
        
        # Test diet planning agent tools (states 4-5)
        diet_tools = [
            (4, {"diet_type": "vegetarian", "allergies": [], "intolerances": [], "dislikes": []}, "diet_planning"),
            (5, {"daily_calorie_target": 2000, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0}, "diet_planning"),
        ]
        
        for step, data, agent_type in diet_tools:
            result = await call_onboarding_step(
                db=db_session,
                user_id=user.id,
                step=step,
                data=data,
                agent_type=agent_type
            )
            
            assert result["success"] is True
            assert result["current_state"] == step
        
        # Test scheduler agent tools (states 6-8)
        scheduler_tools = [
            (6, {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]}, "scheduler"),
            (7, {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]}, "scheduler"),
            (8, {"daily_water_target_ml": 2500, "reminder_frequency_minutes": 60}, "scheduler"),
        ]
        
        for step, data, agent_type in scheduler_tools:
            result = await call_onboarding_step(
                db=db_session,
                user_id=user.id,
                step=step,
                data=data,
                agent_type=agent_type
            )
            
            assert result["success"] is True
            assert result["current_state"] == step
        
        # Test supplement agent tool (state 9)
        result = await call_onboarding_step(
            db=db_session,
            user_id=user.id,
            step=9,
            data={"interested_in_supplements": False, "current_supplements": []},
            agent_type="supplement"
        )
        
        assert result["success"] is True
        assert result["current_state"] == 9
        assert result["next_state"] is None  # Last state
        
        # Verify all states were saved
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 9
        for i in range(1, 10):
            assert f"step_{i}" in onboarding_state.step_data
    
    async def test_agent_tool_includes_next_state_info(
        self,
        db_session: AsyncSession
    ):
        """Test that success responses include next state information.
        
        Validates: Requirements 2.3.5 (Agent receives success confirmation with next state info)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="next_state_test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Next State Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=0,
            is_complete=False,
            step_data={},
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Save state 1
        result = await call_onboarding_step(
            db=db_session,
            user_id=user.id,
            step=1,
            data={"fitness_level": "advanced"},
            agent_type="workout_planning"
        )
        
        # Verify next state info is included
        assert result["success"] is True
        assert "current_state" in result
        assert "next_state" in result
        assert result["current_state"] == 1
        assert result["next_state"] == 2
        assert "message" in result
        
        # Save state 9 (last state)
        # First complete states 2-8
        for step in range(2, 9):
            data_map = {
                2: {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                3: {"equipment": ["dumbbells"], "injuries": [], "limitations": []},
                4: {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
                5: {"daily_calorie_target": 2500, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0},
                6: {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]},
                7: {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]},
                8: {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60},
            }
            await call_onboarding_step(
                db=db_session,
                user_id=user.id,
                step=step,
                data=data_map[step],
                agent_type="test_agent"
            )
        
        # Now save state 9
        result = await call_onboarding_step(
            db=db_session,
            user_id=user.id,
            step=9,
            data={"interested_in_supplements": True, "current_supplements": ["whey_protein"]},
            agent_type="supplement"
        )
        
        # Verify last state has no next_state
        assert result["success"] is True
        assert result["current_state"] == 9
        assert result["next_state"] is None  # No next state after state 9

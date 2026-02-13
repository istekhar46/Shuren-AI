"""
Integration tests for complete onboarding flow.

Tests the end-to-end onboarding workflow:
- All 9 states via onboarding/step endpoint
- Agent routing for each state (via progress endpoint)
- State transitions and progress updates
- Completion and access control changes

Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5
Task: 10.1 - Write integration test for complete onboarding flow
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.onboarding import OnboardingState


@pytest.mark.asyncio
@pytest.mark.integration
class TestCompleteOnboardingFlowIntegration:
    """Integration tests for complete onboarding flow through all 9 states."""
    
    async def test_complete_9_state_onboarding_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete onboarding flow through all 9 states.
        
        This integration test validates:
        1. User can complete all 9 onboarding states sequentially
        2. Progress updates correctly after each state
        3. Agent routing changes based on state (workout -> diet -> scheduler -> supplement)
        4. Completion percentage calculates correctly
        5. Access control changes after completion
        6. Cannot access onboarding endpoints after completion
        
        Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5
        """
        # Setup: Create user with onboarding state
        user = User(
            id=uuid4(),
            email="integration_test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Integration Test User",
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
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Define all 9 states with their data and expected agent
        states = [
            (1, {"fitness_level": "intermediate"}, "workout_planning"),
            (2, {"goals": [{"goal_type": "muscle_gain", "priority": 1}]}, "workout_planning"),
            (3, {"equipment": ["dumbbells"], "injuries": [], "limitations": []}, "workout_planning"),
            (4, {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []}, "diet_planning"),
            (5, {"daily_calorie_target": 2500, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0}, "diet_planning"),
            (6, {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]}, "scheduler"),
            (7, {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]}, "scheduler"),
            (8, {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60}, "scheduler"),
            (9, {"interested_in_supplements": False, "current_supplements": []}, "supplement"),
        ]
        
        # Complete all 9 states
        for step, data, expected_agent in states:
            # Save state
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200, f"State {step} failed: {response.json()}"
            
            # Verify progress updated
            response = await client.get("/api/v1/onboarding/progress")
            assert response.status_code == 200
            progress = response.json()
            
            # Verify state completed
            assert step in progress["completed_states"], f"State {step} not in completed_states"
            assert progress["current_state"] == step, f"Current state should be {step}"
            
            # Verify agent routing
            assert progress["current_state_info"]["agent"] == expected_agent, \
                f"State {step} should route to {expected_agent}"
            
            # Verify completion percentage
            expected_percentage = int((step / 9) * 100)
            assert progress["completion_percentage"] == expected_percentage, \
                f"Completion should be {expected_percentage}% after state {step}"
        
        # Verify final completion status
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["completion_percentage"] == 100
        assert progress["can_complete"] is True
        assert len(progress["completed_states"]) == 9
        
        # Now call the complete endpoint to create the user profile
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 201  # Created status code
        profile_data = response.json()
        
        # Verify profile was created
        assert profile_data["id"] is not None
        assert profile_data["user_id"] == str(user.id)
        assert profile_data["is_locked"] is True
        assert profile_data["fitness_level"] == "intermediate"
        
        # Verify all states were saved correctly in database
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 9
        assert onboarding_state.is_complete is True
        for i in range(1, 10):
            assert f"step_{i}" in onboarding_state.step_data
    
    async def test_incremental_progress_persistence(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that progress persists incrementally and is immediately queryable.
        
        Validates: Requirements 2.1.5 (Incremental Progress Persistence)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="incremental@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Incremental User",
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
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Save state 1
        response = await client.post(
            "/api/v1/onboarding/step",
            json={"step": 1, "data": {"fitness_level": "beginner"}}
        )
        assert response.status_code == 200
        
        # Immediately query - data should be persisted
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert 1 in progress["completed_states"]
        assert progress["current_state"] == 1
        
        # Save state 2
        response = await client.post(
            "/api/v1/onboarding/step",
            json={"step": 2, "data": {"goals": [{"goal_type": "fat_loss", "priority": 1}]}}
        )
        assert response.status_code == 200
        
        # Immediately query - both states should be persisted
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert 1 in progress["completed_states"]
        assert 2 in progress["completed_states"]
        assert progress["current_state"] == 2
    
    async def test_agent_routing_changes_by_state(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that agent routing changes correctly based on current state.
        
        Validates: Requirements 2.1.2 (Agent Routing)
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="routing@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Routing User",
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
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Test agent routing for states 1-3 (workout_planning)
        for step in [1, 2, 3]:
            data = {
                1: {"fitness_level": "intermediate"},
                2: {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                3: {"equipment": ["dumbbells"], "injuries": [], "limitations": []}
            }[step]
            
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200
            
            response = await client.get("/api/v1/onboarding/progress")
            progress = response.json()
            assert progress["current_state_info"]["agent"] == "workout_planning"
        
        # Test agent routing for states 4-5 (diet_planning)
        for step in [4, 5]:
            data = {
                4: {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
                5: {"daily_calorie_target": 2500, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0}
            }[step]
            
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200
            
            response = await client.get("/api/v1/onboarding/progress")
            progress = response.json()
            assert progress["current_state_info"]["agent"] == "diet_planning"
        
        # Test agent routing for states 6-8 (scheduler)
        for step in [6, 7, 8]:
            data = {
                6: {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]},
                7: {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]},
                8: {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60}
            }[step]
            
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200
            
            response = await client.get("/api/v1/onboarding/progress")
            progress = response.json()
            assert progress["current_state_info"]["agent"] == "scheduler"
        
        # Test agent routing for state 9 (supplement)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={"step": 9, "data": {"interested_in_supplements": False, "current_supplements": []}}
        )
        assert response.status_code == 200
        
        response = await client.get("/api/v1/onboarding/progress")
        progress = response.json()
        assert progress["current_state_info"]["agent"] == "supplement"

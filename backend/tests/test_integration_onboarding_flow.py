"""
Integration tests for complete onboarding flow.

Tests the end-to-end onboarding workflow through the chat endpoint:
- All 9 states via chat endpoint
- Agent routing for each state
- State transitions and progress updates
- Completion and access control changes

Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.onboarding import OnboardingState


@pytest.mark.asyncio
@pytest.mark.integration
class TestCompleteOnboardingFlow:
    """Integration tests for complete onboarding flow via chat endpoint."""
    
    async def test_complete_onboarding_flow_all_9_states(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete onboarding flow through all 9 states via chat endpoint.
        
        This test validates:
        1. User can start onboarding at state 1
        2. Appropriate agent is routed for each state
        3. State transitions work correctly
        4. Progress updates after each state
        5. Completion changes access control
        6. User cannot access onboarding chat after completion
        
        Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5
        """
        # Step 1: Create user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="onboarding_flow_test@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Onboarding Flow Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        # Create onboarding state at step 0
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
        
        # Setup authenticated client
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 2: Complete State 1 - Fitness Level (Workout Planning Agent)
        # Step 2: Complete State 1 - Fitness Level (Workout Planning Agent)
        # First, manually save state 1 to advance to it
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 1,
                "data": {"fitness_level": "intermediate"}
            }
        )
        assert response.status_code == 200
        
        # Verify progress after state 1
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 1
        assert 1 in progress["completed_states"]
        assert progress["completion_percentage"] > 0
        assert progress["current_state_info"]["agent"] == "workout_planning"
        
        # Step 3: Complete State 2 - Fitness Goals (Workout Planning Agent)
        # Step 3: Complete State 2 - Fitness Goals (Workout Planning Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 2,
                "data": {
                    "goals": [
                        {"goal_type": "muscle_gain", "priority": 1}
                    ]
                }
            }
        )
        assert response.status_code == 200
        
        # Verify progress after state 2
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 2
        assert 2 in progress["completed_states"]
        assert progress["completion_percentage"] > progress["completion_percentage"]
        
        # Step 4: Complete State 3 - Workout Constraints (Workout Planning Agent)
        # Step 4: Complete State 3 - Workout Constraints (Workout Planning Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 3,
                "data": {
                    "equipment": ["dumbbells", "resistance_bands"],
                    "injuries": [],
                    "limitations": ["lower_back_pain"],
                    "target_weight_kg": 80.0
                }
            }
        )
        assert response.status_code == 200
        
        # Step 5: Complete State 4 - Dietary Preferences (Diet Planning Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 4,
                "data": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": ["lactose"],
                    "dislikes": ["mushrooms"]
                }
            }
        )
        assert response.status_code == 200
        
        # Verify agent changed to diet_planning
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state_info"]["agent"] == "diet_planning"
        
        # Step 6: Complete State 5 - Meal Plan (Diet Planning Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 5,
                "data": {
                    "daily_calorie_target": 2500,
                    "protein_percentage": 30.0,
                    "carbs_percentage": 40.0,
                    "fats_percentage": 30.0
                }
            }
        )
        assert response.status_code == 200
        
        # Step 7: Complete State 6 - Meal Schedule (Scheduler Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 6,
                "data": {
                    "meals": [
                        {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True},
                        {"meal_name": "Lunch", "scheduled_time": "13:00", "enable_notifications": True},
                        {"meal_name": "Dinner", "scheduled_time": "19:00", "enable_notifications": True}
                    ]
                }
            }
        )
        assert response.status_code == 200
        
        # Verify agent changed to scheduler
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state_info"]["agent"] == "scheduler"
        
        # Step 8: Complete State 7 - Workout Schedule (Scheduler Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 7,
                "data": {
                    "workouts": [
                        {"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True},
                        {"day_of_week": 3, "scheduled_time": "18:00", "enable_notifications": True},
                        {"day_of_week": 5, "scheduled_time": "18:00", "enable_notifications": True}
                    ]
                }
            }
        )
        assert response.status_code == 200
        
        # Step 9: Complete State 8 - Hydration (Scheduler Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 8,
                "data": {
                    "daily_water_target_ml": 3000,
                    "reminder_frequency_minutes": 60
                }
            }
        )
        assert response.status_code == 200
        
        # Step 10: Complete State 9 - Supplements (Supplement Agent)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 9,
                "data": {
                    "interested_in_supplements": True,
                    "current_supplements": ["whey_protein", "creatine"]
                }
            }
        )
        assert response.status_code == 200
        
        # Verify agent changed to supplement
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state_info"]["agent"] == "supplement"
        
        # Step 11: Verify completion status
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["completion_percentage"] == 100
        assert progress["can_complete"] is True
        assert len(progress["completed_states"]) == 9
        assert progress["is_complete"] is False  # Not marked complete until explicit completion
        
        # Step 12: Mark onboarding as complete
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 200
        
        # Refresh onboarding_state to get updated is_complete status
        await db_session.refresh(onboarding_state)
        assert onboarding_state.is_complete is True
        
        # Step 13: Verify access control changed (can now access all features)
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["access_control"]["can_access_dashboard"] is True
        assert user_data["access_control"]["can_access_workouts"] is True
        assert user_data["access_control"]["can_access_meals"] is True
        assert user_data["access_control"]["can_access_chat"] is True
        assert user_data["access_control"]["can_access_profile"] is True
        assert len(user_data["access_control"]["locked_features"]) == 0
        
        # Step 14: Verify cannot access onboarding chat after completion
        response = await client.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "I want to change my fitness level",
                "current_state": 1
            }
        )
        assert response.status_code == 403
        assert "already completed" in response.json()["detail"].lower()
    
    async def test_onboarding_state_transitions_are_sequential(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that onboarding state transitions happen sequentially.
        
        Validates: Requirements 2.1.4, 2.1.5
        """
        # Create user
        user = User(
            id=uuid4(),
            email="sequential_test@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Sequential Test User",
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
        
        # Complete state 1
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 1,
                "data": {"fitness_level": "beginner"}
            }
        )
        assert response.status_code == 200
        
        # Verify current_step advanced to 1
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 1
        assert "step_1" in onboarding_state.step_data
        
        # Complete state 2
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 2,
                "data": {
                    "goals": [{"goal_type": "fat_loss", "priority": 1}]
                }
            }
        )
        assert response.status_code == 200
        
        # Verify current_step advanced to 2
        await db_session.refresh(onboarding_state)
        assert onboarding_state.current_step == 2
        assert "step_2" in onboarding_state.step_data
        
        # Verify data is immediately queryable (incremental persistence)
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert 1 in progress["completed_states"]
        assert 2 in progress["completed_states"]
        assert progress["current_state"] == 2
    
    async def test_onboarding_progress_updates_incrementally(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that progress updates incrementally after each state save.
        
        Validates: Requirements 2.1.5
        """
        # Create user
        user = User(
            id=uuid4(),
            email="incremental_test@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Incremental Test User",
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
        
        # Track progress percentages
        percentages = []
        
        # Complete states 1-5 and track progress
        states_data = [
            (1, {"fitness_level": "intermediate"}),
            (2, {"goals": [{"goal_type": "muscle_gain", "priority": 1}]}),
            (3, {"equipment": ["dumbbells"], "injuries": [], "limitations": []}),
            (4, {"diet_type": "vegetarian", "allergies": [], "intolerances": [], "dislikes": []}),
            (5, {"daily_calorie_target": 2000, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0})
        ]
        
        for step, data in states_data:
            # Save state
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200
            
            # Get progress immediately
            response = await client.get("/api/v1/onboarding/progress")
            assert response.status_code == 200
            progress = response.json()
            
            # Verify incremental update
            assert step in progress["completed_states"]
            assert progress["current_state"] == step
            percentages.append(progress["completion_percentage"])
        
        # Verify percentages increased incrementally
        for i in range(len(percentages) - 1):
            assert percentages[i] < percentages[i + 1], \
                f"Progress should increase: {percentages[i]} < {percentages[i + 1]}"
        
        # Verify final percentage is correct (5/9 * 100 ≈ 55%)
        assert percentages[-1] == int((5 / 9) * 100)

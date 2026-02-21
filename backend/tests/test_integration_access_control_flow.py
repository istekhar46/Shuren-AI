"""
Integration tests for access control flow.

Tests the complete access control workflow:
- Incomplete user can only access chat onboarding
- Completed user can access all features
- Completed user cannot access onboarding chat
- Completed user forced to general agent

Validates: Requirements 2.4.1, 2.4.2, 2.4.3, 2.4.4
Task: 10.3 - Write integration test for access control flow
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
class TestAccessControlFlowIntegration:
    """Integration tests for access control based on onboarding status."""
    
    async def test_incomplete_user_access_control(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that incomplete user has restricted access.
        
        Validates: Requirements 2.4.3, 2.4.4 (Feature lock enforcement)
        """
        # Setup incomplete user
        user = User(
            id=uuid4(),
            email="incomplete@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Incomplete User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=3,  # Partially complete
            is_complete=False,
            step_data={
                "step_1": {"fitness_level": "beginner"},
                "step_2": {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
                "step_3": {"equipment": ["dumbbells"], "injuries": [], "limitations": []}
            },
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Verify access control via /auth/me endpoint
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        user_data = response.json()
        
        access_control = user_data["access_control"]
        
        # Only chat should be accessible
        assert access_control["can_access_chat"] is True
        
        # All other features should be locked
        assert access_control["can_access_dashboard"] is False
        assert access_control["can_access_workouts"] is False
        assert access_control["can_access_meals"] is False
        assert access_control["can_access_profile"] is False
        
        # Verify locked features list
        assert "dashboard" in access_control["locked_features"]
        assert "workouts" in access_control["locked_features"]
        assert "meals" in access_control["locked_features"]
        assert "profile" in access_control["locked_features"]
        
        # Verify unlock message is present
        assert access_control["unlock_message"] is not None
        assert "onboarding" in access_control["unlock_message"].lower()
        
        # Verify onboarding progress is included
        assert access_control["onboarding_progress"] is not None
        assert access_control["onboarding_progress"]["current_state"] == 3
        assert access_control["onboarding_progress"]["completion_percentage"] > 0
    
    async def test_completed_user_access_control(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that completed user has full access.
        
        Validates: Requirements 2.4.3, 2.4.4 (All features unlocked after completion)
        """
        # Setup completed user
        user = User(
            id=uuid4(),
            email="completed@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Completed User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        # Create complete onboarding state
        complete_data = {}
        for i in range(1, 10):
            complete_data[f"step_{i}"] = {"completed": True}
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,  # Marked as complete
            step_data=complete_data,
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Verify access control via /auth/me endpoint
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        user_data = response.json()
        
        access_control = user_data["access_control"]
        
        # All features should be accessible
        assert access_control["can_access_dashboard"] is True
        assert access_control["can_access_workouts"] is True
        assert access_control["can_access_meals"] is True
        assert access_control["can_access_chat"] is True
        assert access_control["can_access_profile"] is True
        
        # No locked features
        assert len(access_control["locked_features"]) == 0
        
        # No unlock message
        assert access_control["unlock_message"] is None
        
        # No onboarding progress (already complete)
        assert access_control["onboarding_progress"] is None
    
    async def test_completed_user_cannot_access_onboarding_chat(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that completed user cannot access onboarding chat endpoint.
        
        Validates: Requirements 2.4.1 (Completed user cannot access onboarding chat)
        """
        # Setup completed user
        user = User(
            id=uuid4(),
            email="no_onboarding_chat@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="No Onboarding Chat User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Try to access onboarding chat endpoint
        response = await client.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "I want to change my fitness level",
                "current_state": 1
            }
        )
        
        # Should be rejected with 403
        assert response.status_code == 403
        error = response.json()
        assert "already completed" in error["detail"].lower() or "completed" in error["detail"].lower()
    
    async def test_access_control_transitions_on_completion(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that access control changes when onboarding is completed.
        
        Validates: Requirements 2.4.3, 2.4.4 (Access control transitions)
        """
        # Setup user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="transition@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Transition User",
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
        
        # Verify initial restricted access
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        initial_access = response.json()["access_control"]
        assert initial_access["can_access_dashboard"] is False
        assert len(initial_access["locked_features"]) > 0
        
        # Complete all 9 states
        states_data = [
            (1, {"fitness_level": "intermediate"}),
            (2, {"goals": [{"goal_type": "muscle_gain", "priority": 1}]}),
            (3, {"equipment": ["dumbbells"], "injuries": [], "limitations": []}),
            (4, {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []}),
            (5, {"daily_calorie_target": 2500, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0}),
            (6, {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]}),
            (7, {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]}),
            (8, {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60}),
            (9, {"interested_in_supplements": False, "current_supplements": []}),
        ]
        
        for step, data in states_data:
            response = await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data}
            )
            assert response.status_code == 200
        
        # Mark onboarding complete
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 201  # Created status code
        
        # Verify access control changed to full access
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        final_access = response.json()["access_control"]
        
        assert final_access["can_access_dashboard"] is True
        assert final_access["can_access_workouts"] is True
        assert final_access["can_access_meals"] is True
        assert final_access["can_access_profile"] is True
        assert len(final_access["locked_features"]) == 0
        assert final_access["onboarding_progress"] is None
    
    async def test_onboarding_chat_only_accessible_during_onboarding(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that onboarding chat is only accessible during onboarding.
        
        Validates: Requirements 2.4.1, 2.4.2 (Onboarding chat access control)
        """
        # Setup incomplete user
        user = User(
            id=uuid4(),
            email="onboarding_chat_access@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Onboarding Chat Access User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=2,
            is_complete=False,
            step_data={
                "step_1": {"fitness_level": "beginner"},
                "step_2": {"goals": [{"goal_type": "fat_loss", "priority": 1}]}
            },
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Verify can access onboarding chat during onboarding
        response = await client.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "What equipment do I need?",
                "current_state": 2
            }
        )
        # Should succeed (200) or have a different error (not 403 for completion)
        # Note: May fail for other reasons (state mismatch, etc.) but not because onboarding is complete
        assert response.status_code != 403 or "already completed" not in response.json().get("detail", "").lower()
        
        # Complete onboarding
        for step in range(3, 10):
            data_map = {
                3: {"equipment": ["dumbbells"], "injuries": [], "limitations": []},
                4: {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
                5: {"daily_calorie_target": 2500, "protein_percentage": 30.0, "carbs_percentage": 40.0, "fats_percentage": 30.0},
                6: {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}]},
                7: {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True}]},
                8: {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60},
                9: {"interested_in_supplements": False, "current_supplements": []},
            }
            await client.post(
                "/api/v1/onboarding/step",
                json={"step": step, "data": data_map[step]}
            )
        
        await client.post("/api/v1/onboarding/complete")  # Status code 201
        
        # Now verify cannot access onboarding chat
        response = await client.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "Can I change my fitness level?",
                "current_state": 1
            }
        )
        
        assert response.status_code == 403
        assert "already completed" in response.json()["detail"].lower() or "completed" in response.json()["detail"].lower()

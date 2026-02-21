"""
Tests for onboarding endpoints.

Validates onboarding state retrieval, step submission, and completion.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.v1.endpoints.onboarding import router
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile
from app.services.onboarding_service import OnboardingValidationError


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True
    )


@pytest.fixture
def app_with_mocks(mock_db, mock_user):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/onboarding", tags=["onboarding"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def sync_client(app_with_mocks):
    """Create sync test client for mock-based tests."""
    return TestClient(app_with_mocks)


class TestGetOnboardingState:
    """Tests for GET /api/v1/onboarding/state endpoint."""
    
    def test_get_state_success(self, sync_client, mock_user):
        """Test successful retrieval of onboarding state."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock onboarding state
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_user.id,
                current_step=3,
                is_complete=False,
                step_data={"step_1": {"age": 25}}
            )
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            
            response = sync_client.get("/api/v1/onboarding/state")
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_step"] == 3
            assert data["is_complete"] is False
            assert "step_data" in data
    
    def test_get_state_not_found(self, sync_client):
        """Test 404 when onboarding state not found."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=None)
            
            response = sync_client.get("/api/v1/onboarding/state")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestSaveOnboardingStep:
    """Tests for POST /api/v1/onboarding/step endpoint."""
    
    def test_save_step_success(self, sync_client, mock_user):
        """Test successful step submission."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock updated state
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_user.id,
                current_step=1,
                is_complete=False,
                step_data={"step_1": {"age": 25, "gender": "male", "height_cm": 175, "weight_kg": 70}}
            )
            
            mock_service = MockService.return_value
            mock_service.save_onboarding_step = AsyncMock(return_value=mock_state)
            
            response = sync_client.post(
                "/api/v1/onboarding/step",
                json={
                    "step": 1,
                    "data": {
                        "age": 25,
                        "gender": "male",
                        "height_cm": 175,
                        "weight_kg": 70
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_step"] == 1
            assert "saved successfully" in data["message"].lower()
    
    def test_save_step_validation_error(self, sync_client):
        """Test 400 when step data is invalid."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.save_onboarding_step = AsyncMock(
                side_effect=OnboardingValidationError("Invalid age")
            )
            
            response = sync_client.post(
                "/api/v1/onboarding/step",
                json={
                    "step": 1,
                    "data": {"age": 12}
                }
            )
            
            assert response.status_code == 400
            detail = response.json()["detail"]
            # Handle both string and dict response formats
            if isinstance(detail, dict):
                assert "invalid age" in detail.get("message", "").lower()
            else:
                assert "invalid age" in detail.lower()


class TestCompleteOnboarding:
    """Tests for POST /api/v1/onboarding/complete endpoint (legacy mock tests)."""
    
    # Note: These tests are deprecated in favor of TestCompleteOnboardingIntegration
    # which tests the actual ProfileCreationService-based implementation.
    # Keeping these for backward compatibility testing only.
    
    pass



# ============================================================================
# Integration Tests for New Completion Endpoint (Task 9.4)
# ============================================================================

class TestCompleteOnboardingIntegration:
    """
    Integration tests for POST /api/v1/onboarding/complete endpoint.
    
    Tests the new completion endpoint that uses ProfileCreationService
    and agent_context instead of the old onboarding service.
    
    **Feature: scheduling-agent-completion**
    """
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_successful_completion_with_complete_agent_context(
        self,
        authenticated_client,
        db_session
    ):
        """
        Test successful completion with complete agent_context.
        
        Validates Requirement 20.1-20.9: Complete onboarding flow.
        
        **Feature: scheduling-agent-completion**
        """
        from datetime import datetime
        from sqlalchemy import select, update
        from app.models.onboarding import OnboardingState
        
        client, user = authenticated_client
        
        # Set up complete agent_context
        complete_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["no_equipment"],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "goal_setting": {
                "primary_goal": "muscle_gain",
                "secondary_goal": "fat_loss",
                "target_weight_kg": 75.0,
                "target_body_fat_percentage": 15.0,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "duration_weeks": 12,
                    "training_split": [
                        {
                            "name": "Upper Body",
                            "muscle_groups": ["chest", "back"],
                            "type": "strength",
                            "description": "Upper body workout"
                        }
                    ],
                    "rationale": "4-day split for muscle gain"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": [],
                    "dislikes": []
                },
                "proposed_plan": {
                    "daily_calories": 2800,
                    "protein_g": 175.0,
                    "carbs_g": 350.0,
                    "fats_g": 78.0,
                    "meal_frequency": 4
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "workout_schedule": {
                    "days": ["Monday", "Wednesday", "Friday", "Saturday"],
                    "times": ["07:00", "07:00", "18:00", "09:00"]
                },
                "meal_schedule": {
                    "breakfast": "08:00",
                    "lunch": "13:00",
                    "snack": "16:00",
                    "dinner": "19:00"
                },
                "hydration_preferences": {
                    "frequency_hours": 2,
                    "target_ml": 3000
                },
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Update onboarding state with complete context
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user.id)
            .values(
                agent_context=complete_context,
                is_complete=False
            )
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Call completion endpoint
        response = await client.post("/api/v1/onboarding/complete")
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["fitness_level"] == "intermediate"
        assert data["is_locked"] is True
        assert data["onboarding_complete"] is True
        assert "successfully" in data["message"].lower()
        
        # Verify onboarding state is marked complete
        await db_session.refresh(user)  # Refresh to get latest state
        stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        assert state.is_complete is True
        assert state.current_agent == "general_assistant"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_409_error_when_already_complete(
        self,
        authenticated_client,
        db_session
    ):
        """
        Test 409 error when onboarding already complete.
        
        Validates Requirement 20.3: Check if onboarding already complete.
        
        **Feature: scheduling-agent-completion**
        """
        from sqlalchemy import update
        from app.models.onboarding import OnboardingState
        
        client, user = authenticated_client
        
        # Mark onboarding as complete
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user.id)
            .values(is_complete=True, current_agent="general_assistant")
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Attempt to complete again
        response = await client.post("/api/v1/onboarding/complete")
        
        # Verify 409 response
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_400_error_when_agent_data_missing(
        self,
        authenticated_client,
        db_session
    ):
        """
        Test 400 error when agent data is missing.
        
        Validates Requirement 18.1, 18.2: Error handling for incomplete data.
        
        **Feature: scheduling-agent-completion**
        """
        from sqlalchemy import update
        from app.models.onboarding import OnboardingState
        
        client, user = authenticated_client
        
        # Set incomplete agent_context (missing scheduling)
        incomplete_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": [],
                "completed_at": "2024-01-01T10:00:00Z"
            },
            "goal_setting": {
                "primary_goal": "muscle_gain",
                "completed_at": "2024-01-01T10:05:00Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "training_split": [{"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}]
                },
                "user_approved": True,
                "completed_at": "2024-01-01T10:10:00Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": [],
                    "dislikes": []
                },
                "proposed_plan": {
                    "daily_calories": 2500,
                    "protein_g": 150.0,
                    "carbs_g": 300.0,
                    "fats_g": 70.0,
                    "meal_frequency": 4
                },
                "user_approved": True,
                "completed_at": "2024-01-01T10:15:00Z"
            }
            # Missing "scheduling" section
        }
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user.id)
            .values(agent_context=incomplete_context, is_complete=False)
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Attempt to complete
        response = await client.post("/api/v1/onboarding/complete")
        
        # Verify 400 response
        assert response.status_code == 400
        assert "incomplete" in response.json()["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_401_error_when_not_authenticated(
        self,
        client: AsyncClient
    ):
        """
        Test 401 error when not authenticated.
        
        Validates authentication requirement.
        
        **Feature: scheduling-agent-completion**
        """
        # Attempt to complete without authentication (no Authorization header)
        response = await client.post("/api/v1/onboarding/complete")
        
        # Verify 401 response
        assert response.status_code == 401
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_profile_is_locked_after_completion(
        self,
        authenticated_client,
        db_session
    ):
        """
        Test that profile is locked after completion.
        
        Validates Requirement 20.5: Profile is locked after completion.
        
        **Feature: scheduling-agent-completion**
        """
        from datetime import datetime
        from sqlalchemy import select, update
        from app.models.onboarding import OnboardingState
        from app.models.profile import UserProfile
        
        client, user = authenticated_client
        
        # Set up complete agent_context
        complete_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": [],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "goal_setting": {
                "primary_goal": "fat_loss",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 3,
                    "duration_minutes": 45,
                    "training_split": [
                        {"name": "Full Body", "muscle_groups": ["full_body"], "type": "strength"}
                    ]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "vegetarian",
                    "allergies": [],
                    "intolerances": [],
                    "dislikes": []
                },
                "proposed_plan": {
                    "daily_calories": 2000,
                    "protein_g": 120.0,
                    "carbs_g": 250.0,
                    "fats_g": 60.0,
                    "meal_frequency": 3
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "workout_schedule": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["18:00", "18:00", "18:00"]
                },
                "meal_schedule": {
                    "breakfast": "07:00",
                    "lunch": "12:00",
                    "dinner": "18:00"
                },
                "hydration_preferences": {
                    "frequency_hours": 3,
                    "target_ml": 2500
                },
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user.id)
            .values(agent_context=complete_context, is_complete=False)
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Complete onboarding
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 201
        
        # Verify profile is locked
        stmt = select(UserProfile).where(UserProfile.user_id == user.id)
        result = await db_session.execute(stmt)
        profile = result.scalar_one()
        assert profile.is_locked is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_onboarding_state_is_complete_after_completion(
        self,
        authenticated_client,
        db_session
    ):
        """
        Test that onboarding_state.is_complete is True after completion.
        
        Validates Requirement 20.6: Mark onboarding as complete.
        
        **Feature: scheduling-agent-completion**
        """
        from datetime import datetime
        from sqlalchemy import select, update
        from app.models.onboarding import OnboardingState
        
        client, user = authenticated_client
        
        # Set up complete agent_context
        complete_context = {
            "fitness_assessment": {
                "fitness_level": "advanced",
                "limitations": [],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "goal_setting": {
                "primary_goal": "general_fitness",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 5,
                    "duration_minutes": 90,
                    "training_split": [
                        {"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}
                    ]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": [],
                    "dislikes": []
                },
                "proposed_plan": {
                    "daily_calories": 3000,
                    "protein_g": 200.0,
                    "carbs_g": 400.0,
                    "fats_g": 80.0,
                    "meal_frequency": 5
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "workout_schedule": {
                    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "times": ["06:00", "06:00", "06:00", "06:00", "06:00"]
                },
                "meal_schedule": {
                    "breakfast": "07:00",
                    "snack1": "10:00",
                    "lunch": "13:00",
                    "snack2": "16:00",
                    "dinner": "19:00"
                },
                "hydration_preferences": {
                    "frequency_hours": 1,
                    "target_ml": 4000
                },
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user.id)
            .values(agent_context=complete_context, is_complete=False)
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Complete onboarding
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 201
        
        # Verify onboarding state is complete
        stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
        result = await db_session.execute(stmt)
        state = result.scalar_one()
        assert state.is_complete is True
        assert state.current_agent == "general_assistant"

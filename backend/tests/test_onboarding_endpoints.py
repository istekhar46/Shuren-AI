"""
Tests for onboarding endpoints.

Validates onboarding state retrieval, step submission, and completion.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

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
def app(mock_db, mock_user):
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
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetOnboardingState:
    """Tests for GET /api/v1/onboarding/state endpoint."""
    
    def test_get_state_success(self, client, mock_user):
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
            
            response = client.get("/api/v1/onboarding/state")
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_step"] == 3
            assert data["is_complete"] is False
            assert "step_data" in data
    
    def test_get_state_not_found(self, client):
        """Test 404 when onboarding state not found."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/onboarding/state")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestSaveOnboardingStep:
    """Tests for POST /api/v1/onboarding/step endpoint."""
    
    def test_save_step_success(self, client, mock_user):
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
            
            response = client.post(
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
    
    def test_save_step_validation_error(self, client):
        """Test 400 when step data is invalid."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.save_onboarding_step = AsyncMock(
                side_effect=OnboardingValidationError("Invalid age")
            )
            
            response = client.post(
                "/api/v1/onboarding/step",
                json={
                    "step": 1,
                    "data": {"age": 12}
                }
            )
            
            assert response.status_code == 400
            assert "invalid age" in response.json()["detail"].lower()


class TestCompleteOnboarding:
    """Tests for POST /api/v1/onboarding/complete endpoint."""
    
    def test_complete_onboarding_success(self, client, mock_user):
        """Test successful onboarding completion."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock created profile
            mock_profile = UserProfile(
                id=uuid4(),
                user_id=mock_user.id,
                is_locked=True,
                fitness_level="intermediate"
            )
            # Add empty relationships
            mock_profile.fitness_goals = []
            mock_profile.physical_constraints = []
            mock_profile.dietary_preferences = None
            mock_profile.meal_plan = None
            mock_profile.meal_schedules = []
            mock_profile.workout_schedules = []
            mock_profile.hydration_preferences = None
            mock_profile.lifestyle_baseline = None
            
            mock_service = MockService.return_value
            mock_service.complete_onboarding = AsyncMock(return_value=mock_profile)
            
            response = client.post("/api/v1/onboarding/complete")
            
            assert response.status_code == 201
            data = response.json()
            assert data["is_locked"] is True
            assert data["fitness_level"] == "intermediate"
    
    def test_complete_onboarding_incomplete(self, client):
        """Test 400 when onboarding is incomplete."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.complete_onboarding = AsyncMock(
                side_effect=OnboardingValidationError("Onboarding incomplete")
            )
            
            response = client.post("/api/v1/onboarding/complete")
            
            assert response.status_code == 400
            assert "incomplete" in response.json()["detail"].lower()

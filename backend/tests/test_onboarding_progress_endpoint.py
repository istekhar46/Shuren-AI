"""
Tests for onboarding progress endpoint.

Validates the GET /api/v1/onboarding/progress endpoint that provides
rich progress metadata for UI indicators.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.onboarding import router
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import OnboardingProgress, StateInfo
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


class TestGetOnboardingProgress:
    """Tests for GET /api/v1/onboarding/progress endpoint."""
    
    def test_progress_no_states_completed(self, client, mock_user):
        """Test progress response when no states are completed."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock progress with no completed states
            mock_progress = OnboardingProgress(
                current_state=1,
                total_states=9,
                completed_states=[],
                current_state_info=StateInfo(
                    state_number=1,
                    name="Fitness Level Assessment",
                    agent="workout_planning",
                    description="Tell us about your current fitness level",
                    required_fields=["fitness_level"]
                ),
                next_state_info=StateInfo(
                    state_number=2,
                    name="Primary Fitness Goals",
                    agent="workout_planning",
                    description="What are your fitness goals?",
                    required_fields=["goals"]
                ),
                is_complete=False,
                completion_percentage=0,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["current_state"] == 1
            assert data["total_states"] == 9
            assert data["completed_states"] == []
            assert data["completion_percentage"] == 0
            assert data["can_complete"] is False
            assert data["is_complete"] is False
            
            # Verify current state info
            assert data["current_state_info"]["state_number"] == 1
            assert data["current_state_info"]["name"] == "Fitness Level Assessment"
            assert data["current_state_info"]["agent"] == "workout_planning"
            assert "fitness_level" in data["current_state_info"]["required_fields"]
            
            # Verify next state info exists
            assert data["next_state_info"] is not None
            assert data["next_state_info"]["state_number"] == 2
    
    def test_progress_partial_completion(self, client, mock_user):
        """Test progress response with some states completed."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock progress with 3 states completed (33%)
            mock_progress = OnboardingProgress(
                current_state=4,
                total_states=9,
                completed_states=[1, 2, 3],
                current_state_info=StateInfo(
                    state_number=4,
                    name="Diet Preferences & Restrictions",
                    agent="diet_planning",
                    description="Share your dietary preferences",
                    required_fields=["diet_type", "allergies", "intolerances", "dislikes"]
                ),
                next_state_info=StateInfo(
                    state_number=5,
                    name="Fixed Meal Plan Selection",
                    agent="diet_planning",
                    description="Set your meal plan targets",
                    required_fields=["daily_calorie_target", "protein_percentage"]
                ),
                is_complete=False,
                completion_percentage=33,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify partial completion
            assert data["current_state"] == 4
            assert data["completed_states"] == [1, 2, 3]
            assert data["completion_percentage"] == 33
            assert data["can_complete"] is False
            
            # Verify agent changed to diet_planning
            assert data["current_state_info"]["agent"] == "diet_planning"
    
    def test_progress_almost_complete(self, client, mock_user):
        """Test progress response when on last state."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock progress on state 9 with 8 states completed
            mock_progress = OnboardingProgress(
                current_state=9,
                total_states=9,
                completed_states=[1, 2, 3, 4, 5, 6, 7, 8],
                current_state_info=StateInfo(
                    state_number=9,
                    name="Supplement Preferences",
                    agent="supplement_guidance",
                    description="Tell us about supplement preferences",
                    required_fields=["interested_in_supplements"]
                ),
                next_state_info=None,  # No next state
                is_complete=False,
                completion_percentage=88,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify on last state
            assert data["current_state"] == 9
            assert len(data["completed_states"]) == 8
            assert data["completion_percentage"] == 88
            assert data["next_state_info"] is None  # No next state
            assert data["can_complete"] is False  # Still need to complete state 9
    
    def test_progress_all_states_completed(self, client, mock_user):
        """Test progress response when all states are completed."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock progress with all 9 states completed
            mock_progress = OnboardingProgress(
                current_state=9,
                total_states=9,
                completed_states=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                current_state_info=StateInfo(
                    state_number=9,
                    name="Supplement Preferences",
                    agent="supplement_guidance",
                    description="Tell us about supplement preferences",
                    required_fields=["interested_in_supplements"]
                ),
                next_state_info=None,
                is_complete=True,
                completion_percentage=100,
                can_complete=True
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify complete state
            assert data["current_state"] == 9
            assert len(data["completed_states"]) == 9
            assert data["completion_percentage"] == 100
            assert data["can_complete"] is True
            assert data["is_complete"] is True
    
    def test_progress_not_found(self, client):
        """Test 404 when onboarding state not found."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(
                side_effect=OnboardingValidationError("Onboarding state not found")
            )
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_progress_response_structure_matches_schema(self, client, mock_user):
        """Test that response structure exactly matches OnboardingProgress schema."""
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Mock progress with all required fields
            mock_progress = OnboardingProgress(
                current_state=5,
                total_states=9,
                completed_states=[1, 2, 3, 4],
                current_state_info=StateInfo(
                    state_number=5,
                    name="Fixed Meal Plan Selection",
                    agent="diet_planning",
                    description="Set your meal plan targets",
                    required_fields=["daily_calorie_target", "protein_percentage", "carbs_percentage", "fats_percentage"]
                ),
                next_state_info=StateInfo(
                    state_number=6,
                    name="Meal Timing Schedule",
                    agent="scheduler",
                    description="When do you want to eat?",
                    required_fields=["meals"]
                ),
                is_complete=False,
                completion_percentage=44,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required top-level fields exist
            required_fields = [
                "current_state",
                "total_states",
                "completed_states",
                "current_state_info",
                "next_state_info",
                "is_complete",
                "completion_percentage",
                "can_complete"
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify StateInfo structure for current_state_info
            state_info_fields = ["state_number", "name", "agent", "description", "required_fields"]
            for field in state_info_fields:
                assert field in data["current_state_info"], f"Missing StateInfo field: {field}"
            
            # Verify StateInfo structure for next_state_info
            for field in state_info_fields:
                assert field in data["next_state_info"], f"Missing StateInfo field in next_state_info: {field}"
            
            # Verify data types
            assert isinstance(data["current_state"], int)
            assert isinstance(data["total_states"], int)
            assert isinstance(data["completed_states"], list)
            assert isinstance(data["completion_percentage"], int)
            assert isinstance(data["can_complete"], bool)
            assert isinstance(data["is_complete"], bool)
            assert isinstance(data["current_state_info"]["required_fields"], list)
    
    def test_progress_mid_onboarding_various_states(self, client, mock_user):
        """Test progress at various mid-onboarding states."""
        test_cases = [
            # (current_state, completed_count, expected_percentage)
            (2, 1, 11),  # 1/9 = 11%
            (5, 4, 44),  # 4/9 = 44%
            (7, 6, 66),  # 6/9 = 66%
            (8, 7, 77),  # 7/9 = 77%
        ]
        
        for current_state, completed_count, expected_percentage in test_cases:
            with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
                completed_states = list(range(1, completed_count + 1))
                
                mock_progress = OnboardingProgress(
                    current_state=current_state,
                    total_states=9,
                    completed_states=completed_states,
                    current_state_info=StateInfo(
                        state_number=current_state,
                        name=f"State {current_state}",
                        agent="test_agent",
                        description="Test description",
                        required_fields=["test_field"]
                    ),
                    next_state_info=StateInfo(
                        state_number=current_state + 1,
                        name=f"State {current_state + 1}",
                        agent="test_agent",
                        description="Test description",
                        required_fields=["test_field"]
                    ) if current_state < 9 else None,
                    is_complete=False,
                    completion_percentage=expected_percentage,
                    can_complete=False
                )
                
                mock_service = MockService.return_value
                mock_service.get_progress = AsyncMock(return_value=mock_progress)
                
                response = client.get("/api/v1/onboarding/progress")
                
                assert response.status_code == 200
                data = response.json()
                assert data["current_state"] == current_state
                assert len(data["completed_states"]) == completed_count
                assert data["completion_percentage"] == expected_percentage

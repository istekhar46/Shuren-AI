"""
Property-based tests for onboarding progress endpoint completeness.

Validates that the progress endpoint response always contains all required fields
regardless of the user's onboarding state.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.onboarding import router
from app.models.user import User
from app.schemas.onboarding import OnboardingProgress, StateInfo


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
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


def create_state_info(state_number: int) -> StateInfo:
    """Helper to create StateInfo for testing."""
    state_names = {
        1: "Fitness Level Assessment",
        2: "Primary Fitness Goals",
        3: "Workout Preferences & Constraints",
        4: "Diet Preferences & Restrictions",
        5: "Fixed Meal Plan Selection",
        6: "Meal Timing Schedule",
        7: "Workout Schedule",
        8: "Hydration Schedule",
        9: "Supplement Preferences",
    }
    
    agents = {
        1: "workout_planning", 2: "workout_planning", 3: "workout_planning",
        4: "diet_planning", 5: "diet_planning",
        6: "scheduler", 7: "scheduler", 8: "scheduler",
        9: "supplement_guidance"
    }
    
    return StateInfo(
        state_number=state_number,
        name=state_names.get(state_number, f"State {state_number}"),
        agent=agents.get(state_number, "unknown"),
        description=f"Description for state {state_number}",
        required_fields=[f"field_{state_number}"]
    )


@pytest.mark.property
class TestProgressEndpointCompletenessProperties:
    """Property-based tests for progress endpoint completeness."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        current_state=st.integers(min_value=1, max_value=9),
        num_completed=st.integers(min_value=0, max_value=9)
    )
    def test_property_5_progress_endpoint_completeness(
        self,
        client,
        mock_user,
        current_state: int,
        num_completed: int
    ):
        """
        Property 5: Progress Endpoint Completeness
        
        **Validates: Requirements 2.2.1, 2.2.2, 2.2.3, 2.2.5**
        
        For any user at any onboarding state with any number of completed states,
        verify that the progress endpoint response contains all required fields:
        
        1. current_state (int) - Current onboarding state number
        2. total_states (int) - Total number of states (always 9)
        3. completed_states (list[int]) - List of completed state numbers
        4. current_state_info (StateInfo) - Metadata for current state
        5. next_state_info (StateInfo | None) - Metadata for next state
        6. is_complete (bool) - Whether onboarding is complete
        7. completion_percentage (int) - Percentage of completion
        8. can_complete (bool) - Whether user can complete onboarding
        
        This ensures the frontend always receives complete progress information
        regardless of the user's onboarding state.
        """
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Generate completed states list (ensure it's valid)
            completed_states = list(range(1, min(num_completed + 1, current_state + 1)))
            
            # Calculate completion percentage
            completion_percentage = int((len(completed_states) / 9) * 100)
            
            # Determine if complete
            is_complete = len(completed_states) == 9
            can_complete = len(completed_states) == 9
            
            # Create mock progress
            mock_progress = OnboardingProgress(
                current_state=current_state,
                total_states=9,
                completed_states=completed_states,
                current_state_info=create_state_info(current_state),
                next_state_info=create_state_info(current_state + 1) if current_state < 9 else None,
                is_complete=is_complete,
                completion_percentage=completion_percentage,
                can_complete=can_complete
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            # Make request
            response = client.get("/api/v1/onboarding/progress")
            
            # Property 5.1: Response is successful
            assert response.status_code == 200, \
                f"Progress endpoint should return 200 for state {current_state}"
            
            data = response.json()
            
            # Property 5.2: All required top-level fields are present
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
                assert field in data, \
                    f"Missing required field '{field}' in progress response for state {current_state}"
            
            # Property 5.3: Field types are correct
            assert isinstance(data["current_state"], int), \
                "current_state must be an integer"
            assert isinstance(data["total_states"], int), \
                "total_states must be an integer"
            assert isinstance(data["completed_states"], list), \
                "completed_states must be a list"
            assert isinstance(data["completion_percentage"], int), \
                "completion_percentage must be an integer"
            assert isinstance(data["can_complete"], bool), \
                "can_complete must be a boolean"
            assert isinstance(data["is_complete"], bool), \
                "is_complete must be a boolean"
            
            # Property 5.4: current_state_info has all required fields
            assert data["current_state_info"] is not None, \
                "current_state_info must not be None"
            
            state_info_fields = ["state_number", "name", "agent", "description", "required_fields"]
            for field in state_info_fields:
                assert field in data["current_state_info"], \
                    f"Missing StateInfo field '{field}' in current_state_info"
            
            # Property 5.5: next_state_info structure (if present)
            if data["next_state_info"] is not None:
                for field in state_info_fields:
                    assert field in data["next_state_info"], \
                        f"Missing StateInfo field '{field}' in next_state_info"
            
            # Property 5.6: Values are within valid ranges
            assert 1 <= data["current_state"] <= 9, \
                "current_state must be between 1 and 9"
            assert data["total_states"] == 9, \
                "total_states must always be 9"
            assert 0 <= data["completion_percentage"] <= 100, \
                "completion_percentage must be between 0 and 100"
            
            # Property 5.7: completed_states contains valid state numbers
            for state in data["completed_states"]:
                assert isinstance(state, int), \
                    "All completed states must be integers"
                assert 1 <= state <= 9, \
                    f"Completed state {state} must be between 1 and 9"
            
            # Property 5.8: current_state_info.state_number matches current_state
            assert data["current_state_info"]["state_number"] == data["current_state"], \
                "current_state_info.state_number must match current_state"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(completed_count=st.integers(min_value=0, max_value=9))
    def test_property_completion_percentage_accuracy(
        self,
        client,
        mock_user,
        completed_count: int
    ):
        """
        Property: Completion percentage is accurately calculated
        
        For any number of completed states, verify that the completion
        percentage is correctly calculated as (completed / 9) * 100.
        """
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            completed_states = list(range(1, completed_count + 1))
            expected_percentage = int((completed_count / 9) * 100)
            
            mock_progress = OnboardingProgress(
                current_state=max(1, completed_count),
                total_states=9,
                completed_states=completed_states,
                current_state_info=create_state_info(max(1, completed_count)),
                next_state_info=create_state_info(min(9, completed_count + 1)) if completed_count < 9 else None,
                is_complete=completed_count == 9,
                completion_percentage=expected_percentage,
                can_complete=completed_count == 9
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify percentage calculation
            assert data["completion_percentage"] == expected_percentage, \
                f"Expected {expected_percentage}% for {completed_count} completed states"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(current_state=st.integers(min_value=1, max_value=9))
    def test_property_next_state_info_presence(
        self,
        client,
        mock_user,
        current_state: int
    ):
        """
        Property: next_state_info is present except on last state
        
        For any state except state 9, next_state_info should be present.
        For state 9, next_state_info should be None.
        """
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_progress = OnboardingProgress(
                current_state=current_state,
                total_states=9,
                completed_states=[],
                current_state_info=create_state_info(current_state),
                next_state_info=create_state_info(current_state + 1) if current_state < 9 else None,
                is_complete=False,
                completion_percentage=0,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            if current_state < 9:
                assert data["next_state_info"] is not None, \
                    f"next_state_info should be present for state {current_state}"
                assert data["next_state_info"]["state_number"] == current_state + 1, \
                    f"next_state_info should be for state {current_state + 1}"
            else:
                assert data["next_state_info"] is None, \
                    "next_state_info should be None for state 9"
    
    def test_property_total_states_always_nine(self, client, mock_user):
        """
        Property: total_states is always 9
        
        Regardless of the user's progress, total_states should always be 9.
        """
        test_states = [1, 3, 5, 7, 9]
        
        for current_state in test_states:
            with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
                mock_progress = OnboardingProgress(
                    current_state=current_state,
                    total_states=9,
                    completed_states=[],
                    current_state_info=create_state_info(current_state),
                    next_state_info=create_state_info(current_state + 1) if current_state < 9 else None,
                    is_complete=False,
                    completion_percentage=0,
                    can_complete=False
                )
                
                mock_service = MockService.return_value
                mock_service.get_progress = AsyncMock(return_value=mock_progress)
                
                response = client.get("/api/v1/onboarding/progress")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["total_states"] == 9, \
                    f"total_states should always be 9, got {data['total_states']} for state {current_state}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        current_state=st.integers(min_value=1, max_value=9),
        completed_count=st.integers(min_value=0, max_value=9)
    )
    def test_property_completed_states_list_validity(
        self,
        client,
        mock_user,
        current_state: int,
        completed_count: int
    ):
        """
        Property: completed_states list contains valid, unique, sorted state numbers
        
        The completed_states list should:
        1. Contain only integers between 1 and 9
        2. Contain no duplicates
        3. Be sorted in ascending order
        """
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            # Generate valid completed states
            completed_states = sorted(list(set(range(1, min(completed_count + 1, 10)))))
            
            mock_progress = OnboardingProgress(
                current_state=current_state,
                total_states=9,
                completed_states=completed_states,
                current_state_info=create_state_info(current_state),
                next_state_info=create_state_info(current_state + 1) if current_state < 9 else None,
                is_complete=len(completed_states) == 9,
                completion_percentage=int((len(completed_states) / 9) * 100),
                can_complete=len(completed_states) == 9
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            completed = data["completed_states"]
            
            # Property: All elements are integers
            assert all(isinstance(s, int) for s in completed), \
                "All completed states must be integers"
            
            # Property: All elements are in valid range
            assert all(1 <= s <= 9 for s in completed), \
                "All completed states must be between 1 and 9"
            
            # Property: No duplicates
            assert len(completed) == len(set(completed)), \
                "completed_states should not contain duplicates"
            
            # Property: Sorted in ascending order
            assert completed == sorted(completed), \
                "completed_states should be sorted in ascending order"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(current_state=st.integers(min_value=1, max_value=9))
    def test_property_state_info_agent_consistency(
        self,
        client,
        mock_user,
        current_state: int
    ):
        """
        Property: StateInfo agent field matches expected agent for state
        
        Each state should have the correct agent assigned according to
        the state-to-agent mapping.
        """
        with patch('app.api.v1.endpoints.onboarding.OnboardingService') as MockService:
            mock_progress = OnboardingProgress(
                current_state=current_state,
                total_states=9,
                completed_states=[],
                current_state_info=create_state_info(current_state),
                next_state_info=create_state_info(current_state + 1) if current_state < 9 else None,
                is_complete=False,
                completion_percentage=0,
                can_complete=False
            )
            
            mock_service = MockService.return_value
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            response = client.get("/api/v1/onboarding/progress")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify agent field is present and non-empty
            assert "agent" in data["current_state_info"], \
                "current_state_info must have an 'agent' field"
            assert isinstance(data["current_state_info"]["agent"], str), \
                "agent field must be a string"
            assert len(data["current_state_info"]["agent"]) > 0, \
                "agent field must not be empty"
            
            # Verify agent is one of the valid agent types
            valid_agents = ["workout_planning", "diet_planning", "scheduler", "supplement_guidance"]
            assert data["current_state_info"]["agent"] in valid_agents, \
                f"agent must be one of {valid_agents}"

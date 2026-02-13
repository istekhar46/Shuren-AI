"""
Tests for onboarding chat endpoint.

Validates chat-based onboarding with specialized agent routing,
state management, and access control.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.chat import router
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.agents.context import AgentResponse
from app.services.agent_orchestrator import AgentType


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
def mock_incomplete_user():
    """Create a mock user with incomplete onboarding."""
    user = User(
        id=uuid4(),
        email="incomplete@example.com",
        hashed_password="hashed",
        full_name="Incomplete User",
        is_active=True
    )
    # Mock the onboarding_completed attribute
    user.onboarding_completed = False
    return user


@pytest.fixture
def mock_completed_user():
    """Create a mock user with completed onboarding."""
    user = User(
        id=uuid4(),
        email="completed@example.com",
        hashed_password="hashed",
        full_name="Completed User",
        is_active=True
    )
    # Mock the onboarding_completed attribute
    user.onboarding_completed = True
    return user


@pytest.fixture
def app_with_incomplete_user(mock_db, mock_incomplete_user):
    """Create FastAPI test application with incomplete user."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_incomplete_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def app_with_completed_user(mock_db, mock_completed_user):
    """Create FastAPI test application with completed user."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_completed_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def client_incomplete(app_with_incomplete_user):
    """Create test client with incomplete user."""
    return TestClient(app_with_incomplete_user)


@pytest.fixture
def client_completed(app_with_completed_user):
    """Create test client with completed user."""
    return TestClient(app_with_completed_user)


class TestOnboardingChatEndpoint:
    """Tests for POST /api/v1/chat/onboarding endpoint."""
    
    def test_successful_chat_interaction(self, client_incomplete, mock_incomplete_user):
        """Test successful chat interaction during onboarding."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            # Mock onboarding state (before update)
            mock_state_before = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=1,
                is_complete=False,
                step_data={}
            )
            
            # Mock onboarding state (after update)
            mock_state_after = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=2,
                is_complete=False,
                step_data={"step_1": {"fitness_level": "beginner"}}
            )
            
            # Mock progress
            mock_progress = MagicMock()
            mock_progress.current_state = 2
            mock_progress.total_states = 9
            mock_progress.completed_states = [1]
            mock_progress.completion_percentage = 11
            mock_progress.is_complete = False
            
            # Mock service
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(
                side_effect=[mock_state_before, mock_state_after]
            )
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            # Mock agent response
            mock_agent_response = AgentResponse(
                content="Great! As a beginner, I'll create a plan that...",
                agent_type="workout",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            # Make request
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I'm a beginner",
                    "current_state": 1
                }
            )
            
            # Assertions - verify response structure and content
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "agent_type" in data
            assert "state_updated" in data
            assert "progress" in data
            assert data["agent_type"] == "workout"
            assert isinstance(data["state_updated"], bool)
            assert "current_state" in data["progress"]
            assert "total_states" in data["progress"]
            assert "completion_percentage" in data["progress"]
    
    def test_403_when_user_already_completed_onboarding(self, client_completed):
        """Test 403 error when user has already completed onboarding."""
        response = client_completed.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "I want to change my plan",
                "current_state": 1
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "already completed" in data["detail"].lower()
    
    def test_400_when_state_mismatch(self, client_incomplete, mock_incomplete_user):
        """Test 400 error when current_state doesn't match backend state."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService:
            # Mock onboarding state with different step
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=3,  # Backend is at step 3
                is_complete=False,
                step_data={}
            )
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            
            # Request with state 1 (mismatch)
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I'm a beginner",
                    "current_state": 1  # Frontend thinks it's at step 1
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "state mismatch" in data["detail"].lower()
            assert "current: 3" in data["detail"].lower()
            assert "requested: 1" in data["detail"].lower()
    
    def test_agent_routing_based_on_current_state(self, client_incomplete, mock_incomplete_user):
        """Test that correct agent is selected based on current_state."""
        test_cases = [
            (1, "workout"),   # State 1 -> Workout agent
            (2, "workout"),   # State 2 -> Workout agent
            (3, "workout"),   # State 3 -> Workout agent
            (4, "diet"),      # State 4 -> Diet agent
            (5, "diet"),      # State 5 -> Diet agent
            (6, "scheduler"), # State 6 -> Scheduler agent
            (7, "scheduler"), # State 7 -> Scheduler agent
            (8, "scheduler"), # State 8 -> Scheduler agent
            (9, "supplement"),# State 9 -> Supplement agent
        ]
        
        for state_number, expected_agent_type in test_cases:
            with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
                 patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
                
                # Mock onboarding state
                mock_state = OnboardingState(
                    id=uuid4(),
                    user_id=mock_incomplete_user.id,
                    current_step=state_number,
                    is_complete=False,
                    step_data={}
                )
                
                # Mock progress
                mock_progress = MagicMock()
                mock_progress.current_state = state_number
                mock_progress.total_states = 9
                mock_progress.completed_states = []
                mock_progress.completion_percentage = 0
                mock_progress.is_complete = False
                
                mock_service = MockService.return_value
                mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
                mock_service.get_progress = AsyncMock(return_value=mock_progress)
                
                # Mock agent response
                mock_agent_response = AgentResponse(
                    content=f"Response from {expected_agent_type} agent",
                    agent_type=expected_agent_type,
                    tools_used=[],
                    metadata={}
                )
                
                mock_orchestrator = MockOrchestrator.return_value
                mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
                
                # Make request
                response = client_incomplete.post(
                    "/api/v1/chat/onboarding",
                    json={
                        "message": f"Test message for state {state_number}",
                        "current_state": state_number
                    }
                )
                
                # Verify response is successful and contains expected agent type
                assert response.status_code == 200, \
                    f"State {state_number} should return 200"
                data = response.json()
                assert "agent_type" in data, \
                    f"Response for state {state_number} should contain agent_type"
                assert data["agent_type"] == expected_agent_type, \
                    f"State {state_number} should route to {expected_agent_type} agent"
    
    def test_state_updated_flag_when_state_changes(self, client_incomplete, mock_incomplete_user):
        """Test state_updated flag is True when agent advances state."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            # Mock state before (step 1)
            mock_state_before = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=1,
                is_complete=False,
                step_data={}
            )
            
            # Mock state after (step 2 - advanced)
            mock_state_after = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=2,
                is_complete=False,
                step_data={"step_1": {"fitness_level": "intermediate"}}
            )
            
            mock_progress = MagicMock()
            mock_progress.current_state = 2
            mock_progress.total_states = 9
            mock_progress.completed_states = [1]
            mock_progress.completion_percentage = 11
            mock_progress.is_complete = False
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(
                side_effect=[mock_state_before, mock_state_after]
            )
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            mock_agent_response = AgentResponse(
                content="Saved your fitness level!",
                agent_type="workout",
                tools_used=["save_fitness_level"],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I'm intermediate level",
                    "current_state": 1
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["state_updated"] is True
            assert data["new_state"] == 2
    
    def test_state_updated_flag_when_state_unchanged(self, client_incomplete, mock_incomplete_user):
        """Test state_updated flag is False when agent doesn't advance state."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            # Mock state (same before and after)
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=1,
                is_complete=False,
                step_data={}
            )
            
            mock_progress = MagicMock()
            mock_progress.current_state = 1
            mock_progress.total_states = 9
            mock_progress.completed_states = []
            mock_progress.completion_percentage = 0
            mock_progress.is_complete = False
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            mock_agent_response = AgentResponse(
                content="Can you tell me more about your fitness level?",
                agent_type="workout",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "What do you mean?",
                    "current_state": 1
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["state_updated"] is False
            assert data["new_state"] is None
    
    def test_404_when_onboarding_state_not_found(self, client_incomplete):
        """Test 404 error when onboarding state doesn't exist."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=None)
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "Hello",
                    "current_state": 1
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_validation_error_for_invalid_state_number(self, client_incomplete):
        """Test validation error for state number outside 1-9 range."""
        # Test state 0 (too low)
        response = client_incomplete.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "Hello",
                "current_state": 0
            }
        )
        assert response.status_code == 422
        
        # Test state 10 (too high)
        response = client_incomplete.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "Hello",
                "current_state": 10
            }
        )
        assert response.status_code == 422
    
    def test_validation_error_for_empty_message(self, client_incomplete):
        """Test validation error for empty message."""
        response = client_incomplete.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "",
                "current_state": 1
            }
        )
        
        assert response.status_code == 422
    
    def test_validation_error_for_missing_fields(self, client_incomplete):
        """Test validation error when required fields are missing."""
        # Missing message
        response = client_incomplete.post(
            "/api/v1/chat/onboarding",
            json={
                "current_state": 1
            }
        )
        assert response.status_code == 422
        
        # Missing current_state
        response = client_incomplete.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "Hello"
            }
        )
        assert response.status_code == 422
    
    def test_orchestrator_error_handling(self, client_incomplete, mock_incomplete_user):
        """Test error handling when orchestrator raises ValueError."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=1,
                is_complete=False,
                step_data={}
            )
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            
            # Mock orchestrator to raise ValueError (access control error)
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(
                side_effect=ValueError("Access denied")
            )
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "Hello",
                    "current_state": 1
                }
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "access denied" in data["detail"].lower()
    
    def test_orchestrator_unexpected_error_handling(self, client_incomplete, mock_incomplete_user):
        """Test error handling when orchestrator raises unexpected exception."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=1,
                is_complete=False,
                step_data={}
            )
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            
            # Mock orchestrator to raise unexpected exception
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "Hello",
                    "current_state": 1
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "failed to process" in data["detail"].lower()
    
    def test_progress_information_in_response(self, client_incomplete, mock_incomplete_user):
        """Test that progress information is included in response."""
        with patch('app.api.v1.endpoints.chat.OnboardingService') as MockService, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_state = OnboardingState(
                id=uuid4(),
                user_id=mock_incomplete_user.id,
                current_step=3,
                is_complete=False,
                step_data={}
            )
            
            # Mock detailed progress
            mock_progress = MagicMock()
            mock_progress.current_state = 3
            mock_progress.total_states = 9
            mock_progress.completed_states = [1, 2]
            mock_progress.completion_percentage = 22
            mock_progress.is_complete = False
            
            mock_service = MockService.return_value
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            mock_service.get_progress = AsyncMock(return_value=mock_progress)
            
            mock_agent_response = AgentResponse(
                content="Response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            response = client_incomplete.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "Test",
                    "current_state": 3
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "progress" in data
            progress = data["progress"]
            assert progress["current_state"] == 3
            assert progress["total_states"] == 9
            assert progress["completed_states"] == [1, 2]
            assert progress["completion_percentage"] == 22
            assert progress["is_complete"] is False


class TestOnboardingChatAuthentication:
    """Tests for authentication requirements on onboarding chat endpoint."""
    
    def test_onboarding_chat_requires_authentication(self):
        """Test that onboarding chat endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/chat/onboarding",
            json={
                "message": "Hello",
                "current_state": 1
            }
        )
        
        assert response.status_code in [401, 403]

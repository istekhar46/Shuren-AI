"""
Tests for modified API endpoints in task 7.

Tests the modifications made to:
- GET /api/v1/users/me (access control)
- POST /api/v1/onboarding/step (agent context header, next_state_info)
- POST /api/v1/chat (onboarding completion check, agent restrictions)

Requirements: 3.2.1, 3.2.2, 3.2.3
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import OnboardingProgress, StateInfo
from app.services.agent_orchestrator import AgentType


pytestmark = pytest.mark.asyncio


class TestUsersMeEndpoint:
    """Tests for GET /api/v1/users/me with access control."""
    
    async def test_users_me_incomplete_onboarding(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test /me endpoint returns locked features for incomplete onboarding."""
        client, test_user = authenticated_client
        
        # Update existing onboarding state to step 3
        from sqlalchemy import select
        result = await db_session.execute(
            select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        )
        onboarding_state = result.scalar_one()
        onboarding_state.current_step = 3
        onboarding_state.step_data = {"step_1": {}, "step_2": {}, "step_3": {}}
        await db_session.commit()
        
        # Get user info
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic user data
        assert data["email"] == test_user.email
        assert data["onboarding_completed"] is False
        
        # Verify access control
        access_control = data["access_control"]
        assert access_control["can_access_dashboard"] is False
        assert access_control["can_access_workouts"] is False
        assert access_control["can_access_meals"] is False
        assert access_control["can_access_chat"] is True  # Always true
        assert access_control["can_access_profile"] is False
        
        # Verify locked features
        assert "dashboard" in access_control["locked_features"]
        assert "workouts" in access_control["locked_features"]
        assert "meals" in access_control["locked_features"]
        assert "profile" in access_control["locked_features"]
        
        # Verify unlock message
        assert access_control["unlock_message"] is not None
        assert "onboarding" in access_control["unlock_message"].lower()
        
        # Verify onboarding progress is included
        assert access_control["onboarding_progress"] is not None
        assert access_control["onboarding_progress"]["current_state"] == 3
        assert access_control["onboarding_progress"]["total_states"] == 9
    
    async def test_users_me_complete_onboarding(
        self,
        db_session: AsyncSession
    ):
        """Test /me endpoint returns unlocked features for completed onboarding."""
        # Create a completed onboarding user
        from app.core.security import hash_password, create_access_token
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        completed_user = User(
            id=uuid4(),
            email="completed@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Completed User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(completed_user)
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=completed_user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Reload user with onboarding_state eagerly loaded
        result = await db_session.execute(
            select(User).where(User.id == completed_user.id).options(selectinload(User.onboarding_state))
        )
        completed_user = result.scalar_one()
        
        # Create authenticated client for this user
        token = create_access_token(data={"sub": str(completed_user.id)})
        
        from httpx import AsyncClient
        from app.main import app
        from app.api.deps import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.headers["Authorization"] = f"Bearer {token}"
            response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic user data
        assert data["email"] == completed_user.email
        assert data["onboarding_completed"] is True
        
        # Verify access control - all features unlocked
        access_control = data["access_control"]
        assert access_control["can_access_dashboard"] is True
        assert access_control["can_access_workouts"] is True
        assert access_control["can_access_meals"] is True
        assert access_control["can_access_chat"] is True
        assert access_control["can_access_profile"] is True
        
        # Verify no locked features
        assert access_control["locked_features"] == []
        
        # Verify no unlock message
        assert access_control["unlock_message"] is None
        
        # Verify no onboarding progress
        assert access_control["onboarding_progress"] is None


class TestOnboardingStepEndpoint:
    """Tests for POST /api/v1/onboarding/step with agent context."""
    
    async def test_onboarding_step_with_agent_context(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test onboarding step endpoint logs agent context from header."""
        client, test_user = authenticated_client
        
        # Submit step with agent context header
        import logging
        with patch.object(logging.getLogger('app.api.v1.endpoints.onboarding'), 'info') as mock_logger:
            response = await client.post(
                "/api/v1/onboarding/step",
                json={
                    "step": 1,
                    "data": {"fitness_level": "beginner"}
                },
                headers={"X-Agent-Context": "workout_planning"}
            )
        
        assert response.status_code == 200
        
        # Verify agent context was logged
        mock_logger.assert_called_once()
        log_call = mock_logger.call_args
        assert "workout_planning" in log_call[0][0]
        assert "extra" in log_call[1]
        assert log_call[1]["extra"]["agent"] == "workout_planning"
    
    async def test_onboarding_step_without_agent_context(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test onboarding step endpoint works without agent context header."""
        client, test_user = authenticated_client
        
        # Submit step without agent context header
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 1,
                "data": {"fitness_level": "intermediate"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 1
        assert data["message"] == "Step 1 saved successfully"
    
    async def test_onboarding_step_includes_next_state_info(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test onboarding step response includes next_state_info."""
        client, test_user = authenticated_client
        
        # Submit step 1
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 1,
                "data": {"fitness_level": "advanced"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify next_state is included
        assert data["next_state"] == 2
        
        # Verify next_state_info is included
        assert data["next_state_info"] is not None
        next_info = data["next_state_info"]
        assert next_info["state_number"] == 2
        assert next_info["name"] is not None
        assert next_info["agent"] is not None
        assert next_info["description"] is not None
        assert next_info["required_fields"] is not None
    
    async def test_onboarding_step_last_state_no_next_info(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test onboarding step response has no next_state_info for last state."""
        client, test_user = authenticated_client
        
        # Update onboarding state to step 8
        from sqlalchemy import select
        result = await db_session.execute(
            select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        )
        onboarding_state = result.scalar_one()
        onboarding_state.current_step = 8
        onboarding_state.step_data = {f"step_{i}": {} for i in range(1, 9)}
        await db_session.commit()
        
        # Submit step 9 (last state)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 9,
                "data": {
                    "interested_in_supplements": False,
                    "current_supplements": []
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify no next_state
        assert data["next_state"] is None
        
        # Verify no next_state_info
        assert data["next_state_info"] is None
    
    async def test_onboarding_step_validation_error_includes_field(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test validation error response includes field information."""
        client, test_user = authenticated_client
        
        # Submit invalid data (missing required field)
        response = await client.post(
            "/api/v1/onboarding/step",
            json={
                "step": 1,
                "data": {}  # Missing fitness_level
            }
        )
        
        assert response.status_code == 400
        error = response.json()["detail"]
        
        # Verify error structure
        assert "message" in error
        assert "error_code" in error
        assert error["error_code"] == "VALIDATION_ERROR"


class TestChatEndpointAccessControl:
    """Tests for POST /api/v1/chat with access control."""
    
    async def test_chat_rejects_incomplete_onboarding(
        self,
        authenticated_client: tuple[AsyncClient, User],
        db_session: AsyncSession
    ):
        """Test chat endpoint rejects users with incomplete onboarding."""
        client, test_user = authenticated_client
        
        # Update existing onboarding state to step 3
        from sqlalchemy import select
        result = await db_session.execute(
            select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        )
        onboarding_state = result.scalar_one()
        onboarding_state.current_step = 3
        onboarding_state.step_data = {"step_1": {}, "step_2": {}, "step_3": {}}
        await db_session.commit()
        
        # Try to use chat endpoint
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 403
        error = response.json()["detail"]
        
        # Verify error structure
        assert "message" in error
        assert "onboarding" in error["message"].lower()
        assert error["error_code"] == "ONBOARDING_REQUIRED"
        assert "redirect" in error
        assert error["redirect"] == "/onboarding"
        
        # Verify onboarding progress is included
        assert "onboarding_progress" in error
    
    async def test_chat_allows_completed_onboarding(
        self,
        db_session: AsyncSession
    ):
        """Test chat endpoint allows users with completed onboarding."""
        # Create a completed onboarding user
        from app.core.security import hash_password, create_access_token
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        completed_user = User(
            id=uuid4(),
            email="completed2@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Completed User 2",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(completed_user)
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=completed_user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Reload user with onboarding_state eagerly loaded
        result = await db_session.execute(
            select(User).where(User.id == completed_user.id).options(selectinload(User.onboarding_state))
        )
        completed_user = result.scalar_one()
        
        # Create authenticated client for this user
        token = create_access_token(data={"sub": str(completed_user.id)})
        
        from httpx import AsyncClient
        from app.main import app
        from app.api.deps import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock the orchestrator to avoid actual agent processing
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Hello! How can I help you?"
            mock_response.agent_type = "general"
            mock_response.tools_used = []
            mock_orchestrator.route_query = AsyncMock(return_value=mock_response)
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock context loader
            with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context:
                mock_context.return_value = MagicMock()
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    client.headers["Authorization"] = f"Bearer {token}"
                    response = await client.post(
                        "/api/v1/chat/chat",
                        json={"message": "Hello"}
                    )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["agent_type"] == "general"
    
    async def test_chat_rejects_non_general_agent_request(
        self,
        db_session: AsyncSession
    ):
        """Test chat endpoint rejects explicit non-general agent requests."""
        # Create a completed onboarding user
        from app.core.security import hash_password, create_access_token
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        completed_user = User(
            id=uuid4(),
            email="completed3@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Completed User 3",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(completed_user)
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=completed_user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Reload user with onboarding_state eagerly loaded
        result = await db_session.execute(
            select(User).where(User.id == completed_user.id).options(selectinload(User.onboarding_state))
        )
        completed_user = result.scalar_one()
        
        # Create authenticated client for this user
        token = create_access_token(data={"sub": str(completed_user.id)})
        
        from httpx import AsyncClient
        from app.main import app
        from app.api.deps import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.headers["Authorization"] = f"Bearer {token}"
            response = await client.post(
                "/api/v1/chat/chat",
                json={
                    "message": "Create a workout plan",
                    "agent_type": "workout"
                }
            )
        
        assert response.status_code == 403
        error = response.json()["detail"]
        
        # Verify error structure
        assert "message" in error
        assert "general" in error["message"].lower()
        assert error["error_code"] == "AGENT_NOT_ALLOWED"
        assert error["requested_agent"] == "workout"
        assert error["allowed_agent"] == "general"
    
    async def test_chat_forces_general_agent(
        self,
        db_session: AsyncSession
    ):
        """Test chat endpoint forces general agent for completed users."""
        # Create a completed onboarding user
        from app.core.security import hash_password, create_access_token
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        completed_user = User(
            id=uuid4(),
            email="completed4@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Completed User 4",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(completed_user)
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=completed_user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Reload user with onboarding_state eagerly loaded
        result = await db_session.execute(
            select(User).where(User.id == completed_user.id).options(selectinload(User.onboarding_state))
        )
        completed_user = result.scalar_one()
        
        # Create authenticated client for this user
        token = create_access_token(data={"sub": str(completed_user.id)})
        
        from httpx import AsyncClient
        from app.main import app
        from app.api.deps import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock the orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_response.agent_type = "general"
            mock_response.tools_used = []
            mock_orchestrator.route_query = AsyncMock(return_value=mock_response)
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock context loader
            with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context:
                mock_context.return_value = MagicMock()
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    client.headers["Authorization"] = f"Bearer {token}"
                    response = await client.post(
                        "/api/v1/chat/chat",
                        json={"message": "Hello"}
                    )
        
        assert response.status_code == 200
        
        # Verify orchestrator was called with GENERAL agent and onboarding_mode=False
        mock_orchestrator.route_query.assert_called_once()
        call_kwargs = mock_orchestrator.route_query.call_args[1]
        assert call_kwargs["agent_type"] == AgentType.GENERAL
        assert call_kwargs["onboarding_mode"] is False
    
    async def test_chat_passes_onboarding_mode_false(
        self,
        db_session: AsyncSession
    ):
        """Test chat endpoint passes onboarding_mode=False to orchestrator."""
        # Create a completed onboarding user
        from app.core.security import hash_password, create_access_token
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        completed_user = User(
            id=uuid4(),
            email="completed5@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Completed User 5",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(completed_user)
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=completed_user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Reload user with onboarding_state eagerly loaded
        result = await db_session.execute(
            select(User).where(User.id == completed_user.id).options(selectinload(User.onboarding_state))
        )
        completed_user = result.scalar_one()
        
        # Create authenticated client for this user
        token = create_access_token(data={"sub": str(completed_user.id)})
        
        from httpx import AsyncClient
        from app.main import app
        from app.api.deps import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock the orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_response.agent_type = "general"
            mock_response.tools_used = []
            mock_orchestrator.route_query = AsyncMock(return_value=mock_response)
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock context loader
            with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context:
                mock_context.return_value = MagicMock()
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    client.headers["Authorization"] = f"Bearer {token}"
                    await client.post(
                        "/api/v1/chat/chat",
                        json={"message": "Test message"}
                    )
        
        # Verify onboarding_mode=False was passed
        call_kwargs = mock_orchestrator.route_query.call_args[1]
        assert "onboarding_mode" in call_kwargs
        assert call_kwargs["onboarding_mode"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

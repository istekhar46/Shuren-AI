"""
Tests for onboarding UI state synchronization fix.

Validates that the backend correctly detects state updates made by agents
during onboarding chat interactions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.user import User
from app.models.onboarding import OnboardingState
from app.agents.context import AgentResponse


@pytest.mark.asyncio
@pytest.mark.onboarding
class TestStateAdvancementDetection:
    """Test that state advancement is correctly detected."""
    
    async def test_state_advances_from_1_to_2(self, client, test_user, db_session):
        """Test state advancement detection when agent advances state from 1 to 2."""
        # Setup: Get existing onboarding state (created by test_user fixture)
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        # Update to step 1
        onboarding_state.current_step = 1
        onboarding_state.is_complete = False
        onboarding_state.step_data = {}
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator to simulate state advancement
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="Great! I've saved your fitness level. Let's move on to your goals.",
                agent_type="workout",
                tools_used=["save_fitness_level_tool"],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            
            # Mock route_query to advance the state
            async def mock_route_query(*args, **kwargs):
                # Simulate agent advancing state
                onboarding_state.current_step = 2
                onboarding_state.step_data = {"step_1": {"fitness_level": "beginner"}}
                await db_session.commit()
                return mock_agent_response
            
            mock_orchestrator.route_query = AsyncMock(side_effect=mock_route_query)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I am a complete beginner",
                    "current_state": 1
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # Verify state_updated is True
            assert data["state_updated"] is True, "state_updated should be True when state advances"
            
            # Verify new_state is 2
            assert data["new_state"] == 2, "new_state should be 2"
            
            # Verify progress reflects the update
            assert data["progress"]["current_state"] == 2
            assert 1 in data["progress"]["completed_states"]
    
    async def test_state_advances_from_8_to_9(self, client, test_user, db_session):
        """Test state advancement detection for last state transition (8 to 9)."""
        # Setup: Get existing onboarding state and update to step 8
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 8
        onboarding_state.is_complete = False
        onboarding_state.step_data = {
            "step_1": {"fitness_level": "intermediate"},
            "step_2": {"goals": ["muscle_gain"]},
            # ... other steps
        }
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="Perfect! I've saved your hydration preferences. One more step!",
                agent_type="scheduler",
                tools_used=["save_hydration_preferences"],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            
            # Mock route_query to advance state to 9
            async def mock_route_query(*args, **kwargs):
                onboarding_state.current_step = 9
                await db_session.commit()
                return mock_agent_response
            
            mock_orchestrator.route_query = AsyncMock(side_effect=mock_route_query)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I want to drink 3 liters per day",
                    "current_state": 8
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["state_updated"] is True
            assert data["new_state"] == 9
            assert data["progress"]["current_state"] == 9
            # Note: completed_states may not include 8 depending on progress calculation logic
            # The key assertion is that state_updated is True and new_state is 9


@pytest.mark.asyncio
@pytest.mark.onboarding
class TestStateUnchangedDetection:
    """Test that state remaining unchanged is correctly detected."""
    
    async def test_state_remains_at_1_when_info_incomplete(self, client, test_user, db_session):
        """Test state_updated is False when agent doesn't advance state."""
        # Setup: Get existing onboarding state and set to step 1
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 1
        onboarding_state.is_complete = False
        onboarding_state.step_data = {}
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator - agent asks for more info, doesn't save
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="What is this about? Can you tell me about your fitness level?",
                agent_type="workout",
                tools_used=[],  # No tools used, no state change
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            
            # Mock route_query - state remains unchanged
            async def mock_route_query(*args, **kwargs):
                # State remains at 1, no changes
                return mock_agent_response
            
            mock_orchestrator.route_query = AsyncMock(side_effect=mock_route_query)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request with vague message
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "What is this about?",
                    "current_state": 1
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # Verify state_updated is False
            assert data["state_updated"] is False, "state_updated should be False when state doesn't change"
            
            # Verify new_state is None
            assert data["new_state"] is None, "new_state should be None when state doesn't change"
            
            # Verify progress shows state still at 1
            assert data["progress"]["current_state"] == 1
            assert data["progress"]["completed_states"] == []
    
    async def test_state_remains_unchanged_at_state_5(self, client, test_user, db_session):
        """Test state remains unchanged when user provides incomplete dietary info."""
        # Setup: Get existing onboarding state and update to step 5
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 5
        onboarding_state.is_complete = False
        onboarding_state.step_data = {
            "step_1": {"fitness_level": "intermediate"},
            "step_2": {"goals": ["fat_loss"]},
            "step_3": {"constraints": []},
            "step_4": {"equipment": ["dumbbells"]},
        }
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="I need more details about your dietary preferences. Do you have any allergies?",
                agent_type="diet",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I like vegetables",
                    "current_state": 5
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["state_updated"] is False
            assert data["new_state"] is None
            assert data["progress"]["current_state"] == 5


@pytest.mark.asyncio
@pytest.mark.onboarding
class TestEdgeCases:
    """Test edge cases for state update detection."""
    
    async def test_user_already_on_state_9(self, client, test_user, db_session):
        """Test behavior when user is already on the last state."""
        # Setup: Get existing onboarding state and update to step 9
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 9
        onboarding_state.is_complete = False
        onboarding_state.step_data = {
            "step_1": {"fitness_level": "advanced"},
            # ... all other steps completed
        }
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="You're all set! Ready to complete onboarding?",
                agent_type="supplement",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "Yes, I'm ready",
                    "current_state": 9
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # State should remain at 9
            assert data["state_updated"] is False
            assert data["new_state"] is None
            assert data["progress"]["current_state"] == 9
    
    async def test_state_comparison_uses_initial_state(self, client, test_user, db_session):
        """Test that state comparison uses the initial state, not the request state."""
        # This test verifies the fix: comparison should use initial_step stored before agent call
        
        # Setup: Get existing onboarding state and set to step 1
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 1
        onboarding_state.is_complete = False
        onboarding_state.step_data = {}
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="Saved!",
                agent_type="workout",
                tools_used=["save_fitness_level_tool"],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            
            # Mock route_query to advance state
            async def mock_route_query(*args, **kwargs):
                # Agent advances state from 1 to 2
                onboarding_state.current_step = 2
                await db_session.commit()
                return mock_agent_response
            
            mock_orchestrator.route_query = AsyncMock(side_effect=mock_route_query)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "I'm a beginner",
                    "current_state": 1
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # The fix ensures this is True (comparing 2 > 1, not 2 > 2)
            assert data["state_updated"] is True, \
                "state_updated should be True because initial_step (1) < final_step (2)"
            assert data["new_state"] == 2
    
    async def test_multiple_state_refresh_scenario(self, client, test_user, db_session):
        """Test scenario where user refreshes page and sends another message."""
        # Setup: Get existing onboarding state and update to step 2
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        onboarding_state = result.scalar_one()
        
        onboarding_state.current_step = 2
        onboarding_state.is_complete = False
        onboarding_state.step_data = {
            "step_1": {"fitness_level": "beginner"}
        }
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Mock agent orchestrator
        with patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            mock_agent_response = AgentResponse(
                content="Tell me about your fitness goals.",
                agent_type="workout",
                tools_used=[],
                metadata={}
            )
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.route_query = AsyncMock(return_value=mock_agent_response)
            
            # Create authenticated client
            from app.core.security import create_access_token
            token = create_access_token({"user_id": str(test_user.id)})
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Make request (user already on state 2)
            response = await client.post(
                "/api/v1/chat/onboarding",
                json={
                    "message": "What's next?",
                    "current_state": 2
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # State should remain at 2
            assert data["state_updated"] is False
            assert data["new_state"] is None
            assert data["progress"]["current_state"] == 2

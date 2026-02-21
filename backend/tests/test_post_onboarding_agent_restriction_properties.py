"""
Property-based tests for post-onboarding agent restriction.

Property 10: Post-Onboarding Agent Restriction
- For any completed user, verify only general agent is accessible

Validates: Requirements 2.4.1, 2.4.2
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.models.profile import UserProfile
from app.services.agent_orchestrator import AgentOrchestrator, AgentType


pytestmark = pytest.mark.asyncio


class TestPostOnboardingAgentRestrictionProperty:
    """Property tests for post-onboarding agent restriction."""
    
    @given(
        requested_agent=st.sampled_from([
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SUPPLEMENT,
            AgentType.TRACKER,
            AgentType.SCHEDULER,
            AgentType.GENERAL
        ])
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.property
    async def test_property_10_post_onboarding_agent_restriction(
        self,
        requested_agent: AgentType,
        db_session: AsyncSession
    ):
        """
        Feature: backend-onboarding-chat-integration, Property 10
        
        **Property 10: Post-Onboarding Agent Restriction**
        
        **Validates: Requirements 2.4.1, 2.4.2**
        
        For any user with completed onboarding (onboarding_completed = True),
        verify that:
        1. If requested_agent is GENERAL: request is allowed
        2. If requested_agent is any specialized agent: request is rejected
        3. The orchestrator forces agent_type to GENERAL
        4. onboarding_mode is set to False
        
        This property ensures that completed users can only access the
        general agent, regardless of which agent they request.
        
        Args:
            requested_agent: The agent type requested by the user
            db_session: Database session fixture
        """
        # Create user with completed onboarding
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,  # Completed
            step_data={f"step_{i}": {"test": "data"} for i in range(1, 10)},
            agent_history=[]
        )
        db_session.add(onboarding_state)
        
        # Create user profile (required for completed onboarding)
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            fitness_level="beginner",
            is_locked=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        # Eagerly load onboarding_state relationship to avoid lazy load in async context
        result = await db_session.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.onboarding_state))
        )
        user = result.scalar_one()
        
        # Verify user.onboarding_completed property returns True
        assert user.onboarding_completed is True, \
            "user.onboarding_completed must be True for completed onboarding"
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
        
        # Determine expected behavior based on requested agent
        should_reject = requested_agent != AgentType.GENERAL
        
        if should_reject:
            # Property: Specialized agents should be rejected for completed users
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Test query",
                    agent_type=requested_agent,
                    voice_mode=False,
                    onboarding_mode=False
                )
            
            # Verify error message indicates agent restriction
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in [
                "general",
                "only",
                "available",
                "post-onboarding",
                "completed"
            ]), (
                f"Error message should indicate only general agent is available. "
                f"Got: {exc_info.value}"
            )
        
        else:
            # Property: General agent should be allowed for completed users
            # Mock the agent to avoid actual LLM calls
            with patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
                mock_agent = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Test response"
                mock_response.agent_type = "general"
                mock_response.tools_used = []
                mock_agent.process_text = AsyncMock(return_value=mock_response)
                mock_get_agent.return_value = mock_agent
                
                # Should not raise an error
                response = await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Test query",
                    agent_type=requested_agent,
                    voice_mode=False,
                    onboarding_mode=False
                )
                
                # Verify response is from general agent
                assert response.agent_type == "general", \
                    "Response must be from general agent for completed users"
                
                # Verify agent was created with GENERAL type
                mock_get_agent.assert_called_once()
                call_args = mock_get_agent.call_args[0]
                assert call_args[0] == AgentType.GENERAL, \
                    "Orchestrator must force GENERAL agent for completed users"
    
    @given(
        onboarding_mode=st.booleans()
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.property
    async def test_property_10_onboarding_mode_false_for_completed_users(
        self,
        onboarding_mode: bool,
        db_session: AsyncSession
    ):
        """
        Feature: backend-onboarding-chat-integration, Property 10 (Part 2)
        
        Verify that onboarding_mode must be False for completed users.
        If onboarding_mode=True is passed for a completed user, it should
        be rejected.
        
        Args:
            onboarding_mode: The onboarding mode flag
            db_session: Database session fixture
        """
        # Create user with completed onboarding
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create completed onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {"test": "data"} for i in range(1, 10)},
            agent_history=[]
        )
        db_session.add(onboarding_state)
        
        # Create user profile
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            fitness_level="beginner",
            is_locked=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        # Eagerly load onboarding_state relationship to avoid lazy load in async context
        result = await db_session.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.onboarding_state))
        )
        user = result.scalar_one()
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
        
        if onboarding_mode:
            # Property: onboarding_mode=True should be rejected for completed users
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Test query",
                    agent_type=AgentType.GENERAL,
                    voice_mode=False,
                    onboarding_mode=True  # Should be rejected
                )
            
            # Verify error message indicates onboarding already completed
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in [
                "already",
                "completed",
                "onboarding"
            ]), (
                f"Error message should indicate onboarding already completed. "
                f"Got: {exc_info.value}"
            )
        
        else:
            # Property: onboarding_mode=False should be allowed for completed users
            # Mock the agent to avoid actual LLM calls
            with patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
                mock_agent = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Test response"
                mock_response.agent_type = "general"
                mock_response.tools_used = []
                mock_agent.process_text = AsyncMock(return_value=mock_response)
                mock_get_agent.return_value = mock_agent
                
                # Should not raise an error
                response = await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Test query",
                    agent_type=AgentType.GENERAL,
                    voice_mode=False,
                    onboarding_mode=False  # Correct mode
                )
                
                # Verify response is successful
                assert response.agent_type == "general", \
                    "Response must be from general agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

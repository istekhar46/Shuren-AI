"""
Unit tests for BaseOnboardingAgent abstract class.

Tests verify:
- Abstract class cannot be instantiated directly
- _init_llm returns correct ChatAnthropic configuration
- save_context updates database correctly
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_anthropic import ChatAnthropic

from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import AgentResponse


# ============================================================================
# Test: Abstract Class Cannot Be Instantiated Directly
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_abstract_class_cannot_be_instantiated(db_session: AsyncSession):
    """
    Test that BaseOnboardingAgent cannot be instantiated directly.
    
    Validates Requirement 2.7: Abstract class raises TypeError when instantiated.
    """
    with pytest.raises(TypeError) as exc_info:
        BaseOnboardingAgent(db=db_session, context={})
    
    # Verify error message mentions abstract methods
    error_message = str(exc_info.value)
    assert "abstract" in error_message.lower() or "Can't instantiate" in error_message


# ============================================================================
# Test: _init_llm Returns Correct ChatAnthropic Configuration
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_init_llm_returns_correct_configuration(db_session: AsyncSession):
    """
    Test that _init_llm returns ChatAnthropic with correct configuration.
    
    Validates Requirement 2.6: LLM initialization with correct model and parameters.
    """
    # Create a concrete implementation for testing
    class ConcreteAgent(BaseOnboardingAgent):
        agent_type = "test_agent"
        
        async def process_message(self, message: str, user_id):
            return AgentResponse(
                message="test",
                agent_type=self.agent_type,
                step_complete=False,
                next_action="continue_conversation"
            )
        
        def get_tools(self):
            return []
        
        def get_system_prompt(self):
            return "Test prompt"
    
    # Mock settings to have API key
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Instantiate the concrete agent
        agent = ConcreteAgent(db=db_session, context={})
        
        # Verify LLM is initialized
        assert agent.llm is not None
        assert isinstance(agent.llm, ChatAnthropic)
        
        # Verify configuration
        assert agent.llm.model == "claude-sonnet-4-5-20250929"
        assert agent.llm.temperature == 0.7
        assert agent.llm.max_tokens == 2048


@pytest.mark.unit
@pytest.mark.asyncio
async def test_init_llm_raises_error_without_api_key(db_session: AsyncSession):
    """
    Test that _init_llm raises ValueError when ANTHROPIC_API_KEY is not configured.
    
    Validates Requirement 2.6: Error handling for missing API key.
    """
    # Create a concrete implementation for testing
    class ConcreteAgent(BaseOnboardingAgent):
        agent_type = "test_agent"
        
        async def process_message(self, message: str, user_id):
            return AgentResponse(
                message="test",
                agent_type=self.agent_type,
                step_complete=False,
                next_action="continue_conversation"
            )
        
        def get_tools(self):
            return []
        
        def get_system_prompt(self):
            return "Test prompt"
    
    # Mock settings to have no API key
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = None
        
        # Verify ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            ConcreteAgent(db=db_session, context={})
        
        assert "ANTHROPIC_API_KEY" in str(exc_info.value)


# ============================================================================
# Test: save_context Updates Database Correctly
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_context_updates_database(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_context correctly updates agent_context in database.
    
    Validates Requirement 2.5: Context saving functionality.
    """
    # Create a concrete implementation for testing
    class ConcreteAgent(BaseOnboardingAgent):
        agent_type = "test_agent"
        
        async def process_message(self, message: str, user_id):
            return AgentResponse(
                message="test",
                agent_type=self.agent_type,
                step_complete=False,
                next_action="continue_conversation"
            )
        
        def get_tools(self):
            return []
        
        def get_system_prompt(self):
            return "Test prompt"
    
    # Mock settings to have API key
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Instantiate the concrete agent
        agent = ConcreteAgent(db=db_session, context={})
        
        # Prepare test data
        agent_data = {
            "fitness_level": "intermediate",
            "experience_years": 2,
            "completed_at": "2024-01-15T10:30:00Z"
        }
        
        # Save context
        await agent.save_context(user_id=test_user.id, agent_data=agent_data)
        
        # Verify database was updated
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state is not None
        assert state.agent_context is not None
        assert "test_agent" in state.agent_context
        assert state.agent_context["test_agent"] == agent_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_context_preserves_existing_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_context preserves existing agent contexts.
    
    Validates Requirement 2.5: Context preservation when updating.
    """
    # Create a concrete implementation for testing
    class ConcreteAgent(BaseOnboardingAgent):
        agent_type = "test_agent"
        
        async def process_message(self, message: str, user_id):
            return AgentResponse(
                message="test",
                agent_type=self.agent_type,
                step_complete=False,
                next_action="continue_conversation"
            )
        
        def get_tools(self):
            return []
        
        def get_system_prompt(self):
            return "Test prompt"
    
    # Set up initial context
    from sqlalchemy import select, update
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    initial_context = {
        "other_agent": {
            "some_data": "value"
        }
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == test_user.id)
        .values(agent_context=initial_context)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Mock settings to have API key
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Instantiate the concrete agent
        agent = ConcreteAgent(db=db_session, context={})
        
        # Save new context
        agent_data = {"new_data": "test_value"}
        await agent.save_context(user_id=test_user.id, agent_data=agent_data)
        
        # Verify both contexts exist
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.agent_context is not None
        assert "other_agent" in state.agent_context
        assert "test_agent" in state.agent_context
        assert state.agent_context["other_agent"] == {"some_data": "value"}
        assert state.agent_context["test_agent"] == {"new_data": "test_value"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_context_raises_error_for_missing_user(db_session: AsyncSession):
    """
    Test that save_context raises ValueError for non-existent user.
    
    Validates Requirement 2.5: Error handling for invalid user_id.
    """
    # Create a concrete implementation for testing
    class ConcreteAgent(BaseOnboardingAgent):
        agent_type = "test_agent"
        
        async def process_message(self, message: str, user_id):
            return AgentResponse(
                message="test",
                agent_type=self.agent_type,
                step_complete=False,
                next_action="continue_conversation"
            )
        
        def get_tools(self):
            return []
        
        def get_system_prompt(self):
            return "Test prompt"
    
    # Mock settings to have API key
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Instantiate the concrete agent
        agent = ConcreteAgent(db=db_session, context={})
        
        # Try to save context for non-existent user
        non_existent_user_id = uuid4()
        agent_data = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            await agent.save_context(user_id=non_existent_user_id, agent_data=agent_data)
        
        assert "No onboarding state found" in str(exc_info.value)
        assert str(non_existent_user_id) in str(exc_info.value)


# ============================================================================
# Test: Concrete Implementation Must Implement All Abstract Methods
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_concrete_class_must_implement_all_abstract_methods(db_session: AsyncSession):
    """
    Test that concrete classes must implement all abstract methods.
    
    Validates Requirement 2.2, 2.3, 2.4: Abstract method enforcement.
    """
    # Test missing process_message
    with pytest.raises(TypeError):
        class IncompleteAgent1(BaseOnboardingAgent):
            agent_type = "incomplete"
            
            def get_tools(self):
                return []
            
            def get_system_prompt(self):
                return "Test"
        
        IncompleteAgent1(db=db_session, context={})
    
    # Test missing get_tools
    with pytest.raises(TypeError):
        class IncompleteAgent2(BaseOnboardingAgent):
            agent_type = "incomplete"
            
            async def process_message(self, message: str, user_id):
                return AgentResponse(
                    message="test",
                    agent_type=self.agent_type,
                    step_complete=False,
                    next_action="continue_conversation"
                )
            
            def get_system_prompt(self):
                return "Test"
        
        IncompleteAgent2(db=db_session, context={})
    
    # Test missing get_system_prompt
    with pytest.raises(TypeError):
        class IncompleteAgent3(BaseOnboardingAgent):
            agent_type = "incomplete"
            
            async def process_message(self, message: str, user_id):
                return AgentResponse(
                    message="test",
                    agent_type=self.agent_type,
                    step_complete=False,
                    next_action="continue_conversation"
                )
            
            def get_tools(self):
                return []
        
        IncompleteAgent3(db=db_session, context={})

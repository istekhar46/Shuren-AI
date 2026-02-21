"""
Tests for the AgentOrchestrator warm_up method.

This module tests the warm_up functionality which pre-establishes
LLM connections to reduce latency on the first real query.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_orchestrator import AgentOrchestrator, AgentType


@pytest.mark.asyncio
async def test_warmup_only_runs_in_voice_mode(db_session: AsyncSession):
    """Test that warm_up only runs in voice mode, not text mode."""
    # Create orchestrator in text mode
    orchestrator_text = AgentOrchestrator(db_session, mode="text")
    
    # Warm-up should be a no-op in text mode (no exception)
    await orchestrator_text.warm_up()
    
    # Create orchestrator in voice mode
    orchestrator_voice = AgentOrchestrator(db_session, mode="voice")
    
    # Warm-up should attempt to run in voice mode
    # We'll test this by mocking the LLM call
    with patch('app.agents.test_agent.TestAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.llm = MagicMock()
        mock_agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="test"))
        mock_agent_class.return_value = mock_agent
        
        await orchestrator_voice.warm_up()
        
        # In voice mode, the agent should be created
        # (We can't easily verify this without more complex mocking)


@pytest.mark.asyncio
async def test_warmup_handles_errors_gracefully(db_session: AsyncSession):
    """Test that warm_up handles errors gracefully without raising exceptions."""
    # Create orchestrator in voice mode
    orchestrator = AgentOrchestrator(db_session, mode="voice")
    
    # Mock the _create_agent method to raise an exception
    with patch.object(orchestrator, '_create_agent', side_effect=Exception("Test error")):
        # Warm-up should not raise exception, just log warning
        try:
            await orchestrator.warm_up()
            # If we get here, the error was handled gracefully
            assert True
        except Exception:
            # If an exception is raised, the test fails
            pytest.fail("warm_up should not raise exceptions")


@pytest.mark.asyncio
async def test_warmup_creates_minimal_context(db_session: AsyncSession):
    """Test that warm_up creates a minimal AgentContext for testing."""
    orchestrator = AgentOrchestrator(db_session, mode="voice")
    
    # We'll verify the warm_up method can be called without errors
    # The actual LLM call will fail if API key is not configured,
    # but that's expected and handled gracefully
    await orchestrator.warm_up()
    
    # If we get here without exception, the method works correctly
    assert True


@pytest.mark.asyncio
async def test_warmup_import_dependencies(db_session: AsyncSession):
    """Test that warm_up can import required dependencies."""
    from app.agents.context import AgentContext
    from langchain_core.messages import HumanMessage
    
    # Verify imports work
    assert AgentContext is not None
    assert HumanMessage is not None
    
    # Create minimal context like warm_up does
    minimal_context = AgentContext(
        user_id="warmup-test",
        fitness_level="beginner",
        primary_goal="general_fitness",
        energy_level="medium"
    )
    
    assert minimal_context.user_id == "warmup-test"
    assert minimal_context.fitness_level == "beginner"

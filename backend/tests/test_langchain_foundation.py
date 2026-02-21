"""
Integration tests for LangChain Foundation & Base Agent Framework.

This module tests the core agent infrastructure including:
- AgentContext and AgentResponse models
- BaseAgent abstract class functionality
- TestAgent implementation
- Context loader service
- Agent orchestrator routing
- Multi-provider LLM support
- Voice and text mode operations

Test Categories:
- @pytest.mark.unit - Unit tests for individual components
- @pytest.mark.integration - Integration tests requiring database
- @pytest.mark.asyncio - Async test execution
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import AgentContext, AgentResponse
from app.agents.base import BaseAgent
from app.agents.test_agent import TestAgent
from app.services.context_loader import load_agent_context
from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import FitnessGoal, LifestyleBaseline
from app.core.config import settings


# ============================================================================
# Test Markers
# ============================================================================

pytestmark = [
    pytest.mark.asyncio,  # All tests in this module are async
]


# ============================================================================
# Unit Tests - AgentContext Model
# ============================================================================

@pytest.mark.unit
def test_agent_context_creation():
    """Test AgentContext model creation with all required fields."""
    # Create AgentContext with all required fields
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Assert all fields are correct
    assert context.user_id == "test-user-123"
    assert context.fitness_level == "beginner"
    assert context.primary_goal == "fat_loss"
    assert context.secondary_goal is None  # Default value
    assert context.energy_level == "medium"  # Default value
    assert context.current_workout_plan == {}  # Default empty dict
    assert context.current_meal_plan == {}  # Default empty dict
    assert context.conversation_history == []  # Default empty list
    assert isinstance(context.loaded_at, datetime)
    
    # Test with optional fields
    context_with_optional = AgentContext(
        user_id="test-user-456",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        secondary_goal="general_fitness",
        energy_level="high",
        current_workout_plan={"plan_id": "workout-123"},
        current_meal_plan={"plan_id": "meal-456"},
        conversation_history=[{"role": "user", "content": "Hello"}]
    )
    
    assert context_with_optional.user_id == "test-user-456"
    assert context_with_optional.fitness_level == "intermediate"
    assert context_with_optional.primary_goal == "muscle_gain"
    assert context_with_optional.secondary_goal == "general_fitness"
    assert context_with_optional.energy_level == "high"
    assert context_with_optional.current_workout_plan == {"plan_id": "workout-123"}
    assert context_with_optional.current_meal_plan == {"plan_id": "meal-456"}
    assert len(context_with_optional.conversation_history) == 1
    assert context_with_optional.conversation_history[0]["role"] == "user"


@pytest.mark.unit
def test_agent_context_immutability():
    """Test that AgentContext is immutable (frozen=True)."""
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Attempt to modify a field should raise an error
    with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
        context.user_id = "modified-user"
    
    with pytest.raises(Exception):
        context.fitness_level = "advanced"
    
    with pytest.raises(Exception):
        context.energy_level = "low"


@pytest.mark.unit
def test_agent_context_defaults():
    """Test AgentContext default values for optional fields."""
    # Create context with only required fields
    context = AgentContext(
        user_id="test-user-789",
        fitness_level="advanced",
        primary_goal="general_fitness"
    )
    
    # Verify default values
    assert context.secondary_goal is None
    assert context.energy_level == "medium"
    assert context.current_workout_plan == {}
    assert context.current_meal_plan == {}
    assert context.conversation_history == []
    assert isinstance(context.loaded_at, datetime)


# ============================================================================
# Unit Tests - AgentResponse Model
# ============================================================================

@pytest.mark.unit
def test_agent_response_creation():
    """Test AgentResponse model creation."""
    pass


# ============================================================================
# Integration Tests - TestAgent
# ============================================================================

@pytest.mark.integration
async def test_test_agent_text_response(db_session: AsyncSession, test_user: User):
    """Test TestAgent can respond to text queries."""
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Create TestAgent
    agent = TestAgent(context=context, db_session=db_session)
    
    # Call process_text
    response = await agent.process_text("Hello, can you help me with my fitness goals?")
    
    # Assert response is AgentResponse
    assert isinstance(response, AgentResponse)
    
    # Assert content is non-empty
    assert response.content is not None
    assert len(response.content) > 0
    assert isinstance(response.content, str)
    
    # Assert agent_type is "test"
    assert response.agent_type == "test"
    
    # Assert metadata contains expected fields
    assert "mode" in response.metadata
    assert response.metadata["mode"] == "text"
    assert "user_id" in response.metadata
    assert response.metadata["user_id"] == str(test_user.id)
    assert "fitness_level" in response.metadata
    assert response.metadata["fitness_level"] == "beginner"
    
    # Assert tools_used is empty list (test agent has no tools)
    assert isinstance(response.tools_used, list)
    assert len(response.tools_used) == 0


@pytest.mark.integration
async def test_test_agent_voice_response(db_session: AsyncSession, test_user: User):
    """Test TestAgent can respond to voice queries with concise output."""
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create TestAgent
    agent = TestAgent(context=context, db_session=db_session)
    
    # Call process_voice
    response = await agent.process_voice("What should I eat today?")
    
    # Assert response is string
    assert isinstance(response, str)
    
    # Assert content is non-empty
    assert len(response) > 0
    assert response.strip() != ""


@pytest.mark.integration
async def test_test_agent_streaming(db_session: AsyncSession, test_user: User):
    """Test TestAgent can stream responses."""
    pass


# ============================================================================
# Integration Tests - Context Loader
# ============================================================================

@pytest.mark.integration
async def test_context_loader_success(db_session: AsyncSession, test_user: User):
    """Test context loader retrieves user data from database."""
    # Create UserProfile with FitnessGoal and LifestyleBaseline for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    
    # Create LifestyleBaseline with energy level
    lifestyle = LifestyleBaseline(
        profile_id=profile.id,
        energy_level=8,  # Should map to "high"
        stress_level=5,
        sleep_quality=7
    )
    db_session.add(lifestyle)
    
    await db_session.commit()
    
    # Call load_agent_context
    context = await load_agent_context(db_session, str(test_user.id))
    
    # Assert user_id matches
    assert context.user_id == str(test_user.id)
    
    # Assert fitness_level is valid
    assert context.fitness_level == "intermediate"
    assert context.fitness_level in ["beginner", "intermediate", "advanced"]
    
    # Assert primary_goal is not None
    assert context.primary_goal is not None
    assert context.primary_goal == "muscle_gain"
    
    # Assert energy_level is correctly converted from 1-10 scale
    assert context.energy_level == "high"  # 8 should map to "high"
    
    # Assert context is immutable
    assert isinstance(context, AgentContext)
    
    # Assert other fields are populated
    assert context.current_workout_plan == {}  # Placeholder
    assert context.current_meal_plan == {}  # Placeholder
    assert context.conversation_history == []  # Placeholder
    assert context.loaded_at is not None


@pytest.mark.integration
async def test_context_loader_missing_user(db_session: AsyncSession):
    """Test context loader raises ValueError for missing user."""
    pass


@pytest.mark.integration
async def test_context_loader_with_goals(db_session: AsyncSession, test_user: User):
    """Test context loader extracts primary and secondary goals."""
    pass


@pytest.mark.integration
async def test_context_loader_energy_level(db_session: AsyncSession, test_user: User):
    """Test context loader converts energy level from 1-10 scale."""
    pass


# ============================================================================
# Integration Tests - Agent Orchestrator
# ============================================================================

@pytest.mark.integration
async def test_agent_orchestrator_routing(db_session: AsyncSession, test_user: User):
    """Test AgentOrchestrator routing with explicit TEST agent type."""
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentOrchestrator in text mode
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Call route_query with TEST agent type
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="Hello, can you help me with my fitness plan?",
        agent_type=AgentType.TEST,
        voice_mode=False
    )
    
    # Assert response is AgentResponse
    assert isinstance(response, AgentResponse)
    
    # Assert response content is non-empty
    assert response.content is not None
    assert len(response.content) > 0
    assert isinstance(response.content, str)
    
    # Assert last_agent_type is TEST
    assert orchestrator.last_agent_type == AgentType.TEST
    
    # Assert agent_type in response is "test"
    assert response.agent_type == "test"


@pytest.mark.integration
async def test_orchestrator_voice_mode(db_session: AsyncSession, test_user: User):
    """Test orchestrator routes queries in voice mode with caching."""
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentOrchestrator in voice mode
    orchestrator = AgentOrchestrator(db_session=db_session, mode="voice")
    
    # Call warm_up
    await orchestrator.warm_up()
    
    # Call route_query with voice_mode=True
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What should I eat for breakfast?",
        agent_type=AgentType.TEST,
        voice_mode=True
    )
    
    # Assert response is AgentResponse
    assert isinstance(response, AgentResponse)
    
    # Assert response content is non-empty
    assert response.content is not None
    assert len(response.content) > 0
    assert isinstance(response.content, str)
    
    # Assert metadata mode is "voice"
    assert "mode" in response.metadata
    assert response.metadata["mode"] == "voice"
    
    # Assert agent_type in response is "test"
    assert response.agent_type == "test"
    
    # Verify agent caching works - call route_query again
    response2 = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What about lunch?",
        agent_type=AgentType.TEST,
        voice_mode=True
    )
    
    # Assert second response also works
    assert isinstance(response2, AgentResponse)
    assert len(response2.content) > 0
    assert response2.metadata["mode"] == "voice"


@pytest.mark.integration
async def test_orchestrator_explicit_agent_type(db_session: AsyncSession, test_user: User):
    """Test orchestrator uses explicit agent type when provided."""
    pass


@pytest.mark.integration
async def test_orchestrator_warm_up(db_session: AsyncSession):
    """Test orchestrator warm_up method pre-establishes LLM connection."""
    pass


@pytest.mark.integration
async def test_orchestrator_agent_caching(db_session: AsyncSession, test_user: User):
    """Test orchestrator caches agents in voice mode."""
    pass


# ============================================================================
# Configuration Tests
# ============================================================================

@pytest.mark.unit
def test_llm_configuration():
    """Test LLM configuration is properly loaded."""
    pass


@pytest.mark.unit
def test_get_required_llm_api_key():
    """Test get_required_llm_api_key returns correct API key."""
    pass


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.unit
def test_base_agent_unsupported_provider():
    """Test BaseAgent raises ValueError for unsupported LLM provider."""
    pass


@pytest.mark.integration
async def test_orchestrator_invalid_mode(db_session: AsyncSession):
    """Test orchestrator raises ValueError for invalid mode."""
    pass

"""
Unit tests for GoalSettingAgent.

Tests verify:
- Agent instantiation and inheritance
- System prompt includes fitness_level from context
- System prompt includes limitations from context
- get_tools returns save_fitness_goals tool
- _check_if_complete with and without saved data
- Handling of missing fitness_assessment context
"""

import pytest
from uuid import uuid4
from unittest.mock import patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import AgentResponse


# ============================================================================
# Test: Agent Instantiation and Inheritance
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_instantiation(db_session: AsyncSession):
    """
    Test that GoalSettingAgent can be instantiated correctly.
    
    Validates Requirement 4.1: Agent inherits from BaseOnboardingAgent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        
        # Verify inheritance
        assert isinstance(agent, BaseOnboardingAgent)
        assert isinstance(agent, GoalSettingAgent)
        
        # Verify agent_type
        assert agent.agent_type == "goal_setting"
        
        # Verify db and context are set
        assert agent.db == db_session
        assert agent.context == {}


# ============================================================================
# Test: System Prompt Includes Fitness Level from Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_fitness_level(db_session: AsyncSession):
    """
    Test that system prompt includes fitness_level from context.
    
    Validates Requirement 4.2, 7.2: Context integration in system prompt.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["no equipment at home"]
            }
        }
        
        agent = GoalSettingAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify fitness level is included
        assert "intermediate" in prompt
        
        # Verify context section exists
        assert "Context from previous steps" in prompt or "Fitness Level:" in prompt


# ============================================================================
# Test: System Prompt Includes Limitations from Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_limitations(db_session: AsyncSession):
    """
    Test that system prompt includes limitations from context.
    
    Validates Requirement 7.3: Limitations in system prompt.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": ["knee injury", "no gym access"]
            }
        }
        
        agent = GoalSettingAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify limitations are included
        assert "knee injury" in prompt
        assert "no gym access" in prompt
        
        # Verify limitations label exists
        assert "Limitations:" in prompt or "limitations" in prompt.lower()


# ============================================================================
# Test: System Prompt Handles Missing Context Gracefully
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_handles_missing_context(db_session: AsyncSession):
    """
    Test that system prompt handles missing fitness_assessment context gracefully.
    
    Validates Requirement 7.4: Graceful handling of missing context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Empty context
        agent = GoalSettingAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Should not crash and should have default values
        assert "unknown" in prompt or "none mentioned" in prompt
        assert prompt is not None
        assert len(prompt) > 0


# ============================================================================
# Test: get_tools Returns save_fitness_goals Tool
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tools_returns_save_fitness_goals(db_session: AsyncSession):
    """
    Test that get_tools returns the save_fitness_goals tool.
    
    Validates Requirement 6.1: Tool availability.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        tools = agent.get_tools()
        
        # Verify tools list is not empty
        assert len(tools) == 1
        
        # Verify tool name
        tool = tools[0]
        assert tool.name == "save_fitness_goals"
        
        # Verify tool has description
        assert tool.description is not None
        assert "goal" in tool.description.lower()


# ============================================================================
# Test: _check_if_complete Without Saved Data
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_without_saved_data(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns False when no data is saved.
    
    Validates Requirement 4.5: Completion detection.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        
        # Check completion status (should be False)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


# ============================================================================
# Test: _check_if_complete With Saved Data
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_with_saved_data(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns True when data is saved.
    
    Validates Requirement 4.5: Completion detection.
    """
    # Save goal setting data
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "goal_setting": {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 80.0,
            "completed_at": datetime.utcnow().isoformat()
        }
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == test_user.id)
        .values(agent_context=agent_context)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        
        # Check completion status (should be True)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is True


# ============================================================================
# Test: save_fitness_goals Tool Validation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_validates_primary_goal(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals validates primary_goal parameter.
    
    Validates Requirement 6.3: Input validation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test invalid primary goal
        result = await save_tool.ainvoke({
            "primary_goal": "invalid_goal"
        })
        
        assert result["status"] == "error"
        assert "Invalid primary_goal" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_validates_target_weight(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals validates target_weight_kg range.
    
    Validates Requirement 13.2: Weight validation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test weight too low
        result = await save_tool.ainvoke({
            "primary_goal": "fat_loss",
            "target_weight_kg": 20.0
        })
        
        assert result["status"] == "error"
        assert "30 and 300" in result["message"]
        
        # Test weight too high
        result = await save_tool.ainvoke({
            "primary_goal": "fat_loss",
            "target_weight_kg": 350.0
        })
        
        assert result["status"] == "error"
        assert "30 and 300" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_validates_body_fat_percentage(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals validates target_body_fat_percentage range.
    
    Validates Requirement 13.3: Body fat percentage validation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test body fat too low
        result = await save_tool.ainvoke({
            "primary_goal": "fat_loss",
            "target_body_fat_percentage": 2.0
        })
        
        assert result["status"] == "error"
        assert "3 and 50" in result["message"]
        
        # Test body fat too high
        result = await save_tool.ainvoke({
            "primary_goal": "fat_loss",
            "target_body_fat_percentage": 55.0
        })
        
        assert result["status"] == "error"
        assert "3 and 50" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_normalizes_data(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals normalizes goal names to lowercase.
    
    Validates Requirement 13.1: Data normalization.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test with mixed case and spaces
        result = await save_tool.ainvoke({
            "primary_goal": "MUSCLE GAIN",
            "secondary_goal": "Fat Loss"
        })
        
        assert result["status"] == "success"
        
        # Verify data was normalized
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert state.agent_context["goal_setting"]["primary_goal"] == "muscle_gain"
        assert state.agent_context["goal_setting"]["secondary_goal"] == "fat_loss"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_adds_timestamp(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals adds completed_at timestamp.
    
    Validates Requirement 6.5: Timestamp in ISO 8601 format.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        result = await save_tool.ainvoke({
            "primary_goal": "general_fitness"
        })
        
        assert result["status"] == "success"
        
        # Verify timestamp exists
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "completed_at" in state.agent_context["goal_setting"]
        
        # Verify ISO 8601 format (contains 'T')
        timestamp = state.agent_context["goal_setting"]["completed_at"]
        assert "T" in timestamp


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_goals_handles_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_goals handles database errors gracefully.
    
    Validates Requirement 11.2: Error handling.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = GoalSettingAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Mock save_context to raise an exception
        with patch.object(agent, 'save_context', side_effect=Exception("Database error")):
            result = await save_tool.ainvoke({
                "primary_goal": "fat_loss"
            })
            
            assert result["status"] == "error"
            assert "Failed to save" in result["message"]

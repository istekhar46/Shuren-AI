"""
Unit tests for FitnessAssessmentAgent.

Tests verify:
- Agent instantiation and inheritance
- System prompt contains required content
- get_tools returns save_fitness_assessment tool
- _check_if_complete with and without saved data
- Medical topic handling (redirect to fitness questions)
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
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
    Test that FitnessAssessmentAgent can be instantiated correctly.
    
    Validates Requirement 1.1: Agent inherits from BaseOnboardingAgent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        
        # Verify inheritance
        assert isinstance(agent, BaseOnboardingAgent)
        assert isinstance(agent, FitnessAssessmentAgent)
        
        # Verify agent_type
        assert agent.agent_type == "fitness_assessment"
        
        # Verify db and context are set
        assert agent.db == db_session
        assert agent.context == {}


# ============================================================================
# Test: System Prompt Contains Required Content
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_contains_required_content(db_session: AsyncSession):
    """
    Test that system prompt contains all required elements.
    
    Validates Requirements 9.1-9.7: System prompt content.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Verify role definition
        assert "Fitness Assessment Agent" in prompt
        
        # Verify fitness level definitions
        assert "beginner" in prompt.lower()
        assert "intermediate" in prompt.lower()
        assert "advanced" in prompt.lower()
        
        # Verify guidelines
        assert "1-2 questions" in prompt or "one or two questions" in prompt.lower()
        assert "medical advice" in prompt.lower()
        
        # Verify tool calling instructions
        assert "save_fitness_assessment" in prompt
        
        # Verify medical topic handling
        assert "redirect" in prompt.lower() or "acknowledge" in prompt.lower()


# ============================================================================
# Test: get_tools Returns save_fitness_assessment Tool
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tools_returns_save_fitness_assessment(db_session: AsyncSession):
    """
    Test that get_tools returns the save_fitness_assessment tool.
    
    Validates Requirement 3.1: Tool availability.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        tools = agent.get_tools()
        
        # Verify tools list is not empty
        assert len(tools) == 1
        
        # Verify tool name
        tool = tools[0]
        assert tool.name == "save_fitness_assessment"
        
        # Verify tool has description
        assert tool.description is not None
        assert "fitness" in tool.description.lower()


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
    
    Validates Requirement 1.4: Completion detection.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        
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
    
    Validates Requirement 1.4: Completion detection.
    """
    # Save fitness assessment data
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": [],
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
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        
        # Check completion status (should be True)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is True


# ============================================================================
# Test: save_fitness_assessment Tool Validation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_tool_validates_fitness_level(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment validates fitness_level parameter.
    
    Validates Requirement 3.3: Input validation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test invalid fitness level
        result = await save_tool.ainvoke({
            "fitness_level": "invalid_level",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": [],
            "primary_goal": "fat_loss"
        })
        
        assert result["status"] == "error"
        assert "Invalid fitness_level" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_tool_validates_primary_goal(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment validates primary_goal parameter.
    
    Validates Requirement 4.2: Goal validation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test invalid primary goal
        result = await save_tool.ainvoke({
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": [],
            "primary_goal": "invalid_goal"
        })
        
        assert result["status"] == "error"
        assert "Invalid primary_goal" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_tool_normalizes_data(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment normalizes fitness_level and goals to lowercase.
    
    Validates Requirement 13.1: Data normalization.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Test with mixed case
        result = await save_tool.ainvoke({
            "fitness_level": "INTERMEDIATE",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": ["  some limitation  "],
            "primary_goal": "FAT LOSS",
            "secondary_goal": "Muscle Gain"
        })
        
        assert result["status"] == "success"
        
        # Verify data was normalized
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"
        assert state.agent_context["fitness_assessment"]["limitations"][0] == "some limitation"
        assert state.agent_context["fitness_assessment"]["primary_goal"] == "fat_loss"
        assert state.agent_context["fitness_assessment"]["secondary_goal"] == "muscle_gain"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_tool_adds_timestamp(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment adds completed_at timestamp.
    
    Validates Requirement 3.5: Timestamp in ISO 8601 format.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        result = await save_tool.ainvoke({
            "fitness_level": "beginner",
            "experience_details": {"frequency": "new to exercise"},
            "limitations": [],
            "primary_goal": "general_fitness"
        })
        
        assert result["status"] == "success"
        
        # Verify timestamp exists
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "completed_at" in state.agent_context["fitness_assessment"]
        
        # Verify ISO 8601 format (contains 'T' and ends with 'Z' or has timezone)
        timestamp = state.agent_context["fitness_assessment"]["completed_at"]
        assert "T" in timestamp


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_tool_handles_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment handles database errors gracefully.
    
    Validates Requirement 11.2: Error handling.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        # Mock db.execute to raise an exception
        with patch.object(agent.db, 'execute', side_effect=Exception("Database error")):
            result = await save_tool.ainvoke({
                "fitness_level": "beginner",
                "experience_details": {"frequency": "new"},
                "limitations": [],
                "primary_goal": "general_fitness"
            })
            
            assert result["status"] == "error"
            assert "Failed to save" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_fitness_assessment_advances_to_step_2(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_fitness_assessment marks step 1 complete and advances to step 2.
    
    Validates Requirement 4.2: Step advancement.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = tools[0]
        
        result = await save_tool.ainvoke({
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "4 times per week"},
            "limitations": [],
            "primary_goal": "muscle_gain",
            "secondary_goal": "fat_loss",
            "goal_priority": "muscle_gain_primary"
        })
        
        assert result["status"] == "success"
        
        # Verify step advancement
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert state.step_1_complete is True
        assert state.current_step == 2
        assert state.current_agent == "workout_planning"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_goal_definitions(db_session: AsyncSession):
    """
    Test that system prompt includes goal definitions.
    
    Validates Requirement 4.1: Goal-setting functionality merged.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = FitnessAssessmentAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Verify goal definitions are present
        assert "fat loss" in prompt.lower() or "fat_loss" in prompt.lower()
        assert "muscle gain" in prompt.lower() or "muscle_gain" in prompt.lower()
        assert "general fitness" in prompt.lower() or "general_fitness" in prompt.lower()
        
        # Verify goal collection is mentioned
        assert "goal" in prompt.lower()
        assert "primary" in prompt.lower()

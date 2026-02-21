"""
Unit tests for SchedulingAgent.

Tests verify:
- Agent instantiation and inheritance
- System prompt includes workout plan context
- System prompt includes meal plan context
- get_tools returns scheduling tools
- _check_if_complete with and without saved schedules
- Handling of missing context
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.scheduling import SchedulingAgent
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
    Test that SchedulingAgent can be instantiated correctly.
    
    Validates Requirement 1.1: Agent inherits from BaseOnboardingAgent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = SchedulingAgent(db=db_session, context={})
        
        # Verify inheritance
        assert isinstance(agent, BaseOnboardingAgent)
        assert isinstance(agent, SchedulingAgent)
        
        # Verify agent_type
        assert agent.agent_type == "scheduling"
        
        # Verify db and context are set
        assert agent.db == db_session
        assert agent.context == {}


# ============================================================================
# Test: System Prompt Includes Workout Plan Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_workout_plan(db_session: AsyncSession):
    """
    Test that system prompt includes workout plan from context.
    
    Validates Requirement 6.1: Workout plan summary in system prompt.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 4,
                    "duration_minutes": 60
                }
            }
        }
        
        agent = SchedulingAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify workout plan details are included
        assert "4" in prompt or "4 days" in prompt
        assert "60" in prompt or "60 minutes" in prompt
        
        # Verify context section exists
        assert "Context from previous steps" in prompt or "Workout Plan:" in prompt


# ============================================================================
# Test: System Prompt Includes Meal Plan Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_meal_plan(db_session: AsyncSession):
    """
    Test that system prompt includes meal plan from context.
    
    Validates Requirement 6.2: Meal plan summary in system prompt.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "diet_planning": {
                "proposed_plan": {
                    "meal_frequency": 4,
                    "daily_calories": 2500
                }
            }
        }
        
        agent = SchedulingAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify meal plan details are included
        assert "4" in prompt or "4 meals" in prompt
        assert "2500" in prompt
        
        # Verify meal frequency is mentioned
        assert "meal" in prompt.lower()


# ============================================================================
# Test: System Prompt Includes All Schedule Instructions
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_includes_schedule_instructions(db_session: AsyncSession):
    """
    Test that system prompt includes instructions for all three schedules.
    
    Validates Requirements 6.3, 6.4, 6.5: Instructions for workout, meal, hydration.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "workout_planning": {"proposed_plan": {"frequency": 3, "duration_minutes": 45}},
            "diet_planning": {"proposed_plan": {"meal_frequency": 3, "daily_calories": 2000}}
        }
        
        agent = SchedulingAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify workout schedule instructions
        assert "workout" in prompt.lower()
        assert "days" in prompt.lower()
        assert "times" in prompt.lower()
        
        # Verify meal schedule instructions
        assert "meal" in prompt.lower()
        
        # Verify hydration instructions
        assert "hydration" in prompt.lower() or "water" in prompt.lower()
        
        # Verify tool calling instructions
        assert "save_workout_schedule" in prompt
        assert "save_meal_schedule" in prompt
        assert "save_hydration_preferences" in prompt


# ============================================================================
# Test: System Prompt Handles Missing Context Gracefully
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_handles_missing_context(db_session: AsyncSession):
    """
    Test that system prompt handles missing context gracefully.
    
    Validates graceful handling of missing workout/meal plan context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        # Empty context
        agent = SchedulingAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Should not crash and should have default values
        assert "unknown" in prompt
        assert prompt is not None
        assert len(prompt) > 0


# ============================================================================
# Test: get_tools Returns Empty List (Tools Created in process_message)
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tools_returns_empty_list(db_session: AsyncSession):
    """
    Test that get_tools returns empty list.
    
    Tools are created in process_message with bound user_id and db.
    
    Validates Requirement 1.2: Tool management.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = SchedulingAgent(db=db_session, context={})
        tools = agent.get_tools()
        
        # Verify tools list is empty (tools created in process_message)
        assert len(tools) == 0


# ============================================================================
# Test: _check_if_complete Without Saved Schedules
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_without_saved_schedules(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns False when no schedules are saved.
    
    Validates Requirement 1.11: Completion detection.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = SchedulingAgent(db=db_session, context={})
        
        # Check completion status (should be False)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


# ============================================================================
# Test: _check_if_complete With Only Workout Schedule
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_with_only_workout_schedule(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns False with only workout schedule.
    
    All three schedules must be saved for completion.
    """
    # Save only workout schedule
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "scheduling": {
            "workout_schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "times": ["07:00", "07:00", "07:00"],
                "completed_at": datetime.utcnow().isoformat()
            }
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
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = SchedulingAgent(db=db_session, context={})
        
        # Check completion status (should be False - missing meal and hydration)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


# ============================================================================
# Test: _check_if_complete With All Three Schedules
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_with_all_schedules(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns True when all schedules are saved.
    
    Validates Requirement 1.11: Completion detection with all schedules.
    """
    # Save all three schedules
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "scheduling": {
            "workout_schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "times": ["07:00", "07:00", "07:00"],
                "completed_at": datetime.utcnow().isoformat()
            },
            "meal_schedule": {
                "breakfast": "08:00",
                "lunch": "13:00",
                "dinner": "19:00",
                "completed_at": datetime.utcnow().isoformat()
            },
            "hydration_preferences": {
                "frequency_hours": 2,
                "target_ml": 3000,
                "completed_at": datetime.utcnow().isoformat()
            }
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
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = SchedulingAgent(db=db_session, context={})
        
        # Check completion status (should be True)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is True


# ============================================================================
# Test: process_message Returns Valid AgentResponse
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_message_returns_agent_response(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that process_message returns a valid AgentResponse.
    
    Validates Requirement 1.2: AgentResponse structure.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "workout_planning": {"proposed_plan": {"frequency": 3, "duration_minutes": 45}},
            "diet_planning": {"proposed_plan": {"meal_frequency": 3, "daily_calories": 2000}}
        }
        
        agent = SchedulingAgent(db=db_session, context=context)
        
        # Mock the agent executor to avoid actual LLM calls
        with patch('app.agents.onboarding.scheduling.AgentExecutor') as mock_executor_class:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Let's set up your workout schedule. Which days work best for you?"
            })
            mock_executor_class.return_value = mock_executor
            
            response = await agent.process_message(
                message="I want to set up my schedule",
                user_id=test_user.id
            )
            
            # Verify response structure
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "scheduling"
            assert isinstance(response.message, str)
            assert isinstance(response.step_complete, bool)
            assert response.next_action in ["continue_conversation", "complete_onboarding"]


# ============================================================================
# Test: process_message Sets next_action to complete_onboarding When Done
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_message_sets_complete_onboarding_when_done(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that process_message sets next_action to complete_onboarding when all schedules saved.
    
    Validates Requirement 1.11: Next action signaling.
    """
    # Save all three schedules first
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "scheduling": {
            "workout_schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "times": ["07:00", "07:00", "07:00"],
                "completed_at": datetime.utcnow().isoformat()
            },
            "meal_schedule": {
                "breakfast": "08:00",
                "lunch": "13:00",
                "dinner": "19:00",
                "completed_at": datetime.utcnow().isoformat()
            },
            "hydration_preferences": {
                "frequency_hours": 2,
                "target_ml": 3000,
                "completed_at": datetime.utcnow().isoformat()
            }
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
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "workout_planning": {"proposed_plan": {"frequency": 3, "duration_minutes": 45}},
            "diet_planning": {"proposed_plan": {"meal_frequency": 3, "daily_calories": 2000}}
        }
        
        agent = SchedulingAgent(db=db_session, context=context)
        
        # Mock the agent executor
        with patch('app.agents.onboarding.scheduling.AgentExecutor') as mock_executor_class:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Great! All schedules are set up."
            })
            mock_executor_class.return_value = mock_executor
            
            response = await agent.process_message(
                message="Done",
                user_id=test_user.id
            )
            
            # Verify completion signaling
            assert response.step_complete is True
            assert response.next_action == "complete_onboarding"

"""
Unit tests for WorkoutPlanningAgent.

Tests verify:
- Agent instantiation and inheritance
- System prompt contains required content and context
- get_tools returns three tools (generate, save, modify)
- process_message with preference collection
- generate_workout_plan tool invocation
- save_workout_plan tool with user_approved=True
- save_workout_plan tool rejection with user_approved=False
- modify_workout_plan tool invocation
- _check_if_complete returns True after approved save
- Error handling in tools (invalid parameters, database errors)
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import AgentResponse
from app.services.workout_plan_generator import WorkoutPlan, WorkoutDay, Exercise, ExerciseType


# ============================================================================
# Test: Agent Instantiation and Inheritance
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_instantiation(db_session: AsyncSession):
    """
    Test that WorkoutPlanningAgent can be instantiated correctly.
    
    Validates Requirement 1.1: Agent inherits from BaseOnboardingAgent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "intermediate"},
            "goal_setting": {"primary_goal": "muscle_gain"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        
        # Verify inheritance
        assert isinstance(agent, BaseOnboardingAgent)
        assert isinstance(agent, WorkoutPlanningAgent)
        
        # Verify agent_type
        assert agent.agent_type == "workout_planning"
        
        # Verify db and context are set
        assert agent.db == db_session
        assert agent.context == context
        
        # Verify workout_generator is initialized
        assert agent.workout_generator is not None
        
        # Verify current_plan storage is initialized
        assert agent.current_plan is None


# ============================================================================
# Test: System Prompt Contains Required Content and Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_contains_context_from_previous_agents(db_session: AsyncSession):
    """
    Test that system prompt includes context from fitness_assessment and goal_setting.
    
    Validates Requirement 10.1: System prompt includes fitness_level and primary_goal.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["knee pain", "no equipment"]
            },
            "goal_setting": {
                "primary_goal": "fat_loss"
            }
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify context is included
        assert "intermediate" in prompt
        assert "fat_loss" in prompt
        assert "knee pain" in prompt or "no equipment" in prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_contains_required_instructions(db_session: AsyncSession):
    """
    Test that system prompt contains all required instructions.
    
    Validates Requirements 10.2-10.8: System prompt instructions.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Verify role definition
        assert "Workout Planning Agent" in prompt
        
        # Verify asks about preferences
        assert "preferences" in prompt.lower()
        assert "location" in prompt.lower()
        assert "equipment" in prompt.lower()
        assert "frequency" in prompt.lower()
        
        # Verify tool calling instructions
        assert "generate_workout_plan" in prompt
        assert "save_workout_plan" in prompt
        assert "modify_workout_plan" in prompt
        
        # Verify approval detection instructions
        assert "yes" in prompt.lower() or "looks good" in prompt.lower()
        assert "user_approved=True" in prompt
        
        # Verify modification handling
        assert "modification" in prompt.lower() or "change" in prompt.lower()
        
        # Verify explanation requirement
        assert "explain" in prompt.lower() or "rationale" in prompt.lower()


# ============================================================================
# Test: get_tools Returns Three Tools
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tools_returns_three_tools(db_session: AsyncSession):
    """
    Test that get_tools returns generate, save, and modify tools.
    
    Validates Requirement 3.1: Tool availability.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        tools = agent.get_tools()
        
        # Verify three tools are returned
        assert len(tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in tools]
        assert "generate_workout_plan" in tool_names
        assert "save_workout_plan" in tool_names
        assert "modify_workout_plan" in tool_names
        
        # Verify all tools have descriptions
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


# ============================================================================
# Test: generate_workout_plan Tool Invocation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_tool_success(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_workout_plan tool successfully generates a plan.
    
    Validates Requirements 3.2-3.4: Tool parameters and plan generation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": []
            },
            "goal_setting": {
                "primary_goal": "muscle_gain"
            }
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        
        # Call tool
        result = await generate_tool.ainvoke({
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell", "dumbbells"]
        })
        
        # Verify result is a dict (WorkoutPlan)
        assert isinstance(result, dict)
        assert "frequency" in result
        assert "training_split" in result
        assert "workout_days" in result
        assert result["frequency"] == 4
        
        # Verify plan is stored in agent
        assert agent.current_plan is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_tool_uses_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_workout_plan uses fitness_level and primary_goal from context.
    
    Validates Requirement 3.3: Tool uses context from previous agents.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": ["no equipment"]
            },
            "goal_setting": {
                "primary_goal": "fat_loss"
            }
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        
        # Call tool
        result = await generate_tool.ainvoke({
            "frequency": 3,
            "location": "home",
            "duration_minutes": 45,
            "equipment": []
        })
        
        # Verify plan was generated (beginner should get Full Body split)
        assert isinstance(result, dict)
        assert "training_split" in result
        # Beginner with 3 days should get Full Body
        assert "Full Body" in result["training_split"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_tool_handles_invalid_parameters(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_workout_plan handles invalid parameters gracefully.
    
    Validates Requirement 14.1: Error handling for invalid parameters.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        
        # Test with invalid frequency
        result = await generate_tool.ainvoke({
            "frequency": 10,  # Invalid: must be 2-7
            "location": "gym",
            "duration_minutes": 60,
            "equipment": []
        })
        
        # Verify error response
        assert "error" in result
        assert "message" in result


# ============================================================================
# Test: save_workout_plan Tool with user_approved=True
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_workout_plan_tool_with_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_workout_plan saves data when user_approved=True.
    
    Validates Requirements 3.5-3.8: Save tool with approval.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        # Create plan data
        plan_data = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell"],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Call save tool with approval
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "user_approved": True
        })
        
        # Verify success
        assert result["status"] == "success"
        
        # Verify data was saved to database
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "workout_planning" in state.agent_context
        assert state.agent_context["workout_planning"]["user_approved"] is True
        assert "proposed_plan" in state.agent_context["workout_planning"]
        assert "completed_at" in state.agent_context["workout_planning"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_workout_plan_includes_metadata(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_workout_plan includes preferences and metadata.
    
    Validates Requirement 3.8: Save includes metadata.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        plan_data = {
            "frequency": 3,
            "location": "home",
            "duration_minutes": 45,
            "equipment": ["dumbbells"],
            "training_split": "Full Body",
            "workout_days": [],
            "progression_strategy": "Linear progression"
        }
        
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "user_approved": True
        })
        
        assert result["status"] == "success"
        
        # Verify metadata
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        workout_data = state.agent_context["workout_planning"]
        
        # Verify preferences are saved separately
        assert "preferences" in workout_data
        assert workout_data["preferences"]["location"] == "home"
        assert workout_data["preferences"]["frequency"] == 3
        assert workout_data["preferences"]["duration_minutes"] == 45
        assert workout_data["preferences"]["equipment"] == ["dumbbells"]
        
        # Verify timestamp
        assert "completed_at" in workout_data
        assert "T" in workout_data["completed_at"]  # ISO 8601 format


# ============================================================================
# Test: save_workout_plan Tool Rejection with user_approved=False
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_workout_plan_tool_rejects_without_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_workout_plan rejects when user_approved=False.
    
    Validates Requirement 3.6: Save tool rejection without approval.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        plan_data = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": [],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Call save tool without approval
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "user_approved": False
        })
        
        # Verify error response
        assert result["status"] == "error"
        assert "approval" in result["message"].lower()
        
        # Verify data was NOT saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "workout_planning" not in state.agent_context or \
               state.agent_context.get("workout_planning", {}).get("user_approved") is not True


# ============================================================================
# Test: modify_workout_plan Tool Invocation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_workout_plan_tool_success(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_workout_plan successfully modifies a plan.
    
    Validates Requirements 3.9-3.11: Modification tool.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        
        # Create current plan
        current_plan = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell"],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Modify frequency
        result = await modify_tool.ainvoke({
            "current_plan": current_plan,
            "modifications": {"frequency": 3}
        })
        
        # Verify modified plan
        assert isinstance(result, dict)
        assert result["frequency"] == 3
        # Frequency change should trigger new training split
        assert "training_split" in result
        
        # Verify plan is stored in agent
        assert agent.current_plan is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_workout_plan_tool_handles_invalid_modifications(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_workout_plan handles invalid modifications.
    
    Validates Requirement 14.5: Error handling for invalid modifications.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        
        current_plan = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": [],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Try invalid modification
        result = await modify_tool.ainvoke({
            "current_plan": current_plan,
            "modifications": {"frequency": 10}  # Invalid: must be 2-7
        })
        
        # Verify error response
        assert "error" in result
        assert "message" in result


# ============================================================================
# Test: _check_if_complete Returns True After Approved Save
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_returns_false_without_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns False when no approval exists.
    
    Validates Requirement 1.10: Completion detection.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        
        # Check completion (should be False)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_returns_true_with_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns True when user_approved=True.
    
    Validates Requirement 1.10: Completion detection after approval.
    """
    # Save workout planning data with approval
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "workout_planning": {
            "preferences": {"frequency": 4, "location": "gym"},
            "proposed_plan": {"frequency": 4, "training_split": "Upper/Lower"},
            "user_approved": True,
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
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        
        # Check completion (should be True)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_if_complete_returns_false_with_unapproved_data(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _check_if_complete returns False when user_approved=False.
    
    Validates Requirement 1.10: Completion requires approval.
    """
    # Save workout planning data WITHOUT approval
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "workout_planning": {
            "preferences": {"frequency": 4},
            "user_approved": False
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
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        
        # Check completion (should be False)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


# ============================================================================
# Test: Error Handling in Tools
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_handles_service_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_workout_plan handles service errors gracefully.
    
    Validates Requirement 14.3: Error handling for service failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        
        # Mock workout_generator to raise exception
        with patch.object(
            agent.workout_generator,
            'generate_plan',
            side_effect=Exception("Service error")
        ):
            result = await generate_tool.ainvoke({
                "frequency": 4,
                "location": "gym",
                "duration_minutes": 60,
                "equipment": []
            })
            
            # Verify error response
            assert "error" in result
            assert result["error"] == "generation_failed"
            assert "Failed to generate" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_workout_plan_handles_database_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_workout_plan handles database errors gracefully.
    
    Validates Requirement 14.3: Error handling for database failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        plan_data = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": [],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Mock save_context to raise exception
        with patch.object(agent, 'save_context', side_effect=Exception("Database error")):
            result = await save_tool.ainvoke({
                "plan_data": plan_data,
                "user_approved": True
            })
            
            # Verify error response
            assert result["status"] == "error"
            assert "Failed to save" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_workout_plan_handles_service_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_workout_plan handles service errors gracefully.
    
    Validates Requirement 14.3: Error handling for modification failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        
        current_plan = {
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": [],
            "training_split": "Upper/Lower",
            "workout_days": [],
            "progression_strategy": "Progressive overload"
        }
        
        # Mock modify_plan to raise exception
        with patch.object(
            agent.workout_generator,
            'modify_plan',
            side_effect=Exception("Service error")
        ):
            result = await modify_tool.ainvoke({
                "current_plan": current_plan,
                "modifications": {"frequency": 3}
            })
            
            # Verify error response
            assert "error" in result
            assert result["error"] == "modification_failed"
            assert "Failed to modify" in result["message"]

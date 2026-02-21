"""
Unit tests for DietPlanningAgent.

Tests verify:
- Agent instantiation and inheritance
- System prompt contains required content and context from all previous agents
- get_tools returns three tools (generate, save, modify)
- process_message with dietary preference collection
- generate_meal_plan tool invocation with workout plan context
- save_meal_plan tool with user_approved=True
- save_meal_plan tool rejection with user_approved=False
- modify_meal_plan tool invocation
- _check_if_complete returns True after approved save
- Error handling in tools (invalid parameters, database errors)
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import AgentResponse
from app.services.meal_plan_generator import MealPlan, SampleMeal, MealType


# ============================================================================
# Test: Agent Instantiation and Inheritance
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_instantiation(db_session: AsyncSession):
    """
    Test that DietPlanningAgent can be instantiated correctly.
    
    Validates Requirement 4.1: Agent inherits from BaseOnboardingAgent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "primary_goal": "muscle_gain"
            },
            "workout_planning": {
                "plan": {"frequency": 4}
            }
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        
        # Verify inheritance
        assert isinstance(agent, BaseOnboardingAgent)
        assert isinstance(agent, DietPlanningAgent)
        
        # Verify agent_type
        assert agent.agent_type == "diet_planning"
        
        # Verify db and context are set
        assert agent.db == db_session
        assert agent.context == context
        
        # Verify meal_generator is initialized
        assert agent.meal_generator is not None
        
        # Verify current_plan storage is initialized
        assert agent.current_plan is None


# ============================================================================
# Test: System Prompt Contains Context from All Previous Agents
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_contains_context_from_all_previous_agents(db_session: AsyncSession):
    """
    Test that system prompt includes context from fitness_assessment, goal_setting, and workout_planning.
    
    Validates Requirement 11.1: System prompt includes all previous agent context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "advanced",
                "limitations": [],
                "primary_goal": "fat_loss"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 5,
                    "training_split": "Push/Pull/Legs"
                }
            }
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        prompt = agent.get_system_prompt()
        
        # Verify context from all previous agents is included
        assert "advanced" in prompt
        assert "fat_loss" in prompt
        assert "5" in prompt  # workout frequency


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_prompt_contains_required_instructions(db_session: AsyncSession):
    """
    Test that system prompt contains all required instructions.
    
    Validates Requirements 11.2-11.8: System prompt instructions.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        prompt = agent.get_system_prompt()
        
        # Verify role definition
        assert "Diet Planning Agent" in prompt
        
        # Verify asks about dietary preferences
        assert "dietary" in prompt.lower() or "diet" in prompt.lower()
        assert "allergies" in prompt.lower()
        
        # Verify tool calling instructions
        assert "generate_meal_plan" in prompt
        assert "save_meal_plan" in prompt
        assert "modify_meal_plan" in prompt
        
        # Verify approval detection instructions
        assert "yes" in prompt.lower() or "looks good" in prompt.lower()
        assert "user_approved=True" in prompt
        
        # Verify dietary restriction handling
        assert "respect" in prompt.lower() or "honor" in prompt.lower()
        assert "restrictions" in prompt.lower()
        
        # Verify calorie/macro explanation requirement
        assert "calorie" in prompt.lower()
        assert "macro" in prompt.lower() or "protein" in prompt.lower()


# ============================================================================
# Test: get_tools Returns Three Tools
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tools_returns_three_tools(db_session: AsyncSession):
    """
    Test that get_tools returns generate, save, and modify tools.
    
    Validates Requirement 6.1: Tool availability.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        tools = agent.get_tools()
        
        # Verify three tools are returned
        assert len(tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in tools]
        assert "generate_meal_plan" in tool_names
        assert "save_meal_plan" in tool_names
        assert "modify_meal_plan" in tool_names
        
        # Verify all tools have descriptions
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


# ============================================================================
# Test: generate_meal_plan Tool with Workout Plan Context
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_meal_plan_tool_success(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_meal_plan tool successfully generates a plan.
    
    Validates Requirements 6.2-6.4: Tool parameters and plan generation.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": [],
                "primary_goal": "muscle_gain"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 4,
                    "training_split": "Upper/Lower"
                }
            }
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        
        # Call tool
        result = await generate_tool.ainvoke({
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": ["broccoli"],
            "meal_frequency": 4,
            "meal_prep_level": "medium"
        })
        
        # Verify result is a dict (MealPlan)
        assert isinstance(result, dict)
        assert "daily_calories" in result
        assert "protein_g" in result
        assert "carbs_g" in result
        assert "fats_g" in result
        assert "sample_meals" in result
        
        # Verify plan is stored in agent
        assert agent.current_plan is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_meal_plan_tool_uses_workout_plan_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_meal_plan uses workout plan from context.
    
    Validates Requirement 6.3: Tool uses workout plan context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": [],
                "primary_goal": "fat_loss"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 5,  # High frequency should affect calories
                    "training_split": "Push/Pull/Legs"
                }
            }
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        
        # Call tool
        result = await generate_tool.ainvoke({
            "diet_type": "vegetarian",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 3,
            "meal_prep_level": "low"
        })
        
        # Verify plan was generated
        assert isinstance(result, dict)
        assert "daily_calories" in result
        # High workout frequency should result in higher calories
        assert result["daily_calories"] > 1500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_meal_plan_tool_handles_invalid_parameters(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_meal_plan handles invalid parameters gracefully.
    
    Validates Requirement 14.2: Error handling for invalid parameters.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        
        # Test with invalid meal_frequency
        result = await generate_tool.ainvoke({
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 10,  # Invalid: must be 2-6
            "meal_prep_level": "medium"
        })
        
        # Verify error response
        assert "error" in result
        assert "message" in result


# ============================================================================
# Test: save_meal_plan Tool with user_approved=True
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_meal_plan_tool_with_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_meal_plan saves data when user_approved=True.
    
    Validates Requirements 6.5-6.8: Save tool with approval.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        
        # Create plan data
        plan_data = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": ["fish"],
            "meal_frequency": 4,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Snack, Dinner"
        }
        
        # Call save tool with approval and meal times
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "meal_times": {
                "breakfast": "07:00",
                "lunch": "12:00",
                "snack": "15:00",
                "dinner": "19:00"
            },
            "user_approved": True
        })
        
        # Verify success
        assert result["status"] == "success"
        
        # Verify data was saved to database
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "diet_planning" in state.agent_context
        assert state.agent_context["diet_planning"]["user_approved"] is True
        assert "plan" in state.agent_context["diet_planning"]
        assert "schedule" in state.agent_context["diet_planning"]
        assert "completed_at" in state.agent_context["diet_planning"]
        
        # Verify step advancement
        assert state.step_3_complete is True
        assert state.current_step == 4
        assert state.current_agent == "scheduling"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_meal_plan_includes_metadata(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_meal_plan includes preferences and metadata.
    
    Validates Requirement 6.8: Save includes metadata.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        
        plan_data = {
            "diet_type": "vegan",
            "allergies": ["nuts"],
            "dislikes": ["mushrooms"],
            "meal_frequency": 3,
            "meal_prep_level": "high",
            "daily_calories": 2000,
            "protein_g": 120,
            "carbs_g": 250,
            "fats_g": 56,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Dinner"
        }
        
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "meal_times": {
                "breakfast": "07:00",
                "lunch": "12:00",
                "dinner": "19:00"
            },
            "user_approved": True
        })
        
        assert result["status"] == "success"
        
        # Verify metadata
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        diet_data = state.agent_context["diet_planning"]
        
        # Verify plan and schedule are saved
        assert "plan" in diet_data
        assert diet_data["plan"]["diet_type"] == "vegan"
        assert diet_data["plan"]["allergies"] == ["nuts"]
        assert diet_data["plan"]["dislikes"] == ["mushrooms"]
        assert diet_data["plan"]["meal_frequency"] == 3
        assert diet_data["plan"]["meal_prep_level"] == "high"
        
        # Verify schedule
        assert "schedule" in diet_data
        assert diet_data["schedule"]["breakfast"] == "07:00"
        assert diet_data["schedule"]["lunch"] == "12:00"
        assert diet_data["schedule"]["dinner"] == "19:00"
        
        # Verify timestamp
        assert "completed_at" in diet_data
        assert "T" in diet_data["completed_at"]  # ISO 8601 format


# ============================================================================
# Test: save_meal_plan Tool Rejection with user_approved=False
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_meal_plan_tool_rejects_without_approval(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_meal_plan rejects when user_approved=False.
    
    Validates Requirement 6.6: Save tool rejection without approval.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        
        plan_data = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 4,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Snack, Dinner"
        }
        
        # Call save tool without approval
        result = await save_tool.ainvoke({
            "plan_data": plan_data,
            "meal_times": {
                "breakfast": "07:00",
                "lunch": "12:00",
                "snack": "15:00",
                "dinner": "19:00"
            },
            "user_approved": False
        })
        
        # Verify error response
        assert result["status"] == "error"
        assert "approval" in result["message"].lower()
        
        # Verify data was NOT saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "diet_planning" not in state.agent_context or \
               state.agent_context.get("diet_planning", {}).get("user_approved") is not True


# ============================================================================
# Test: modify_meal_plan Tool Invocation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_meal_plan_tool_success(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_meal_plan successfully modifies a plan.
    
    Validates Requirements 6.9-6.11: Modification tool.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_meal_plan")
        
        # Create current plan
        current_plan = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 3,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Dinner"
        }
        
        # Modify meal frequency
        result = await modify_tool.ainvoke({
            "current_plan": current_plan,
            "modifications": {"meal_frequency": 4}
        })
        
        # Verify modified plan
        assert isinstance(result, dict)
        assert result["meal_frequency"] == 4
        # Meal frequency change should trigger new meal timing
        assert "meal_timing_suggestions" in result
        
        # Verify plan is stored in agent
        assert agent.current_plan is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_meal_plan_tool_handles_invalid_modifications(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_meal_plan handles invalid modifications.
    
    Validates Requirement 14.5: Error handling for invalid modifications.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_meal_plan")
        
        current_plan = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 3,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Dinner"
        }
        
        # Try invalid modification
        result = await modify_tool.ainvoke({
            "current_plan": current_plan,
            "modifications": {"meal_frequency": 10}  # Invalid: must be 2-6
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
    
    Validates Requirement 4.11: Completion detection.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        
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
    
    Validates Requirement 4.11: Completion detection after approval.
    """
    # Save diet planning data with approval
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "diet_planning": {
            "preferences": {"diet_type": "omnivore", "meal_frequency": 4},
            "proposed_plan": {"daily_calories": 2400, "protein_g": 150},
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
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        
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
    
    Validates Requirement 4.11: Completion requires approval.
    """
    # Save diet planning data WITHOUT approval
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    agent_context = {
        "diet_planning": {
            "preferences": {"diet_type": "omnivore"},
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
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        
        # Check completion (should be False)
        is_complete = await agent._check_if_complete(test_user.id)
        
        assert is_complete is False


# ============================================================================
# Test: Error Handling in Tools
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_meal_plan_handles_service_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that generate_meal_plan handles service errors gracefully.
    
    Validates Requirement 14.3: Error handling for service failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        
        # Mock meal_generator to raise exception
        with patch.object(
            agent.meal_generator,
            'generate_plan',
            side_effect=Exception("Service error")
        ):
            result = await generate_tool.ainvoke({
                "diet_type": "omnivore",
                "allergies": [],
                "dislikes": [],
                "meal_frequency": 4,
                "meal_prep_level": "medium"
            })
            
            # Verify error response
            assert "error" in result
            assert result["error"] == "generation_failed"
            assert "Failed to generate" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_meal_plan_handles_database_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that save_meal_plan handles database errors gracefully.
    
    Validates Requirement 14.3: Error handling for database failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        
        plan_data = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 4,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Snack, Dinner"
        }
        
        # Mock save_context to raise exception
        with patch.object(agent, 'save_context', side_effect=Exception("Database error")):
            result = await save_tool.ainvoke({
                "plan_data": plan_data,
                "meal_times": {
                    "breakfast": "07:00",
                    "lunch": "12:00",
                    "snack": "15:00",
                    "dinner": "19:00"
                },
                "user_approved": True
            })
            
            # Verify error response
            assert result["status"] == "error"
            assert "Failed to save" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_modify_meal_plan_handles_service_errors(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that modify_meal_plan handles service errors gracefully.
    
    Validates Requirement 14.3: Error handling for modification failures.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        
        agent = DietPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        modify_tool = next(t for t in tools if t.name == "modify_meal_plan")
        
        current_plan = {
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 3,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [],
            "meal_timing_suggestions": "Breakfast, Lunch, Dinner"
        }
        
        # Mock modify_plan to raise exception
        with patch.object(
            agent.meal_generator,
            'modify_plan',
            side_effect=Exception("Service error")
        ):
            result = await modify_tool.ainvoke({
                "current_plan": current_plan,
                "modifications": {"meal_frequency": 4}
            })
            
            # Verify error response
            assert "error" in result
            assert result["error"] == "modification_failed"
            assert "Failed to modify" in result["message"]



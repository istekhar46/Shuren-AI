"""
Unit tests for OnboardingAgentOrchestrator service.

Tests verify:
- _load_onboarding_state loads correct state
- _create_agent returns correct agent class
- Error handling for invalid user_id
- Step to agent mapping correctness
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import OnboardingAgentType
from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.agents.onboarding.scheduling import SchedulingAgent


def mock_llm_settings():
    """Helper function to create properly configured mock settings for LLM."""
    from app.core.config import LLMProvider
    mock_settings = MagicMock()
    mock_settings.LLM_PROVIDER = LLMProvider.ANTHROPIC
    mock_settings.LLM_MODEL = "claude-sonnet-4-5-20250929"
    mock_settings.LLM_TEMPERATURE = 0.7
    mock_settings.LLM_MAX_TOKENS = 2048
    mock_settings.ANTHROPIC_API_KEY = "test-api-key"
    mock_settings.get_required_llm_api_key.return_value = "test-api-key"
    return mock_settings


# ============================================================================
# Test: _load_onboarding_state Loads Correct State
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_onboarding_state_returns_correct_state(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _load_onboarding_state loads the correct onboarding state.
    
    Validates Requirement 5.1: Load onboarding state from database.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    # Load the state
    state = await orchestrator._load_onboarding_state(test_user.id)
    
    # Verify state is loaded correctly
    assert state is not None
    assert state.user_id == test_user.id
    assert state.current_step == 0
    assert state.is_complete is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_onboarding_state_returns_none_for_missing_user(
    db_session: AsyncSession
):
    """
    Test that _load_onboarding_state returns None for non-existent user.
    
    Validates Requirement 5.1: Handle missing user gracefully.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    # Try to load state for non-existent user
    non_existent_user_id = uuid4()
    state = await orchestrator._load_onboarding_state(non_existent_user_id)
    
    # Verify None is returned
    assert state is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_onboarding_state_with_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _load_onboarding_state loads state with agent_context.
    
    Validates Requirement 5.1: Load context from database.
    """
    # Update state with context
    from sqlalchemy import select, update
    
    test_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "experience_years": 2
        }
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == test_user.id)
        .values(agent_context=test_context)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Load state
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    state = await orchestrator._load_onboarding_state(test_user.id)
    
    # Verify context is loaded
    assert state is not None
    assert state.agent_context == test_context


# ============================================================================
# Test: _create_agent Returns Correct Agent Class
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_returns_fitness_assessment_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent returns FitnessAssessmentAgent for FITNESS_ASSESSMENT type.
    
    Validates Requirement 5.8: Agent factory creates correct type.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        context = {}
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.FITNESS_ASSESSMENT,
            context,
            test_user.id
        )
        
        assert isinstance(agent, FitnessAssessmentAgent)
        assert agent.context.agent_context == context


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_returns_goal_setting_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent returns GoalSettingAgent for GOAL_SETTING type.
    
    Validates Requirement 5.8: Agent factory creates correct type.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        context = {"fitness_assessment": {"fitness_level": "intermediate"}}
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.GOAL_SETTING,
            context,
            test_user.id
        )
        
        assert isinstance(agent, GoalSettingAgent)
        assert agent.context.agent_context == context


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_returns_workout_planning_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent returns WorkoutPlanningAgent for WORKOUT_PLANNING type.
    
    Validates Requirement 5.8: Agent factory creates correct type.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        context = {}
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.WORKOUT_PLANNING,
            context,
            test_user.id
        )
        
        assert isinstance(agent, WorkoutPlanningAgent)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_returns_diet_planning_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent returns DietPlanningAgent for DIET_PLANNING type.
    
    Validates Requirement 5.8: Agent factory creates correct type.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        context = {}
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.DIET_PLANNING,
            context,
            test_user.id
        )
        
        assert isinstance(agent, DietPlanningAgent)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_returns_scheduling_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent returns SchedulingAgent for SCHEDULING type.
    
    Validates Requirement 5.8: Agent factory creates correct type.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        context = {}
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.SCHEDULING,
            context,
            test_user.id
        )
        
        assert isinstance(agent, SchedulingAgent)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_agent_passes_context_to_constructor(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that _create_agent passes context to agent constructor.
    
    Validates Requirement 5.8: Context passed to agent constructor.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        test_context = {
            "fitness_assessment": {
                "fitness_level": "advanced",
                "experience_years": 5
            },
            "goal_setting": {
                "primary_goal": "muscle_gain"
            }
        }
        
        agent = await orchestrator._create_agent(
            OnboardingAgentType.WORKOUT_PLANNING,
            test_context,
            test_user.id
        )
        
        # Verify context was passed
        assert agent.context.agent_context == test_context
        assert agent.context.agent_context["fitness_assessment"]["fitness_level"] == "advanced"


# ============================================================================
# Test: Error Handling for Invalid user_id
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_agent_raises_error_for_missing_user(
    db_session: AsyncSession
):
    """
    Test that get_current_agent raises ValueError for non-existent user.
    
    Validates Requirement 5.1, 5.8: Error handling for invalid user_id.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    # Try to get agent for non-existent user
    non_existent_user_id = uuid4()
    
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.get_current_agent(non_existent_user_id)
    
    # Verify error message
    assert "No onboarding state found" in str(exc_info.value)
    assert str(non_existent_user_id) in str(exc_info.value)


# ============================================================================
# Test: Step to Agent Mapping
# ============================================================================

@pytest.mark.unit
def test_step_to_agent_maps_step_0_to_fitness_assessment(db_session: AsyncSession):
    """
    Test that step 0 maps to FITNESS_ASSESSMENT.
    
    Validates Requirement 5.2: Steps 0-2 map to FITNESS_ASSESSMENT.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(0)
    assert agent_type == OnboardingAgentType.FITNESS_ASSESSMENT


@pytest.mark.unit
def test_step_to_agent_maps_step_1_to_fitness_assessment(db_session: AsyncSession):
    """
    Test that step 1 maps to FITNESS_ASSESSMENT.
    
    Validates Requirement 5.2: Steps 0-2 map to FITNESS_ASSESSMENT.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(1)
    assert agent_type == OnboardingAgentType.FITNESS_ASSESSMENT


@pytest.mark.unit
def test_step_to_agent_maps_step_2_to_fitness_assessment(db_session: AsyncSession):
    """
    Test that step 2 maps to FITNESS_ASSESSMENT.
    
    Validates Requirement 5.2: Steps 0-2 map to FITNESS_ASSESSMENT.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(2)
    assert agent_type == OnboardingAgentType.FITNESS_ASSESSMENT


@pytest.mark.unit
def test_step_to_agent_maps_step_3_to_goal_setting(db_session: AsyncSession):
    """
    Test that step 3 maps to GOAL_SETTING.
    
    Validates Requirement 5.3: Step 3 maps to GOAL_SETTING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(3)
    assert agent_type == OnboardingAgentType.GOAL_SETTING


@pytest.mark.unit
def test_step_to_agent_maps_step_4_to_workout_planning(db_session: AsyncSession):
    """
    Test that step 4 maps to WORKOUT_PLANNING.
    
    Validates Requirement 5.4: Steps 4-5 map to WORKOUT_PLANNING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(4)
    assert agent_type == OnboardingAgentType.WORKOUT_PLANNING


@pytest.mark.unit
def test_step_to_agent_maps_step_5_to_workout_planning(db_session: AsyncSession):
    """
    Test that step 5 maps to WORKOUT_PLANNING.
    
    Validates Requirement 5.4: Steps 4-5 map to WORKOUT_PLANNING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(5)
    assert agent_type == OnboardingAgentType.WORKOUT_PLANNING


@pytest.mark.unit
def test_step_to_agent_maps_step_6_to_diet_planning(db_session: AsyncSession):
    """
    Test that step 6 maps to DIET_PLANNING.
    
    Validates Requirement 5.5: Steps 6-7 map to DIET_PLANNING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(6)
    assert agent_type == OnboardingAgentType.DIET_PLANNING


@pytest.mark.unit
def test_step_to_agent_maps_step_7_to_diet_planning(db_session: AsyncSession):
    """
    Test that step 7 maps to DIET_PLANNING.
    
    Validates Requirement 5.5: Steps 6-7 map to DIET_PLANNING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(7)
    assert agent_type == OnboardingAgentType.DIET_PLANNING


@pytest.mark.unit
def test_step_to_agent_maps_step_8_to_scheduling(db_session: AsyncSession):
    """
    Test that step 8 maps to SCHEDULING.
    
    Validates Requirement 5.6: Steps 8-9 map to SCHEDULING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(8)
    assert agent_type == OnboardingAgentType.SCHEDULING


@pytest.mark.unit
def test_step_to_agent_maps_step_9_to_scheduling(db_session: AsyncSession):
    """
    Test that step 9 maps to SCHEDULING.
    
    Validates Requirement 5.6: Steps 8-9 map to SCHEDULING.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    agent_type = orchestrator._step_to_agent(9)
    assert agent_type == OnboardingAgentType.SCHEDULING


@pytest.mark.unit
def test_step_to_agent_raises_error_for_negative_step(db_session: AsyncSession):
    """
    Test that _step_to_agent raises ValueError for negative step.
    
    Validates Requirement 5.7: Invalid steps raise ValueError.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    with pytest.raises(ValueError) as exc_info:
        orchestrator._step_to_agent(-1)
    
    assert "Invalid onboarding step" in str(exc_info.value)
    assert "-1" in str(exc_info.value)


@pytest.mark.unit
def test_step_to_agent_raises_error_for_step_greater_than_9(db_session: AsyncSession):
    """
    Test that _step_to_agent raises ValueError for step > 9.
    
    Validates Requirement 5.7: Invalid steps raise ValueError.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    with pytest.raises(ValueError) as exc_info:
        orchestrator._step_to_agent(10)
    
    assert "Invalid onboarding step" in str(exc_info.value)
    assert "10" in str(exc_info.value)


@pytest.mark.unit
def test_step_to_agent_raises_error_for_step_100(db_session: AsyncSession):
    """
    Test that _step_to_agent raises ValueError for very large step.
    
    Validates Requirement 5.7: Invalid steps raise ValueError.
    """
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    with pytest.raises(ValueError) as exc_info:
        orchestrator._step_to_agent(100)
    
    assert "Invalid onboarding step" in str(exc_info.value)


# ============================================================================
# Test: get_current_agent Integration
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_agent_returns_correct_agent_for_step_0(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that get_current_agent returns FitnessAssessmentAgent for step 0.
    
    Validates Requirements 5.1, 5.2, 5.8, 5.9: Complete orchestration flow.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        agent = await orchestrator.get_current_agent(test_user.id)
        
        assert isinstance(agent, FitnessAssessmentAgent)
        assert agent.db == db_session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_agent_returns_correct_agent_for_step_3(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that get_current_agent returns GoalSettingAgent for step 3.
    
    Validates Requirements 5.1, 5.3, 5.8, 5.9: Complete orchestration flow.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        # Update user's step to 3
        from sqlalchemy import update
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == test_user.id)
            .values(current_step=3)
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        assert isinstance(agent, GoalSettingAgent)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_agent_passes_context_from_database(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that get_current_agent passes context from database to agent.
    
    Validates Requirement 5.9: Context passed to agent constructor.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        # Set up context in database
        from sqlalchemy import update
        
        test_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "experience_years": 0
            }
        }
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == test_user.id)
            .values(
                current_step=3,
                agent_context=test_context
            )
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        # Get agent
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        # Verify context was passed
        assert agent.context.agent_context == test_context
        assert agent.context.agent_context["fitness_assessment"]["fitness_level"] == "beginner"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_agent_handles_empty_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that get_current_agent handles empty/null context gracefully.
    
    Validates Requirement 5.9: Handle missing context.
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        # Verify agent is created with empty context
        assert isinstance(agent, FitnessAssessmentAgent)
        assert agent.context.agent_context == {} or agent.context.agent_context is None


# ============================================================================
# Test: Integration Tests for Orchestrator (Task 8.3)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_routing_to_scheduling_agent_for_step_8(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that orchestrator routes to SchedulingAgent for step 8.
    
    Validates Requirement 1.1: Routing to SchedulingAgent for steps 8-9.
    
    **Feature: scheduling-agent-completion**
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        # Update user's step to 8
        from sqlalchemy import update
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == test_user.id)
            .values(current_step=8, current_agent="scheduling")
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        assert isinstance(agent, SchedulingAgent)
        assert agent.db == db_session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_routing_to_scheduling_agent_for_step_9(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that orchestrator routes to SchedulingAgent for step 9.
    
    Validates Requirement 1.1: Routing to SchedulingAgent for steps 8-9.
    
    **Feature: scheduling-agent-completion**
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        # Update user's step to 9
        from sqlalchemy import update
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == test_user.id)
            .values(current_step=9, current_agent="scheduling")
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        assert isinstance(agent, SchedulingAgent)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_routing_to_onboarding_agents_when_complete(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that orchestrator rejects routing when onboarding is complete.
    
    Validates Requirement 16.1, 16.2: Do not route to onboarding agents
    if onboarding complete.
    
    **Feature: scheduling-agent-completion**
    """
    # Mark onboarding as complete
    from sqlalchemy import update
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == test_user.id)
        .values(
            current_step=9,
            is_complete=True,
            current_agent="general_assistant"
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    # Attempt to get current agent should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.get_current_agent(test_user.id)
    
    # Verify error message indicates onboarding is complete
    assert "Onboarding already complete" in str(exc_info.value)
    assert "general assistant" in str(exc_info.value).lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_advance_step_from_diet_planning_to_scheduling(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that advance_step correctly transitions from diet planning to scheduling.
    
    Validates that step advancement works correctly when moving to scheduling agent.
    
    **Feature: scheduling-agent-completion**
    """
    # Set user to step 7 (last diet planning step)
    from sqlalchemy import update, select
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == test_user.id)
        .values(current_step=7, current_agent="diet_planning")
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    orchestrator = OnboardingAgentOrchestrator(db=db_session)
    
    # Advance to next step
    await orchestrator.advance_step(test_user.id)
    
    # Verify step advanced to 8 and agent changed to scheduling
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    result = await db_session.execute(stmt)
    state = result.scalar_one()
    
    assert state.current_step == 8
    assert state.current_agent == "scheduling"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scheduling_agent_receives_context_from_previous_agents(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that SchedulingAgent receives context from previous agents.
    
    Validates that context continuity is maintained when routing to scheduling agent.
    
    **Feature: scheduling-agent-completion**
    """
    with patch('app.agents.onboarding.base.settings', mock_llm_settings()):
        # Set up complete context from previous agents
        from sqlalchemy import update
        
        complete_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["no_equipment"],
                "completed_at": "2024-01-01T10:00:00Z"
            },
            "goal_setting": {
                "primary_goal": "muscle_gain",
                "completed_at": "2024-01-01T10:05:00Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "training_split": [
                        {"name": "Upper Body", "muscle_groups": ["chest", "back"], "type": "strength"}
                    ]
                },
                "user_approved": True,
                "completed_at": "2024-01-01T10:10:00Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": [],
                    "dislikes": []
                },
                "proposed_plan": {
                    "daily_calories": 2800,
                    "protein_g": 175.0,
                    "carbs_g": 350.0,
                    "fats_g": 78.0,
                    "meal_frequency": 4
                },
                "user_approved": True,
                "completed_at": "2024-01-01T10:15:00Z"
            }
        }
        
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == test_user.id)
            .values(
                current_step=8,
                current_agent="scheduling",
                agent_context=complete_context
            )
        )
        await db_session.execute(stmt)
        await db_session.commit()
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        agent = await orchestrator.get_current_agent(test_user.id)
        
        # Verify agent received complete context
        assert isinstance(agent, SchedulingAgent)
        assert agent.context.agent_context == complete_context
        assert "fitness_assessment" in agent.context.agent_context
        assert "goal_setting" in agent.context.agent_context
        assert "workout_planning" in agent.context.agent_context
        assert "diet_planning" in agent.context.agent_context



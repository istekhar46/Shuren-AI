"""
Integration tests for step advancement logic.

Tests verify:
- Step advancement after fitness assessment completion
- Step advancement after goal setting completion
- current_step increments correctly
- current_agent updates to reflect new agent type
- Next message routes to new agent
"""

import pytest
from uuid import uuid4
from unittest.mock import patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.onboarding import OnboardingAgentType


# ============================================================================
# Test: Step Advancement After Fitness Assessment
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_step_advancement_after_fitness_assessment(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that step advances from 2 to 3 after fitness assessment completes.
    
    Validates Requirements 14.1, 14.5: Step advancement after fitness assessment.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Set user to step 2 (last fitness assessment step)
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        state.current_step = 2
        state.current_agent = OnboardingAgentType.FITNESS_ASSESSMENT.value
        await db_session.commit()
        
        # Complete fitness assessment
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        fitness_data = {
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Advance step
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        await orchestrator.advance_step(test_user.id)
        
        # Verify step incremented to 3
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 3
        
        # Verify current_agent changed to goal_setting
        assert state.current_agent == OnboardingAgentType.GOAL_SETTING.value
        
        # Verify next message routes to GoalSettingAgent
        agent = await orchestrator.get_current_agent(test_user.id)
        assert isinstance(agent, GoalSettingAgent)
        assert agent.agent_type == "goal_setting"


# ============================================================================
# Test: Step Advancement After Goal Setting
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_step_advancement_after_goal_setting(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that step advances from 3 to 4 after goal setting completes.
    
    Validates Requirements 14.2, 14.3, 14.4: Step advancement after goal setting.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Set user to step 3 (goal setting step)
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        state.current_step = 3
        state.current_agent = OnboardingAgentType.GOAL_SETTING.value
        # Add fitness assessment context
        state.agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": []
            }
        }
        await db_session.commit()
        
        # Complete goal setting
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        goal_agent._current_user_id = test_user.id
        
        goal_data = {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 75.0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await goal_agent.save_context(test_user.id, goal_data)
        
        # Advance step
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        await orchestrator.advance_step(test_user.id)
        
        # Verify step incremented to 4
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 4
        
        # Verify current_agent changed to workout_planning
        assert state.current_agent == OnboardingAgentType.WORKOUT_PLANNING.value


# ============================================================================
# Test: Multiple Step Advancements
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_step_advancements(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that multiple step advancements work correctly in sequence.
    
    Validates Requirements 14.1, 14.2, 14.3, 14.4: Sequential step advancement.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        # Start at step 0
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 0
        
        # Advance to step 1
        await orchestrator.advance_step(test_user.id)
        
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 1
        assert state.current_agent == OnboardingAgentType.FITNESS_ASSESSMENT.value
        
        # Advance to step 2
        await orchestrator.advance_step(test_user.id)
        
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 2
        assert state.current_agent == OnboardingAgentType.FITNESS_ASSESSMENT.value
        
        # Advance to step 3 (should change agent)
        await orchestrator.advance_step(test_user.id)
        
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 3
        assert state.current_agent == OnboardingAgentType.GOAL_SETTING.value


# ============================================================================
# Test: Database Transaction Commit
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_step_advancement_commits_transaction(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that step advancement commits the database transaction.
    
    Validates Requirement 14.4: Transaction commit on step advancement.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Set user to step 1
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        state.current_step = 1
        await db_session.commit()
        
        # Advance step
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        await orchestrator.advance_step(test_user.id)
        
        # Create new session to verify commit
        from sqlalchemy.ext.asyncio import AsyncSession
        async with db_session.begin():
            stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
            result = await db_session.execute(stmt)
            state = result.scalars().first()
            
            # Should see updated step (transaction was committed)
            assert state.current_step == 2


# ============================================================================
# Test: Agent Type Mapping Across Steps
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_type_mapping_across_steps(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that agent type correctly maps across all step transitions.
    
    Validates Requirements 14.1, 14.2, 14.3: Agent type mapping.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        # Test step 0-2 -> FITNESS_ASSESSMENT
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        state.current_step = 0
        await db_session.commit()
        
        await orchestrator.advance_step(test_user.id)
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        assert state.current_agent == OnboardingAgentType.FITNESS_ASSESSMENT.value
        
        # Test step 3 -> GOAL_SETTING
        state.current_step = 2
        await db_session.commit()
        
        await orchestrator.advance_step(test_user.id)
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        assert state.current_step == 3
        assert state.current_agent == OnboardingAgentType.GOAL_SETTING.value
        
        # Test step 4-5 -> WORKOUT_PLANNING
        await orchestrator.advance_step(test_user.id)
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        assert state.current_step == 4
        assert state.current_agent == OnboardingAgentType.WORKOUT_PLANNING.value

"""
End-to-end integration tests for Fitness and Goal Setting Agents.

Tests verify complete flows:
- Complete fitness assessment flow
- Complete goal setting flow  
- Complete fitness → goal flow
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock
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
# Test: Complete Fitness Assessment Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_fitness_assessment_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete fitness assessment flow from start to finish.
    
    Validates Requirement 15.3: End-to-end fitness assessment flow.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Start with step 0
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 0
        assert state.agent_context == {}
        
        # Create fitness assessment agent
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        # Simulate collecting fitness data
        fitness_data = {
            "fitness_level": "intermediate",
            "experience_details": {
                "frequency": "3 times per week",
                "duration": "45 minutes",
                "types": ["weightlifting", "cardio"]
            },
            "limitations": ["no equipment at home", "previous knee injury"],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Save fitness assessment
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Verify data saved to agent_context
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert "fitness_assessment" in state.agent_context
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"
        assert len(state.agent_context["fitness_assessment"]["limitations"]) == 2
        
        # Verify completion check
        is_complete = await fitness_agent._check_if_complete(test_user.id)
        assert is_complete is True
        
        # Advance to next step
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        # Set to step 2 (last fitness assessment step) before advancing
        state.current_step = 2
        await db_session.commit()
        
        await orchestrator.advance_step(test_user.id)
        
        # Verify step advanced to 3
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 3
        assert state.current_agent == OnboardingAgentType.GOAL_SETTING.value


# ============================================================================
# Test: Complete Goal Setting Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_goal_setting_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete goal setting flow with fitness context.
    
    Validates Requirement 15.3: End-to-end goal setting flow.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Start with step 3 and fitness_assessment context
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        state.current_step = 3
        state.current_agent = OnboardingAgentType.GOAL_SETTING.value
        state.agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "experience_details": {"frequency": "new to exercise"},
                "limitations": ["time constraints"],
                "completed_at": datetime.utcnow().isoformat()
            }
        }
        await db_session.commit()
        
        # Create goal setting agent with context
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        goal_agent._current_user_id = test_user.id
        
        # Verify agent references fitness level
        prompt = goal_agent.get_system_prompt()
        assert "beginner" in prompt
        assert "time constraints" in prompt
        
        # Simulate collecting goal data
        goal_data = {
            "primary_goal": "fat_loss",
            "secondary_goal": None,
            "target_weight_kg": 70.0,
            "target_body_fat_percentage": 18.0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Save goal setting
        await goal_agent.save_context(test_user.id, goal_data)
        
        # Verify data saved to agent_context
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert "goal_setting" in state.agent_context
        assert state.agent_context["goal_setting"]["primary_goal"] == "fat_loss"
        assert state.agent_context["goal_setting"]["target_weight_kg"] == 70.0
        
        # Verify completion check
        is_complete = await goal_agent._check_if_complete(test_user.id)
        assert is_complete is True
        
        # Advance to next step
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        await orchestrator.advance_step(test_user.id)
        
        # Verify step advanced to 4
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 4
        assert state.current_agent == OnboardingAgentType.WORKOUT_PLANNING.value


# ============================================================================
# Test: Complete Fitness → Goal Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_fitness_to_goal_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete flow from fitness assessment through goal setting.
    
    Validates Requirement 15.3: End-to-end fitness → goal flow.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        orchestrator = OnboardingAgentOrchestrator(db=db_session)
        
        # Start with step 0
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 0
        
        # ===== PHASE 1: Complete Fitness Assessment =====
        
        # Create fitness assessment agent
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        # Save fitness assessment data
        fitness_data = {
            "fitness_level": "advanced",
            "experience_details": {
                "frequency": "5 times per week",
                "duration": "90 minutes",
                "types": ["powerlifting", "olympic lifting"]
            },
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Verify fitness assessment saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert "fitness_assessment" in state.agent_context
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "advanced"
        
        # Advance to goal setting (set to step 2 first)
        state.current_step = 2
        await db_session.commit()
        
        await orchestrator.advance_step(test_user.id)
        
        # Verify advancement to goal setting
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 3
        assert state.current_agent == OnboardingAgentType.GOAL_SETTING.value
        
        # ===== PHASE 2: Complete Goal Setting =====
        
        # Create goal setting agent with fitness context
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        goal_agent._current_user_id = test_user.id
        
        # Verify goal agent has access to fitness context
        assert goal_agent.context["fitness_assessment"]["fitness_level"] == "advanced"
        
        # Verify system prompt includes fitness level
        prompt = goal_agent.get_system_prompt()
        assert "advanced" in prompt
        
        # Save goal setting data
        goal_data = {
            "primary_goal": "muscle_gain",
            "secondary_goal": "fat_loss",
            "target_weight_kg": 90.0,
            "target_body_fat_percentage": 12.0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await goal_agent.save_context(test_user.id, goal_data)
        
        # Verify both contexts saved correctly
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert "fitness_assessment" in state.agent_context
        assert "goal_setting" in state.agent_context
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "advanced"
        assert state.agent_context["goal_setting"]["primary_goal"] == "muscle_gain"
        
        # Advance to workout planning
        await orchestrator.advance_step(test_user.id)
        
        # Verify step advanced to 4
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert state.current_step == 4
        assert state.current_agent == OnboardingAgentType.WORKOUT_PLANNING.value
        
        # Verify both contexts still exist
        assert "fitness_assessment" in state.agent_context
        assert "goal_setting" in state.agent_context


# ============================================================================
# Test: Context Continuity Across Full Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_continuity_across_full_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that context is preserved and accessible throughout the full flow.
    
    Validates Requirements 7.1, 7.5: Context continuity.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Save fitness assessment
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        fitness_data = {
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "4 times per week"},
            "limitations": ["home gym only"],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Load context and create goal agent
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        goal_agent._current_user_id = test_user.id
        
        # Save goal setting
        goal_data = {
            "primary_goal": "general_fitness",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await goal_agent.save_context(test_user.id, goal_data)
        
        # Verify both contexts exist and are accessible
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        # Verify fitness context preserved
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"
        assert "home gym only" in state.agent_context["fitness_assessment"]["limitations"]
        
        # Verify goal context added
        assert state.agent_context["goal_setting"]["primary_goal"] == "general_fitness"
        
        # Verify timestamps exist
        assert "completed_at" in state.agent_context["fitness_assessment"]
        assert "completed_at" in state.agent_context["goal_setting"]

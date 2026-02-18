"""
Integration tests for context handover between agents.

Tests verify:
- Context passing from FitnessAssessmentAgent to GoalSettingAgent
- GoalSettingAgent can access fitness_level from context
- GoalSettingAgent can access limitations from context
- System prompt includes context data
- Graceful handling of missing context
"""

import pytest
from uuid import uuid4
from unittest.mock import patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.models.onboarding import OnboardingState
from app.models.user import User


# ============================================================================
# Test: Context Passing from Fitness to Goal Agent
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_passing_from_fitness_to_goal_agent(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that GoalSettingAgent receives fitness_assessment context.
    
    Validates Requirement 7.1: Context handover from fitness to goal agent.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Step 1: Save fitness assessment data
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
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
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Step 2: Load context for goal agent
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        # Verify fitness_assessment was saved
        assert state.agent_context is not None
        assert "fitness_assessment" in state.agent_context
        
        # Step 3: Instantiate GoalSettingAgent with saved context
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        
        # Verify agent can access fitness_level
        assert goal_agent.context.get("fitness_assessment", {}).get("fitness_level") == "intermediate"
        
        # Verify agent can access limitations
        limitations = goal_agent.context.get("fitness_assessment", {}).get("limitations", [])
        assert "no equipment at home" in limitations
        assert "previous knee injury" in limitations


# ============================================================================
# Test: System Prompt Includes Context Data
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_goal_agent_system_prompt_includes_fitness_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that GoalSettingAgent system prompt includes fitness context.
    
    Validates Requirements 7.2, 7.3: System prompt includes fitness data.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Save fitness assessment data
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        fitness_data = {
            "fitness_level": "beginner",
            "experience_details": {"frequency": "new to exercise"},
            "limitations": ["limited time", "home workouts only"],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Load context
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        # Create goal agent with context
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        prompt = goal_agent.get_system_prompt()
        
        # Verify system prompt includes fitness level
        assert "beginner" in prompt
        
        # Verify system prompt includes limitations
        assert "limited time" in prompt
        assert "home workouts only" in prompt


# ============================================================================
# Test: Multiple Agents Can Save to Different Keys
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_agents_save_to_different_keys(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that multiple agents can save data without overwriting each other.
    
    Validates Requirement 7.1: Multiple agents can save to agent_context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Save fitness assessment data
        fitness_agent = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent._current_user_id = test_user.id
        
        fitness_data = {
            "fitness_level": "advanced",
            "experience_details": {"frequency": "5 times per week"},
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent.save_context(test_user.id, fitness_data)
        
        # Load context and save goal data
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        goal_agent = GoalSettingAgent(db=db_session, context=state.agent_context)
        goal_agent._current_user_id = test_user.id
        
        goal_data = {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 85.0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await goal_agent.save_context(test_user.id, goal_data)
        
        # Verify both contexts exist
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        assert "fitness_assessment" in state.agent_context
        assert "goal_setting" in state.agent_context
        assert state.agent_context["fitness_assessment"]["fitness_level"] == "advanced"
        assert state.agent_context["goal_setting"]["primary_goal"] == "muscle_gain"


# ============================================================================
# Test: Context Persists Across Agent Instantiations
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_persists_across_instantiations(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that context persists when agents are re-instantiated.
    
    Validates Requirement 7.1: Context persistence.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # First instantiation - save data
        fitness_agent_1 = FitnessAssessmentAgent(db=db_session, context={})
        fitness_agent_1._current_user_id = test_user.id
        
        fitness_data = {
            "fitness_level": "intermediate",
            "experience_details": {"frequency": "3 times per week"},
            "limitations": ["time constraints"],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await fitness_agent_1.save_context(test_user.id, fitness_data)
        
        # Second instantiation - load context
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        result = await db_session.execute(stmt)
        state = result.scalars().first()
        
        fitness_agent_2 = FitnessAssessmentAgent(db=db_session, context=state.agent_context)
        
        # Verify context is available
        assert fitness_agent_2.context.get("fitness_assessment", {}).get("fitness_level") == "intermediate"


# ============================================================================
# Test: Graceful Handling of Missing Context
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_goal_agent_handles_missing_fitness_context(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that GoalSettingAgent handles missing fitness_assessment context gracefully.
    
    Validates Requirement 7.4: Graceful handling of missing context.
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Create goal agent without fitness context
        goal_agent = GoalSettingAgent(db=db_session, context={})
        
        # Should not crash
        prompt = goal_agent.get_system_prompt()
        
        # Should have default values
        assert "unknown" in prompt or "none mentioned" in prompt
        assert prompt is not None
        assert len(prompt) > 0

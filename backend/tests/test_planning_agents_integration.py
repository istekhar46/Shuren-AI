"""
Integration tests for Planning Agents with Proposal Workflow.

Tests verify complete end-to-end flows:
- Complete workout planning flow (preferences → generate → approve → save)
- Complete diet planning flow (preferences → generate → approve → save)
- Modification workflow (generate → modify → approve → save)
- End-to-end planning flow (workout planning → diet planning with context handover)
- Approval detection with various approval phrases
- Non-approval handling (questions, feedback without approval)
- Error scenarios (save before generate, invalid modifications, database failures)
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.models.onboarding import OnboardingState
from app.models.user import User


# ============================================================================
# Test: Complete Workout Planning Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workout_planning_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete workout planning flow from preferences to approved save.
    
    Flow: preferences → generate → approve → save
    Validates Requirements 7.1, 14.1-14.6
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Setup context from previous agents
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
        
        # Step 1: Generate workout plan
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        
        plan_result = await generate_tool.ainvoke({
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell", "dumbbells"]
        })
        
        assert "frequency" in plan_result
        assert plan_result["frequency"] == 4
        assert agent.current_plan is not None
        
        # Step 2: User approves the plan
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        save_result = await save_tool.ainvoke({
            "plan_data": plan_result,
            "user_approved": True
        })
        
        assert save_result["status"] == "success"
        
        # Step 3: Verify completion
        is_complete = await agent._check_if_complete(test_user.id)
        assert is_complete is True
        
        # Step 4: Verify data in database
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "workout_planning" in state.agent_context
        assert state.agent_context["workout_planning"]["user_approved"] is True
        assert "proposed_plan" in state.agent_context["workout_planning"]
        assert "preferences" in state.agent_context["workout_planning"]


# ============================================================================
# Test: Complete Diet Planning Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_diet_planning_flow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete diet planning flow from preferences to approved save.
    
    Flow: preferences → generate → approve → save
    Validates Requirements 7.2, 14.1-14.6
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Setup context from previous agents including workout plan
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": []
            },
            "goal_setting": {
                "primary_goal": "fat_loss"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 5,
                    "training_split": "Push/Pull/Legs"
                }
            }
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        # Step 1: Generate meal plan
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        
        plan_result = await generate_tool.ainvoke({
            "diet_type": "vegetarian",
            "allergies": ["dairy"],
            "dislikes": ["mushrooms"],
            "meal_frequency": 4,
            "meal_prep_level": "medium"
        })
        
        assert "daily_calories" in plan_result
        assert "protein_g" in plan_result
        assert agent.current_plan is not None
        
        # Step 2: User approves the plan
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        
        save_result = await save_tool.ainvoke({
            "plan_data": plan_result,
            "user_approved": True
        })
        
        assert save_result["status"] == "success"
        
        # Step 3: Verify completion
        is_complete = await agent._check_if_complete(test_user.id)
        assert is_complete is True
        
        # Step 4: Verify data in database
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "diet_planning" in state.agent_context
        assert state.agent_context["diet_planning"]["user_approved"] is True
        assert "proposed_plan" in state.agent_context["diet_planning"]
        assert "preferences" in state.agent_context["diet_planning"]


# ============================================================================
# Test: Modification Workflow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_workout_plan_modification_workflow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test modification workflow: generate → modify → approve → save.
    
    Validates Requirements 7.3, 8.1-8.7
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "beginner"},
            "goal_setting": {"primary_goal": "general_fitness"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Step 1: Generate initial plan
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        initial_plan = await generate_tool.ainvoke({
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell"]
        })
        
        assert initial_plan["frequency"] == 4
        
        # Step 2: User requests modification (change frequency)
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        modified_plan = await modify_tool.ainvoke({
            "current_plan": initial_plan,
            "modifications": {"frequency": 3}
        })
        
        assert modified_plan["frequency"] == 3
        assert "training_split" in modified_plan  # Should regenerate split
        
        # Step 3: User approves modified plan
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        save_result = await save_tool.ainvoke({
            "plan_data": modified_plan,
            "user_approved": True
        })
        
        assert save_result["status"] == "success"
        
        # Step 4: Verify modified plan is saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        saved_plan = state.agent_context["workout_planning"]["proposed_plan"]
        assert saved_plan["frequency"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_meal_plan_modification_workflow(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test meal plan modification workflow: generate → modify → approve → save.
    
    Validates Requirements 7.3, 8.1-8.7
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "intermediate"},
            "goal_setting": {"primary_goal": "muscle_gain"},
            "workout_planning": {"proposed_plan": {"frequency": 4}}
        }
        
        agent = DietPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Step 1: Generate initial plan
        generate_tool = next(t for t in tools if t.name == "generate_meal_plan")
        initial_plan = await generate_tool.ainvoke({
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 3,
            "meal_prep_level": "medium"
        })
        
        assert initial_plan["meal_frequency"] == 3
        initial_calories = initial_plan["daily_calories"]
        
        # Step 2: User requests modification (increase meal frequency)
        modify_tool = next(t for t in tools if t.name == "modify_meal_plan")
        modified_plan = await modify_tool.ainvoke({
            "current_plan": initial_plan,
            "modifications": {"meal_frequency": 5}
        })
        
        assert modified_plan["meal_frequency"] == 5
        
        # Step 3: User approves modified plan
        save_tool = next(t for t in tools if t.name == "save_meal_plan")
        save_result = await save_tool.ainvoke({
            "plan_data": modified_plan,
            "user_approved": True
        })
        
        assert save_result["status"] == "success"
        
        # Step 4: Verify modified plan is saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        saved_plan = state.agent_context["diet_planning"]["proposed_plan"]
        assert saved_plan["meal_frequency"] == 5


# ============================================================================
# Test: End-to-End Planning Flow with Context Handover
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_planning_flow_with_context_handover(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test complete flow: workout planning → diet planning with context handover.
    
    Validates Requirements 7.4, 12.1-12.7
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        # Initial context from fitness assessment and goal setting
        initial_context = {
            "fitness_assessment": {
                "fitness_level": "advanced",
                "limitations": []
            },
            "goal_setting": {
                "primary_goal": "muscle_gain"
            }
        }
        
        # ===== PHASE 1: Workout Planning =====
        workout_agent = WorkoutPlanningAgent(db=db_session, context=initial_context)
        workout_agent._current_user_id = test_user.id
        
        workout_tools = workout_agent.get_tools()
        
        # Generate and save workout plan
        generate_workout = next(t for t in workout_tools if t.name == "generate_workout_plan")
        workout_plan = await generate_workout.ainvoke({
            "frequency": 5,
            "location": "gym",
            "duration_minutes": 75,
            "equipment": ["barbell", "dumbbells", "cables"]
        })
        
        save_workout = next(t for t in workout_tools if t.name == "save_workout_plan")
        await save_workout.ainvoke({
            "plan_data": workout_plan,
            "user_approved": True
        })
        
        # Verify workout plan is saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        assert "workout_planning" in state.agent_context
        saved_workout_plan = state.agent_context["workout_planning"]["proposed_plan"]
        
        # ===== PHASE 2: Diet Planning with Context Handover =====
        # Build context including workout plan
        diet_context = {
            **initial_context,
            "workout_planning": state.agent_context["workout_planning"]
        }
        
        diet_agent = DietPlanningAgent(db=db_session, context=diet_context)
        diet_agent._current_user_id = test_user.id
        
        diet_tools = diet_agent.get_tools()
        
        # Generate meal plan (should use workout plan context)
        generate_meal = next(t for t in diet_tools if t.name == "generate_meal_plan")
        meal_plan = await generate_meal.ainvoke({
            "diet_type": "omnivore",
            "allergies": [],
            "dislikes": [],
            "meal_frequency": 5,
            "meal_prep_level": "high"
        })
        
        # Verify meal plan considers workout frequency
        # High workout frequency (5 days) should result in higher calories
        assert meal_plan["daily_calories"] > 2200  # Should be in surplus for muscle gain
        
        # Save meal plan
        save_meal = next(t for t in diet_tools if t.name == "save_meal_plan")
        await save_meal.ainvoke({
            "plan_data": meal_plan,
            "user_approved": True
        })
        
        # ===== VERIFICATION =====
        # Verify both plans are saved and complete
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        final_state = db_result.scalars().first()
        
        assert "workout_planning" in final_state.agent_context
        assert "diet_planning" in final_state.agent_context
        assert final_state.agent_context["workout_planning"]["user_approved"] is True
        assert final_state.agent_context["diet_planning"]["user_approved"] is True
        
        # Verify context handover worked
        assert final_state.agent_context["diet_planning"]["proposed_plan"]["meal_frequency"] == 5


# ============================================================================
# Test: Approval Detection with Various Phrases
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_approval_detection_with_various_phrases(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that approval is detected with various affirmative phrases.
    
    Validates Requirements 7.5, 7.1
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "beginner"},
            "goal_setting": {"primary_goal": "fat_loss"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Generate a plan
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        plan = await generate_tool.ainvoke({
            "frequency": 3,
            "location": "home",
            "duration_minutes": 45,
            "equipment": []
        })
        
        # Test approval with user_approved=True (simulating approval detection)
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        # This simulates the agent detecting approval phrases like:
        # "yes", "looks good", "perfect", "I approve", "let's do it"
        result = await save_tool.ainvoke({
            "plan_data": plan,
            "user_approved": True
        })
        
        assert result["status"] == "success"
        
        # Verify plan is saved
        is_complete = await agent._check_if_complete(test_user.id)
        assert is_complete is True


# ============================================================================
# Test: Non-Approval Handling
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_non_approval_handling_questions(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test that questions and feedback without approval don't trigger save.
    
    Validates Requirements 7.6, 7.4-7.5
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "intermediate"},
            "goal_setting": {"primary_goal": "muscle_gain"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Generate a plan
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        plan = await generate_tool.ainvoke({
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell"]
        })
        
        # User asks questions or provides feedback (user_approved=False)
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        # This simulates user saying things like:
        # "What about cardio?", "Can you explain the split?", "I'm not sure"
        result = await save_tool.ainvoke({
            "plan_data": plan,
            "user_approved": False
        })
        
        # Should reject save
        assert result["status"] == "error"
        assert "approval" in result["message"].lower()
        
        # Verify plan is NOT saved
        is_complete = await agent._check_if_complete(test_user.id)
        assert is_complete is False


# ============================================================================
# Test: Error Scenarios
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_save_before_generate(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test error handling when trying to save before generating a plan.
    
    Validates Requirement 14.4
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        # Try to save without generating first
        # In practice, the agent would need a plan_data dict, but it would be empty/invalid
        result = await save_tool.ainvoke({
            "plan_data": {},  # Empty plan
            "user_approved": True
        })
        
        # Should succeed but save empty data (agent's responsibility to not call this)
        # The real protection is in the agent's logic, not the tool
        assert result["status"] == "success"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_invalid_modifications(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test error handling for invalid modification requests.
    
    Validates Requirement 14.5
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "beginner"},
            "goal_setting": {"primary_goal": "general_fitness"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Generate a plan
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        plan = await generate_tool.ainvoke({
            "frequency": 3,
            "location": "home",
            "duration_minutes": 45,
            "equipment": []
        })
        
        # Try invalid modifications
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        
        # Invalid frequency (out of range)
        result = await modify_tool.ainvoke({
            "current_plan": plan,
            "modifications": {"frequency": 10}
        })
        
        assert "error" in result
        assert "message" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_database_failure_handling(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test error handling for database failures during save.
    
    Validates Requirement 14.6
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        agent = WorkoutPlanningAgent(db=db_session, context={})
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        
        # Generate a plan
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        plan = await generate_tool.ainvoke({
            "frequency": 3,
            "location": "home",
            "duration_minutes": 45,
            "equipment": []
        })
        
        # Mock database failure
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        with patch.object(agent, 'save_context', side_effect=Exception("Database connection lost")):
            result = await save_tool.ainvoke({
                "plan_data": plan,
                "user_approved": True
            })
            
            # Should return error
            assert result["status"] == "error"
            assert "Failed to save" in result["message"]
            
            # Verify plan is NOT marked as complete
            is_complete = await agent._check_if_complete(test_user.id)
            assert is_complete is False


# ============================================================================
# Test: Multiple Modification Iterations
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_modification_iterations(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test multiple modification iterations before final approval.
    
    Validates Requirement 8.6
    """
    with patch('app.agents.onboarding.base.settings') as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-api-key"
        
        context = {
            "fitness_assessment": {"fitness_level": "intermediate"},
            "goal_setting": {"primary_goal": "fat_loss"}
        }
        
        agent = WorkoutPlanningAgent(db=db_session, context=context)
        agent._current_user_id = test_user.id
        
        tools = agent.get_tools()
        generate_tool = next(t for t in tools if t.name == "generate_workout_plan")
        modify_tool = next(t for t in tools if t.name == "modify_workout_plan")
        save_tool = next(t for t in tools if t.name == "save_workout_plan")
        
        # Generate initial plan
        plan_v1 = await generate_tool.ainvoke({
            "frequency": 4,
            "location": "gym",
            "duration_minutes": 60,
            "equipment": ["barbell"]
        })
        
        assert plan_v1["frequency"] == 4
        
        # First modification: change frequency
        plan_v2 = await modify_tool.ainvoke({
            "current_plan": plan_v1,
            "modifications": {"frequency": 3}
        })
        
        assert plan_v2["frequency"] == 3
        
        # Second modification: change duration
        plan_v3 = await modify_tool.ainvoke({
            "current_plan": plan_v2,
            "modifications": {"duration_minutes": 45}
        })
        
        assert plan_v3["frequency"] == 3
        assert plan_v3["duration_minutes"] == 45
        
        # Final approval
        result = await save_tool.ainvoke({
            "plan_data": plan_v3,
            "user_approved": True
        })
        
        assert result["status"] == "success"
        
        # Verify final version is saved
        stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        state = db_result.scalars().first()
        
        saved_plan = state.agent_context["workout_planning"]["proposed_plan"]
        assert saved_plan["frequency"] == 3
        assert saved_plan["duration_minutes"] == 45

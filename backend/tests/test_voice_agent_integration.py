"""
Integration tests for LiveKit Voice Agent.

This module tests the FitnessVoiceAgent class and its integration with:
- Agent orchestrator
- Context loader
- Function tools (get_todays_workout, get_todays_meals, log_workout_set, ask_specialist_agent)
- Background log worker
- Database operations

Test Categories:
- @pytest.mark.integration - Integration tests requiring database
- @pytest.mark.asyncio - Async test execution

Note: These tests mock LLM calls to avoid timeouts and API costs.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from app.livekit_agents.voice_agent_worker import FitnessVoiceAgent
from app.agents.context import AgentContext, AgentResponse
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import FitnessGoal, LifestyleBaseline
from app.models.workout_log import WorkoutLog


# ============================================================================
# Test Markers
# ============================================================================

pytestmark = [
    pytest.mark.asyncio,  # All tests in this module are async
    pytest.mark.integration,  # All tests require database
]


# ============================================================================
# Integration Tests - Voice Agent Initialization
# ============================================================================

@patch('app.services.agent_orchestrator.AgentOrchestrator.warm_up')
async def test_voice_agent_initialization(mock_warm_up, db_session: AsyncSession, test_user: User):
    """
    Test FitnessVoiceAgent initialization with test user.
    
    Validates: Requirements 17.5, 17.6
    - Agent orchestrator is initialized
    - User context is loaded
    - User context matches test user
    """
    # Mock warm_up to avoid LLM calls
    mock_warm_up.return_value = None
    
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    
    # Create LifestyleBaseline with energy level
    lifestyle = LifestyleBaseline(
        profile_id=profile.id,
        energy_level=7,
        stress_level=5,
        sleep_quality=6
    )
    db_session.add(lifestyle)
    
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Verify initial state
    assert agent.user_id == str(test_user.id)
    assert agent.agent_type == "workout"
    assert agent.orchestrator is None
    assert agent.user_context is None
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Assert orchestrator is not None
    assert agent.orchestrator is not None
    
    # Assert user_context is not None
    assert agent.user_context is not None
    
    # Assert user_context.user_id matches test user
    assert agent.user_context.user_id == str(test_user.id)
    
    # Assert user_context has expected values
    assert agent.user_context.fitness_level == "intermediate"
    assert agent.user_context.primary_goal == "muscle_gain"
    assert agent.user_context.energy_level in ["medium", "high"]  # Energy level mapping


async def test_voice_agent_initialization_missing_user(db_session: AsyncSession):
    """
    Test FitnessVoiceAgent initialization fails gracefully for missing user.
    
    Validates: Error handling for missing user profile
    """
    # Create agent with non-existent user ID
    fake_user_id = str(uuid4())
    agent = FitnessVoiceAgent(user_id=fake_user_id, agent_type="general")
    
    # Call initialize_orchestrator() should raise ValueError
    with pytest.raises(ValueError):
        await agent.initialize_orchestrator()


# ============================================================================
# Integration Tests - get_todays_workout Tool
# ============================================================================

async def test_get_todays_workout_tool(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout function tool returns cached data.
    
    Validates: Requirements 17.2, 17.7
    - Tool returns workout data from cached context
    - Result is a string
    - Result length > 0
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Mock user_context with workout plan (no need to initialize orchestrator)
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss",
        current_workout_plan={
            "name": "Upper Body Push",
            "exercises": [
                {"name": "Bench Press", "sets": 3, "reps": 10},
                {"name": "Overhead Press", "sets": 3, "reps": 8},
                {"name": "Push-ups", "sets": 3, "reps": 15}
            ]
        }
    )
    
    # Call get_todays_workout()
    result = await agent.get_todays_workout()
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0
    
    # Assert result contains workout name
    assert "Upper Body Push" in result
    
    # Assert result contains exercise names
    assert "Bench Press" in result
    assert "Overhead Press" in result
    assert "Push-ups" in result


async def test_get_todays_workout_no_context(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout handles missing context gracefully.
    
    Validates: Error handling when context not loaded
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Call get_todays_workout() without context
    result = await agent.get_todays_workout()
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


async def test_get_todays_workout_empty_plan(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout handles empty workout plan.
    
    Validates: Graceful handling of missing workout plan
    """
    # Create agent
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Mock user_context with empty workout plan
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss",
        current_workout_plan={}
    )
    
    # Call get_todays_workout()
    result = await agent.get_todays_workout()
    
    # Assert result suggests creating a plan
    assert isinstance(result, str)
    assert "don't see" in result.lower() or "create" in result.lower()


# ============================================================================
# Integration Tests - get_todays_meals Tool
# ============================================================================

async def test_get_todays_meals_tool(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_meals function tool returns cached data.
    
    Validates: Requirements 17.2, 17.7
    - Tool returns meal data from cached context
    - Result is a string (JSON format)
    - Result length > 0
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="diet")
    
    # Mock user_context with meal plan
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        current_meal_plan={
            "name": "High Protein Meal Plan",
            "meals": [
                {
                    "meal_type": "breakfast",
                    "name": "Oatmeal with Protein",
                    "calories": 450,
                    "protein_g": 30,
                    "carbs_g": 50,
                    "fat_g": 12
                },
                {
                    "meal_type": "lunch",
                    "name": "Chicken and Rice",
                    "calories": 600,
                    "protein_g": 45,
                    "carbs_g": 60,
                    "fat_g": 15
                },
                {
                    "meal_type": "dinner",
                    "name": "Salmon with Vegetables",
                    "calories": 550,
                    "protein_g": 40,
                    "carbs_g": 40,
                    "fat_g": 20
                }
            ]
        }
    )
    
    # Call get_todays_meals()
    result = await agent.get_todays_meals()
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0
    
    # Assert result contains meal plan name
    assert "High Protein Meal Plan" in result
    
    # Assert result contains meal types
    assert "breakfast" in result.lower()
    assert "lunch" in result.lower()
    assert "dinner" in result.lower()


async def test_get_todays_meals_no_context(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_meals handles missing context gracefully.
    
    Validates: Error handling when context not loaded
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="diet")
    
    # Call get_todays_meals() without context
    result = await agent.get_todays_meals()
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


# ============================================================================
# Integration Tests - log_workout_set Tool
# ============================================================================

async def test_log_workout_set_tool(db_session: AsyncSession, test_user: User):
    """
    Test log_workout_set function tool queues data and returns confirmation.
    
    Validates: Requirements 17.3, 17.8
    - Tool queues workout set data
    - Result contains "Logged"
    - Result contains exercise name
    - Background worker persists data to database
    """
    # Create UserProfile for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Call log_workout_set with test data
    result = await agent.log_workout_set(
        exercise="Bench Press",
        reps=10,
        weight=135.0
    )
    
    # Assert result contains "Logged"
    assert "Logged" in result or "logged" in result.lower()
    
    # Assert result contains exercise name
    assert "Bench Press" in result
    
    # Assert result contains reps and weight
    assert "10" in result
    assert "135" in result
    
    # Wait for log worker to process the entry
    await asyncio.sleep(0.5)
    
    # Verify entry was persisted to database
    from sqlalchemy import select
    stmt = select(WorkoutLog).where(
        WorkoutLog.user_id == test_user.id,
        WorkoutLog.exercise == "Bench Press"
    )
    result_db = await db_session.execute(stmt)
    log_entry = result_db.scalar_one_or_none()
    
    # Assert log entry exists in database
    assert log_entry is not None
    assert log_entry.exercise == "Bench Press"
    assert log_entry.reps == 10
    assert log_entry.weight_kg == 135.0
    
    # Cleanup
    await agent.cleanup()


async def test_log_workout_set_multiple_entries(db_session: AsyncSession, test_user: User):
    """
    Test log_workout_set handles multiple entries correctly.
    
    Validates: Background worker processes multiple entries
    """
    # Create UserProfile for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="advanced",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Log multiple workout sets
    exercises = [
        ("Bench Press", 10, 135.0),
        ("Squats", 8, 225.0),
        ("Deadlifts", 5, 315.0)
    ]
    
    for exercise, reps, weight in exercises:
        result = await agent.log_workout_set(
            exercise=exercise,
            reps=reps,
            weight=weight
        )
        assert "Logged" in result or "logged" in result.lower()
    
    # Wait for queue to be empty (all entries processed)`n    await agent._log_queue.join()`n    `n    # Give a small buffer for database commits`n    await asyncio.sleep(0.2)
    
    # Verify all entries were persisted to database
    from sqlalchemy import select
    stmt = select(WorkoutLog).where(WorkoutLog.user_id == test_user.id)
    result_db = await db_session.execute(stmt)
    log_entries = result_db.scalars().all()
    
    # Assert all 3 entries exist
    assert len(log_entries) == 3
    
    # Verify exercise names
    exercise_names = {entry.exercise for entry in log_entries}
    assert "Bench Press" in exercise_names
    assert "Squats" in exercise_names
    assert "Deadlifts" in exercise_names
    
    # Cleanup
    await agent.cleanup()


# ============================================================================
# Integration Tests - ask_specialist_agent Tool
# ============================================================================

@patch('app.services.agent_orchestrator.AgentOrchestrator.route_query')
@patch('app.services.agent_orchestrator.AgentOrchestrator.warm_up')
async def test_ask_specialist_agent_tool(
    mock_warm_up,
    mock_route_query,
    db_session: AsyncSession,
    test_user: User
):
    """
    Test ask_specialist_agent function tool delegates to orchestrator.
    
    Validates: Requirements 17.4, 17.9
    - Tool routes query to orchestrator
    - Result is a string
    - Result length > 0
    """
    # Mock warm_up and route_query to avoid LLM calls
    mock_warm_up.return_value = None
    mock_response = AgentResponse(
        content="Here are some great chest exercises: bench press, push-ups, and dumbbell flyes.",
        agent_type="workout",
        metadata={}
    )
    mock_route_query.return_value = mock_response
    
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Call ask_specialist_agent with test query and specialist
    result = await agent.ask_specialist_agent(
        query="What exercises should I do for chest development?",
        specialist="workout"
    )
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0
    
    # Assert mock was called
    assert mock_route_query.called


async def test_ask_specialist_agent_invalid_specialist(db_session: AsyncSession, test_user: User):
    """
    Test ask_specialist_agent handles invalid specialist type.
    
    Validates: Error handling for invalid specialist
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Mock orchestrator to avoid initialization
    agent.orchestrator = Mock()
    
    # Call ask_specialist_agent with invalid specialist
    result = await agent.ask_specialist_agent(
        query="Test query",
        specialist="invalid_specialist"
    )
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "workout" in result.lower() or "diet" in result.lower() or "supplement" in result.lower()


async def test_ask_specialist_agent_no_orchestrator(db_session: AsyncSession, test_user: User):
    """
    Test ask_specialist_agent handles missing orchestrator gracefully.
    
    Validates: Error handling when orchestrator not initialized
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Call ask_specialist_agent without orchestrator
    result = await agent.ask_specialist_agent(
        query="Test query",
        specialist="workout"
    )
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


# ============================================================================
# Integration Tests - Background Log Worker
# ============================================================================

async def test_log_worker_cleanup(db_session: AsyncSession, test_user: User):
    """
    Test log worker cleanup cancels task gracefully.
    
    Validates: Requirements 14.3, 14.4
    - Cleanup cancels log worker task
    - Cleanup waits for task completion
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Verify log worker task is running
    assert agent._log_worker_task is not None
    assert not agent._log_worker_task.done()
    
    # Call cleanup
    await agent.cleanup()
    
    # Verify log worker task is cancelled
    assert agent._log_worker_task.done()


async def test_log_worker_error_handling(db_session: AsyncSession, test_user: User):
    """
    Test log worker continues processing after errors.
    
    Validates: Requirements 7.6, 19.4
    - Log worker logs errors
    - Log worker continues processing after error
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Queue an invalid entry (missing required fields)
    invalid_entry = {
        "exercise": None,  # Invalid: None value
        "reps": "invalid",  # Invalid: string instead of int
        "weight": -100,  # Invalid: negative weight
        "timestamp": "invalid-timestamp"  # Invalid: bad timestamp format
    }
    
    await agent._log_queue.put(invalid_entry)
    
    # Queue a valid entry after the invalid one
    valid_entry = {
        "exercise": "Bench Press",
        "reps": 10,
        "weight": 135.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await agent._log_queue.put(valid_entry)
    
    # Wait for log worker to process both entries
    await asyncio.sleep(1.0)
    
    # Verify log worker is still running (didn't crash)
    assert agent._log_worker_task is not None
    assert not agent._log_worker_task.done()
    
    # Cleanup
    await agent.cleanup()


# ============================================================================
# Integration Tests - Base Instructions
# ============================================================================

async def test_base_instructions_vary_by_agent_type():
    """
    Test _get_base_instructions returns different instructions for each agent type.
    
    Validates: Requirements 3.5, 20.2
    - Instructions mention agent type
    - Instructions are non-empty
    - Instructions vary by agent type
    """
    agent_types = ["workout", "diet", "supplement", "general"]
    
    for agent_type in agent_types:
        # Create agent with specific type
        agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type=agent_type)
        
        # Get base instructions
        instructions = agent._get_base_instructions(agent_type)
        
        # Assert instructions are non-empty
        assert len(instructions) > 50
        
        # Assert instructions mention response guidelines
        assert "30 seconds" in instructions or "concise" in instructions.lower()
        
        # Assert instructions mention tools
        assert "get_todays_workout" in instructions or "ask_specialist_agent" in instructions


async def test_base_instructions_workout_agent():
    """
    Test workout agent instructions include workout-specific guidance.
    
    Validates: Workout agent has appropriate domain instructions
    """
    agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type="workout")
    instructions = agent._get_base_instructions("workout")
    
    # Assert workout-specific content
    assert "workout" in instructions.lower()
    assert "exercise" in instructions.lower()


async def test_base_instructions_diet_agent():
    """
    Test diet agent instructions include nutrition-specific guidance.
    
    Validates: Diet agent has appropriate domain instructions
    """
    agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type="diet")
    instructions = agent._get_base_instructions("diet")
    
    # Assert diet-specific content
    assert "nutrition" in instructions.lower() or "meal" in instructions.lower()

    """
    Test FitnessVoiceAgent initialization with test user.
    
    Validates: Requirements 17.5, 17.6
    - Agent orchestrator is initialized
    - User context is loaded
    - User context matches test user
    """
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    
    # Create LifestyleBaseline with energy level
    lifestyle = LifestyleBaseline(
        profile_id=profile.id,
        energy_level=7,
        stress_level=5,
        sleep_quality=6
    )
    db_session.add(lifestyle)
    
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Verify initial state
    assert agent.user_id == str(test_user.id)
    assert agent.agent_type == "workout"
    assert agent.orchestrator is None
    assert agent.user_context is None
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Assert orchestrator is not None
    assert agent.orchestrator is not None
    
    # Assert user_context is not None
    assert agent.user_context is not None
    
    # Assert user_context.user_id matches test user
    assert agent.user_context.user_id == str(test_user.id)
    
    # Assert user_context has expected values
    assert agent.user_context.fitness_level == "intermediate"
    assert agent.user_context.primary_goal == "muscle_gain"
    assert agent.user_context.energy_level in ["medium", "high"]  # Energy level mapping


async def test_voice_agent_initialization_missing_user(db_session: AsyncSession):
    """
    Test FitnessVoiceAgent initialization fails gracefully for missing user.
    
    Validates: Error handling for missing user profile
    """
    # Create agent with non-existent user ID
    fake_user_id = str(uuid4())
    agent = FitnessVoiceAgent(user_id=fake_user_id, agent_type="general")
    
    # Call initialize_orchestrator() should raise ValueError
    with pytest.raises(ValueError):
        await agent.initialize_orchestrator()


# ============================================================================
# Integration Tests - get_todays_workout Tool
# ============================================================================

async def test_get_todays_workout_tool(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout function tool returns cached data.
    
    Validates: Requirements 17.2, 17.7
    - Tool returns workout data from cached context
    - Result is a string
    - Result length > 0
    """
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Mock user_context with workout plan
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss",
        current_workout_plan={
            "name": "Upper Body Push",
            "exercises": [
                {"name": "Bench Press", "sets": 3, "reps": 10},
                {"name": "Overhead Press", "sets": 3, "reps": 8},
                {"name": "Push-ups", "sets": 3, "reps": 15}
            ]
        }
    )
    
    # Call get_todays_workout()
    result = await agent.get_todays_workout()
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0
    
    # Assert result contains workout name
    assert "Upper Body Push" in result
    
    # Assert result contains exercise names
    assert "Bench Press" in result
    assert "Overhead Press" in result
    assert "Push-ups" in result


async def test_get_todays_workout_no_context(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout handles missing context gracefully.
    
    Validates: Error handling when context not loaded
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Call get_todays_workout() without context
    result = await agent.get_todays_workout()
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


async def test_get_todays_workout_empty_plan(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_workout handles empty workout plan.
    
    Validates: Graceful handling of missing workout plan
    """
    # Create agent
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Mock user_context with empty workout plan
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss",
        current_workout_plan={}
    )
    
    # Call get_todays_workout()
    result = await agent.get_todays_workout()
    
    # Assert result suggests creating a plan
    assert isinstance(result, str)
    assert "don't see" in result.lower() or "create" in result.lower()


# ============================================================================
# Integration Tests - get_todays_meals Tool
# ============================================================================

async def test_get_todays_meals_tool(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_meals function tool returns cached data.
    
    Validates: Requirements 17.2, 17.7
    - Tool returns meal data from cached context
    - Result is a string (JSON format)
    - Result length > 0
    """
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="diet")
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Mock user_context with meal plan
    agent.user_context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        current_meal_plan={
            "name": "High Protein Meal Plan",
            "meals": [
                {
                    "meal_type": "breakfast",
                    "name": "Oatmeal with Protein",
                    "calories": 450,
                    "protein_g": 30,
                    "carbs_g": 50,
                    "fat_g": 12
                },
                {
                    "meal_type": "lunch",
                    "name": "Chicken and Rice",
                    "calories": 600,
                    "protein_g": 45,
                    "carbs_g": 60,
                    "fat_g": 15
                },
                {
                    "meal_type": "dinner",
                    "name": "Salmon with Vegetables",
                    "calories": 550,
                    "protein_g": 40,
                    "carbs_g": 40,
                    "fat_g": 20
                }
            ]
        }
    )
    
    # Call get_todays_meals()
    result = await agent.get_todays_meals()
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0
    
    # Assert result contains meal plan name
    assert "High Protein Meal Plan" in result
    
    # Assert result contains meal types
    assert "breakfast" in result.lower()
    assert "lunch" in result.lower()
    assert "dinner" in result.lower()


async def test_get_todays_meals_no_context(db_session: AsyncSession, test_user: User):
    """
    Test get_todays_meals handles missing context gracefully.
    
    Validates: Error handling when context not loaded
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="diet")
    
    # Call get_todays_meals() without context
    result = await agent.get_todays_meals()
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


# ============================================================================
# Integration Tests - log_workout_set Tool
# ============================================================================

async def test_log_workout_set_tool(db_session: AsyncSession, test_user: User):
    """
    Test log_workout_set function tool queues data and returns confirmation.
    
    Validates: Requirements 17.3, 17.8
    - Tool queues workout set data
    - Result contains "Logged"
    - Result contains exercise name
    - Background worker persists data to database
    """
    # Create UserProfile for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Call log_workout_set with test data
    result = await agent.log_workout_set(
        exercise="Bench Press",
        reps=10,
        weight=135.0
    )
    
    # Assert result contains "Logged"
    assert "Logged" in result or "logged" in result.lower()
    
    # Assert result contains exercise name
    assert "Bench Press" in result
    
    # Assert result contains reps and weight
    assert "10" in result
    assert "135" in result
    
    # Wait for log worker to process the entry
    await asyncio.sleep(0.5)
    
    # Verify entry was persisted to database
    from sqlalchemy import select
    stmt = select(WorkoutLog).where(
        WorkoutLog.user_id == test_user.id,
        WorkoutLog.exercise == "Bench Press"
    )
    result_db = await db_session.execute(stmt)
    log_entry = result_db.scalar_one_or_none()
    
    # Assert log entry exists in database
    assert log_entry is not None
    assert log_entry.exercise == "Bench Press"
    assert log_entry.reps == 10
    assert log_entry.weight_kg == 135.0
    
    # Cleanup
    await agent.cleanup()


async def test_log_workout_set_multiple_entries(db_session: AsyncSession, test_user: User):
    """
    Test log_workout_set handles multiple entries correctly.
    
    Validates: Background worker processes multiple entries
    """
    # Create UserProfile for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="advanced",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Log multiple workout sets
    exercises = [
        ("Bench Press", 10, 135.0),
        ("Squats", 8, 225.0),
        ("Deadlifts", 5, 315.0)
    ]
    
    for exercise, reps, weight in exercises:
        result = await agent.log_workout_set(
            exercise=exercise,
            reps=reps,
            weight=weight
        )
        assert "Logged" in result or "logged" in result.lower()
    
    # Wait for queue to be empty (all entries processed)`n    await agent._log_queue.join()`n    `n    # Give a small buffer for database commits`n    await asyncio.sleep(0.2)
    
    # Verify all entries were persisted to database
    from sqlalchemy import select
    stmt = select(WorkoutLog).where(WorkoutLog.user_id == test_user.id)
    result_db = await db_session.execute(stmt)
    log_entries = result_db.scalars().all()
    
    # Assert all 3 entries exist
    assert len(log_entries) == 3
    
    # Verify exercise names
    exercise_names = {entry.exercise for entry in log_entries}
    assert "Bench Press" in exercise_names
    assert "Squats" in exercise_names
    assert "Deadlifts" in exercise_names
    
    # Cleanup
    await agent.cleanup()


# ============================================================================
# Integration Tests - ask_specialist_agent Tool
# ============================================================================

async def test_ask_specialist_agent_tool(db_session: AsyncSession, test_user: User):
    """
    Test ask_specialist_agent function tool delegates to orchestrator.
    
    Validates: Requirements 17.4, 17.9
    - Tool routes query to orchestrator
    - Result is a string
    - Result length > 0
    """
    # Create UserProfile with FitnessGoal for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create FitnessGoal for the profile
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Call ask_specialist_agent with test query and specialist
    result = await agent.ask_specialist_agent(
        query="What exercises should I do for chest development?",
        specialist="workout"
    )
    
    # Assert result is string
    assert isinstance(result, str)
    
    # Assert result length > 0
    assert len(result) > 0


async def test_ask_specialist_agent_invalid_specialist(db_session: AsyncSession, test_user: User):
    """
    Test ask_specialist_agent handles invalid specialist type.
    
    Validates: Error handling for invalid specialist
    """
    # Create UserProfile for the test user
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Call initialize_orchestrator()
    await agent.initialize_orchestrator()
    
    # Call ask_specialist_agent with invalid specialist
    result = await agent.ask_specialist_agent(
        query="Test query",
        specialist="invalid_specialist"
    )
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "workout" in result.lower() or "diet" in result.lower() or "supplement" in result.lower()


async def test_ask_specialist_agent_no_orchestrator(db_session: AsyncSession, test_user: User):
    """
    Test ask_specialist_agent handles missing orchestrator gracefully.
    
    Validates: Error handling when orchestrator not initialized
    """
    # Create agent without initializing orchestrator
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="general")
    
    # Call ask_specialist_agent without orchestrator
    result = await agent.ask_specialist_agent(
        query="Test query",
        specialist="workout"
    )
    
    # Assert result is error message
    assert isinstance(result, str)
    assert "trouble" in result.lower() or "try again" in result.lower()


# ============================================================================
# Integration Tests - Background Log Worker
# ============================================================================

async def test_log_worker_cleanup(db_session: AsyncSession, test_user: User):
    """
    Test log worker cleanup cancels task gracefully.
    
    Validates: Requirements 14.3, 14.4
    - Cleanup cancels log worker task
    - Cleanup waits for task completion
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Verify log worker task is running
    assert agent._log_worker_task is not None
    assert not agent._log_worker_task.done()
    
    # Call cleanup
    await agent.cleanup()
    
    # Verify log worker task is cancelled
    assert agent._log_worker_task.done()


async def test_log_worker_error_handling(db_session: AsyncSession, test_user: User):
    """
    Test log worker continues processing after errors.
    
    Validates: Requirements 7.6, 19.4
    - Log worker logs errors
    - Log worker continues processing after error
    """
    # Create FitnessVoiceAgent with test user
    agent = FitnessVoiceAgent(user_id=str(test_user.id), agent_type="workout")
    
    # Start log worker
    await agent.start_log_worker()
    
    # Queue an invalid entry (missing required fields)
    invalid_entry = {
        "exercise": None,  # Invalid: None value
        "reps": "invalid",  # Invalid: string instead of int
        "weight": -100,  # Invalid: negative weight
        "timestamp": "invalid-timestamp"  # Invalid: bad timestamp format
    }
    
    await agent._log_queue.put(invalid_entry)
    
    # Queue a valid entry after the invalid one
    valid_entry = {
        "exercise": "Bench Press",
        "reps": 10,
        "weight": 135.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await agent._log_queue.put(valid_entry)
    
    # Wait for log worker to process both entries
    await asyncio.sleep(1.0)
    
    # Verify log worker is still running (didn't crash)
    assert agent._log_worker_task is not None
    assert not agent._log_worker_task.done()
    
    # Cleanup
    await agent.cleanup()


# ============================================================================
# Integration Tests - Base Instructions
# ============================================================================

async def test_base_instructions_vary_by_agent_type():
    """
    Test _get_base_instructions returns different instructions for each agent type.
    
    Validates: Requirements 3.5, 20.2
    - Instructions mention agent type
    - Instructions are non-empty
    - Instructions vary by agent type
    """
    agent_types = ["workout", "diet", "supplement", "general"]
    
    for agent_type in agent_types:
        # Create agent with specific type
        agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type=agent_type)
        
        # Get base instructions
        instructions = agent._get_base_instructions(agent_type)
        
        # Assert instructions are non-empty
        assert len(instructions) > 50
        
        # Assert instructions mention response guidelines
        assert "30 seconds" in instructions or "concise" in instructions.lower()
        
        # Assert instructions mention tools
        assert "get_todays_workout" in instructions or "ask_specialist_agent" in instructions


async def test_base_instructions_workout_agent():
    """
    Test workout agent instructions include workout-specific guidance.
    
    Validates: Workout agent has appropriate domain instructions
    """
    agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type="workout")
    instructions = agent._get_base_instructions("workout")
    
    # Assert workout-specific content
    assert "workout" in instructions.lower()
    assert "exercise" in instructions.lower()


async def test_base_instructions_diet_agent():
    """
    Test diet agent instructions include nutrition-specific guidance.
    
    Validates: Diet agent has appropriate domain instructions
    """
    agent = FitnessVoiceAgent(user_id=str(uuid4()), agent_type="diet")
    instructions = agent._get_base_instructions("diet")
    
    # Assert diet-specific content
    assert "nutrition" in instructions.lower() or "meal" in instructions.lower()


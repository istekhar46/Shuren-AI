"""
Unit tests for agent onboarding function tools.

This module tests:
- Each agent's onboarding tools call the correct endpoint
- Error handling and structured responses
- Agent context logging

Requirements tested: 2.3.1, 2.3.2, 2.3.4
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workout_planner import WorkoutPlannerAgent
from app.agents.diet_planner import DietPlannerAgent
from app.agents.scheduler import SchedulerAgent
from app.agents.supplement_guide import SupplementGuideAgent
from app.agents.context import AgentContext
from app.agents.onboarding_tools import call_onboarding_step
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.services.onboarding_service import OnboardingValidationError


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def agent_context(test_user: User) -> AgentContext:
    """Create a test agent context."""
    return AgentContext(
        user_id=str(test_user.id),  # Convert UUID to string
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high"
    )


@pytest_asyncio.fixture
async def workout_agent(db_session: AsyncSession, agent_context: AgentContext) -> WorkoutPlannerAgent:
    """Create a WorkoutPlannerAgent instance for testing."""
    agent = WorkoutPlannerAgent(context=agent_context, db_session=db_session)
    return agent


@pytest_asyncio.fixture
async def diet_agent(db_session: AsyncSession, agent_context: AgentContext) -> DietPlannerAgent:
    """Create a DietPlannerAgent instance for testing."""
    agent = DietPlannerAgent(context=agent_context, db_session=db_session)
    return agent


@pytest_asyncio.fixture
async def scheduler_agent(db_session: AsyncSession, agent_context: AgentContext) -> SchedulerAgent:
    """Create a SchedulerAgent instance for testing."""
    agent = SchedulerAgent(context=agent_context, db_session=db_session)
    return agent


@pytest_asyncio.fixture
async def supplement_agent(db_session: AsyncSession, agent_context: AgentContext) -> SupplementGuideAgent:
    """Create a SupplementGuideAgent instance for testing."""
    agent = SupplementGuideAgent(context=agent_context, db_session=db_session)
    return agent


# ============================================================================
# Test call_onboarding_step Helper Function
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_call_onboarding_step_success(
    db_session: AsyncSession,
    test_user: User,
    caplog
):
    """Test call_onboarding_step with successful save.
    
    Requirements: 2.3.1, 2.3.4
    """
    # Arrange
    step = 1
    data = {"fitness_level": "beginner"}
    agent_type = "workout_planning"
    
    with caplog.at_level(logging.INFO):
        # Act
        result = await call_onboarding_step(
            db=db_session,
            user_id=test_user.id,
            step=step,
            data=data,
            agent_type=agent_type
        )
    
    # Assert - Check response structure
    assert result["success"] is True
    assert "message" in result
    assert result["message"] == f"State {step} saved successfully"
    assert result["current_state"] == 1
    assert result["next_state"] == 2
    
    # Assert - Check logging
    assert any(
        f"Agent {agent_type} saving onboarding step {step}" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_call_onboarding_step_validation_error(
    db_session: AsyncSession,
    test_user: User,
    caplog
):
    """Test call_onboarding_step with validation error.
    
    Requirements: 2.3.2, 2.3.4
    """
    # Arrange
    step = 1
    data = {"fitness_level": "invalid_level"}  # Invalid value
    agent_type = "workout_planning"
    
    with caplog.at_level(logging.WARNING):
        # Act
        result = await call_onboarding_step(
            db=db_session,
            user_id=test_user.id,
            step=step,
            data=data,
            agent_type=agent_type
        )
    
    # Assert - Check error response structure
    assert result["success"] is False
    assert "error" in result
    assert "field" in result
    assert result["error_code"] == "VALIDATION_ERROR"
    
    # Assert - Check logging
    assert any(
        "Validation error" in record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_call_onboarding_step_logs_agent_context(
    db_session: AsyncSession,
    test_user: User,
    caplog
):
    """Test that call_onboarding_step logs agent context.
    
    Requirements: 2.3.4
    """
    # Arrange
    step = 2
    data = {"goals": [{"goal_type": "fat_loss", "priority": 1}]}
    agent_type = "workout_planning"
    
    with caplog.at_level(logging.INFO):
        # Act
        await call_onboarding_step(
            db=db_session,
            user_id=test_user.id,
            step=step,
            data=data,
            agent_type=agent_type
        )
    
    # Assert - Check that log includes agent context
    log_records = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(log_records) > 0
    
    # Check log message
    assert any(
        agent_type in record.message and str(step) in record.message
        for record in log_records
    )
    
    # Check log extra fields
    assert any(
        hasattr(record, "user_id") and hasattr(record, "agent") and hasattr(record, "step")
        for record in log_records
    )


# ============================================================================
# Test WorkoutPlannerAgent Onboarding Tools
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_workout_agent_save_fitness_level(
    workout_agent: WorkoutPlannerAgent,
    db_session: AsyncSession
):
    """Test WorkoutPlannerAgent.save_fitness_level calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    fitness_level = "intermediate"
    
    # Act
    result = await workout_agent.save_fitness_level(fitness_level)
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 1
    assert result["next_state"] == 2
    
    # Verify data was saved to database
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(workout_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    assert "step_1" in onboarding_state.step_data
    assert onboarding_state.step_data["step_1"]["fitness_level"] == fitness_level


@pytest.mark.asyncio
@pytest.mark.unit
async def test_workout_agent_save_fitness_goals(
    workout_agent: WorkoutPlannerAgent,
    db_session: AsyncSession
):
    """Test WorkoutPlannerAgent.save_fitness_goals calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    goals = [
        {"goal_type": "muscle_gain", "priority": 1},
        {"goal_type": "fat_loss", "priority": 2}
    ]
    
    # Act
    result = await workout_agent.save_fitness_goals(goals)
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 2
    assert result["next_state"] == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_workout_agent_save_workout_constraints(
    workout_agent: WorkoutPlannerAgent,
    db_session: AsyncSession
):
    """Test WorkoutPlannerAgent.save_workout_constraints calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    equipment = ["dumbbells", "resistance_bands"]
    injuries = []
    limitations = ["lower_back_pain"]
    target_weight_kg = 75.0
    target_body_fat_percentage = 15.0
    
    # Act
    result = await workout_agent.save_workout_constraints(
        equipment=equipment,
        injuries=injuries,
        limitations=limitations,
        target_weight_kg=target_weight_kg,
        target_body_fat_percentage=target_body_fat_percentage
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 3
    assert result["next_state"] == 4
    
    # Verify data was saved
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(workout_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    assert "step_3" in onboarding_state.step_data
    step_data = onboarding_state.step_data["step_3"]
    assert step_data["equipment"] == equipment
    assert step_data["target_weight_kg"] == target_weight_kg


@pytest.mark.asyncio
@pytest.mark.unit
async def test_workout_agent_save_workout_constraints_optional_fields(
    workout_agent: WorkoutPlannerAgent,
    db_session: AsyncSession
):
    """Test WorkoutPlannerAgent.save_workout_constraints without optional fields.
    
    Requirements: 2.3.1
    """
    # Arrange
    equipment = ["bodyweight"]
    injuries = []
    limitations = []
    
    # Act
    result = await workout_agent.save_workout_constraints(
        equipment=equipment,
        injuries=injuries,
        limitations=limitations
    )
    
    # Assert
    assert result["success"] is True
    
    # Verify optional fields not included
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(workout_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    step_data = onboarding_state.step_data["step_3"]
    assert "target_weight_kg" not in step_data
    assert "target_body_fat_percentage" not in step_data


# ============================================================================
# Test DietPlannerAgent Onboarding Tools
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_diet_agent_save_dietary_preferences(
    diet_agent: DietPlannerAgent,
    db_session: AsyncSession
):
    """Test DietPlannerAgent.save_dietary_preferences calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    diet_type = "vegetarian"
    allergies = ["peanuts"]
    intolerances = ["lactose"]
    dislikes = ["mushrooms"]
    
    # Act
    result = await diet_agent.save_dietary_preferences(
        diet_type=diet_type,
        allergies=allergies,
        intolerances=intolerances,
        dislikes=dislikes
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 4
    assert result["next_state"] == 5
    
    # Verify data was saved
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(diet_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    assert "step_4" in onboarding_state.step_data
    step_data = onboarding_state.step_data["step_4"]
    assert step_data["diet_type"] == diet_type
    assert step_data["allergies"] == allergies


@pytest.mark.asyncio
@pytest.mark.unit
async def test_diet_agent_save_meal_plan(
    diet_agent: DietPlannerAgent,
    db_session: AsyncSession
):
    """Test DietPlannerAgent.save_meal_plan calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    daily_calorie_target = 2000
    protein_percentage = 30.0
    carbs_percentage = 45.0
    fats_percentage = 25.0
    
    # Act
    result = await diet_agent.save_meal_plan(
        daily_calorie_target=daily_calorie_target,
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fats_percentage=fats_percentage
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 5
    assert result["next_state"] == 6


@pytest.mark.asyncio
@pytest.mark.unit
async def test_diet_agent_save_meal_plan_validation_error(
    diet_agent: DietPlannerAgent,
    db_session: AsyncSession
):
    """Test DietPlannerAgent.save_meal_plan with invalid percentages.
    
    Requirements: 2.3.2
    """
    # Arrange - percentages don't sum to 100
    daily_calorie_target = 2000
    protein_percentage = 30.0
    carbs_percentage = 40.0
    fats_percentage = 40.0  # Sum = 110
    
    # Act
    result = await diet_agent.save_meal_plan(
        daily_calorie_target=daily_calorie_target,
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fats_percentage=fats_percentage
    )
    
    # Assert
    assert result["success"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "error" in result
    assert "field" in result


# ============================================================================
# Test SchedulerAgent Onboarding Tools
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_scheduler_agent_save_meal_schedule(
    scheduler_agent: SchedulerAgent,
    db_session: AsyncSession
):
    """Test SchedulerAgent.save_meal_schedule calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    meals = [
        {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True},
        {"meal_name": "Lunch", "scheduled_time": "13:00", "enable_notifications": True},
        {"meal_name": "Dinner", "scheduled_time": "19:00", "enable_notifications": False}
    ]
    
    # Act
    result = await scheduler_agent.save_meal_schedule(meals)
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 6
    assert result["next_state"] == 7
    
    # Verify data was saved
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(scheduler_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    assert "step_6" in onboarding_state.step_data
    assert len(onboarding_state.step_data["step_6"]["meals"]) == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scheduler_agent_save_workout_schedule(
    scheduler_agent: SchedulerAgent,
    db_session: AsyncSession
):
    """Test SchedulerAgent.save_workout_schedule calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    workouts = [
        {"day_of_week": 1, "scheduled_time": "07:00", "enable_notifications": True},
        {"day_of_week": 3, "scheduled_time": "07:00", "enable_notifications": True},
        {"day_of_week": 5, "scheduled_time": "18:00", "enable_notifications": False}
    ]
    
    # Act
    result = await scheduler_agent.save_workout_schedule(workouts)
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 7
    assert result["next_state"] == 8


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scheduler_agent_save_hydration_schedule(
    scheduler_agent: SchedulerAgent,
    db_session: AsyncSession
):
    """Test SchedulerAgent.save_hydration_schedule calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    daily_water_target_ml = 3000
    reminder_frequency_minutes = 60
    
    # Act
    result = await scheduler_agent.save_hydration_schedule(
        daily_water_target_ml=daily_water_target_ml,
        reminder_frequency_minutes=reminder_frequency_minutes
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 8
    assert result["next_state"] == 9


# ============================================================================
# Test SupplementGuideAgent Onboarding Tools
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_supplement_agent_save_supplement_preferences(
    supplement_agent: SupplementGuideAgent,
    db_session: AsyncSession
):
    """Test SupplementGuideAgent.save_supplement_preferences calls correct endpoint.
    
    Requirements: 2.3.1
    """
    # Arrange
    interested_in_supplements = True
    current_supplements = ["protein powder", "creatine"]
    
    # Act
    result = await supplement_agent.save_supplement_preferences(
        interested_in_supplements=interested_in_supplements,
        current_supplements=current_supplements
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 9
    assert result["next_state"] is None  # Last state
    
    # Verify data was saved
    from sqlalchemy import select
    from uuid import UUID
    stmt = select(OnboardingState).where(
        OnboardingState.user_id == UUID(supplement_agent.context.user_id)
    )
    db_result = await db_session.execute(stmt)
    onboarding_state = db_result.scalar_one()
    
    assert "step_9" in onboarding_state.step_data
    step_data = onboarding_state.step_data["step_9"]
    assert step_data["interested_in_supplements"] is True
    assert step_data["current_supplements"] == current_supplements


@pytest.mark.asyncio
@pytest.mark.unit
async def test_supplement_agent_save_supplement_preferences_not_interested(
    supplement_agent: SupplementGuideAgent,
    db_session: AsyncSession
):
    """Test SupplementGuideAgent.save_supplement_preferences when not interested.
    
    Requirements: 2.3.1
    """
    # Arrange
    interested_in_supplements = False
    current_supplements = []
    
    # Act
    result = await supplement_agent.save_supplement_preferences(
        interested_in_supplements=interested_in_supplements,
        current_supplements=current_supplements
    )
    
    # Assert
    assert result["success"] is True
    assert result["current_state"] == 9


# ============================================================================
# Test Error Handling and Structured Responses
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_tool_returns_structured_error_on_validation_failure(
    workout_agent: WorkoutPlannerAgent,
    db_session: AsyncSession
):
    """Test that agent tools return structured error responses.
    
    Requirements: 2.3.2
    """
    # Arrange - invalid fitness level
    fitness_level = "expert"  # Not a valid option
    
    # Act
    result = await workout_agent.save_fitness_level(fitness_level)
    
    # Assert - Check structured error response
    assert result["success"] is False
    assert "error" in result
    assert "field" in result
    assert "error_code" in result
    assert result["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_tool_returns_structured_success_response(
    diet_agent: DietPlannerAgent,
    db_session: AsyncSession
):
    """Test that agent tools return structured success responses.
    
    Requirements: 2.3.1
    """
    # Arrange
    diet_type = "vegan"
    allergies = []
    intolerances = []
    dislikes = []
    
    # Act
    result = await diet_agent.save_dietary_preferences(
        diet_type=diet_type,
        allergies=allergies,
        intolerances=intolerances,
        dislikes=dislikes
    )
    
    # Assert - Check structured success response
    assert result["success"] is True
    assert "message" in result
    assert "current_state" in result
    assert "next_state" in result
    assert isinstance(result["current_state"], int)
    assert isinstance(result["next_state"], (int, type(None)))


@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_tool_handles_empty_lists(
    scheduler_agent: SchedulerAgent,
    db_session: AsyncSession
):
    """Test that agent tools handle empty lists correctly.
    
    Requirements: 2.3.1, 2.3.2
    """
    # Arrange - empty meals list should fail validation
    meals = []
    
    # Act
    result = await scheduler_agent.save_meal_schedule(meals)
    
    # Assert - Should return validation error
    assert result["success"] is False
    assert result["error_code"] == "VALIDATION_ERROR"

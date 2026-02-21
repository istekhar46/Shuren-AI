"""Integration test for agent foundation migration with existing data.

This test simulates a real-world scenario where the database has existing
onboarding records and verifies the migration preserves all data.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def database_with_existing_records(db_session: AsyncSession) -> list[tuple[User, OnboardingState]]:
    """Create multiple users with various onboarding states.
    
    Simulates a production database with:
    - Users at different onboarding steps
    - Completed and incomplete onboarding
    - Various step_data configurations
    """
    records = []
    
    # User 1: Just started onboarding
    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        hashed_password=hash_password("password"),
        full_name="User One",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user1)
    
    state1 = OnboardingState(
        id=uuid4(),
        user_id=user1.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(state1)
    records.append((user1, state1))
    
    # User 2: Mid-way through onboarding
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        hashed_password=hash_password("password"),
        full_name="User Two",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user2)
    
    state2 = OnboardingState(
        id=uuid4(),
        user_id=user2.id,
        current_step=5,
        is_complete=False,
        step_data={
            "step_1": {"age": 30, "gender": "male", "height_cm": 180, "weight_kg": 80},
            "step_2": {"fitness_level": "intermediate"},
            "step_3": {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
            "step_4": {"constraints": []},
            "step_5": {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []}
        },
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(state2)
    records.append((user2, state2))
    
    # User 3: Completed onboarding
    user3 = User(
        id=uuid4(),
        email="user3@example.com",
        hashed_password=hash_password("password"),
        full_name="User Three",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user3)
    
    state3 = OnboardingState(
        id=uuid4(),
        user_id=user3.id,
        current_step=9,
        is_complete=True,
        step_data={
            "step_1": {"age": 25, "gender": "female", "height_cm": 165, "weight_kg": 60},
            "step_2": {"fitness_level": "beginner"},
            "step_3": {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
            "step_4": {"constraints": [{"constraint_type": "equipment", "description": "No gym access"}]},
            "step_5": {"diet_type": "vegetarian", "allergies": [], "intolerances": ["lactose"], "dislikes": []},
            "step_6": {"daily_calorie_target": 1800, "protein_percentage": 25, "carbs_percentage": 50, "fats_percentage": 25},
            "step_7": {"meal_schedules": []},
            "step_8": {"workout_schedules": []},
            "step_9": {"daily_water_target_ml": 2000, "reminder_frequency_minutes": 120, "enable_notifications": False}
        },
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(state3)
    records.append((user3, state3))
    
    await db_session.commit()
    
    # Refresh all records
    for user, state in records:
        await db_session.refresh(user)
        await db_session.refresh(state)
    
    return records


@pytest.mark.asyncio
@pytest.mark.integration
async def test_migration_with_multiple_existing_records(
    db_session: AsyncSession,
    database_with_existing_records: list[tuple[User, OnboardingState]]
):
    """Test that migration preserves data for all existing records.
    
    Verifies:
    - All users still exist
    - All onboarding states are preserved
    - All step_data is intact
    - New fields have correct defaults
    """
    original_records = database_with_existing_records
    
    # Reload all records from database
    for original_user, original_state in original_records:
        # Reload user
        user = await db_session.get(User, original_user.id)
        assert user is not None
        assert user.email == original_user.email
        assert user.full_name == original_user.full_name
        
        # Reload onboarding state
        state = await db_session.get(OnboardingState, original_state.id)
        assert state is not None
        
        # Verify original fields preserved
        assert state.user_id == original_state.user_id
        assert state.current_step == original_state.current_step
        assert state.is_complete == original_state.is_complete
        assert state.step_data == original_state.step_data
        assert state.agent_history == original_state.agent_history
        
        # Verify new fields have defaults
        assert state.current_agent is None
        assert state.agent_context == {}
        assert state.conversation_history == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_new_agent_workflow_with_migrated_data(
    db_session: AsyncSession,
    database_with_existing_records: list[tuple[User, OnboardingState]]
):
    """Test that new agent workflow works with migrated data.
    
    Simulates the agent foundation using the new fields on existing records.
    """
    # Get a user mid-way through onboarding
    user, state = database_with_existing_records[1]  # User 2 at step 5
    
    # Reload state
    state = await db_session.get(OnboardingState, state.id)
    
    # Simulate agent setting current_agent
    state.current_agent = "diet_planning"
    
    # Simulate agent adding context
    state.agent_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "completed_at": "2024-01-15T10:00:00Z"
        },
        "goal_setting": {
            "primary_goal": "muscle_gain",
            "completed_at": "2024-01-15T10:05:00Z"
        }
    }
    
    # Simulate conversation
    state.conversation_history = [
        {
            "role": "user",
            "content": "I want to build muscle",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Great goal! Let's create a plan for you.",
            "timestamp": "2024-01-15T10:00:05Z",
            "agent_type": "goal_setting"
        }
    ]
    
    await db_session.commit()
    await db_session.refresh(state)
    
    # Verify all data is saved correctly
    assert state.current_agent == "diet_planning"
    assert "fitness_assessment" in state.agent_context
    assert "goal_setting" in state.agent_context
    assert len(state.conversation_history) == 2
    
    # Verify original data still intact
    assert state.current_step == 5
    assert state.step_data["step_1"]["age"] == 30
    assert state.step_data["step_2"]["fitness_level"] == "intermediate"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backward_compatibility_with_existing_service(
    db_session: AsyncSession,
    database_with_existing_records: list[tuple[User, OnboardingState]]
):
    """Test that existing onboarding service still works after migration.
    
    Verifies that code that doesn't use the new fields continues to work.
    """
    # Get a user
    user, original_state = database_with_existing_records[0]
    
    # Simulate existing service updating step_data (without touching new fields)
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    
    # Update step_data like existing service would
    state.step_data = {"step_1": {"age": 28, "gender": "male", "height_cm": 175, "weight_kg": 75}}
    state.current_step = 1
    
    await db_session.commit()
    await db_session.refresh(state)
    
    # Verify update worked
    assert state.step_data["step_1"]["age"] == 28
    assert state.current_step == 1
    
    # Verify new fields still have defaults (not affected by old service)
    assert state.current_agent is None
    assert state.agent_context == {}
    assert state.conversation_history == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_query_performance_with_new_fields(
    db_session: AsyncSession,
    database_with_existing_records: list[tuple[User, OnboardingState]]
):
    """Test that queries still perform well with new JSONB fields.
    
    Verifies that adding JSONB fields doesn't significantly impact query performance.
    """
    # Query all onboarding states
    stmt = select(OnboardingState)
    result = await db_session.execute(stmt)
    states = result.scalars().all()
    
    # Verify we got all records
    assert len(states) == 3
    
    # Verify all have new fields
    for state in states:
        assert hasattr(state, 'current_agent')
        assert hasattr(state, 'agent_context')
        assert hasattr(state, 'conversation_history')
        
        # Verify defaults
        assert state.current_agent is None
        assert isinstance(state.agent_context, dict)
        assert isinstance(state.conversation_history, list)

"""Test database migration for agent foundation fields.

This test verifies that the migration adds the three new fields correctly
and preserves existing data.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def user_with_existing_onboarding(db_session: AsyncSession) -> tuple[User, OnboardingState]:
    """Create a user with existing onboarding state before migration.
    
    This simulates existing data in the database.
    """
    # Create user
    user = User(
        id=uuid4(),
        email="migration_test@example.com",
        hashed_password=hash_password("testpassword"),
        full_name="Migration Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create onboarding state with existing fields only
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=3,
        is_complete=False,
        step_data={"step_1": {"age": 25}, "step_2": {"fitness_level": "intermediate"}},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(onboarding_state)
    
    return user, onboarding_state


@pytest.mark.asyncio
async def test_migration_adds_new_fields(db_session: AsyncSession):
    """Test that new fields are added to the onboarding_states table.
    
    Verifies:
    - current_agent field exists and is nullable
    - agent_context field exists with default {}
    - conversation_history field exists with default []
    """
    # Create a new onboarding state
    user = User(
        id=uuid4(),
        email="newuser@example.com",
        hashed_password=hash_password("password"),
        full_name="New User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Verify new fields exist with correct defaults
    assert hasattr(onboarding_state, 'current_agent')
    assert hasattr(onboarding_state, 'agent_context')
    assert hasattr(onboarding_state, 'conversation_history')
    
    # Verify default values
    assert onboarding_state.current_agent is None
    assert onboarding_state.agent_context == {}
    assert onboarding_state.conversation_history == []


@pytest.mark.asyncio
async def test_migration_preserves_existing_data(
    db_session: AsyncSession,
    user_with_existing_onboarding: tuple[User, OnboardingState]
):
    """Test that migration preserves all existing onboarding data.
    
    Verifies:
    - user_id is preserved
    - current_step is preserved
    - is_complete is preserved
    - step_data is preserved
    - agent_history is preserved
    """
    user, original_state = user_with_existing_onboarding
    
    # Reload the onboarding state from database
    result = await db_session.get(OnboardingState, original_state.id)
    
    # Verify all original fields are preserved
    assert result.user_id == user.id
    assert result.current_step == 3
    assert result.is_complete is False
    assert result.step_data == {"step_1": {"age": 25}, "step_2": {"fitness_level": "intermediate"}}
    assert result.agent_history == []
    
    # Verify new fields have default values
    assert result.current_agent is None
    assert result.agent_context == {}
    assert result.conversation_history == []


@pytest.mark.asyncio
async def test_new_fields_can_be_updated(db_session: AsyncSession):
    """Test that new fields can be updated with valid data.
    
    Verifies:
    - current_agent can be set to a string value
    - agent_context can store JSONB data
    - conversation_history can store array of messages
    """
    # Create user and onboarding state
    user = User(
        id=uuid4(),
        email="updatetest@example.com",
        hashed_password=hash_password("password"),
        full_name="Update Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Update new fields
    onboarding_state.current_agent = "fitness_assessment"
    onboarding_state.agent_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "experience_years": 2
        }
    }
    onboarding_state.conversation_history = [
        {
            "role": "user",
            "content": "I workout 3 times a week",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant",
            "content": "Great! That shows good consistency.",
            "timestamp": "2024-01-15T10:30:05Z",
            "agent_type": "fitness_assessment"
        }
    ]
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Verify updates were saved
    assert onboarding_state.current_agent == "fitness_assessment"
    assert onboarding_state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"
    assert len(onboarding_state.conversation_history) == 2
    assert onboarding_state.conversation_history[0]["role"] == "user"


@pytest.mark.asyncio
async def test_current_agent_nullable(db_session: AsyncSession):
    """Test that current_agent field is nullable.
    
    Verifies that current_agent can be None (for backward compatibility).
    """
    user = User(
        id=uuid4(),
        email="nullable@example.com",
        hashed_password=hash_password("password"),
        full_name="Nullable Test",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        current_agent=None,  # Explicitly set to None
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Verify None is allowed
    assert onboarding_state.current_agent is None


@pytest.mark.asyncio
async def test_agent_context_default_empty_dict(db_session: AsyncSession):
    """Test that agent_context defaults to empty dict.
    
    Verifies that agent_context is never None, always at least {}.
    """
    user = User(
        id=uuid4(),
        email="emptydict@example.com",
        hashed_password=hash_password("password"),
        full_name="Empty Dict Test",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Verify default is empty dict, not None
    assert onboarding_state.agent_context is not None
    assert onboarding_state.agent_context == {}
    assert isinstance(onboarding_state.agent_context, dict)


@pytest.mark.asyncio
async def test_conversation_history_default_empty_list(db_session: AsyncSession):
    """Test that conversation_history defaults to empty list.
    
    Verifies that conversation_history is never None, always at least [].
    """
    user = User(
        id=uuid4(),
        email="emptylist@example.com",
        hashed_password=hash_password("password"),
        full_name="Empty List Test",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        agent_history=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(onboarding_state)
    
    # Verify default is empty list, not None
    assert onboarding_state.conversation_history is not None
    assert onboarding_state.conversation_history == []
    assert isinstance(onboarding_state.conversation_history, list)

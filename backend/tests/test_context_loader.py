"""
Tests for the context loader service.

This module tests the load_agent_context function which loads user data
from the database and assembles it into an immutable AgentContext object.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.context_loader import load_agent_context
from app.agents.context import AgentContext
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    DietaryPreference,
    LifestyleBaseline,
)
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_import_context_loader():
    """Test that context loader can be imported successfully."""
    from app.services.context_loader import load_agent_context
    assert load_agent_context is not None
    assert callable(load_agent_context)


@pytest.mark.asyncio
async def test_load_agent_context_with_complete_profile(db_session: AsyncSession):
    """Test loading context with a complete user profile."""
    # Create user
    user = User(
        id=uuid4(),
        email="contexttest@example.com",
        hashed_password=hash_password("password123"),
        full_name="Context Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level="intermediate",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create fitness goals
    primary_goal = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="muscle_gain",
        target_weight_kg=80.0,
        priority=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(primary_goal)
    
    secondary_goal = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="fat_loss",
        target_body_fat_percentage=15.0,
        priority=2,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(secondary_goal)
    
    # Create lifestyle baseline
    lifestyle = LifestyleBaseline(
        id=uuid4(),
        profile_id=profile.id,
        energy_level=8,  # Should map to "high"
        stress_level=5,
        sleep_quality=7,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(lifestyle)
    
    await db_session.commit()
    
    # Load context
    context = await load_agent_context(db_session, str(user.id), include_history=True)
    
    # Verify context is AgentContext instance
    assert isinstance(context, AgentContext)
    
    # Verify user_id
    assert context.user_id == str(user.id)
    
    # Verify fitness level
    assert context.fitness_level == "intermediate"
    
    # Verify goals
    assert context.primary_goal == "muscle_gain"
    assert context.secondary_goal == "fat_loss"
    
    # Verify energy level mapping (8 -> "high")
    assert context.energy_level == "high"
    
    # Verify plans are dictionaries (placeholders)
    assert isinstance(context.current_workout_plan, dict)
    assert isinstance(context.current_meal_plan, dict)
    
    # Verify conversation history is a list
    assert isinstance(context.conversation_history, list)
    
    # Verify loaded_at timestamp
    assert isinstance(context.loaded_at, datetime)


@pytest.mark.asyncio
async def test_load_agent_context_with_minimal_profile(db_session: AsyncSession):
    """Test loading context with minimal profile data."""
    # Create user
    user = User(
        id=uuid4(),
        email="minimal@example.com",
        hashed_password=hash_password("password123"),
        full_name="Minimal User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile with minimal data
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level=None,  # Not set
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Load context
    context = await load_agent_context(db_session, str(user.id), include_history=False)
    
    # Verify defaults are applied
    assert context.fitness_level == "beginner"  # Default
    assert context.primary_goal == "general_fitness"  # Default
    assert context.secondary_goal is None
    assert context.energy_level == "medium"  # Default
    assert context.conversation_history == []  # Empty because include_history=False


@pytest.mark.asyncio
async def test_load_agent_context_energy_level_mapping(db_session: AsyncSession):
    """Test energy level mapping from 1-10 scale to low/medium/high."""
    # Test low energy (1-3)
    user_low = User(
        id=uuid4(),
        email="energy_low@example.com",
        hashed_password=hash_password("password123"),
        full_name="Energy Low User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user_low)
    
    profile_low = UserProfile(
        id=uuid4(),
        user_id=user_low.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile_low)
    
    lifestyle_low = LifestyleBaseline(
        id=uuid4(),
        profile_id=profile_low.id,
        energy_level=2,
        stress_level=5,
        sleep_quality=5,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(lifestyle_low)
    await db_session.commit()
    
    context = await load_agent_context(db_session, str(user_low.id))
    assert context.energy_level == "low"
    
    # Test medium energy (4-7)
    user_medium = User(
        id=uuid4(),
        email="energy_medium@example.com",
        hashed_password=hash_password("password123"),
        full_name="Energy Medium User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user_medium)
    
    profile_medium = UserProfile(
        id=uuid4(),
        user_id=user_medium.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile_medium)
    
    lifestyle_medium = LifestyleBaseline(
        id=uuid4(),
        profile_id=profile_medium.id,
        energy_level=5,
        stress_level=5,
        sleep_quality=5,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(lifestyle_medium)
    await db_session.commit()
    
    context = await load_agent_context(db_session, str(user_medium.id))
    assert context.energy_level == "medium"
    
    # Test high energy (8-10)
    user_high = User(
        id=uuid4(),
        email="energy_high@example.com",
        hashed_password=hash_password("password123"),
        full_name="Energy High User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user_high)
    
    profile_high = UserProfile(
        id=uuid4(),
        user_id=user_high.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile_high)
    
    lifestyle_high = LifestyleBaseline(
        id=uuid4(),
        profile_id=profile_high.id,
        energy_level=9,
        stress_level=5,
        sleep_quality=5,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(lifestyle_high)
    await db_session.commit()
    
    context = await load_agent_context(db_session, str(user_high.id))
    assert context.energy_level == "high"


@pytest.mark.asyncio
async def test_load_agent_context_missing_user(db_session: AsyncSession):
    """Test error handling when user profile is not found."""
    # Try to load context for non-existent user
    non_existent_user_id = str(uuid4())
    
    with pytest.raises(ValueError) as exc_info:
        await load_agent_context(db_session, non_existent_user_id)
    
    # Verify error message
    assert "User profile not found" in str(exc_info.value)
    assert non_existent_user_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_load_agent_context_invalid_user_id_format(db_session: AsyncSession):
    """Test error handling for invalid user_id format."""
    # Try to load context with invalid UUID format
    invalid_user_id = "not-a-valid-uuid"
    
    with pytest.raises(ValueError) as exc_info:
        await load_agent_context(db_session, invalid_user_id)
    
    # Verify error message
    assert "Invalid user_id format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_load_agent_context_immutability(db_session: AsyncSession):
    """Test that AgentContext is immutable."""
    # Create user and profile
    user = User(
        id=uuid4(),
        email="immutable@example.com",
        hashed_password=hash_password("password123"),
        full_name="Immutable User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Load context
    context = await load_agent_context(db_session, str(user.id))
    
    # Try to modify context (should raise error)
    with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
        context.fitness_level = "advanced"


@pytest.mark.asyncio
async def test_load_agent_context_with_multiple_goals(db_session: AsyncSession):
    """Test loading context with multiple fitness goals sorted by priority."""
    # Create user and profile
    user = User(
        id=uuid4(),
        email="multigoal@example.com",
        hashed_password=hash_password("password123"),
        full_name="Multi Goal User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="advanced",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create goals with different priorities (not in order)
    goal_3 = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="general_fitness",
        priority=3,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(goal_3)
    
    goal_1 = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(goal_1)
    
    goal_2 = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=2,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(goal_2)
    
    await db_session.commit()
    
    # Load context
    context = await load_agent_context(db_session, str(user.id))
    
    # Verify goals are sorted by priority
    assert context.primary_goal == "fat_loss"  # Priority 1
    assert context.secondary_goal == "muscle_gain"  # Priority 2


@pytest.mark.asyncio
async def test_load_agent_context_include_history_parameter(db_session: AsyncSession):
    """Test that include_history parameter controls conversation history loading."""
    # Create user and profile
    user = User(
        id=uuid4(),
        email="history@example.com",
        hashed_password=hash_password("password123"),
        full_name="History User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Load context with include_history=True
    context_with_history = await load_agent_context(db_session, str(user.id), include_history=True)
    assert isinstance(context_with_history.conversation_history, list)
    
    # Load context with include_history=False
    context_without_history = await load_agent_context(db_session, str(user.id), include_history=False)
    assert context_without_history.conversation_history == []


@pytest.mark.asyncio
async def test_load_conversation_history_with_messages(db_session: AsyncSession):
    """Test that conversation history is loaded correctly when messages exist."""
    from app.models.conversation import ConversationMessage
    
    # Create user and profile
    user = User(
        id=uuid4(),
        email="conversation@example.com",
        hashed_password=hash_password("password123"),
        full_name="Conversation User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create conversation messages
    msg1 = ConversationMessage(
        id=uuid4(),
        user_id=user.id,
        role="user",
        content="What's my workout today?",
        agent_type=None,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(msg1)
    
    msg2 = ConversationMessage(
        id=uuid4(),
        user_id=user.id,
        role="assistant",
        content="Today is leg day! Here's your workout...",
        agent_type="workout",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(msg2)
    
    msg3 = ConversationMessage(
        id=uuid4(),
        user_id=user.id,
        role="user",
        content="What should I eat for lunch?",
        agent_type=None,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(msg3)
    
    await db_session.commit()
    
    # Load context with history
    context = await load_agent_context(db_session, str(user.id), include_history=True)
    
    # Verify conversation history is loaded
    assert len(context.conversation_history) == 3
    
    # Verify messages are in chronological order
    assert context.conversation_history[0]["role"] == "user"
    assert context.conversation_history[0]["content"] == "What's my workout today?"
    assert context.conversation_history[0]["agent_type"] is None
    
    assert context.conversation_history[1]["role"] == "assistant"
    assert context.conversation_history[1]["content"] == "Today is leg day! Here's your workout..."
    assert context.conversation_history[1]["agent_type"] == "workout"
    
    assert context.conversation_history[2]["role"] == "user"
    assert context.conversation_history[2]["content"] == "What should I eat for lunch?"
    assert context.conversation_history[2]["agent_type"] is None


@pytest.mark.asyncio
async def test_load_conversation_history_limit(db_session: AsyncSession):
    """Test that conversation history respects the limit parameter."""
    from app.models.conversation import ConversationMessage
    
    # Create user and profile
    user = User(
        id=uuid4(),
        email="historylimit@example.com",
        hashed_password=hash_password("password123"),
        full_name="History Limit User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create 15 conversation messages
    for i in range(15):
        msg = ConversationMessage(
            id=uuid4(),
            user_id=user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            agent_type="general" if i % 2 == 1 else None,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(msg)
    
    await db_session.commit()
    
    # Load context with history (default limit is 10)
    context = await load_agent_context(db_session, str(user.id), include_history=True)
    
    # Verify only last 10 messages are loaded
    assert len(context.conversation_history) == 10
    
    # Verify they are the most recent messages (5-14)
    assert context.conversation_history[0]["content"] == "Message 5"
    assert context.conversation_history[-1]["content"] == "Message 14"



@pytest.mark.asyncio
async def test_load_agent_context_onboarding_mode_parameter(db_session: AsyncSession):
    """Test that onboarding_mode parameter is accepted and logged."""
    # Create user and profile
    user = User(
        id=uuid4(),
        email="onboarding_mode@example.com",
        hashed_password=hash_password("password123"),
        full_name="Onboarding Mode User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Load context with onboarding_mode=True
    context_onboarding = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=True
    )
    assert isinstance(context_onboarding, AgentContext)
    assert context_onboarding.user_id == str(user.id)
    
    # Load context with onboarding_mode=False
    context_post_onboarding = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=False
    )
    assert isinstance(context_post_onboarding, AgentContext)
    assert context_post_onboarding.user_id == str(user.id)


@pytest.mark.asyncio
async def test_load_agent_context_partial_context_during_onboarding(db_session: AsyncSession):
    """Test that partial context is loaded during onboarding."""
    # Create user with incomplete profile (onboarding in progress)
    user = User(
        id=uuid4(),
        email="partial_context@example.com",
        hashed_password=hash_password("password123"),
        full_name="Partial Context User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile that's not locked (onboarding not complete)
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,  # Not locked = onboarding in progress
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Add partial data - only fitness goal, no other preferences yet
    goal = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Load context with onboarding_mode=True
    context = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=True
    )
    
    # Verify partial context is loaded
    assert context.fitness_level == "beginner"
    assert context.primary_goal == "fat_loss"
    assert context.secondary_goal is None
    assert context.energy_level == "medium"  # Default
    
    # Verify plans are empty (not created yet during onboarding)
    assert context.current_workout_plan == {}
    assert context.current_meal_plan == {}


@pytest.mark.asyncio
async def test_load_agent_context_full_context_post_onboarding(db_session: AsyncSession):
    """Test that full context is loaded post-onboarding."""
    # Create user with complete profile (onboarding complete)
    user = User(
        id=uuid4(),
        email="full_context@example.com",
        hashed_password=hash_password("password123"),
        full_name="Full Context User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create locked profile (onboarding complete)
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,  # Locked = onboarding complete
        fitness_level="intermediate",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Add complete data
    primary_goal = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="muscle_gain",
        target_weight_kg=80.0,
        priority=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(primary_goal)
    
    secondary_goal = FitnessGoal(
        id=uuid4(),
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=2,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(secondary_goal)
    
    lifestyle = LifestyleBaseline(
        id=uuid4(),
        profile_id=profile.id,
        energy_level=7,
        stress_level=5,
        sleep_quality=8,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(lifestyle)
    
    await db_session.commit()
    
    # Load context with onboarding_mode=False
    context = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=False
    )
    
    # Verify full context is loaded
    assert context.fitness_level == "intermediate"
    assert context.primary_goal == "muscle_gain"
    assert context.secondary_goal == "fat_loss"
    assert context.energy_level == "medium"
    
    # Plans would be loaded here (currently placeholders)
    assert isinstance(context.current_workout_plan, dict)
    assert isinstance(context.current_meal_plan, dict)


@pytest.mark.asyncio
async def test_load_agent_context_conversation_history_with_onboarding_mode(db_session: AsyncSession):
    """Test that conversation history loading respects onboarding_mode."""
    from app.models.conversation import ConversationMessage
    
    # Create user and profile
    user = User(
        id=uuid4(),
        email="history_onboarding@example.com",
        hashed_password=hash_password("password123"),
        full_name="History Onboarding User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create conversation messages
    msg1 = ConversationMessage(
        id=uuid4(),
        user_id=user.id,
        role="user",
        content="What's my fitness level?",
        agent_type=None,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(msg1)
    
    msg2 = ConversationMessage(
        id=uuid4(),
        user_id=user.id,
        role="assistant",
        content="You're a beginner. Let's start with basics.",
        agent_type="workout",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(msg2)
    
    await db_session.commit()
    
    # Load context during onboarding
    context_onboarding = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=True
    )
    
    # Verify conversation history is loaded
    assert len(context_onboarding.conversation_history) == 2
    assert context_onboarding.conversation_history[0]["role"] == "user"
    assert context_onboarding.conversation_history[1]["role"] == "assistant"
    
    # Load context post-onboarding
    context_post = await load_agent_context(
        db_session, 
        str(user.id), 
        include_history=True,
        onboarding_mode=False
    )
    
    # Verify conversation history is loaded
    assert len(context_post.conversation_history) == 2
    assert context_post.conversation_history[0]["role"] == "user"
    assert context_post.conversation_history[1]["role"] == "assistant"

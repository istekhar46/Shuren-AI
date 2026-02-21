"""
Tests for AgentOrchestrator access control with onboarding mode.

This module tests the access control logic that enforces:
- During onboarding: specialized agents allowed, reject if completed
- Post-onboarding: only general agent allowed, reject if not completed
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile
from app.models.preferences import FitnessGoal
from app.core.security import hash_password


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_with_incomplete_user(db_session: AsyncSession):
    """Test onboarding_mode=True with incomplete user allows specialized agents."""
    # Create a fresh user without using test_user fixture to avoid conflicts
    user = User(
        id=uuid4(),
        email="incomplete@test.com",
        hashed_password=hash_password("password123"),
        full_name="Incomplete User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=2,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create minimal profile for context loading
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal for context (using profile_id - must be after profile commit)
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow specialized agent during onboarding
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="I want to build muscle",
        agent_type=AgentType.WORKOUT,
        onboarding_mode=True
    )
    
    assert response is not None
    assert response.agent_type == AgentType.WORKOUT.value


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_with_completed_user_fails(db_session: AsyncSession):
    """Test onboarding_mode=True with completed user raises error."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="completed@test.com",
        hashed_password=hash_password("password123"),
        full_name="Completed User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create completed onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=9,
        is_complete=True,
        step_data={
            "step_1": {"fitness_level": "beginner"},
            "step_2": {"goals": [{"goal_type": "fat_loss"}]},
            "step_3": {"equipment": ["dumbbells"], "injuries": [], "limitations": []},
            "step_4": {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
            "step_5": {"daily_calorie_target": 2000, "protein_percentage": 30, "carbs_percentage": 40, "fats_percentage": 30},
            "step_6": {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00"}]},
            "step_7": {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00"}]},
            "step_8": {"daily_water_target_ml": 2000, "reminder_frequency_minutes": 60},
            "step_9": {"interested_in_supplements": False}
        }
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject onboarding mode for completed user
    with pytest.raises(ValueError, match="Onboarding already completed"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="I want to build muscle",
            agent_type=AgentType.WORKOUT,
            onboarding_mode=True
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normal_mode_with_incomplete_user_fails(db_session: AsyncSession):
    """Test onboarding_mode=False with incomplete user raises error."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="incomplete2@test.com",
        hashed_password=hash_password("password123"),
        full_name="Incomplete User 2",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=2,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject normal mode for incomplete user
    with pytest.raises(ValueError, match="Complete onboarding first"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="What should I eat today?",
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normal_mode_with_completed_user_forces_general_agent(
    db_session: AsyncSession, 
    completed_onboarding_user: tuple
):
    """Test onboarding_mode=False with completed user allows only general agent."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow general agent without explicit agent_type
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="What should I eat today?",
        onboarding_mode=False
    )
    
    # Should be forced to general agent
    assert response is not None
    assert response.agent_type == AgentType.GENERAL.value


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normal_mode_explicit_non_general_agent_fails(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test explicit non-general agent request fails post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject explicit non-general agent
    with pytest.raises(ValueError, match="Specialized agent .* is not available after onboarding completion"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="Create a workout plan",
            agent_type=AgentType.WORKOUT,
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_metadata_included(db_session: AsyncSession):
    """Test that onboarding_mode is included in response metadata."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="metadata@test.com",
        hashed_password=hash_password("password123"),
        full_name="Metadata User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=1,
        is_complete=False,
        step_data={}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal (using profile_id - must be after profile commit)
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Test with onboarding_mode=True
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="I'm a beginner",
        agent_type=AgentType.WORKOUT,
        onboarding_mode=True
    )
    
    assert response.metadata is not None
    assert "onboarding_mode" in response.metadata
    assert response.metadata["onboarding_mode"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normal_mode_metadata_included(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that onboarding_mode=False is included in response metadata."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Test with onboarding_mode=False
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="What should I do today?",
        onboarding_mode=False
    )
    
    assert response.metadata is not None
    assert "onboarding_mode" in response.metadata
    assert response.metadata["onboarding_mode"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_voice_mode_includes_onboarding_metadata(db_session: AsyncSession):
    """Test that voice mode includes onboarding_mode in metadata."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="voice@test.com",
        hashed_password=hash_password("password123"),
        full_name="Voice User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=1,
        is_complete=False,
        step_data={}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal (using profile_id - must be after profile commit)
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator in voice mode
    orchestrator = AgentOrchestrator(db_session=db_session, mode="voice")
    
    # Test voice mode with onboarding
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="I'm a beginner",
        agent_type=AgentType.WORKOUT,
        voice_mode=True,
        onboarding_mode=True
    )
    
    assert response.metadata is not None
    assert "onboarding_mode" in response.metadata
    assert response.metadata["onboarding_mode"] is True
    assert response.metadata["mode"] == "voice"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_blocks_general_agent(db_session: AsyncSession):
    """Test that general agent is blocked during onboarding."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="block_general@test.com",
        hashed_password=hash_password("password123"),
        full_name="Block General User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=2,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject general agent during onboarding
    with pytest.raises(ValueError, match="General agent is not available during onboarding"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="What should I do?",
            agent_type=AgentType.GENERAL,
            onboarding_mode=True
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_blocks_tracker_agent(db_session: AsyncSession):
    """Test that tracker agent is blocked during onboarding."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="block_tracker@test.com",
        hashed_password=hash_password("password123"),
        full_name="Block Tracker User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=2,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject tracker agent during onboarding
    with pytest.raises(ValueError, match="Tracker agent is not available during onboarding"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="Track my progress",
            agent_type=AgentType.TRACKER,
            onboarding_mode=True
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_onboarding_allows_general_agent(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that general agent is allowed post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow general agent explicitly
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="What should I do today?",
        agent_type=AgentType.GENERAL,
        onboarding_mode=False
    )
    
    assert response is not None
    assert response.agent_type == AgentType.GENERAL.value


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_onboarding_blocks_workout_agent(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that workout agent is blocked post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject workout agent
    with pytest.raises(ValueError, match="Specialized agent 'workout' is not available after onboarding completion"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="Create a workout plan",
            agent_type=AgentType.WORKOUT,
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_onboarding_blocks_diet_agent(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that diet agent is blocked post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject diet agent
    with pytest.raises(ValueError, match="Specialized agent 'diet' is not available after onboarding completion"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="Create a meal plan",
            agent_type=AgentType.DIET,
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_onboarding_blocks_scheduler_agent(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that scheduler agent is blocked post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject scheduler agent
    with pytest.raises(ValueError, match="Specialized agent 'scheduler' is not available after onboarding completion"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="Schedule my workouts",
            agent_type=AgentType.SCHEDULER,
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_onboarding_blocks_supplement_agent(
    db_session: AsyncSession,
    completed_onboarding_user: tuple
):
    """Test that supplement agent is blocked post-onboarding."""
    user, profile = completed_onboarding_user
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should reject supplement agent
    with pytest.raises(ValueError, match="Specialized agent 'supplement' is not available after onboarding completion"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="What supplements should I take?",
            agent_type=AgentType.SUPPLEMENT,
            onboarding_mode=False
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_missing_onboarding_state_raises_error(db_session: AsyncSession):
    """Test that missing onboarding state raises error."""
    # Create a user without onboarding state
    user = User(
        id=uuid4(),
        email="no_onboarding@test.com",
        hashed_password=hash_password("password123"),
        full_name="No Onboarding User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile but NO onboarding state
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should raise error about missing onboarding state
    with pytest.raises(ValueError, match="Onboarding state not found for user"):
        await orchestrator.route_query(
            user_id=str(user.id),
            query="What should I do?",
            onboarding_mode=True
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_allows_diet_agent(db_session: AsyncSession):
    """Test that diet agent is allowed during onboarding."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="diet_onboarding@test.com",
        hashed_password=hash_password("password123"),
        full_name="Diet Onboarding User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=4,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow diet agent during onboarding
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="What should I eat?",
        agent_type=AgentType.DIET,
        onboarding_mode=True
    )
    
    assert response is not None
    assert response.agent_type == AgentType.DIET.value


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_allows_scheduler_agent(db_session: AsyncSession):
    """Test that scheduler agent is allowed during onboarding."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="scheduler_onboarding@test.com",
        hashed_password=hash_password("password123"),
        full_name="Scheduler Onboarding User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=6,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow scheduler agent during onboarding
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="When should I workout?",
        agent_type=AgentType.SCHEDULER,
        onboarding_mode=True
    )
    
    assert response is not None
    assert response.agent_type == AgentType.SCHEDULER.value


@pytest.mark.asyncio
@pytest.mark.unit
async def test_onboarding_mode_allows_supplement_agent(db_session: AsyncSession):
    """Test that supplement agent is allowed during onboarding."""
    # Create a fresh user
    user = User(
        id=uuid4(),
        email="supplement_onboarding@test.com",
        hashed_password=hash_password("password123"),
        full_name="Supplement Onboarding User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create incomplete onboarding state
    onboarding_state = OnboardingState(
        user_id=user.id,
        current_step=9,
        is_complete=False,
        step_data={"step_1": {"fitness_level": "beginner"}}
    )
    db_session.add(onboarding_state)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    # Add fitness goal
    goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(goal)
    
    await db_session.commit()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    # Should allow supplement agent during onboarding
    response = await orchestrator.route_query(
        user_id=str(user.id),
        query="Should I take supplements?",
        agent_type=AgentType.SUPPLEMENT,
        onboarding_mode=True
    )
    
    assert response is not None
    assert response.agent_type == AgentType.SUPPLEMENT.value

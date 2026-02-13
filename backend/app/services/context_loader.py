"""Context loader service for loading user data into AgentContext.

This module provides functionality to load user profile data from the database
and assemble it into an immutable AgentContext object for agent interactions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.context import AgentContext
from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    PhysicalConstraint,
    DietaryPreference,
    MealPlan,
    MealSchedule,
    WorkoutSchedule,
    HydrationPreference,
    LifestyleBaseline,
)
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


async def load_agent_context(
    db: AsyncSession,
    user_id: str,
    include_history: bool = True,
    onboarding_mode: bool = False
) -> AgentContext:
    """
    Load user data from database and assemble into AgentContext.
    
    This function queries the user's profile and related data from the database,
    then assembles it into an immutable AgentContext object for agent interactions.
    
    Context Loading Behavior:
    - During onboarding (onboarding_mode=True): Loads partial context with what's
      been collected so far. Profile may not be complete or locked yet.
    - Post-onboarding (onboarding_mode=False): Loads full context including all
      preferences, plans, and tracking data.
    
    Args:
        db: Async database session
        user_id: User's unique identifier (UUID as string)
        include_history: Whether to load conversation history (default: True)
        onboarding_mode: Whether this is during onboarding (default: False)
    
    Returns:
        AgentContext: Immutable context object with all user data
    
    Raises:
        ValueError: If user profile not found in database
    
    Example:
        >>> # During onboarding - partial context
        >>> context = await load_agent_context(db, "user-123", onboarding_mode=True)
        >>> 
        >>> # Post-onboarding - full context
        >>> context = await load_agent_context(db, "user-123", onboarding_mode=False)
        >>> print(context.fitness_level)
        'beginner'
    """
    # Convert user_id string to UUID for database query
    try:
        user_uuid = UUID(user_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid user_id format: {user_id}") from e
    
    # Query UserProfile with eager loading of relationships
    # During onboarding, profile may not exist yet or may be incomplete
    stmt = (
        select(UserProfile)
        .where(UserProfile.user_id == user_uuid)
        .where(UserProfile.deleted_at.is_(None))
        .options(
            selectinload(UserProfile.fitness_goals),
            selectinload(UserProfile.meal_plan),
            selectinload(UserProfile.dietary_preferences),
            selectinload(UserProfile.lifestyle_baseline),
        )
    )
    
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    # Raise error if profile not found
    if not profile:
        raise ValueError(f"User profile not found: {user_id}")
    
    # Log context loading mode
    logger.debug(
        f"Loading context for user {user_id}: "
        f"onboarding_mode={onboarding_mode}, "
        f"profile_locked={profile.is_locked}"
    )
    
    # Extract fitness level (default to 'beginner' if not set)
    fitness_level = profile.fitness_level or "beginner"
    
    # Extract primary and secondary goals from fitness_goals
    primary_goal = None
    secondary_goal = None
    
    if profile.fitness_goals:
        # Sort by priority to get primary and secondary goals
        sorted_goals = sorted(profile.fitness_goals, key=lambda g: g.priority)
        if len(sorted_goals) > 0:
            primary_goal = sorted_goals[0].goal_type
        if len(sorted_goals) > 1:
            secondary_goal = sorted_goals[1].goal_type
    
    # Default primary goal if not set
    if not primary_goal:
        primary_goal = "general_fitness"
    
    # Extract energy level from lifestyle baseline
    energy_level = "medium"  # Default
    if profile.lifestyle_baseline and profile.lifestyle_baseline.energy_level:
        # Convert 1-10 scale to low/medium/high
        energy_value = profile.lifestyle_baseline.energy_level
        if energy_value <= 3:
            energy_level = "low"
        elif energy_value <= 7:
            energy_level = "medium"
        else:
            energy_level = "high"
    
    # Load current workout plan (placeholder for Sub-Doc 2)
    current_workout_plan = await _load_current_workout(db, user_uuid)
    
    # Load current meal plan (placeholder for Sub-Doc 2)
    current_meal_plan = await _load_current_meal(db, user_uuid)
    
    # Load conversation history
    # During onboarding: Load onboarding-specific conversation history
    # Post-onboarding: Load full conversation history
    conversation_history = []
    if include_history:
        conversation_history = await _load_conversation_history(
            db, 
            user_uuid,
            onboarding_mode=onboarding_mode
        )
    
    # Build and return AgentContext
    context = AgentContext(
        user_id=user_id,
        fitness_level=fitness_level,
        primary_goal=primary_goal,
        secondary_goal=secondary_goal,
        energy_level=energy_level,
        current_workout_plan=current_workout_plan,
        current_meal_plan=current_meal_plan,
        conversation_history=conversation_history,
        loaded_at=datetime.utcnow()
    )
    
    logger.info(
        f"Loaded context for user {user_id}: "
        f"onboarding_mode={onboarding_mode}, "
        f"fitness_level={fitness_level}, "
        f"primary_goal={primary_goal}, "
        f"history_messages={len(conversation_history)}"
    )
    
    return context



async def _load_current_workout(db: AsyncSession, user_uuid: UUID) -> Dict:
    """
    Load current workout plan for user (placeholder).
    
    TODO: Implement in Sub-Doc 2 (Specialized Agents)
    This will load the user's active workout plan with exercises,
    sets, reps, and progression tracking.
    
    Args:
        db: Async database session
        user_uuid: User's UUID
    
    Returns:
        Dict: Workout plan data (currently empty placeholder)
    """
    # Placeholder implementation
    return {}


async def _load_current_meal(db: AsyncSession, user_uuid: UUID) -> Dict:
    """
    Load current meal plan for user (placeholder).
    
    TODO: Implement in Sub-Doc 2 (Specialized Agents)
    This will load the user's active meal plan with meals,
    recipes, and nutritional information.
    
    Args:
        db: Async database session
        user_uuid: User's UUID
    
    Returns:
        Dict: Meal plan data (currently empty placeholder)
    """
    # Placeholder implementation
    return {}


async def _load_conversation_history(
    db: AsyncSession,
    user_uuid: UUID,
    limit: int = 10,
    onboarding_mode: bool = False
) -> List[Dict]:
    """
    Load recent conversation history for user.
    
    Queries the conversation_messages table to retrieve the most recent
    messages for context in agent interactions. Messages are returned
    in chronological order (oldest to newest).
    
    During onboarding, this loads onboarding-specific conversation history.
    Post-onboarding, this loads the full conversation history.
    
    Args:
        db: Async database session
        user_uuid: User's UUID
        limit: Maximum number of messages to load (default: 10)
        onboarding_mode: Whether this is during onboarding (default: False)
    
    Returns:
        List[Dict]: Conversation messages in chronological order, each with:
            - role: "user" or "assistant"
            - content: Message text
            - agent_type: Agent that handled the message (None for user messages)
    """
    from app.models.conversation import ConversationMessage
    
    # Query conversation_messages table
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.user_id == user_uuid)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Reverse to chronological order and format
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "agent_type": msg.agent_type
        }
        for msg in reversed(messages)
    ]

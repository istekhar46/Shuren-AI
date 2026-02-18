"""
Onboarding endpoints for managing user onboarding flow.

This module provides REST API endpoints for:
- Retrieving current onboarding state
- Submitting onboarding step data
- Completing onboarding and creating user profile
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    OnboardingCompleteResponse,
    OnboardingProgressResponse,
    OnboardingStateResponse,
    OnboardingStepRequest,
    OnboardingStepResponse,
    CurrentAgentResponse
)
from app.schemas.profile import UserProfileResponse
from app.services.onboarding_service import OnboardingService, OnboardingValidationError


router = APIRouter()


@router.get("/progress", response_model=OnboardingProgressResponse, status_code=status.HTTP_200_OK)
async def get_onboarding_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingProgressResponse:
    """
    Get rich onboarding progress metadata for UI indicators.
    
    Provides detailed progress information including current state,
    completed states, state metadata, and completion percentage.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        OnboardingProgressResponse with current state, completed states,
        state metadata, completion percentage, and can_complete flag
        
    Raises:
        HTTPException(404): If onboarding state not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Get progress
    try:
        progress = await onboarding_service.get_progress(current_user.id)
    except OnboardingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    return OnboardingProgressResponse(
        current_state=progress.current_state,
        total_states=progress.total_states,
        completed_states=progress.completed_states,
        current_state_info=progress.current_state_info,
        next_state_info=progress.next_state_info,
        is_complete=progress.is_complete,
        completion_percentage=progress.completion_percentage,
        can_complete=progress.can_complete
    )


@router.get("/state", response_model=OnboardingStateResponse, status_code=status.HTTP_200_OK)
async def get_onboarding_state(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingStateResponse:
    """
    Get current onboarding state for authenticated user.
    
    Retrieves the user's current progress through the onboarding flow,
    including current step number, completion status, and all saved step data.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        OnboardingStateResponse with id, user_id, current_step, is_complete, step_data
        
    Raises:
        HTTPException(404): If onboarding state not found
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Get onboarding state
    onboarding_state = await onboarding_service.get_onboarding_state(current_user.id)
    
    if not onboarding_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding state not found"
        )
    
    return OnboardingStateResponse(
        id=str(onboarding_state.id),
        user_id=str(onboarding_state.user_id),
        current_step=onboarding_state.current_step,
        is_complete=onboarding_state.is_complete,
        step_data=onboarding_state.step_data or {}
    )


@router.post("/step", response_model=OnboardingStepResponse, status_code=status.HTTP_200_OK)
async def save_onboarding_step(
    step_request: OnboardingStepRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_agent_context: Annotated[str | None, Header(alias="X-Agent-Context")] = None
) -> OnboardingStepResponse:
    """
    Save onboarding step data with validation.
    
    Validates step data according to step-specific requirements,
    saves to the onboarding state, and advances the current step.
    Optionally logs agent context for debugging and analytics.
    
    Args:
        step_request: OnboardingStepRequest with step number and data
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        x_agent_context: Optional agent context from X-Agent-Context header
        
    Returns:
        OnboardingStepResponse with current_step, is_complete, message, and next_state_info
        
    Raises:
        HTTPException(400): If step data is invalid (includes field information)
        HTTPException(422): If request validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    import logging
    from app.services.onboarding_service import STATE_METADATA
    
    logger = logging.getLogger(__name__)
    
    # Log agent context if provided
    if x_agent_context:
        logger.info(
            f"Onboarding step {step_request.step} called by agent: {x_agent_context}",
            extra={
                "user_id": str(current_user.id),
                "agent": x_agent_context,
                "step": step_request.step
            }
        )
    
    # Initialize onboarding service
    onboarding_service = OnboardingService(db)
    
    # Save onboarding step with validation
    try:
        onboarding_state = await onboarding_service.save_onboarding_step(
            user_id=current_user.id,
            step=step_request.step,
            data=step_request.data,
            agent_type=x_agent_context  # Pass agent context for history tracking
        )
    except OnboardingValidationError as e:
        # Return structured validation error with field information
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "field": e.field if hasattr(e, 'field') else None,
                "error_code": "VALIDATION_ERROR"
            }
        )
    
    # Get next state info
    next_state = step_request.step + 1 if step_request.step < 9 else None
    next_state_info = STATE_METADATA.get(next_state) if next_state else None
    
    return OnboardingStepResponse(
        current_step=onboarding_state.current_step,
        is_complete=onboarding_state.is_complete,
        message=f"Step {step_request.step} saved successfully",
        next_state=next_state,
        next_state_info=next_state_info
    )


@router.post("/complete", response_model=OnboardingCompleteResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingCompleteResponse:
    """
    Complete onboarding and create locked user profile from agent_context.
    
    This endpoint:
    1. Loads the user's OnboardingState
    2. Checks if onboarding is already complete (returns 409 if true)
    3. Verifies all required agent data is present in agent_context
    4. Creates UserProfile with all related entities using ProfileCreationService
    5. Marks onboarding as complete (is_complete=True)
    6. Sets current_agent to "general_assistant"
    7. Returns profile information
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        OnboardingCompleteResponse with profile_id, user_id, fitness_level,
        is_locked, onboarding_complete, and success message
        
    Raises:
        HTTPException(400): If agent data is missing or incomplete
        HTTPException(401): If authentication fails (handled by dependency)
        HTTPException(409): If onboarding is already complete
        HTTPException(422): If data validation fails
        HTTPException(500): If database error occurs
    """
    import logging
    from sqlalchemy import select, update
    from sqlalchemy.exc import SQLAlchemyError
    from pydantic import ValidationError
    
    from app.models.onboarding import OnboardingState
    from app.services.profile_creation_service import ProfileCreationService
    from app.services.onboarding_completion import OnboardingIncompleteError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load onboarding state
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == current_user.id
        )
        result = await db.execute(stmt)
        onboarding_state = result.scalars().first()
        
        if not onboarding_state:
            logger.error(f"Onboarding state not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding state not found"
            )
        
        # Check if onboarding already complete
        if onboarding_state.is_complete:
            logger.warning(f"Onboarding already complete for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Onboarding has already been completed for this user"
            )
        
        # Create profile from agent_context
        profile_service = ProfileCreationService(db)
        
        try:
            profile = await profile_service.create_profile_from_agent_context(
                user_id=current_user.id,
                agent_context=onboarding_state.agent_context or {}
            )
        except OnboardingIncompleteError as e:
            # Agent data is missing or incomplete
            logger.error(f"Onboarding incomplete for user {current_user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Onboarding data incomplete: {str(e)}"
            )
        except ValueError as e:
            # Data validation failed
            logger.error(f"Validation error for user {current_user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data validation failed: {str(e)}"
            )
        except SQLAlchemyError as e:
            # Database error
            logger.error(f"Database error for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating your profile. Please try again."
            )
        
        # Mark onboarding as complete
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == current_user.id)
            .values(
                is_complete=True,
                current_agent="general_assistant"
            )
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Onboarding completed successfully for user {current_user.id}")
        
        # Return success response
        return OnboardingCompleteResponse(
            profile_id=str(profile.id),
            user_id=str(current_user.id),
            fitness_level=profile.fitness_level,
            is_locked=profile.is_locked,
            onboarding_complete=True,
            message="Onboarding completed successfully! Your personalized fitness profile is ready."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error completing onboarding for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )



@router.post("/chat", response_model=OnboardingChatResponse, status_code=status.HTTP_200_OK)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingChatResponse:
    """
    Chat with the current onboarding agent.
    
    The agent is determined by the user's current onboarding step.
    The agent has access to all previous context from earlier steps.
    
    Args:
        request: Chat request with user message
        current_user: Authenticated user from JWT
        db: Database session
        
    Returns:
        OnboardingChatResponse with agent's reply
        
    Raises:
        HTTPException(401): If authentication fails (handled by dependency)
        HTTPException(404): If user not found or onboarding state not found
        HTTPException(422): If request validation fails (handled by FastAPI)
        HTTPException(500): On internal errors
    """
    import logging
    from datetime import datetime, timezone
    from sqlalchemy import select, update
    from app.models.onboarding import OnboardingState
    from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create orchestrator
        orchestrator = OnboardingAgentOrchestrator(db)
        
        # Get current agent
        try:
            agent = await orchestrator.get_current_agent(current_user.id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        # Process message
        response = await agent.process_message(
            message=request.message,
            user_id=current_user.id
        )
        
        # Load onboarding state to append to conversation history
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == current_user.id
        )
        result = await db.execute(stmt)
        state = result.scalars().first()
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding state not found"
            )
        
        # Append to conversation history
        conversation_history = state.conversation_history or []
        
        # Add user message
        conversation_history.append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Add agent response
        conversation_history.append({
            "role": "assistant",
            "content": response.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_type": response.agent_type
        })
        
        # Update conversation history in database
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == current_user.id)
            .values(conversation_history=conversation_history)
        )
        await db.execute(stmt)
        await db.commit()
        
        # Return response
        return OnboardingChatResponse(
            message=response.message,
            agent_type=response.agent_type,
            current_step=state.current_step,
            step_complete=response.step_complete,
            next_action=response.next_action
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in chat_onboarding: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your message"
        )



@router.get("/current-agent", response_model=CurrentAgentResponse, status_code=status.HTTP_200_OK)
async def get_current_agent(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CurrentAgentResponse:
    """
    Get information about the current onboarding agent.
    
    Returns agent type, step number, and context summary to help
    the client display appropriate UI.
    
    Args:
        current_user: Authenticated user from JWT
        db: Database session
        
    Returns:
        CurrentAgentResponse with agent info
        
    Raises:
        HTTPException(401): If authentication fails (handled by dependency)
        HTTPException(404): If user not found or onboarding state not found
        HTTPException(500): On internal errors
    """
    import logging
    from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
    from app.schemas.onboarding import OnboardingAgentType
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create orchestrator
        orchestrator = OnboardingAgentOrchestrator(db)
        
        # Load state
        state = await orchestrator._load_onboarding_state(current_user.id)
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding state not found"
            )
        
        # Determine agent type
        try:
            agent_type = orchestrator._step_to_agent(state.current_step)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        # Get agent description
        agent_descriptions = {
            OnboardingAgentType.FITNESS_ASSESSMENT: "I'll help assess your current fitness level",
            OnboardingAgentType.GOAL_SETTING: "Let's define your fitness goals",
            OnboardingAgentType.WORKOUT_PLANNING: "I'll create your personalized workout plan",
            OnboardingAgentType.DIET_PLANNING: "Let's build your meal plan",
            OnboardingAgentType.SCHEDULING: "We'll set up your daily schedule"
        }
        
        return CurrentAgentResponse(
            agent_type=agent_type.value,
            current_step=state.current_step,
            agent_description=agent_descriptions[agent_type],
            context_summary=state.agent_context or {}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in get_current_agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred retrieving agent information"
        )

"""Common onboarding function tools for agents."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_service import OnboardingService, OnboardingValidationError

logger = logging.getLogger(__name__)


async def call_onboarding_step(
    db: AsyncSession,
    user_id: UUID,
    step: int,
    data: dict[str, Any],
    agent_type: str
) -> dict[str, Any]:
    """Internal helper to save onboarding step data.
    
    This function wraps the OnboardingService.save_onboarding_step method
    and provides structured error handling for agent function tools.
    
    Args:
        db: Database session
        user_id: User's UUID
        step: Step number (1-9)
        data: Step data to save
        agent_type: Agent type calling this function (for logging)
    
    Returns:
        Success/error response dict with the following structure:
        - success (bool): Whether the operation succeeded
        - message (str): Success message (if success=True)
        - current_state (int): Current onboarding state (if success=True)
        - next_state (int|None): Next state number or None if complete (if success=True)
        - error (str): Error message (if success=False)
        - field (str): Field that caused validation error (if success=False)
        - error_code (str): Error code for categorization (if success=False)
    """
    try:
        # Log agent context
        logger.info(
            f"Agent {agent_type} saving onboarding step {step}",
            extra={"user_id": str(user_id), "agent": agent_type, "step": step}
        )
        
        # Save step using service (pass agent_type for history tracking)
        service = OnboardingService(db)
        state = await service.save_onboarding_step(
            user_id=user_id,
            step=step,
            data=data,
            agent_type=agent_type
        )
        
        # Return success response
        next_state = step + 1 if step < 9 else None
        return {
            "success": True,
            "message": f"State {step} saved successfully",
            "current_state": state.current_step,
            "next_state": next_state
        }
        
    except OnboardingValidationError as e:
        # Return validation error in agent-friendly format
        logger.warning(
            f"Validation error in step {step}: {e.message}",
            extra={"user_id": str(user_id), "agent": agent_type, "field": e.field}
        )
        return {
            "success": False,
            "error": e.message,
            "field": e.field,
            "error_code": "VALIDATION_ERROR"
        }
    
    except Exception as e:
        # Return unexpected error
        logger.error(
            f"Unexpected error saving step {step}: {e}",
            extra={"user_id": str(user_id), "agent": agent_type},
            exc_info=True
        )
        return {
            "success": False,
            "error": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        }

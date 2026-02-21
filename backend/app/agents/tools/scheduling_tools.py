"""
Scheduling Agent tools for saving workout, meal, and hydration schedules.

This module provides LangChain tools for the Scheduling Agent to save
schedule data to the agent_context in OnboardingState.
"""

import logging
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from langchain.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingState
from app.utils.schedule_validation import (
    validate_day_name,
    validate_time_format,
    validate_time_range,
    validate_meal_spacing,
    validate_meal_ordering
)

logger = logging.getLogger(__name__)


def create_scheduling_tools(db: AsyncSession, user_id: UUID) -> List:
    """
    Create scheduling tools bound to a specific database session and user.
    
    Args:
        db: Database session
        user_id: User ID for saving schedule data
        
    Returns:
        List of LangChain tools for scheduling (hydration and supplements only)
    """
    
    @tool
    async def save_hydration_preferences(
        frequency_hours: int,
        target_ml: int
    ) -> dict:
        """
        Save hydration preferences to agent context.
        
        Call this tool when you have collected the user's hydration reminder
        preferences. The preferences will be saved to the agent context for
        later use in profile creation.
        
        Args:
            frequency_hours: Reminder frequency in hours (1-4)
                            How often to remind the user to drink water
            target_ml: Daily water target in milliliters (1500-5000)
                      Total amount of water to drink per day
                      
        Returns:
            Dict with status and message
            
        Example:
            save_hydration_preferences(
                frequency_hours=2,
                target_ml=3000
            )
        """
        # Validate frequency_hours
        if not isinstance(frequency_hours, int):
            return {
                "status": "error",
                "message": "frequency_hours must be an integer"
            }
        
        if not (1 <= frequency_hours <= 4):
            return {
                "status": "error",
                "message": f"frequency_hours must be between 1 and 4, got {frequency_hours}"
            }
        
        # Validate target_ml
        if not isinstance(target_ml, int):
            return {
                "status": "error",
                "message": "target_ml must be an integer"
            }
        
        if not (1500 <= target_ml <= 5000):
            return {
                "status": "error",
                "message": f"target_ml must be between 1500 and 5000, got {target_ml}"
            }
        
        # Load OnboardingState
        try:
            stmt = select(OnboardingState).where(OnboardingState.user_id == user_id)
            result = await db.execute(stmt)
            state = result.scalars().first()
            
            if not state:
                return {
                    "status": "error",
                    "message": "Onboarding state not found"
                }
            
            # Initialize agent_context if needed
            if not state.agent_context:
                state.agent_context = {}
            
            # Initialize scheduling section if needed
            if "scheduling" not in state.agent_context:
                state.agent_context["scheduling"] = {}
            
            # Save hydration preferences
            state.agent_context["scheduling"]["hydration"] = {
                "frequency_hours": frequency_hours,
                "target_ml": target_ml,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Mark as modified for SQLAlchemy to detect change
            state.agent_context = dict(state.agent_context)
            
            await db.commit()
            await db.refresh(state)
            
            logger.info(
                f"Saved hydration preferences for user {user_id}: {target_ml}ml every {frequency_hours}h",
                extra={"user_id": str(user_id), "frequency_hours": frequency_hours, "target_ml": target_ml}
            )
            
            return {
                "status": "success",
                "message": f"Hydration preferences saved successfully: {target_ml}ml daily target with reminders every {frequency_hours} hours"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error saving hydration preferences for user {user_id}: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "message": "Failed to save hydration preferences. Please try again."
            }
    
    @tool
    async def save_supplement_preferences(
        interested: bool,
        current_supplements: List[str] = None
    ) -> dict:
        """
        Save supplement preferences to agent context.
        
        Call this tool when you have collected the user's interest in supplements
        and any current supplements they're taking. This is informational only -
        no supplement prescriptions or recommendations are made.
        
        Args:
            interested: Whether user is interested in learning about supplements
            current_supplements: Optional list of supplements currently taking
                                (e.g., ["protein powder", "creatine", "multivitamin"])
                                
        Returns:
            Dict with status and message
            
        Example:
            save_supplement_preferences(
                interested=True,
                current_supplements=["protein powder", "multivitamin"]
            )
        """
        # Validate interested
        if not isinstance(interested, bool):
            return {
                "status": "error",
                "message": "interested must be a boolean (True or False)"
            }
        
        # Validate current_supplements if provided
        if current_supplements is not None:
            if not isinstance(current_supplements, list):
                return {
                    "status": "error",
                    "message": "current_supplements must be a list or None"
                }
            
            # Validate each supplement is a string
            for supplement in current_supplements:
                if not isinstance(supplement, str):
                    return {
                        "status": "error",
                        "message": "Each supplement must be a string"
                    }
        
        # Load OnboardingState
        try:
            from sqlalchemy import update
            
            # Prepare supplement data
            supplement_data = {
                "interested": interested,
                "current_supplements": current_supplements or [],
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Update onboarding state with supplement preferences and mark step 4 complete
            stmt = (
                update(OnboardingState)
                .where(OnboardingState.user_id == user_id)
                .values(
                    agent_context=OnboardingState.agent_context.op('||')(
                        {"scheduling": {"supplements": supplement_data}}
                    ),
                    step_4_complete=True
                )
            )
            await db.execute(stmt)
            await db.commit()
            
            logger.info(
                f"Saved supplement preferences for user {user_id}: interested={interested}, "
                f"current={len(current_supplements or [])} supplements",
                extra={
                    "user_id": str(user_id),
                    "interested": interested,
                    "current_supplements": current_supplements
                }
            )
            
            return {
                "status": "success",
                "message": "Supplement preferences saved successfully. Onboarding complete!"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error saving supplement preferences for user {user_id}: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "message": "Failed to save supplement preferences. Please try again."
            }
    
    return [save_hydration_preferences, save_supplement_preferences]

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
        List of LangChain tools for scheduling
    """
    
    @tool
    async def save_workout_schedule(
        days: List[str],
        times: List[str]
    ) -> dict:
        """
        Save workout schedule to agent context.
        
        Call this tool when you have collected the user's preferred workout days
        and times. The schedule will be saved to the agent context for later use
        in profile creation.
        
        Args:
            days: List of day names (e.g., ["Monday", "Wednesday", "Friday"])
                  Valid days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
            times: List of times in HH:MM format (e.g., ["07:00", "07:00", "18:00"])
                   Times must be in 24-hour format with leading zeros
                   
        Returns:
            Dict with status and message
            
        Example:
            save_workout_schedule(
                days=["Monday", "Wednesday", "Friday"],
                times=["07:00", "07:00", "18:00"]
            )
        """
        # Validate days list
        if not days or not isinstance(days, list):
            return {
                "status": "error",
                "message": "days must be a non-empty list"
            }
        
        # Validate times list
        if not times or not isinstance(times, list):
            return {
                "status": "error",
                "message": "times must be a non-empty list"
            }
        
        # Validate lengths match
        if len(days) != len(times):
            return {
                "status": "error",
                "message": f"Length mismatch: days has {len(days)} items but times has {len(times)} items"
            }
        
        # Validate each day name
        for day in days:
            if not validate_day_name(day):
                return {
                    "status": "error",
                    "message": f"Invalid day name: {day}. Valid days are: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
                }
        
        # Validate each time format and range
        for time_str in times:
            if not validate_time_format(time_str):
                return {
                    "status": "error",
                    "message": f"Invalid time format: {time_str}. Time must be in HH:MM format (e.g., 07:00, 18:30)"
                }
            
            if not validate_time_range(time_str):
                return {
                    "status": "error",
                    "message": f"Invalid time range: {time_str}. Time must be between 00:00 and 23:59"
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
            
            # Save workout schedule
            state.agent_context["scheduling"]["workout_schedule"] = {
                "days": days,
                "times": times,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Mark as modified for SQLAlchemy to detect change
            state.agent_context = dict(state.agent_context)
            
            await db.commit()
            await db.refresh(state)
            
            logger.info(
                f"Saved workout schedule for user {user_id}: {len(days)} days",
                extra={"user_id": str(user_id), "days": days, "times": times}
            )
            
            return {
                "status": "success",
                "message": f"Workout schedule saved successfully: {len(days)} workout days per week"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error saving workout schedule for user {user_id}: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "message": "Failed to save workout schedule. Please try again."
            }
    
    @tool
    async def save_meal_schedule(
        meal_times: Dict[str, str]
    ) -> dict:
        """
        Save meal schedule to agent context.
        
        Call this tool when you have collected the user's preferred meal timing.
        The schedule will be saved to the agent context for later use in profile creation.
        
        Args:
            meal_times: Dictionary mapping meal names to times in HH:MM format
                       Example: {"breakfast": "08:00", "lunch": "13:00", "dinner": "19:00"}
                       Times must be in 24-hour format with leading zeros
                       Number of meals must match meal_frequency from diet plan
                       Meals must be at least 2 hours apart
                       Meals must be in chronological order
                       
        Returns:
            Dict with status and message
            
        Example:
            save_meal_schedule(
                meal_times={
                    "breakfast": "08:00",
                    "lunch": "13:00",
                    "snack": "16:00",
                    "dinner": "19:00"
                }
            )
        """
        # Validate meal_times is a dict
        if not meal_times or not isinstance(meal_times, dict):
            return {
                "status": "error",
                "message": "meal_times must be a non-empty dictionary"
            }
        
        # Validate all time formats
        for meal_name, time_str in meal_times.items():
            if not validate_time_format(time_str):
                return {
                    "status": "error",
                    "message": f"Invalid time format for {meal_name}: {time_str}. Time must be in HH:MM format (e.g., 08:00, 13:30)"
                }
            
            if not validate_time_range(time_str):
                return {
                    "status": "error",
                    "message": f"Invalid time range for {meal_name}: {time_str}. Time must be between 00:00 and 23:59"
                }
        
        # Load OnboardingState to check meal_frequency
        try:
            stmt = select(OnboardingState).where(OnboardingState.user_id == user_id)
            result = await db.execute(stmt)
            state = result.scalars().first()
            
            if not state:
                return {
                    "status": "error",
                    "message": "Onboarding state not found"
                }
            
            # Get meal_frequency from diet_planning
            meal_frequency = state.agent_context.get("diet_planning", {}).get("proposed_plan", {}).get("meal_frequency")
            
            if meal_frequency is None:
                return {
                    "status": "error",
                    "message": "Meal frequency not found in diet plan. Please complete diet planning first."
                }
            
            # Validate number of meals matches frequency
            if len(meal_times) != meal_frequency:
                return {
                    "status": "error",
                    "message": f"Meal count mismatch: provided {len(meal_times)} meals but meal plan requires {meal_frequency}"
                }
            
            # Validate meal spacing (at least 2 hours apart)
            if not validate_meal_spacing(meal_times):
                return {
                    "status": "error",
                    "message": "Insufficient spacing: meals must be at least 2 hours apart for proper digestion"
                }
            
            # Validate meal ordering (chronological)
            if not validate_meal_ordering(meal_times):
                return {
                    "status": "error",
                    "message": "Invalid meal order: meals must be in chronological order throughout the day"
                }
            
            # Initialize agent_context if needed
            if not state.agent_context:
                state.agent_context = {}
            
            # Initialize scheduling section if needed
            if "scheduling" not in state.agent_context:
                state.agent_context["scheduling"] = {}
            
            # Save meal schedule
            state.agent_context["scheduling"]["meal_schedule"] = {
                **meal_times,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Mark as modified for SQLAlchemy to detect change
            state.agent_context = dict(state.agent_context)
            
            await db.commit()
            await db.refresh(state)
            
            logger.info(
                f"Saved meal schedule for user {user_id}: {len(meal_times)} meals",
                extra={"user_id": str(user_id), "meal_times": meal_times}
            )
            
            return {
                "status": "success",
                "message": f"Meal schedule saved successfully: {len(meal_times)} meals per day"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Error saving meal schedule for user {user_id}: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "message": "Failed to save meal schedule. Please try again."
            }
    
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
            state.agent_context["scheduling"]["hydration_preferences"] = {
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
    
    return [save_workout_schedule, save_meal_schedule, save_hydration_preferences]

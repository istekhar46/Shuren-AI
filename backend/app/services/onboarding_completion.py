"""
Onboarding completion verification service.

This module provides functionality to verify that all required agent data
has been collected before allowing onboarding completion and profile creation.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class OnboardingIncompleteError(Exception):
    """
    Exception raised when onboarding completion is attempted with incomplete data.
    
    This error indicates that one or more required agents have not completed
    their data collection, or that required fields are missing from the
    agent_context.
    
    Attributes:
        message: Human-readable error message describing what is missing
        missing_data: List of missing agent keys or fields
    """
    
    def __init__(self, message: str, missing_data: List[str] = None):
        """
        Initialize OnboardingIncompleteError.
        
        Args:
            message: Error message describing the missing data
            missing_data: Optional list of missing agent keys or fields
        """
        self.message = message
        self.missing_data = missing_data or []
        super().__init__(self.message)


def verify_onboarding_completion(agent_context: dict) -> None:
    """
    Verify that all required agent data is present for onboarding completion.
    
    This function checks that all four onboarding agents have completed their
    data collection and that all required fields are present in the agent_context.
    
    Required agents and their data (4-step flow):
    1. fitness_assessment - Must have completed_at timestamp and goals
    2. workout_planning - Must have user_approved=True, plan, and schedule
    3. diet_planning - Must have user_approved=True, plan, and schedule
    4. scheduling - Must have hydration preferences
    
    Args:
        agent_context: The agent_context dictionary from OnboardingState
        
    Raises:
        OnboardingIncompleteError: If any required agent data is missing
        
    Examples:
        >>> agent_context = {
        ...     "fitness_assessment": {"completed_at": "2024-01-15T10:30:00Z", "primary_goal": "muscle_gain"},
        ...     "workout_planning": {"user_approved": True, "plan": {...}, "schedule": {...}},
        ...     "diet_planning": {"user_approved": True, "plan": {...}, "schedule": {...}},
        ...     "scheduling": {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 120}
        ... }
        >>> verify_onboarding_completion(agent_context)  # No error raised
        
        >>> incomplete_context = {"fitness_assessment": {"completed_at": "..."}}
        >>> verify_onboarding_completion(incomplete_context)
        Traceback (most recent call last):
        ...
        OnboardingIncompleteError: Onboarding incomplete: missing workout_planning data
    """
    if not agent_context or not isinstance(agent_context, dict):
        raise OnboardingIncompleteError(
            "Onboarding incomplete: agent_context is empty or invalid",
            missing_data=["agent_context"]
        )
    
    missing_data = []
    
    # Check fitness_assessment (Step 1) - includes goals now
    if "fitness_assessment" not in agent_context:
        missing_data.append("fitness_assessment")
    else:
        fitness_data = agent_context.get("fitness_assessment", {})
        if "completed_at" not in fitness_data:
            missing_data.append("fitness_assessment.completed_at")
        if "primary_goal" not in fitness_data:
            missing_data.append("fitness_assessment.primary_goal")
    
    # Check workout_planning (Step 2) - includes plan and schedule
    if "workout_planning" not in agent_context:
        missing_data.append("workout_planning")
    else:
        workout_data = agent_context.get("workout_planning", {})
        if not workout_data.get("user_approved"):
            missing_data.append("workout_planning.user_approved")
        # Check for plan (can be "plan" or "proposed_plan" for backward compatibility)
        if "plan" not in workout_data and "proposed_plan" not in workout_data:
            missing_data.append("workout_planning.plan")
        # Check for schedule
        if "schedule" not in workout_data:
            missing_data.append("workout_planning.schedule")
    
    # Check diet_planning (Step 3) - includes plan and schedule
    if "diet_planning" not in agent_context:
        missing_data.append("diet_planning")
    else:
        diet_data = agent_context.get("diet_planning", {})
        if not diet_data.get("user_approved"):
            missing_data.append("diet_planning.user_approved")
        # Check for plan (can be "plan" or "proposed_plan" for backward compatibility)
        if "plan" not in diet_data and "proposed_plan" not in diet_data:
            missing_data.append("diet_planning.plan")
        # Check for schedule
        if "schedule" not in diet_data:
            missing_data.append("diet_planning.schedule")
    
    # Check scheduling (Step 4) - hydration preferences only
    if "scheduling" not in agent_context:
        missing_data.append("scheduling")
    else:
        scheduling_data = agent_context.get("scheduling", {})
        
        # Check for hydration preferences (new structure: direct fields)
        if "daily_water_target_ml" not in scheduling_data:
            missing_data.append("scheduling.daily_water_target_ml")
        
        if "reminder_frequency_minutes" not in scheduling_data:
            missing_data.append("scheduling.reminder_frequency_minutes")
    
    # If any data is missing, raise error
    if missing_data:
        missing_str = ", ".join(missing_data)
        raise OnboardingIncompleteError(
            f"Onboarding incomplete: missing {missing_str}",
            missing_data=missing_data
        )
    
    logger.info("Onboarding completion verification passed - all required data present")

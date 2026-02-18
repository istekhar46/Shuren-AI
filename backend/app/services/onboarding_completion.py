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
    
    This function checks that all five onboarding agents have completed their
    data collection and that all required fields are present in the agent_context.
    
    Required agents and their data:
    1. fitness_assessment - Must have completed_at timestamp
    2. goal_setting - Must have completed_at timestamp
    3. workout_planning - Must have user_approved=True
    4. diet_planning - Must have user_approved=True
    5. scheduling - Must have all three schedules:
       - workout_schedule
       - meal_schedule
       - hydration_preferences
    
    Args:
        agent_context: The agent_context dictionary from OnboardingState
        
    Raises:
        OnboardingIncompleteError: If any required agent data is missing
        
    Examples:
        >>> agent_context = {
        ...     "fitness_assessment": {"completed_at": "2024-01-15T10:30:00Z"},
        ...     "goal_setting": {"completed_at": "2024-01-15T10:35:00Z"},
        ...     "workout_planning": {"user_approved": True},
        ...     "diet_planning": {"user_approved": True},
        ...     "scheduling": {
        ...         "workout_schedule": {...},
        ...         "meal_schedule": {...},
        ...         "hydration_preferences": {...}
        ...     }
        ... }
        >>> verify_onboarding_completion(agent_context)  # No error raised
        
        >>> incomplete_context = {"fitness_assessment": {"completed_at": "..."}}
        >>> verify_onboarding_completion(incomplete_context)
        Traceback (most recent call last):
        ...
        OnboardingIncompleteError: Onboarding incomplete: missing goal_setting data
    """
    if not agent_context or not isinstance(agent_context, dict):
        raise OnboardingIncompleteError(
            "Onboarding incomplete: agent_context is empty or invalid",
            missing_data=["agent_context"]
        )
    
    missing_data = []
    
    # Check fitness_assessment
    if "fitness_assessment" not in agent_context:
        missing_data.append("fitness_assessment")
    elif "completed_at" not in agent_context.get("fitness_assessment", {}):
        missing_data.append("fitness_assessment.completed_at")
    
    # Check goal_setting
    if "goal_setting" not in agent_context:
        missing_data.append("goal_setting")
    elif "completed_at" not in agent_context.get("goal_setting", {}):
        missing_data.append("goal_setting.completed_at")
    
    # Check workout_planning
    if "workout_planning" not in agent_context:
        missing_data.append("workout_planning")
    elif not agent_context.get("workout_planning", {}).get("user_approved"):
        missing_data.append("workout_planning.user_approved")
    
    # Check diet_planning
    if "diet_planning" not in agent_context:
        missing_data.append("diet_planning")
    elif not agent_context.get("diet_planning", {}).get("user_approved"):
        missing_data.append("diet_planning.user_approved")
    
    # Check scheduling
    if "scheduling" not in agent_context:
        missing_data.append("scheduling")
    else:
        scheduling_data = agent_context.get("scheduling", {})
        
        # Check for all three required schedules
        if "workout_schedule" not in scheduling_data:
            missing_data.append("scheduling.workout_schedule")
        
        if "meal_schedule" not in scheduling_data:
            missing_data.append("scheduling.meal_schedule")
        
        if "hydration_preferences" not in scheduling_data:
            missing_data.append("scheduling.hydration_preferences")
    
    # If any data is missing, raise error
    if missing_data:
        missing_str = ", ".join(missing_data)
        raise OnboardingIncompleteError(
            f"Onboarding incomplete: missing {missing_str}",
            missing_data=missing_data
        )
    
    logger.info("Onboarding completion verification passed - all required data present")

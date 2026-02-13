"""Onboarding Pydantic schemas"""

from typing import Any

from pydantic import BaseModel, Field


class OnboardingStateResponse(BaseModel):
    """Schema for onboarding state response.
    
    Represents the current state of a user's onboarding progress,
    including all saved step data in JSONB format.
    
    Attributes:
        id: Unique identifier for the onboarding state
        user_id: User's unique identifier
        current_step: Current step number (0-9)
        is_complete: Whether onboarding is complete
        step_data: JSONB dictionary containing all saved step data
    """
    id: str
    user_id: str
    current_step: int
    is_complete: bool
    step_data: dict[str, Any]
    
    class Config:
        from_attributes = True


class OnboardingStepRequest(BaseModel):
    """Schema for submitting onboarding step data.
    
    Used to save data for a specific onboarding state with validation.
    The data structure varies by step number and is validated by
    OnboardingService validators.
    
    Attributes:
        step: Step number (1-9) to save data for
        data: Step-specific data dictionary (structure varies by step)
    """
    step: int = Field(ge=1, le=9, description="Onboarding step number (1-9)")
    data: dict[str, Any] = Field(description="Step-specific data to save")


class StateInfo(BaseModel):
    """Schema for onboarding state metadata.
    
    Provides rich metadata about an onboarding state for UI rendering,
    including which agent handles it and what fields are required.
    
    Attributes:
        state_number: State number (1-9)
        name: Human-readable state name
        agent: Agent type that handles this state (e.g., "workout_planning")
        description: User-facing description of what this state collects
        required_fields: List of required field names for validation
    """
    state_number: int
    name: str
    agent: str
    description: str
    required_fields: list[str]


class OnboardingStepResponse(BaseModel):
    """Schema for onboarding step submission response.
    
    Returned after successfully saving onboarding step data,
    includes confirmation and information about the next state.
    
    Attributes:
        current_step: Updated current step number
        is_complete: Whether all onboarding is now complete
        message: Success confirmation message
        next_state: Next state number (None if complete)
        next_state_info: Metadata for next state (None if complete)
    """
    current_step: int
    is_complete: bool
    message: str
    next_state: int | None = None
    next_state_info: StateInfo | None = None


class OnboardingProgress(BaseModel):
    """Schema for onboarding progress tracking.
    
    Internal model used by OnboardingService to track progress.
    Contains all information needed for progress indicators and UI state.
    
    Attributes:
        current_state: Current state number (1-9)
        total_states: Total number of states (always 9)
        completed_states: List of completed state numbers
        current_state_info: Metadata for current state
        next_state_info: Metadata for next state (None if on last state)
        is_complete: Whether onboarding is complete
        completion_percentage: Percentage complete (0-100)
        can_complete: Whether user can complete onboarding (all states done)
    """
    current_state: int
    total_states: int
    completed_states: list[int]
    current_state_info: StateInfo
    next_state_info: StateInfo | None
    is_complete: bool
    completion_percentage: int
    can_complete: bool


class OnboardingProgressResponse(BaseModel):
    """Schema for onboarding progress endpoint response.
    
    Returned by GET /api/v1/onboarding/progress endpoint.
    Provides rich progress metadata for UI indicators including
    current state, completed states, and completion percentage.
    
    Attributes:
        current_state: Current state number (1-9)
        total_states: Total number of states (always 9)
        completed_states: List of completed state numbers
        current_state_info: Metadata for current state
        next_state_info: Metadata for next state (None if on last state)
        is_complete: Whether onboarding is complete
        completion_percentage: Percentage complete (0-100)
        can_complete: Whether user can complete onboarding (all states done)
    """
    current_state: int
    total_states: int = 9
    completed_states: list[int]
    current_state_info: StateInfo
    next_state_info: StateInfo | None
    is_complete: bool
    completion_percentage: int
    can_complete: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_state": 3,
                "total_states": 9,
                "completed_states": [1, 2],
                "current_state_info": {
                    "state_number": 3,
                    "name": "Workout Preferences & Constraints",
                    "agent": "workout_planning",
                    "description": "Tell us about your equipment and limitations",
                    "required_fields": ["equipment", "injuries", "limitations"]
                },
                "next_state_info": {
                    "state_number": 4,
                    "name": "Diet Preferences & Restrictions",
                    "agent": "diet_planning",
                    "description": "Share your dietary preferences"
                },
                "is_complete": False,
                "completion_percentage": 33,
                "can_complete": False
            }
        }


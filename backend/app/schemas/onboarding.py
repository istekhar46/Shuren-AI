"""Onboarding Pydantic schemas"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OnboardingAgentType(str, Enum):
    """
    Enumeration of all onboarding agent types.
    
    Each agent type corresponds to specific onboarding steps
    and has specialized knowledge for that domain.
    """
    
    FITNESS_ASSESSMENT = "fitness_assessment"  # Step 1
    WORKOUT_PLANNING = "workout_planning"      # Step 2
    DIET_PLANNING = "diet_planning"            # Step 3
    SCHEDULING = "scheduling"                  # Step 4


class OnboardingStateResponse(BaseModel):
    """Schema for onboarding state response.
    
    Represents the current state of a user's onboarding progress,
    including step completion flags for the 4-step flow.
    
    Attributes:
        id: Unique identifier for the onboarding state
        user_id: User's unique identifier
        current_step: Current step number (1-4)
        is_complete: Whether onboarding is complete
        step_1_complete: Whether step 1 (fitness assessment) is complete
        step_2_complete: Whether step 2 (workout planning) is complete
        step_3_complete: Whether step 3 (diet planning) is complete
        step_4_complete: Whether step 4 (scheduling) is complete
        agent_context: JSONB dictionary containing data collected by agents
    """
    id: str
    user_id: str
    current_step: int
    is_complete: bool
    step_1_complete: bool
    step_2_complete: bool
    step_3_complete: bool
    step_4_complete: bool
    agent_context: dict[str, Any] = Field(default_factory=dict)
    
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
        current_state: Current state number (1-4)
        total_states: Total number of states (always 4)
        completed_states: List of completed state numbers
        current_state_info: Metadata for current state
        next_state_info: Metadata for next state (None if on last state)
        is_complete: Whether onboarding is complete
        completion_percentage: Percentage complete (0-100)
        can_complete: Whether user can complete onboarding (all states done)
    """
    current_state: int
    total_states: int = 4
    completed_states: list[int]
    current_state_info: StateInfo
    next_state_info: StateInfo | None
    is_complete: bool
    completion_percentage: int
    can_complete: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_state": 2,
                "total_states": 4,
                "completed_states": [1],
                "current_state_info": {
                    "state_number": 2,
                    "name": "Workout Planning",
                    "agent": "workout_planning",
                    "description": "Create your personalized workout plan",
                    "required_fields": ["equipment", "injuries", "limitations", "days_per_week"]
                },
                "next_state_info": {
                    "state_number": 3,
                    "name": "Diet Planning",
                    "agent": "diet_planning",
                    "description": "Build your personalized meal plan"
                },
                "is_complete": False,
                "completion_percentage": 25,
                "can_complete": False
            }
        }


class AgentResponse(BaseModel):
    """
    Standardized response format from onboarding agents.
    
    This schema defines the structure of responses returned by all
    onboarding agents, ensuring consistent communication between
    agents and the API layer.
    
    Attributes:
        message: Agent's response message to the user
        agent_type: Type of agent that generated this response
        step_complete: Whether the current onboarding step is complete
        next_action: What should happen next (continue_conversation, advance_step, complete_onboarding)
        context_update: Context data to save for this agent
    """
    
    message: str = Field(
        ...,
        description="Agent's response message to the user",
        min_length=1
    )
    
    agent_type: str = Field(
        ...,
        description="Type of agent that generated this response"
    )
    
    step_complete: bool = Field(
        default=False,
        description="Whether the current onboarding step is complete"
    )
    
    next_action: str = Field(
        default="continue_conversation",
        description="What should happen next: 'continue_conversation', 'advance_step', 'complete_onboarding'"
    )
    
    context_update: dict[str, Any] = Field(
        default_factory=dict,
        description="Context data to save for this agent"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Great! I understand you're at an intermediate fitness level. Let's talk about your goals.",
                "agent_type": "fitness_assessment",
                "step_complete": True,
                "next_action": "advance_step",
                "context_update": {
                    "fitness_level": "intermediate",
                    "experience_years": 2,
                    "completed_at": "2024-01-15T10:30:00Z"
                }
            }
        }


class OnboardingChatRequest(BaseModel):
    """
    Request schema for onboarding chat endpoint.
    
    Used to send user messages to the current onboarding agent.
    The agent is determined by the user's current onboarding step.
    
    Attributes:
        message: User's message to the onboarding agent (1-2000 characters)
        step: Optional step number for validation (0-9)
    """
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message to the onboarding agent"
    )
    
    step: int | None = Field(
        default=None,
        ge=0,
        le=9,
        description="Optional step number for validation"
    )
    
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate that message is not empty or whitespace only."""
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I workout 3 times a week at the gym",
                "step": 0
            }
        }


class OnboardingChatResponse(BaseModel):
    """
    Response schema for onboarding chat endpoint.
    
    Returned after the agent processes a user message.
    Includes the agent's response and current state information.
    
    Attributes:
        message: Agent's response message
        agent_type: Type of agent that handled this message
        current_step: Current onboarding step number
        step_complete: Whether the current step is complete
        next_action: What should happen next
    """
    
    message: str = Field(
        ...,
        description="Agent's response message"
    )
    
    agent_type: str = Field(
        ...,
        description="Type of agent that handled this message"
    )
    
    current_step: int = Field(
        ...,
        ge=0,
        le=9,
        description="Current onboarding step number"
    )
    
    step_complete: bool = Field(
        default=False,
        description="Whether the current step is complete"
    )
    
    next_action: str = Field(
        default="continue_conversation",
        description="What should happen next"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Great! 3 times a week shows good consistency. What type of exercises do you usually do?",
                "agent_type": "fitness_assessment",
                "current_step": 0,
                "step_complete": False,
                "next_action": "continue_conversation"
            }
        }


class CurrentAgentResponse(BaseModel):
    """
    Response schema for current agent info endpoint.
    
    Provides information about the current onboarding agent
    to help the client display appropriate UI and context.
    
    Attributes:
        agent_type: Type of the current agent
        current_step: Current onboarding step number
        agent_description: Human-readable description of agent's role
        context_summary: Summary of context collected so far
    """
    
    agent_type: str = Field(
        ...,
        description="Type of the current agent"
    )
    
    current_step: int = Field(
        ...,
        ge=0,
        le=9,
        description="Current onboarding step number"
    )
    
    agent_description: str = Field(
        ...,
        description="Human-readable description of agent's role"
    )
    
    context_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of context collected so far"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "fitness_assessment",
                "current_step": 1,
                "agent_description": "I'll help assess your current fitness level",
                "context_summary": {
                    "fitness_assessment": {
                        "fitness_level": "intermediate",
                        "experience_years": 2
                    }
                }
            }
        }



class OnboardingCompleteResponse(BaseModel):
    """
    Response schema for onboarding completion endpoint.
    
    Returned after successfully completing onboarding and creating
    the user's locked profile with all related entities.
    
    Attributes:
        profile_id: UUID of the created profile
        user_id: UUID of the user
        fitness_level: User's fitness level from assessment
        is_locked: Whether the profile is locked (always True)
        onboarding_complete: Whether onboarding is complete (always True)
        message: Success confirmation message
    """
    
    profile_id: str = Field(
        ...,
        description="UUID of the created profile"
    )
    
    user_id: str = Field(
        ...,
        description="UUID of the user"
    )
    
    fitness_level: str = Field(
        ...,
        description="User's fitness level from assessment"
    )
    
    is_locked: bool = Field(
        ...,
        description="Whether the profile is locked"
    )
    
    onboarding_complete: bool = Field(
        ...,
        description="Whether onboarding is complete"
    )
    
    message: str = Field(
        ...,
        description="Success confirmation message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "fitness_level": "intermediate",
                "is_locked": True,
                "onboarding_complete": True,
                "message": "Onboarding completed successfully! Your personalized fitness profile is ready."
            }
        }

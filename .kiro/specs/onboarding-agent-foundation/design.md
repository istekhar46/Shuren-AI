# Design Document: Onboarding Agent Foundation

## Overview

The Onboarding Agent Foundation establishes the core infrastructure for a conversational onboarding system powered by specialized AI agents. This foundation provides the database schema enhancements, base agent architecture, orchestration service, and API endpoints that enable intelligent, context-aware onboarding conversations.

The system transforms the current form-based onboarding into an interactive experience where AI agents guide users through each step, building context progressively and maintaining conversation continuity. This is the first of four specifications that will implement the complete conversational onboarding system.

### Key Design Principles

1. **Progressive Context Building**: Each agent adds to a shared context that subsequent agents can access
2. **Separation of Concerns**: Clear boundaries between orchestration, agent logic, and data persistence
3. **Backward Compatibility**: New infrastructure coexists with existing onboarding flow
4. **Extensibility**: Easy to add new agent types or modify routing logic
5. **Type Safety**: Pydantic schemas ensure data validation at API boundaries

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  POST /api/v1/onboarding/chat                               │
│  GET  /api/v1/onboarding/current-agent                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OnboardingAgentOrchestrator                     │
│  - Routes messages to appropriate agent                      │
│  - Loads context from database                               │
│  - Maps steps to agent types                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  BaseOnboardingAgent                         │
│  - Abstract interface for all agents                         │
│  - LLM initialization                                        │
│  - Context management                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   Fitness    │ │   Goal   │ │ Workout  │ │   Diet   │
│  Assessment  │ │ Setting  │ │ Planning │ │ Planning │
│    Agent     │ │  Agent   │ │  Agent   │ │  Agent   │
└──────────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Data Flow

```
User Message → API Endpoint → Orchestrator → Agent → LLM → Response
                    ↓              ↓           ↓
                Database      Load Context  Save Context
```

## Components and Interfaces

### 1. Database Schema Enhancement

#### OnboardingState Model Updates

```python
class OnboardingState(BaseModel):
    __tablename__ = "onboarding_states"
    
    # Existing fields
    id: UUID
    user_id: UUID
    current_step: int
    is_complete: bool
    step_data: JSONB
    agent_history: JSONB
    
    # NEW FIELDS
    current_agent: str | None  # e.g., "fitness_assessment", "goal_setting"
    agent_context: JSONB       # Context passed between agents
    conversation_history: JSONB  # Chat messages per step
```

**Migration Strategy**:
- Add three new columns with nullable/default values
- Existing records get default values: `current_agent=None`, `agent_context={}`, `conversation_history=[]`
- No data migration needed - fields populate as agents are used
- Backward compatible with existing OnboardingService

#### Agent Context Structure

```python
{
    "fitness_assessment": {
        "fitness_level": "intermediate",
        "experience_years": 2,
        "limitations": ["no_equipment_at_home"],
        "completed_at": "2024-01-15T10:30:00Z"
    },
    "goal_setting": {
        "primary_goal": "muscle_gain",
        "secondary_goal": "fat_loss",
        "target_weight_kg": 75,
        "completed_at": "2024-01-15T10:35:00Z"
    },
    # ... other agents
}
```

#### Conversation History Structure

```python
[
    {
        "role": "user",
        "content": "I workout 3 times a week",
        "timestamp": "2024-01-15T10:30:00Z"
    },
    {
        "role": "assistant",
        "content": "Great! 3 times a week shows good consistency...",
        "timestamp": "2024-01-15T10:30:05Z",
        "agent_type": "fitness_assessment"
    }
]
```

### 2. Base Agent Architecture

#### BaseOnboardingAgent Abstract Class

```python
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_anthropic import ChatAnthropic

class BaseOnboardingAgent(ABC):
    """
    Abstract base class for all onboarding agents.
    
    Provides common functionality for LLM integration, context management,
    and database operations. All specialized onboarding agents must extend
    this class and implement the abstract methods.
    """
    
    def __init__(self, db: AsyncSession, context: dict):
        """
        Initialize agent with database session and context.
        
        Args:
            db: Async database session for database operations
            context: Agent context dictionary from OnboardingState
        """
        self.db = db
        self.context = context
        self.llm = self._init_llm()
    
    def _init_llm(self) -> ChatAnthropic:
        """
        Initialize the LLM for this agent.
        
        Returns:
            ChatAnthropic instance configured for onboarding
        """
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0.7,
            max_tokens=2048
        )
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message and return agent response.
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """
        Get agent-specific tools for LLM function calling.
        
        Returns:
            List of LangChain tools available to this agent
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            System prompt string defining agent role and behavior
        """
        pass
    
    async def save_context(self, user_id: UUID, agent_data: dict) -> None:
        """
        Save agent-specific context to OnboardingState.
        
        Args:
            user_id: UUID of the user
            agent_data: Dictionary of data to save for this agent
        """
        from sqlalchemy import select, update
        from app.models.onboarding import OnboardingState
        
        # Load current state
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state:
            # Update agent_context
            agent_context = state.agent_context or {}
            agent_context[self.agent_type] = agent_data
            
            # Update in database
            stmt = (
                update(OnboardingState)
                .where(OnboardingState.user_id == user_id)
                .values(agent_context=agent_context)
            )
            await self.db.execute(stmt)
            await self.db.commit()
```

#### AgentResponse Schema

```python
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """
    Standardized response format from onboarding agents.
    """
    
    message: str = Field(
        ...,
        description="Agent's response message to the user"
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
    
    context_update: dict = Field(
        default_factory=dict,
        description="Context data to save for this agent"
    )
```

### 3. Agent Type Enumeration

```python
from enum import Enum

class OnboardingAgentType(str, Enum):
    """
    Enumeration of all onboarding agent types.
    
    Each agent type corresponds to specific onboarding steps
    and has specialized knowledge for that domain.
    """
    
    FITNESS_ASSESSMENT = "fitness_assessment"  # Steps 0-2
    GOAL_SETTING = "goal_setting"              # Step 3
    WORKOUT_PLANNING = "workout_planning"      # Steps 4-5
    DIET_PLANNING = "diet_planning"            # Steps 6-7
    SCHEDULING = "scheduling"                  # Steps 8-9
```

### 4. Onboarding Agent Orchestrator

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class OnboardingAgentOrchestrator:
    """
    Orchestrates onboarding agents based on current step.
    
    Responsibilities:
    - Load onboarding state from database
    - Map current step to appropriate agent type
    - Instantiate agent with context
    - Route messages to the correct agent
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize orchestrator with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_current_agent(
        self,
        user_id: UUID
    ) -> BaseOnboardingAgent:
        """
        Get the appropriate agent for user's current onboarding step.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Instance of the appropriate onboarding agent
            
        Raises:
            ValueError: If step is invalid or user not found
        """
        # Load onboarding state
        state = await self._load_onboarding_state(user_id)
        
        if not state:
            raise ValueError(f"No onboarding state found for user {user_id}")
        
        # Determine agent type from step
        agent_type = self._step_to_agent(state.current_step)
        
        # Load context
        context = state.agent_context or {}
        
        # Create and return agent
        return await self._create_agent(agent_type, context)
    
    def _step_to_agent(self, step: int) -> OnboardingAgentType:
        """
        Map onboarding step number to agent type.
        
        Args:
            step: Current onboarding step (0-9)
            
        Returns:
            OnboardingAgentType for this step
            
        Raises:
            ValueError: If step is out of valid range
        """
        if step < 0 or step > 9:
            raise ValueError(f"Invalid onboarding step: {step}")
        
        if step <= 2:
            return OnboardingAgentType.FITNESS_ASSESSMENT
        elif step == 3:
            return OnboardingAgentType.GOAL_SETTING
        elif step <= 5:
            return OnboardingAgentType.WORKOUT_PLANNING
        elif step <= 7:
            return OnboardingAgentType.DIET_PLANNING
        else:  # steps 8-9
            return OnboardingAgentType.SCHEDULING
    
    async def _create_agent(
        self,
        agent_type: OnboardingAgentType,
        context: dict
    ) -> BaseOnboardingAgent:
        """
        Factory method to create agent instance.
        
        Args:
            agent_type: Type of agent to create
            context: Agent context from database
            
        Returns:
            Instance of the appropriate agent class
        """
        # Import agent classes (will be implemented in future specs)
        from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
        from app.agents.onboarding.goal_setting import GoalSettingAgent
        from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
        from app.agents.onboarding.diet_planning import DietPlanningAgent
        from app.agents.onboarding.scheduling import SchedulingAgent
        
        agent_classes = {
            OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
            OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
            OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
            OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
            OnboardingAgentType.SCHEDULING: SchedulingAgent,
        }
        
        agent_class = agent_classes[agent_type]
        return agent_class(self.db, context)
    
    async def _load_onboarding_state(
        self,
        user_id: UUID
    ) -> OnboardingState | None:
        """
        Load onboarding state from database.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            OnboardingState or None if not found
        """
        from app.models.onboarding import OnboardingState
        
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
```

### 5. API Endpoints

#### POST /api/v1/onboarding/chat

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()

@router.post("/chat", response_model=OnboardingChatResponse)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        HTTPException: 404 if user not found, 500 on errors
    """
    try:
        # Create orchestrator
        orchestrator = OnboardingAgentOrchestrator(db)
        
        # Get current agent
        agent = await orchestrator.get_current_agent(current_user.id)
        
        # Process message
        response = await agent.process_message(
            message=request.message,
            user_id=current_user.id
        )
        
        # Save conversation to history
        await _append_to_conversation_history(
            db=db,
            user_id=current_user.id,
            user_message=request.message,
            agent_response=response.message,
            agent_type=response.agent_type
        )
        
        # Get current step for response
        state = await orchestrator._load_onboarding_state(current_user.id)
        
        return OnboardingChatResponse(
            message=response.message,
            agent_type=response.agent_type,
            current_step=state.current_step,
            step_complete=response.step_complete,
            next_action=response.next_action
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat_onboarding: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your message"
        )
```

#### GET /api/v1/onboarding/current-agent

```python
@router.get("/current-agent", response_model=CurrentAgentResponse)
async def get_current_agent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        HTTPException: 404 if user not found
    """
    try:
        # Create orchestrator
        orchestrator = OnboardingAgentOrchestrator(db)
        
        # Load state
        state = await orchestrator._load_onboarding_state(current_user.id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail="Onboarding state not found"
            )
        
        # Determine agent type
        agent_type = orchestrator._step_to_agent(state.current_step)
        
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
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_current_agent: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred retrieving agent information"
        )
```

### 6. Request and Response Schemas

```python
from pydantic import BaseModel, Field, field_validator

class OnboardingChatRequest(BaseModel):
    """Request schema for onboarding chat endpoint."""
    
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
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class OnboardingChatResponse(BaseModel):
    """Response schema for onboarding chat endpoint."""
    
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


class CurrentAgentResponse(BaseModel):
    """Response schema for current agent info endpoint."""
    
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
    
    context_summary: dict = Field(
        default_factory=dict,
        description="Summary of context collected so far"
    )
```

### 7. Specialized Agent Stub Implementations

For this foundation spec, we create stub implementations of the five specialized agents. These will be fully implemented in subsequent specs.

```python
# app/agents/onboarding/fitness_assessment.py
class FitnessAssessmentAgent(BaseOnboardingAgent):
    """Agent for assessing user's fitness level (Steps 0-2)."""
    
    agent_type = "fitness_assessment"
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """Process message - stub implementation."""
        return AgentResponse(
            message="Fitness assessment agent - to be implemented",
            agent_type=self.agent_type,
            step_complete=False,
            next_action="continue_conversation"
        )
    
    def get_tools(self) -> List:
        """Get tools - stub implementation."""
        return []
    
    def get_system_prompt(self) -> str:
        """Get system prompt for fitness assessment."""
        return """You are a Fitness Assessment Agent helping users determine their fitness level.

Your role:
- Ask friendly questions about their exercise experience
- Assess their fitness level (beginner/intermediate/advanced)
- Identify any physical limitations (equipment, injuries - non-medical)
- Be encouraging and non-judgmental

Guidelines:
- Keep questions conversational
- Don't overwhelm with too many questions at once
- Never provide medical advice
- Save assessment results when user confirms
"""


# Similar stub implementations for:
# - GoalSettingAgent
# - WorkoutPlanningAgent
# - DietPlanningAgent
# - SchedulingAgent
```

## Data Models

### OnboardingState (Enhanced)

```python
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import BaseModel

class OnboardingState(BaseModel):
    """Enhanced onboarding state with agent support."""
    
    __tablename__ = "onboarding_states"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)
    step_data = Column(JSONB, default=dict, nullable=False)
    agent_history = Column(JSONB, default=list, nullable=False)
    
    # NEW FIELDS
    current_agent = Column(String(50), nullable=True)
    agent_context = Column(JSONB, default=dict, nullable=False)
    conversation_history = Column(JSONB, default=list, nullable=False)
```

### Database Migration

```python
"""Add agent fields to onboarding_states

Revision ID: add_agent_fields_to_onboarding
Revises: previous_revision
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_agent_fields_to_onboarding'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add agent-related fields to onboarding_states table."""
    op.add_column(
        'onboarding_states',
        sa.Column('current_agent', sa.String(50), nullable=True)
    )
    op.add_column(
        'onboarding_states',
        sa.Column(
            'agent_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        )
    )
    op.add_column(
        'onboarding_states',
        sa.Column(
            'conversation_history',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb")
        )
    )


def downgrade() -> None:
    """Remove agent-related fields from onboarding_states table."""
    op.drop_column('onboarding_states', 'conversation_history')
    op.drop_column('onboarding_states', 'agent_context')
    op.drop_column('onboarding_states', 'current_agent')
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Database Migration Preserves Existing Data

*For any* existing OnboardingState record, applying the migration should preserve all original field values (user_id, current_step, is_complete, step_data, agent_history) while adding new fields with their default values.

**Validates: Requirements 1.5, 1.6**

### Property 2: New Fields Have Correct Defaults

*For any* OnboardingState record queried after migration, if the record existed before migration, the new fields should have values: current_agent=None, agent_context={}, conversation_history=[].

**Validates: Requirements 1.6**

### Property 3: Abstract Methods Must Be Implemented

*For any* class that inherits from BaseOnboardingAgent, attempting to instantiate it without implementing all abstract methods (process_message, get_tools, get_system_prompt) should raise TypeError.

**Validates: Requirements 2.2, 2.3, 2.4, 2.7**

### Property 4: Save Context Updates Database

*For any* valid user_id and agent_data dictionary, calling save_context should update the agent_context field in OnboardingState such that querying the database returns the updated context.

**Validates: Requirements 2.5**

### Property 5: AgentResponse Schema Completeness

*For any* AgentResponse instance, it should contain all required fields (message, agent_type, step_complete, next_action) with correct types (str, str, bool, str respectively).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 6: AgentResponse Serialization Round-Trip

*For any* valid AgentResponse object, serializing to JSON and then deserializing should produce an equivalent object with all field values preserved.

**Validates: Requirements 3.5**

### Property 7: Optional Fields Handle None Values

*For any* AgentResponse with None values in optional fields, serialization and deserialization should complete without errors and preserve the None values.

**Validates: Requirements 3.6**

### Property 8: Step to Agent Mapping Correctness

*For any* step number in the valid range [0-9], the _step_to_agent method should return the correct OnboardingAgentType according to the specification: steps 0-2 → FITNESS_ASSESSMENT, step 3 → GOAL_SETTING, steps 4-5 → WORKOUT_PLANNING, steps 6-7 → DIET_PLANNING, steps 8-9 → SCHEDULING.

**Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 9: Invalid Steps Raise ValueError

*For any* step number outside the valid range (step < 0 or step > 9), calling _step_to_agent should raise ValueError.

**Validates: Requirements 5.7**

### Property 10: Agent Factory Creates Correct Type

*For any* valid OnboardingAgentType, calling _create_agent should return an instance of the correct agent class (FitnessAssessmentAgent, GoalSettingAgent, WorkoutPlanningAgent, DietPlanningAgent, or SchedulingAgent).

**Validates: Requirements 5.8**

### Property 11: Context Passed to Agent Constructor

*For any* agent created by the orchestrator, the context parameter passed to the agent's constructor should match the agent_context loaded from the OnboardingState.

**Validates: Requirements 5.9**

### Property 12: API Request Validation

*For any* request to POST /api/v1/onboarding/chat with invalid data (missing required fields, wrong types, or empty message), the endpoint should return HTTP 422 with validation errors.

**Validates: Requirements 6.2, 6.6**

### Property 13: Successful Requests Update Conversation History

*For any* valid authenticated request to POST /api/v1/onboarding/chat, after processing, the conversation_history in OnboardingState should contain the user's message and the agent's response.

**Validates: Requirements 6.8**

### Property 14: Agent Routing Correctness

*For any* valid authenticated request, the message should be routed to the agent corresponding to the user's current_step, and the response should have agent_type matching that agent.

**Validates: Requirements 6.3, 6.4**

### Property 15: Backward Compatibility Preservation

*For any* existing OnboardingState record and any operation from the existing OnboardingService, the operation should complete successfully without errors, producing the same results as before the migration.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

### Property 16: LLM Initialization Configuration

*For any* BaseOnboardingAgent subclass, calling _init_llm should return a ChatAnthropic instance configured with model="claude-sonnet-4-5-20250929", temperature=0.7, and max_tokens=2048.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4**

## Error Handling

### Error Categories

1. **Authentication Errors (401)**
   - Missing JWT token
   - Invalid or expired JWT token
   - User not found in database

2. **Validation Errors (422)**
   - Missing required fields in request body
   - Invalid field types
   - Empty or whitespace-only messages
   - Step number out of range

3. **Not Found Errors (404)**
   - User has no OnboardingState
   - Invalid user_id

4. **Server Errors (500)**
   - Database connection failures
   - LLM API failures
   - Unexpected exceptions in agent processing

### Error Response Format

All errors return consistent JSON structure:

```json
{
    "detail": "Human-readable error message",
    "error_code": "SPECIFIC_ERROR_CODE",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Handling Strategy

1. **Graceful Degradation**: If LLM fails, return helpful error message instead of crashing
2. **Logging**: All errors logged with context (user_id, step, agent_type)
3. **User-Friendly Messages**: Never expose internal implementation details
4. **Retry Logic**: Database operations retry once on transient failures
5. **Transaction Rollback**: Database errors trigger automatic rollback

### Specific Error Scenarios

**Missing API Key**:
```python
if not settings.ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not configured. "
        "Please set the environment variable."
    )
```

**Invalid Step Number**:
```python
if step < 0 or step > 9:
    raise ValueError(
        f"Invalid onboarding step: {step}. "
        f"Valid range is 0-9."
    )
```

**Database Connection Error**:
```python
try:
    result = await db.execute(stmt)
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(
        status_code=503,
        detail="Database temporarily unavailable. Please try again."
    )
```

**LLM API Error**:
```python
try:
    response = await llm.ainvoke(messages)
except Exception as e:
    logger.error(f"LLM API error: {e}")
    return AgentResponse(
        message="I'm having trouble processing your message. Please try again.",
        agent_type=self.agent_type,
        step_complete=False,
        next_action="retry"
    )
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using Hypothesis

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

- **Library**: Hypothesis for Python
- **Minimum iterations**: 100 per property test
- **Test tagging**: Each property test must reference its design document property
- **Tag format**: `# Feature: onboarding-agent-foundation, Property {number}: {property_text}`

### Unit Testing Focus

Unit tests should focus on:
- Specific examples that demonstrate correct behavior
- Integration points between components (orchestrator ↔ agents, API ↔ orchestrator)
- Edge cases (empty context, missing fields, boundary step numbers)
- Error conditions (authentication failures, database errors, invalid inputs)

Avoid writing too many unit tests for scenarios that property tests already cover. For example, don't write 10 unit tests for different step numbers when Property 8 already validates all step mappings.

### Test Organization

```
backend/tests/
├── test_onboarding_agent_foundation/
│   ├── test_base_agent.py              # Unit tests for BaseOnboardingAgent
│   ├── test_orchestrator.py            # Unit tests for orchestrator
│   ├── test_api_endpoints.py           # Integration tests for API
│   ├── test_schemas.py                 # Unit tests for Pydantic schemas
│   ├── test_migration.py               # Database migration tests
│   └── test_properties.py              # Property-based tests
```

### Property Test Examples

**Property 8: Step to Agent Mapping**
```python
from hypothesis import given, strategies as st
import pytest

@given(step=st.integers(min_value=0, max_value=9))
async def test_step_to_agent_mapping_property(step: int):
    """
    Feature: onboarding-agent-foundation, Property 8: Step to Agent Mapping Correctness
    
    For any step number in [0-9], _step_to_agent returns correct agent type.
    """
    orchestrator = OnboardingAgentOrchestrator(mock_db)
    agent_type = orchestrator._step_to_agent(step)
    
    # Verify correct mapping
    if step <= 2:
        assert agent_type == OnboardingAgentType.FITNESS_ASSESSMENT
    elif step == 3:
        assert agent_type == OnboardingAgentType.GOAL_SETTING
    elif step <= 5:
        assert agent_type == OnboardingAgentType.WORKOUT_PLANNING
    elif step <= 7:
        assert agent_type == OnboardingAgentType.DIET_PLANNING
    else:  # 8-9
        assert agent_type == OnboardingAgentType.SCHEDULING
```

**Property 6: AgentResponse Serialization Round-Trip**
```python
from hypothesis import given, strategies as st

@given(
    message=st.text(min_size=1, max_size=1000),
    agent_type=st.sampled_from(["fitness_assessment", "goal_setting", "workout_planning"]),
    step_complete=st.booleans(),
    next_action=st.sampled_from(["continue_conversation", "advance_step", "complete_onboarding"])
)
def test_agent_response_round_trip_property(
    message: str,
    agent_type: str,
    step_complete: bool,
    next_action: str
):
    """
    Feature: onboarding-agent-foundation, Property 6: AgentResponse Serialization Round-Trip
    
    For any valid AgentResponse, serializing and deserializing preserves all values.
    """
    # Create response
    original = AgentResponse(
        message=message,
        agent_type=agent_type,
        step_complete=step_complete,
        next_action=next_action
    )
    
    # Serialize and deserialize
    json_str = original.model_dump_json()
    restored = AgentResponse.model_validate_json(json_str)
    
    # Verify equivalence
    assert restored.message == original.message
    assert restored.agent_type == original.agent_type
    assert restored.step_complete == original.step_complete
    assert restored.next_action == original.next_action
```

### Unit Test Examples

**Database Migration Test**
```python
async def test_migration_adds_new_fields():
    """Test that migration adds the three new fields to onboarding_states."""
    # Apply migration
    await run_migration("add_agent_fields_to_onboarding")
    
    # Check schema
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('onboarding_states')}
    
    # Verify new fields exist
    assert 'current_agent' in columns
    assert 'agent_context' in columns
    assert 'conversation_history' in columns
    
    # Verify types
    assert isinstance(columns['current_agent']['type'], String)
    assert isinstance(columns['agent_context']['type'], JSONB)
    assert isinstance(columns['conversation_history']['type'], JSONB)
```

**API Authentication Test**
```python
async def test_chat_endpoint_requires_authentication(client: AsyncClient):
    """Test that chat endpoint returns 401 without authentication."""
    response = await client.post(
        "/api/v1/onboarding/chat",
        json={"message": "Hello"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()
```

**Abstract Method Enforcement Test**
```python
def test_base_agent_cannot_be_instantiated():
    """Test that BaseOnboardingAgent cannot be instantiated directly."""
    with pytest.raises(TypeError, match="abstract methods"):
        BaseOnboardingAgent(mock_db, {})
```

### Integration Test Example

```python
async def test_end_to_end_chat_flow(
    authenticated_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession
):
    """Test complete flow from API request to agent response."""
    # Create onboarding state
    state = OnboardingState(
        user_id=test_user.id,
        current_step=0,
        agent_context={},
        conversation_history=[]
    )
    db_session.add(state)
    await db_session.commit()
    
    # Send message
    response = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I'm a beginner"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "fitness_assessment"
    assert data["current_step"] == 0
    assert len(data["message"]) > 0
    
    # Verify conversation history updated
    await db_session.refresh(state)
    assert len(state.conversation_history) == 2  # user + assistant
    assert state.conversation_history[0]["role"] == "user"
    assert state.conversation_history[1]["role"] == "assistant"
```

### Coverage Requirements

- Minimum 80% code coverage for new code
- 100% coverage for critical paths (orchestrator routing, context saving)
- All error handling paths must be tested
- All Pydantic schemas must have validation tests

### Test Execution

```bash
# Run all tests
poetry run pytest backend/tests/test_onboarding_agent_foundation/

# Run only unit tests
poetry run pytest backend/tests/test_onboarding_agent_foundation/ -m "not property"

# Run only property tests
poetry run pytest backend/tests/test_onboarding_agent_foundation/test_properties.py

# Run with coverage
poetry run pytest backend/tests/test_onboarding_agent_foundation/ --cov=app.agents.onboarding --cov=app.services.onboarding_orchestrator --cov-report=html

# Run specific test
poetry run pytest backend/tests/test_onboarding_agent_foundation/test_orchestrator.py::test_step_to_agent_mapping_property
```

## Implementation Notes

### Dependencies

New dependencies required:

```toml
[tool.poetry.dependencies]
langchain = "^0.1.0"
langchain-anthropic = "^0.1.0"
langchain-core = "^0.1.0"

[tool.poetry.group.dev.dependencies]
hypothesis = "^6.92.0"
```

Add with:
```bash
poetry add langchain langchain-anthropic langchain-core
poetry add --group dev hypothesis
```

### File Structure

```
backend/app/
├── agents/
│   └── onboarding/
│       ├── __init__.py
│       ├── base.py                    # BaseOnboardingAgent
│       ├── fitness_assessment.py      # Stub implementation
│       ├── goal_setting.py            # Stub implementation
│       ├── workout_planning.py        # Stub implementation
│       ├── diet_planning.py           # Stub implementation
│       └── scheduling.py              # Stub implementation
├── api/v1/endpoints/
│   └── onboarding.py                  # Enhanced with chat endpoints
├── models/
│   └── onboarding.py                  # Enhanced OnboardingState model
├── schemas/
│   └── onboarding.py                  # New request/response schemas
└── services/
    └── onboarding_orchestrator.py     # New orchestrator service
```

### Configuration

Add to `app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LLM Configuration
    ANTHROPIC_API_KEY: str
    LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
```

### Deployment Considerations

1. **Database Migration**: Run migration during maintenance window
2. **API Versioning**: New endpoints are additive, no breaking changes
3. **Feature Flag**: Consider feature flag for gradual rollout
4. **Monitoring**: Add metrics for agent response times and error rates
5. **Rollback Plan**: Migration can be rolled back safely

### Performance Targets

- Agent response time: < 2 seconds (p95)
- Database query time: < 50ms (p95)
- API endpoint latency: < 2.5 seconds (p95)
- Context loading: < 100ms (p95)

### Security Considerations

1. **Authentication**: All endpoints require valid JWT
2. **Authorization**: Users can only access their own onboarding state
3. **Input Validation**: All user input validated by Pydantic schemas
4. **SQL Injection**: Protected by SQLAlchemy parameterized queries
5. **API Key Security**: Anthropic API key stored in environment variables
6. **Rate Limiting**: Consider rate limiting for chat endpoint (future enhancement)

### Monitoring and Logging

Log the following events:
- Agent routing decisions (step → agent type)
- LLM API calls (duration, tokens used)
- Database errors
- Authentication failures
- Validation errors

Metrics to track:
- Chat endpoint request rate
- Agent response time distribution
- Error rate by error type
- Context save success rate
- LLM API latency

## Future Enhancements

This foundation enables future enhancements:

1. **Agent Implementations**: Specs 2-4 will implement the five specialized agents
2. **Streaming Responses**: Add streaming support for real-time chat experience
3. **Voice Integration**: Connect to LiveKit for voice-based onboarding
4. **Multi-language Support**: Add i18n for system prompts and responses
5. **Agent Analytics**: Track which questions agents ask most frequently
6. **Context Compression**: Implement context summarization for long conversations
7. **A/B Testing**: Test different system prompts and agent behaviors

## Conclusion

The Onboarding Agent Foundation provides a robust, extensible infrastructure for conversational onboarding. The architecture separates concerns cleanly, maintains backward compatibility, and enables easy addition of new agent types. The dual testing approach ensures both specific correctness and general properties hold across all inputs.

This foundation is production-ready and provides the base for implementing the five specialized agents in subsequent specifications.

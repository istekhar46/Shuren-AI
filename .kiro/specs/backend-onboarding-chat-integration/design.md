# Backend Onboarding Chat Integration - Design Document

**Feature Name:** backend-onboarding-chat-integration  
**Status:** Draft  
**Created:** 2026-02-11  
**Last Updated:** 2026-02-11

---

## 1. Overview

This design document specifies the technical implementation for enabling chat-based onboarding with specialized AI agents in the Shuren backend. The implementation consolidates the existing 11-step onboarding flow into 9 states aligned with agent responsibilities, adds new endpoints for chat-driven onboarding, and implements agent function tools for data persistence.

### 1.1 Design Goals

- Enable conversational onboarding through specialized agents
- Maintain backward compatibility with existing REST API
- Provide rich progress tracking for frontend UI
- Implement robust access control based on onboarding status
- Ensure data consistency during agent-driven interactions

### 1.2 Key Design Decisions

**Decision 1: Agent Function Tools vs Direct Database Access**
- **Choice:** Agents call existing REST endpoints as function tools
- **Rationale:** Reuses existing validation logic, maintains single source of truth, easier to test and debug
- **Trade-off:** Slight performance overhead vs code duplication

**Decision 2: State Consolidation Strategy**
- **Choice:** Merge steps 4 & 5 (target metrics + constraints) into single state 3
- **Rationale:** Both handled by same agent, reduces user friction, maintains logical grouping
- **Trade-off:** More complex validation for state 3 vs simpler individual states

**Decision 3: Onboarding Mode Flag**
- **Choice:** Add `onboarding_mode` parameter to agent orchestrator
- **Rationale:** Clean separation of onboarding vs post-onboarding routing logic
- **Trade-off:** Additional parameter vs implicit mode detection


## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Mobile/Web)                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP/REST
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Endpoints (v1)                          │  │
│  │  • POST /chat/onboarding (new)                          │  │
│  │  • GET /onboarding/progress (new)                       │  │
│  │  • POST /onboarding/step (modified)                     │  │
│  │  • GET /users/me (modified)                             │  │
│  │  • POST /chat (modified)                                │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │              Service Layer                               │  │
│  │  • OnboardingService (modified)                         │  │
│  │  • AgentOrchestrator (modified)                         │  │
│  │  • ChatService (existing)                               │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │              Agent Layer                                 │  │
│  │  • WorkoutPlannerAgent (with new tools)                 │  │
│  │  • DietPlannerAgent (with new tools)                    │  │
│  │  • SchedulerAgent (with new tools)                      │  │
│  │  • SupplementGuideAgent (with new tools)                │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │              Data Layer                                  │  │
│  │  • OnboardingState (modified constraint)                │  │
│  │  • User, UserProfile (existing)                         │  │
│  │  • Preferences (existing)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                   │
                   │ SQL
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Onboarding Chat Flow:**
```
1. User sends message → POST /chat/onboarding
2. Endpoint validates user is not onboarding_completed
3. Load current onboarding state from database
4. Route to appropriate agent based on current_state
5. Agent processes message with LLM
6. Agent calls function tool (e.g., save_fitness_level)
7. Function tool invokes POST /onboarding/step internally
8. OnboardingService validates and saves data
9. State advances, response returned to user
10. Frontend updates progress UI
```

**Progress Tracking Flow:**
```
1. Frontend requests → GET /onboarding/progress
2. Load OnboardingState from database
3. Calculate completion percentage
4. Fetch state metadata (name, agent, description)
5. Return rich progress object
6. Frontend renders progress indicator
```


## 3. Components and Interfaces

### 3.1 New API Endpoints

#### 3.1.1 Onboarding Progress Endpoint

**Endpoint:** `GET /api/v1/onboarding/progress`

**Purpose:** Provide rich progress metadata for UI indicators

**Implementation Location:** `backend/app/api/v1/endpoints/onboarding.py`

**Request:**
- Method: GET
- Authentication: Required (JWT)
- Headers: `Authorization: Bearer <token>`

**Response Schema:**
```python
class StateInfo(BaseModel):
    state_number: int
    name: str
    agent: str
    description: str
    required_fields: list[str]

class OnboardingProgressResponse(BaseModel):
    current_state: int
    total_states: int = 9
    completed_states: list[int]
    current_state_info: StateInfo
    next_state_info: StateInfo | None
    is_complete: bool
    completion_percentage: int
    can_complete: bool
```

**Business Logic:**
```python
async def get_onboarding_progress(user_id: UUID) -> OnboardingProgressResponse:
    # 1. Load onboarding state
    state = await onboarding_service.get_onboarding_state(user_id)
    
    # 2. Calculate completed states from step_data
    completed = [i for i in range(1, 10) if f"step_{i}" in state.step_data]
    
    # 3. Get current and next state metadata
    current_info = STATE_METADATA[state.current_state]
    next_info = STATE_METADATA.get(state.current_state + 1)
    
    # 4. Calculate completion percentage
    percentage = (len(completed) / 9) * 100
    
    # 5. Check if can complete (all 9 states done)
    can_complete = len(completed) == 9
    
    return OnboardingProgressResponse(...)
```

**State Metadata Constant:**
```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="workout_planning",
        description="Tell us about your current fitness level",
        required_fields=["fitness_level"]
    ),
    2: StateInfo(
        state_number=2,
        name="Primary Fitness Goals",
        agent="workout_planning",
        description="What are your fitness goals?",
        required_fields=["goals"]
    ),
    # ... states 3-9
}
```


#### 3.1.2 Onboarding Chat Endpoint

**Endpoint:** `POST /api/v1/chat/onboarding`

**Purpose:** Handle chat-based onboarding with agent routing

**Implementation Location:** `backend/app/api/v1/endpoints/chat.py`

**Request Schema:**
```python
class OnboardingChatRequest(BaseModel):
    message: str
    current_state: int = Field(ge=1, le=9)
```

**Response Schema:**
```python
class OnboardingChatResponse(BaseModel):
    response: str
    agent_type: str
    state_updated: bool
    new_state: int | None
    progress: dict[str, Any]
```

**Implementation:**
```python
@router.post("/onboarding", response_model=OnboardingChatResponse)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify user is not onboarding_completed
    if current_user.onboarding_completed:
        raise HTTPException(
            status_code=403,
            detail="Onboarding already completed"
        )
    
    # 2. Load onboarding state
    onboarding_service = OnboardingService(db)
    state = await onboarding_service.get_onboarding_state(current_user.id)
    
    # 3. Verify current_state matches
    if state.current_step != request.current_state:
        raise HTTPException(
            status_code=400,
            detail=f"State mismatch. Current: {state.current_step}, Requested: {request.current_state}"
        )
    
    # 4. Route to appropriate agent
    orchestrator = AgentOrchestrator(db, mode="text")
    agent_type = STATE_TO_AGENT_MAP[request.current_state]
    
    # 5. Process query with agent in onboarding mode
    agent_response = await orchestrator.route_query(
        user_id=str(current_user.id),
        query=request.message,
        agent_type=agent_type,
        onboarding_mode=True
    )
    
    # 6. Check if state was updated (agent called save function)
    updated_state = await onboarding_service.get_onboarding_state(current_user.id)
    state_updated = updated_state.current_step > state.current_step
    
    # 7. Get progress
    progress = await get_onboarding_progress(current_user.id)
    
    return OnboardingChatResponse(
        response=agent_response.content,
        agent_type=agent_type.value,
        state_updated=state_updated,
        new_state=updated_state.current_step if state_updated else None,
        progress=progress.dict()
    )
```

**State to Agent Mapping:**
```python
STATE_TO_AGENT_MAP = {
    1: AgentType.WORKOUT,  # Fitness Level
    2: AgentType.WORKOUT,  # Fitness Goals
    3: AgentType.WORKOUT,  # Workout Constraints
    4: AgentType.DIET,     # Dietary Preferences
    5: AgentType.DIET,     # Meal Plan
    6: AgentType.SCHEDULER, # Meal Schedule
    7: AgentType.SCHEDULER, # Workout Schedule
    8: AgentType.SCHEDULER, # Hydration
    9: AgentType.SUPPLEMENT # Supplements (optional)
}
```


### 3.2 Modified API Endpoints

#### 3.2.1 Enhanced User Endpoint

**Endpoint:** `GET /api/v1/users/me`

**Changes:** Add `access_control` object to response

**Implementation Location:** `backend/app/api/v1/endpoints/auth.py`

**New Response Schema:**
```python
class AccessControl(BaseModel):
    can_access_dashboard: bool
    can_access_workouts: bool
    can_access_meals: bool
    can_access_chat: bool
    can_access_profile: bool
    locked_features: list[str]
    unlock_message: str | None
    onboarding_progress: dict[str, Any] | None

class UserResponse(BaseModel):
    id: str
    email: str
    onboarding_completed: bool
    access_control: AccessControl
    # ... existing fields
```

**Implementation:**
```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Build access control object
    if current_user.onboarding_completed:
        access_control = AccessControl(
            can_access_dashboard=True,
            can_access_workouts=True,
            can_access_meals=True,
            can_access_chat=True,
            can_access_profile=True,
            locked_features=[],
            unlock_message=None,
            onboarding_progress=None
        )
    else:
        # Get onboarding progress
        onboarding_service = OnboardingService(db)
        progress = await get_onboarding_progress(current_user.id)
        
        access_control = AccessControl(
            can_access_dashboard=False,
            can_access_workouts=False,
            can_access_meals=False,
            can_access_chat=True,  # Always true
            can_access_profile=False,
            locked_features=["dashboard", "workouts", "meals", "profile"],
            unlock_message="Complete onboarding to unlock all features",
            onboarding_progress=progress.dict()
        )
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        onboarding_completed=current_user.onboarding_completed,
        access_control=access_control,
        # ... other fields
    )
```


#### 3.2.2 Updated Onboarding Step Endpoint

**Endpoint:** `POST /api/v1/onboarding/step`

**Changes:** Support 9 states instead of 11, accept agent context header

**Implementation Location:** `backend/app/api/v1/endpoints/onboarding.py`

**Request Schema:**
```python
class OnboardingStepRequest(BaseModel):
    step: int = Field(ge=1, le=9)  # Changed from le=11
    data: dict[str, Any]
```

**Request Headers:**
```
X-Agent-Context: workout_planning (optional)
```

**Implementation:**
```python
@router.post("/step", response_model=OnboardingStepResponse)
async def save_onboarding_step(
    request: OnboardingStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_context: str | None = Header(None, alias="X-Agent-Context")
):
    # Log agent context if provided
    if agent_context:
        logger.info(
            f"Onboarding step {request.step} called by agent: {agent_context}",
            extra={"user_id": str(current_user.id), "agent": agent_context}
        )
    
    try:
        # Save step using service
        onboarding_service = OnboardingService(db)
        state = await onboarding_service.save_onboarding_step(
            user_id=current_user.id,
            step=request.step,
            data=request.data
        )
        
        # Get next state info
        next_state = request.step + 1 if request.step < 9 else None
        next_state_info = STATE_METADATA.get(next_state) if next_state else None
        
        return OnboardingStepResponse(
            current_step=state.current_step,
            is_complete=state.is_complete,
            message=f"State {request.step} saved successfully",
            next_state=next_state,
            next_state_info=next_state_info
        )
        
    except OnboardingValidationError as e:
        # Return structured validation error
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "field": e.field,
                "error_code": "VALIDATION_ERROR"
            }
        )
```


#### 3.2.3 Chat Endpoint with Agent Restrictions

**Endpoint:** `POST /api/v1/chat`

**Changes:** Enforce agent access control based on onboarding status

**Implementation Location:** `backend/app/api/v1/endpoints/chat.py`

**Implementation:**
```python
@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check onboarding status
    if not current_user.onboarding_completed:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Complete onboarding first",
                "error_code": "ONBOARDING_REQUIRED",
                "redirect": "/onboarding"
            }
        )
    
    # If explicit agent_type provided, reject (only general agent allowed)
    if request.agent_type and request.agent_type != "general":
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Only general agent available after onboarding",
                "error_code": "AGENT_NOT_ALLOWED"
            }
        )
    
    # Force general agent
    orchestrator = AgentOrchestrator(db, mode="text")
    response = await orchestrator.route_query(
        user_id=str(current_user.id),
        query=request.message,
        agent_type=AgentType.GENERAL,  # Always general
        onboarding_mode=False
    )
    
    return ChatResponse(
        response=response.content,
        agent_type="general",
        # ... other fields
    )
```


### 3.3 Service Layer Changes

#### 3.3.1 OnboardingService Updates

**File:** `backend/app/services/onboarding_service.py`

**New Methods:**

```python
async def get_progress(self, user_id: UUID) -> OnboardingProgress:
    """Get rich progress metadata for UI.
    
    Returns:
        OnboardingProgress with current state, completed states,
        state metadata, and completion percentage
    """
    state = await self.get_onboarding_state(user_id)
    
    # Extract completed states from step_data
    completed = []
    for i in range(1, 10):
        if f"step_{i}" in state.step_data:
            completed.append(i)
    
    # Get state metadata
    current_info = STATE_METADATA[state.current_step]
    next_state = state.current_step + 1 if state.current_step < 9 else None
    next_info = STATE_METADATA.get(next_state)
    
    # Calculate percentage
    percentage = int((len(completed) / 9) * 100)
    
    # Check if can complete
    can_complete = len(completed) == 9
    
    return OnboardingProgress(
        current_state=state.current_step,
        total_states=9,
        completed_states=completed,
        current_state_info=current_info,
        next_state_info=next_info,
        is_complete=state.is_complete,
        completion_percentage=percentage,
        can_complete=can_complete
    )

async def can_complete_onboarding(self, user_id: UUID) -> bool:
    """Check if all required states are complete.
    
    Returns:
        True if all 9 states have data, False otherwise
    """
    state = await self.get_onboarding_state(user_id)
    
    for i in range(1, 10):
        if f"step_{i}" not in state.step_data:
            return False
    
    return True
```

**Updated Validators:**

The existing validators need to be remapped to the new 9-state structure:

```python
def _validate_step_data(self, step: int, data: dict[str, Any]) -> None:
    """Validate step-specific data for 9 states."""
    validators = {
        1: self._validate_state_1_fitness_level,      # Was step 2
        2: self._validate_state_2_fitness_goals,       # Was step 3
        3: self._validate_state_3_workout_constraints, # Merge of steps 4 & 5
        4: self._validate_state_4_dietary_preferences, # Was step 6
        5: self._validate_state_5_meal_plan,           # Was step 7
        6: self._validate_state_6_meal_schedule,       # Was step 8
        7: self._validate_state_7_workout_schedule,    # Was step 9
        8: self._validate_state_8_hydration,           # Was step 10
        9: self._validate_state_9_supplements,         # Was step 11
    }
    
    validator = validators.get(step)
    if validator:
        validator(data)
```

**New Merged Validator:**

```python
def _validate_state_3_workout_constraints(self, data: dict[str, Any]) -> None:
    """Validate state 3: Workout constraints (merged from steps 4 & 5).
    
    Combines target metrics and physical constraints validation.
    """
    # Validate equipment (required)
    if "equipment" not in data or not isinstance(data["equipment"], list):
        raise OnboardingValidationError("Equipment must be a list", "equipment")
    
    # Validate injuries (required, can be empty)
    if "injuries" not in data or not isinstance(data["injuries"], list):
        raise OnboardingValidationError("Injuries must be a list", "injuries")
    
    # Validate limitations (required, can be empty)
    if "limitations" not in data or not isinstance(data["limitations"], list):
        raise OnboardingValidationError("Limitations must be a list", "limitations")
    
    # Validate optional target metrics
    if "target_weight_kg" in data and data["target_weight_kg"] is not None:
        weight = data["target_weight_kg"]
        if not isinstance(weight, (int, float)) or weight < 30 or weight > 300:
            raise OnboardingValidationError(
                "Target weight must be between 30 and 300 kg",
                "target_weight_kg"
            )
    
    if "target_body_fat_percentage" in data and data["target_body_fat_percentage"] is not None:
        bf = data["target_body_fat_percentage"]
        if not isinstance(bf, (int, float)) or bf < 1 or bf > 50:
            raise OnboardingValidationError(
                "Target body fat percentage must be between 1 and 50",
                "target_body_fat_percentage"
            )
```


#### 3.3.2 AgentOrchestrator Updates

**File:** `backend/app/services/agent_orchestrator.py`

**Modified Method Signature:**

```python
async def route_query(
    self,
    user_id: str,
    query: str,
    agent_type: Optional[AgentType] = None,
    voice_mode: bool = False,
    onboarding_mode: bool = False  # NEW PARAMETER
) -> "AgentResponse":
    """Route a user query to the appropriate agent.
    
    Args:
        user_id: User's unique identifier
        query: User's query text
        agent_type: Optional explicit agent type
        voice_mode: Whether this is a voice interaction
        onboarding_mode: Whether this is during onboarding (NEW)
    
    Returns:
        AgentResponse from the agent
    """
    # Load user context
    from app.services.context_loader import load_agent_context
    from app.agents.context import AgentResponse
    
    context = await load_agent_context(
        db=self.db_session,
        user_id=user_id,
        include_history=True
    )
    
    # Get user to check onboarding status
    from app.models.auth import User
    from sqlalchemy import select
    
    result = await self.db_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    # Enforce access control
    if onboarding_mode:
        # During onboarding: allow specialized agents
        if user.onboarding_completed:
            raise ValueError("Onboarding already completed")
        # Allow specified agent_type
    else:
        # Post-onboarding: enforce restrictions
        if not user.onboarding_completed:
            raise ValueError("Complete onboarding first")
        
        # Force general agent
        if agent_type and agent_type != AgentType.GENERAL:
            raise ValueError("Only general agent available post-onboarding")
        
        agent_type = AgentType.GENERAL
    
    # Classify if needed
    if agent_type is None:
        agent_type = await self._classify_query(query)
    
    # Get or create agent
    agent = self._get_or_create_agent(agent_type, context)
    
    # Process based on mode
    if voice_mode:
        response_content = await agent.process_voice(query)
        response = AgentResponse(
            content=response_content,
            agent_type=agent_type.value,
            tools_used=[],
            metadata={
                "mode": "voice",
                "user_id": user_id,
                "onboarding_mode": onboarding_mode
            }
        )
    else:
        response = await agent.process_text(query)
    
    self.last_agent_type = agent_type
    
    return response
```


### 3.4 Agent Function Tools

Each specialized agent needs function tools to save onboarding data. These tools wrap the existing `POST /onboarding/step` endpoint.

#### 3.4.1 Common Helper Function

**File:** `backend/app/agents/onboarding_tools.py` (new file)

```python
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
    
    Args:
        db: Database session
        user_id: User's UUID
        step: Step number (1-9)
        data: Step data to save
        agent_type: Agent type calling this function (for logging)
    
    Returns:
        Success/error response dict
    """
    try:
        # Log agent context
        logger.info(
            f"Agent {agent_type} saving onboarding step {step}",
            extra={"user_id": str(user_id), "agent": agent_type, "step": step}
        )
        
        # Save step
        service = OnboardingService(db)
        state = await service.save_onboarding_step(
            user_id=user_id,
            step=step,
            data=data
        )
        
        # Return success
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
```


#### 3.4.2 Workout Planning Agent Tools

**File:** `backend/app/agents/workout_planner.py` (modifications)

```python
from app.agents.onboarding_tools import call_onboarding_step

class WorkoutPlannerAgent(BaseAgent):
    """Workout Planning Agent with onboarding tools."""
    
    def _get_tools(self) -> list:
        """Get agent-specific tools including onboarding tools."""
        tools = super()._get_tools()
        
        # Add onboarding tools
        tools.extend([
            self.save_fitness_level,
            self.save_fitness_goals,
            self.save_workout_constraints
        ])
        
        return tools
    
    async def save_fitness_level(
        self,
        fitness_level: Literal["beginner", "intermediate", "advanced"]
    ) -> dict:
        """Save user's fitness level (State 1).
        
        Args:
            fitness_level: User's current fitness level
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=1,
            data={"fitness_level": fitness_level},
            agent_type="workout_planning"
        )
    
    async def save_fitness_goals(
        self,
        goals: list[dict]
    ) -> dict:
        """Save user's fitness goals (State 2).
        
        Args:
            goals: List of goal objects with goal_type, priority
                   Example: [{"goal_type": "fat_loss", "priority": 1}]
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=2,
            data={"goals": goals},
            agent_type="workout_planning"
        )
    
    async def save_workout_constraints(
        self,
        equipment: list[str],
        injuries: list[str],
        limitations: list[str],
        target_weight_kg: float | None = None,
        target_body_fat_percentage: float | None = None
    ) -> dict:
        """Save workout constraints and optional targets (State 3).
        
        Args:
            equipment: Available equipment (e.g., ["dumbbells", "resistance_bands"])
            injuries: Current injuries (can be empty list)
            limitations: Physical limitations (can be empty list)
            target_weight_kg: Optional target weight
            target_body_fat_percentage: Optional target body fat %
        
        Returns:
            Success/error response dict
        """
        data = {
            "equipment": equipment,
            "injuries": injuries,
            "limitations": limitations
        }
        
        if target_weight_kg is not None:
            data["target_weight_kg"] = target_weight_kg
        
        if target_body_fat_percentage is not None:
            data["target_body_fat_percentage"] = target_body_fat_percentage
        
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=3,
            data=data,
            agent_type="workout_planning"
        )
```


#### 3.4.3 Diet Planning Agent Tools

**File:** `backend/app/agents/diet_planner.py` (modifications)

```python
from app.agents.onboarding_tools import call_onboarding_step

class DietPlannerAgent(BaseAgent):
    """Diet Planning Agent with onboarding tools."""
    
    def _get_tools(self) -> list:
        """Get agent-specific tools including onboarding tools."""
        tools = super()._get_tools()
        
        tools.extend([
            self.save_dietary_preferences,
            self.save_meal_plan
        ])
        
        return tools
    
    async def save_dietary_preferences(
        self,
        diet_type: Literal["omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo"],
        allergies: list[str],
        intolerances: list[str],
        dislikes: list[str]
    ) -> dict:
        """Save dietary preferences and restrictions (State 4).
        
        Args:
            diet_type: Type of diet user follows
            allergies: Food allergies (can be empty)
            intolerances: Food intolerances (can be empty)
            dislikes: Foods user dislikes (can be empty)
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=4,
            data={
                "diet_type": diet_type,
                "allergies": allergies,
                "intolerances": intolerances,
                "dislikes": dislikes
            },
            agent_type="diet_planning"
        )
    
    async def save_meal_plan(
        self,
        daily_calorie_target: int,
        protein_percentage: float,
        carbs_percentage: float,
        fats_percentage: float
    ) -> dict:
        """Save meal plan with calorie and macro targets (State 5).
        
        Args:
            daily_calorie_target: Daily calorie goal (1000-5000)
            protein_percentage: Protein % of calories (0-100)
            carbs_percentage: Carbs % of calories (0-100)
            fats_percentage: Fats % of calories (0-100)
            
        Note: Percentages must sum to 100
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=5,
            data={
                "daily_calorie_target": daily_calorie_target,
                "protein_percentage": protein_percentage,
                "carbs_percentage": carbs_percentage,
                "fats_percentage": fats_percentage
            },
            agent_type="diet_planning"
        )
```


#### 3.4.4 Scheduler Agent Tools

**File:** `backend/app/agents/scheduler.py` (modifications)

```python
from app.agents.onboarding_tools import call_onboarding_step

class SchedulerAgent(BaseAgent):
    """Scheduling & Reminder Agent with onboarding tools."""
    
    def _get_tools(self) -> list:
        """Get agent-specific tools including onboarding tools."""
        tools = super()._get_tools()
        
        tools.extend([
            self.save_meal_schedule,
            self.save_workout_schedule,
            self.save_hydration_schedule
        ])
        
        return tools
    
    async def save_meal_schedule(
        self,
        meals: list[dict]
    ) -> dict:
        """Save meal timing schedule (State 6).
        
        Args:
            meals: List of meal objects
                   Example: [
                       {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": true},
                       {"meal_name": "Lunch", "scheduled_time": "13:00", "enable_notifications": true}
                   ]
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=6,
            data={"meals": meals},
            agent_type="scheduler"
        )
    
    async def save_workout_schedule(
        self,
        workouts: list[dict]
    ) -> dict:
        """Save workout schedule (State 7).
        
        Args:
            workouts: List of workout objects
                      Example: [
                          {"day_of_week": 1, "scheduled_time": "07:00", "enable_notifications": true},
                          {"day_of_week": 3, "scheduled_time": "07:00", "enable_notifications": true}
                      ]
                      day_of_week: 0=Monday, 6=Sunday
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=7,
            data={"workouts": workouts},
            agent_type="scheduler"
        )
    
    async def save_hydration_schedule(
        self,
        daily_water_target_ml: int,
        reminder_frequency_minutes: int
    ) -> dict:
        """Save hydration preferences (State 8).
        
        Args:
            daily_water_target_ml: Daily water intake goal in ml (500-10000)
            reminder_frequency_minutes: How often to remind (15-480 minutes)
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=8,
            data={
                "daily_water_target_ml": daily_water_target_ml,
                "reminder_frequency_minutes": reminder_frequency_minutes
            },
            agent_type="scheduler"
        )
```


#### 3.4.5 Supplement Guide Agent Tools

**File:** `backend/app/agents/supplement_guide.py` (modifications)

```python
from app.agents.onboarding_tools import call_onboarding_step

class SupplementGuideAgent(BaseAgent):
    """Supplement Guidance Agent with onboarding tools."""
    
    def _get_tools(self) -> list:
        """Get agent-specific tools including onboarding tools."""
        tools = super()._get_tools()
        
        tools.extend([
            self.save_supplement_preferences
        ])
        
        return tools
    
    async def save_supplement_preferences(
        self,
        interested_in_supplements: bool,
        current_supplements: list[str] = []
    ) -> dict:
        """Save supplement preferences (State 9 - Optional).
        
        Args:
            interested_in_supplements: Whether user wants supplement guidance
            current_supplements: List of supplements currently taking (optional)
        
        Returns:
            Success/error response dict
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=9,
            data={
                "interested_in_supplements": interested_in_supplements,
                "current_supplements": current_supplements
            },
            agent_type="supplement"
        )
```


## 4. Data Models

### 4.1 Database Schema Changes

#### 4.1.1 OnboardingState Model

**File:** `backend/app/models/onboarding.py`

**Changes:**
```python
class OnboardingState(BaseModel):
    """Onboarding state entity tracking user progress through onboarding flow.
    
    Tracks the current step (0-9) and stores step data in JSONB format.
    Each user has exactly one onboarding state.
    """
    
    __tablename__ = "onboarding_states"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # CHANGED: current_step now 0-9 instead of 0-11
    current_step = Column(Integer, default=0, nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)
    
    # Step data stored as JSONB
    # Format: {"step_1": {...}, "step_2": {...}, ..., "step_9": {...}}
    step_data = Column(JSONB, default=dict, nullable=False)
    
    # NEW: Track agent routing history for analytics
    agent_history = Column(JSONB, default=list, nullable=False)
    # Format: [{"state": 1, "agent": "workout_planning", "timestamp": "..."}]
    
    user = relationship("User", back_populates="onboarding_state")
    
    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_onboarding'),
        Index('idx_onboarding_user', 'user_id', postgresql_where=(Column('deleted_at').is_(None))),
        # NEW: Check constraint for valid step range
        CheckConstraint('current_step >= 0 AND current_step <= 9', name='valid_current_step')
    )
```

**Migration Required:**
- Add `agent_history` column (JSONB, default=[])
- Update check constraint from `current_step <= 11` to `current_step <= 9`
- Migrate existing data (see section 4.2)


### 4.2 Data Migration Strategy

#### 4.2.1 Migration Script

**File:** `backend/alembic/versions/xxxx_consolidate_onboarding_states.py`

```python
"""Consolidate onboarding from 11 steps to 9 states

Revision ID: xxxx
Revises: yyyy
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # 1. Add agent_history column
    op.add_column(
        'onboarding_states',
        sa.Column('agent_history', postgresql.JSONB, nullable=False, server_default='[]')
    )
    
    # 2. Drop old constraint
    op.drop_constraint('valid_current_step', 'onboarding_states', type_='check')
    
    # 3. Migrate data (11 steps → 9 states)
    # This is done via Python script to handle JSONB manipulation
    connection = op.get_bind()
    
    # Get all onboarding states
    result = connection.execute(
        sa.text("SELECT id, step_data, current_step FROM onboarding_states WHERE deleted_at IS NULL")
    )
    
    for row in result:
        state_id = row[0]
        step_data = row[1] or {}
        current_step = row[2]
        
        # Create new step_data mapping
        new_step_data = {}
        
        # Step 1 (basic_info) → Remove (moved to User model during registration)
        # Step 2 (fitness_level) → State 1
        if "step_2" in step_data:
            new_step_data["step_1"] = step_data["step_2"]
        
        # Step 3 (fitness_goals) → State 2
        if "step_3" in step_data:
            new_step_data["step_2"] = step_data["step_3"]
        
        # Steps 4 & 5 (target_metrics + constraints) → State 3 (merged)
        if "step_4" in step_data or "step_5" in step_data:
            merged_data = {}
            
            # From step 4 (target metrics)
            if "step_4" in step_data:
                step_4_data = step_data["step_4"]
                if "target_weight_kg" in step_4_data:
                    merged_data["target_weight_kg"] = step_4_data["target_weight_kg"]
                if "target_body_fat_percentage" in step_4_data:
                    merged_data["target_body_fat_percentage"] = step_4_data["target_body_fat_percentage"]
            
            # From step 5 (constraints)
            if "step_5" in step_data:
                step_5_data = step_data["step_5"]
                # Extract equipment, injuries, limitations from constraints list
                constraints = step_5_data.get("constraints", [])
                equipment = [c["description"] for c in constraints if c.get("constraint_type") == "equipment"]
                injuries = [c["description"] for c in constraints if c.get("constraint_type") == "injury"]
                limitations = [c["description"] for c in constraints if c.get("constraint_type") == "limitation"]
                
                merged_data["equipment"] = equipment
                merged_data["injuries"] = injuries
                merged_data["limitations"] = limitations
            
            new_step_data["step_3"] = merged_data
        
        # Step 6 (dietary_preferences) → State 4
        if "step_6" in step_data:
            new_step_data["step_4"] = step_data["step_6"]
        
        # Step 7 (meal_planning) → State 5
        if "step_7" in step_data:
            new_step_data["step_5"] = step_data["step_7"]
        
        # Step 8 (meal_schedule) → State 6
        if "step_8" in step_data:
            new_step_data["step_6"] = step_data["step_8"]
        
        # Step 9 (workout_schedule) → State 7
        if "step_9" in step_data:
            new_step_data["step_7"] = step_data["step_9"]
        
        # Step 10 (hydration) → State 8
        if "step_10" in step_data:
            new_step_data["step_8"] = step_data["step_10"]
        
        # Step 11 (lifestyle_baseline) → State 9
        if "step_11" in step_data:
            new_step_data["step_9"] = step_data["step_11"]
        
        # Calculate new current_step
        new_current_step = 0
        if current_step >= 2:
            new_current_step = 1
        if current_step >= 3:
            new_current_step = 2
        if current_step >= 5:  # Steps 4 & 5 merged
            new_current_step = 3
        if current_step >= 6:
            new_current_step = 4
        if current_step >= 7:
            new_current_step = 5
        if current_step >= 8:
            new_current_step = 6
        if current_step >= 9:
            new_current_step = 7
        if current_step >= 10:
            new_current_step = 8
        if current_step >= 11:
            new_current_step = 9
        
        # Preserve original data in metadata for rollback
        new_step_data["_migration_metadata"] = {
            "original_step_data": step_data,
            "original_current_step": current_step,
            "migrated_at": sa.func.now()
        }
        
        # Update record
        connection.execute(
            sa.text(
                "UPDATE onboarding_states SET step_data = :step_data, current_step = :current_step WHERE id = :id"
            ),
            {"step_data": new_step_data, "current_step": new_current_step, "id": state_id}
        )
    
    # 4. Add new constraint
    op.create_check_constraint(
        'valid_current_step',
        'onboarding_states',
        'current_step >= 0 AND current_step <= 9'
    )


def downgrade():
    # Rollback migration
    # 1. Drop new constraint
    op.drop_constraint('valid_current_step', 'onboarding_states', type_='check')
    
    # 2. Restore original data from _migration_metadata
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT id, step_data FROM onboarding_states WHERE deleted_at IS NULL")
    )
    
    for row in result:
        state_id = row[0]
        step_data = row[1] or {}
        
        if "_migration_metadata" in step_data:
            original_data = step_data["_migration_metadata"]["original_step_data"]
            original_step = step_data["_migration_metadata"]["original_current_step"]
            
            connection.execute(
                sa.text(
                    "UPDATE onboarding_states SET step_data = :step_data, current_step = :current_step WHERE id = :id"
                ),
                {"step_data": original_data, "current_step": original_step, "id": state_id}
            )
    
    # 3. Add old constraint
    op.create_check_constraint(
        'valid_current_step',
        'onboarding_states',
        'current_step >= 0 AND current_step <= 11'
    )
    
    # 4. Drop agent_history column
    op.drop_column('onboarding_states', 'agent_history')
```


## 5. Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### 5.1 State Routing Properties

**Property 1: State-to-Agent Mapping Consistency**

*For any* onboarding state number (1-9), the system SHALL route to the correct specialized agent according to the state-to-agent mapping.

**Validates: Requirements 2.1.2**

**Property 2: Onboarding Mode Access Control**

*For any* user with `onboarding_completed = false`, the chat onboarding endpoint SHALL allow access to specialized agents, and *for any* user with `onboarding_completed = true`, the endpoint SHALL reject requests with 403 error.

**Validates: Requirements 2.1.1, 2.4.1**

### 5.2 Data Validation Properties

**Property 3: Validation Before Persistence**

*For any* invalid onboarding data submitted to any state, the system SHALL reject the data with a validation error before making any database changes.

**Validates: Requirements 2.1.3**

**Property 4: Agent Error Response Structure**

*For any* validation error encountered by an agent function tool, the response SHALL contain `success: false`, an `error` message, and the `field` that failed validation.

**Validates: Requirements 2.3.2**

### 5.3 Progress Tracking Properties

**Property 5: Progress Endpoint Completeness**

*For any* user with an onboarding state, the progress endpoint SHALL return all required fields: `current_state` (1-9), `completed_states` list, `current_state_info`, `completion_percentage`, and `agent_type` for the current state.

**Validates: Requirements 2.2.1, 2.2.2, 2.2.3, 2.2.5**

**Property 6: Completion Percentage Calculation**

*For any* set of completed onboarding states, the completion percentage SHALL equal `(number_of_completed_states / 9) * 100`.

**Validates: Requirements 2.2.4**

**Property 7: State Confirmation Response**

*For any* successfully saved onboarding state, the response SHALL include confirmation message and next state information.

**Validates: Requirements 2.1.4, 2.3.5**

### 5.4 Resumability Properties

**Property 8: Incremental Progress Persistence**

*For any* onboarding state save operation, if the operation succeeds, the data SHALL be persisted in the database such that querying the state immediately after returns the saved data.

**Validates: Requirements 2.1.5**

**Property 9: Idempotent State Saves**

*For any* onboarding state and data, saving the same state with the same data multiple times SHALL result in the same final state (idempotent operation).

**Validates: Requirements 2.1.5**


### 5.5 Access Control Properties

**Property 10: Post-Onboarding Agent Restriction**

*For any* completed user (onboarding_completed = true), attempting to access the regular chat endpoint SHALL route all queries to the general agent, and explicit requests for specialized agents SHALL return 403 error.

**Validates: Requirements 2.4.1, 2.4.2**

**Property 11: Feature Lock Enforcement**

*For any* user with `onboarding_completed = false`, the access_control object SHALL have `can_access_chat = true` and all other `can_access_*` flags set to `false`.

**Validates: Requirements 2.4.4**

**Property 12: Feature Unlock on Completion**

*For any* user with `onboarding_completed = true`, the access_control object SHALL have all `can_access_*` flags set to `true` and `locked_features` as an empty list.

**Validates: Requirements 2.4.4**

### 5.6 Logging and Observability Properties

**Property 13: Agent Context Logging**

*For any* agent function tool call or onboarding step save operation, the system SHALL log the operation with agent context information (agent type, user_id, step number).

**Validates: Requirements 2.3.4, 2.5.3, 2.5.5**

**Property 14: Agent Routing History Tracking**

*For any* onboarding state update via agent, the system SHALL record the agent type and timestamp in the `agent_history` field.

**Validates: Requirements 2.5.2**

**Property 15: Conversation Message Agent Attribution**

*For any* chat message during onboarding, the response SHALL include the `agent_type` field identifying which agent handled the query.

**Validates: Requirements 2.5.1**

### 5.7 Function Tool Properties

**Property 16: Agent Function Tool Invocation**

*For any* agent with onboarding function tools, calling a tool SHALL successfully invoke the corresponding REST endpoint and return a structured response.

**Validates: Requirements 2.3.1**


## 6. Error Handling

### 6.1 Error Response Format

All errors follow a consistent structure:

```python
class ErrorResponse(BaseModel):
    detail: str | dict
    error_code: str
    field: str | None = None  # For validation errors
    request_id: str | None = None  # For server errors
```

### 6.2 Error Scenarios

#### 6.2.1 Validation Errors (400)

**Trigger:** Invalid data submitted to onboarding step

**Response:**
```json
{
  "detail": {
    "message": "Protein percentage must be between 0 and 100",
    "field": "protein_percentage",
    "error_code": "VALIDATION_ERROR"
  }
}
```

**Handling:**
- OnboardingService raises `OnboardingValidationError`
- Endpoint catches and converts to HTTP 400
- Agent function tools return `{"success": false, "error": "...", "field": "..."}`

#### 6.2.2 Access Control Errors (403)

**Scenarios:**
1. Accessing chat endpoint before onboarding complete
2. Accessing onboarding chat after completion
3. Requesting specialized agent post-onboarding

**Response:**
```json
{
  "detail": "Complete onboarding to access this feature",
  "error_code": "ONBOARDING_REQUIRED",
  "onboarding_progress": {
    "current_state": 3,
    "completion_percentage": 33
  }
}
```

**Handling:**
- Check `user.onboarding_completed` at endpoint level
- Raise `HTTPException(403, detail=...)`
- Include helpful context (progress, redirect URL)

#### 6.2.3 State Mismatch Errors (400)

**Trigger:** Frontend sends `current_state` that doesn't match backend state

**Response:**
```json
{
  "detail": "State mismatch. Current: 5, Requested: 3",
  "error_code": "STATE_MISMATCH",
  "current_state": 5
}
```

**Handling:**
- Verify `request.current_state == onboarding_state.current_step`
- Return current state to help frontend sync

#### 6.2.4 Not Found Errors (404)

**Trigger:** Onboarding state not found for user

**Response:**
```json
{
  "detail": "Onboarding state not found",
  "error_code": "NOT_FOUND"
}
```

**Handling:**
- Check if `get_onboarding_state()` returns None
- Raise `HTTPException(404, detail=...)`

#### 6.2.5 Server Errors (500)

**Trigger:** Unexpected exceptions, database failures, agent errors

**Response:**
```json
{
  "detail": "An unexpected error occurred",
  "error_code": "INTERNAL_ERROR",
  "request_id": "uuid-here"
}
```

**Handling:**
- Catch all unexpected exceptions at endpoint level
- Log full stack trace with request_id
- Return generic error to client
- Alert monitoring system

### 6.3 Error Logging Strategy

```python
# Validation errors: INFO level (expected)
logger.info(
    f"Validation error in step {step}: {error.message}",
    extra={"user_id": user_id, "field": error.field}
)

# Access control errors: WARNING level (potential abuse)
logger.warning(
    f"Access denied: {reason}",
    extra={"user_id": user_id, "endpoint": endpoint}
)

# Server errors: ERROR level (requires investigation)
logger.error(
    f"Unexpected error: {error}",
    extra={"user_id": user_id, "request_id": request_id},
    exc_info=True
)
```


## 7. Testing Strategy

### 7.1 Testing Approach

This feature requires both unit tests and property-based tests to ensure correctness:

- **Unit tests**: Verify specific examples, edge cases, and integration points
- **Property tests**: Verify universal properties across all inputs using Hypothesis

### 7.2 Unit Testing

**Focus Areas:**
- Specific endpoint behavior with known inputs
- Error handling for specific scenarios
- Integration between components
- Edge cases (empty lists, boundary values)

**Example Unit Tests:**

```python
# Test onboarding progress endpoint
async def test_get_onboarding_progress_returns_correct_structure(authenticated_client):
    client, user = authenticated_client
    response = await client.get("/api/v1/onboarding/progress")
    assert response.status_code == 200
    data = response.json()
    assert "current_state" in data
    assert "completion_percentage" in data
    assert data["total_states"] == 9

# Test access control
async def test_chat_endpoint_rejects_incomplete_onboarding(authenticated_client):
    client, user = authenticated_client
    # User has onboarding_completed = False
    response = await client.post("/api/v1/chat", json={"message": "Hello"})
    assert response.status_code == 403
    assert "ONBOARDING_REQUIRED" in response.json()["error_code"]

# Test state consolidation
async def test_save_state_3_merges_constraints_and_targets(db_session, test_user):
    service = OnboardingService(db_session)
    data = {
        "equipment": ["dumbbells"],
        "injuries": [],
        "limitations": ["lower_back_pain"],
        "target_weight_kg": 75.0
    }
    state = await service.save_onboarding_step(test_user.id, 3, data)
    assert state.current_step == 3
    assert "step_3" in state.step_data
```

### 7.3 Property-Based Testing

**Configuration:**
- Minimum 100 iterations per property test
- Use Hypothesis for input generation
- Tag each test with feature name and property number

**Property Test Examples:**

```python
from hypothesis import given, strategies as st
import pytest

# Property 1: State-to-Agent Mapping Consistency
@given(state=st.integers(min_value=1, max_value=9))
@pytest.mark.property
async def test_property_1_state_to_agent_mapping(state: int, db_session):
    """
    Feature: backend-onboarding-chat-integration, Property 1
    For any onboarding state (1-9), verify correct agent is selected
    """
    expected_agents = {
        1: "workout", 2: "workout", 3: "workout",
        4: "diet", 5: "diet",
        6: "scheduler", 7: "scheduler", 8: "scheduler",
        9: "supplement"
    }
    
    agent_type = STATE_TO_AGENT_MAP[state]
    assert agent_type.value == expected_agents[state]

# Property 6: Completion Percentage Calculation
@given(completed_states=st.lists(st.integers(min_value=1, max_value=9), unique=True))
@pytest.mark.property
async def test_property_6_completion_percentage(completed_states: list[int], db_session, test_user):
    """
    Feature: backend-onboarding-chat-integration, Property 6
    For any set of completed states, percentage = (completed/9)*100
    """
    # Setup: save completed states
    service = OnboardingService(db_session)
    for state in completed_states:
        await service.save_onboarding_step(test_user.id, state, get_valid_data_for_state(state))
    
    # Get progress
    progress = await service.get_progress(test_user.id)
    
    # Verify calculation
    expected_percentage = int((len(completed_states) / 9) * 100)
    assert progress.completion_percentage == expected_percentage

# Property 8: Incremental Progress Persistence
@given(
    state=st.integers(min_value=1, max_value=9),
    data=st.fixed_dictionaries({})  # Generate valid data based on state
)
@pytest.mark.property
async def test_property_8_incremental_persistence(state: int, data: dict, db_session, test_user):
    """
    Feature: backend-onboarding-chat-integration, Property 8
    For any state save, data persists and is immediately queryable
    """
    service = OnboardingService(db_session)
    
    # Save state
    await service.save_onboarding_step(test_user.id, state, data)
    
    # Query immediately
    retrieved_state = await service.get_onboarding_state(test_user.id)
    
    # Verify persistence
    assert f"step_{state}" in retrieved_state.step_data
    assert retrieved_state.step_data[f"step_{state}"] == data

# Property 13: Agent Context Logging
@given(
    state=st.integers(min_value=1, max_value=9),
    agent_type=st.sampled_from(["workout_planning", "diet_planning", "scheduler", "supplement"])
)
@pytest.mark.property
async def test_property_13_agent_context_logging(state: int, agent_type: str, db_session, test_user, caplog):
    """
    Feature: backend-onboarding-chat-integration, Property 13
    For any agent function call, verify agent context is logged
    """
    from app.agents.onboarding_tools import call_onboarding_step
    
    # Call with agent context
    await call_onboarding_step(
        db=db_session,
        user_id=test_user.id,
        step=state,
        data=get_valid_data_for_state(state),
        agent_type=agent_type
    )
    
    # Verify logging
    assert any(agent_type in record.message for record in caplog.records)
    assert any(str(test_user.id) in str(record) for record in caplog.records)
```

### 7.4 Integration Testing

**Test Scenarios:**
1. Complete onboarding flow via chat (all 9 states)
2. Agent function tools calling REST endpoints
3. State transitions and progress updates
4. Access control enforcement across endpoints
5. Data migration from 11 steps to 9 states

**Example Integration Test:**

```python
async def test_complete_onboarding_via_chat_integration(authenticated_client, db_session):
    """Test full onboarding flow through chat endpoint."""
    client, user = authenticated_client
    
    # State 1: Fitness Level
    response = await client.post("/api/v1/chat/onboarding", json={
        "message": "I'm a beginner",
        "current_state": 1
    })
    assert response.status_code == 200
    assert response.json()["agent_type"] == "workout"
    assert response.json()["state_updated"] == True
    
    # Continue through all 9 states...
    # State 2-9 similar pattern
    
    # Verify completion
    progress = await client.get("/api/v1/onboarding/progress")
    assert progress.json()["completion_percentage"] == 100
    assert progress.json()["can_complete"] == True
```

### 7.5 Test Data Generators

**Helper Functions:**

```python
def get_valid_data_for_state(state: int) -> dict:
    """Generate valid test data for each state."""
    data_generators = {
        1: lambda: {"fitness_level": "beginner"},
        2: lambda: {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
        3: lambda: {
            "equipment": ["dumbbells"],
            "injuries": [],
            "limitations": [],
            "target_weight_kg": 75.0
        },
        4: lambda: {
            "diet_type": "omnivore",
            "allergies": [],
            "intolerances": [],
            "dislikes": []
        },
        5: lambda: {
            "daily_calorie_target": 2000,
            "protein_percentage": 30.0,
            "carbs_percentage": 40.0,
            "fats_percentage": 30.0
        },
        6: lambda: {
            "meals": [
                {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": True}
            ]
        },
        7: lambda: {
            "workouts": [
                {"day_of_week": 1, "scheduled_time": "07:00", "enable_notifications": True}
            ]
        },
        8: lambda: {
            "daily_water_target_ml": 2000,
            "reminder_frequency_minutes": 60
        },
        9: lambda: {
            "interested_in_supplements": False,
            "current_supplements": []
        }
    }
    return data_generators[state]()
```

### 7.6 Test Execution

**Run all tests:**
```bash
poetry run pytest
```

**Run property tests only:**
```bash
poetry run pytest -m property
```

**Run with coverage:**
```bash
poetry run pytest --cov=app --cov-report=html
```

**Run specific test file:**
```bash
poetry run pytest tests/test_onboarding_chat_integration.py
```


## 8. Performance Considerations

### 8.1 Performance Targets

Based on requirements, the following targets must be met:

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Onboarding Progress Endpoint | < 50ms | P95 latency |
| Chat Onboarding Endpoint | < 2s | P95 latency (including LLM) |
| Step Save Endpoint | < 200ms | P95 latency |
| Database Migration | < 5 min | For 100K users |

### 8.2 Optimization Strategies

#### 8.2.1 Database Query Optimization

**Onboarding State Queries:**
```python
# Use selective loading to avoid N+1 queries
state = await db.execute(
    select(OnboardingState)
    .where(OnboardingState.user_id == user_id)
    .options(selectinload(OnboardingState.user))
)

# Index on user_id for fast lookups (already exists)
# JSONB GIN index for step_data queries if needed
```

**Progress Calculation:**
```python
# Cache state metadata in memory (constant data)
STATE_METADATA = {...}  # No database lookup needed

# Completed states calculated from JSONB in single query
completed = [i for i in range(1, 10) if f"step_{i}" in state.step_data]
```

#### 8.2.2 Agent Function Tool Performance

**Minimize Overhead:**
```python
# Reuse database session (don't create new connection)
async def call_onboarding_step(db: AsyncSession, ...):
    service = OnboardingService(db)  # Reuses existing session
    
# Avoid redundant validation
# Validation happens once in OnboardingService, not in tool
```

#### 8.2.3 LLM Call Optimization

**For Chat Onboarding:**
- Use streaming responses for better perceived performance
- Cache agent instances in voice mode (already implemented)
- Use fast classifier model (Claude Haiku) for routing
- Limit context size to essential information

#### 8.2.4 Migration Performance

**Batch Processing:**
```python
# Process in batches of 1000 users
BATCH_SIZE = 1000

for offset in range(0, total_users, BATCH_SIZE):
    batch = connection.execute(
        sa.text(
            "SELECT id, step_data, current_step FROM onboarding_states "
            "WHERE deleted_at IS NULL LIMIT :limit OFFSET :offset"
        ),
        {"limit": BATCH_SIZE, "offset": offset}
    )
    
    # Process batch
    # Commit after each batch
```

### 8.3 Monitoring and Metrics

**Key Metrics to Track:**

```python
# Endpoint latency
metrics.histogram("onboarding.progress.latency", duration_ms)
metrics.histogram("onboarding.chat.latency", duration_ms)
metrics.histogram("onboarding.step.latency", duration_ms)

# Success rates
metrics.counter("onboarding.step.success", tags={"step": step})
metrics.counter("onboarding.step.validation_error", tags={"step": step, "field": field})

# Agent routing
metrics.counter("onboarding.agent.routed", tags={"state": state, "agent": agent_type})

# Completion rates
metrics.counter("onboarding.completed", tags={"duration_minutes": duration})
metrics.gauge("onboarding.completion_rate", completion_percentage)
```

### 8.4 Scalability Considerations

**Concurrent Users:**
- Async/await throughout ensures non-blocking I/O
- Database connection pooling (configured in SQLAlchemy)
- Stateless endpoints enable horizontal scaling

**Database Load:**
- JSONB operations are efficient for step_data
- Indexes on user_id prevent full table scans
- Read replicas can handle progress queries

**Agent Load:**
- Agent orchestrator caches agents in voice mode
- LLM rate limiting handled by provider
- Fallback to general agent on classification failure


## 9. Security Considerations

### 9.1 Authentication and Authorization

**JWT Authentication:**
- All endpoints require valid JWT token
- Token validated via `get_current_user` dependency
- User identity extracted from token claims

**Authorization Checks:**
```python
# Onboarding status check
if not current_user.onboarding_completed:
    raise HTTPException(403, "Complete onboarding first")

# Agent access control
if onboarding_mode and user.onboarding_completed:
    raise HTTPException(403, "Onboarding already completed")
```

### 9.2 Input Validation

**Pydantic Validation:**
- All request bodies validated via Pydantic schemas
- Type checking, range validation, format validation
- Automatic 422 responses for invalid input

**Business Logic Validation:**
- OnboardingService validators for each state
- Validation before database persistence
- Structured error responses with field information

**SQL Injection Prevention:**
- SQLAlchemy ORM with parameterized queries
- No raw SQL with user input
- JSONB operations use SQLAlchemy expressions

### 9.3 Rate Limiting

**Endpoint Rate Limits:**
```python
# Apply rate limiting middleware
@router.post("/onboarding")
@rate_limit(max_requests=100, window_seconds=60)
async def chat_onboarding(...):
    ...

# Per-user limits
# 100 requests per minute per user
# Prevents abuse and DoS attacks
```

### 9.4 Data Privacy

**PII Handling:**
- Onboarding data contains health information
- Stored encrypted at rest (database level)
- Transmitted over HTTPS only
- Access logged for audit trail

**Agent Context:**
- Agent logs include user_id for debugging
- Logs stored securely with retention policy
- No sensitive data in log messages

### 9.5 Agent Security

**Function Tool Safety:**
- Tools only call internal endpoints (no external APIs)
- User context validated before tool execution
- Tools cannot access other users' data

**LLM Prompt Injection:**
- User input sanitized before LLM processing
- System prompts protected from user manipulation
- Agent responses validated before returning


## 10. Deployment Strategy

### 10.1 Deployment Phases

**Phase 1: Database Migration (Week 1)**
1. Create Alembic migration file
2. Test migration on staging database with production data copy
3. Run migration on production during low-traffic window
4. Verify constraint updated and data migrated correctly
5. Monitor for errors, keep backup for 30 days

**Phase 2: Backend Implementation (Week 2-3)**
1. Implement new endpoints (progress, chat onboarding)
2. Modify existing endpoints (users/me, onboarding/step, chat)
3. Add agent function tools to all specialized agents
4. Update OnboardingService with new methods
5. Modify AgentOrchestrator with onboarding_mode parameter

**Phase 3: Testing (Week 3)**
1. Run unit tests (target: 80%+ coverage)
2. Run property-based tests (100 iterations each)
3. Run integration tests (full onboarding flow)
4. Manual testing with various scenarios
5. Load testing on staging (10K concurrent users)

**Phase 4: Staging Deployment (Week 4)**
1. Deploy to staging environment
2. Frontend integration testing
3. End-to-end testing with mobile/web clients
4. User acceptance testing with internal team
5. Performance validation against targets

**Phase 5: Production Deployment (Week 4)**
1. Deploy backend to production
2. Monitor error rates and latency
3. Gradual rollout (10% → 50% → 100% of users)
4. Monitor completion rates and user feedback
5. Hotfix deployment process ready

### 10.2 Rollback Plan

**If Migration Fails:**
1. Restore database from backup
2. Revert Alembic migration: `poetry run alembic downgrade -1`
3. Investigate failure cause
4. Fix issues and retry

**If Deployment Fails:**
1. Revert to previous backend version
2. Database remains compatible (backward compatible changes)
3. Frontend continues using old endpoints
4. Investigate failure cause
5. Fix issues and redeploy

**Data Rollback:**
- Original step data preserved in `_migration_metadata`
- Can reconstruct original state if needed
- Backup retained for 30 days

### 10.3 Monitoring and Alerts

**Key Metrics:**
```python
# Error rates
alert("onboarding.error_rate > 1%", severity="warning")
alert("onboarding.error_rate > 5%", severity="critical")

# Latency
alert("onboarding.progress.p95_latency > 100ms", severity="warning")
alert("onboarding.chat.p95_latency > 3s", severity="warning")

# Completion rates
alert("onboarding.completion_rate < 50%", severity="warning")
alert("onboarding.drop_off_rate_state_3 > 30%", severity="info")
```

**Dashboards:**
- Onboarding funnel (states 1-9)
- Completion rates by state
- Agent routing distribution
- Error rates by endpoint
- Latency percentiles (P50, P95, P99)

### 10.4 Feature Flags

**Gradual Rollout:**
```python
# Feature flag for chat-based onboarding
if feature_flags.is_enabled("chat_onboarding", user_id):
    # Use new chat endpoint
    return await chat_onboarding(...)
else:
    # Use old step-by-step endpoint
    return await traditional_onboarding(...)
```

**Rollback Without Deployment:**
- Disable feature flag to revert to old flow
- No code deployment needed
- Can target specific user segments


## 11. Open Questions and Decisions

### 11.1 Resolved Decisions

**Q1: Should agents call REST endpoints or database directly?**
- **Decision:** Agents call REST endpoints as function tools
- **Rationale:** Reuses validation logic, maintains single source of truth, easier to test
- **Date:** 2026-02-11

**Q2: How to handle state consolidation (11 → 9)?**
- **Decision:** Merge steps 4 & 5 into state 3, preserve original data in metadata
- **Rationale:** Both handled by same agent, reduces friction, allows rollback
- **Date:** 2026-02-11

**Q3: Should state 9 (supplements) be optional?**
- **Decision:** Yes, but still counted in completion percentage
- **Rationale:** Not all users interested in supplements, but want consistent 9-state flow
- **Date:** 2026-02-11

### 11.2 Open Questions

**Q1: Should users be able to go back to previous states during onboarding?**
- **Status:** Open
- **Impact:** UX design, state management complexity
- **Recommendation:** Allow backward navigation, but require re-validation
- **Decision Needed By:** Frontend design phase

**Q2: How long to retain migration metadata?**
- **Status:** Open
- **Impact:** Database storage, rollback capability
- **Recommendation:** 30 days, then cleanup via background job
- **Decision Needed By:** Before production deployment

**Q3: Should we support resuming onboarding from any state or only sequential?**
- **Status:** Open
- **Impact:** State validation, user experience
- **Recommendation:** Sequential only for MVP, add non-sequential later
- **Decision Needed By:** Before frontend implementation

**Q4: What happens if user wants to change onboarding responses after completion?**
- **Status:** Open
- **Impact:** Profile update flow, versioning
- **Recommendation:** Separate profile edit flow (not part of this spec)
- **Decision Needed By:** Profile management spec

### 11.3 Future Enhancements

**Not in Scope for MVP:**
1. Real-time WebSocket progress updates
2. Voice-based onboarding via LiveKit
3. AI-generated onboarding suggestions
4. Multi-language support for onboarding
5. Onboarding analytics dashboard

**Potential Future Work:**
1. A/B testing different onboarding flows
2. Personalized state ordering based on user type
3. Skip logic (e.g., skip supplements if not interested)
4. Progress gamification (badges, achievements)
5. Social proof (X% of users completed this state)


## 12. Appendix

### 12.1 Complete State Metadata

```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="workout_planning",
        description="Tell us about your current fitness level",
        required_fields=["fitness_level"]
    ),
    2: StateInfo(
        state_number=2,
        name="Primary Fitness Goals",
        agent="workout_planning",
        description="What are your fitness goals?",
        required_fields=["goals"]
    ),
    3: StateInfo(
        state_number=3,
        name="Workout Preferences & Constraints",
        agent="workout_planning",
        description="Tell us about your equipment and any limitations",
        required_fields=["equipment", "injuries", "limitations"]
    ),
    4: StateInfo(
        state_number=4,
        name="Diet Preferences & Restrictions",
        agent="diet_planning",
        description="Share your dietary preferences and restrictions",
        required_fields=["diet_type", "allergies", "intolerances", "dislikes"]
    ),
    5: StateInfo(
        state_number=5,
        name="Fixed Meal Plan Selection",
        agent="diet_planning",
        description="Let's set up your meal plan with calorie and macro targets",
        required_fields=["daily_calorie_target", "protein_percentage", "carbs_percentage", "fats_percentage"]
    ),
    6: StateInfo(
        state_number=6,
        name="Meal Timing Schedule",
        agent="scheduler",
        description="When do you prefer to eat your meals?",
        required_fields=["meals"]
    ),
    7: StateInfo(
        state_number=7,
        name="Workout Schedule",
        agent="scheduler",
        description="When do you want to work out?",
        required_fields=["workouts"]
    ),
    8: StateInfo(
        state_number=8,
        name="Hydration Schedule",
        agent="scheduler",
        description="Let's set up your water intake goals",
        required_fields=["daily_water_target_ml", "reminder_frequency_minutes"]
    ),
    9: StateInfo(
        state_number=9,
        name="Supplement Preferences",
        agent="supplement",
        description="Are you interested in supplement guidance? (Optional)",
        required_fields=["interested_in_supplements"]
    )
}
```

### 12.2 API Endpoint Summary

**New Endpoints:**
- `GET /api/v1/onboarding/progress` - Get rich progress metadata
- `POST /api/v1/chat/onboarding` - Chat-based onboarding with agent routing

**Modified Endpoints:**
- `GET /api/v1/users/me` - Added access_control object
- `POST /api/v1/onboarding/step` - Support 9 states, accept agent context header
- `POST /api/v1/chat` - Enforce agent restrictions post-onboarding

**Unchanged Endpoints:**
- `GET /api/v1/onboarding/state` - Get current onboarding state
- `POST /api/v1/onboarding/complete` - Mark onboarding complete
- All other existing endpoints

### 12.3 File Changes Summary

**New Files:**
- `backend/app/agents/onboarding_tools.py` - Common helper for agent function tools
- `backend/alembic/versions/xxxx_consolidate_onboarding_states.py` - Migration script

**Modified Files:**
- `backend/app/models/onboarding.py` - Add agent_history, update constraint
- `backend/app/schemas/onboarding.py` - Add new request/response schemas
- `backend/app/services/onboarding_service.py` - Add new methods, update validators
- `backend/app/services/agent_orchestrator.py` - Add onboarding_mode parameter
- `backend/app/api/v1/endpoints/onboarding.py` - Add progress endpoint, modify step endpoint
- `backend/app/api/v1/endpoints/chat.py` - Add onboarding chat endpoint, modify chat endpoint
- `backend/app/api/v1/endpoints/auth.py` - Modify users/me endpoint
- `backend/app/agents/workout_planner.py` - Add onboarding function tools
- `backend/app/agents/diet_planner.py` - Add onboarding function tools
- `backend/app/agents/scheduler.py` - Add onboarding function tools
- `backend/app/agents/supplement_guide.py` - Add onboarding function tools

### 12.4 Dependencies

**No New Dependencies Required:**
- All functionality uses existing libraries
- Hypothesis already in dev dependencies for property testing
- FastAPI, SQLAlchemy, Pydantic already available

### 12.5 Backward Compatibility

**Breaking Changes:**
- None - all changes are additive or backward compatible

**Deprecated:**
- None - old endpoints remain functional

**Migration Path:**
- Existing users: Data automatically migrated
- New users: Use new 9-state flow
- Frontend: Can support both flows during transition

---

**Document Status:** Ready for Review  
**Next Steps:** Create tasks.md with implementation checklist


# Implement TRD Onboarding Agent System

## Problem Statement

The onboarding chat system is incorrectly routing to post-onboarding agents instead of the specialized onboarding agents defined in the TRD. The system has the correct architecture components (OnboardingAgentOrchestrator, specialized onboarding agents) but the chat endpoints are using the wrong routing mechanism.

### Current Behavior (Incorrect)
```
User in State 1 → STATE_TO_AGENT_MAP → AgentType.WORKOUT → Post-onboarding workout agent
  ↓
Agent asks: "Are you ready to see today's workout?" ❌
```

### Expected Behavior (Per TRD)
```
User in State 1 → OnboardingAgentOrchestrator → OnboardingAgentType.FITNESS_ASSESSMENT → FitnessAssessmentAgent
  ↓
Agent asks: "What is your current fitness level?" ✓
```

## Root Cause Analysis

The system has **two parallel routing mechanisms**:

1. **TRD Architecture (Correct, but not used by chat endpoints)**:
   - `OnboardingAgentOrchestrator` in `app/services/onboarding_orchestrator.py`
   - Maps steps to `OnboardingAgentType` enum (FITNESS_ASSESSMENT, GOAL_SETTING, etc.)
   - Routes to specialized agents in `app/agents/onboarding/`
   - Used by `/api/v1/onboarding/chat` endpoint ✓

2. **Legacy Routing (Incorrect, used by streaming endpoint)**:
   - `STATE_TO_AGENT_MAP` in `app/services/onboarding_service.py`
   - Maps states to `AgentType` enum (WORKOUT, DIET, etc.)
   - Routes to post-onboarding agents in `app/agents/`
   - Used by `/api/v1/chat/onboarding-stream` endpoint ❌

**The Issue**: The streaming endpoint (`/api/v1/chat/onboarding-stream`) uses `STATE_TO_AGENT_MAP` and `AgentOrchestrator` instead of `OnboardingAgentOrchestrator`, causing it to route to the wrong agents.

## Requirements

### 1. Remove Legacy Routing Mechanism

**Goal**: Eliminate `STATE_TO_AGENT_MAP` and all code that uses post-onboarding agents for onboarding flow.

**Components to Remove**:
- `STATE_TO_AGENT_MAP` dictionary in `app/services/onboarding_service.py`
- All imports of `STATE_TO_AGENT_MAP` in chat endpoints
- All usage of `AgentOrchestrator` with `onboarding_mode=True`
- All references to `AgentType.WORKOUT`, `AgentType.DIET`, etc. in onboarding context
- Tests that validate `STATE_TO_AGENT_MAP` (replace with OnboardingAgentOrchestrator tests)

### 2. Use OnboardingAgentOrchestrator Everywhere

**Goal**: All onboarding chat endpoints must use `OnboardingAgentOrchestrator` to route to specialized onboarding agents.

**Required Changes**:

#### A. Update `/api/v1/chat/onboarding` endpoint
- Replace `STATE_TO_AGENT_MAP` lookup with `OnboardingAgentOrchestrator.get_current_agent()`
- Remove `AgentOrchestrator` usage
- Use specialized onboarding agents directly

#### B. Update `/api/v1/chat/onboarding-stream` endpoint
- Replace `STATE_TO_AGENT_MAP` lookup with `OnboardingAgentOrchestrator.get_current_agent()`
- Remove `AgentOrchestrator` usage
- Stream responses from specialized onboarding agents

#### C. Update `/api/v1/onboarding/chat` endpoint (if different from above)
- Ensure it uses `OnboardingAgentOrchestrator`
- Remove any `STATE_TO_AGENT_MAP` references

### 3. Verify Specialized Onboarding Agents

**Goal**: Ensure all specialized onboarding agents exist and work correctly.

**Required Agents** (per TRD):
- `FitnessAssessmentAgent` (steps 0-2) - Already exists ✓
- `GoalSettingAgent` (step 3) - Already exists ✓
- `WorkoutPlanningAgent` (steps 4-5) - Already exists ✓
- `DietPlanningAgent` (steps 6-7) - Already exists ✓
- `SchedulingAgent` (steps 8-9) - Already exists ✓

**Verification**:
- Each agent must have correct system prompts per TRD
- Each agent must have appropriate tools
- Each agent must save data to `agent_context` correctly

### 4. Update State Metadata

**Goal**: Ensure `STATE_METADATA` in `onboarding_service.py` reflects the correct agent types.

**Current State Metadata** (Incorrect):
```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="workout_planning",  # ❌ Wrong
        ...
    ),
}
```

**Required State Metadata** (Per TRD):
```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="fitness_assessment",  # ✓ Correct
        ...
    ),
    2: StateInfo(
        state_number=2,
        name="Primary Fitness Goals",
        agent="fitness_assessment",  # ✓ Steps 0-2 use same agent
        ...
    ),
    3: StateInfo(
        state_number=3,
        name="Workout Preferences & Constraints",
        agent="goal_setting",  # ✓ Correct
        ...
    ),
    # ... etc
}
```

## Acceptance Criteria

### AC1: Streaming Endpoint Routes to Correct Agent
- GIVEN a user is in onboarding state 1
- WHEN they send a message to `/api/v1/chat/onboarding-stream`
- THEN the system uses `OnboardingAgentOrchestrator.get_current_agent()`
- AND routes to `FitnessAssessmentAgent`
- AND the agent asks fitness assessment questions

### AC2: Non-Streaming Endpoint Routes to Correct Agent
- GIVEN a user is in onboarding state 1
- WHEN they send a message to `/api/v1/chat/onboarding`
- THEN the system uses `OnboardingAgentOrchestrator.get_current_agent()`
- AND routes to `FitnessAssessmentAgent`
- AND the agent asks fitness assessment questions

### AC3: Event Stream Returns Correct Agent Type
- GIVEN a user sends a message in state 1
- WHEN the streaming response completes
- THEN the `agent_type` field equals "fitness_assessment"
- AND NOT "workout"
- AND the `current_state` field equals 1

### AC4: No Legacy Routing Code Remains
- GIVEN the codebase after implementation
- WHEN searching for `STATE_TO_AGENT_MAP`
- THEN it should not exist in `onboarding_service.py`
- AND it should not be imported in any chat endpoints
- AND it should not be used in any routing logic

### AC5: All States Route Correctly
- GIVEN a user progresses through all 9 onboarding states
- WHEN they interact with the chat endpoints
- THEN each state routes to the correct specialized agent:
  - States 0-2 → FitnessAssessmentAgent
  - State 3 → GoalSettingAgent
  - States 4-5 → WorkoutPlanningAgent
  - States 6-7 → DietPlanningAgent
  - States 8-9 → SchedulingAgent

### AC6: Agent Behavior Matches TRD
- GIVEN the FitnessAssessmentAgent handles state 1
- WHEN a user starts the conversation
- THEN the agent asks about current fitness level
- AND asks about exercise experience
- AND asks about physical limitations
- AND asks about equipment access
- AND NEVER asks about "today's workout"

### AC7: State Metadata is Correct
- GIVEN the STATE_METADATA dictionary
- WHEN checking each state's agent field
- THEN it matches the OnboardingAgentType that handles that state
- AND NOT the post-onboarding AgentType

## Technical Implementation Details

### Files to Modify

#### 1. `backend/app/services/onboarding_service.py`
**Changes**:
- Remove `STATE_TO_AGENT_MAP` dictionary entirely
- Update `STATE_METADATA` agent fields to match TRD:
  - States 1-2: `agent="fitness_assessment"`
  - State 3: `agent="goal_setting"`
  - States 4-5: `agent="workout_planning"`
  - States 6-7: `agent="diet_planning"`
  - States 8-9: `agent="scheduling"`

#### 2. `backend/app/api/v1/endpoints/chat.py`
**Changes**:
- Remove import: `from app.services.onboarding_service import STATE_TO_AGENT_MAP`
- Add import: `from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator`
- In `chat_onboarding()` function:
  - Remove: `agent_type = STATE_TO_AGENT_MAP.get(request.current_state)`
  - Replace with: `orchestrator = OnboardingAgentOrchestrator(db)` and `agent = await orchestrator.get_current_agent(current_user.id)`
  - Remove: `orchestrator = AgentOrchestrator(db_session=db, mode="text")`
  - Remove: `agent_response = await orchestrator.route_query(..., onboarding_mode=True)`
  - Replace with: `agent_response = await agent.process_message(request.message, current_user.id)`
- In `chat_onboarding_stream()` function:
  - Remove: `agent_type = STATE_TO_AGENT_MAP.get(state.current_step)`
  - Replace with: `orchestrator = OnboardingAgentOrchestrator(db)` and `agent = await orchestrator.get_current_agent(current_user.id)`
  - Remove: `orchestrator = AgentOrchestrator(db_session=db, mode="text")`
  - Remove: `agent = orchestrator._get_or_create_agent(agent_type, context)`
  - Use the agent from OnboardingAgentOrchestrator directly

#### 3. `backend/app/api/v1/endpoints/onboarding.py`
**Changes**:
- Verify `/api/v1/onboarding/chat` endpoint uses `OnboardingAgentOrchestrator`
- If it uses `STATE_TO_AGENT_MAP`, replace with orchestrator

#### 4. `backend/tests/test_state_agent_mapping_properties.py`
**Changes**:
- Delete this file entirely (tests legacy STATE_TO_AGENT_MAP)
- Tests for OnboardingAgentOrchestrator already exist in `test_onboarding_orchestrator.py`

#### 5. `backend/app/services/agent_orchestrator.py`
**Changes**:
- Remove all `onboarding_mode` parameter handling
- Remove access control logic for onboarding agents
- Remove classification logic for onboarding mode
- This class should ONLY handle post-onboarding agents

### Architecture After Implementation

```
Onboarding Flow:
  User Message → Chat Endpoint
    ↓
  OnboardingAgentOrchestrator.get_current_agent(user_id)
    ↓
  _step_to_agent(current_step) → OnboardingAgentType
    ↓
  _create_agent(agent_type) → Specialized Onboarding Agent
    ↓
  agent.process_message() or agent.stream_response()
    ↓
  Response to User

Post-Onboarding Flow:
  User Message → Chat Endpoint
    ↓
  AgentOrchestrator.route_query(agent_type=GENERAL)
    ↓
  General Assistant Agent
    ↓
  Response to User
```

## Out of Scope

- Implementing new onboarding agents (they already exist)
- Changing the database schema
- Modifying the frontend
- Changing the OnboardingAgentOrchestrator logic (it's already correct)
- Updating post-onboarding agent behavior

## Success Metrics

- Zero references to `STATE_TO_AGENT_MAP` in production code
- All onboarding states route to correct specialized agents 100% of the time
- Event stream returns correct `agent_type` matching `OnboardingAgentType` values
- State 1 agent asks fitness assessment questions 100% of the time
- Zero instances of "today's workout" questions during onboarding

## References

- **TRD**: `docs/technichal/onboarding_agent_system_trd.md`
- **Orchestrator**: `backend/app/services/onboarding_orchestrator.py` (already correct)
- **Specialized Agents**: `backend/app/agents/onboarding/` (already exist)
- **Chat Endpoints**: `backend/app/api/v1/endpoints/chat.py` (needs fixing)
- **Legacy Routing**: `backend/app/services/onboarding_service.py` (STATE_TO_AGENT_MAP to remove)

## References

- **TRD**: `docs/technichal/onboarding_agent_system_trd.md`
- **Orchestrator**: `backend/app/services/onboarding_orchestrator.py` (already correct)
- **Specialized Agents**: `backend/app/agents/onboarding/` (already exist)
- **Chat Endpoints**: `backend/app/api/v1/endpoints/chat.py` (needs fixing)
- **Legacy Routing**: `backend/app/services/onboarding_service.py` (STATE_TO_AGENT_MAP to remove)

## User Stories

### US1: As a new user, I want to be asked fitness assessment questions in state 1
**Given** I am a new user starting onboarding at state 1  
**When** I send my first message to the onboarding chat  
**Then** the system routes me to the FitnessAssessmentAgent  
**And** the agent asks me about my current fitness level  
**And** NOT about today's workout

### US2: As a developer, I want a single routing mechanism for onboarding
**Given** I am maintaining the onboarding system  
**When** I look at the codebase  
**Then** I see only OnboardingAgentOrchestrator used for routing  
**And** I do NOT see STATE_TO_AGENT_MAP anywhere  
**And** I do NOT see AgentOrchestrator used with onboarding_mode=True

### US3: As a user progressing through onboarding, I want each state to use the correct specialized agent
**Given** I am progressing through onboarding states 1-9  
**When** I interact with the chat at each state  
**Then** each state routes to the agent specified in the TRD  
**And** each agent asks questions appropriate for that state  
**And** each agent saves data to the correct context structure

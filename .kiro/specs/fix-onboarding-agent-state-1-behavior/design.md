# Design: Implement TRD Onboarding Agent System

## Overview

This design implements the TRD-specified onboarding agent architecture by removing all legacy routing code and ensuring all onboarding chat endpoints use `OnboardingAgentOrchestrator` to route to specialized onboarding agents.

## Architecture

### Current Architecture (Incorrect)

```
┌─────────────────────────────────────────────────────────────┐
│ Chat Endpoints                                              │
├─────────────────────────────────────────────────────────────┤
│ /api/v1/chat/onboarding          ✓ Uses OnboardingOrch     │
│ /api/v1/chat/onboarding-stream   ✗ Uses STATE_TO_AGENT_MAP │
│ /api/v1/onboarding/chat          ✓ Uses OnboardingOrch     │
└─────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
        ┌───────────────────────┐   ┌──────────────────────┐
        │ OnboardingAgent       │   │ AgentOrchestrator    │
        │ Orchestrator          │   │ (Post-onboarding)    │
        │ (TRD Architecture)    │   │ + STATE_TO_AGENT_MAP │
        └───────────────────────┘   └──────────────────────┘
                    │                           │
                    ▼                           ▼
        ┌───────────────────────┐   ┌──────────────────────┐
        │ Specialized           │   │ Post-Onboarding      │
        │ Onboarding Agents     │   │ Agents (WRONG!)      │
        │ - FitnessAssessment   │   │ - Workout            │
        │ - GoalSetting         │   │ - Diet               │
        │ - WorkoutPlanning     │   │ - Scheduler          │
        │ - DietPlanning        │   │ - Supplement         │
        │ - Scheduling          │   │                      │
        └───────────────────────┘   └──────────────────────┘
```

### Target Architecture (TRD-Compliant)

```
┌─────────────────────────────────────────────────────────────┐
│ Chat Endpoints (ALL use OnboardingAgentOrchestrator)       │
├─────────────────────────────────────────────────────────────┤
│ /api/v1/chat/onboarding          ✓                         │
│ /api/v1/chat/onboarding-stream   ✓ (FIXED)                 │
│ /api/v1/onboarding/chat          ✓                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ OnboardingAgent       │
                │ Orchestrator          │
                │ (TRD Architecture)    │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Specialized           │
                │ Onboarding Agents     │
                │ - FitnessAssessment   │
                │ - GoalSetting         │
                │ - WorkoutPlanning     │
                │ - DietPlanning        │
                │ - Scheduling          │
                └───────────────────────┘

STATE_TO_AGENT_MAP: DELETED ✗
AgentOrchestrator.onboarding_mode: REMOVED ✗
```

## Component Design

### 1. Remove STATE_TO_AGENT_MAP

**File**: `backend/app/services/onboarding_service.py`

**Current Code** (Lines 107-119):
```python
STATE_TO_AGENT_MAP = {
    1: AgentType.WORKOUT,
    2: AgentType.WORKOUT,
    3: AgentType.WORKOUT,
    4: AgentType.DIET,
    5: AgentType.DIET,
    6: AgentType.SCHEDULER,
    7: AgentType.SCHEDULER,
    8: AgentType.SCHEDULER,
    9: AgentType.SUPPLEMENT,
}
```

**Action**: Delete this entire dictionary and its comment block.

**Rationale**: This mapping routes to post-onboarding agents, which is incorrect per TRD. The `OnboardingAgentOrchestrator._step_to_agent()` method already provides the correct mapping.

### 2. Update STATE_METADATA

**File**: `backend/app/services/onboarding_service.py`

**Current Metadata** (Incorrect agent fields):
```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="workout_planning",  # ❌ Wrong
        ...
    ),
    2: StateInfo(
        state_number=2,
        name="Primary Fitness Goals",
        agent="workout_planning",  # ❌ Wrong
        ...
    ),
    # ... etc
}
```

**Updated Metadata** (Per TRD):
```python
STATE_METADATA = {
    1: StateInfo(
        state_number=1,
        name="Fitness Level Assessment",
        agent="fitness_assessment",  # ✓ Correct
        description="Tell us about your current fitness level",
        required_fields=["fitness_level"]
    ),
    2: StateInfo(
        state_number=2,
        name="Exercise Experience",
        agent="fitness_assessment",  # ✓ Steps 0-2 use same agent
        description="Share your exercise background",
        required_fields=["experience_years"]
    ),
    3: StateInfo(
        state_number=3,
        name="Fitness Goals",
        agent="goal_setting",  # ✓ Correct
        description="What are your fitness goals?",
        required_fields=["goals"]
    ),
    4: StateInfo(
        state_number=4,
        name="Workout Preferences",
        agent="workout_planning",  # ✓ Correct
        description="Tell us about your workout preferences",
        required_fields=["equipment", "location"]
    ),
    5: StateInfo(
        state_number=5,
        name="Workout Plan",
        agent="workout_planning",  # ✓ Steps 4-5 use same agent
        description="Review and approve your workout plan",
        required_fields=["workout_plan_approved"]
    ),
    6: StateInfo(
        state_number=6,
        name="Diet Preferences",
        agent="diet_planning",  # ✓ Correct
        description="Share your dietary preferences and restrictions",
        required_fields=["diet_type", "allergies", "intolerances"]
    ),
    7: StateInfo(
        state_number=7,
        name="Meal Plan",
        agent="diet_planning",  # ✓ Steps 6-7 use same agent
        description="Review and approve your meal plan",
        required_fields=["meal_plan_approved"]
    ),
    8: StateInfo(
        state_number=8,
        name="Workout Schedule",
        agent="scheduling",  # ✓ Correct
        description="When do you want to work out?",
        required_fields=["workouts"]
    ),
    9: StateInfo(
        state_number=9,
        name="Meal & Hydration Schedule",
        agent="scheduling",  # ✓ Steps 8-9 use same agent
        description="Set your meal times and hydration goals",
        required_fields=["meals", "daily_water_target_ml"]
    ),
}
```

**Rationale**: The agent field must match the `OnboardingAgentType` values that actually handle each state, not the post-onboarding agent types.

### 3. Update /api/v1/chat/onboarding Endpoint

**File**: `backend/app/api/v1/endpoints/chat.py`

**Current Implementation** (Lines 215-360):
```python
async def chat_onboarding(...):
    # ...
    # 4. Route to appropriate agent based on current_state
    agent_type = STATE_TO_AGENT_MAP.get(request.current_state)  # ❌
    
    # 5. Initialize AgentOrchestrator in text mode
    orchestrator = AgentOrchestrator(db_session=db, mode="text")  # ❌
    
    # 6. Process query with agent in onboarding mode
    agent_response = await orchestrator.route_query(
        user_id=user_id,
        query=request.message,
        agent_type=agent_type,
        voice_mode=False,
        onboarding_mode=True  # ❌
    )
```

**Updated Implementation**:
```python
async def chat_onboarding(...):
    # ...
    # 4. Get specialized onboarding agent
    from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
    
    orchestrator = OnboardingAgentOrchestrator(db)
    
    try:
        agent = await orchestrator.get_current_agent(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # 5. Process message with specialized agent
    try:
        agent_response = await agent.process_message(
            message=request.message,
            user_id=current_user.id
        )
    except Exception as e:
        logger.error(
            f"Agent processing failed for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )
    
    # 6. Check if state was updated
    updated_state = await onboarding_service.get_onboarding_state(current_user.id)
    state_updated = updated_state.current_step > initial_step
    
    # 7. Get progress
    progress = await onboarding_service.get_progress(current_user.id)
    
    # 8. Return response with correct agent_type
    return OnboardingChatResponse(
        response=agent_response.message,
        agent_type=agent_response.agent_type,  # Will be "fitness_assessment", etc.
        state_updated=state_updated,
        new_state=updated_state.current_step if state_updated else None,
        progress={...}
    )
```

**Key Changes**:
- Remove `STATE_TO_AGENT_MAP` lookup
- Remove `AgentOrchestrator` usage
- Use `OnboardingAgentOrchestrator.get_current_agent()`
- Call `agent.process_message()` directly
- Agent returns correct `agent_type` from `OnboardingAgentType` enum

### 4. Update /api/v1/chat/onboarding-stream Endpoint

**File**: `backend/app/api/v1/endpoints/chat.py`

**Current Implementation** (Lines 430-720):
```python
async def chat_onboarding_stream(...):
    async def generate():
        # ...
        # Route to appropriate agent based on current_state
        agent_type = STATE_TO_AGENT_MAP.get(state.current_step)  # ❌
        
        # Initialize AgentOrchestrator in text mode
        orchestrator = AgentOrchestrator(db_session=db, mode="text")  # ❌
        
        # Get or create agent instance
        agent = orchestrator._get_or_create_agent(agent_type, context)  # ❌
        
        # Stream response chunks
        async for chunk in agent.stream_response(message):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
```

**Updated Implementation**:
```python
async def chat_onboarding_stream(...):
    async def generate():
        # ...
        # Get specialized onboarding agent
        from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
        
        orchestrator = OnboardingAgentOrchestrator(db)
        
        try:
            agent = await orchestrator.get_current_agent(current_user.id)
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Failed to get onboarding agent: {error_msg}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            return
        
        # Get agent type for response
        agent_type_value = agent.agent_type  # "fitness_assessment", etc.
        
        # Stream response chunks via agent.stream_response()
        try:
            async for chunk in agent.stream_response(message):
                full_response += chunk
                chunk_count += 1
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Check if state was updated
            updated_state = await onboarding_service.get_onboarding_state(current_user.id)
            state_updated = updated_state.current_step > initial_step
            
            # Get progress
            progress = await onboarding_service.get_progress(current_user.id)
            
            # Send final event with correct agent_type
            yield f"data: {json.dumps({
                'done': True,
                'agent_type': agent_type_value,  # "fitness_assessment", not "workout"
                'state_updated': state_updated,
                'new_state': updated_state.current_step if state_updated else None,
                'progress': {...}
            })}\n\n"
```

**Key Changes**:
- Remove `STATE_TO_AGENT_MAP` lookup
- Remove `AgentOrchestrator` usage
- Use `OnboardingAgentOrchestrator.get_current_agent()`
- Get `agent_type` from agent instance
- Stream responses from specialized agent

### 5. Remove onboarding_mode from AgentOrchestrator

**File**: `backend/app/services/agent_orchestrator.py`

**Components to Remove**:

1. **Remove `onboarding_mode` parameter** from:
   - `route_query()` method
   - `_classify_query()` method
   - `_enforce_access_control()` method
   - `_log_routing_decision()` method

2. **Remove onboarding-specific logic**:
   - Access control checks for `onboarding_mode=True`
   - Classification prompts for onboarding
   - Forcing general agent post-onboarding

3. **Simplify to post-onboarding only**:
```python
async def route_query(
    self,
    user_id: str,
    query: str,
    agent_type: Optional[AgentType] = None,
    voice_mode: bool = False
) -> "AgentResponse":
    """
    Route a user query to the appropriate agent.
    
    This method is for POST-ONBOARDING interactions only.
    For onboarding, use OnboardingAgentOrchestrator instead.
    """
    # Load user context
    context = await load_agent_context(
        db=self.db_session,
        user_id=user_id,
        include_history=True
    )
    
    # Verify onboarding is complete
    if not context.onboarding_complete:
        raise ValueError(
            "User has not completed onboarding. "
            "Use OnboardingAgentOrchestrator for onboarding interactions."
        )
    
    # Force GENERAL agent for all post-onboarding queries
    if agent_type is None or agent_type != AgentType.TEST:
        agent_type = AgentType.GENERAL
    
    # Get or create agent
    agent = self._get_or_create_agent(agent_type, context)
    
    # Process based on mode
    if voice_mode:
        response_content = await agent.process_voice(query)
        response = AgentResponse(
            content=response_content,
            agent_type=agent_type.value,
            tools_used=[],
            metadata={"mode": "voice", "user_id": user_id}
        )
    else:
        response = await agent.process_text(query)
    
    return response
```

**Rationale**: `AgentOrchestrator` should only handle post-onboarding interactions. All onboarding logic belongs in `OnboardingAgentOrchestrator`.

### 6. Delete Legacy Tests

**File**: `backend/tests/test_state_agent_mapping_properties.py`

**Action**: Delete this entire file.

**Rationale**: This file tests `STATE_TO_AGENT_MAP` which is being removed. The correct routing logic is already tested in `backend/tests/test_onboarding_orchestrator.py`.

## Data Flow

### Onboarding Chat Flow (After Implementation)

```
1. User sends message to /api/v1/chat/onboarding-stream
   ↓
2. Endpoint authenticates user
   ↓
3. Load OnboardingState from database
   ↓
4. Create OnboardingAgentOrchestrator(db)
   ↓
5. orchestrator.get_current_agent(user_id)
   ├─ Load OnboardingState
   ├─ Call _step_to_agent(current_step)
   │  └─ Returns OnboardingAgentType (e.g., FITNESS_ASSESSMENT)
   ├─ Load agent_context from OnboardingState
   └─ Call _create_agent(agent_type, context)
      └─ Returns FitnessAssessmentAgent instance
   ↓
6. agent.stream_response(message)
   ├─ Agent processes message with LLM
   ├─ Agent may call tools to save data
   └─ Yields response chunks
   ↓
7. Stream chunks to client as SSE events
   ↓
8. Send final event with:
   - agent_type: "fitness_assessment" (from agent.agent_type)
   - state_updated: true/false
   - progress: {...}
```

### State-to-Agent Mapping (TRD-Compliant)

```
OnboardingAgentOrchestrator._step_to_agent():

Step 0-2 → OnboardingAgentType.FITNESS_ASSESSMENT
           └─ FitnessAssessmentAgent
              - Asks about fitness level
              - Asks about exercise experience
              - Assesses limitations

Step 3   → OnboardingAgentType.GOAL_SETTING
           └─ GoalSettingAgent
              - Defines primary goal
              - Identifies secondary goals

Step 4-5 → OnboardingAgentType.WORKOUT_PLANNING
           └─ WorkoutPlanningAgent
              - Gathers workout preferences
              - Generates workout plan
              - Gets user approval

Step 6-7 → OnboardingAgentType.DIET_PLANNING
           └─ DietPlanningAgent
              - Gathers diet preferences
              - Generates meal plan
              - Gets user approval

Step 8-9 → OnboardingAgentType.SCHEDULING
           └─ SchedulingAgent
              - Sets workout schedule
              - Sets meal schedule
              - Configures hydration
```

## Error Handling

### 1. User Not Found
```python
try:
    agent = await orchestrator.get_current_agent(user_id)
except ValueError as e:
    if "not found" in str(e).lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding state not found"
        )
```

### 2. Onboarding Already Complete
```python
try:
    agent = await orchestrator.get_current_agent(user_id)
except ValueError as e:
    if "already complete" in str(e).lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Onboarding already completed. Use /api/v1/chat instead."
        )
```

### 3. Agent Processing Failure
```python
try:
    response = await agent.process_message(message, user_id)
except Exception as e:
    logger.error(f"Agent processing failed: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to process message"
    )
```

## Testing Strategy

### Unit Tests (Already Exist)

**File**: `backend/tests/test_onboarding_orchestrator.py`

These tests already validate:
- Step-to-agent mapping (steps 0-2 → FITNESS_ASSESSMENT, etc.)
- Agent instantiation with context
- Error handling for invalid steps
- Context loading and passing

**No changes needed** - these tests already validate the TRD architecture.

### Integration Tests (Need Updates)

**Files to Update**:
- `backend/tests/test_onboarding_chat_endpoint.py`
- `backend/tests/test_integration_onboarding_flow.py`

**Changes**:
- Update assertions to expect `agent_type="fitness_assessment"` instead of `"workout"`
- Verify streaming endpoint returns correct agent types
- Test all 9 states route to correct agents

### Property-Based Tests (Delete)

**File**: `backend/tests/test_state_agent_mapping_properties.py`

**Action**: Delete this file entirely.

## Migration Path

### Phase 1: Remove Legacy Code
1. Delete `STATE_TO_AGENT_MAP` from `onboarding_service.py`
2. Update `STATE_METADATA` agent fields
3. Delete `test_state_agent_mapping_properties.py`

### Phase 2: Update Chat Endpoints
1. Update `/api/v1/chat/onboarding` endpoint
2. Update `/api/v1/chat/onboarding-stream` endpoint
3. Remove all `STATE_TO_AGENT_MAP` imports

### Phase 3: Clean Up AgentOrchestrator
1. Remove `onboarding_mode` parameter
2. Remove onboarding-specific access control
3. Simplify to post-onboarding only

### Phase 4: Update Tests
1. Update integration tests for correct agent types
2. Verify all tests pass
3. Run full test suite

## Rollback Plan

If issues arise:
1. Revert changes to chat endpoints
2. Restore `STATE_TO_AGENT_MAP` temporarily
3. Investigate and fix issues
4. Re-apply changes

**Note**: Since the TRD architecture already exists and is tested, rollback should not be necessary.

## Success Criteria

- ✓ `STATE_TO_AGENT_MAP` does not exist in codebase
- ✓ All chat endpoints use `OnboardingAgentOrchestrator`
- ✓ State 1 returns `agent_type="fitness_assessment"`
- ✓ All 9 states route to correct specialized agents
- ✓ All tests pass
- ✓ No references to `AgentOrchestrator` with `onboarding_mode=True`

## Performance Considerations

**No performance impact expected**:
- `OnboardingAgentOrchestrator` is already implemented and efficient
- Specialized agents are already instantiated correctly
- No additional database queries required
- Streaming performance unchanged

## Security Considerations

**No security changes**:
- Authentication remains unchanged
- Authorization logic remains in endpoints
- Agent access control handled by orchestrator
- No new security vulnerabilities introduced

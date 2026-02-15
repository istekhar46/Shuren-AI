# Onboarding UI State Synchronization - Requirements

## Feature Name
onboarding-ui-state-sync

## Problem Statement

When the AI agent updates the onboarding state during a chat interaction (e.g., from state 1 to state 2), the backend correctly updates the database and returns `state_updated: false` in the response, even though the logs show the state was updated from 1 to 2. This causes the frontend UI to not reflect the state change, leaving users confused about their progress.

### Current Behavior
1. User sends message "I am a complete beginner" in state 1
2. Agent processes message and calls `save_fitness_level_tool` 
3. Backend logs show: "Agent routing history updated: state 1 -> 2 via workout_planning"
4. Backend response returns: `state_updated: false, new_state: null`
5. Frontend does not update the UI to show state 2
6. User remains on state 1 in the UI despite being on state 2 in the database

### Root Cause
The backend endpoint checks if the state was updated by comparing the state BEFORE the agent call with the state AFTER the agent call. However, the comparison happens using the `current_state` from the request, not from the database state loaded at the beginning of the request.

```python
# Line 307-308 in backend/app/api/v1/endpoints/chat.py
updated_state = await onboarding_service.get_onboarding_state(current_user.id)
state_updated = updated_state.current_step > state.current_step
```

The issue is that `state.current_step` is the state loaded at line 257, which is BEFORE the agent processes the message. When the agent updates the state, `updated_state.current_step` becomes the new state, but the comparison should detect this change.

## User Stories

### US-1: Accurate State Update Detection
**As a** user completing onboarding  
**I want** the UI to automatically update when the agent advances my onboarding state  
**So that** I can see my progress and know which step I'm on

**Acceptance Criteria:**
- AC-1.1: When agent saves onboarding data that advances the state, `state_updated` must be `true` in the response
- AC-1.2: The `new_state` field must contain the updated state number
- AC-1.3: The `progress` object must reflect the updated completion percentage and completed states
- AC-1.4: The comparison logic must correctly detect state changes

### US-2: UI State Synchronization
**As a** user completing onboarding  
**I want** the progress bar and state metadata to update immediately after the agent advances my state  
**So that** I see accurate information about my current step

**Acceptance Criteria:**
- AC-2.1: Progress bar updates to show the new state number
- AC-2.2: State metadata (name, description) updates to reflect the new state
- AC-2.3: Completion percentage updates to reflect the new progress
- AC-2.4: Completed states list includes the just-completed state

### US-3: Consistent State Tracking
**As a** developer  
**I want** the backend to correctly track state changes during agent interactions  
**So that** the frontend receives accurate state update information

**Acceptance Criteria:**
- AC-3.1: State comparison uses the correct before/after states
- AC-3.2: State updates are committed to the database before the comparison
- AC-3.3: The response includes all necessary information for UI updates
- AC-3.4: Logs accurately reflect the state update detection

## Technical Context

### Backend Flow
1. User sends message with `current_state: 1`
2. Endpoint loads onboarding state from database (state 1)
3. Agent processes message and calls `save_onboarding_step(step=1, data={...})`
4. `save_onboarding_step` updates `current_step` to 1 (or advances to 2 if step > current_step)
5. Endpoint reloads onboarding state to check for updates
6. Comparison: `updated_state.current_step > state.current_step`

### Frontend Flow
1. User sends message
2. Frontend receives response with `state_updated` and `new_state`
3. If `state_updated === true`, frontend updates:
   - `currentState` to `new_state`
   - `completionPercentage` from `progress.completion_percentage`
   - `completedStates` to include the previous state
   - Fetches updated metadata for the new state

### API Response Schema
```typescript
{
  response: string;
  agent_type: string;
  state_updated: boolean;
  new_state: number | null;
  progress: {
    current_state: number;
    total_states: number;
    completed_states: number[];
    completion_percentage: number;
    is_complete: boolean;
  };
}
```

## Constraints

1. Must maintain backward compatibility with existing frontend code
2. Must not break existing onboarding flow
3. Must handle edge cases:
   - Agent saves data but doesn't advance state (e.g., user provides incomplete info)
   - Agent advances multiple states in one interaction (unlikely but possible)
   - Database transaction failures
4. Must work with all 9 onboarding states
5. Must work with all agent types (workout, diet, scheduler, supplement)

## Success Metrics

1. 100% of state updates are correctly detected by the backend
2. 100% of UI updates happen immediately after state changes
3. Zero state synchronization bugs reported by users
4. Logs show consistent state tracking throughout the flow

## Out of Scope

1. Real-time state updates via WebSockets (future enhancement)
2. Optimistic UI updates (frontend assumes success before backend confirms)
3. State rollback on errors
4. Multi-user state synchronization
5. State update animations or transitions

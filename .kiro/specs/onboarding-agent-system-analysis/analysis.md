# Onboarding Agent System - Implementation Analysis

## Current State Analysis

### Current Implementation
The existing onboarding system is a **form-based flow** with:

1. **Data Model** (`OnboardingState`):
   - `current_step`: Integer (0-9)
   - `is_complete`: Boolean
   - `step_data`: JSONB storing all step data
   - `agent_history`: JSONB tracking agent routing

2. **Service Layer** (`OnboardingService`):
   - Step-by-step validation
   - JSONB-based data storage
   - Profile creation on completion
   - 9-state flow (consolidated from original 11 steps)

3. **API Endpoints**:
   - `GET /api/v1/onboarding/progress` - Progress tracking
   - `GET /api/v1/onboarding/state` - Current state
   - `POST /api/v1/onboarding/step` - Save step data
   - `POST /api/v1/onboarding/complete` - Complete onboarding

4. **Agent Integration**:
   - `STATE_TO_AGENT_MAP` maps steps to agents
   - Agents are used but not conversationally
   - No chat-based onboarding flow

### Target State (from TRD)
The new system requires:

1. **Conversational Onboarding**:
   - Each step handled by dedicated AI agent
   - Agents ask personalized questions
   - Context passed between agents
   - Plan proposal and approval workflow

2. **New Data Model**:
   - `current_agent`: String field for active agent
   - `agent_context`: JSONB for inter-agent context
   - `conversation_history`: JSONB for chat history

3. **New API Endpoints**:
   - `POST /api/v1/onboarding/chat` - Chat with current agent
   - `GET /api/v1/onboarding/current-agent` - Get agent info

4. **Agent Architecture**:
   - `BaseOnboardingAgent` abstract class
   - 5 specialized onboarding agents
   - `OnboardingAgentOrchestrator` for routing
   - Tools for saving data and generating plans

## Implementation Breakdown

Based on the TRD complexity, I recommend splitting into **4 separate specs**:

### Spec 1: Foundation & Data Model
**Scope**: Database schema changes and base infrastructure
- Update `OnboardingState` model with new fields
- Create `BaseOnboardingAgent` abstract class
- Create `OnboardingAgentOrchestrator` service
- Add new API endpoints (skeleton)
- Migration scripts

**Complexity**: Medium
**Dependencies**: None
**Estimated Effort**: 1-2 weeks

### Spec 2: Fitness & Goal Agents
**Scope**: First two onboarding agents
- Implement `FitnessAssessmentAgent` (Steps 1-2)
- Implement `GoalSettingAgent` (Step 3)
- Agent tools for saving fitness data
- Context handover between agents
- Testing

**Complexity**: Medium
**Dependencies**: Spec 1
**Estimated Effort**: 1-2 weeks

### Spec 3: Planning Agents with Proposal Workflow
**Scope**: Workout and diet planning with approval
- Implement `WorkoutPlanningAgent` (Steps 4-5)
- Implement `DietPlanningAgent` (Steps 6-7)
- Plan generation services
- Conversational approval detection
- Plan modification workflow
- Testing

**Complexity**: High (includes plan generation)
**Dependencies**: Spec 1, Spec 2
**Estimated Effort**: 2-3 weeks

### Spec 4: Scheduling Agent & Completion
**Scope**: Final agent and onboarding completion
- Implement `SchedulingAgent` (Steps 8-9)
- Complete onboarding flow integration
- Profile creation from agent context
- Post-onboarding transition
- End-to-end testing

**Complexity**: Medium
**Dependencies**: Spec 1, Spec 2, Spec 3
**Estimated Effort**: 1-2 weeks

## Key Technical Decisions

### 1. Agent Context Structure
Use JSONB `agent_context` field with nested structure:
```json
{
  "fitness_assessment": {
    "fitness_level": "intermediate",
    "completed_at": "2024-01-15T10:30:00Z"
  },
  "goal_setting": {...},
  "workout_planning": {...},
  "diet_planning": {...},
  "scheduling": {...}
}
```

### 2. Conversational Approval Detection
Agents use LLM to detect approval intent from user messages:
- "Yes", "Looks good", "Perfect", "I approve", etc.
- Call `save_*_plan(plan_data, user_approved=True)` tool
- Advance to next agent automatically

### 3. Agent Tools Architecture
Each agent has domain-specific tools:
- `save_*_data()` - Save step data to context
- `generate_*_plan()` - Generate plans (workout/meal)
- `modify_*_plan()` - Modify proposed plans
- Tools are LangChain `@tool` decorated functions

### 4. Backward Compatibility
- Keep existing `POST /api/v1/onboarding/step` endpoint
- New chat endpoint is additive
- Existing step_data JSONB structure preserved
- Migration path for in-progress onboarding

## Risk Assessment

### High Risk Areas
1. **Plan Generation Quality**: Workout/meal plans must be realistic
2. **Approval Detection**: Must accurately detect user approval intent
3. **Context Handover**: Data must flow correctly between agents
4. **Performance**: Chat latency must be acceptable (<2s)

### Mitigation Strategies
1. Use existing plan generation services if available
2. Explicit approval keywords + LLM intent detection
3. Comprehensive integration tests for context flow
4. Cache agent instances, optimize LLM calls

## Testing Strategy

### Unit Tests
- Agent tool functions
- Validation logic
- Context serialization/deserialization

### Integration Tests
- Agent-to-agent handover
- Complete onboarding flow
- Plan generation and approval
- Profile creation from context

### Property-Based Tests
- Context structure invariants
- Step progression rules
- Data validation properties

## Migration Considerations

### Database Migration
- Add new columns to `onboarding_states` table
- Backfill `agent_context` from existing `step_data`
- No breaking changes to existing columns

### API Versioning
- New endpoints are additive (no breaking changes)
- Existing endpoints continue to work
- Frontend can adopt new chat flow incrementally

### Rollback Plan
- New columns are nullable
- Old endpoints still functional
- Can disable new chat endpoint via feature flag

## Success Metrics

### Functional
- All 5 agents implemented and tested
- Complete onboarding flow works end-to-end
- Profile creation from agent context successful
- Context handover 100% accurate

### Performance
- Chat response time < 2s (p95)
- Plan generation < 5s
- Complete onboarding < 15 minutes

### Quality
- Test coverage > 80%
- Zero data loss during agent transitions
- User approval detection > 95% accurate

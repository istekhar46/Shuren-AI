# Backend Onboarding Chat Integration - Specification Summary

**Document Version:** 1.0  
**Created:** 2026-02-11  
**Status:** Approved - Ready for Implementation  
**Full Spec:** `.kiro/specs/backend-onboarding-chat-integration/requirements.md`

---

## Executive Summary

This specification defines backend modifications to support chat-based onboarding with specialized AI agents, consolidating the existing 11-step process into 9 states aligned with agent responsibilities while maintaining backward compatibility.

---

## Key Changes Overview

### 1. Onboarding State Consolidation

**From:** 11 sequential steps  
**To:** 9 agent-aligned states

**Mapping:**
- Remove Step 1 (basic info) → Move to registration
- Step 2 → State 1: Fitness Level (Workout Planning Agent)
- Step 3 → State 2: Fitness Goals (Workout Planning Agent)
- Steps 4 & 5 → State 3: Workout Constraints (Workout Planning Agent) **[MERGED]**
- Step 6 → State 4: Dietary Preferences (Diet Planning Agent)
- Step 7 → State 5: Meal Plan (Diet Planning Agent)
- Step 8 → State 6: Meal Schedule (Scheduling Agent)
- Step 9 → State 7: Workout Schedule (Scheduling Agent)
- Step 10 → State 8: Hydration (Scheduling Agent)
- Step 11 → State 9: Supplements (Supplement Agent) **[OPTIONAL]**

### 2. New API Endpoints

#### `GET /api/v1/onboarding/progress`
Returns rich progress metadata for UI indicators.

**Response:**
```json
{
  "current_state": 3,
  "total_states": 9,
  "completed_states": [1, 2],
  "current_state_info": {
    "name": "Workout Preferences & Constraints",
    "agent": "workout_planning",
    "description": "Tell us about your equipment and limitations"
  },
  "completion_percentage": 33,
  "can_complete": false
}
```

#### `POST /api/v1/chat/onboarding`
Handles chat-based onboarding with automatic agent routing.

**Request:**
```json
{
  "message": "I'm a beginner",
  "current_state": 1
}
```

**Response:**
```json
{
  "response": "Great! As a beginner, I'll create a plan that...",
  "agent_type": "workout_planning",
  "state_updated": true,
  "new_state": 2,
  "progress": {
    "current_state": 2,
    "completion_percentage": 22
  }
}
```

### 3. Modified Endpoints

#### `GET /api/v1/users/me`
**Added:** `access_control` object with feature locks

```json
{
  "access_control": {
    "can_access_dashboard": false,
    "can_access_workouts": false,
    "can_access_meals": false,
    "can_access_chat": true,
    "locked_features": ["dashboard", "workouts", "meals", "profile"],
    "unlock_message": "Complete onboarding to unlock all features"
  }
}
```

#### `POST /api/v1/onboarding/step`
**Changed:** Supports states 1-9 (was steps 1-11)  
**Added:** `X-Agent-Context` header support

#### `POST /api/v1/chat`
**Added:** Agent access control enforcement
- Pre-onboarding: Returns 403 "Complete onboarding first"
- Post-onboarding: Forces `AgentType.GENERAL`, rejects specialized agents

---

## Agent Function Tools

Each specialized agent gets function tools to save onboarding data:

### Workout Planning Agent (States 1-3)
- `save_fitness_level(fitness_level)`
- `save_fitness_goals(goals)`
- `save_workout_constraints(equipment, injuries, limitations, targets)`

### Diet Planning Agent (States 4-5)
- `save_dietary_preferences(diet_type, allergies, intolerances, dislikes)`
- `save_meal_plan(calories, protein%, carbs%, fats%)`

### Scheduling & Reminder Agent (States 6-8)
- `save_meal_schedule(meals)`
- `save_workout_schedule(workouts)`
- `save_hydration_schedule(water_target, reminder_frequency)`

### Supplement Guidance Agent (State 9)
- `save_supplement_preferences(interested, current_supplements)`

**All tools internally call:** `POST /api/v1/onboarding/step`

---

## Database Changes

### Schema Update
```sql
-- Update constraint
ALTER TABLE onboarding_states 
DROP CONSTRAINT valid_current_step;

ALTER TABLE onboarding_states 
ADD CONSTRAINT valid_current_step 
CHECK (current_step >= 0 AND current_step <= 9);
```

### Data Migration
- Remap existing 11-step data to 9-state format
- Merge steps 4 & 5 into state 3
- Preserve original data in `step_data` JSONB
- Migration script processes 1000 users at a time

---

## Service Layer Changes

### OnboardingService
**New Methods:**
- `get_progress(user_id)` - Rich progress metadata
- `get_state_info(state_number)` - State metadata
- `can_complete_onboarding(user_id)` - Completion check

**Updated Validators:**
- 9 state validators (was 11 step validators)
- State 3 merges validation from old steps 4 & 5

### AgentOrchestrator
**New Method:**
- `route_onboarding_query(user_id, query, current_state)` - Routes to appropriate agent

**Updated Access Control:**
```python
# Pre-onboarding: Allow specialized agents
if not user.onboarding_completed:
    # Route based on current_state
    
# Post-onboarding: Force general agent
else:
    if agent_type != AgentType.GENERAL:
        raise HTTPException(403, "Only general agent available")
```

---

## Implementation Approach

### Hybrid Strategy
- **Keep existing REST endpoints** for backward compatibility
- **Add new chat endpoints** for agent-driven flow
- **Agents use REST endpoints as function tools**
- **Both paths lead to same data storage**

### Benefits
- No breaking changes
- Gradual migration path
- Easy testing and debugging
- Flexible for future enhancements

---

## Migration Timeline

### Week 1: Database & Data Migration
- Update schema constraints
- Run data migration script
- Verify data integrity

### Week 2-3: Backend Implementation
- Implement new endpoints
- Update existing endpoints
- Add agent function tools
- Update service layer

### Week 3: Testing
- Unit tests
- Integration tests
- API tests
- Performance tests

### Week 4: Deployment
- Deploy to staging
- Frontend integration
- UAT
- Production deployment

---

## Success Metrics

### Performance Targets
- Progress endpoint: < 50ms (P95)
- Chat onboarding endpoint: < 2s (P95)
- Step save endpoint: < 200ms (P95)

### Business Metrics
- Onboarding completion rate: 70% (target)
- Validation error rate: < 1%
- Server error rate: < 0.1%

---

## Access Control Rules

### During Onboarding (`onboarding_completed = false`)
- ✅ Can access: Chat (onboarding endpoint only)
- ❌ Cannot access: Dashboard, Workouts, Meals, Profile
- ✅ Agents allowed: Specialized agents based on current state
- ❌ Agents blocked: General agent

### After Onboarding (`onboarding_completed = true`)
- ✅ Can access: All features unlocked
- ✅ Agents allowed: General agent only
- ❌ Agents blocked: All specialized agents

---

## Error Handling

### 400 Validation Error
```json
{
  "detail": "Protein percentage must be between 0 and 100",
  "field": "protein_percentage",
  "error_code": "VALIDATION_ERROR"
}
```

### 403 Access Control Error
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

---

## Testing Requirements

### Must Test
- [ ] State consolidation (11 → 9)
- [ ] Agent routing per state
- [ ] Access control enforcement
- [ ] Progress calculation
- [ ] Data migration accuracy
- [ ] Complete onboarding flow via chat
- [ ] Agent function tool calls
- [ ] Error handling and rollback
- [ ] Concurrent sessions
- [ ] Backward compatibility

---

## Dependencies

### Internal
- Agent orchestration system
- LLM integration (Anthropic Claude)
- Authentication system
- Database (PostgreSQL 15+)

### External
- Frontend team (UI implementation)
- DevOps team (deployment)
- QA team (testing)
- Product team (acceptance)

---

## Open Questions

1. Should we support non-sequential state progression?
2. How to handle post-onboarding profile changes?
3. Can users skip optional state 9 (supplements)?
4. How long to retain original 11-step data?
5. Can agents navigate backward during onboarding?

**Status:** Awaiting product team input

---

## Next Steps

1. ✅ Requirements approved
2. ⏳ Create design.md with technical details
3. ⏳ Create tasks.md with implementation checklist
4. ⏳ Begin Week 1: Database migration
5. ⏳ Begin Week 2: Backend implementation

---

**For detailed requirements, see:** `.kiro/specs/backend-onboarding-chat-integration/requirements.md`

**For implementation tasks, see:** `.kiro/specs/backend-onboarding-chat-integration/tasks.md` (coming soon)

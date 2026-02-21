# Backend Onboarding Chat Integration - Requirements

**Feature Name:** backend-onboarding-chat-integration  
**Status:** Draft  
**Created:** 2026-02-11  
**Owner:** Backend Team  
**Priority:** High

---

## 1. Overview

This specification defines the backend modifications required to support the refined product requirements for Shuren AI's onboarding system. The goal is to enable a chat-first onboarding experience where specialized AI agents guide users through profile setup while maintaining the existing REST API infrastructure.

### 1.1 Problem Statement

The current backend implements a traditional step-based REST API for onboarding (11 steps), but the refined product requirements specify:
- Chat-based onboarding with specialized agents
- 9 onboarding states (reduced from 11 steps)
- Agent-specific routing during onboarding
- Navigation lock until onboarding completion
- General agent only after onboarding

### 1.2 Goals

- Enable chat-based onboarding with specialized agents
- Consolidate 11 steps into 9 states aligned with agent responsibilities
- Provide rich progress tracking for UI indicators
- Implement agent access control based on onboarding status
- Maintain backward compatibility with existing REST endpoints

### 1.3 Non-Goals

- Frontend implementation (separate spec)
- LiveKit voice integration (future enhancement)
- Agent LLM prompt engineering (separate spec)
- Real-time WebSocket progress updates (future enhancement)

---

## 2. User Stories

### 2.1 As a New User
**Story:** As a new user, I want to complete onboarding through a conversational chat interface so that the process feels natural and guided.

**Acceptance Criteria:**
- [ ] 2.1.1 User can start onboarding via chat endpoint
- [ ] 2.1.2 Appropriate specialized agent handles each onboarding state
- [ ] 2.1.3 Agent validates responses before saving data
- [ ] 2.1.4 User receives confirmation after each state completion
- [ ] 2.1.5 Progress is saved incrementally (can resume if interrupted)

### 2.2 As a Frontend Developer
**Story:** As a frontend developer, I need clear progress indicators so that I can show users where they are in the onboarding flow.

**Acceptance Criteria:**
- [ ] 2.2.1 Backend provides current state number (1-9)
- [ ] 2.2.2 Backend provides list of completed states
- [ ] 2.2.3 Backend provides metadata for current and next states
- [ ] 2.2.4 Backend provides completion percentage
- [ ] 2.2.5 Response includes agent type for current state

### 2.3 As a Specialized Agent
**Story:** As a specialized agent, I need function tools to save onboarding data so that I can persist user responses during conversation.

**Acceptance Criteria:**
- [ ] 2.3.1 Agent can call existing REST endpoints as function tools
- [ ] 2.3.2 Agent receives validation errors in structured format
- [ ] 2.3.3 Agent can query current onboarding state
- [ ] 2.3.4 Agent calls are logged with agent context
- [ ] 2.3.5 Agent receives success confirmation with next state info

### 2.4 As a Completed User
**Story:** As a user who completed onboarding, I want access to only the general agent so that I have a consistent post-onboarding experience.

**Acceptance Criteria:**
- [ ] 2.4.1 Chat endpoint routes all queries to general agent
- [ ] 2.4.2 Explicit agent_type selection returns 403 error
- [ ] 2.4.3 General agent has access to full user profile
- [ ] 2.4.4 Navigation lock is removed (all features accessible)
- [ ] 2.4.5 User can still view onboarding history

### 2.5 As a System Administrator
**Story:** As a system administrator, I need to understand which agent handled each onboarding interaction for debugging and analytics.

**Acceptance Criteria:**
- [ ] 2.5.1 Conversation messages include agent_type
- [ ] 2.5.2 Onboarding state includes agent routing history
- [ ] 2.5.3 Logs include agent context headers
- [ ] 2.5.4 Analytics can track completion rates per agent
- [ ] 2.5.5 Failed validations are logged with agent context

---

## 3. Functional Requirements

### 3.1 Onboarding State Consolidation

**Requirement:** Consolidate existing 11 steps into 9 states aligned with agent responsibilities.

**Current Steps (11):**
1. Basic info (age, gender, height, weight)
2. Fitness level
3. Fitness goals
4. Target metrics
5. Physical constraints
6. Dietary preferences
7. Meal planning
8. Meal schedule
9. Workout schedule
10. Hydration
11. Lifestyle baseline

**New States (9):**
1. Fitness Level Assessment (Workout Planning Agent)
2. Primary Fitness Goals (Workout Planning Agent)
3. Workout Preferences & Constraints (Workout Planning Agent)
4. Diet Preferences & Restrictions (Diet Planning Agent)
5. Fixed Meal Plan Selection (Diet Planning Agent)
6. Meal Timing Schedule (Scheduling & Reminder Agent)
7. Workout Schedule (Scheduling & Reminder Agent)
8. Hydration Schedule (Scheduling & Reminder Agent)
9. Supplement Preferences (Supplement Guidance Agent) - Optional

**Changes:**
- Remove step 1 (basic info) - collect during registration
- Merge steps 4 & 5 into state 3
- Renumber remaining steps to 1-9



### 3.2 New API Endpoints

#### 3.2.1 Onboarding Progress Endpoint

**Endpoint:** `GET /api/v1/onboarding/progress`

**Purpose:** Provide rich progress metadata for UI indicators

**Authentication:** Required (JWT)

**Response Schema:**
```json
{
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
  "is_complete": false,
  "completion_percentage": 33,
  "can_complete": false
}
```

**Business Rules:**
- Returns 404 if onboarding state not found
- `can_complete` is true only when all 9 states are completed
- `completion_percentage` = (completed_states / total_states) * 100
- `next_state_info` is null if on last state

#### 3.2.2 Agent-Driven Onboarding Chat Endpoint

**Endpoint:** `POST /api/v1/chat/onboarding`

**Purpose:** Handle chat-based onboarding with agent routing

**Authentication:** Required (JWT)

**Request Schema:**
```json
{
  "message": "I'm a beginner",
  "current_state": 1
}
```

**Response Schema:**
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

**Business Rules:**
- Only accessible if `onboarding_completed = false`
- Routes to appropriate agent based on `current_state`
- Agent internally calls `POST /api/v1/onboarding/step` as function tool
- Returns validation errors in conversational format
- Automatically advances state on successful data save

### 3.3 Modified API Endpoints

#### 3.3.1 Enhanced User Endpoint

**Endpoint:** `GET /api/v1/users/me`

**Changes:** Add `access_control` object to response

**New Response Fields:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "onboarding_completed": false,
  "access_control": {
    "can_access_dashboard": false,
    "can_access_workouts": false,
    "can_access_meals": false,
    "can_access_chat": true,
    "can_access_profile": false,
    "locked_features": ["dashboard", "workouts", "meals", "profile"],
    "unlock_message": "Complete onboarding to unlock all features",
    "onboarding_progress": {
      "current_state": 3,
      "total_states": 9,
      "completion_percentage": 33
    }
  }
}
```

**Business Rules:**
- `can_access_chat` is always true
- All other features locked until `onboarding_completed = true`
- `onboarding_progress` is null if onboarding complete

#### 3.3.2 Updated Onboarding Step Endpoint

**Endpoint:** `POST /api/v1/onboarding/step`

**Changes:** Support 9 states instead of 11, accept agent context

**Request Schema:**
```json
{
  "step": 3,
  "data": {
    "equipment": ["dumbbells", "resistance_bands"],
    "injuries": [],
    "limitations": ["lower_back_pain"]
  }
}
```

**Request Headers:**
```
X-Agent-Context: workout_planning (optional)
```

**Business Rules:**
- `step` must be 1-9 (changed from 1-11)
- Validation rules updated for consolidated states
- Agent context logged for analytics
- Returns next state information

#### 3.3.3 Chat Endpoint with Agent Restrictions

**Endpoint:** `POST /api/v1/chat`

**Changes:** Enforce agent access control based on onboarding status

**Business Rules:**
- If `onboarding_completed = false`:
  - Reject request with 403: "Complete onboarding first"
  - Suggest using `/api/v1/chat/onboarding` instead
- If `onboarding_completed = true`:
  - Ignore `agent_type` parameter if provided
  - Always route to `AgentType.GENERAL`
  - Return 403 if explicit non-general agent requested

### 3.4 Database Schema Changes

#### 3.4.1 OnboardingState Model Updates

**Changes:**
```python
# Update constraint
CONSTRAINT valid_current_step CHECK (current_step >= 0 AND current_step <= 9)
# Changed from: current_step <= 11
```

**Migration Required:**
- Update constraint in database
- Migrate existing step data (11 steps → 9 states)
- Preserve historical data in `step_data` JSONB

#### 3.4.2 Data Migration Strategy

**Mapping Logic:**
```
Old Step 1 (basic_info) → Move to User model during registration
Old Step 2 (fitness_level) → New State 1
Old Step 3 (fitness_goals) → New State 2
Old Steps 4 & 5 (target_metrics + constraints) → New State 3 (merged)
Old Step 6 (dietary_preferences) → New State 4
Old Step 7 (meal_planning) → New State 5
Old Step 8 (meal_schedule) → New State 6
Old Step 9 (workout_schedule) → New State 7
Old Step 10 (hydration) → New State 8
Old Step 11 (lifestyle_baseline) → New State 9
```

**Migration Script:**
```python
# For each existing onboarding_state:
# 1. Read step_data
# 2. Remap step numbers
# 3. Merge steps 4 & 5 into single state 3
# 4. Update current_step accordingly
# 5. Preserve original data in metadata
```

### 3.5 Service Layer Changes

#### 3.5.1 OnboardingService Updates

**New Methods:**
```python
async def get_progress(self, user_id: UUID) -> OnboardingProgress:
    """Get rich progress metadata for UI."""
    
async def get_state_info(self, state_number: int) -> StateInfo:
    """Get metadata for a specific state."""
    
async def can_complete_onboarding(self, user_id: UUID) -> bool:
    """Check if all required states are complete."""
```

**Updated Validators:**
- `_validate_state_1_fitness_level()` (was step 2)
- `_validate_state_2_fitness_goals()` (was step 3)
- `_validate_state_3_workout_constraints()` (merge of steps 4 & 5)
- `_validate_state_4_dietary_preferences()` (was step 6)
- `_validate_state_5_meal_plan()` (was step 7)
- `_validate_state_6_meal_schedule()` (was step 8)
- `_validate_state_7_workout_schedule()` (was step 9)
- `_validate_state_8_hydration()` (was step 10)
- `_validate_state_9_supplements()` (was step 11, now optional)

#### 3.5.2 AgentOrchestrator Updates

**New Method:**
```python
async def route_onboarding_query(
    self,
    user_id: UUID,
    query: str,
    current_state: int
) -> AgentResponse:
    """Route onboarding queries to appropriate specialized agent."""
    
    # Map state to agent
    agent_map = {
        1: AgentType.WORKOUT_PLANNING,
        2: AgentType.WORKOUT_PLANNING,
        3: AgentType.WORKOUT_PLANNING,
        4: AgentType.DIET_PLANNING,
        5: AgentType.DIET_PLANNING,
        6: AgentType.SCHEDULER,
        7: AgentType.SCHEDULER,
        8: AgentType.SCHEDULER,
        9: AgentType.SUPPLEMENT,
    }
    
    agent_type = agent_map.get(current_state)
    return await self.route_query(user_id, query, agent_type, onboarding_mode=True)
```

**Updated Access Control:**
```python
async def route_query(self, user_id, query, agent_type=None, onboarding_mode=False):
    user = await get_user(user_id)
    
    # Onboarding mode: allow specialized agents
    if onboarding_mode:
        if user.onboarding_completed:
            raise HTTPException(403, "Onboarding already completed")
        # Allow specialized agents during onboarding
    
    # Normal mode: enforce restrictions
    else:
        if not user.onboarding_completed:
            raise HTTPException(403, "Complete onboarding first")
        
        # Force general agent post-onboarding
        if agent_type and agent_type != AgentType.GENERAL:
            raise HTTPException(403, "Only general agent available")
        
        agent_type = AgentType.GENERAL
```



### 3.6 Agent Function Tools

#### 3.6.1 Tool Definitions for Specialized Agents

Each specialized agent needs function tools to save onboarding data. These tools wrap existing REST endpoints.

**Workout Planning Agent Tools:**
```python
@llm_function
async def save_fitness_level(
    fitness_level: Literal["beginner", "intermediate", "advanced"]
) -> dict:
    """Save user's fitness level (State 1)."""
    return await call_onboarding_step(1, {"fitness_level": fitness_level})

@llm_function
async def save_fitness_goals(
    goals: list[dict]
) -> dict:
    """Save user's fitness goals (State 2)."""
    return await call_onboarding_step(2, {"goals": goals})

@llm_function
async def save_workout_constraints(
    equipment: list[str],
    injuries: list[str],
    limitations: list[str],
    target_weight_kg: Optional[float] = None,
    target_body_fat_percentage: Optional[float] = None
) -> dict:
    """Save workout constraints and optional targets (State 3)."""
    data = {
        "equipment": equipment,
        "injuries": injuries,
        "limitations": limitations
    }
    if target_weight_kg:
        data["target_weight_kg"] = target_weight_kg
    if target_body_fat_percentage:
        data["target_body_fat_percentage"] = target_body_fat_percentage
    
    return await call_onboarding_step(3, data)
```

**Diet Planning Agent Tools:**
```python
@llm_function
async def save_dietary_preferences(
    diet_type: str,
    allergies: list[str],
    intolerances: list[str],
    dislikes: list[str]
) -> dict:
    """Save dietary preferences and restrictions (State 4)."""
    return await call_onboarding_step(4, {
        "diet_type": diet_type,
        "allergies": allergies,
        "intolerances": intolerances,
        "dislikes": dislikes
    })

@llm_function
async def save_meal_plan(
    daily_calorie_target: int,
    protein_percentage: float,
    carbs_percentage: float,
    fats_percentage: float
) -> dict:
    """Save meal plan with calorie and macro targets (State 5)."""
    return await call_onboarding_step(5, {
        "daily_calorie_target": daily_calorie_target,
        "protein_percentage": protein_percentage,
        "carbs_percentage": carbs_percentage,
        "fats_percentage": fats_percentage
    })
```

**Scheduling & Reminder Agent Tools:**
```python
@llm_function
async def save_meal_schedule(
    meals: list[dict]
) -> dict:
    """Save meal timing schedule (State 6)."""
    return await call_onboarding_step(6, {"meals": meals})

@llm_function
async def save_workout_schedule(
    workouts: list[dict]
) -> dict:
    """Save workout schedule (State 7)."""
    return await call_onboarding_step(7, {"workouts": workouts})

@llm_function
async def save_hydration_schedule(
    daily_water_target_ml: int,
    reminder_frequency_minutes: int
) -> dict:
    """Save hydration preferences (State 8)."""
    return await call_onboarding_step(8, {
        "daily_water_target_ml": daily_water_target_ml,
        "reminder_frequency_minutes": reminder_frequency_minutes
    })
```

**Supplement Guidance Agent Tools:**
```python
@llm_function
async def save_supplement_preferences(
    interested_in_supplements: bool,
    current_supplements: list[str] = []
) -> dict:
    """Save supplement preferences (State 9 - Optional)."""
    return await call_onboarding_step(9, {
        "interested_in_supplements": interested_in_supplements,
        "current_supplements": current_supplements
    })
```

**Helper Function:**
```python
async def call_onboarding_step(step: int, data: dict) -> dict:
    """Internal helper to call onboarding step endpoint."""
    response = await http_client.post(
        "/api/v1/onboarding/step",
        json={"step": step, "data": data},
        headers={"X-Agent-Context": get_current_agent_type()}
    )
    
    if response.status_code == 400:
        # Return validation error in agent-friendly format
        error = response.json()
        return {
            "success": False,
            "error": error["detail"],
            "field": error.get("field")
        }
    
    return {
        "success": True,
        "message": f"State {step} saved successfully",
        "next_state": step + 1 if step < 9 else None
    }
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **Onboarding Progress Endpoint:** < 50ms response time
- **Chat Onboarding Endpoint:** < 2s response time (including LLM)
- **Step Save Endpoint:** < 200ms response time
- **Database Migration:** < 5 minutes for 100K users

### 4.2 Scalability

- Support 10,000 concurrent onboarding sessions
- Handle 1M completed onboarding profiles
- Agent function tool calls: < 100ms overhead

### 4.3 Reliability

- Data consistency: All-or-nothing state updates
- Idempotent step saves (can retry safely)
- Graceful degradation if agent unavailable
- Automatic retry for transient failures

### 4.4 Security

- JWT authentication required for all endpoints
- Agent context headers logged for audit
- Rate limiting: 100 requests/minute per user
- Input validation on all data fields
- SQL injection prevention via parameterized queries

### 4.5 Observability

- Log all agent routing decisions
- Track completion rates per state
- Monitor validation failure rates
- Alert on high drop-off rates
- Trace agent function tool calls

---

## 5. Data Validation Rules

### 5.1 State 1: Fitness Level
- `fitness_level`: Required, one of ["beginner", "intermediate", "advanced"]

### 5.2 State 2: Fitness Goals
- `goals`: Required, non-empty array
- Each goal must have `goal_type`: one of ["fat_loss", "muscle_gain", "general_fitness"]

### 5.3 State 3: Workout Constraints
- `equipment`: Required, array of strings
- `injuries`: Required, array of strings (can be empty)
- `limitations`: Required, array of strings (can be empty)
- `target_weight_kg`: Optional, 30-300 if provided
- `target_body_fat_percentage`: Optional, 1-50 if provided

### 5.4 State 4: Dietary Preferences
- `diet_type`: Required, one of ["omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo"]
- `allergies`: Required, array of strings (can be empty)
- `intolerances`: Required, array of strings (can be empty)
- `dislikes`: Required, array of strings (can be empty)

### 5.5 State 5: Meal Plan
- `daily_calorie_target`: Required, 1000-5000
- `protein_percentage`: Required, 0-100
- `carbs_percentage`: Required, 0-100
- `fats_percentage`: Required, 0-100
- Sum of percentages must equal 100 (±0.01 tolerance)

### 5.6 State 6: Meal Schedule
- `meals`: Required, non-empty array
- Each meal must have:
  - `meal_name`: Required, non-empty string
  - `scheduled_time`: Required, HH:MM format
  - `enable_notifications`: Optional, boolean (default true)

### 5.7 State 7: Workout Schedule
- `workouts`: Required, non-empty array
- Each workout must have:
  - `day_of_week`: Required, 0-6 (Monday-Sunday)
  - `scheduled_time`: Required, HH:MM format
  - `enable_notifications`: Optional, boolean (default true)

### 5.8 State 8: Hydration Schedule
- `daily_water_target_ml`: Required, 500-10000
- `reminder_frequency_minutes`: Required, 15-480

### 5.9 State 9: Supplement Preferences (Optional)
- `interested_in_supplements`: Required, boolean
- `current_supplements`: Optional, array of strings

---

## 6. Error Handling

### 6.1 Validation Errors (400)

**Response Format:**
```json
{
  "detail": "Protein percentage must be between 0 and 100",
  "field": "protein_percentage",
  "error_code": "VALIDATION_ERROR"
}
```

### 6.2 Access Control Errors (403)

**Scenarios:**
- Accessing chat endpoint before onboarding complete
- Requesting specialized agent after onboarding
- Accessing locked features during onboarding

**Response Format:**
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

### 6.3 Not Found Errors (404)

**Scenarios:**
- Onboarding state not found
- User profile not found

**Response Format:**
```json
{
  "detail": "Onboarding state not found",
  "error_code": "NOT_FOUND"
}
```

### 6.4 Server Errors (500)

**Scenarios:**
- Database connection failure
- Agent service unavailable
- Unexpected exceptions

**Response Format:**
```json
{
  "detail": "An unexpected error occurred",
  "error_code": "INTERNAL_ERROR",
  "request_id": "uuid"
}
```

---

## 7. Testing Requirements

### 7.1 Unit Tests

- [ ] Test state consolidation logic (11 → 9)
- [ ] Test validation for each state
- [ ] Test agent routing based on state
- [ ] Test access control enforcement
- [ ] Test progress calculation
- [ ] Test data migration script

### 7.2 Integration Tests

- [ ] Test complete onboarding flow via chat
- [ ] Test agent function tool calls
- [ ] Test state transitions
- [ ] Test error handling and rollback
- [ ] Test concurrent onboarding sessions
- [ ] Test backward compatibility with existing data

### 7.3 API Tests

- [ ] Test all new endpoints
- [ ] Test modified endpoints
- [ ] Test authentication and authorization
- [ ] Test rate limiting
- [ ] Test error responses
- [ ] Test response schemas

### 7.4 Performance Tests

- [ ] Load test onboarding endpoints
- [ ] Stress test concurrent sessions
- [ ] Benchmark database migration
- [ ] Profile agent function tool overhead

---

## 8. Migration Plan

### 8.1 Phase 1: Database Schema Update (Week 1)

1. Create Alembic migration for constraint update
2. Test migration on staging database
3. Run migration on production (low-traffic window)
4. Verify constraint updated successfully

### 8.2 Phase 2: Data Migration (Week 1)

1. Create data migration script
2. Test on sample of production data
3. Run migration in batches (1000 users at a time)
4. Verify data integrity after migration
5. Keep backup of original data for 30 days

### 8.3 Phase 3: Backend Implementation (Week 2-3)

1. Implement new endpoints
2. Update existing endpoints
3. Add agent function tools
4. Update service layer logic
5. Add access control enforcement

### 8.4 Phase 4: Testing (Week 3)

1. Run unit tests
2. Run integration tests
3. Run API tests
4. Perform manual testing
5. Load testing on staging

### 8.5 Phase 5: Deployment (Week 4)

1. Deploy to staging
2. Frontend integration testing
3. User acceptance testing
4. Deploy to production
5. Monitor metrics and errors

---

## 9. Rollback Plan

### 9.1 If Migration Fails

1. Restore database from backup
2. Revert Alembic migration
3. Investigate failure cause
4. Fix issues and retry

### 9.2 If Deployment Fails

1. Revert to previous backend version
2. Database remains compatible (backward compatible changes)
3. Investigate failure cause
4. Fix issues and redeploy

### 9.3 Data Rollback

- Original step data preserved in `step_data` JSONB
- Can reconstruct original state if needed
- Backup retained for 30 days

---

## 10. Success Metrics

### 10.1 Onboarding Completion

- **Target:** 70% completion rate (up from current baseline)
- **Measure:** Percentage of users who complete all 9 states
- **Timeline:** Within 30 days of deployment

### 10.2 Performance

- **Target:** < 50ms for progress endpoint
- **Target:** < 2s for chat onboarding endpoint
- **Target:** < 200ms for step save endpoint
- **Measure:** P95 latency

### 10.3 Error Rates

- **Target:** < 1% validation error rate
- **Target:** < 0.1% server error rate
- **Measure:** Error rate per endpoint

### 10.4 User Experience

- **Target:** Positive feedback on chat-based onboarding
- **Measure:** User surveys and feedback
- **Timeline:** 30 days post-deployment

---

## 11. Dependencies

### 11.1 Internal Dependencies

- Agent orchestration system must be functional
- LLM integration must be stable
- Database must support JSONB operations
- Authentication system must be working

### 11.2 External Dependencies

- Anthropic Claude API (for agents)
- PostgreSQL 15+
- Redis 7.0+ (for caching)

### 11.3 Team Dependencies

- Frontend team for UI implementation
- DevOps team for deployment
- QA team for testing
- Product team for acceptance

---

## 12. Open Questions

1. **Q:** Should we support resuming onboarding from any state, or only sequential progression?
   **A:** TBD - Need product input

2. **Q:** What happens if a user wants to change their onboarding responses after completion?
   **A:** TBD - Profile update flow (separate spec)

3. **Q:** Should we allow skipping optional state 9 (supplements)?
   **A:** TBD - Need product input

4. **Q:** How long should we retain original 11-step data after migration?
   **A:** TBD - Need compliance input

5. **Q:** Should agents be able to go back to previous states during onboarding?
   **A:** TBD - Need UX input

---

## 13. Appendix

### 13.1 State-to-Agent Mapping

| State | Name | Agent | Required |
|-------|------|-------|----------|
| 1 | Fitness Level Assessment | Workout Planning | Yes |
| 2 | Primary Fitness Goals | Workout Planning | Yes |
| 3 | Workout Preferences & Constraints | Workout Planning | Yes |
| 4 | Diet Preferences & Restrictions | Diet Planning | Yes |
| 5 | Fixed Meal Plan Selection | Diet Planning | Yes |
| 6 | Meal Timing Schedule | Scheduling & Reminder | Yes |
| 7 | Workout Schedule | Scheduling & Reminder | Yes |
| 8 | Hydration Schedule | Scheduling & Reminder | Yes |
| 9 | Supplement Preferences | Supplement Guidance | No |

### 13.2 API Endpoint Summary

**New Endpoints:**
- `GET /api/v1/onboarding/progress`
- `POST /api/v1/chat/onboarding`

**Modified Endpoints:**
- `GET /api/v1/users/me` (add access_control)
- `POST /api/v1/onboarding/step` (support 9 states)
- `POST /api/v1/chat` (enforce agent restrictions)

**Unchanged Endpoints:**
- `GET /api/v1/onboarding/state`
- `POST /api/v1/onboarding/complete`
- All other existing endpoints

### 13.3 Database Changes Summary

**Schema Changes:**
- Update `OnboardingState.current_step` constraint (0-11 → 0-9)

**Data Migration:**
- Remap 11 steps to 9 states
- Merge steps 4 & 5 into state 3
- Preserve original data in metadata

**No Breaking Changes:**
- Existing data remains queryable
- Backward compatible migration

---

**Document Status:** Ready for Design Phase  
**Next Steps:** Create design.md with technical implementation details

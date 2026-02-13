# Agent Orchestration Refinement - Requirements

**Feature Name:** agent-orchestration-refinement  
**Status:** Draft  
**Created:** 2026-02-14  
**Owner:** Backend Team  
**Priority:** High

---

## 1. Overview

This specification defines the modifications required to the Agent Orchestration system to fully align with the refined product requirements for Shuren AI. The current implementation already has the `onboarding_mode` parameter, but needs refinement to ensure proper agent access control, context management, and alignment with the product vision.

### 1.1 Problem Statement

The current `AgentOrchestrator` implementation has basic onboarding mode support, but needs refinement to:
- Ensure strict enforcement of agent access control during and after onboarding
- Properly manage agent context based on onboarding completion status
- Align agent routing with the 6 specialized agents defined in product requirements
- Ensure specialized agents are ONLY accessible during onboarding
- Ensure general agent is ONLY accessible post-onboarding
- Improve error messaging for better user experience

### 1.2 Goals

- Refine agent access control logic to match product requirements exactly
- Ensure specialized agents (Workout, Diet, Scheduler, Supplement) are onboarding-only
- Ensure general agent is post-onboarding only
- Add comprehensive validation and error handling
- Improve logging for agent routing decisions
- Maintain backward compatibility with existing voice/text modes
- Ensure performance targets are met (<2s voice, <3s text)

### 1.3 Non-Goals

- Changing the fundamental architecture of AgentOrchestrator
- Modifying individual agent implementations (separate specs)
- Adding new agent types beyond the 6 defined
- Implementing LiveKit voice integration changes
- Frontend modifications

---

## 2. User Stories

### 2.1 As a New User During Onboarding
**Story:** As a new user going through onboarding, I want the system to route my queries to the appropriate specialized agent based on my current onboarding state, so that I receive expert guidance for each step.

**Acceptance Criteria:**
- [ ] 2.1.1 System routes to Workout agent for states 1-3
- [ ] 2.1.2 System routes to Diet agent for states 4-5
- [ ] 2.1.3 System routes to Scheduler agent for states 6-8
- [ ] 2.1.4 System routes to Supplement agent for state 9
- [ ] 2.1.5 System rejects access to general agent during onboarding
- [ ] 2.1.6 System provides clear error messages if routing fails

### 2.2 As a Completed User
**Story:** As a user who has completed onboarding, I want all my queries to be handled by the general agent, so that I have a consistent conversational experience.

**Acceptance Criteria:**
- [ ] 2.2.1 System routes all queries to general agent
- [ ] 2.2.2 System rejects explicit requests for specialized agents
- [ ] 2.2.3 System provides clear error message if specialized agent requested
- [ ] 2.2.4 System loads full user context for general agent
- [ ] 2.2.5 General agent has access to all user data (workouts, meals, schedules)

### 2.3 As a System Administrator
**Story:** As a system administrator, I need detailed logging of agent routing decisions so that I can debug issues and monitor system behavior.

**Acceptance Criteria:**
- [ ] 2.3.1 All routing decisions are logged with user_id and agent_type
- [ ] 2.3.2 Access control violations are logged with reason
- [ ] 2.3.3 Onboarding mode is included in all log entries
- [ ] 2.3.4 Performance metrics are logged (routing time)
- [ ] 2.3.5 Classification results are logged for debugging

### 2.4 As a Developer
**Story:** As a developer, I need clear error messages and exceptions so that I can quickly identify and fix integration issues.

**Acceptance Criteria:**
- [ ] 2.4.1 ValueError raised with descriptive message for access control violations
- [ ] 2.4.2 ValueError raised with descriptive message for invalid agent types
- [ ] 2.4.3 ValueError raised with descriptive message for missing user/onboarding state
- [ ] 2.4.4 All exceptions include context (user_id, agent_type, onboarding_mode)
- [ ] 2.4.5 Error messages suggest corrective actions

---

## 3. Functional Requirements

### 3.1 Agent Access Control Refinement

**Requirement:** Enforce strict agent access control based on onboarding completion status.

#### 3.1.1 During Onboarding (onboarding_mode=True)

**Rules:**
1. **ONLY specialized agents are accessible** (Workout, Diet, Scheduler, Supplement)
2. **General agent is NOT accessible**
3. **Tracker agent is NOT accessible** (tracking happens post-onboarding)
4. **Test agent remains accessible** (for testing purposes)

**Validation:**
- If `onboarding_state.is_complete == True`, reject with error: "Onboarding already completed. Use regular chat endpoint."
- If `agent_type == AgentType.GENERAL`, reject with error: "General agent not available during onboarding. Complete onboarding first."
- If `agent_type == AgentType.TRACKER`, reject with error: "Tracker agent not available during onboarding."

#### 3.1.2 Post-Onboarding (onboarding_mode=False)

**Rules:**
1. **ONLY general agent is accessible**
2. **All specialized agents are NOT accessible** (Workout, Diet, Scheduler, Supplement)
3. **Tracker agent is accessible** (via general agent delegation)
4. **Test agent remains accessible** (for testing purposes)

**Validation:**
- If `onboarding_state.is_complete == False`, reject with error: "Complete onboarding first before accessing regular chat."
- If `agent_type` is specified and not `AgentType.GENERAL`, reject with error: "Only general agent is available after onboarding completion."
- **Force `agent_type = AgentType.GENERAL`** regardless of input

#### 3.1.3 Access Control Matrix

| Agent Type | During Onboarding | Post-Onboarding | Notes |
|------------|-------------------|-----------------|-------|
| WORKOUT | ✅ Allowed | ❌ Blocked | Onboarding states 1-3 |
| DIET | ✅ Allowed | ❌ Blocked | Onboarding states 4-5 |
| SCHEDULER | ✅ Allowed | ❌ Blocked | Onboarding states 6-8 |
| SUPPLEMENT | ✅ Allowed | ❌ Blocked | Onboarding state 9 |
| GENERAL | ❌ Blocked | ✅ Allowed | Post-onboarding only |
| TRACKER | ❌ Blocked | ✅ Allowed* | *Via general agent |
| TEST | ✅ Allowed | ✅ Allowed | Testing only |

### 3.2 Enhanced Error Handling

**Requirement:** Provide clear, actionable error messages for all access control violations.

#### 3.2.1 Error Message Templates

**Onboarding Already Completed:**
```python
raise ValueError(
    "Onboarding already completed. "
    "Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. "
    f"User: {user_id}, Onboarding completed at: {onboarding_state.updated_at}"
)
```

**Onboarding Not Completed:**
```python
raise ValueError(
    "Complete onboarding first before accessing regular chat. "
    f"Current progress: {onboarding_state.current_step}/9 states completed. "
    f"Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. "
    f"User: {user_id}"
)
```

**General Agent During Onboarding:**
```python
raise ValueError(
    "General agent is not available during onboarding. "
    "Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. "
    f"Current state: {onboarding_state.current_step}/9. "
    f"User: {user_id}"
)
```

**Specialized Agent Post-Onboarding:**
```python
raise ValueError(
    f"Specialized agent '{agent_type.value}' is not available after onboarding completion. "
    "Only the general agent is accessible for post-onboarding interactions. "
    "The general agent can answer questions about workouts, meals, and schedules. "
    f"User: {user_id}"
)
```

**Missing Onboarding State:**
```python
raise ValueError(
    f"Onboarding state not found for user: {user_id}. "
    "User must complete registration and initialize onboarding first."
)
```

### 3.3 Enhanced Logging

**Requirement:** Add comprehensive logging for all agent routing decisions.

#### 3.3.1 Routing Decision Logging

**Log Entry Format:**
```python
logger.info(
    f"Agent routing: user={user_id}, "
    f"agent_type={agent_type.value}, "
    f"onboarding_mode={onboarding_mode}, "
    f"onboarding_complete={onboarding_state.is_complete}, "
    f"onboarding_step={onboarding_state.current_step}/9, "
    f"mode={self.mode}, "
    f"classification_used={agent_type_was_classified}"
)
```

#### 3.3.2 Access Control Violation Logging

**Log Entry Format:**
```python
logger.warning(
    f"Access control violation: user={user_id}, "
    f"requested_agent={agent_type.value if agent_type else 'None'}, "
    f"onboarding_mode={onboarding_mode}, "
    f"onboarding_complete={onboarding_state.is_complete}, "
    f"reason={violation_reason}"
)
```

#### 3.3.3 Performance Logging

**Log Entry Format:**
```python
logger.debug(
    f"Agent routing performance: user={user_id}, "
    f"classification_time_ms={classification_time_ms}, "
    f"agent_creation_time_ms={agent_creation_time_ms}, "
    f"total_routing_time_ms={total_routing_time_ms}"
)
```

### 3.4 Context Loading Refinement

**Requirement:** Ensure proper context loading based on onboarding status.

#### 3.4.1 During Onboarding

**Context Requirements:**
- Load partial user context (what's been collected so far)
- Include onboarding state and progress
- Include conversation history (onboarding-specific)
- **Do NOT** load full profile (not yet created)

**Implementation:**
```python
context = await load_agent_context(
    db=self.db_session,
    user_id=user_id,
    include_history=True,
    onboarding_mode=True  # NEW: Signals partial context loading
)
```

#### 3.4.2 Post-Onboarding

**Context Requirements:**
- Load full user profile
- Load all preferences (workout, diet, schedules)
- Load conversation history (all)
- Load tracking data and progress

**Implementation:**
```python
context = await load_agent_context(
    db=self.db_session,
    user_id=user_id,
    include_history=True,
    onboarding_mode=False  # Full context loading
)
```

### 3.5 Agent Classification Refinement

**Requirement:** Update classification logic to respect onboarding mode.

#### 3.5.1 Classification During Onboarding

**Rules:**
- Classification should ONLY return specialized agents (Workout, Diet, Scheduler, Supplement)
- If classifier returns "general", map to appropriate specialized agent based on context
- Never return TRACKER during onboarding

**Updated Classification Prompt:**
```python
if onboarding_mode:
    classification_prompt = """Classify this onboarding query into ONE category:
- workout: Fitness level, exercise plans, workout preferences, equipment, injuries
- diet: Dietary preferences, meal plans, nutrition, food restrictions, allergies
- scheduler: Meal timing, workout schedule, hydration reminders, timing preferences
- supplement: Supplement preferences and guidance

Respond with ONLY the category name."""
else:
    # Existing classification prompt for post-onboarding
    classification_prompt = """Classify this fitness query into ONE category:
- workout: Exercise plans, form, demonstrations, logging sets, workout routines, training
- diet: Meal plans, nutrition, recipes, food substitutions, calories, macros, eating
- supplement: Supplement guidance and information, vitamins, protein powder
- tracker: Progress tracking, adherence, metrics, weight tracking, measurements
- scheduler: Schedule changes, reminders, timing, rescheduling workouts or meals
- general: Motivation, casual conversation, general questions, greetings

Respond with ONLY the category name."""
```

#### 3.5.2 Classification Post-Onboarding

**Rules:**
- Classification can return any agent type
- **Always override to GENERAL** regardless of classification result
- Log the original classification for analytics

**Implementation:**
```python
if not onboarding_mode:
    # Classify for analytics, but always use general agent
    classified_type = await self._classify_query(query, onboarding_mode=False)
    logger.info(f"Query classified as {classified_type.value}, routing to general agent")
    agent_type = AgentType.GENERAL
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **Routing Decision:** < 10ms (excluding classification)
- **Classification:** < 500ms (with caching in voice mode)
- **Context Loading:** < 100ms
- **Total Routing Time:** < 2s (voice mode), < 3s (text mode)

### 4.2 Reliability

- **Access Control:** 100% enforcement (no bypasses)
- **Error Handling:** All exceptions caught and logged
- **Graceful Degradation:** Default to safe behavior on errors

### 4.3 Observability

- **Logging:** All routing decisions logged
- **Metrics:** Track routing time, classification accuracy, access violations
- **Tracing:** Include request_id in all log entries

### 4.4 Security

- **Access Control:** Strict enforcement of agent restrictions
- **Input Validation:** Validate all parameters
- **Error Messages:** Don't expose sensitive information

---

## 5. Testing Requirements

### 5.1 Unit Tests

- [ ] Test access control during onboarding (all scenarios)
- [ ] Test access control post-onboarding (all scenarios)
- [ ] Test error message generation
- [ ] Test classification with onboarding_mode flag
- [ ] Test context loading with onboarding_mode flag
- [ ] Test agent creation for all agent types
- [ ] Test caching behavior in voice mode

### 5.2 Integration Tests

- [ ] Test complete onboarding flow with agent routing
- [ ] Test post-onboarding flow with general agent
- [ ] Test access control violations end-to-end
- [ ] Test context loading with real database
- [ ] Test classification accuracy

### 5.3 Property-Based Tests

- [ ] **Property 1:** For any user with incomplete onboarding, specialized agents are accessible
- [ ] **Property 2:** For any user with complete onboarding, only general agent is accessible
- [ ] **Property 3:** For any access control violation, ValueError is raised with descriptive message
- [ ] **Property 4:** For any routing decision, logging includes all required fields

---

## 6. Migration Plan

### 6.1 Phase 1: Code Refinement (Week 1)

1. Update access control logic in `route_query()`
2. Add enhanced error messages
3. Add comprehensive logging
4. Update classification logic with onboarding_mode
5. Update context loading integration

### 6.2 Phase 2: Testing (Week 1)

1. Write unit tests for all scenarios
2. Write integration tests
3. Write property-based tests
4. Manual testing with various scenarios

### 6.3 Phase 3: Deployment (Week 2)

1. Deploy to staging
2. Integration testing with frontend
3. Performance testing
4. Deploy to production
5. Monitor metrics

---

## 7. Success Metrics

### 7.1 Correctness

- **Target:** 100% access control enforcement
- **Measure:** No unauthorized agent access in logs
- **Timeline:** Immediate

### 7.2 Performance

- **Target:** < 2s voice, < 3s text (95th percentile)
- **Measure:** Response time metrics
- **Timeline:** Within 7 days of deployment

### 7.3 User Experience

- **Target:** Clear error messages for all violations
- **Measure:** User feedback and support tickets
- **Timeline:** Within 30 days of deployment

---

## 8. Open Questions

1. **Q:** Should we allow TEST agent in production or only in development?
   **A:** TBD - Need DevOps input

2. **Q:** Should we add rate limiting per agent type?
   **A:** TBD - Need product input

3. **Q:** Should we track agent routing analytics in a separate table?
   **A:** TBD - Need analytics team input

---

## 9. Appendix

### 9.1 Current Implementation Status

Based on codebase analysis:
- ✅ `onboarding_mode` parameter exists
- ✅ Basic access control implemented
- ⚠️ Error messages need refinement
- ⚠️ Logging needs enhancement
- ⚠️ Classification needs onboarding_mode awareness
- ⚠️ Context loading needs onboarding_mode integration

### 9.2 Related Specifications

- `backend-onboarding-chat-integration` - Onboarding endpoints and flow
- `agent-function-tools` - Agent tool implementations
- `context-loader-service` - Context loading logic

---

**Document Status:** Ready for Design Phase  
**Next Steps:** Create design.md with technical implementation details

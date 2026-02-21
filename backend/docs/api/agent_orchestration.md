# Agent Orchestration API Documentation

## Overview

The Agent Orchestration system routes user queries to specialized AI agents based on the user's onboarding status and query content. This document describes the access control rules, error messages, and logging format for the orchestration system.

## Access Control Rules

### Agent Access Matrix

The system enforces strict access control based on whether the user is in onboarding mode or has completed onboarding:

| Agent Type | During Onboarding | Post-Onboarding | Notes |
|------------|-------------------|-----------------|-------|
| WORKOUT | ✅ Allowed | ❌ Blocked | Onboarding states 1-3 |
| DIET | ✅ Allowed | ❌ Blocked | Onboarding states 4-5 |
| SCHEDULER | ✅ Allowed | ❌ Blocked | Onboarding states 6-8 |
| SUPPLEMENT | ✅ Allowed | ❌ Blocked | Onboarding state 9 |
| GENERAL | ❌ Blocked | ✅ Allowed | Post-onboarding only |
| TRACKER | ❌ Blocked | ✅ Allowed* | *Via general agent |
| TEST | ✅ Allowed | ✅ Allowed | Testing only |

### During Onboarding (onboarding_mode=True)

**Allowed:**
- Specialized agents: WORKOUT, DIET, SCHEDULER, SUPPLEMENT
- TEST agent (for testing purposes)

**Blocked:**
- GENERAL agent - Not available until onboarding is complete
- TRACKER agent - Progress tracking begins after onboarding

**Validation Rules:**
1. If `onboarding_state.is_complete == True`, reject with error
2. If `agent_type == GENERAL`, reject with error
3. If `agent_type == TRACKER`, reject with error

### Post-Onboarding (onboarding_mode=False)

**Allowed:**
- GENERAL agent (forced for all queries)
- TRACKER agent (accessible via general agent delegation)
- TEST agent (for testing purposes)

**Blocked:**
- All specialized agents: WORKOUT, DIET, SCHEDULER, SUPPLEMENT

**Validation Rules:**
1. If `onboarding_state.is_complete == False`, reject with error
2. If `agent_type` is a specialized agent, reject with error
3. Force `agent_type = GENERAL` for all non-test queries

## Error Messages

All access control violations return a `ValueError` with a descriptive message that includes:
- Clear explanation of the violation
- Current user state (onboarding progress)
- Corrective action (which endpoint to use)
- User ID for debugging

### Error Message Templates

#### 1. Onboarding Already Completed

**Scenario:** User tries to access onboarding endpoint after completing onboarding

**Error Message:**
```
Onboarding already completed. Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. User: {user_id}, Onboarding completed at: {timestamp}
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "Onboarding already completed. Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. User: user-123, Onboarding completed at: 2026-02-13T10:30:00Z"
}
```

#### 2. Onboarding Not Completed

**Scenario:** User tries to access regular chat endpoint before completing onboarding

**Error Message:**
```
Complete onboarding first before accessing regular chat. Current progress: {current_step}/9 states completed. Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. User: {user_id}
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "Complete onboarding first before accessing regular chat. Current progress: 5/9 states completed. Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. User: user-123"
}
```

#### 3. General Agent During Onboarding

**Scenario:** User or system tries to use general agent during onboarding

**Error Message:**
```
General agent is not available during onboarding. Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. Current state: {current_step}/9. User: {user_id}
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "General agent is not available during onboarding. Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. Current state: 3/9. User: user-123"
}
```

#### 4. Specialized Agent Post-Onboarding

**Scenario:** User or system tries to use specialized agent after onboarding completion

**Error Message:**
```
Specialized agent '{agent_type}' is not available after onboarding completion. Only the general agent is accessible for post-onboarding interactions. The general agent can answer questions about workouts, meals, and schedules. User: {user_id}
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "Specialized agent 'workout' is not available after onboarding completion. Only the general agent is accessible for post-onboarding interactions. The general agent can answer questions about workouts, meals, and schedules. User: user-123"
}
```

#### 5. Tracker Agent During Onboarding

**Scenario:** User or system tries to use tracker agent during onboarding

**Error Message:**
```
Tracker agent is not available during onboarding. Progress tracking begins after onboarding completion. User: {user_id}
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "Tracker agent is not available during onboarding. Progress tracking begins after onboarding completion. User: user-123"
}
```

#### 6. Missing Onboarding State

**Scenario:** User has no onboarding state record in database

**Error Message:**
```
Onboarding state not found for user: {user_id}. User must complete registration and initialize onboarding first.
```

**HTTP Status:** 400 Bad Request

**Example:**
```json
{
  "detail": "Onboarding state not found for user: user-123. User must complete registration and initialize onboarding first."
}
```

## Logging Format

### Routing Decision Log

**Log Level:** INFO

**Format:**
```
Agent routing: user={user_id}, agent_type={agent_type}, onboarding_mode={onboarding_mode}, onboarding_complete={is_complete}, onboarding_step={current_step}/9, mode={mode}, classification_used={classification_used}, routing_time_ms={routing_time_ms}
```

**Fields:**
- `user`: User's unique identifier
- `agent_type`: Selected agent type (workout, diet, general, etc.)
- `onboarding_mode`: Boolean indicating if this is an onboarding interaction
- `onboarding_complete`: Boolean indicating if user completed onboarding
- `onboarding_step`: Current onboarding step (1-9) or 'N/A'
- `mode`: Interaction mode (text or voice)
- `classification_used`: Boolean indicating if query classification was used
- `routing_time_ms`: Total routing time in milliseconds

**Example:**
```
INFO: Agent routing: user=user-123, agent_type=workout, onboarding_mode=True, onboarding_complete=False, onboarding_step=2/9, mode=voice, classification_used=True, routing_time_ms=45
```

### Access Control Violation Log

**Log Level:** WARNING

**Format:**
```
Access control violation: user={user_id}, requested_agent={agent_type}, onboarding_mode={onboarding_mode}, onboarding_complete={is_complete}, reason={violation_reason}
```

**Fields:**
- `user`: User's unique identifier
- `requested_agent`: Agent type that was requested (or 'None')
- `onboarding_mode`: Boolean indicating if this is an onboarding interaction
- `onboarding_complete`: Boolean indicating if user completed onboarding
- `reason`: Short description of the violation

**Example:**
```
WARNING: Access control violation: user=user-123, requested_agent=general, onboarding_mode=True, onboarding_complete=False, reason=general_agent_during_onboarding
```

### Performance Metrics Log

**Log Level:** DEBUG

**Format:**
```
Performance metrics: classification={classification_time_ms}ms, agent_creation={agent_creation_time_ms}ms, total_routing={total_routing_time_ms}ms
```

**Fields:**
- `classification`: Time spent on query classification in milliseconds
- `agent_creation`: Time spent creating/retrieving agent in milliseconds
- `total_routing`: Total routing time in milliseconds

**Example:**
```
DEBUG: Performance metrics: classification=120ms, agent_creation=15ms, total_routing=145ms
```

### Access Control Pass Log

**Log Level:** DEBUG

**Format:**
```
Access control passed: user={user_id}, agent_type={agent_type}, onboarding_mode={onboarding_mode}, onboarding_step={current_step}/9
```

**Example:**
```
DEBUG: Access control passed: user=user-123, agent_type=workout, onboarding_mode=True, onboarding_step=2/9
```

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Access Control Check | < 5ms | P95 latency |
| Classification | < 500ms | P95 latency (with caching) |
| Logging | < 1ms | P95 latency |
| Total Routing (Voice) | < 2s | P95 latency |
| Total Routing (Text) | < 3s | P95 latency |

## Usage Examples

### Example 1: Onboarding Query (Voice Mode)

**Request:**
```python
orchestrator = AgentOrchestrator(db_session, mode="voice")
response = await orchestrator.route_query(
    user_id="user-123",
    query="I can do 10 pushups",
    voice_mode=True,
    onboarding_mode=True
)
```

**Logs Generated:**
```
DEBUG: Access control passed: user=user-123, agent_type=workout, onboarding_mode=True, onboarding_step=2/9
DEBUG: Classification time: 120ms
DEBUG: Agent creation time: 15ms
DEBUG: Performance metrics: classification=120ms, agent_creation=15ms, total_routing=145ms
INFO: Agent routing: user=user-123, agent_type=workout, onboarding_mode=True, onboarding_complete=False, onboarding_step=2/9, mode=voice, classification_used=True, routing_time_ms=145
```

### Example 2: Post-Onboarding Query (Text Mode)

**Request:**
```python
orchestrator = AgentOrchestrator(db_session, mode="text")
response = await orchestrator.route_query(
    user_id="user-456",
    query="What should I eat today?",
    voice_mode=False,
    onboarding_mode=False
)
```

**Logs Generated:**
```
DEBUG: Access control passed: user=user-456, agent_type=general, onboarding_mode=False, onboarding_complete=True
INFO: Query classified as diet, forcing to general agent (post-onboarding)
DEBUG: Classification time: 180ms
DEBUG: Agent creation time: 20ms
DEBUG: Performance metrics: classification=180ms, agent_creation=20ms, total_routing=210ms
INFO: Agent routing: user=user-456, agent_type=general, onboarding_mode=False, onboarding_complete=True, onboarding_step=9/9, mode=text, classification_used=True, routing_time_ms=210
```

### Example 3: Access Control Violation

**Request:**
```python
orchestrator = AgentOrchestrator(db_session, mode="text")
response = await orchestrator.route_query(
    user_id="user-789",
    query="Hello",
    agent_type=AgentType.GENERAL,
    voice_mode=False,
    onboarding_mode=True  # User is in onboarding but requesting general agent
)
```

**Logs Generated:**
```
WARNING: Access control violation: user=user-789, reason=general_agent_during_onboarding, current_step=3/9
```

**Error Raised:**
```python
ValueError: General agent is not available during onboarding. Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. Current state: 3/9. User: user-789
```

## Integration Notes

### For Frontend Developers

1. **Endpoint Selection:**
   - Use `/api/v1/chat/onboarding` during onboarding
   - Use `/api/v1/chat` after onboarding completion
   - Check `onboarding_state.is_complete` to determine which endpoint to use

2. **Error Handling:**
   - All access control errors return 400 Bad Request
   - Error messages include corrective actions
   - Display error messages to users to guide them to correct endpoint

3. **Agent Type:**
   - Do NOT specify `agent_type` in requests - let the system classify
   - System automatically routes to appropriate agent based on context

### For Backend Developers

1. **Access Control:**
   - Always call `_enforce_access_control()` before routing
   - Never bypass access control checks
   - Access control is enforced at orchestrator level, not endpoint level

2. **Logging:**
   - All routing decisions are automatically logged
   - Use structured logging with consistent field names
   - Include performance metrics for monitoring

3. **Testing:**
   - Test all access control scenarios
   - Verify error messages include required context
   - Check that logs include all required fields

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Access Violations:**
   - Track count and rate of access control violations
   - Alert if rate exceeds 10/minute (indicates potential issue)

2. **Performance:**
   - Monitor P95 routing time
   - Alert if voice mode exceeds 2s or text mode exceeds 3s

3. **Classification Accuracy:**
   - Track classification results vs expected agent types
   - Monitor default fallback rate (should be < 5%)

### Recommended Alerts

**Critical:**
- Access violation rate > 10/minute
- Routing time P95 > 3s
- Error rate > 1%

**Warning:**
- Access violation rate > 5/minute
- Routing time P95 > 2s
- Classification failures > 5%

## Version History

- **v1.0** (2026-02-14): Initial documentation for agent orchestration refinement
  - Added strict access control enforcement
  - Enhanced error messages with context
  - Comprehensive logging for debugging and analytics

# Agent Orchestration Refinement - Migration Guide

## Overview

This guide documents the changes introduced in the Agent Orchestration Refinement update and provides migration instructions for developers working with the system.

**Version:** 1.0  
**Release Date:** 2026-02-14  
**Impact:** Medium - Enhanced access control and error handling

## Summary of Changes

### What Changed

1. **Enhanced Access Control:** Strict enforcement of agent access based on onboarding status
2. **Improved Error Messages:** Detailed error messages with context and corrective actions
3. **Comprehensive Logging:** All routing decisions logged with performance metrics
4. **Classification Refinement:** Onboarding-aware query classification
5. **Forced General Agent:** Post-onboarding queries always use general agent

### What Stayed the Same

- Agent interface and API contracts
- Database schema (no migrations required)
- Endpoint URLs and request/response formats
- Agent implementations (no changes to individual agents)
- Voice and text mode behavior

## Breaking Changes

### ⚠️ None

This update is **fully backward compatible**. No breaking changes were introduced.

## New Behavior

### 1. Strict Access Control Enforcement

**Previous Behavior:**
- Basic access control with minimal validation
- Some edge cases not properly handled
- Inconsistent error messages

**New Behavior:**
- Strict enforcement of agent access rules
- All edge cases handled with clear error messages
- Consistent validation across all scenarios

**Impact:** Low - Existing valid requests continue to work. Invalid requests now get better error messages.

**Example:**

```python
# Before: Unclear error
orchestrator.route_query(
    user_id="user-123",
    query="Hello",
    agent_type=AgentType.GENERAL,
    onboarding_mode=True  # User in onboarding
)
# Raised: Generic ValueError

# After: Clear error with guidance
orchestrator.route_query(
    user_id="user-123",
    query="Hello",
    agent_type=AgentType.GENERAL,
    onboarding_mode=True
)
# Raises: ValueError with message:
# "General agent is not available during onboarding. 
#  Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. 
#  Current state: 3/9. User: user-123"
```

### 2. Enhanced Error Messages

**Previous Behavior:**
- Minimal error context
- No corrective actions suggested
- Limited debugging information

**New Behavior:**
- Detailed error context (user state, progress)
- Clear corrective actions (which endpoint to use)
- User ID included for debugging

**Impact:** Low - Better developer and user experience

**Migration Action:** None required - errors are more helpful automatically

### 3. Comprehensive Logging

**Previous Behavior:**
- Basic logging of agent selection
- Limited context in logs
- No performance metrics

**New Behavior:**
- All routing decisions logged with full context
- Access violations logged as warnings
- Performance metrics included (routing time)

**Impact:** Low - Better observability and debugging

**Migration Action:** Update monitoring dashboards to use new log fields

**New Log Fields:**
- `onboarding_mode`: Boolean indicating onboarding status
- `onboarding_complete`: Boolean indicating completion
- `onboarding_step`: Current step (1-9)
- `classification_used`: Boolean indicating if classification was used
- `routing_time_ms`: Total routing time in milliseconds

### 4. Classification Awareness

**Previous Behavior:**
- Single classification prompt for all queries
- No awareness of onboarding context

**New Behavior:**
- Different classification prompts for onboarding vs post-onboarding
- Onboarding prompt only returns specialized agents
- Post-onboarding prompt returns any agent (but forced to general)

**Impact:** Low - Better classification accuracy

**Migration Action:** None required - classification is internal

### 5. Forced General Agent Post-Onboarding

**Previous Behavior:**
- Classification result used directly
- Specialized agents could be selected post-onboarding

**New Behavior:**
- All post-onboarding queries forced to general agent
- Classification result logged but overridden
- Only TEST agent exempt from forcing

**Impact:** Low - Aligns with product requirements

**Migration Action:** None required - behavior is automatic

## Migration Steps

### For Backend Developers

#### Step 1: Update Monitoring (Optional)

If you have monitoring dashboards for agent orchestration:

1. Add new log fields to your queries:
   - `onboarding_mode`
   - `onboarding_complete`
   - `onboarding_step`
   - `classification_used`
   - `routing_time_ms`

2. Create alerts for access violations:
   ```
   WARNING: Access control violation: user=*, reason=*
   ```

3. Monitor performance metrics:
   ```
   DEBUG: Performance metrics: classification=*ms, agent_creation=*ms, total_routing=*ms
   ```

#### Step 2: Update Tests (If Needed)

If you have tests that explicitly check error messages:

**Before:**
```python
with pytest.raises(ValueError):
    await orchestrator.route_query(...)
```

**After:**
```python
with pytest.raises(ValueError, match="General agent is not available during onboarding"):
    await orchestrator.route_query(...)
```

#### Step 3: Review Error Handling

If you catch and handle orchestrator errors:

**Before:**
```python
try:
    response = await orchestrator.route_query(...)
except ValueError as e:
    logger.error(f"Routing failed: {e}")
    return {"error": "Invalid request"}
```

**After (Optional Enhancement):**
```python
try:
    response = await orchestrator.route_query(...)
except ValueError as e:
    logger.error(f"Routing failed: {e}")
    # New error messages include corrective actions
    # You can now parse and display them to users
    return {"error": str(e)}  # More helpful to users
```

### For Frontend Developers

#### No Changes Required

The API contract remains unchanged:
- Same endpoints
- Same request/response formats
- Same status codes

**Optional Enhancement:**

Display error messages to users - they now include helpful guidance:

```javascript
// Before
catch (error) {
  showError("Something went wrong");
}

// After (Optional)
catch (error) {
  // Error messages now include corrective actions
  showError(error.detail);  // e.g., "Complete onboarding first..."
}
```

### For DevOps/SRE

#### Step 1: Update Monitoring Dashboards

Add metrics for:
1. Access control violations (count and rate)
2. Routing performance (P95 latency)
3. Classification accuracy

#### Step 2: Configure Alerts

**Critical Alerts:**
- Access violation rate > 10/minute
- Routing time P95 > 3s
- Error rate > 1%

**Warning Alerts:**
- Access violation rate > 5/minute
- Routing time P95 > 2s
- Classification failures > 5%

#### Step 3: Update Runbooks

Add troubleshooting steps for new error messages:
- "Onboarding already completed" → Check endpoint routing
- "Complete onboarding first" → Verify onboarding state
- "General agent not available during onboarding" → Check onboarding_mode flag

## Testing the Migration

### Verification Checklist

- [ ] Onboarding queries route to specialized agents
- [ ] Post-onboarding queries route to general agent
- [ ] Access violations return clear error messages
- [ ] All routing decisions are logged
- [ ] Performance metrics are within targets
- [ ] Monitoring dashboards show new metrics
- [ ] Alerts are configured and tested

### Test Scenarios

#### Scenario 1: Onboarding Flow

```python
# User in onboarding (step 2)
orchestrator = AgentOrchestrator(db_session, mode="voice")
response = await orchestrator.route_query(
    user_id="test-user",
    query="I can do 10 pushups",
    voice_mode=True,
    onboarding_mode=True
)

# Expected: Routes to WORKOUT agent
# Expected: Logs include onboarding_mode=True, onboarding_step=2/9
assert response.agent_type == "workout"
```

#### Scenario 2: Post-Onboarding Flow

```python
# User completed onboarding
orchestrator = AgentOrchestrator(db_session, mode="text")
response = await orchestrator.route_query(
    user_id="test-user",
    query="What should I eat today?",
    voice_mode=False,
    onboarding_mode=False
)

# Expected: Routes to GENERAL agent (forced)
# Expected: Logs show classification=diet but agent_type=general
assert response.agent_type == "general"
```

#### Scenario 3: Access Violation

```python
# User in onboarding tries to use general agent
orchestrator = AgentOrchestrator(db_session, mode="text")

with pytest.raises(ValueError, match="General agent is not available during onboarding"):
    await orchestrator.route_query(
        user_id="test-user",
        query="Hello",
        agent_type=AgentType.GENERAL,
        onboarding_mode=True
    )

# Expected: ValueError with detailed message
# Expected: WARNING log for access violation
```

## Rollback Plan

### If Issues Are Detected

1. **Identify the Issue:**
   - Check error logs for unexpected errors
   - Review monitoring dashboards for anomalies
   - Verify access control violations are legitimate

2. **Rollback Steps:**
   ```bash
   # Revert to previous version
   git revert <commit-hash>
   
   # Rebuild and deploy
   docker-compose build api
   docker-compose up -d api
   ```

3. **Verify Rollback:**
   - Test onboarding flow
   - Test post-onboarding flow
   - Check error rates return to normal

### Rollback Triggers

- Error rate > 1%
- Performance degradation > 20%
- Access control bypass detected
- Critical functionality broken

## FAQ

### Q: Do I need to update my code?

**A:** No, the changes are backward compatible. Your existing code will continue to work.

### Q: Will error messages change?

**A:** Yes, error messages are now more detailed and helpful. If you parse error messages, you may want to update your parsing logic.

### Q: Do I need to run database migrations?

**A:** No, there are no database schema changes.

### Q: Will this affect performance?

**A:** No, performance targets remain the same (<2s voice, <3s text). The new access control checks add <5ms overhead.

### Q: What if I'm using custom agents?

**A:** Custom agents are not affected. The orchestrator changes only affect routing logic, not agent implementations.

### Q: How do I test the new behavior?

**A:** Use the test scenarios in this guide. All existing tests should pass without modification.

### Q: What if I find a bug?

**A:** Report it immediately with:
- User ID
- Query text
- Onboarding mode
- Error message
- Log entries

## Support

### Documentation

- [API Documentation](../api/agent_orchestration.md)
- [Requirements Document](../../.kiro/specs/agent-orchestration-refinement/requirements.md)
- [Design Document](../../.kiro/specs/agent-orchestration-refinement/design.md)

### Contact

- **Backend Team:** For implementation questions
- **DevOps Team:** For deployment and monitoring
- **Product Team:** For behavior and requirements questions

## Version History

- **v1.0** (2026-02-14): Initial migration guide
  - Documented all changes
  - Provided migration steps
  - Added test scenarios
  - Included rollback plan

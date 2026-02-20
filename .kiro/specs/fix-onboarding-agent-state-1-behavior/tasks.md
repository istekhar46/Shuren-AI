# Implementation Tasks: Fix Onboarding Agent State 1 Behavior

## Overview
Implement TRD-compliant onboarding agent routing by removing legacy `STATE_TO_AGENT_MAP` and ensuring all endpoints use `OnboardingAgentOrchestrator`.

## Task List

### 1. Remove Legacy Routing Code
- [x] 1.1 Delete STATE_TO_AGENT_MAP from onboarding_service.py
- [x] 1.2 Update STATE_METADATA agent fields to match TRD
- [x] 1.3 Delete test_state_agent_mapping_properties.py

### 2. Update Chat Endpoints
- [x] 2.1 Refactor /api/v1/chat/onboarding endpoint
  - [x] 2.1.1 Remove STATE_TO_AGENT_MAP import and usage
  - [x] 2.1.2 Add OnboardingAgentOrchestrator import
  - [x] 2.1.3 Replace AgentOrchestrator with OnboardingAgentOrchestrator
  - [x] 2.1.4 Update response to use correct agent_type
- [x] 2.2 Refactor /api/v1/chat/onboarding-stream endpoint
  - [x] 2.2.1 Remove STATE_TO_AGENT_MAP import and usage
  - [x] 2.2.2 Add OnboardingAgentOrchestrator import
  - [x] 2.2.3 Replace AgentOrchestrator with OnboardingAgentOrchestrator
  - [x] 2.2.4 Update streaming response to use correct agent_type

### 3. Clean Up AgentOrchestrator
- [x] 3.1 Remove onboarding_mode parameter from route_query()
- [x] 3.2 Remove onboarding-specific access control logic
- [x] 3.3 Remove onboarding-specific classification logic
- [x] 3.4 Add validation to reject non-completed onboarding users
- [x] 3.5 Update docstrings to clarify post-onboarding only

### 4. Update Tests
- [x] 4.1 Update test_onboarding_chat_endpoint.py assertions
  - [x] 4.1.1 Update expected agent_type values
  - [x] 4.1.2 Verify state 1 returns "fitness_assessment"
- [x] 4.2 Update test_integration_onboarding_flow.py
  - [x] 4.2.1 Verify all states route to correct agents
  - [x] 4.2.2 Update streaming endpoint tests
- [x] 4.3 Run full test suite and fix any failures

### 5. Verification
- [x] 5.1 Manual test state 1 with streaming endpoint
- [x] 5.2 Verify event stream returns correct agent_type
- [x] 5.3 Verify no STATE_TO_AGENT_MAP references remain
- [x] 5.4 Run diagnostics on modified files

## Task Details

### Task 1.1: Delete STATE_TO_AGENT_MAP from onboarding_service.py

**File**: `backend/app/services/onboarding_service.py`

**Action**: Delete lines 107-119 (STATE_TO_AGENT_MAP dictionary and comment)

**Validation**: Search codebase for `STATE_TO_AGENT_MAP` - should return zero results

---

### Task 1.2: Update STATE_METADATA agent fields to match TRD

**File**: `backend/app/services/onboarding_service.py`

**Changes**: Update the `agent` field in each StateInfo to match TRD specification:
- State 1: `agent="fitness_assessment"`
- State 2: `agent="fitness_assessment"`
- State 3: `agent="goal_setting"`
- State 4: `agent="workout_planning"`
- State 5: `agent="workout_planning"`
- State 6: `agent="diet_planning"`
- State 7: `agent="diet_planning"`
- State 8: `agent="scheduling"`
- State 9: `agent="scheduling"`

**Validation**: Verify agent fields match OnboardingAgentType enum values

---

### Task 1.3: Delete test_state_agent_mapping_properties.py

**File**: `backend/tests/test_state_agent_mapping_properties.py`

**Action**: Delete entire file

**Rationale**: Tests legacy STATE_TO_AGENT_MAP which is being removed

**Validation**: File should not exist after deletion

---

### Task 2.1: Refactor /api/v1/chat/onboarding endpoint

**File**: `backend/app/api/v1/endpoints/chat.py`

**Function**: `chat_onboarding()` (approximately lines 215-360)

**Changes**:

1. **Remove imports**:
   ```python
   # Remove this line
   from app.services.onboarding_service import STATE_TO_AGENT_MAP
   ```

2. **Add imports**:
   ```python
   from app.services.onboarding_orchestrator import OnboardingAgentOrchestrator
   ```

3. **Replace routing logic**:
   ```python
   # OLD (remove):
   agent_type = STATE_TO_AGENT_MAP.get(request.current_state)
   orchestrator = AgentOrchestrator(db_session=db, mode="text")
   agent_response = await orchestrator.route_query(
       user_id=user_id,
       query=request.message,
       agent_type=agent_type,
       voice_mode=False,
       onboarding_mode=True
   )
   
   # NEW (replace with):
   orchestrator = OnboardingAgentOrchestrator(db)
   try:
       agent = await orchestrator.get_current_agent(current_user.id)
   except ValueError as e:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail=str(e)
       )
   
   try:
       agent_response = await agent.process_message(
           message=request.message,
           user_id=current_user.id
       )
   except Exception as e:
       logger.error(f"Agent processing failed: {e}", exc_info=True)
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="Failed to process message"
       )
   ```

4. **Update response**:
   ```python
   return OnboardingChatResponse(
       response=agent_response.message,
       agent_type=agent_response.agent_type,  # Now returns "fitness_assessment", etc.
       state_updated=state_updated,
       new_state=updated_state.current_step if state_updated else None,
       progress={...}
   )
   ```

**Validation**: 
- Endpoint returns 200 for valid requests
- agent_type field matches OnboardingAgentType values
- State 1 returns "fitness_assessment"

---

### Task 2.2: Refactor /api/v1/chat/onboarding-stream endpoint

**File**: `backend/app/api/v1/endpoints/chat.py`

**Function**: `chat_onboarding_stream()` (approximately lines 430-720)

**Changes**:

1. **Remove imports** (same as Task 2.1)

2. **Add imports** (same as Task 2.1)

3. **Replace routing logic in generate() function**:
   ```python
   # OLD (remove):
   agent_type = STATE_TO_AGENT_MAP.get(state.current_step)
   orchestrator = AgentOrchestrator(db_session=db, mode="text")
   agent = orchestrator._get_or_create_agent(agent_type, context)
   
   # NEW (replace with):
   orchestrator = OnboardingAgentOrchestrator(db)
   try:
       agent = await orchestrator.get_current_agent(current_user.id)
   except ValueError as e:
       error_msg = str(e)
       logger.error(f"Failed to get onboarding agent: {error_msg}")
       yield f"data: {json.dumps({'error': error_msg})}\n\n"
       return
   
   agent_type_value = agent.agent_type  # Get correct agent type
   ```

4. **Update final SSE event**:
   ```python
   yield f"data: {json.dumps({
       'done': True,
       'agent_type': agent_type_value,  # Use agent.agent_type, not STATE_TO_AGENT_MAP
       'state_updated': state_updated,
       'new_state': updated_state.current_step if state_updated else None,
       'progress': {...}
   })}\n\n"
   ```

**Validation**:
- Streaming endpoint returns SSE events
- Final event contains correct agent_type
- State 1 returns "fitness_assessment" in agent_type field

---

### Task 3.1-3.5: Clean Up AgentOrchestrator

**File**: `backend/app/services/agent_orchestrator.py`

**Changes**:

1. **Remove onboarding_mode parameter** from:
   - `route_query()` method signature
   - All method calls that pass `onboarding_mode`

2. **Remove onboarding-specific logic**:
   - Access control checks for onboarding mode
   - Classification prompts for onboarding
   - Any conditional logic based on `onboarding_mode`

3. **Add validation** at start of `route_query()`:
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
       
       # ... rest of method
   ```

4. **Update docstrings** to clarify post-onboarding only usage

**Validation**:
- No references to `onboarding_mode` in AgentOrchestrator
- Method raises ValueError for non-completed onboarding users
- All tests pass

---

### Task 4.1: Update test_onboarding_chat_endpoint.py assertions

**File**: `backend/tests/test_onboarding_chat_endpoint.py`

**Changes**:

1. **Update expected agent_type values**:
   ```python
   # OLD:
   assert response.json()["agent_type"] == "workout"
   
   # NEW:
   assert response.json()["agent_type"] == "fitness_assessment"
   ```

2. **Add test for state 1 specifically**:
   ```python
   async def test_state_1_routes_to_fitness_assessment(
       authenticated_client,
       db_session
   ):
       """Verify state 1 routes to FitnessAssessmentAgent"""
       client, user = authenticated_client
       
       # Set user to state 1
       state = await onboarding_service.get_onboarding_state(user.id)
       state.current_step = 1
       await db_session.commit()
       
       # Send message
       response = await client.post(
           "/api/v1/chat/onboarding",
           json={"message": "I'm a beginner", "current_state": 1}
       )
       
       assert response.status_code == 200
       data = response.json()
       assert data["agent_type"] == "fitness_assessment"
       assert "workout" not in data["response"].lower()
   ```

**Validation**: All tests pass with updated assertions

---

### Task 4.2: Update test_integration_onboarding_flow.py

**File**: `backend/tests/test_integration_onboarding_flow.py`

**Changes**:

1. **Update agent_type assertions for all states**:
   - States 1-2: `assert agent_type == "fitness_assessment"`
   - State 3: `assert agent_type == "goal_setting"`
   - States 4-5: `assert agent_type == "workout_planning"`
   - States 6-7: `assert agent_type == "diet_planning"`
   - States 8-9: `assert agent_type == "scheduling"`

2. **Add streaming endpoint test**:
   ```python
   async def test_streaming_endpoint_correct_agent_types(
       authenticated_client,
       db_session
   ):
       """Verify streaming endpoint returns correct agent types"""
       client, user = authenticated_client
       
       for state_num in range(1, 10):
           # Set state
           state = await onboarding_service.get_onboarding_state(user.id)
           state.current_step = state_num
           await db_session.commit()
           
           # Stream message
           response = await client.post(
               "/api/v1/chat/onboarding-stream",
               json={"message": "test", "current_state": state_num}
           )
           
           # Parse SSE events
           events = parse_sse_events(response.content)
           final_event = events[-1]
           
           # Verify correct agent_type
           expected_agent = get_expected_agent_for_state(state_num)
           assert final_event["agent_type"] == expected_agent
   ```

**Validation**: All integration tests pass

---

### Task 4.3: Run full test suite and fix any failures

**Commands**:
```bash
poetry run pytest backend/tests/ -v
poetry run pytest backend/tests/test_onboarding_orchestrator.py -v
poetry run pytest backend/tests/test_onboarding_chat_endpoint.py -v
poetry run pytest backend/tests/test_integration_onboarding_flow.py -v
```

**Action**: Fix any test failures that arise from the changes

**Validation**: All tests pass with 0 failures

---

### Task 5.1-5.4: Verification

**Manual Testing**:
1. Start development server
2. Create test user and start onboarding
3. Send message to `/api/v1/chat/onboarding-stream` at state 1
4. Verify response contains `agent_type: "fitness_assessment"`
5. Verify agent asks fitness assessment questions

**Code Search**:
```bash
# Should return 0 results
grep -r "STATE_TO_AGENT_MAP" backend/app/
grep -r "onboarding_mode=True" backend/app/
```

**Diagnostics**:
Run getDiagnostics on all modified files to check for errors

**Validation**: 
- Manual test successful
- No legacy code references found
- No diagnostic errors

## Completion Criteria

- [ ] All tasks marked as complete
- [ ] All tests passing
- [ ] No STATE_TO_AGENT_MAP references in codebase
- [ ] State 1 returns "fitness_assessment" agent_type
- [ ] All 9 states route to correct specialized agents
- [ ] No diagnostic errors in modified files
- [ ] Manual testing confirms correct behavior

## Notes

- The OnboardingAgentOrchestrator and specialized agents already exist and are tested
- This is primarily a refactoring task to remove legacy code
- No new functionality is being added
- Focus on clean removal of old code and consistent use of TRD architecture

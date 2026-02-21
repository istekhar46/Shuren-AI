# Agent Orchestration Refinement - Design Document

**Feature Name:** agent-orchestration-refinement  
**Status:** Draft  
**Created:** 2026-02-14  
**Last Updated:** 2026-02-14

---

## 1. Overview

This design document specifies the technical implementation for refining the Agent Orchestration system to fully align with the refined product requirements. The implementation focuses on enhancing access control, error handling, logging, and classification logic.

### 1.1 Design Goals

- Enhance agent access control to strictly enforce product requirements
- Improve error messages for better developer and user experience
- Add comprehensive logging for debugging and analytics
- Refine classification logic to respect onboarding mode
- Maintain backward compatibility with existing functionality
- Ensure performance targets are met

### 1.2 Key Design Decisions

**Decision 1: Strict Access Control Enforcement**
- **Choice:** Enforce access control at orchestrator level, not endpoint level
- **Rationale:** Single source of truth, easier to test, consistent across voice/text
- **Trade-off:** Orchestrator becomes more complex vs distributed validation

**Decision 2: Enhanced Error Messages**
- **Choice:** Include context and corrective actions in all error messages
- **Rationale:** Better developer experience, faster debugging, clearer user feedback
- **Trade-off:** Slightly larger error responses vs minimal messages

**Decision 3: Classification Awareness**
- **Choice:** Pass `onboarding_mode` to classification method
- **Rationale:** Different classification prompts for different contexts
- **Trade-off:** Additional parameter vs implicit mode detection

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  route_query(user_id, query, agent_type,             │  │
│  │              voice_mode, onboarding_mode)             │  │
│  │                                                        │  │
│  │  1. Load User & OnboardingState                      │  │
│  │  2. Enforce Access Control ← ENHANCED                │  │
│  │  3. Classify Query (if needed) ← ENHANCED            │  │
│  │  4. Get/Create Agent                                 │  │
│  │  5. Process Query                                    │  │
│  │  6. Return Response                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  _enforce_access_control() ← NEW METHOD              │  │
│  │  - Validates onboarding status                       │  │
│  │  - Validates agent type permissions                  │  │
│  │  - Raises ValueError with detailed messages          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  _classify_query(query, onboarding_mode) ← ENHANCED  │  │
│  │  - Uses different prompts based on mode              │  │
│  │  - Returns appropriate agent types                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  _log_routing_decision() ← NEW METHOD                │  │
│  │  - Logs all routing decisions                        │  │
│  │  - Includes performance metrics                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Access Control Flow

```
route_query() called
      ↓
Load User & OnboardingState
      ↓
_enforce_access_control()
      ↓
┌─────────────────────────────────────┐
│ Is onboarding_mode=True?            │
└─────────────┬───────────────────────┘
              │
      ┌───────┴───────┐
      │               │
     YES             NO
      │               │
      ↓               ↓
Is onboarding     Is onboarding
complete?         complete?
      │               │
     YES             NO
      │               │
      ↓               ↓
  REJECT          REJECT
  "Already        "Complete
  completed"      onboarding
                  first"
      │               │
     NO              YES
      │               │
      ↓               ↓
Is agent_type     Force agent_type
specialized?      = GENERAL
      │               │
     YES             │
      │               │
      ↓               ↓
   ALLOW          ALLOW
```

---

## 3. Implementation Details

### 3.1 Enhanced Access Control Method

**New Method:** `_enforce_access_control()`

**Location:** `backend/app/services/agent_orchestrator.py`

**Implementation:**

```python
def _enforce_access_control(
    self,
    user: User,
    onboarding_state: Optional[OnboardingState],
    agent_type: Optional[AgentType],
    onboarding_mode: bool
) -> None:
    """
    Enforce strict agent access control based on onboarding status.
    
    This method implements the core access control logic that ensures:
    - Specialized agents are ONLY accessible during onboarding
    - General agent is ONLY accessible post-onboarding
    - Proper error messages guide users to correct endpoints
    
    Args:
        user: User model instance
        onboarding_state: OnboardingState model instance (can be None)
        agent_type: Requested agent type (can be None if classification needed)
        onboarding_mode: Whether this is an onboarding interaction
    
    Raises:
        ValueError: If access control rules are violated
    
    Access Control Matrix:
        During Onboarding (onboarding_mode=True):
            - Specialized agents (WORKOUT, DIET, SCHEDULER, SUPPLEMENT): ✅ Allowed
            - General agent: ❌ Blocked
            - Tracker agent: ❌ Blocked
            - Test agent: ✅ Allowed (testing only)
        
        Post-Onboarding (onboarding_mode=False):
            - Specialized agents: ❌ Blocked
            - General agent: ✅ Allowed (forced)
            - Tracker agent: ✅ Allowed (via general agent)
            - Test agent: ✅ Allowed (testing only)
    """
    user_id = str(user.id)
    
    # Check if onboarding state exists
    if not onboarding_state:
        logger.error(f"Onboarding state not found for user: {user_id}")
        raise ValueError(
            f"Onboarding state not found for user: {user_id}. "
            "User must complete registration and initialize onboarding first."
        )
    
    # Define specialized agents (onboarding-only)
    specialized_agents = {
        AgentType.WORKOUT,
        AgentType.DIET,
        AgentType.SCHEDULER,
        AgentType.SUPPLEMENT
    }
    
    # CASE 1: During Onboarding (onboarding_mode=True)
    if onboarding_mode:
        # Reject if onboarding already completed
        if onboarding_state.is_complete:
            logger.warning(
                f"Access control violation: user={user_id}, "
                f"reason=onboarding_already_completed, "
                f"completed_at={onboarding_state.updated_at}"
            )
            raise ValueError(
                "Onboarding already completed. "
                "Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. "
                f"User: {user_id}, Onboarding completed at: {onboarding_state.updated_at}"
            )
        
        # Reject if general agent requested during onboarding
        if agent_type == AgentType.GENERAL:
            logger.warning(
                f"Access control violation: user={user_id}, "
                f"reason=general_agent_during_onboarding, "
                f"current_step={onboarding_state.current_step}/9"
            )
            raise ValueError(
                "General agent is not available during onboarding. "
                "Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. "
                f"Current state: {onboarding_state.current_step}/9. "
                f"User: {user_id}"
            )
        
        # Reject if tracker agent requested during onboarding
        if agent_type == AgentType.TRACKER:
            logger.warning(
                f"Access control violation: user={user_id}, "
                f"reason=tracker_agent_during_onboarding"
            )
            raise ValueError(
                "Tracker agent is not available during onboarding. "
                "Progress tracking begins after onboarding completion. "
                f"User: {user_id}"
            )
        
        # Allow specialized agents and test agent
        # (agent_type will be validated later in _create_agent)
        logger.debug(
            f"Access control passed: user={user_id}, "
            f"agent_type={agent_type.value if agent_type else 'to_be_classified'}, "
            f"onboarding_mode=True, "
            f"onboarding_step={onboarding_state.current_step}/9"
        )
    
    # CASE 2: Post-Onboarding (onboarding_mode=False)
    else:
        # Reject if onboarding not completed
        if not onboarding_state.is_complete:
            logger.warning(
                f"Access control violation: user={user_id}, "
                f"reason=onboarding_not_completed, "
                f"current_step={onboarding_state.current_step}/9"
            )
            raise ValueError(
                "Complete onboarding first before accessing regular chat. "
                f"Current progress: {onboarding_state.current_step}/9 states completed. "
                f"Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. "
                f"User: {user_id}"
            )
        
        # Reject if specialized agent explicitly requested
        if agent_type and agent_type in specialized_agents:
            logger.warning(
                f"Access control violation: user={user_id}, "
                f"reason=specialized_agent_post_onboarding, "
                f"requested_agent={agent_type.value}"
            )
            raise ValueError(
                f"Specialized agent '{agent_type.value}' is not available after onboarding completion. "
                "Only the general agent is accessible for post-onboarding interactions. "
                "The general agent can answer questions about workouts, meals, and schedules. "
                f"User: {user_id}"
            )
        
        # Allow general agent and tracker agent (tracker via general agent delegation)
        # Test agent also allowed for testing
        logger.debug(
            f"Access control passed: user={user_id}, "
            f"agent_type={agent_type.value if agent_type else 'general'}, "
            f"onboarding_mode=False, "
            f"onboarding_complete=True"
        )
```

### 3.2 Enhanced Classification Method

**Modified Method:** `_classify_query()`

**Changes:**
- Add `onboarding_mode` parameter
- Use different classification prompts based on mode
- Return appropriate agent types for each mode

**Implementation:**

```python
async def _classify_query(
    self,
    query: str,
    onboarding_mode: bool = False
) -> AgentType:
    """
    Classify a user query to determine the appropriate agent type.
    
    Uses different classification prompts based on onboarding mode:
    - During onboarding: Only returns specialized agents
    - Post-onboarding: Returns any agent type (but will be overridden to GENERAL)
    
    Args:
        query: User's query text
        onboarding_mode: Whether this is during onboarding
    
    Returns:
        AgentType: The classified agent type
    """
    # Create cache key from first 50 characters of query
    # Include onboarding_mode in cache key for proper separation
    cache_key = f"{onboarding_mode}:{query[:50].lower().strip()}"
    
    # Check classification cache
    if cache_key in self._classification_cache:
        logger.debug(f"Using cached classification for query: {cache_key}")
        return self._classification_cache[cache_key]
    
    # Initialize classifier LLM
    classifier = self._init_classifier_llm()
    
    # Build classification messages based on mode
    from langchain_core.messages import SystemMessage, HumanMessage
    
    if onboarding_mode:
        # Onboarding classification: Only specialized agents
        classification_prompt = """Classify this onboarding query into ONE category:
- workout: Fitness level, exercise plans, workout preferences, equipment, injuries, limitations
- diet: Dietary preferences, meal plans, nutrition, food restrictions, allergies, intolerances
- scheduler: Meal timing, workout schedule, hydration reminders, timing preferences
- supplement: Supplement preferences, guidance, current usage

Respond with ONLY the category name."""
    else:
        # Post-onboarding classification: All agents (but will be overridden to general)
        classification_prompt = """Classify this fitness query into ONE category:
- workout: Exercise plans, form, demonstrations, logging sets, workout routines, training
- diet: Meal plans, nutrition, recipes, food substitutions, calories, macros, eating
- supplement: Supplement guidance and information, vitamins, protein powder
- tracker: Progress tracking, adherence, metrics, weight tracking, measurements
- scheduler: Schedule changes, reminders, timing, rescheduling workouts or meals
- general: Motivation, casual conversation, general questions, greetings

Respond with ONLY the category name."""
    
    messages = [
        SystemMessage(content=classification_prompt),
        HumanMessage(content=query)
    ]
    
    try:
        # Call classifier LLM
        result = await classifier.ainvoke(messages)
        agent_type_str = result.content.strip().lower()
        
        logger.debug(
            f"Classifier returned: {agent_type_str} for query: {query[:50]}, "
            f"onboarding_mode={onboarding_mode}"
        )
        
        # Parse response to AgentType enum
        try:
            classified_type = AgentType(agent_type_str)
        except ValueError:
            # Default based on mode
            if onboarding_mode:
                # Default to WORKOUT during onboarding (first agent)
                logger.warning(
                    f"Unknown agent type from classifier: {agent_type_str}, "
                    f"defaulting to WORKOUT for onboarding query: {query[:50]}"
                )
                classified_type = AgentType.WORKOUT
            else:
                # Default to GENERAL post-onboarding
                logger.warning(
                    f"Unknown agent type from classifier: {agent_type_str}, "
                    f"defaulting to GENERAL for query: {query[:50]}"
                )
                classified_type = AgentType.GENERAL
        
        # Cache result in voice mode for performance
        if self.mode == "voice":
            self._classification_cache[cache_key] = classified_type
            logger.debug(f"Cached classification: {classified_type.value} for key: {cache_key}")
        
        return classified_type
        
    except Exception as e:
        # Log error and default based on mode
        logger.error(
            f"Classification failed for query '{query[:50]}': {e}. "
            f"Defaulting based on onboarding_mode={onboarding_mode}"
        )
        return AgentType.WORKOUT if onboarding_mode else AgentType.GENERAL
```

### 3.3 Enhanced Logging Method

**New Method:** `_log_routing_decision()`

**Implementation:**

```python
def _log_routing_decision(
    self,
    user_id: str,
    agent_type: AgentType,
    onboarding_mode: bool,
    onboarding_state: Optional[OnboardingState],
    classification_used: bool,
    routing_time_ms: int
) -> None:
    """
    Log agent routing decision with comprehensive context.
    
    Args:
        user_id: User's unique identifier
        agent_type: Selected agent type
        onboarding_mode: Whether this is onboarding mode
        onboarding_state: OnboardingState instance
        classification_used: Whether classification was used
        routing_time_ms: Time taken for routing decision
    """
    logger.info(
        f"Agent routing: user={user_id}, "
        f"agent_type={agent_type.value}, "
        f"onboarding_mode={onboarding_mode}, "
        f"onboarding_complete={onboarding_state.is_complete if onboarding_state else 'N/A'}, "
        f"onboarding_step={onboarding_state.current_step if onboarding_state else 'N/A'}/9, "
        f"mode={self.mode}, "
        f"classification_used={classification_used}, "
        f"routing_time_ms={routing_time_ms}"
    )
```

### 3.4 Updated route_query() Method

**Modified Method:** `route_query()`

**Changes:**
- Add call to `_enforce_access_control()`
- Pass `onboarding_mode` to `_classify_query()`
- Add call to `_log_routing_decision()`
- Add performance timing
- Force GENERAL agent post-onboarding

**Implementation:**

```python
async def route_query(
    self,
    user_id: str,
    query: str,
    agent_type: Optional[AgentType] = None,
    voice_mode: bool = False,
    onboarding_mode: bool = False
) -> "AgentResponse":
    """
    Route a user query to the appropriate agent and return the response.
    
    [Existing docstring content...]
    """
    import time
    start_time = time.time()
    
    # Import here to avoid circular dependency
    from app.services.context_loader import load_agent_context
    from app.agents.context import AgentResponse
    from app.models.user import User
    from app.models.onboarding import OnboardingState
    from sqlalchemy import select

    # Step 1: Load user context from database
    context = await load_agent_context(
        db=self.db_session,
        user_id=user_id,
        include_history=True,
        onboarding_mode=onboarding_mode  # Pass to context loader
    )
    
    # Step 1.5: Load user and onboarding state for access control
    result = await self.db_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Load onboarding state
    onboarding_result = await self.db_session.execute(
        select(OnboardingState).where(OnboardingState.user_id == user_id)
    )
    onboarding_state = onboarding_result.scalar_one_or_none()
    
    # Step 2: Enforce access control (NEW)
    self._enforce_access_control(
        user=user,
        onboarding_state=onboarding_state,
        agent_type=agent_type,
        onboarding_mode=onboarding_mode
    )
    
    # Step 3: Classify query if agent_type not provided
    classification_used = False
    if agent_type is None:
        agent_type = await self._classify_query(query, onboarding_mode)
        classification_used = True
    
    # Step 3.5: Force GENERAL agent post-onboarding (NEW)
    if not onboarding_mode:
        if agent_type != AgentType.GENERAL and agent_type != AgentType.TEST:
            logger.info(
                f"Query classified as {agent_type.value}, "
                f"forcing to general agent (post-onboarding)"
            )
            agent_type = AgentType.GENERAL

    # Step 4: Get or create agent instance
    agent = self._get_or_create_agent(agent_type, context)

    # Step 5: Process based on mode
    if voice_mode:
        # Voice mode: return concise string response wrapped in AgentResponse
        response_content = await agent.process_voice(query)
        response = AgentResponse(
            content=response_content,
            agent_type=agent_type.value,
            tools_used=[],
            metadata={
                "mode": "voice",
                "user_id": user_id,
                "fitness_level": context.fitness_level,
                "onboarding_mode": onboarding_mode
            }
        )
    else:
        # Text mode: return full AgentResponse
        response = await agent.process_text(query)
        # Add onboarding_mode to metadata
        if not response.metadata:
            response.metadata = {}
        response.metadata["onboarding_mode"] = onboarding_mode

    # Step 6: Track last agent type used
    self.last_agent_type = agent_type
    
    # Step 7: Log routing decision (NEW)
    routing_time_ms = int((time.time() - start_time) * 1000)
    self._log_routing_decision(
        user_id=user_id,
        agent_type=agent_type,
        onboarding_mode=onboarding_mode,
        onboarding_state=onboarding_state,
        classification_used=classification_used,
        routing_time_ms=routing_time_ms
    )

    return response
```

---

## 4. Testing Strategy

### 4.1 Unit Tests

**Test File:** `backend/tests/test_agent_orchestrator_refinement.py`

**Test Cases:**

```python
class TestAccessControlEnforcement:
    """Test access control enforcement logic."""
    
    async def test_onboarding_mode_allows_specialized_agents(self):
        """During onboarding, specialized agents should be accessible."""
        
    async def test_onboarding_mode_blocks_general_agent(self):
        """During onboarding, general agent should be blocked."""
        
    async def test_onboarding_mode_blocks_tracker_agent(self):
        """During onboarding, tracker agent should be blocked."""
        
    async def test_post_onboarding_allows_general_agent(self):
        """Post-onboarding, general agent should be accessible."""
        
    async def test_post_onboarding_blocks_specialized_agents(self):
        """Post-onboarding, specialized agents should be blocked."""
        
    async def test_onboarding_complete_rejects_onboarding_mode(self):
        """If onboarding complete, onboarding_mode=True should be rejected."""
        
    async def test_onboarding_incomplete_rejects_normal_mode(self):
        """If onboarding incomplete, onboarding_mode=False should be rejected."""
        
    async def test_missing_onboarding_state_raises_error(self):
        """Missing onboarding state should raise ValueError."""


class TestClassificationRefinement:
    """Test classification with onboarding_mode awareness."""
    
    async def test_classification_during_onboarding(self):
        """Classification during onboarding returns specialized agents."""
        
    async def test_classification_post_onboarding(self):
        """Classification post-onboarding returns any agent type."""
        
    async def test_classification_cache_separation(self):
        """Cache keys should be separate for different onboarding modes."""
        
    async def test_classification_default_during_onboarding(self):
        """Unknown classification during onboarding defaults to WORKOUT."""
        
    async def test_classification_default_post_onboarding(self):
        """Unknown classification post-onboarding defaults to GENERAL."""


class TestErrorMessages:
    """Test error message generation."""
    
    async def test_onboarding_already_completed_message(self):
        """Error message for completed onboarding includes helpful info."""
        
    async def test_onboarding_not_completed_message(self):
        """Error message for incomplete onboarding includes progress."""
        
    async def test_general_agent_during_onboarding_message(self):
        """Error message explains why general agent is blocked."""
        
    async def test_specialized_agent_post_onboarding_message(self):
        """Error message explains why specialized agent is blocked."""


class TestLogging:
    """Test logging functionality."""
    
    async def test_routing_decision_logged(self):
        """All routing decisions should be logged."""
        
    async def test_access_violation_logged(self):
        """Access control violations should be logged as warnings."""
        
    async def test_performance_metrics_logged(self):
        """Performance metrics should be included in logs."""
```

### 4.2 Integration Tests

**Test File:** `backend/tests/test_agent_orchestrator_integration.py`

**Test Cases:**

```python
class TestEndToEndRouting:
    """Test end-to-end routing with real database."""
    
    async def test_onboarding_flow_with_routing(self):
        """Test complete onboarding flow with agent routing."""
        
    async def test_post_onboarding_flow_with_routing(self):
        """Test post-onboarding flow with general agent."""
        
    async def test_access_control_violations_end_to_end(self):
        """Test access control violations through full stack."""
```

### 4.3 Property-Based Tests

**Test File:** `backend/tests/test_agent_orchestrator_properties.py`

**Properties:**

```python
from hypothesis import given, strategies as st

@given(
    onboarding_complete=st.booleans(),
    onboarding_mode=st.booleans(),
    agent_type=st.sampled_from(list(AgentType))
)
async def test_property_access_control_consistency(
    onboarding_complete: bool,
    onboarding_mode: bool,
    agent_type: AgentType
):
    """
    Property: Access control decisions are consistent.
    
    For any combination of onboarding_complete, onboarding_mode, and agent_type,
    the access control decision should be deterministic and follow the rules.
    """
```

---

## 5. Performance Considerations

### 5.1 Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Access Control Check | < 5ms | In-memory validation |
| Classification | < 500ms | With caching in voice mode |
| Logging | < 1ms | Async logging |
| Total Routing | < 2s | Voice mode (95th percentile) |
| Total Routing | < 3s | Text mode (95th percentile) |

### 5.2 Optimization Strategies

**Caching:**
- Classification results cached in voice mode
- Cache key includes onboarding_mode for proper separation
- Agent instances cached in voice mode

**Database Queries:**
- Single query to load user and onboarding state
- Use `scalar_one_or_none()` for efficiency

**Logging:**
- Use structured logging with extra fields
- Async logging to avoid blocking

---

## 6. Deployment Strategy

### 6.1 Rollout Plan

**Phase 1: Staging Deployment**
1. Deploy to staging environment
2. Run integration tests
3. Manual testing with various scenarios
4. Performance testing

**Phase 2: Canary Deployment**
1. Deploy to 10% of production traffic
2. Monitor error rates and performance
3. Verify access control enforcement
4. Check log quality

**Phase 3: Full Deployment**
1. Deploy to 100% of production traffic
2. Monitor metrics for 24 hours
3. Verify no regressions

### 6.2 Rollback Plan

**If Issues Detected:**
1. Revert to previous version
2. Investigate root cause
3. Fix issues in staging
4. Retry deployment

**Rollback Triggers:**
- Error rate > 1%
- Performance degradation > 20%
- Access control bypass detected

---

## 7. Monitoring and Alerts

### 7.1 Key Metrics

**Access Control:**
- `agent_orchestrator.access_violation.count` - Count of access violations
- `agent_orchestrator.access_violation.rate` - Rate per minute

**Performance:**
- `agent_orchestrator.routing_time_ms` - Routing time histogram
- `agent_orchestrator.classification_time_ms` - Classification time histogram

**Usage:**
- `agent_orchestrator.routing.count` - Count by agent_type and onboarding_mode
- `agent_orchestrator.classification.accuracy` - Classification accuracy

### 7.2 Alerts

**Critical Alerts:**
- Access violation rate > 10/minute
- Routing time P95 > 3s
- Error rate > 1%

**Warning Alerts:**
- Access violation rate > 5/minute
- Routing time P95 > 2s
- Classification failures > 5%

---

## 8. Open Questions

1. **Q:** Should we add a grace period for users who just completed onboarding?
   **A:** TBD - Need product input

2. **Q:** Should we track classification accuracy over time?
   **A:** TBD - Need analytics team input

3. **Q:** Should we add circuit breaker for classification failures?
   **A:** TBD - Need reliability engineering input

---

## 9. Appendix

### 9.1 Error Message Examples

**Example 1: Onboarding Already Completed**
```
ValueError: Onboarding already completed. Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. User: user-123, Onboarding completed at: 2026-02-13T10:30:00Z
```

**Example 2: Onboarding Not Completed**
```
ValueError: Complete onboarding first before accessing regular chat. Current progress: 5/9 states completed. Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. User: user-123
```

**Example 3: General Agent During Onboarding**
```
ValueError: General agent is not available during onboarding. Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. Current state: 3/9. User: user-123
```

**Example 4: Specialized Agent Post-Onboarding**
```
ValueError: Specialized agent 'workout' is not available after onboarding completion. Only the general agent is accessible for post-onboarding interactions. The general agent can answer questions about workouts, meals, and schedules. User: user-123
```

### 9.2 Log Entry Examples

**Example 1: Successful Routing**
```
INFO: Agent routing: user=user-123, agent_type=workout, onboarding_mode=True, onboarding_complete=False, onboarding_step=2/9, mode=text, classification_used=True, routing_time_ms=45
```

**Example 2: Access Violation**
```
WARNING: Access control violation: user=user-123, reason=general_agent_during_onboarding, current_step=3/9
```

**Example 3: Performance Metrics**
```
DEBUG: Agent routing performance: user=user-123, classification_time_ms=420, agent_creation_time_ms=15, total_routing_time_ms=450
```

---

**Document Status:** Ready for Implementation  
**Next Steps:** Create tasks.md with implementation plan

# General Agent Delegation Tools - Requirements

## 1. Overview

This spec addresses the enhancement identified in the validation report: adding delegation tools to the General Assistant Agent so it can query user data (workouts, meals, schedules, exercises) post-onboarding.

Currently, the general agent has limited tools (`get_user_stats`, `provide_motivation`). This enhancement will enable it to answer specific questions about the user's workout plans, meal plans, schedules, and exercise demonstrations by delegating to the same data sources used by specialized agents.

## 2. Problem Statement

**Current State**:
- General agent is the only agent accessible post-onboarding ✅
- General agent has basic tools for stats and motivation ✅
- General agent cannot answer specific questions like:
  - "What's my workout today?"
  - "Show me my meal plan for this week"
  - "When is my next workout scheduled?"
  - "How do I perform a squat?"

**Desired State**:
- General agent can answer all fitness-related questions by querying user data
- Users don't need to navigate to different sections - chat provides all information
- General agent delegates to the same data sources as specialized agents

## 3. User Stories

### US-1: Query Today's Workout
**As a** completed user  
**I want to** ask "What's my workout today?" in chat  
**So that** I can see my scheduled exercises without navigating to the workout section

**Acceptance Criteria**:
- General agent can retrieve today's workout plan
- Response includes exercises, sets, reps, rest periods
- Response matches data from workout planner agent's `get_current_workout` tool
- If no workout scheduled, agent responds with "rest day" message

### US-2: Query Meal Plan
**As a** completed user  
**I want to** ask "What should I eat today?" in chat  
**So that** I can see my meal plan without navigating to the meal section

**Acceptance Criteria**:
- General agent can retrieve today's meal plan
- Response includes meals, timing, nutritional information
- Response matches data from diet planner agent's `get_current_meal_plan` tool
- If no meal plan configured, agent provides helpful message

### US-3: Query Schedule
**As a** completed user  
**I want to** ask "When is my next workout?" in chat  
**So that** I can see my upcoming schedule without navigating to the schedule section

**Acceptance Criteria**:
- General agent can retrieve upcoming workout and meal schedules
- Response includes days, times, notification settings
- Response matches data from scheduler agent's `get_upcoming_schedule` tool

### US-4: Query Exercise Demonstrations
**As a** completed user  
**I want to** ask "How do I perform a squat?" in chat  
**So that** I can see exercise demonstrations without navigating to the exercise library

**Acceptance Criteria**:
- General agent can retrieve exercise demonstration details
- Response includes GIF URL, video URL, instructions, difficulty level
- Response matches data from workout planner agent's `show_exercise_demo` tool
- If exercise not found, agent provides helpful error message

### US-5: Query Recipe Details
**As a** completed user  
**I want to** ask "How do I make dal tadka?" in chat  
**So that** I can see recipe details without navigating to the recipe section

**Acceptance Criteria**:
- General agent can retrieve recipe details
- Response includes ingredients, cooking instructions, nutritional info
- Response matches data from diet planner agent's `get_recipe_details` tool
- If recipe not found, agent provides helpful error message

## 4. Functional Requirements

### FR-1: Workout Query Tool
**Priority**: High  
**Description**: Add `get_workout_info` tool to general agent

**Requirements**:
- Tool queries the same database tables as workout planner agent
- Returns today's workout plan with exercises, sets, reps, rest periods
- Handles "rest day" scenario gracefully
- Returns JSON format matching workout planner agent's response

### FR-2: Meal Query Tool
**Priority**: High  
**Description**: Add `get_meal_info` tool to general agent

**Requirements**:
- Tool queries the same database tables as diet planner agent
- Returns today's meal plan with dishes, timing, nutritional information
- Handles "no meal plan configured" scenario gracefully
- Returns JSON format matching diet planner agent's response

### FR-3: Schedule Query Tool
**Priority**: High  
**Description**: Add `get_schedule_info` tool to general agent

**Requirements**:
- Tool queries the same database tables as scheduler agent
- Returns upcoming workout and meal schedules
- Includes days, times, notification settings
- Returns JSON format matching scheduler agent's response

### FR-4: Exercise Demo Tool
**Priority**: Medium  
**Description**: Add `get_exercise_demo` tool to general agent

**Requirements**:
- Tool queries the exercise library database
- Returns GIF URL, video URL, instructions, difficulty level
- Handles "exercise not found" scenario gracefully
- Returns JSON format matching workout planner agent's response

### FR-5: Recipe Query Tool
**Priority**: Medium  
**Description**: Add `get_recipe_details` tool to general agent

**Requirements**:
- Tool queries the dish and ingredient database
- Returns ingredients, cooking instructions, nutritional info
- Handles "recipe not found" scenario gracefully
- Returns JSON format matching diet planner agent's response

### FR-6: Nutritional Calculation Tool
**Priority**: Low  
**Description**: Add `calculate_nutrition` tool to general agent

**Requirements**:
- Tool queries the dish database for nutritional information
- Returns macros (protein, carbs, fats) and calories
- Returns JSON format matching diet planner agent's response

## 5. Non-Functional Requirements

### NFR-1: Performance
- Tool execution time < 200ms for database queries
- No impact on general agent response time
- Efficient database queries with proper indexing

### NFR-2: Code Reusability
- Tools should reuse existing database query logic where possible
- Avoid duplicating code from specialized agents
- Consider extracting shared query logic to service layer

### NFR-3: Error Handling
- Graceful handling of database errors
- User-friendly error messages
- Logging of errors for debugging

### NFR-4: Consistency
- Response format matches specialized agent responses
- Same data returned as specialized agents
- Consistent error messages

## 6. Technical Constraints

### TC-1: Database Access
- Tools must use the same database session as the agent
- Tools must respect soft deletes (`deleted_at IS NULL`)
- Tools must filter by user context

### TC-2: Agent Context
- Tools must have access to `AgentContext` for user_id
- Tools must use `self.context.user_id` for queries
- Tools must not expose other users' data

### TC-3: LangChain Integration
- Tools must use `@tool` decorator for LangChain compatibility
- Tools must return JSON strings for LLM parsing
- Tools must have clear docstrings for LLM understanding

## 7. Out of Scope

- Modifying specialized agent tools (they remain unchanged)
- Adding new data sources or database tables
- Implementing caching for tool responses
- Adding voice-specific optimizations
- Implementing tool result streaming

## 8. Success Criteria

### Quantitative Metrics
- All 5 user stories have passing acceptance criteria
- Tool execution time < 200ms (95th percentile)
- Zero code duplication with specialized agents
- 100% test coverage for new tools

### Qualitative Metrics
- Users can get all fitness information via chat
- No need to navigate to different sections for basic queries
- Consistent experience between specialized and general agents
- Clear, helpful error messages

## 9. Dependencies

- Existing database schema (no changes required)
- Existing specialized agent implementations
- Existing `AgentContext` and `BaseAgent` classes
- Existing database session management

## 10. Risks & Mitigations

### Risk 1: Code Duplication
**Impact**: Medium  
**Probability**: High  
**Mitigation**: Extract shared query logic to service layer or helper functions

### Risk 2: Performance Degradation
**Impact**: Medium  
**Probability**: Low  
**Mitigation**: Use efficient queries, proper indexing, and performance testing

### Risk 3: Inconsistent Responses
**Impact**: Low  
**Probability**: Medium  
**Mitigation**: Reuse exact same query logic as specialized agents, add integration tests

## 11. Open Questions

1. Should we extract shared query logic to a service layer, or duplicate it in general agent?
   - **Recommendation**: Extract to service layer for maintainability

2. Should general agent tools support the same parameters as specialized agent tools?
   - **Recommendation**: Yes, for consistency

3. Should we add caching for frequently accessed data?
   - **Recommendation**: Out of scope for this spec, consider for future optimization

## 12. Acceptance Criteria Summary

### Must Have (P0)
- [ ] General agent has `get_workout_info` tool
- [ ] General agent has `get_meal_info` tool
- [ ] General agent has `get_schedule_info` tool
- [ ] All tools return data matching specialized agents
- [ ] All tools handle errors gracefully
- [ ] All user stories pass acceptance criteria

### Should Have (P1)
- [ ] General agent has `get_exercise_demo` tool
- [ ] General agent has `get_recipe_details` tool
- [ ] Shared query logic extracted to service layer
- [ ] Integration tests for all tools

### Nice to Have (P2)
- [ ] General agent has `calculate_nutrition` tool
- [ ] Performance benchmarks for tool execution
- [ ] Tool usage analytics

## 13. Timeline Estimate

- **Requirements Review**: 30 minutes
- **Design**: 1 hour
- **Implementation**: 2-3 hours
- **Testing**: 1 hour
- **Documentation**: 30 minutes
- **Total**: 5-6 hours

## 14. References

- Validation Report: `validation_report.md`
- Refined Product Requirements: `docs/product/refined_product_requirement_shuren.md`
- General Assistant Agent: `backend/app/agents/general_assistant.py`
- Workout Planner Agent: `backend/app/agents/workout_planner.py`
- Diet Planner Agent: `backend/app/agents/diet_planner.py`
- Scheduler Agent: `backend/app/agents/scheduler.py`

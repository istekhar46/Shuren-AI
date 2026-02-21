# Onboarding Flow Redesign - Implementation Tasks

**Feature:** onboarding-flow-redesign  
**Status:** Ready for Implementation  
**Estimated Duration:** 7-9 days  
**Last Updated:** 2026-02-20

---

## Task Overview

This task list breaks down the implementation of the 4-step onboarding flow redesign into specific, actionable tasks organized by phase.

**Legend:**
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed
- `[~]` = Queued

---

## Phase 1: Foundation (Days 1-2)

### 1. Database Schema Updates (Fresh Start)

- [x] 1.1 Reset database and migration history
  - Run `poetry run python scripts/reset_db.py` to drop all tables
  - Delete all migration files in `backend/alembic/versions/`
  - Keep only `__init__.py` in versions directory
  - **Acceptance Criteria:**
    - All tables dropped from database
    - All migration files deleted
    - Database is clean slate

- [x] 1.2 Update SQLAlchemy models for new schema
  - Update OnboardingState model:
    - Add step_1_complete through step_4_complete (Boolean, default False)
    - Set current_step default to 1
    - Remove step_data column if exists
    - Keep agent_context, conversation_history, agent_history (JSONB)
  - Update MealTemplate model:
    - Add plan_name (String(255), nullable=True)
    - Add daily_calorie_target (Integer, nullable=True)
    - Add protein_grams (Numeric(6,2), nullable=True)
    - Add carbs_grams (Numeric(6,2), nullable=True)
    - Add fats_grams (Numeric(6,2), nullable=True)
    - Add weekly_template (JSONB, nullable=True)
  - **Acceptance Criteria:**
    - Models updated with new columns
    - Type hints correct
    - No linting errors

- [x] 1.3 Create initial migration with complete schema
  - Run `poetry run alembic revision --autogenerate -m "initial schema with 4-step onboarding"`
  - Review generated migration file
  - Verify all tables and columns included
  - **Acceptance Criteria:**
    - Migration file created
    - All tables defined
    - New columns included in onboarding_states and meal_templates

- [x] 1.4 Apply migration to development database
  - Run `poetry run alembic upgrade head`
  - Verify all tables created
  - Run `poetry run python scripts/check_db.py` to verify
  - **Acceptance Criteria:**
    - Migration applies successfully
    - All tables exist in database
    - Schema matches models

### 2. Agent Orchestrator Updates

- [x] 2.1 Update step-to-agent mapping
  - Modify `_step_to_agent()` method to map 4 steps instead of 9
  - Update step validation (1-4 instead of 1-9)
  - **Acceptance Criteria:**
    - Step 1 → FITNESS_ASSESSMENT
    - Step 2 → WORKOUT_PLANNING
    - Step 3 → DIET_PLANNING
    - Step 4 → SCHEDULING
    - Invalid steps raise ValueError

- [x] 2.2 Remove GoalSettingAgent from orchestrator
  - Remove GoalSettingAgent from agent_classes dict
  - Remove GOAL_SETTING from OnboardingAgentType enum
  - Update imports
  - **Acceptance Criteria:**
    - GoalSettingAgent not instantiated
    - No references to GOAL_SETTING type
    - Code compiles without errors

- [x] 2.3 Update agent descriptions
  - Update agent_descriptions dict in `/onboarding/current-agent` endpoint
  - Update for 4-step flow
  - **Acceptance Criteria:**
    - Descriptions match new agent responsibilities
    - All 4 agents have descriptions
    - No references to old 9-step flow

### 3. Update Pydantic Schemas

- [x] 3.1 Update OnboardingStateResponse schema
  - Add step_1_complete through step_4_complete fields
  - Remove step_data field
  - Update documentation
  - **Acceptance Criteria:**
    - Schema matches database model
    - All fields have correct types
    - Documentation is clear

- [x] 3.2 Update OnboardingProgressResponse schema
  - Update total_states to 4
  - Update state metadata for 4 steps
  - **Acceptance Criteria:**
    - Progress calculation works for 4 steps
    - Completion percentage accurate

---

## Phase 2: Agent Implementation (Days 3-5)

### 4. FitnessAssessmentAgent (Step 1)

- [x] 4.1 Merge goal-setting functionality
  - Update system prompt to include goal collection
  - Add goal-related questions to conversation flow
  - **Acceptance Criteria:**
    - Agent asks about fitness level AND goals
    - Conversation feels natural
    - All required data collected

- [x] 4.2 Update save_fitness_assessment tool
  - Extend to save goals (primary_goal, secondary_goal, goal_priority)
  - Validate goal values
  - Save to agent_context["fitness_assessment"]
  - Mark step_1_complete = true
  - Advance to step 2
  - **Acceptance Criteria:**
    - Tool saves all fitness and goal data
    - Validation works correctly
    - Database updated properly
    - Step advances to 2

- [x] 4.3 Write unit tests for FitnessAssessmentAgent
  - Test save_fitness_assessment tool
  - Test validation logic
  - Test step completion
  - **Acceptance Criteria:**
    - All tests pass
    - Coverage > 80%

### 5. WorkoutPlanningAgent (Step 2)

- [x] 5.1 Integrate WorkoutPlanGenerator service
  - Import WorkoutPlanGenerator in agent
  - Initialize in __init__ method
  - **Acceptance Criteria:**
    - Service imported correctly
    - No circular dependencies

- [x] 5.2 Implement generate_workout_plan tool
  - Call WorkoutPlanGenerator.generate_plan()
  - Pass fitness data from step 1
  - Return plan as dict
  - **Acceptance Criteria:**
    - Tool generates complete workout plans
    - Plans include all required fields
    - Plans respect constraints

- [x] 5.3 Implement modify_workout_plan tool
  - Call WorkoutPlanGenerator.modify_plan()
  - Handle modification requests
  - Return modified plan
  - **Acceptance Criteria:**
    - Tool modifies plans correctly
    - Modifications applied as requested
    - Plan structure remains valid

- [x] 5.4 Implement save_workout_plan tool
  - Validate plan structure
  - Collect workout schedule (days and times)
  - Save plan and schedule to agent_context["workout_planning"]
  - Mark step_2_complete = true
  - Advance to step 3
  - **Acceptance Criteria:**
    - Tool saves plan and schedule
    - Validation works correctly
    - Database updated properly
    - Step advances to 3

- [x] 5.5 Update system prompt for plan approval workflow
  - Add instructions for presenting plans
  - Add instructions for handling modifications
  - Add instructions for getting approval
  - Add instructions for collecting schedule
  - **Acceptance Criteria:**
    - Prompt guides agent through workflow
    - Agent presents plans clearly
    - Agent handles modifications well

- [x] 5.6 Write unit tests for WorkoutPlanningAgent
  - Test generate_workout_plan tool
  - Test modify_workout_plan tool
  - Test save_workout_plan tool
  - Test validation logic
  - **Acceptance Criteria:**
    - All tests pass
    - Coverage > 80%

### 6. DietPlanningAgent (Step 3)

- [x] 6.1 Integrate MealPlanGenerator service
  - Import MealPlanGenerator in agent
  - Initialize in __init__ method
  - **Acceptance Criteria:**
    - Service imported correctly
    - No circular dependencies

- [x] 6.2 Implement generate_meal_plan tool
  - Call MealPlanGenerator.generate_plan()
  - Pass fitness and workout data from previous steps
  - Return plan as dict
  - **Acceptance Criteria:**
    - Tool generates complete meal plans
    - Plans include macros and sample meals
    - Plans respect dietary restrictions

- [x] 6.3 Implement modify_meal_plan tool
  - Call MealPlanGenerator.modify_plan()
  - Handle modification requests
  - Return modified plan
  - **Acceptance Criteria:**
    - Tool modifies plans correctly
    - Modifications applied as requested
    - Plan structure remains valid

- [x] 6.4 Implement save_meal_plan tool
  - Validate plan structure
  - Collect meal schedule (meal times)
  - Save plan and schedule to agent_context["diet_planning"]
  - Mark step_3_complete = true
  - Advance to step 4
  - **Acceptance Criteria:**
    - Tool saves plan and schedule
    - Validation works correctly
    - Database updated properly
    - Step advances to 4

- [x] 6.5 Update system prompt for plan approval workflow
  - Add instructions for presenting meal plans
  - Add instructions for handling modifications
  - Add instructions for getting approval
  - Add instructions for collecting meal times
  - **Acceptance Criteria:**
    - Prompt guides agent through workflow
    - Agent presents plans clearly
    - Agent handles modifications well

- [x] 6.6 Write unit tests for DietPlanningAgent
  - Test generate_meal_plan tool
  - Test modify_meal_plan tool
  - Test save_meal_plan tool
  - Test validation logic
  - **Acceptance Criteria:**
    - All tests pass
    - Coverage > 80%

### 7. SchedulingAgent (Step 4)

- [x] 7.1 Remove workout/meal schedule collection
  - Remove save_workout_schedule tool (moved to WorkoutPlanningAgent)
  - Remove save_meal_schedule tool (moved to DietPlanningAgent)
  - Update imports
  - **Acceptance Criteria:**
    - Scheduling tools removed
    - No broken references
    - Code compiles

- [x] 7.2 Keep save_hydration_preferences tool
  - Verify tool works correctly
  - Update to save to agent_context["scheduling"]["hydration"]
  - **Acceptance Criteria:**
    - Tool saves hydration preferences
    - Data structure matches design

- [x] 7.3 Implement save_supplement_preferences tool
  - Collect interest in supplements
  - Collect current supplements (optional)
  - Save to agent_context["scheduling"]["supplements"]
  - Mark step_4_complete = true
  - **Acceptance Criteria:**
    - Tool saves supplement preferences
    - Step 4 marked complete
    - No step advancement (stays at 4)

- [x] 7.4 Update system prompt
  - Remove workout/meal schedule instructions
  - Add supplement guidance instructions
  - Emphasize informational only (no prescriptions)
  - **Acceptance Criteria:**
    - Prompt reflects new responsibilities
    - Agent provides education not prescriptions

- [x] 7.5 Write unit tests for SchedulingAgent
  - Test save_hydration_preferences tool
  - Test save_supplement_preferences tool
  - Test step completion
  - **Acceptance Criteria:**
    - All tests pass
    - Coverage > 80%

---

## Phase 3: API & Integration (Days 6-7)

### 8. API Endpoint Updates

- [x] 8.1 Update GET /onboarding/progress endpoint
  - Update STATE_METADATA for 4 steps
  - Update total_states to 4
  - Update completion percentage calculation
  - **Acceptance Criteria:**
    - Endpoint returns correct progress for 4 steps
    - Completion percentage accurate
    - State metadata correct

- [x] 8.2 Update GET /onboarding/state endpoint
  - Return step completion flags
  - Remove step_data from response
  - **Acceptance Criteria:**
    - Response includes step_1_complete through step_4_complete
    - No step_data in response

- [x] 8.3 Keep POST /onboarding/chat endpoint
  - Verify works with updated orchestrator
  - Test with all 4 agents
  - **Acceptance Criteria:**
    - Chat works for all 4 steps
    - Agent routing correct
    - Conversation history saved

- [x] 8.4 Keep GET /onboarding/current-agent endpoint
  - Update agent descriptions
  - Verify works with 4-step flow
  - **Acceptance Criteria:**
    - Returns correct agent for each step
    - Descriptions match new flow

- [x] 8.5 Keep POST /onboarding/complete endpoint
  - Verify works with new agent_context structure
  - Test profile creation from 4-step data
  - **Acceptance Criteria:**
    - Endpoint creates profile successfully
    - All related entities created
    - Profile locked correctly

- [x] 8.6 Remove POST /onboarding/step endpoint
  - Delete endpoint from router
  - Remove from API documentation
  - **Acceptance Criteria:**
    - Endpoint removed
    - No broken references
    - API docs updated

### 9. ProfileCreationService Integration

- [x] 9.1 Verify ProfileCreationService reads new agent_context structure
  - Test with fitness_assessment data
  - Test with workout_planning data (plan + schedule)
  - Test with diet_planning data (plan + schedule)
  - Test with scheduling data (hydration + supplements)
  - **Acceptance Criteria:**
    - Service reads all data correctly
    - No errors with new structure

- [x] 9.2 Update profile creation to use workout_planning.plan
  - Read plan from agent_context["workout_planning"]["plan"]
  - Create WorkoutPlan entity with plan_data JSONB
  - **Acceptance Criteria:**
    - WorkoutPlan created correctly
    - plan_data populated from agent_context

- [x] 9.3 Update profile creation to use diet_planning.plan
  - Read plan from agent_context["diet_planning"]["plan"]
  - Create MealPlanTemplate entity with weekly_template JSONB
  - **Acceptance Criteria:**
    - MealPlanTemplate created correctly
    - weekly_template populated from agent_context

- [x] 9.4 Update schedule creation
  - Read workout schedule from agent_context["workout_planning"]["schedule"]
  - Read meal schedule from agent_context["diet_planning"]["schedule"]
  - Create WorkoutSchedule and MealSchedule entities
  - **Acceptance Criteria:**
    - Schedules created correctly
    - Times match agent_context data

### 10. Integration Testing

- [x] 10.1 Write end-to-end onboarding flow test
  - Test complete flow from step 1 to completion
  - Verify all data saved correctly
  - Verify profile created with all entities
  - **Acceptance Criteria:**
    - Test completes successfully
    - All steps work together
    - Profile creation works

- [x] 10.2 Test agent handoffs
  - Test transition from step 1 to 2
  - Test transition from step 2 to 3
  - Test transition from step 3 to 4
  - Verify context preserved across steps
  - **Acceptance Criteria:**
    - All transitions work smoothly
    - Context available to next agent
    - No data loss

- [x] 10.3 Test plan generation and modification
  - Test workout plan generation
  - Test workout plan modification
  - Test meal plan generation
  - Test meal plan modification
  - **Acceptance Criteria:**
    - Plans generate successfully
    - Modifications work correctly
    - Plans remain valid after modifications

- [x] 10.4 Test error handling
  - Test with invalid inputs
  - Test with missing data
  - Test with LLM failures
  - Test with database errors
  - **Acceptance Criteria:**
    - Errors handled gracefully
    - User-friendly error messages
    - No data corruption

---

## Phase 4: Testing & Refinement (Days 8-9)

### 11. Property-Based Testing

- [ ] 11.1 Write property tests for WorkoutPlanGenerator
  - Test that plans always have valid structure
  - Test that frequency matches input
  - Test that exercises have valid sets/reps
  - **Acceptance Criteria:**
    - Properties hold for all valid inputs
    - Tests pass with Hypothesis

- [ ] 11.2 Write property tests for MealPlanGenerator
  - Test that macros sum to calories (within tolerance)
  - Test that meal count matches frequency
  - Test that allergies are respected
  - **Acceptance Criteria:**
    - Properties hold for all valid inputs
    - Tests pass with Hypothesis

- [ ] 11.3 Write property tests for agent_context structure
  - Test that saved data matches input data
  - Test that all required fields present
  - **Acceptance Criteria:**
    - Properties hold for all agents
    - No data loss or corruption

### 12. Performance Testing

- [ ] 12.1 Test chat response times
  - Measure response time for simple messages
  - Measure response time for tool calls
  - Verify < 3s target
  - **Acceptance Criteria:**
    - 95th percentile < 3s
    - No timeouts

- [ ] 12.2 Test plan generation times
  - Measure workout plan generation time
  - Measure meal plan generation time
  - Verify < 10s and < 15s targets
  - **Acceptance Criteria:**
    - Workout plans < 10s (95th percentile)
    - Meal plans < 15s (95th percentile)

- [ ] 12.3 Test database operations
  - Measure save operation times
  - Measure profile creation time
  - Verify < 500ms and < 2s targets
  - **Acceptance Criteria:**
    - Saves < 500ms (95th percentile)
    - Profile creation < 2s (95th percentile)

### 13. Code Quality & Documentation

- [ ] 13.1 Run linting and type checking
  - Run `poetry run mypy backend/app`
  - Run `poetry run flake8 backend/app`
  - Fix all errors and warnings
  - **Acceptance Criteria:**
    - No linting errors
    - No type errors
    - Code follows style guide

- [ ] 13.2 Update API documentation
  - Update OpenAPI/Swagger docs
  - Add examples for all endpoints
  - Document error responses
  - **Acceptance Criteria:**
    - Docs accurate and complete
    - Examples work correctly

- [ ] 13.3 Update code comments and docstrings
  - Add/update docstrings for all agents
  - Add/update docstrings for all tools
  - Add inline comments for complex logic
  - **Acceptance Criteria:**
    - All public methods documented
    - Complex logic explained
    - Docstrings follow Google style

- [ ] 13.4 Update technical documentation
  - Update architecture diagrams
  - Update sequence diagrams
  - Update deployment guide
  - **Acceptance Criteria:**
    - Docs reflect new 4-step flow
    - Diagrams accurate
    - Deployment guide updated

### 14. Monitoring & Observability

- [ ] 14.1 Add Prometheus metrics
  - Add onboarding_step_duration metric
  - Add onboarding_completion_rate metric
  - Add plan_generation_duration metric
  - Add plan_modification_count metric
  - **Acceptance Criteria:**
    - Metrics exported correctly
    - Grafana dashboards work

- [ ] 14.2 Add structured logging
  - Log step completions with context
  - Log plan generations with duration
  - Log errors with stack traces
  - **Acceptance Criteria:**
    - Logs structured (JSON)
    - All important events logged
    - Log levels appropriate

- [ ] 14.3 Set up alerts
  - Alert on completion rate < 80%
  - Alert on step duration > 5 min
  - Alert on plan generation failures > 5%
  - Alert on database latency > 1s
  - **Acceptance Criteria:**
    - Alerts configured in monitoring system
    - Alert thresholds appropriate
    - Notifications work

---

## Phase 5: Deployment (Post-Implementation)

### 15. Staging Deployment

- [ ] 15.1 Deploy to staging environment
  - Reset staging database: `poetry run python scripts/reset_db.py`
  - Run migration: `poetry run alembic upgrade head`
  - Deploy updated code
  - Verify all services running
  - **Acceptance Criteria:**
    - Database reset successful
    - Migration creates all tables
    - Code deployed without errors
    - All health checks pass

- [ ] 15.2 Run smoke tests in staging
  - Test complete onboarding flow
  - Test all API endpoints
  - Test error scenarios
  - **Acceptance Criteria:**
    - All smoke tests pass
    - No critical issues found

- [ ] 15.3 Internal testing
  - Team members complete onboarding
  - Collect feedback
  - Fix any issues found
  - **Acceptance Criteria:**
    - At least 5 team members test
    - Feedback documented
    - Critical issues fixed

### 16. Production Rollout

- [ ] 16.1 Create feature flag
  - Add feature flag for new onboarding flow
  - Default to disabled
  - **Acceptance Criteria:**
    - Feature flag works correctly
    - Can toggle without deployment

- [ ] 16.2 Deploy to production
  - **IMPORTANT**: Coordinate with team for production database reset
  - Backup existing data if needed
  - Reset production database during maintenance window
  - Run migration: `poetry run alembic upgrade head`
  - Deploy updated code
  - Verify all services running
  - **Acceptance Criteria:**
    - Database reset successful
    - Migration creates all tables
    - Zero downtime deployment (use maintenance window)
    - All health checks pass

- [ ] 16.3 Enable for 10% of users
  - Enable feature flag for 10%
  - Monitor metrics closely
  - Watch for errors
  - **Acceptance Criteria:**
    - 10% of users see new flow
    - No critical errors
    - Metrics look good

- [ ] 16.4 Gradual rollout
  - Increase to 25% after 24 hours
  - Increase to 50% after 48 hours
  - Increase to 100% after 72 hours
  - **Acceptance Criteria:**
    - Completion rate > 85%
    - No increase in errors
    - User feedback positive

---

## Success Criteria

### Technical Metrics
- ✅ All tests pass (unit, integration, property-based)
- ✅ Code coverage > 80%
- ✅ API response times meet targets
- ✅ Zero data loss during migration
- ✅ No critical bugs in production

### User Metrics
- ✅ Onboarding completion rate > 85%
- ✅ Average completion time < 25 minutes
- ✅ User satisfaction score > 4.2/5
- ✅ Plan modification rate < 30%
- ✅ Week 1 engagement > 70%

---

## Notes

- Use `poetry run` for all Python commands
- Run tests frequently during development
- Commit after each completed task
- Update this file as tasks are completed
- Mark tasks as `[x]` when done, `[-]` when in progress


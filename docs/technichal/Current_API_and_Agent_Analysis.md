# Current API and Agent Analysis

## Executive Summary

This document analyzes the existing onboarding API endpoints, agents, and services to understand what needs to change for the new 4-step onboarding flow.

**Key Finding**: The current system is well-architected with reusable components. Most services (WorkoutPlanGenerator, MealPlanGenerator) can be reused as-is. The main changes needed are:
1. Simplify agent orchestration from 5 agents (9 steps) to 4 agents (4 steps)
2. Update agent prompts to generate complete plans during onboarding
3. Modify API endpoints to support plan approval workflow
4. Update database schema (already analyzed - minimal changes needed)

---

## Current API Endpoints

### File: `backend/app/api/v1/endpoints/onboarding.py`

#### 1. GET `/onboarding/progress`
**Purpose**: Get rich onboarding progress metadata for UI indicators

**Response**: `OnboardingProgressResponse`
- current_state, total_states, completed_states
- current_state_info, next_state_info
- is_complete, completion_percentage, can_complete

**Status for New Flow**: ✅ **KEEP WITH MODIFICATIONS**
- Update to return 4 steps instead of 9
- Update state metadata to reflect new step names

---

#### 2. GET `/onboarding/state`
**Purpose**: Get current onboarding state

**Response**: `OnboardingStateResponse`
- id, user_id, current_step, is_complete
- step_data (JSONB field)

**Status for New Flow**: ✅ **KEEP WITH MODIFICATIONS**
- Replace `step_data` with `agent_context` (already exists in model)
- Update to work with new 4-step flow

---

#### 3. POST `/onboarding/step`
**Purpose**: Save onboarding step data with validation

**Request**: `OnboardingStepRequest`
- step: int
- data: dict

**Response**: `OnboardingStepResponse`
- current_step, is_complete, message, next_state, next_state_info

**Status for New Flow**: ❌ **REMOVE OR REDESIGN**
- Old flow: Client sends data, server validates and saves
- New flow: Agent generates plan, user approves/modifies, agent saves via tool calls
- This endpoint becomes redundant - agents save directly via tools

---

#### 4. POST `/onboarding/complete`
**Purpose**: Complete onboarding and create locked user profile

**Process**:
1. Loads OnboardingState
2. Checks if already complete (409 if true)
3. Verifies all required agent data in agent_context
4. Creates UserProfile using ProfileCreationService
5. Marks onboarding complete
6. Sets current_agent to "general_assistant"

**Status for New Flow**: ✅ **KEEP AS-IS**
- This endpoint is perfect for new flow
- Already reads from agent_context (where agents save data)
- Already validates completeness
- Already creates profile from agent data

---

#### 5. POST `/onboarding/chat`
**Purpose**: Chat with current onboarding agent

**Request**: `OnboardingChatRequest`
- message: str

**Response**: `OnboardingChatResponse`
- message: str (agent's reply)
- agent_type: str
- current_step: int
- step_complete: bool
- next_action: str

**Process**:
1. Creates OnboardingAgentOrchestrator
2. Gets current agent based on user's step
3. Processes message through agent
4. Appends to conversation_history
5. Returns agent response

**Status for New Flow**: ✅ **KEEP WITH MODIFICATIONS**
- Core functionality perfect for new flow
- Need to update orchestrator to map 4 steps instead of 9
- Response schema already supports step_complete flag (for plan approval)

---

#### 6. GET `/onboarding/current-agent`
**Purpose**: Get information about current onboarding agent

**Response**: `CurrentAgentResponse`
- agent_type: str
- current_step: int
- agent_description: str
- context_summary: dict

**Status for New Flow**: ✅ **KEEP WITH MODIFICATIONS**
- Update agent descriptions for new 4-step flow
- Update step-to-agent mapping

---

## Current Agent Architecture

### Agent Orchestrator

**File**: `backend/app/services/onboarding_orchestrator.py`

**Current Step-to-Agent Mapping** (9 steps → 5 agents):
```python
Steps 1-2: FITNESS_ASSESSMENT
Step 3:    GOAL_SETTING
Steps 4-5: DIET_PLANNING
Steps 6-7: WORKOUT_PLANNING
Steps 8-9: SCHEDULING
```

**New Step-to-Agent Mapping** (4 steps → 4 agents):
```python
Step 1: FITNESS_ASSESSMENT (fitness level + goals)
Step 2: WORKOUT_PLANNING (constraints + complete workout plan)
Step 3: DIET_PLANNING (preferences + complete meal plan)
Step 4: SCHEDULING (hydration + supplements)
```

**Key Methods**:
- `get_current_agent(user_id)` - Returns appropriate agent for current step
- `_step_to_agent(step)` - Maps step number to agent type
- `_create_agent(agent_type, context_dict, user_id)` - Factory method
- `advance_step(user_id)` - Increments step after agent completes

**Changes Needed**:
- Update `_step_to_agent()` to map 4 steps instead of 9
- Remove GoalSettingAgent (merge into FitnessAssessmentAgent)
- Update agent type enum to reflect new flow

---

### Agent Base Class

**File**: `backend/app/agents/onboarding/base.py`

**Key Features**:
- Uses LangChain for LLM integration
- Structured tool-calling pattern
- Saves data to `agent_context` JSONB field
- Tracks state to avoid repetitive questions
- Returns structured responses with `step_complete` flag

**Status**: ✅ **KEEP AS-IS**
- Base class is well-designed and reusable
- No changes needed to base architecture

---

### Current Agents

#### 1. FitnessAssessmentAgent
**File**: `backend/app/agents/onboarding/fitness_assessment.py`

**Current Responsibility**: Assess fitness level (steps 1-2)

**Tools**:
- `save_fitness_assessment` - Saves to agent_context

**New Responsibility**: Assess fitness level + collect fitness goals (step 1)

**Changes Needed**:
- Merge goal-setting functionality from GoalSettingAgent
- Update prompt to collect both fitness level AND goals in one conversation
- Add tool to save goals (or extend existing tool)

---

#### 2. GoalSettingAgent
**File**: `backend/app/agents/onboarding/goal_setting.py`

**Current Responsibility**: Collect workout constraints and equipment (step 3)

**Status**: ❌ **REMOVE**
- Merge fitness goals into FitnessAssessmentAgent (step 1)
- Merge workout constraints into WorkoutPlanningAgent (step 2)

---

#### 3. WorkoutPlanningAgent
**File**: `backend/app/agents/onboarding/workout_planning.py`

**Current Responsibility**: Generate workout plan (steps 6-7)

**Tools**:
- `generate_workout_plan` - Uses WorkoutPlanGenerator service
- `save_workout_plan` - Saves to agent_context
- `modify_workout_plan` - Modifies existing plan

**Service Used**: `WorkoutPlanGenerator` (backend/app/services/workout_plan_generator.py)

**New Responsibility**: Collect constraints + generate complete workout plan + get approval (step 2)

**Changes Needed**:
- Merge constraint collection from GoalSettingAgent
- Update prompt to:
  1. Ask about constraints (equipment, location, injuries)
  2. Generate COMPLETE workout plan using WorkoutPlanGenerator
  3. Present plan to user
  4. Handle approval/modification requests
  5. Save approved plan via tool call
- Tools are already perfect - no changes needed!

---

#### 4. DietPlanningAgent
**File**: `backend/app/agents/onboarding/diet_planning.py`

**Current Responsibility**: Generate meal plan (steps 4-5)

**Tools**:
- `generate_meal_plan` - Uses MealPlanGenerator service
- `save_meal_plan` - Saves to agent_context
- `modify_meal_plan` - Modifies existing plan

**Service Used**: `MealPlanGenerator` (backend/app/services/meal_plan_generator.py)

**New Responsibility**: Collect preferences + generate complete meal plan + get approval (step 3)

**Changes Needed**:
- Update prompt to:
  1. Ask about diet preferences, allergies, dislikes
  2. Generate COMPLETE meal plan using MealPlanGenerator
  3. Present plan to user with sample meals and macros
  4. Handle approval/modification requests
  5. Save approved plan via tool call
- Tools are already perfect - no changes needed!

---

#### 5. SchedulingAgent
**File**: `backend/app/agents/onboarding/scheduling.py`

**Current Responsibility**: Collect workout, meal, and hydration schedules (steps 8-9)

**Tools** (from `backend/app/agents/tools/scheduling_tools.py`):
- `save_workout_schedule(days, times)` - Saves workout timing
- `save_meal_schedule(meal_times)` - Saves meal timing
- `save_hydration_preferences(frequency_hours, target_ml)` - Saves hydration

**New Responsibility**: Collect hydration preferences + supplement guidance (step 4)

**Changes Needed**:
- Remove workout schedule collection (move to WorkoutPlanningAgent step 2)
- Remove meal schedule collection (move to DietPlanningAgent step 3)
- Keep hydration preferences
- Add supplement guidance (informational only, no prescription)
- Update prompt accordingly

---

## Service Layer Analysis

### WorkoutPlanGenerator Service

**File**: `backend/app/services/workout_plan_generator.py`

**Key Methods**:
- `generate_plan()` - Generates complete workout plan
  - Parameters: fitness_level, primary_goal, frequency, location, duration_minutes, equipment, limitations
  - Returns: WorkoutPlan object with complete program
  
- `modify_plan()` - Modifies existing plan based on user feedback
  - Parameters: current_plan, modifications dict
  - Returns: Modified WorkoutPlan object

**Workout Plan Structure**:
```python
class WorkoutPlan:
    frequency: int (2-7 days/week)
    duration_minutes: int (20-180)
    location: str (home/gym)
    equipment: List[str]
    training_split: str (Full Body, Upper/Lower, PPL, Body Part Split)
    workout_days: List[WorkoutDay]
    progression_strategy: str
```

**WorkoutDay Structure**:
```python
class WorkoutDay:
    day_name: str
    exercises: List[Exercise]
    total_duration_minutes: int
```

**Exercise Structure**:
```python
class Exercise:
    name: str
    type: ExerciseType (compound/isolation/cardio/flexibility)
    sets: int
    reps: str (e.g., "8-12", "AMRAP")
    rest_seconds: int
    notes: str
```

**Status**: ✅ **KEEP AS-IS - PERFECT FOR NEW FLOW**
- Already generates complete, detailed workout plans
- Already supports modifications
- Already handles all fitness levels and goals
- Already adapts to equipment and location
- No changes needed!

---

### MealPlanGenerator Service

**File**: `backend/app/services/meal_plan_generator.py`

**Key Methods**:
- `generate_plan()` - Generates complete meal plan
  - Parameters: fitness_level, primary_goal, workout_plan, diet_type, allergies, dislikes, meal_frequency, meal_prep_level
  - Returns: MealPlan object with complete nutrition strategy
  
- `modify_plan()` - Modifies existing plan based on user feedback
  - Parameters: current_plan, modifications dict
  - Returns: Modified MealPlan object

**Meal Plan Structure**:
```python
class MealPlan:
    diet_type: str (omnivore/vegetarian/vegan/pescatarian)
    allergies: List[str]
    dislikes: List[str]
    meal_frequency: int (2-6 meals/day)
    meal_prep_level: str (low/medium/high)
    daily_calories: int (1200-5000)
    protein_g: int
    carbs_g: int
    fats_g: int
    sample_meals: List[SampleMeal]
    meal_timing_suggestions: str
```

**SampleMeal Structure**:
```python
class SampleMeal:
    meal_type: MealType (breakfast/lunch/dinner/snack)
    name: str
    ingredients: List[str]
    approximate_calories: int
    approximate_protein_g: int
    approximate_carbs_g: int
    approximate_fats_g: int
    prep_time_minutes: int
```

**Status**: ✅ **KEEP AS-IS - PERFECT FOR NEW FLOW**
- Already generates complete meal plans with macros
- Already provides sample meals
- Already supports modifications
- Already handles dietary restrictions
- Already calculates calories based on workout plan
- No changes needed!

---

## Agent Tool Analysis

### Scheduling Tools

**File**: `backend/app/agents/tools/scheduling_tools.py`

**Tools**:
1. `save_workout_schedule(days, times)` - ✅ Keep, move to WorkoutPlanningAgent
2. `save_meal_schedule(meal_times)` - ✅ Keep, move to DietPlanningAgent
3. `save_hydration_preferences(frequency_hours, target_ml)` - ✅ Keep in SchedulingAgent

**Status**: ✅ **KEEP ALL TOOLS - REDISTRIBUTE TO DIFFERENT AGENTS**

---

## Data Flow Comparison

### OLD FLOW (9 steps, 5 agents)

```
Step 1-2: FitnessAssessmentAgent
  ↓ saves fitness_level to agent_context
  
Step 3: GoalSettingAgent
  ↓ saves goals, constraints, equipment to agent_context
  
Step 4-5: DietPlanningAgent
  ↓ collects preferences
  ↓ generates meal plan
  ↓ saves to agent_context
  
Step 6-7: WorkoutPlanningAgent
  ↓ generates workout plan
  ↓ saves to agent_context
  
Step 8-9: SchedulingAgent
  ↓ collects workout schedule
  ↓ collects meal schedule
  ↓ collects hydration preferences
  ↓ saves to agent_context
  
Complete: ProfileCreationService reads agent_context → creates profile
```

### NEW FLOW (4 steps, 4 agents)

```
Step 1: FitnessAssessmentAgent (ENHANCED)
  ↓ collects fitness_level
  ↓ collects fitness_goals
  ↓ saves to agent_context
  
Step 2: WorkoutPlanningAgent (ENHANCED)
  ↓ collects constraints, equipment, location
  ↓ generates COMPLETE workout plan (using WorkoutPlanGenerator)
  ↓ presents plan to user
  ↓ handles modifications
  ↓ user approves
  ↓ saves approved plan + workout schedule to agent_context
  
Step 3: DietPlanningAgent (ENHANCED)
  ↓ collects diet preferences, allergies, dislikes
  ↓ generates COMPLETE meal plan (using MealPlanGenerator)
  ↓ presents plan with sample meals and macros
  ↓ handles modifications
  ↓ user approves
  ↓ saves approved plan + meal schedule to agent_context
  
Step 4: SchedulingAgent (SIMPLIFIED)
  ↓ collects hydration preferences
  ↓ provides supplement guidance (informational)
  ↓ saves to agent_context
  
Complete: ProfileCreationService reads agent_context → creates profile
```

---

## Summary of Changes Needed

### 1. API Endpoints (backend/app/api/v1/endpoints/onboarding.py)

✅ **Keep with modifications**:
- GET `/onboarding/progress` - Update for 4 steps
- GET `/onboarding/state` - Update for 4 steps
- POST `/onboarding/chat` - Update orchestrator mapping
- GET `/onboarding/current-agent` - Update descriptions
- POST `/onboarding/complete` - Keep as-is

❌ **Remove**:
- POST `/onboarding/step` - Redundant in new flow

### 2. Agent Orchestrator (backend/app/services/onboarding_orchestrator.py)

**Changes**:
- Update `_step_to_agent()` method to map 4 steps:
  ```python
  Step 1: FITNESS_ASSESSMENT
  Step 2: WORKOUT_PLANNING
  Step 3: DIET_PLANNING
  Step 4: SCHEDULING
  ```
- Remove GoalSettingAgent from agent_classes dict

### 3. Agents

**FitnessAssessmentAgent** (step 1):
- ✏️ Merge goal-setting functionality
- ✏️ Update prompt to collect fitness level + goals
- ✏️ Add tool to save goals

**WorkoutPlanningAgent** (step 2):
- ✏️ Merge constraint collection
- ✏️ Update prompt for plan generation + approval workflow
- ✏️ Add workout schedule collection
- ✅ Keep existing tools (already perfect)

**DietPlanningAgent** (step 3):
- ✏️ Update prompt for plan generation + approval workflow
- ✏️ Add meal schedule collection
- ✅ Keep existing tools (already perfect)

**SchedulingAgent** (step 4):
- ✏️ Remove workout/meal schedule collection
- ✏️ Add supplement guidance
- ✏️ Update prompt
- ✅ Keep hydration tool

**GoalSettingAgent**:
- ❌ Remove (merge into FitnessAssessmentAgent and WorkoutPlanningAgent)

### 4. Services

**WorkoutPlanGenerator**:
- ✅ Keep as-is (perfect!)

**MealPlanGenerator**:
- ✅ Keep as-is (perfect!)

### 5. Database Schema

**Already analyzed in separate document** - minimal changes needed:
- Add 4 boolean flags to onboarding_states
- Add 6 columns to meal_templates
- Drop step_data column from onboarding_states

---

## Implementation Complexity Assessment

### Complexity: MEDIUM-LOW

**Why it's easier than expected**:
1. ✅ Services (WorkoutPlanGenerator, MealPlanGenerator) are already perfect
2. ✅ Agent tools are already perfect
3. ✅ Base agent architecture is solid
4. ✅ API endpoint structure is good
5. ✅ Database schema needs minimal changes

**What actually needs work**:
1. ✏️ Update agent prompts (4 agents)
2. ✏️ Update orchestrator mapping (1 method)
3. ✏️ Merge/remove GoalSettingAgent
4. ✏️ Update API endpoint metadata
5. ✏️ Database migration (minimal)

**Estimated Effort**:
- Agent prompt updates: 2-3 days
- Orchestrator changes: 1 day
- API updates: 1 day
- Database migration: 1 day
- Testing: 2-3 days
- **Total: 7-9 days**

---

## Risk Assessment

### Low Risk
- ✅ Services are stable and tested
- ✅ Tool implementations are solid
- ✅ Base architecture is sound

### Medium Risk
- ⚠️ Agent prompt engineering (need to test approval workflow)
- ⚠️ Conversation flow (ensure natural transitions)

### Mitigation
- Use existing agent patterns as templates
- Test each agent independently
- Implement feature flags for gradual rollout

---

## Next Steps

1. ✅ Complete this analysis document
2. ✏️ Update requirements.md with API/agent findings
3. ✏️ Update design.md with implementation details
4. ✏️ Create migration plan
5. ✏️ Begin implementation with FitnessAssessmentAgent (step 1)


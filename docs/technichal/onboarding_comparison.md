# Onboarding System Comparison
## Current Implementation vs. New Requirements

---

## Executive Summary

The current implementation has **70% of the foundation** needed for the new specialized onboarding agent system. The main differences are:

1. **Current**: Uses existing general-purpose agents (Workout, Diet, Scheduler, Supplement) for onboarding
2. **New**: Requires dedicated onboarding-specific agents with specialized prompts and plan generation/approval workflow

The current system already routes to specialized agents based on onboarding state, but lacks the conversational flow, plan proposal/approval, and progressive context handover that the new requirements specify.

---

## Detailed Comparison

### 1. Onboarding Flow Structure

| Aspect | Current Implementation | New Requirements | Gap |
|--------|----------------------|------------------|-----|
| **Number of Steps** | 9 states | 5 specialized agents handling 9 steps | ✅ Same |
| **State Management** | `OnboardingState` model with `current_step`, `step_data` JSONB | Same + `agent_context` JSONB, `conversation_history` JSONB | ⚠️ Missing fields |
| **Step Progression** | Linear 1→9 | Linear with agent handover | ✅ Compatible |
| **Data Storage** | JSONB `step_data` with `step_1`, `step_2`, etc. | JSONB `agent_context` with agent-specific keys | ⚠️ Different structure |

### 2. Agent Architecture

#### Current Implementation

```python
# STATE_TO_AGENT_MAP in onboarding_service.py
STATE_TO_AGENT_MAP = {
    1: AgentType.WORKOUT,      # Fitness Level
    2: AgentType.WORKOUT,      # Goals
    3: AgentType.WORKOUT,      # Constraints
    4: AgentType.DIET,         # Diet Preferences
    5: AgentType.DIET,         # Meal Plan
    6: AgentType.SCHEDULER,    # Meal Schedule
    7: AgentType.SCHEDULER,    # Workout Schedule
    8: AgentType.SCHEDULER,    # Hydration
    9: AgentType.SUPPLEMENT,   # Supplements
}
```

**How it works:**
1. User sends message via `POST /api/v1/chat/onboarding`
2. Backend looks up current state (1-9)
3. Routes to appropriate **general-purpose agent** (Workout/Diet/Scheduler/Supplement)
4. Agent processes message with `onboarding_mode=True` flag
5. Agent can call `save_onboarding_step()` tool to save data
6. State advances when data is saved

**Agents used:**
- `WorkoutPlannerAgent` - handles states 1-3
- `DietPlannerAgent` - handles states 4-5
- `SchedulerAgent` - handles states 6-8
- `SupplementGuideAgent` - handles state 9

#### New Requirements

```python
# Proposed structure
class OnboardingAgentType(str, Enum):
    FITNESS_ASSESSMENT = "fitness_assessment"      # Steps 1-2
    GOAL_SETTING = "goal_setting"                  # Step 3
    WORKOUT_PLANNING = "workout_planning"          # Steps 4-5
    DIET_PLANNING = "diet_planning"                # Steps 6-7
    SCHEDULING = "scheduling"                      # Steps 8-9
```

**How it should work:**
1. User sends message via `POST /api/v1/onboarding/chat`
2. Backend determines current **onboarding agent** (not general agent)
3. Agent has **specialized onboarding prompt** with context from previous agents
4. Agent asks questions, **proposes plans**, gets approval
5. Agent saves to `agent_context` with structured data
6. Agent explicitly hands over to next agent with context

**Agents needed:**
- `FitnessAssessmentAgent` - NEW, dedicated to steps 1-2
- `GoalSettingAgent` - NEW, dedicated to step 3
- `WorkoutPlanningAgent` (onboarding version) - NEW, steps 4-5 with plan generation
- `DietPlanningAgent` (onboarding version) - NEW, steps 6-7 with plan generation
- `SchedulingAgent` (onboarding version) - NEW, steps 8-9

### 3. Data Model Comparison

#### Current: OnboardingState Model

```python
class OnboardingState(BaseModel):
    user_id = Column(UUID, ForeignKey("users.id"))
    current_step = Column(Integer, default=0)
    is_complete = Column(Boolean, default=False)
    step_data = Column(JSONB, default=dict)          # ✅ Exists
    agent_history = Column(JSONB, default=list)      # ✅ Exists (tracks routing)
```

**step_data structure:**
```json
{
  "step_1": {"fitness_level": "intermediate"},
  "step_2": {"goals": [{"goal_type": "muscle_gain"}]},
  "step_3": {"equipment": ["gym"], "injuries": [], "limitations": []},
  ...
}
```

#### New: Enhanced OnboardingState Model

```python
class OnboardingState(BaseModel):
    user_id = Column(UUID, ForeignKey("users.id"))
    current_step = Column(Integer, default=0)
    current_agent = Column(String(50))               # ❌ Missing
    is_complete = Column(Boolean, default=False)
    step_data = Column(JSONB, default=dict)          # ✅ Exists
    agent_context = Column(JSONB, default=dict)      # ❌ Missing
    conversation_history = Column(JSONB, default=[]) # ❌ Missing
    agent_history = Column(JSONB, default=list)      # ✅ Exists
```

**agent_context structure:**
```json
{
  "fitness_assessment": {
    "fitness_level": "intermediate",
    "experience_years": 2,
    "limitations": [],
    "completed_at": "2024-01-15T10:30:00Z"
  },
  "goal_setting": {
    "primary_goal": "muscle_gain",
    "secondary_goal": "fat_loss",
    "target_weight_kg": 75,
    "completed_at": "2024-01-15T10:35:00Z"
  },
  "workout_planning": {
    "preferences": {...},
    "proposed_plan": {...},
    "user_approved": true,
    "completed_at": "2024-01-15T10:45:00Z"
  }
}
```

### 4. API Endpoints Comparison

#### Current Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/v1/onboarding/progress` | Get progress metadata | ✅ Exists |
| `GET /api/v1/onboarding/state` | Get current state | ✅ Exists |
| `POST /api/v1/onboarding/step` | Save step data (direct) | ✅ Exists |
| `POST /api/v1/onboarding/complete` | Complete onboarding | ✅ Exists |
| `POST /api/v1/chat/onboarding` | Chat with agent during onboarding | ✅ Exists |
| `GET /api/v1/chat/onboarding-stream` | Streaming chat | ✅ Exists |

#### New Requirements

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /api/v1/onboarding/chat` | Chat with current onboarding agent | ⚠️ Rename from `/chat/onboarding` |
| `POST /api/v1/onboarding/approve-plan` | Approve proposed plan | ❌ Missing |
| `GET /api/v1/onboarding/current-agent` | Get current agent info | ❌ Missing |
| `GET /api/v1/onboarding/progress` | Get progress | ✅ Exists |
| `POST /api/v1/onboarding/complete` | Complete onboarding | ✅ Exists |

### 5. Key Workflow Differences

#### Current Workflow

```
User: "I'm intermediate level"
    ↓
POST /api/v1/chat/onboarding
{
  "message": "I'm intermediate level",
  "current_state": 1
}
    ↓
Backend routes to WorkoutPlannerAgent (general agent)
    ↓
Agent processes with onboarding_mode=True
    ↓
Agent calls save_onboarding_step() tool
    ↓
Response: "Great! Intermediate level saved. What are your goals?"
    ↓
State advances to 2
```

**Characteristics:**
- ✅ Uses existing general-purpose agents
- ✅ Agents can save data via tools
- ❌ No specialized onboarding prompts
- ❌ No plan generation/proposal
- ❌ No explicit context handover
- ❌ No conversation history per agent

#### New Workflow

```
User: "I'm intermediate level"
    ↓
POST /api/v1/onboarding/chat
{
  "message": "I'm intermediate level",
  "step": 1
}
    ↓
Backend routes to FitnessAssessmentAgent (dedicated onboarding agent)
    ↓
Agent has specialized prompt with onboarding context
    ↓
Agent asks follow-up questions
    ↓
Agent calls save_fitness_assessment() tool
    ↓
Response: "Excellent! I've saved your fitness assessment. Let's move on to defining your goals."
    ↓
System advances to GoalSettingAgent with context:
{
  "fitness_assessment": {
    "fitness_level": "intermediate",
    "completed_at": "..."
  }
}
```

**Later in workflow:**

```
User: "4 days a week"
    ↓
WorkoutPlanningAgent (onboarding version)
    ↓
Agent calls generate_workout_plan()
    ↓
Agent proposes plan on screen
    ↓
Response: "Here's your 4-day plan: [detailed plan]. Does this work for you?"
    ↓
User: "Yes!"
    ↓
POST /api/v1/onboarding/approve-plan
{
  "plan_type": "workout",
  "approved": true
}
    ↓
Agent saves plan to user profile
    ↓
Advances to DietPlanningAgent with full context
```

**Characteristics:**
- ❌ Requires new dedicated onboarding agents
- ✅ Agents save data via tools (similar)
- ✅ Specialized onboarding prompts per agent
- ✅ Plan generation and proposal workflow
- ✅ Explicit context handover between agents
- ✅ Conversation history tracked per agent

### 6. Context Management

#### Current Implementation

**Context passing:**
- Agents receive `onboarding_mode=True` flag
- Agents can access `step_data` from OnboardingState
- No structured context handover
- Each agent call is independent

**Example:**
```python
# In WorkoutPlannerAgent
if onboarding_mode:
    # Agent knows it's onboarding but doesn't have structured context
    # from previous steps
    pass
```

#### New Requirements

**Context passing:**
- Each agent receives `agent_context` dict with all previous agent data
- Structured handover with completion timestamps
- Progressive context building

**Example:**
```python
# In WorkoutPlanningAgent (onboarding version)
def get_system_prompt(self) -> str:
    fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level")
    primary_goal = self.context.get("goal_setting", {}).get("primary_goal")
    
    return f"""
You are a Workout Planning Agent.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}

Your role: Create a workout plan based on their level and goals...
    """
```

### 7. Plan Generation & Approval

#### Current Implementation

**No plan generation workflow:**
- Agents collect data step by step
- No plan proposal/preview
- No explicit approval step
- Plans created only at the end via `complete_onboarding()`

**Flow:**
```
State 1-9: Collect data
    ↓
POST /api/v1/onboarding/complete
    ↓
complete_onboarding() creates:
  - UserProfile
  - FitnessGoals
  - PhysicalConstraints
  - DietaryPreferences
  - MealPlan
  - MealSchedules
  - WorkoutSchedules
  - HydrationPreferences
```

#### New Requirements

**Plan generation during onboarding:**
- Workout Planning Agent generates and proposes workout plan
- Diet Planning Agent generates and proposes meal plan
- User sees plan preview and approves/modifies
- Plans saved incrementally to user profile

**Flow:**
```
State 4-5: Workout Planning Agent
    ↓
Agent calls generate_workout_plan()
    ↓
Displays plan to user
    ↓
User approves
    ↓
POST /api/v1/onboarding/approve-plan
    ↓
Saves WorkoutPlan to user profile
    ↓
Advances to Diet Planning Agent

State 6-7: Diet Planning Agent
    ↓
Agent calls generate_meal_plan()
    ↓
Displays plan to user
    ↓
User approves
    ↓
Saves MealPlan to user profile
    ↓
Advances to Scheduling Agent
```

---

## Gap Analysis

### What Exists ✅

1. **Database Model**: `OnboardingState` with `step_data` and `agent_history`
2. **API Endpoints**: Chat endpoint, progress endpoint, complete endpoint
3. **Agent Routing**: `STATE_TO_AGENT_MAP` routes to specialized agents
4. **Agent Tools**: Agents can call `save_onboarding_step()` to save data
5. **Validation**: Step-specific validators for all 9 states
6. **Profile Creation**: `complete_onboarding()` creates full user profile
7. **Conversation Storage**: Messages saved to `conversation_messages` table

### What's Missing ❌

1. **Dedicated Onboarding Agents**:
   - `FitnessAssessmentAgent` (new)
   - `GoalSettingAgent` (new)
   - Onboarding-specific versions of Workout/Diet/Scheduling agents

2. **Database Fields**:
   - `OnboardingState.current_agent` (string)
   - `OnboardingState.agent_context` (JSONB) - different from `step_data`
   - `OnboardingState.conversation_history` (JSONB)

3. **Plan Generation Services**:
   - `WorkoutService.generate_plan()` for onboarding
   - `MealService.generate_plan()` for onboarding

4. **New API Endpoint**:
   - `GET /api/v1/onboarding/current-agent`

5. **Agent Orchestration**:
   - `OnboardingAgentOrchestrator` (separate from general `AgentOrchestrator`)
   - Context handover logic between agents
   - Conversational plan approval via agent tools

6. **Specialized Prompts**:
   - Each onboarding agent needs unique system prompts
   - Prompts must include context from previous agents
   - Prompts must guide plan generation and conversational approval
   - Prompts must detect approval intent ("yes", "looks good", etc.)

### What Needs Modification ⚠️

1. **OnboardingState Model**: Add missing fields
2. **Chat Endpoint**: Rename and enhance to support plan approval
3. **Agent Base Classes**: Create `BaseOnboardingAgent` separate from `BaseAgent`
4. **Complete Onboarding**: Modify to work with `agent_context` instead of `step_data`

---

## Migration Path

### Phase 1: Database Schema (Week 1)

```sql
-- Add new columns to onboarding_states
ALTER TABLE onboarding_states 
ADD COLUMN current_agent VARCHAR(50),
ADD COLUMN agent_context JSONB DEFAULT '{}',
ADD COLUMN conversation_history JSONB DEFAULT '[]';

-- Create index for agent queries
CREATE INDEX idx_onboarding_current_agent 
ON onboarding_states(current_agent) 
WHERE deleted_at IS NULL;
```

### Phase 2: Create Onboarding Agents (Week 2-3)

1. Create `BaseOnboardingAgent` class
2. Implement `FitnessAssessmentAgent`
3. Implement `GoalSettingAgent`
4. Create onboarding versions of Workout/Diet/Scheduling agents
5. Implement `OnboardingAgentOrchestrator`

### Phase 3: Plan Generation (Week 4)

1. Build `WorkoutService.generate_plan()`
2. Build `MealService.generate_plan()`
3. Add plan approval workflow
4. Create `POST /api/v1/onboarding/approve-plan` endpoint

### Phase 4: Integration & Testing (Week 5-6)

1. Update `complete_onboarding()` to use `agent_context`
2. Add context handover logic
3. End-to-end testing
4. Migrate existing `step_data` to `agent_context` format

---

## Backward Compatibility

### Strategy

1. **Keep both structures temporarily**:
   - `step_data` (old format)
   - `agent_context` (new format)

2. **Dual-write during transition**:
   - Save to both `step_data` and `agent_context`
   - `complete_onboarding()` reads from both

3. **Gradual migration**:
   - New users use `agent_context`
   - Old users continue with `step_data`
   - Background job migrates old data

4. **Feature flag**:
   ```python
   USE_NEW_ONBOARDING_AGENTS = os.getenv("USE_NEW_ONBOARDING_AGENTS", "false") == "true"
   ```

---

## Conclusion

### Current System Strengths

✅ Solid foundation with agent routing  
✅ JSONB storage for flexibility  
✅ Validation framework in place  
✅ Profile creation logic complete  
✅ Conversation storage working  

### Required Changes

❌ Create 5 dedicated onboarding agents  
❌ Add 3 database fields  
❌ Build plan generation services  
❌ Implement plan approval workflow  
❌ Add context handover logic  

### Effort Estimate

- **Database changes**: 1 day
- **New agents**: 2 weeks
- **Plan generation**: 1 week
- **Integration**: 1 week
- **Testing**: 1 week

**Total**: 5-6 weeks for complete implementation

### Recommendation

The current system provides a strong foundation. The main work is creating dedicated onboarding agents with specialized prompts and implementing the plan generation/approval workflow. The database schema and API structure are mostly compatible with minor additions.

**Priority order:**
1. Add database fields (quick win)
2. Create FitnessAssessmentAgent and GoalSettingAgent (prove concept)
3. Build plan generation services (core value)
4. Implement remaining agents (scale pattern)
5. Add approval workflow (polish)

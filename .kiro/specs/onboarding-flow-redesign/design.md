# Onboarding Flow Redesign - Design Document

## Overview

This document provides the technical design for implementing the 4-step onboarding flow redesign. It covers architecture, data models, API design, agent implementation, and integration points.

**Feature:** onboarding-flow-redesign  
**Status:** Design In Progress  
**Last Updated:** 2026-02-20

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  Onboarding Endpoints             │  │
│  │  - /chat                          │  │
│  │  - /generate-workout-plan         │  │
│  │  - /save-workout-plan             │  │
│  │  - /generate-meal-plan            │  │
│  │  - /save-meal-plan                │  │
│  │  - /complete                      │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │  OnboardingAgentOrchestrator     │  │
│  │  - Routes to correct agent       │  │
│  │  - Manages agent lifecycle       │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │  Specialized Agents              │  │
│  │  ┌──────────────────────────┐    │  │
│  │  │ FitnessAssessmentAgent   │    │  │
│  │  │ - save_fitness_assessment│    │  │
│  │  └──────────────────────────┘    │  │
│  │  ┌──────────────────────────┐    │  │
│  │  │ WorkoutPlanningAgent     │    │  │
│  │  │ - save_workout_constraints│   │  │
│  │  │ - generate_workout_plan   │   │  │
│  │  │ - save_workout_plan       │   │  │
│  │  └──────────────────────────┘    │  │
│  │  ┌──────────────────────────┐    │  │
│  │  │ DietPlanningAgent        │    │  │
│  │  │ - save_diet_preferences   │   │  │
│  │  │ - generate_meal_plan      │   │  │
│  │  │ - save_meal_plan          │   │  │
│  │  └──────────────────────────┘    │  │
│  │  ┌──────────────────────────┐    │  │
│  │  │ SchedulingAgent          │    │  │
│  │  │ - save_hydration_prefs    │   │  │
│  │  │ - save_supplement_prefs   │   │  │
│  │  │ - complete_onboarding     │   │  │
│  │  └──────────────────────────┘    │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │  Database Layer                  │  │
│  │  - OnboardingState               │  │
│  │  - WorkoutPlan                   │  │
│  │  - MealPlanTemplate              │  │
│  │  - UserProfile                   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│   PostgreSQL    │      │  Anthropic   │
│   Database      │      │  Claude API  │
└─────────────────┘      └──────────────┘
```

### Component Responsibilities

**Frontend:**
- Renders chat interface
- Displays generated plans
- Handles user input and approval
- Shows progress indicators

**Onboarding Endpoints:**
- Authenticate requests
- Route to orchestrator
- Return formatted responses
- Handle errors

**OnboardingAgentOrchestrator:**
- Determines current agent based on step
- Loads agent context and conversation history
- Instantiates appropriate agent
- Manages step transitions

**Specialized Agents:**
- Conduct natural conversations
- Call LLM for plan generation
- Validate user inputs
- Execute tool calls to save data
- Signal step completion

**Database Layer:**
- Persist onboarding state
- Store generated plans
- Create user profiles
- Maintain data integrity

---

## Data Models

### Database Schema


#### Existing Tables (No Changes Needed)

**workout_plans** ✅ ALREADY EXISTS
```sql
-- Current schema is perfect for new flow
-- Foreign key is to users.id, not user_profiles.id
CREATE TABLE workout_plans (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    plan_description TEXT,
    duration_weeks INTEGER NOT NULL,
    days_per_week INTEGER NOT NULL,
    plan_data JSONB,  -- ✅ Perfect for complete workout structure
    plan_rationale TEXT,
    is_locked BOOLEAN DEFAULT TRUE NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    CONSTRAINT unique_user_workout_plan UNIQUE (user_id)
);

-- Relationships to WorkoutDay and WorkoutExercise already exist
-- These can be populated later from plan_data if needed
```

**meal_plans** ✅ ALREADY EXISTS
```sql
-- Current schema is perfect - already uses grams not percentages
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    daily_calorie_target INTEGER NOT NULL,
    protein_grams DECIMAL(6,2) NOT NULL,  -- ✅ Already in grams
    carbs_grams DECIMAL(6,2) NOT NULL,
    fats_grams DECIMAL(6,2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    CONSTRAINT unique_profile_meal_plan UNIQUE (profile_id)
);
```

**All Preference Tables** ✅ ALREADY EXIST
- fitness_goals (profile_id, goal_type, target_weight_kg, target_body_fat_percentage, priority)
- physical_constraints (profile_id, constraint_type, description, severity)
- dietary_preferences (profile_id, diet_type, allergies, intolerances, dislikes)
- meal_schedules (profile_id, meal_name, scheduled_time, enable_notifications)
- workout_schedules (profile_id, day_of_week, scheduled_time, enable_notifications)
- hydration_preferences (profile_id, daily_water_target_ml, reminder_frequency_minutes, enable_notifications)

All support the new onboarding flow without modifications.

#### Tables Requiring Modifications

**meal_templates** - ADD COLUMNS FOR COMPLETE PLAN STORAGE
```sql
-- Add columns to support complete meal plan storage
ALTER TABLE meal_templates
    ADD COLUMN plan_name VARCHAR(255),
    ADD COLUMN daily_calorie_target INTEGER,
    ADD COLUMN protein_grams DECIMAL(6,2),
    ADD COLUMN carbs_grams DECIMAL(6,2),
    ADD COLUMN fats_grams DECIMAL(6,2),
    ADD COLUMN weekly_template JSONB;

-- Existing columns remain:
-- - id, profile_id, week_number, is_active
-- - generated_by, generation_reason
-- - Relationships to TemplateMeal (for backward compatibility)
```

#### Modified Tables

**onboarding_states**
```sql
-- Drop old column
ALTER TABLE onboarding_states DROP COLUMN IF EXISTS step_data;

-- Modify current_step default
ALTER TABLE onboarding_states ALTER COLUMN current_step SET DEFAULT 1;

-- Add step completion tracking
ALTER TABLE onboarding_states 
    ADD COLUMN step_1_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_2_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_3_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_4_complete BOOLEAN DEFAULT FALSE;

-- Keep existing columns:
-- - user_id
-- - current_step
-- - is_complete
-- - agent_context (JSONB)
-- - conversation_history (JSONB)
-- - agent_history (JSONB)
-- - current_agent
```

### JSONB Structures

#### workout_plans.plan_data
```json
{
  "plan_name": "6-Day Fat Loss + Muscle Building",
  "duration_weeks": 24,
  "days_per_week": 6,
  "split_type": "push_pull_legs_modified",
  "progressive_overload_strategy": "Increase weight 2.5-5% when hitting top rep range",
  "days": [
    {
      "day_number": 1,
      "name": "Chest + Triceps + Abs",
      "focus": "Upper body push",
      "estimated_duration_minutes": 70,
      "exercises": [
        {
          "order": 1,
          "name": "Barbell Bench Press",
          "type": "compound",
          "muscle_groups": ["chest", "triceps", "shoulders"],
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "tempo": "2-0-2-0",
          "notes": "Progressive overload",
          "video_url": "https://example.com/bench-press.gif"
        }
      ]
    }
  ]
}
```

#### meal_plan_templates.weekly_template
```json
{
  "daily_schedule": [
    {
      "meal_name": "Pre-Workout Snack",
      "scheduled_time": "06:00",
      "meal_type": "snack",
      "target_calories": 150,
      "target_protein": 3,
      "options": [
        {
          "option_number": 1,
          "description": "1 banana + 5 almonds + black coffee",
          "ingredients": [
            {"name": "Banana", "quantity": 1, "unit": "medium"},
            {"name": "Almonds", "quantity": 5, "unit": "pieces"}
          ],
          "calories": 150,
          "protein": 3,
          "carbs": 30,
          "fats": 3
        }
      ]
    }
  ],
  "weekly_rotation": {
    "monday": {"breakfast": "option_1", "lunch": "option_1"},
    "tuesday": {"breakfast": "option_2", "lunch": "option_2"}
  },
  "substitution_rules": [
    {
      "original": "chicken",
      "alternatives": ["turkey", "lean_beef"],
      "reason": "Protein variety"
    }
  ]
}
```

#### onboarding_states.agent_context
```json
{
  "fitness_assessment": {
    "fitness_level": "intermediate",
    "experience_years": 2,
    "primary_goal": "fat_loss",
    "secondary_goal": "muscle_gain",
    "goal_priority": "fat_loss_primary",
    "saved_at": "2026-02-20T10:30:00Z"
  },
  "workout_planning": {
    "equipment": ["gym_full"],
    "injuries": ["shoulder_minor"],
    "limitations": ["no_heavy_overhead_press"],
    "days_per_week": 6,
    "minutes_per_session": 70,
    "saved_at": "2026-02-20T10:45:00Z"
  },
  "diet_planning": {
    "diet_type": "omnivore",
    "allergies": [],
    "intolerances": ["dairy_mild"],
    "dislikes": ["fish"],
    "meal_frequency": 6,
    "saved_at": "2026-02-20T11:00:00Z"
  },
  "scheduling": {
    "daily_water_target_ml": 3000,
    "reminder_frequency_minutes": 120,
    "interested_in_supplements": true,
    "current_supplements": ["whey_protein"],
    "saved_at": "2026-02-20T11:15:00Z"
  }
}
```

---

## API Design

### Endpoint Specifications

#### POST /api/v1/onboarding/chat

**Purpose:** Send user message to current onboarding agent

**Request:**
```json
{
  "message": "I'm intermediate level, been training for 2 years",
  "step": 1  // Optional, for validation
}
```

**Response:**
```json
{
  "message": "Great! 2 years of consistent training puts you in a good position...",
  "agent_type": "fitness_assessment",
  "current_step": 1,
  "step_complete": false,
  "next_action": "continue_conversation"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 401: Unauthorized
- 404: Onboarding state not found
- 500: Server error

**Implementation:**
```python
@router.post("/chat", response_model=OnboardingChatResponse)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingChatResponse:
    orchestrator = OnboardingAgentOrchestrator(db)
    agent = await orchestrator.get_current_agent(current_user.id)
    response = await agent.process_message(request.message, current_user.id)
    
    # Save to conversation history
    await save_conversation_message(db, current_user.id, request.message, response.message)
    
    return OnboardingChatResponse(
        message=response.message,
        agent_type=response.agent_type,
        current_step=agent.current_step,
        step_complete=response.step_complete,
        next_action=response.next_action
    )
```


#### GET /api/v1/onboarding/current-step

**Purpose:** Get user's current onboarding step and completion status

**Response:**
```json
{
  "current_step": 2,
  "agent_type": "workout_planning",
  "step_1_complete": true,
  "step_2_complete": false,
  "step_3_complete": false,
  "step_4_complete": false,
  "is_complete": false
}
```

#### POST /api/v1/onboarding/generate-workout-plan

**Purpose:** Generate workout plan based on saved constraints

**Request:**
```json
{
  "constraints": {  // Optional, uses saved if not provided
    "equipment": ["gym_full"],
    "injuries": ["shoulder_minor"],
    "days_per_week": 6
  }
}
```

**Response:**
```json
{
  "plan": {
    "plan_name": "6-Day Fat Loss + Muscle Building",
    "duration_weeks": 24,
    "days": [...]  // Full plan structure
  },
  "generation_time_seconds": 8.5
}
```

#### POST /api/v1/onboarding/save-workout-plan

**Purpose:** Save user-approved workout plan

**Request:**
```json
{
  "plan_data": {
    "plan_name": "6-Day Fat Loss + Muscle Building",
    "duration_weeks": 24,
    "days": [...]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Workout plan saved successfully",
  "plan_id": "uuid",
  "next_step": 3
}
```

#### POST /api/v1/onboarding/generate-meal-plan

**Purpose:** Generate meal plan based on saved preferences

**Request:**
```json
{
  "preferences": {  // Optional, uses saved if not provided
    "diet_type": "omnivore",
    "meal_frequency": 6
  }
}
```

**Response:**
```json
{
  "plan": {
    "plan_name": "High Protein Fat Loss",
    "daily_calorie_target": 2200,
    "daily_schedule": [...]  // Full plan structure
  },
  "generation_time_seconds": 12.3
}
```

#### POST /api/v1/onboarding/save-meal-plan

**Purpose:** Save user-approved meal plan

**Request:**
```json
{
  "plan_data": {
    "plan_name": "High Protein Fat Loss",
    "daily_calorie_target": 2200,
    "daily_schedule": [...],
    "weekly_template": {...}
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Meal plan saved successfully",
  "plan_id": "uuid",
  "next_step": 4
}
```

#### POST /api/v1/onboarding/complete

**Purpose:** Complete onboarding and create user profile

**Response:**
```json
{
  "profile_id": "uuid",
  "user_id": "uuid",
  "fitness_level": "intermediate",
  "is_locked": true,
  "onboarding_complete": true,
  "message": "Onboarding completed successfully!"
}
```

---

## Agent Implementation

### Agent Base Class

```python
class BaseOnboardingAgent(ABC):
    """Base class for all onboarding agents."""
    
    def __init__(self, db: AsyncSession, context: OnboardingAgentContext):
        self.db = db
        self.context = context
        self.llm = get_llm_client()
    
    @abstractmethod
    async def process_message(self, message: str, user_id: UUID) -> AgentResponse:
        """Process user message and return response."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get agent-specific system prompt."""
        pass
    
    async def call_llm(self, messages: List[Dict]) -> str:
        """Call LLM with conversation history."""
        system_prompt = self.get_system_prompt()
        response = await self.llm.chat(
            system=system_prompt,
            messages=messages
        )
        return response.content
```

### Fitness Assessment Agent

```python
class FitnessAssessmentAgent(BaseOnboardingAgent):
    """Handles Step 1: Fitness level and goals."""
    
    def get_system_prompt(self) -> str:
        return """You are a fitness assessment specialist helping users define 
        their fitness level and goals. Be friendly, encouraging, and thorough.
        
        Your tasks:
        1. Determine fitness level (beginner/intermediate/advanced)
        2. Understand training experience
        3. Identify primary and secondary goals
        4. Clarify goal priorities
        
        When you have all information, call save_fitness_assessment tool."""
    
    async def process_message(self, message: str, user_id: UUID) -> AgentResponse:
        # Add message to conversation history
        self.context.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Call LLM with tools
        response = await self.call_llm_with_tools(
            messages=self.context.conversation_history,
            tools=[self.save_fitness_assessment]
        )
        
        # Check if tool was called
        if response.tool_calls:
            tool_result = await self.execute_tool(response.tool_calls[0])
            return AgentResponse(
                message=response.content,
                agent_type="fitness_assessment",
                step_complete=True,
                next_action="advance_step",
                context_update=tool_result
            )
        
        return AgentResponse(
            message=response.content,
            agent_type="fitness_assessment",
            step_complete=False,
            next_action="continue_conversation"
        )
    
    async def save_fitness_assessment(
        self,
        fitness_level: str,
        experience_years: int,
        primary_goal: str,
        secondary_goal: str = None,
        goal_priority: str = None
    ) -> Dict:
        """Tool: Save fitness assessment data."""
        # Validate inputs
        valid_levels = ["beginner", "intermediate", "advanced"]
        if fitness_level not in valid_levels:
            raise ValueError(f"Invalid fitness level: {fitness_level}")
        
        valid_goals = ["fat_loss", "muscle_gain", "general_fitness"]
        if primary_goal not in valid_goals:
            raise ValueError(f"Invalid goal: {primary_goal}")
        
        # Save to agent_context
        data = {
            "fitness_level": fitness_level,
            "experience_years": experience_years,
            "primary_goal": primary_goal,
            "secondary_goal": secondary_goal,
            "goal_priority": goal_priority,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update database
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == self.context.user_id)
            .values(
                agent_context=func.jsonb_set(
                    OnboardingState.agent_context,
                    ["fitness_assessment"],
                    data
                ),
                step_1_complete=True,
                current_step=2
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return data
```

### Workout Planning Agent

```python
class WorkoutPlanningAgent(BaseOnboardingAgent):
    """Handles Step 2: Workout constraints and plan generation."""
    
    def __init__(self, db: AsyncSession, context: OnboardingAgentContext):
        super().__init__(db, context)
        self.workout_generator = WorkoutPlanGenerator()  # Existing service!
    
    def get_system_prompt(self) -> str:
        return """You are a workout planning specialist. Your job is to:
        1. Gather workout constraints (equipment, injuries, time availability)
        2. Generate a COMPLETE workout plan using the workout generator
        3. Present the plan to the user with full details
        4. Handle modification requests
        5. Get user approval
        6. Collect workout schedule (days and times)
        7. Save the approved plan
        
        Use the user's fitness level and goals from step 1.
        Be specific with exercises, sets, reps, and rest periods.
        
        When presenting the plan, format it clearly with:
        - Weekly split structure
        - Each day's exercises with sets/reps/rest
        - Progressive overload strategy
        - Estimated duration
        
        After user approves, ask for workout schedule (which days and times)."""
    
    async def generate_workout_plan(
        self,
        equipment: List[str],
        injuries: List[str],
        limitations: List[str],
        days_per_week: int,
        minutes_per_session: int,
        location: str = "gym"
    ) -> Dict:
        """Tool: Generate workout plan using WorkoutPlanGenerator service."""
        # Get fitness data from context
        fitness_data = self.context.agent_context.get("fitness_assessment", {})
        
        # Use existing WorkoutPlanGenerator service
        plan = await self.workout_generator.generate_plan(
            fitness_level=fitness_data.get("fitness_level"),
            primary_goal=fitness_data.get("primary_goal"),
            frequency=days_per_week,
            location=location,
            duration_minutes=minutes_per_session,
            equipment=equipment,
            limitations=injuries + limitations
        )
        
        # Convert to dict for JSON serialization
        return plan.model_dump()
    
    async def modify_workout_plan(
        self,
        current_plan: Dict,
        modifications: Dict
    ) -> Dict:
        """Tool: Modify existing workout plan based on user feedback."""
        # Use existing WorkoutPlanGenerator service
        modified_plan = await self.workout_generator.modify_plan(
            current_plan=current_plan,
            modifications=modifications
        )
        
        return modified_plan.model_dump()
    
    async def save_workout_plan(
        self,
        plan_data: Dict,
        workout_days: List[str],
        workout_times: List[str]
    ) -> Dict:
        """Tool: Save approved workout plan and schedule."""
        # Validate plan structure
        required_fields = ["frequency", "duration_minutes", "location", "equipment", 
                          "training_split", "workout_days", "progression_strategy"]
        for field in required_fields:
            if field not in plan_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate schedule
        if len(workout_days) != len(workout_times):
            raise ValueError("Workout days and times must have same length")
        
        # Save to agent_context
        workout_context = {
            "plan": plan_data,
            "schedule": {
                "days": workout_days,
                "times": workout_times
            },
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update onboarding state
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == self.context.user_id)
            .values(
                agent_context=func.jsonb_set(
                    OnboardingState.agent_context,
                    ["workout_planning"],
                    workout_context
                ),
                step_2_complete=True,
                current_step=3
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return {"saved": True, "next_step": 3}
```

### Diet Planning Agent

```python
class DietPlanningAgent(BaseOnboardingAgent):
    """Handles Step 3: Diet preferences and meal plan generation."""
    
    def __init__(self, db: AsyncSession, context: OnboardingAgentContext):
        super().__init__(db, context)
        self.meal_generator = MealPlanGenerator()  # Existing service!
    
    def get_system_prompt(self) -> str:
        return """You are a nutrition planning specialist. Your job is to:
        1. Gather dietary preferences (diet type, allergies, dislikes)
        2. Ask about meal frequency and prep willingness
        3. Generate a COMPLETE meal plan using the meal generator
        4. Present the plan with sample meals, macros, and timing
        5. Handle modification requests
        6. Get user approval
        7. Collect meal schedule (meal times)
        8. Save the approved plan
        
        Use the user's fitness level, goals, and workout plan from previous steps.
        
        When presenting the plan, format it clearly with:
        - Daily calorie target
        - Macro breakdown (protein/carbs/fats in grams)
        - Sample meals for each time slot
        - Meal timing suggestions
        - Weekly rotation ideas
        
        After user approves, ask for specific meal times."""
    
    async def generate_meal_plan(
        self,
        diet_type: str,
        allergies: List[str],
        dislikes: List[str],
        meal_frequency: int,
        meal_prep_level: str = "medium"
    ) -> Dict:
        """Tool: Generate meal plan using MealPlanGenerator service."""
        # Get fitness and workout data from context
        fitness_data = self.context.agent_context.get("fitness_assessment", {})
        workout_data = self.context.agent_context.get("workout_planning", {})
        workout_plan = workout_data.get("plan", {})
        
        # Use existing MealPlanGenerator service
        plan = await self.meal_generator.generate_plan(
            fitness_level=fitness_data.get("fitness_level"),
            primary_goal=fitness_data.get("primary_goal"),
            workout_plan=workout_plan,
            diet_type=diet_type,
            allergies=allergies,
            dislikes=dislikes,
            meal_frequency=meal_frequency,
            meal_prep_level=meal_prep_level
        )
        
        # Convert to dict for JSON serialization
        return plan.model_dump()
    
    async def modify_meal_plan(
        self,
        current_plan: Dict,
        modifications: Dict
    ) -> Dict:
        """Tool: Modify existing meal plan based on user feedback."""
        # Use existing MealPlanGenerator service
        modified_plan = await self.meal_generator.modify_plan(
            current_plan=current_plan,
            modifications=modifications
        )
        
        return modified_plan.model_dump()
    
    async def save_meal_plan(
        self,
        plan_data: Dict,
        meal_times: Dict[str, str]
    ) -> Dict:
        """Tool: Save approved meal plan and schedule."""
        # Validate plan structure
        required_fields = ["diet_type", "meal_frequency", "daily_calories", 
                          "protein_g", "carbs_g", "fats_g", "sample_meals"]
        for field in required_fields:
            if field not in plan_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate meal times count matches frequency
        if len(meal_times) != plan_data["meal_frequency"]:
            raise ValueError(f"Meal times count must match meal frequency")
        
        # Save to agent_context
        diet_context = {
            "plan": plan_data,
            "schedule": meal_times,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update onboarding state
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == self.context.user_id)
            .values(
                agent_context=func.jsonb_set(
                    OnboardingState.agent_context,
                    ["diet_planning"],
                    diet_context
                ),
                step_3_complete=True,
                current_step=4
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return {"saved": True, "next_step": 4}
```

### Scheduling Agent

```python
class SchedulingAgent(BaseOnboardingAgent):
    """Handles Step 4: Hydration and supplement preferences."""
    
    def get_system_prompt(self) -> str:
        return """You are a lifestyle optimization specialist. Your job is to:
        1. Discuss hydration importance based on their activity level
        2. Set up hydration reminders (frequency and daily target)
        3. Ask about interest in supplement guidance
        4. Provide educational information about supplements (NO prescriptions)
        5. Save preferences
        
        Be informative but never prescriptive. Supplements are optional guidance only.
        
        After collecting preferences, inform user that onboarding is complete
        and they can now access their personalized dashboard."""
    
    async def save_hydration_preferences(
        self,
        daily_water_target_ml: int,
        reminder_frequency_hours: int,
        enable_reminders: bool = True
    ) -> Dict:
        """Tool: Save hydration preferences."""
        # Validate inputs
        if not (1500 <= daily_water_target_ml <= 5000):
            raise ValueError("Daily water target must be between 1500-5000ml")
        
        if not (1 <= reminder_frequency_hours <= 4):
            raise ValueError("Reminder frequency must be between 1-4 hours")
        
        # Save to agent_context
        hydration_data = {
            "daily_water_target_ml": daily_water_target_ml,
            "reminder_frequency_hours": reminder_frequency_hours,
            "enable_reminders": enable_reminders,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update onboarding state
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == self.context.user_id)
            .values(
                agent_context=func.jsonb_set(
                    OnboardingState.agent_context,
                    ["scheduling", "hydration"],
                    hydration_data
                )
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return hydration_data
    
    async def save_supplement_preferences(
        self,
        interested_in_supplements: bool,
        current_supplements: List[str] = None
    ) -> Dict:
        """Tool: Save supplement preferences."""
        supplement_data = {
            "interested_in_supplements": interested_in_supplements,
            "current_supplements": current_supplements or [],
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update onboarding state
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == self.context.user_id)
            .values(
                agent_context=func.jsonb_set(
                    OnboardingState.agent_context,
                    ["scheduling", "supplements"],
                    supplement_data
                ),
                step_4_complete=True
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return {"saved": True, "onboarding_ready_to_complete": True}
```

---

## Agent Orchestrator Updates

### Updated Step-to-Agent Mapping

```python
class OnboardingAgentOrchestrator:
    """Orchestrates onboarding agents based on current step."""
    
    def _step_to_agent(self, step: int) -> OnboardingAgentType:
        """Map onboarding step number to agent type (NEW 4-STEP FLOW)."""
        if step < 1 or step > 4:
            raise ValueError(f"Invalid onboarding step: {step}")
        
        # NEW MAPPING
        if step == 1:
            return OnboardingAgentType.FITNESS_ASSESSMENT
        elif step == 2:
            return OnboardingAgentType.WORKOUT_PLANNING
        elif step == 3:
            return OnboardingAgentType.DIET_PLANNING
        else:  # step 4
            return OnboardingAgentType.SCHEDULING
    
    async def _create_agent(
        self,
        agent_type: OnboardingAgentType,
        context_dict: dict,
        user_id: UUID
    ) -> BaseOnboardingAgent:
        """Factory method to create agent instance."""
        # Load conversation history
        conversation_history = await self._load_conversation_history(user_id)
        
        # Create context
        context = OnboardingAgentContext(
            user_id=str(user_id),
            conversation_history=conversation_history,
            agent_context=context_dict
        )
        
        # Instantiate agent (REMOVED GoalSettingAgent)
        agent_classes = {
            OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
            OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
            OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
            OnboardingAgentType.SCHEDULING: SchedulingAgent,
        }
        
        agent_class = agent_classes[agent_type]
        return agent_class(self.db, context)
```



---

## Profile Creation Service

### ProfileCreationService Integration

The existing `ProfileCreationService` reads from `agent_context` and creates all related entities. No changes needed!

```python
class ProfileCreationService:
    """Creates user profile from onboarding agent_context."""
    
    async def create_profile_from_agent_context(
        self,
        user_id: UUID,
        agent_context: Dict
    ) -> UserProfile:
        """
        Create complete user profile from agent_context.
        
        Reads data from:
        - agent_context["fitness_assessment"]
        - agent_context["workout_planning"]
        - agent_context["diet_planning"]
        - agent_context["scheduling"]
        
        Creates:
        - UserProfile
        - FitnessGoal records
        - PhysicalConstraint records
        - DietaryPreference record
        - WorkoutPlan record (from workout_planning.plan)
        - MealPlanTemplate record (from diet_planning.plan)
        - WorkoutSchedule records (from workout_planning.schedule)
        - MealSchedule records (from diet_planning.schedule)
        - HydrationPreference record
        - UserProfileVersion snapshot
        """
        # Validate all required data present
        self._validate_agent_context(agent_context)
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            fitness_level=agent_context["fitness_assessment"]["fitness_level"],
            is_locked=True,
            locked_at=datetime.now(timezone.utc)
        )
        self.db.add(profile)
        await self.db.flush()  # Get profile.id
        
        # Create fitness goals
        await self._create_fitness_goals(profile.id, agent_context["fitness_assessment"])
        
        # Create physical constraints
        await self._create_physical_constraints(profile.id, agent_context["workout_planning"])
        
        # Create dietary preferences
        await self._create_dietary_preferences(profile.id, agent_context["diet_planning"])
        
        # Create workout plan
        await self._create_workout_plan(user_id, agent_context["workout_planning"])
        
        # Create meal plan
        await self._create_meal_plan(profile.id, agent_context["diet_planning"])
        
        # Create schedules
        await self._create_workout_schedules(profile.id, agent_context["workout_planning"]["schedule"])
        await self._create_meal_schedules(profile.id, agent_context["diet_planning"]["schedule"])
        
        # Create hydration preferences
        await self._create_hydration_preferences(profile.id, agent_context["scheduling"]["hydration"])
        
        # Create profile version snapshot
        await self._create_profile_version(profile.id, agent_context)
        
        await self.db.commit()
        return profile
```

---

## Database Migration

### Fresh Start Approach

Since this is a local development environment with no production data to preserve, we'll use a **fresh start approach**:

1. **Reset Database**: Drop all tables and clear migration history
2. **Update Models**: Modify SQLAlchemy models with new schema
3. **Create Initial Migration**: Generate complete schema from models
4. **Apply Migration**: Create all tables fresh

### Database Reset Process

```bash
# 1. Reset database (drops all tables)
cd backend
poetry run python scripts/reset_db.py

# 2. Delete old migration files
# Manually delete all files in backend/alembic/versions/ except __init__.py

# 3. Update SQLAlchemy models
# Edit backend/app/models/onboarding.py
# Edit backend/app/models/meal_template.py

# 4. Create initial migration
poetry run alembic revision --autogenerate -m "initial schema with 4-step onboarding"

# 5. Apply migration
poetry run alembic upgrade head

# 6. Verify tables created
poetry run python scripts/check_db.py
```

### Updated Models

**OnboardingState Model** (`backend/app/models/onboarding.py`):
```python
class OnboardingState(Base):
    __tablename__ = "onboarding_states"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    current_step = Column(Integer, nullable=False, default=1)  # Changed from 0 to 1
    is_complete = Column(Boolean, default=False, nullable=False)
    
    # Step completion tracking (NEW)
    step_1_complete = Column(Boolean, default=False, nullable=False)
    step_2_complete = Column(Boolean, default=False, nullable=False)
    step_3_complete = Column(Boolean, default=False, nullable=False)
    step_4_complete = Column(Boolean, default=False, nullable=False)
    
    # JSONB fields for agent data
    agent_context = Column(JSONB, nullable=True)
    conversation_history = Column(JSONB, nullable=True)
    agent_history = Column(JSONB, nullable=True)
    current_agent = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="onboarding_state")
```

**MealTemplate Model** (`backend/app/models/meal_template.py`):
```python
class MealTemplate(Base):
    __tablename__ = "meal_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # NEW: Complete meal plan storage
    plan_name = Column(String(255), nullable=True)
    daily_calorie_target = Column(Integer, nullable=True)
    protein_grams = Column(Numeric(6, 2), nullable=True)
    carbs_grams = Column(Numeric(6, 2), nullable=True)
    fats_grams = Column(Numeric(6, 2), nullable=True)
    weekly_template = Column(JSONB, nullable=True)
    
    # Existing fields
    generated_by = Column(String(50), nullable=True)
    generation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_templates")
    template_meals = relationship("TemplateMeal", back_populates="meal_template", cascade="all, delete-orphan")
```

### No Backward Compatibility Needed

Since we're starting fresh:
- ✅ No data migration required
- ✅ No backward compatibility concerns
- ✅ Clean schema from the start
- ✅ Simpler implementation

### Production Deployment Note

For production deployment, coordinate with the team:
1. Schedule maintenance window
2. Backup existing data if needed
3. Reset production database
4. Apply fresh migration
5. Users will need to re-onboard (communicate this clearly)

---

## Testing Strategy

### Unit Tests

**Test Coverage Requirements**: 80%+ for all new/modified code

#### Agent Tests

```python
# tests/test_agents/test_fitness_assessment_agent.py
@pytest.mark.asyncio
async def test_fitness_assessment_saves_data(db_session, test_user):
    """Test that fitness assessment agent saves data correctly."""
    context = OnboardingAgentContext(
        user_id=str(test_user.id),
        conversation_history=[],
        agent_context={}
    )
    
    agent = FitnessAssessmentAgent(db_session, context)
    
    # Call save tool
    result = await agent.save_fitness_assessment(
        fitness_level="intermediate",
        experience_years=2,
        primary_goal="fat_loss",
        secondary_goal="muscle_gain",
        goal_priority="fat_loss_primary"
    )
    
    # Verify data saved
    assert result["fitness_level"] == "intermediate"
    assert result["experience_years"] == 2
    
    # Verify database updated
    stmt = select(OnboardingState).where(OnboardingState.user_id == test_user.id)
    state = (await db_session.execute(stmt)).scalar_one()
    assert state.step_1_complete is True
    assert state.current_step == 2
    assert state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"


# tests/test_agents/test_workout_planning_agent.py
@pytest.mark.asyncio
async def test_workout_plan_generation(db_session, test_user_with_fitness_data):
    """Test that workout planning agent generates complete plans."""
    context = OnboardingAgentContext(
        user_id=str(test_user_with_fitness_data.id),
        conversation_history=[],
        agent_context={
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "primary_goal": "fat_loss"
            }
        }
    )
    
    agent = WorkoutPlanningAgent(db_session, context)
    
    # Generate plan
    plan = await agent.generate_workout_plan(
        equipment=["gym_full"],
        injuries=[],
        limitations=[],
        days_per_week=4,
        minutes_per_session=60,
        location="gym"
    )
    
    # Verify plan structure
    assert "frequency" in plan
    assert "workout_days" in plan
    assert plan["frequency"] == 4
    assert len(plan["workout_days"]) > 0
    
    # Verify exercises have required fields
    first_day = plan["workout_days"][0]
    assert "exercises" in first_day
    first_exercise = first_day["exercises"][0]
    assert all(key in first_exercise for key in ["name", "sets", "reps", "rest_seconds"])
```

#### Service Tests

```python
# tests/test_services/test_workout_plan_generator.py
@pytest.mark.asyncio
async def test_workout_generator_creates_valid_plan():
    """Test WorkoutPlanGenerator creates valid plans."""
    generator = WorkoutPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="beginner",
        primary_goal="muscle_gain",
        frequency=3,
        location="home",
        duration_minutes=45,
        equipment=["dumbbells"],
        limitations=[]
    )
    
    # Verify plan structure
    assert plan.frequency == 3
    assert plan.location == "home"
    assert len(plan.workout_days) == 3
    assert plan.training_split == "Full Body"
    
    # Verify exercises are appropriate for home
    for day in plan.workout_days:
        for exercise in day.exercises:
            assert "barbell" not in exercise.name.lower()  # No barbells at home


# tests/test_services/test_meal_plan_generator.py
@pytest.mark.asyncio
async def test_meal_generator_respects_allergies():
    """Test MealPlanGenerator respects dietary restrictions."""
    generator = MealPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal="fat_loss",
        workout_plan={"frequency": 4},
        diet_type="vegetarian",
        allergies=["dairy"],
        dislikes=["mushrooms"],
        meal_frequency=4,
        meal_prep_level="medium"
    )
    
    # Verify no dairy in sample meals
    for meal in plan.sample_meals:
        ingredients_str = " ".join(meal.ingredients).lower()
        assert "dairy" not in ingredients_str
        assert "milk" not in ingredients_str
        assert "cheese" not in ingredients_str
        assert "mushroom" not in ingredients_str
```

### Integration Tests

```python
# tests/test_integration/test_onboarding_flow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_onboarding_flow(authenticated_client, db_session):
    """Test complete 4-step onboarding flow end-to-end."""
    client, user = authenticated_client
    
    # Step 1: Fitness Assessment
    response = await client.post("/api/v1/onboarding/chat", json={
        "message": "I'm intermediate level, been training for 2 years. My goal is fat loss."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "fitness_assessment"
    
    # Continue conversation until step complete
    # ... (multiple chat exchanges)
    
    # Verify step 1 complete
    response = await client.get("/api/v1/onboarding/current-step")
    data = response.json()
    assert data["step_1_complete"] is True
    assert data["current_step"] == 2
    
    # Step 2: Workout Planning
    # ... (chat to collect constraints)
    # ... (generate plan)
    # ... (approve plan)
    
    # Step 3: Diet Planning
    # ... (chat to collect preferences)
    # ... (generate meal plan)
    # ... (approve plan)
    
    # Step 4: Scheduling
    # ... (set hydration preferences)
    
    # Complete onboarding
    response = await client.post("/api/v1/onboarding/complete")
    assert response.status_code == 201
    data = response.json()
    assert data["onboarding_complete"] is True
    assert "profile_id" in data
    
    # Verify profile created
    profile_id = UUID(data["profile_id"])
    stmt = select(UserProfile).where(UserProfile.id == profile_id)
    profile = (await db_session.execute(stmt)).scalar_one()
    assert profile.is_locked is True
    assert profile.fitness_level == "intermediate"
```

### Property-Based Tests

```python
# tests/test_properties/test_workout_plan_properties.py
from hypothesis import given, strategies as st

@given(
    frequency=st.integers(min_value=2, max_value=7),
    duration=st.integers(min_value=20, max_value=180)
)
@pytest.mark.asyncio
async def test_workout_plan_always_valid(frequency, duration):
    """Property: Generated workout plans are always valid."""
    generator = WorkoutPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal="general_fitness",
        frequency=frequency,
        location="gym",
        duration_minutes=duration,
        equipment=["gym_full"],
        limitations=[]
    )
    
    # Property: Plan frequency matches input
    assert plan.frequency == frequency
    
    # Property: All workout days have exercises
    assert len(plan.workout_days) > 0
    for day in plan.workout_days:
        assert len(day.exercises) > 0
    
    # Property: All exercises have valid sets/reps
    for day in plan.workout_days:
        for exercise in day.exercises:
            assert exercise.sets > 0
            assert exercise.rest_seconds >= 0


# tests/test_properties/test_meal_plan_properties.py
@given(
    meal_frequency=st.integers(min_value=2, max_value=6)
)
@pytest.mark.asyncio
async def test_meal_plan_macros_sum_to_calories(meal_frequency):
    """Property: Meal plan macros always sum to approximately target calories."""
    generator = MealPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        workout_plan={"frequency": 4},
        diet_type="omnivore",
        allergies=[],
        dislikes=[],
        meal_frequency=meal_frequency,
        meal_prep_level="medium"
    )
    
    # Property: Macros sum to calories within 10% tolerance
    calculated_calories = (plan.protein_g * 4) + (plan.carbs_g * 4) + (plan.fats_g * 9)
    tolerance = plan.daily_calories * 0.1
    assert abs(calculated_calories - plan.daily_calories) <= tolerance
    
    # Property: Sample meals count matches frequency
    assert len(plan.sample_meals) >= 3  # At least 3 sample meals
```

---

## Error Handling

### Error Types and Responses

```python
class OnboardingError(Exception):
    """Base exception for onboarding errors."""
    pass

class OnboardingValidationError(OnboardingError):
    """Raised when validation fails."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class OnboardingIncompleteError(OnboardingError):
    """Raised when trying to complete with missing data."""
    pass

class PlanGenerationError(OnboardingError):
    """Raised when plan generation fails."""
    pass
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid fitness level",
    "field": "fitness_level",
    "details": {
      "valid_values": ["beginner", "intermediate", "advanced"]
    }
  }
}
```

### Error Handling in Endpoints

```python
@router.post("/chat")
async def chat_onboarding(...):
    try:
        # Process message
        response = await agent.process_message(message)
        return response
    except OnboardingValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.message,
                "field": e.field
            }
        )
    except PlanGenerationError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "PLAN_GENERATION_ERROR",
                "message": "Failed to generate plan. Please try again.",
                "retry_after": 5
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )
```

---

## Performance Considerations

### Response Time Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Chat message | < 3s | LLM call included |
| Generate workout plan | < 10s | Uses WorkoutPlanGenerator |
| Generate meal plan | < 15s | Uses MealPlanGenerator |
| Save plan | < 500ms | Database write |
| Complete onboarding | < 2s | Creates all entities |

### Optimization Strategies

1. **Caching**:
   - Cache common plan templates
   - Cache LLM responses for similar inputs
   - Use Redis for session state

2. **Async Operations**:
   - All database operations use async/await
   - Parallel tool execution where possible
   - Background tasks for non-critical operations

3. **Database Optimization**:
   - Indexes on user_id, current_step
   - JSONB GIN indexes on agent_context
   - Connection pooling

4. **LLM Optimization**:
   - Streaming responses for long generations
   - Prompt caching for system prompts
   - Fallback to simpler models for validation

---

## Security Considerations

### Authentication & Authorization

- All endpoints require JWT authentication
- User can only access their own onboarding state
- Rate limiting: 60 requests/minute per user
- Plan generation rate limit: 5 per minute per user

### Data Validation

- All user inputs validated before LLM calls
- SQL injection prevention via parameterized queries
- XSS prevention via input sanitization
- JSONB injection prevention

### Privacy

- Conversation history encrypted at rest
- PII handling compliant with GDPR
- User can request data deletion
- Audit log for all profile changes

---

## Monitoring & Observability

### Metrics to Track

```python
# Prometheus metrics
onboarding_step_duration = Histogram(
    'onboarding_step_duration_seconds',
    'Time spent on each onboarding step',
    ['step_number']
)

onboarding_completion_rate = Counter(
    'onboarding_completions_total',
    'Total onboarding completions',
    ['completion_status']  # success, abandoned, error
)

plan_generation_duration = Histogram(
    'plan_generation_duration_seconds',
    'Time to generate plans',
    ['plan_type']  # workout, meal
)

plan_modification_count = Counter(
    'plan_modifications_total',
    'Number of plan modifications requested',
    ['plan_type', 'modification_type']
)
```

### Logging Strategy

```python
# Structured logging
logger.info(
    "Onboarding step completed",
    extra={
        "user_id": str(user_id),
        "step": step_number,
        "duration_seconds": duration,
        "agent_type": agent_type,
        "modifications_requested": modification_count
    }
)
```

### Alerts

- Alert if completion rate drops below 80%
- Alert if average step duration exceeds 5 minutes
- Alert if plan generation fails > 5% of requests
- Alert if database write latency > 1s

---

## Deployment Strategy

### Phase 1: Development (Week 1-2)
- Implement database migration
- Update agent orchestrator
- Implement FitnessAssessmentAgent
- Implement WorkoutPlanningAgent

### Phase 2: Core Implementation (Week 3-4)
- Implement DietPlanningAgent
- Implement SchedulingAgent
- Update API endpoints
- Write unit tests

### Phase 3: Integration & Testing (Week 5)
- Integration testing
- Property-based testing
- Performance testing
- Bug fixes

### Phase 4: Staging Deployment (Week 6)
- Deploy to staging environment
- Internal testing
- User acceptance testing
- Prompt refinement

### Phase 5: Production Rollout (Week 7-8)
- Feature flag enabled for 10% of users
- Monitor metrics closely
- Gradual rollout to 25%, 50%, 100%
- A/B test against old flow

### Rollback Plan

If completion rate drops below 70% or critical bugs found:
1. Disable feature flag immediately
2. Route all users to old flow
3. Investigate and fix issues
4. Re-test in staging
5. Gradual re-rollout

---

## Success Criteria

### Technical Success

- ✅ All tests pass (unit, integration, property-based)
- ✅ Code coverage > 80%
- ✅ API response times meet targets
- ✅ Zero data loss during migration
- ✅ No critical bugs in production

### User Success

- ✅ Onboarding completion rate > 85%
- ✅ Average completion time < 25 minutes
- ✅ User satisfaction score > 4.2/5
- ✅ Plan modification rate < 30%
- ✅ Week 1 engagement > 70%

### Business Success

- ✅ Increased user retention
- ✅ Reduced support tickets
- ✅ Positive user feedback
- ✅ Higher plan adherence rates

---

## Appendix

### A. Agent Prompt Templates

See `backend/app/agents/onboarding/prompts/` for full prompt templates.

### B. API Response Schemas

See `backend/app/schemas/onboarding.py` for complete Pydantic schemas.

### C. Database Schema Diagrams

See `docs/technichal/Onboarding_Schema_Analysis.md` for detailed schema analysis.

### D. Migration Scripts

See `backend/alembic/versions/` for complete migration scripts.

---

**Document Status**: Complete  
**Last Updated**: 2026-02-20  
**Next Review**: After implementation Phase 1


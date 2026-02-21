# Design Document

## Overview

The Scheduling Agent & Onboarding Completion feature implements the final specialized onboarding agent that collects workout, meal, and hydration schedules, then completes the onboarding flow by creating a locked UserProfile from all collected agent context. This marks the transition from conversational onboarding to the post-onboarding state where users interact with the General Assistant Agent.

This design builds on the foundation established in Specs 1-3 (Onboarding Agent Foundation, Fitness & Goal Agents, Planning Agents) to complete the four-agent onboarding system. The key innovation is the profile creation service that atomically transforms agent_context data into a complete, locked UserProfile with all related database entities.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Onboarding Flow                          │
│  Steps 1-2    Step 3      Steps 4-5       Steps 6-7   Steps 8-9 │
│  Fitness   → Goal     → Workout      → Diet       → Scheduling │
│  Assessment  Setting    Planning       Planning      Agent     │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Onboarding Completion    │
                    │ Verification             │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ Profile Creation Service │
                    │ (Atomic Transaction)     │
                    └──────────┬───────────────┘
                               │
                               ▼
              ┌────────────────┴────────────────┐
              │                                  │
              ▼                                  ▼
    ┌─────────────────┐              ┌──────────────────┐
    │  UserProfile    │              │  Related Entities│
    │  (is_locked=T)  │              │  - FitnessGoal   │
    └─────────────────┘              │  - MealPlan      │
                                     │  - WorkoutPlan   │
                                     │  - Schedules     │
                                     └──────────────────┘
                                              │
                                              ▼
                                   ┌──────────────────┐
                                   │ General Assistant│
                                   │ Agent (Read-Only)│
                                   └──────────────────┘
```

### Data Flow

1. **Schedule Collection**: Scheduling Agent collects workout days/times, meal times, and hydration preferences
2. **Context Storage**: Agent tools save schedule data to agent_context["scheduling"]
3. **Completion Trigger**: When all schedules are saved, agent signals onboarding completion
4. **Verification**: System verifies all 5 agents have completed their steps
5. **Profile Creation**: ProfileCreationService extracts data from agent_context and creates UserProfile
6. **Entity Creation**: Service creates all related entities (goals, plans, schedules) in atomic transaction
7. **Profile Locking**: UserProfile.is_locked set to True to prevent casual modifications
8. **State Transition**: OnboardingState.is_complete set to True, current_agent set to "general_assistant"

## Components and Interfaces

### 1. Scheduling Agent

**Purpose**: Collect workout, meal, and hydration schedules through conversational interaction

**Class**: `SchedulingAgent(BaseOnboardingAgent)`

**Attributes**:
- `agent_type`: "scheduling"
- `db`: AsyncSession for database operations
- `context`: dict containing agent_context from previous agents
- `llm`: ChatAnthropic instance for natural language processing

**Methods**:
```python
async def process_message(self, message: str, user_id: UUID) -> AgentResponse:
    """Process user message about scheduling preferences"""
    
async def get_system_prompt(self) -> str:
    """Return system prompt with workout_plan and meal_plan context"""
    
def get_tools(self) -> List:
    """Return scheduling-specific tools"""
```

**System Prompt Template**:
```
You are a Scheduling Agent helping users set up their daily routines.

Context from previous steps:
- Workout Plan: {workout_plan_summary}
- Meal Plan: {meal_plan_summary}

Your role:
- Set workout days and times based on user's availability
- Set meal timing for each meal in the meal plan
- Configure hydration reminders
- Ensure schedule is realistic and sustainable

Guidelines:
- Consider their daily routine and constraints
- Suggest optimal timing based on goals and workout plan
- Be flexible with timing preferences
- Explain importance of consistency in scheduling
- Call save tools when user confirms schedule information
```

### 2. Scheduling Agent Tools

**Tool 1: save_workout_schedule**

```python
@tool
async def save_workout_schedule(
    days: List[str],
    times: List[str],
    user_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Save workout schedule to agent context.
    
    Args:
        days: List of day names (e.g., ["Monday", "Wednesday", "Friday"])
        times: List of times in HH:MM format (e.g., ["07:00", "07:00", "18:00"])
        user_id: User ID
        db: Database session
    
    Returns:
        Success status and message
    
    Validation:
        - days must be valid day names (Monday-Sunday)
        - times must be in HH:MM format
        - len(days) must equal len(times)
        - times must be between 00:00 and 23:59
    """
```

**Tool 2: save_meal_schedule**

```python
@tool
async def save_meal_schedule(
    meal_times: Dict[str, str],
    user_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Save meal schedule to agent context.
    
    Args:
        meal_times: Dict mapping meal names to times
                   (e.g., {"breakfast": "08:00", "lunch": "13:00", "dinner": "19:00"})
        user_id: User ID
        db: Database session
    
    Returns:
        Success status and message
    
    Validation:
        - All times must be in HH:MM format
        - Number of meals must match meal_frequency from meal_plan
        - Times must be in chronological order
        - At least 2 hours between consecutive meals
    """
```

**Tool 3: save_hydration_preferences**

```python
@tool
async def save_hydration_preferences(
    frequency_hours: int,
    target_ml: int,
    user_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Save hydration preferences to agent context.
    
    Args:
        frequency_hours: Reminder frequency in hours (1-4)
        target_ml: Daily water target in milliliters (1500-5000)
        user_id: User ID
        db: Database session
    
    Returns:
        Success status and message
    
    Validation:
        - frequency_hours must be between 1 and 4
        - target_ml must be between 1500 and 5000
    """
```


### 3. Profile Creation Service

**Purpose**: Create complete UserProfile from agent_context data in atomic transaction

**Class**: `ProfileCreationService`

**Methods**:
```python
async def create_profile_from_agent_context(
    self,
    user_id: UUID,
    agent_context: dict
) -> UserProfile:
    """
    Create UserProfile and all related entities from agent_context.
    
    Args:
        user_id: User ID
        agent_context: Complete agent_context from OnboardingState
    
    Returns:
        Created UserProfile with all relationships loaded
    
    Raises:
        OnboardingIncompleteError: If required agent data is missing
        ValidationError: If data validation fails
        DatabaseError: If transaction fails
    
    Process:
        1. Verify all required agent data present
        2. Extract and validate data from agent_context
        3. Create UserProfile entity
        4. Create all related entities
        5. Execute in atomic transaction
        6. Return profile with relationships loaded
    """
```

**Helper Methods**:
```python
def _verify_agent_completion(self, agent_context: dict) -> None:
    """Verify all agents have completed their steps"""
    
def _extract_fitness_data(self, agent_context: dict) -> dict:
    """Extract fitness assessment data"""
    
def _extract_goal_data(self, agent_context: dict) -> dict:
    """Extract goal setting data"""
    
def _extract_workout_data(self, agent_context: dict) -> dict:
    """Extract workout planning data"""
    
def _extract_diet_data(self, agent_context: dict) -> dict:
    """Extract diet planning data"""
    
def _extract_schedule_data(self, agent_context: dict) -> dict:
    """Extract scheduling data"""
    
async def _create_profile_entity(self, user_id: UUID, fitness_level: str) -> UserProfile:
    """Create UserProfile entity"""
    
async def _create_fitness_goals(self, profile_id: UUID, goal_data: dict) -> List[FitnessGoal]:
    """Create FitnessGoal entities"""
    
async def _create_physical_constraints(self, profile_id: UUID, limitations: List[str]) -> List[PhysicalConstraint]:
    """Create PhysicalConstraint entities"""
    
async def _create_dietary_preference(self, profile_id: UUID, diet_data: dict) -> DietaryPreference:
    """Create DietaryPreference entity"""
    
async def _create_meal_plan(self, profile_id: UUID, meal_plan_data: dict) -> MealPlan:
    """Create MealPlan entity"""
    
async def _create_meal_schedules(self, profile_id: UUID, meal_schedule_data: dict) -> List[MealSchedule]:
    """Create MealSchedule entities"""
    
async def _create_workout_plan(self, user_id: UUID, workout_data: dict) -> WorkoutPlan:
    """Create WorkoutPlan entity"""
    
async def _create_workout_schedules(self, profile_id: UUID, workout_schedule_data: dict) -> List[WorkoutSchedule]:
    """Create WorkoutSchedule entities"""
    
async def _create_hydration_preference(self, profile_id: UUID, hydration_data: dict) -> HydrationPreference:
    """Create HydrationPreference entity"""
```

### 4. Onboarding Completion Verification

**Purpose**: Verify all agents have completed before profile creation

**Function**: `verify_onboarding_completion(agent_context: dict) -> None`

**Verification Checks**:
1. `agent_context["fitness_assessment"]` exists with `completed_at` timestamp
2. `agent_context["goal_setting"]` exists with `completed_at` timestamp
3. `agent_context["workout_planning"]` exists with `user_approved=True`
4. `agent_context["diet_planning"]` exists with `user_approved=True`
5. `agent_context["scheduling"]` exists with all three schedule types:
   - `workout_schedule`
   - `meal_schedule`
   - `hydration_preferences`

**Error Handling**:
- If any check fails, raise `OnboardingIncompleteError` with details of missing data
- Error message should specify which agent data is missing or incomplete

### 5. Agent Context to Database Mapping

**Fitness Assessment → UserProfile + PhysicalConstraint**

```python
# From agent_context
fitness_data = agent_context["fitness_assessment"]

# To database
profile.fitness_level = fitness_data["fitness_level"]  # "beginner", "intermediate", "advanced"

for limitation in fitness_data.get("limitations", []):
    constraint = PhysicalConstraint(
        profile_id=profile.id,
        constraint_type="limitation",
        description=limitation
    )
```

**Goal Setting → FitnessGoal**

```python
# From agent_context
goal_data = agent_context["goal_setting"]

# To database
primary_goal = FitnessGoal(
    profile_id=profile.id,
    goal_type=goal_data["primary_goal"],  # "fat_loss", "muscle_gain", "general_fitness"
    target_weight_kg=goal_data.get("target_weight_kg"),
    target_body_fat_percentage=goal_data.get("target_body_fat_percentage"),
    priority=1
)

if "secondary_goal" in goal_data:
    secondary_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type=goal_data["secondary_goal"],
        priority=2
    )
```

**Workout Planning → WorkoutPlan + WorkoutDay + WorkoutExercise**

```python
# From agent_context
workout_data = agent_context["workout_planning"]["proposed_plan"]

# To database
workout_plan = WorkoutPlan(
    user_id=user_id,
    plan_name=f"{fitness_level.title()} {primary_goal.replace('_', ' ').title()} Plan",
    plan_description=workout_data.get("description"),
    duration_weeks=workout_data.get("duration_weeks", 12),
    days_per_week=workout_data["frequency"],
    plan_rationale=workout_data.get("rationale"),
    is_locked=True
)

for day_num, day_data in enumerate(workout_data["training_split"], start=1):
    workout_day = WorkoutDay(
        workout_plan_id=workout_plan.id,
        day_number=day_num,
        day_name=day_data["name"],
        muscle_groups=day_data["muscle_groups"],
        workout_type=day_data["type"],
        estimated_duration_minutes=workout_data["duration_minutes"]
    )
    
    for order, exercise in enumerate(day_data["exercises"], start=1):
        workout_exercise = WorkoutExercise(
            workout_day_id=workout_day.id,
            exercise_library_id=exercise["exercise_id"],  # Lookup from library
            exercise_order=order,
            sets=exercise["sets"],
            reps_target=exercise.get("reps"),
            rest_seconds=exercise.get("rest_seconds", 60),
            notes=exercise.get("notes")
        )
```

**Diet Planning → DietaryPreference + MealPlan**

```python
# From agent_context
diet_prefs = agent_context["diet_planning"]["preferences"]
meal_plan_data = agent_context["diet_planning"]["proposed_plan"]

# To database
dietary_pref = DietaryPreference(
    profile_id=profile.id,
    diet_type=diet_prefs["diet_type"],  # "omnivore", "vegetarian", "vegan", etc.
    allergies=diet_prefs.get("allergies", []),
    intolerances=diet_prefs.get("intolerances", []),
    dislikes=diet_prefs.get("dislikes", [])
)

meal_plan = MealPlan(
    profile_id=profile.id,
    daily_calorie_target=meal_plan_data["daily_calories"],
    protein_percentage=meal_plan_data["protein_percentage"],
    carbs_percentage=meal_plan_data["carbs_percentage"],
    fats_percentage=meal_plan_data["fats_percentage"]
)
```

**Scheduling → WorkoutSchedule + MealSchedule + HydrationPreference**

```python
# From agent_context
schedule_data = agent_context["scheduling"]

# Workout schedules
for day, time in zip(schedule_data["workout_schedule"]["days"], 
                     schedule_data["workout_schedule"]["times"]):
    workout_schedule = WorkoutSchedule(
        profile_id=profile.id,
        day_of_week=day_name_to_number(day),  # Monday=0, Sunday=6
        scheduled_time=time_str_to_time(time),  # "07:00" -> time(7, 0)
        enable_notifications=True
    )

# Meal schedules
for meal_name, time in schedule_data["meal_schedule"].items():
    meal_schedule = MealSchedule(
        profile_id=profile.id,
        meal_name=meal_name,
        scheduled_time=time_str_to_time(time),
        enable_notifications=True
    )

# Hydration preference
hydration_pref = HydrationPreference(
    profile_id=profile.id,
    daily_water_target_ml=schedule_data["hydration_preferences"]["target_ml"],
    reminder_frequency_minutes=schedule_data["hydration_preferences"]["frequency_hours"] * 60,
    enable_notifications=True
)
```

### 6. Onboarding Completion Endpoint

**Endpoint**: `POST /api/v1/onboarding/complete`

**Request**: No body required (uses authenticated user)

**Response**:
```json
{
    "profile_id": "uuid",
    "user_id": "uuid",
    "fitness_level": "intermediate",
    "is_locked": true,
    "onboarding_complete": true,
    "message": "Onboarding completed successfully. Your profile has been created and locked."
}
```

**Error Responses**:
- 400 Bad Request: Missing required agent data
- 401 Unauthorized: Not authenticated
- 409 Conflict: Onboarding already complete
- 500 Internal Server Error: Profile creation failed

**Implementation**:
```python
@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OnboardingCompleteResponse:
    """Complete onboarding and create user profile"""
    
    # Load onboarding state
    state = await get_onboarding_state(current_user.id, db)
    
    # Check if already complete
    if state.is_complete:
        raise HTTPException(status_code=409, detail="Onboarding already complete")
    
    # Verify all agents completed
    verify_onboarding_completion(state.agent_context)
    
    # Create profile from agent context
    profile_service = ProfileCreationService(db)
    profile = await profile_service.create_profile_from_agent_context(
        user_id=current_user.id,
        agent_context=state.agent_context
    )
    
    # Mark onboarding complete
    state.is_complete = True
    state.current_agent = "general_assistant"
    await db.commit()
    
    return OnboardingCompleteResponse(
        profile_id=profile.id,
        user_id=current_user.id,
        fitness_level=profile.fitness_level,
        is_locked=profile.is_locked,
        onboarding_complete=True,
        message="Onboarding completed successfully. Your profile has been created and locked."
    )
```


## Data Models

### Agent Context Structure for Scheduling

```python
{
    "scheduling": {
        "workout_schedule": {
            "days": ["Monday", "Wednesday", "Friday", "Saturday"],
            "times": ["07:00", "07:00", "18:00", "09:00"]
        },
        "meal_schedule": {
            "breakfast": "08:00",
            "lunch": "13:00",
            "snack": "16:00",
            "dinner": "19:00"
        },
        "hydration_preferences": {
            "frequency_hours": 2,
            "target_ml": 3000
        },
        "completed_at": "2024-01-15T11:10:00Z"
    }
}
```

### Complete Agent Context Example

```python
{
    "fitness_assessment": {
        "fitness_level": "intermediate",
        "experience_years": 2,
        "limitations": ["no_equipment_at_home"],
        "completed_at": "2024-01-15T10:30:00Z"
    },
    "goal_setting": {
        "primary_goal": "muscle_gain",
        "secondary_goal": "fat_loss",
        "target_weight_kg": 75.0,
        "completed_at": "2024-01-15T10:35:00Z"
    },
    "workout_planning": {
        "preferences": {
            "location": "gym",
            "frequency": 4,
            "duration_minutes": 60
        },
        "proposed_plan": {
            "frequency": 4,
            "duration_minutes": 60,
            "training_split": [
                {
                    "name": "Upper Body Push",
                    "muscle_groups": ["chest", "shoulders", "triceps"],
                    "type": "strength",
                    "exercises": [...]
                },
                ...
            ],
            "rationale": "4-day upper/lower split for muscle gain"
        },
        "user_approved": true,
        "completed_at": "2024-01-15T10:45:00Z"
    },
    "diet_planning": {
        "preferences": {
            "diet_type": "omnivore",
            "allergies": ["dairy"],
            "dislikes": ["mushrooms"],
            "meal_frequency": 4
        },
        "proposed_plan": {
            "daily_calories": 2800,
            "protein_g": 175,
            "carbs_g": 350,
            "fats_g": 78,
            "protein_percentage": 25,
            "carbs_percentage": 50,
            "fats_percentage": 25,
            "meal_frequency": 4,
            "sample_meals": [...]
        },
        "user_approved": true,
        "completed_at": "2024-01-15T11:00:00Z"
    },
    "scheduling": {
        "workout_schedule": {
            "days": ["Monday", "Wednesday", "Friday", "Saturday"],
            "times": ["07:00", "07:00", "18:00", "09:00"]
        },
        "meal_schedule": {
            "breakfast": "08:00",
            "lunch": "13:00",
            "snack": "16:00",
            "dinner": "19:00"
        },
        "hydration_preferences": {
            "frequency_hours": 2,
            "target_ml": 3000
        },
        "completed_at": "2024-01-15T11:10:00Z"
    }
}
```

### Database Entities Created

**UserProfile**:
- user_id
- fitness_level: "intermediate"
- is_locked: True

**FitnessGoal** (2 records):
1. goal_type: "muscle_gain", priority: 1, target_weight_kg: 75.0
2. goal_type: "fat_loss", priority: 2

**PhysicalConstraint** (1 record):
- constraint_type: "limitation"
- description: "no_equipment_at_home"

**DietaryPreference** (1 record):
- diet_type: "omnivore"
- allergies: ["dairy"]
- dislikes: ["mushrooms"]

**MealPlan** (1 record):
- daily_calorie_target: 2800
- protein_percentage: 25
- carbs_percentage: 50
- fats_percentage: 25

**MealSchedule** (4 records):
1. meal_name: "breakfast", scheduled_time: 08:00
2. meal_name: "lunch", scheduled_time: 13:00
3. meal_name: "snack", scheduled_time: 16:00
4. meal_name: "dinner", scheduled_time: 19:00

**WorkoutPlan** (1 record):
- plan_name: "Intermediate Muscle Gain Plan"
- days_per_week: 4
- duration_weeks: 12
- is_locked: True

**WorkoutDay** (4 records):
- One for each training day with exercises

**WorkoutSchedule** (4 records):
1. day_of_week: 0 (Monday), scheduled_time: 07:00
2. day_of_week: 2 (Wednesday), scheduled_time: 07:00
3. day_of_week: 4 (Friday), scheduled_time: 18:00
4. day_of_week: 5 (Saturday), scheduled_time: 09:00

**HydrationPreference** (1 record):
- daily_water_target_ml: 3000
- reminder_frequency_minutes: 120

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Workout Schedule Day Validation

*For any* list of day names provided to save_workout_schedule, only valid day names (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday) should be accepted, and any invalid day name should result in a validation error.

**Validates: Requirements 5.3**

### Property 2: Workout Schedule Time Format Validation

*For any* list of time strings provided to save_workout_schedule, only times in HH:MM format with hours 00-23 and minutes 00-59 should be accepted, and any invalid format should result in a validation error.

**Validates: Requirements 5.4, 21.2**

### Property 3: Workout Schedule Length Matching

*For any* workout schedule with days and times lists, the length of days must equal the length of times, otherwise a validation error should be raised.

**Validates: Requirements 5.5**

### Property 4: Meal Schedule Time Format Validation

*For any* meal schedule dictionary, all time values must be in HH:MM format with valid hours (00-23) and minutes (00-59), otherwise a validation error should be raised.

**Validates: Requirements 5.8**

### Property 5: Meal Schedule Frequency Matching

*For any* meal schedule provided to save_meal_schedule, the number of meals must match the meal_frequency from the meal_plan in agent_context, otherwise a validation error should be raised.

**Validates: Requirements 5.9**

### Property 6: Hydration Frequency Range Validation

*For any* frequency_hours value provided to save_hydration_preferences, it must be between 1 and 4 (inclusive), otherwise a validation error should be raised.

**Validates: Requirements 5.12**

### Property 7: Hydration Target Range Validation

*For any* target_ml value provided to save_hydration_preferences, it must be between 1500 and 5000 (inclusive), otherwise a validation error should be raised.

**Validates: Requirements 5.13**

### Property 8: Timestamp Format Consistency

*For any* successful save operation by scheduling agent tools, the completed_at timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

**Validates: Requirements 5.15**

### Property 9: Missing Agent Data Error Handling

*For any* agent_context missing required agent data (fitness_assessment, goal_setting, workout_planning, diet_planning, or scheduling), the verification function should raise OnboardingIncompleteError with details of the missing data.

**Validates: Requirements 7.6**

### Property 10: Profile Creation Atomicity

*For any* profile creation attempt, either all database entities (UserProfile, FitnessGoal, PhysicalConstraint, DietaryPreference, MealPlan, MealSchedule, WorkoutSchedule, HydrationPreference) are created successfully, or none are created (transaction rollback).

**Validates: Requirements 8.11**

### Property 11: Profile Creation Rollback on Failure

*For any* profile creation that fails due to validation error or database constraint violation, all database changes must be rolled back and no partial profile should exist.

**Validates: Requirements 8.13**

### Property 12: Meal Time Spacing Validation

*For any* meal schedule with multiple meals, consecutive meals must be at least 2 hours apart, otherwise a validation error should be raised.

**Validates: Requirements 21.3**

### Property 13: Meal Time Chronological Order

*For any* meal schedule, meal times must be in chronological order throughout the day (earlier meals have earlier times), otherwise a validation error should be raised.

**Validates: Requirements 21.4**

## Error Handling

### Validation Errors

**Invalid Day Names**:
```python
# Input: days=["Monday", "Moonday", "Friday"]
# Error: ValidationError("Invalid day name: Moonday. Valid days are: Monday, Tuesday, ...")
```

**Invalid Time Format**:
```python
# Input: times=["07:00", "25:00", "18:00"]
# Error: ValidationError("Invalid time format: 25:00. Time must be in HH:MM format with hours 00-23")
```

**Mismatched Lengths**:
```python
# Input: days=["Monday", "Wednesday"], times=["07:00"]
# Error: ValidationError("Length mismatch: days has 2 items but times has 1 item")
```

**Meal Frequency Mismatch**:
```python
# Input: meal_schedule with 3 meals, but meal_plan.meal_frequency=4
# Error: ValidationError("Meal count mismatch: provided 3 meals but meal plan requires 4")
```

**Insufficient Meal Spacing**:
```python
# Input: {"breakfast": "08:00", "lunch": "09:00"}
# Error: ValidationError("Insufficient spacing: breakfast and lunch are only 1 hour apart (minimum 2 hours required)")
```

### Onboarding Incomplete Errors

**Missing Agent Data**:
```python
# Missing workout_planning approval
# Error: OnboardingIncompleteError("Onboarding incomplete: workout_planning.user_approved is missing or False")
```

**Missing Schedule Data**:
```python
# Missing hydration_preferences
# Error: OnboardingIncompleteError("Onboarding incomplete: scheduling.hydration_preferences is missing")
```

### Transaction Errors

**Profile Creation Failure**:
```python
# Database constraint violation during profile creation
# Error: DatabaseError("Profile creation failed: unique constraint violation on user_id")
# Result: All changes rolled back, no partial profile created
```

**Rollback Success**:
```python
# After rollback, verify no entities exist
assert UserProfile.query.filter_by(user_id=user_id).count() == 0
assert FitnessGoal.query.filter_by(profile_id=profile_id).count() == 0
# All related entities should also be absent
```

## Testing Strategy

### Unit Tests

**Scheduling Agent Tests**:
- Test save_workout_schedule with valid data
- Test save_meal_schedule with valid data
- Test save_hydration_preferences with valid data
- Test validation errors for invalid inputs
- Test agent response format

**Profile Creation Service Tests**:
- Test profile creation with complete agent_context
- Test profile creation with missing optional data
- Test verification of agent completion
- Test data extraction from agent_context
- Test entity creation for each type
- Test profile locking after creation

**Validation Tests**:
- Test day name validation
- Test time format validation
- Test range validation for hydration
- Test meal spacing validation
- Test meal ordering validation

### Property-Based Tests

All property tests should run with minimum 100 iterations and be tagged with:
**Feature: scheduling-agent-completion, Property {number}: {property_text}**

**Property 1: Workout Schedule Day Validation**
- Generate random lists of day names (valid and invalid)
- Verify only valid day names are accepted
- Tag: **Feature: scheduling-agent-completion, Property 1: Workout Schedule Day Validation**

**Property 2: Workout Schedule Time Format Validation**
- Generate random time strings (valid and invalid formats)
- Verify only valid HH:MM format with valid ranges accepted
- Tag: **Feature: scheduling-agent-completion, Property 2: Workout Schedule Time Format Validation**

**Property 3: Workout Schedule Length Matching**
- Generate random lists of days and times with varying lengths
- Verify validation error when lengths don't match
- Tag: **Feature: scheduling-agent-completion, Property 3: Workout Schedule Length Matching**

**Property 4: Meal Schedule Time Format Validation**
- Generate random meal schedule dictionaries with various time formats
- Verify only valid time formats accepted
- Tag: **Feature: scheduling-agent-completion, Property 4: Meal Schedule Time Format Validation**

**Property 5: Meal Schedule Frequency Matching**
- Generate random meal schedules with varying meal counts
- Verify validation error when count doesn't match meal_frequency
- Tag: **Feature: scheduling-agent-completion, Property 5: Meal Schedule Frequency Matching**

**Property 6: Hydration Frequency Range Validation**
- Generate random integers for frequency_hours
- Verify only values 1-4 accepted
- Tag: **Feature: scheduling-agent-completion, Property 6: Hydration Frequency Range Validation**

**Property 7: Hydration Target Range Validation**
- Generate random integers for target_ml
- Verify only values 1500-5000 accepted
- Tag: **Feature: scheduling-agent-completion, Property 7: Hydration Target Range Validation**

**Property 8: Timestamp Format Consistency**
- Call save tools multiple times
- Verify all completed_at timestamps are in ISO 8601 format
- Tag: **Feature: scheduling-agent-completion, Property 8: Timestamp Format Consistency**

**Property 9: Missing Agent Data Error Handling**
- Generate random agent_context with missing agent data
- Verify OnboardingIncompleteError raised with correct details
- Tag: **Feature: scheduling-agent-completion, Property 9: Missing Agent Data Error Handling**

**Property 10: Profile Creation Atomicity**
- Attempt profile creation with various agent_context states
- Verify either all entities created or none created
- Tag: **Feature: scheduling-agent-completion, Property 10: Profile Creation Atomicity**

**Property 11: Profile Creation Rollback on Failure**
- Inject failures during profile creation
- Verify all changes rolled back
- Tag: **Feature: scheduling-agent-completion, Property 11: Profile Creation Rollback on Failure**

**Property 12: Meal Time Spacing Validation**
- Generate random meal schedules with varying time spacing
- Verify validation error when meals less than 2 hours apart
- Tag: **Feature: scheduling-agent-completion, Property 12: Meal Time Spacing Validation**

**Property 13: Meal Time Chronological Order**
- Generate random meal schedules with various orderings
- Verify validation error when meals not in chronological order
- Tag: **Feature: scheduling-agent-completion, Property 13: Meal Time Chronological Order**

### Integration Tests

**Complete Onboarding Flow**:
- Test full flow from Fitness Assessment through Scheduling to Profile Creation
- Verify all agent_context data correctly mapped to database entities
- Verify profile is locked after creation
- Verify onboarding_state.is_complete is True
- Verify current_agent is "general_assistant"

**Backward Compatibility**:
- Test existing onboarding completion endpoint still works
- Test users mid-onboarding can complete with new system
- Test fallback to old flow if agent_context incomplete

**Post-Onboarding Routing**:
- Test chat messages route to General Assistant after completion
- Test General Assistant has read access to profile
- Test profile modifications require explicit confirmation

### End-to-End Tests

**Happy Path**:
1. User completes all 5 agent steps
2. User triggers onboarding completion
3. Profile created successfully
4. User can chat with General Assistant
5. User can view their plans and schedules

**Error Scenarios**:
1. User attempts completion with incomplete data → 400 error
2. User attempts completion twice → 409 error
3. Profile creation fails → rollback and 500 error
4. Invalid schedule data → validation error

### Test Coverage Target

Minimum 80% code coverage for:
- SchedulingAgent class
- ProfileCreationService class
- Validation functions
- API endpoints
- Data mapping functions

## Deployment Considerations

### Database Migration

**New Tables**: None (all tables already exist)

**Schema Changes**: None required

**Data Migration**: None required (new feature, no existing data to migrate)

### Backward Compatibility

**Existing Onboarding Flow**:
- Old onboarding completion endpoint remains functional
- Users mid-onboarding can complete with either old or new flow
- agent_context is optional; if missing, fall back to step_data

**Rollback Plan**:
- If issues arise, disable new completion endpoint
- Users can complete via old endpoint
- No data loss or corruption

### Performance Considerations

**Profile Creation Transaction**:
- Single transaction creates 10-20 database entities
- Expected duration: < 500ms
- Use connection pooling to handle concurrent completions

**Agent Context Size**:
- agent_context JSONB field can grow to 50-100KB
- PostgreSQL handles JSONB efficiently
- No performance concerns for typical usage

### Monitoring

**Metrics to Track**:
- Onboarding completion rate
- Profile creation success rate
- Profile creation duration (p50, p95, p99)
- Validation error frequency by type
- Transaction rollback frequency

**Alerts**:
- Profile creation failure rate > 5%
- Profile creation duration > 1 second
- Onboarding completion rate drops > 20%


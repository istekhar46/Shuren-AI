# General Agent Delegation Tools - Design Document

## 1. Overview

This design document specifies the technical implementation for adding delegation tools to the General Assistant Agent. These tools enable the general agent to query user data (workouts, meals, schedules, exercises, recipes) by reusing the same database query logic used by specialized agents.

### Design Goals

- Enable general agent to answer all fitness-related queries post-onboarding
- Reuse existing database query logic to avoid code duplication
- Maintain consistency with specialized agent responses
- Provide graceful error handling with user-friendly messages
- Keep tool execution performant (< 200ms)

### Key Design Decisions

1. **Service Layer Extraction**: Extract shared query logic into service functions to avoid duplication
2. **Tool Delegation Pattern**: General agent tools delegate to service layer, not directly to specialized agent tools
3. **Response Format Consistency**: All tools return JSON with same structure as specialized agents
4. **Error Handling Strategy**: Consistent error response format across all tools
5. **Context-Based Filtering**: All queries use `AgentContext.user_id` for data isolation

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    General Assistant Agent                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ get_workout│  │ get_meal   │  │ get_schedule│  ...       │
│  │   _info    │  │   _info    │  │   _info    │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼────────────────┼───────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ WorkoutService │  │  MealService   │  │ScheduleService│ │
│  │                │  │                │  │               │  │
│  │ - get_today_   │  │ - get_today_   │  │ - get_upcoming│ │
│  │   workout()    │  │   meal_plan()  │  │   _schedule() │  │
│  └────────┬───────┘  └────────┬───────┘  └───────┬───────┘  │
└───────────┼──────────────────┼──────────────────┼───────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ WorkoutPlan  │  │ MealTemplate │  │WorkoutSchedule│      │
│  │ WorkoutDay   │  │ TemplateMeal │  │ MealSchedule  │      │
│  │WorkoutExercise│ │    Dish      │  │               │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**General Assistant Agent**:
- Defines LangChain `@tool` decorated functions
- Validates tool parameters
- Calls service layer functions
- Formats responses as JSON strings for LLM consumption
- Handles exceptions and returns user-friendly error messages

**Service Layer** (New):
- Contains reusable query logic
- Accepts `user_id` and `db_session` parameters
- Returns Python objects (not JSON strings)
- Handles database queries and joins
- Applies soft delete filtering
- Raises specific exceptions for error cases

**Database Layer**:
- SQLAlchemy models (existing, no changes)
- Async database operations via asyncpg


## 3. Components and Interfaces

### 3.1 Service Layer

Create new service modules to extract shared query logic:

#### `app/services/workout_service.py`

```python
from datetime import date
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, ExerciseLibrary
from app.models.preferences import WorkoutSchedule
from app.models.profile import UserProfile

class WorkoutService:
    """Service for workout-related database operations."""
    
    @staticmethod
    async def get_today_workout(
        user_id: UUID,
        db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get today's workout plan for a user.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with workout details or None if no workout scheduled
            
        Raises:
            ValueError: If user profile or workout plan not found
        """
        # Implementation details in tasks
        pass
    
    @staticmethod
    async def get_exercise_demo(
        exercise_name: str,
        db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get exercise demonstration details from library.
        
        Args:
            exercise_name: Name of exercise (case-insensitive partial match)
            db_session: Database session
            
        Returns:
            Dict with exercise details or None if not found
        """
        # Implementation details in tasks
        pass
```

#### `app/services/meal_service.py`

```python
from datetime import date
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dish import Dish, DishIngredient, Ingredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile

class MealService:
    """Service for meal-related database operations."""
    
    @staticmethod
    async def get_today_meal_plan(
        user_id: UUID,
        db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get today's meal plan for a user.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with meal details or None if no meal plan configured
            
        Raises:
            ValueError: If user profile not found
        """
        # Implementation details in tasks
        pass
    
    @staticmethod
    async def get_recipe_details(
        dish_name: str,
        db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get recipe details including ingredients and instructions.
        
        Args:
            dish_name: Name of dish (case-insensitive partial match)
            db_session: Database session
            
        Returns:
            Dict with recipe details or None if not found
        """
        # Implementation details in tasks
        pass
```

#### `app/services/schedule_service.py`

```python
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.preferences import WorkoutSchedule, MealSchedule
from app.models.profile import UserProfile

class ScheduleService:
    """Service for schedule-related database operations."""
    
    @staticmethod
    async def get_upcoming_schedule(
        user_id: UUID,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Get upcoming workout and meal schedules for a user.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with workout and meal schedules
            
        Raises:
            ValueError: If user profile not found
        """
        # Implementation details in tasks
        pass
```

### 3.2 General Assistant Agent Tools

Add new tools to `GeneralAssistantAgent.get_tools()`:

#### Tool: `get_workout_info`

```python
@tool
async def get_workout_info() -> str:
    """Get today's workout plan for the user.
    
    Returns:
        JSON string with workout details including exercises, sets, reps, and rest periods.
        If no workout scheduled, returns a rest day message.
    """
    try:
        result = await WorkoutService.get_today_workout(
            user_id=context.user_id,
            db_session=db_session
        )
        
        if result is None:
            return json.dumps({
                "success": True,
                "data": {
                    "message": "No workout scheduled for today. It's a rest day!"
                }
            })
        
        return json.dumps({
            "success": True,
            "data": result,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "general_assistant_agent"
            }
        })
        
    except ValueError as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Error in get_workout_info: {e}")
        return json.dumps({
            "success": False,
            "error": "Unable to retrieve workout information. Please try again."
        })
```

#### Tool: `get_meal_info`

```python
@tool
async def get_meal_info() -> str:
    """Get today's meal plan for the user.
    
    Returns:
        JSON string with meal details including dishes, timing, and nutritional information.
        If no meal plan configured, returns a helpful message.
    """
    # Similar structure to get_workout_info
    pass
```

#### Tool: `get_schedule_info`

```python
@tool
async def get_schedule_info() -> str:
    """Get upcoming workout and meal schedules for the user.
    
    Returns:
        JSON string with upcoming schedules including days, times, and notification settings.
    """
    # Similar structure to get_workout_info
    pass
```

#### Tool: `get_exercise_demo`

```python
@tool
async def get_exercise_demo(exercise_name: str) -> str:
    """Get exercise demonstration details from the exercise library.
    
    Args:
        exercise_name: Name of the exercise to demonstrate
    
    Returns:
        JSON string with GIF URL, video URL, instructions, and difficulty level.
        If exercise not found, returns a helpful error message.
    """
    # Similar structure to get_workout_info
    pass
```

#### Tool: `get_recipe_details`

```python
@tool
async def get_recipe_details(dish_name: str) -> str:
    """Get recipe details including ingredients and cooking instructions.
    
    Args:
        dish_name: Name of the dish/recipe
    
    Returns:
        JSON string with ingredients, cooking instructions, and nutritional information.
        If recipe not found, returns a helpful error message.
    """
    # Similar structure to get_workout_info
    pass
```


## 4. Data Models

### Service Layer Response Formats

#### Workout Response

```python
{
    "day_name": str,  # e.g., "Push Day"
    "workout_type": str,  # e.g., "strength"
    "muscle_groups": List[str],  # e.g., ["chest", "shoulders", "triceps"]
    "estimated_duration_minutes": int,
    "exercises": [
        {
            "name": str,
            "sets": int,
            "reps": str,  # e.g., "8-12" or "10"
            "weight_kg": Optional[float],
            "rest_seconds": int,
            "notes": Optional[str]
        }
    ]
}
```

#### Meal Response

```python
{
    "day_of_week": int,  # 0=Monday, 6=Sunday
    "meals": [
        {
            "meal_name": str,  # e.g., "breakfast"
            "scheduled_time": str,  # e.g., "08:00"
            "dish_name": str,
            "dish_name_hindi": Optional[str],
            "calories": float,
            "protein_g": float,
            "carbs_g": float,
            "fats_g": float,
            "serving_size_g": float,
            "prep_time_minutes": int,
            "cook_time_minutes": int,
            "is_vegetarian": bool,
            "is_vegan": bool
        }
    ],
    "daily_totals": {
        "calories": float,
        "protein_g": float,
        "carbs_g": float,
        "fats_g": float
    },
    "targets": {
        "daily_calorie_target": int,
        "protein_percentage": float,
        "carbs_percentage": float,
        "fats_percentage": float
    }
}
```

#### Schedule Response

```python
{
    "workouts": [
        {
            "id": str,  # UUID
            "day": str,  # e.g., "Monday"
            "day_of_week": int,  # 0-6
            "time": str,  # e.g., "18:00"
            "notifications_enabled": bool
        }
    ],
    "meals": [
        {
            "id": str,  # UUID
            "meal_name": str,
            "time": str,
            "notifications_enabled": bool
        }
    ]
}
```

#### Exercise Demo Response

```python
{
    "exercise_name": str,
    "gif_url": Optional[str],
    "video_url": Optional[str],
    "description": str,
    "instructions": str,
    "difficulty_level": str,  # "beginner", "intermediate", "advanced"
    "primary_muscle_group": str
}
```

#### Recipe Response

```python
{
    "dish_name": str,
    "dish_name_hindi": Optional[str],
    "description": Optional[str],
    "cuisine_type": str,
    "meal_type": str,
    "difficulty_level": str,
    "prep_time_minutes": int,
    "cook_time_minutes": int,
    "serving_size_g": float,
    "nutrition": {
        "calories": float,
        "protein_g": float,
        "carbs_g": float,
        "fats_g": float,
        "fiber_g": Optional[float]
    },
    "dietary_tags": {
        "is_vegetarian": bool,
        "is_vegan": bool,
        "is_gluten_free": bool,
        "is_dairy_free": bool,
        "is_nut_free": bool
    },
    "ingredients": [
        {
            "name": str,
            "name_hindi": Optional[str],
            "quantity": float,
            "unit": str,
            "preparation_note": Optional[str],
            "is_optional": bool
        }
    ]
}
```

### Error Response Format

All tools use consistent error response format:

```python
{
    "success": False,
    "error": str  # User-friendly error message
}
```


## 5. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing the acceptance criteria, I identified several redundancies:

1. **Response format properties (US-1.2, US-2.2, US-3.2, US-4.2, US-5.2)** can be combined into a single property about response completeness
2. **Consistency properties (US-1.3, US-2.3, US-3.3, US-4.3, US-5.3)** all test the same concept: service layer returns same data as specialized agents
3. **Edge case properties (US-1.4, US-2.4, US-4.4, US-5.4)** are better handled as unit test examples rather than universal properties

After reflection, the core properties are:

### Property 1: Workout Query Returns Complete Data

*For any* user with a workout plan, querying today's workout should return all required fields: day_name, workout_type, muscle_groups, estimated_duration_minutes, and a list of exercises with sets, reps, rest_seconds.

**Validates: Requirements US-1.1, US-1.2**

### Property 2: Meal Query Returns Complete Data

*For any* user with a meal template, querying today's meal plan should return all required fields: day_of_week, meals list with nutritional info, daily_totals, and targets.

**Validates: Requirements US-2.1, US-2.2**

### Property 3: Schedule Query Returns Complete Data

*For any* user with schedules configured, querying upcoming schedules should return both workout and meal schedules with all required fields: id, day/time information, and notification settings.

**Validates: Requirements US-3.1, US-3.2**

### Property 4: Exercise Demo Query Returns Complete Data

*For any* exercise in the library, querying its demonstration should return all required fields: exercise_name, gif_url, video_url, description, instructions, difficulty_level, primary_muscle_group.

**Validates: Requirements US-4.1, US-4.2**

### Property 5: Recipe Query Returns Complete Data

*For any* dish in the database, querying its recipe should return all required fields: dish_name, nutrition info, dietary tags, and ingredients list with quantities.

**Validates: Requirements US-5.1, US-5.2**

### Property 6: Service Layer Consistency

*For any* user context, calling the service layer function should return the same data structure as the corresponding specialized agent tool (workout planner, diet planner, scheduler).

**Validates: Requirements US-1.3, US-2.3, US-3.3, US-4.3, US-5.3**

### Property 7: User Data Isolation

*For any* tool call, the returned data should only include information for the specified user_id from AgentContext, never exposing other users' data.

**Validates: Requirements TC-2 (Agent Context)**

### Property 8: Soft Delete Filtering

*For any* database query, the results should exclude records where `deleted_at IS NOT NULL`, ensuring only active data is returned.

**Validates: Requirements TC-1 (Database Access)**


## 6. Error Handling

### Error Categories

1. **User Not Found**: User profile doesn't exist
2. **Data Not Found**: Requested resource doesn't exist (exercise, dish, etc.)
3. **No Data Configured**: User hasn't set up plans yet (workout plan, meal template)
4. **Database Error**: SQLAlchemy exceptions during queries
5. **Unexpected Error**: Any other exceptions

### Error Handling Strategy

```python
try:
    # Call service layer
    result = await service_function(user_id, db_session)
    
    # Handle None result (data not found)
    if result is None:
        return json.dumps({
            "success": True,
            "data": {
                "message": "Helpful user-friendly message"
            }
        })
    
    # Return success response
    return json.dumps({
        "success": True,
        "data": result,
        "metadata": {...}
    })
    
except ValueError as e:
    # Handle validation errors (user not found, invalid params)
    return json.dumps({
        "success": False,
        "error": str(e)
    })
    
except SQLAlchemyError as e:
    # Log database errors
    logger.error(f"Database error in tool: {e}")
    return json.dumps({
        "success": False,
        "error": "Unable to retrieve data. Please try again."
    })
    
except Exception as e:
    # Log unexpected errors
    logger.error(f"Unexpected error in tool: {e}")
    return json.dumps({
        "success": False,
        "error": "An unexpected error occurred. Please try again."
    })
```

### User-Friendly Error Messages

- **No workout scheduled**: "No workout scheduled for today. It's a rest day!"
- **No meal plan**: "No meal plan configured yet. Please complete your meal planning setup."
- **Exercise not found**: "Exercise '{name}' not found in library. Try a different name or check spelling."
- **Recipe not found**: "Recipe '{name}' not found. Try a different dish name."
- **Database error**: "Unable to retrieve {resource}. Please try again."
- **Unexpected error**: "An unexpected error occurred. Please try again."


## 7. Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both are complementary and necessary for comprehensive coverage

### Unit Testing

Focus on:
- Specific examples demonstrating correct behavior
- Edge cases (no workout scheduled, no meal plan, exercise not found)
- Error conditions (database errors, invalid parameters)
- Integration between tools and service layer

Example unit tests:
```python
async def test_get_workout_info_with_valid_workout(authenticated_client, test_user_with_workout):
    """Test getting workout info when user has a workout scheduled."""
    # Arrange: User with workout plan for today
    # Act: Call get_workout_info tool
    # Assert: Returns complete workout data
    
async def test_get_workout_info_rest_day(authenticated_client, test_user):
    """Test getting workout info when no workout scheduled (rest day)."""
    # Arrange: User with no workout scheduled today
    # Act: Call get_workout_info tool
    # Assert: Returns rest day message
    
async def test_get_exercise_demo_not_found(authenticated_client):
    """Test getting exercise demo for non-existent exercise."""
    # Arrange: Invalid exercise name
    # Act: Call get_exercise_demo tool
    # Assert: Returns helpful error message
```

### Property-Based Testing

Use Hypothesis to test universal properties with random data generation.

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: general-agent-delegation-tools, Property {N}: {property_text}`

Example property tests:
```python
from hypothesis import given, strategies as st

@given(
    user_id=st.uuids(),
    workout_exists=st.booleans()
)
async def test_property_workout_query_completeness(user_id, workout_exists, db_session):
    """
    Feature: general-agent-delegation-tools, Property 1: Workout Query Returns Complete Data
    
    For any user with a workout plan, the response should contain all required fields.
    """
    # Arrange: Create user with or without workout plan
    # Act: Call WorkoutService.get_today_workout
    # Assert: If workout exists, verify all required fields present
    
@given(exercise_name=st.text(min_size=1, max_size=100))
async def test_property_exercise_demo_completeness(exercise_name, db_session):
    """
    Feature: general-agent-delegation-tools, Property 4: Exercise Demo Query Returns Complete Data
    
    For any exercise in the library, the response should contain all required fields.
    """
    # Arrange: Seed exercise library with random exercises
    # Act: Call WorkoutService.get_exercise_demo
    # Assert: If exercise found, verify all required fields present
```

### Test Coverage Requirements

- Service layer functions: 100% coverage
- General agent tools: 100% coverage
- Edge cases: All documented edge cases tested
- Error conditions: All error paths tested
- Property tests: Minimum 100 iterations per property

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **hypothesis**: Property-based testing
- **pytest-cov**: Coverage reporting

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app/services --cov=app/agents --cov-report=html

# Run only property tests
poetry run pytest -m property

# Run only unit tests
poetry run pytest -m unit

# Run specific test file
poetry run pytest tests/test_workout_service.py
```


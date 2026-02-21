# Design Document: Specialized AI Agents

## Overview

This design document specifies the implementation of 6 specialized AI agents for the Shuren fitness application. Each agent extends the BaseAgent class and provides domain-specific expertise through specialized tools and system prompts.

The agents integrate with the existing LangChain foundation (Phase 2 Sub-Doc 1) and database models (Phase 1). They support both text and voice interaction modes, with voice mode optimized for <2s latency and text mode providing detailed responses with markdown formatting.

### Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  AgentOrchestrator                       │
│  - Classifies queries using fast LLM                    │
│  - Routes to appropriate agent                          │
│  - Caches agents/classifications in voice mode          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌─────────┐
    │ Agent 1 │            │ Agent 6 │
    │ (Base)  │    ...     │ (Base)  │
    └────┬────┘            └────┬────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  LangChain Tools │
         │  - Database ops  │
         │  - Calculations  │
         │  - Retrievals    │
         └──────────────────┘
```

## Architecture

### Agent Hierarchy

All specialized agents extend `BaseAgent` and implement the following abstract methods:

1. **process_text(query: str) -> AgentResponse**: Full text processing with tool calling
2. **process_voice(query: str) -> str**: Concise voice response without tools
3. **stream_response(query: str) -> AsyncIterator[str]**: Streaming text response
4. **get_tools() -> List**: Domain-specific LangChain tools
5. **_system_prompt(voice_mode: bool) -> str**: Specialized system prompt

### Agent Types

1. **WorkoutPlannerAgent** - Exercise plans, form guidance, workout logging
2. **DietPlannerAgent** - Meal plans, nutrition, recipes, substitutions
3. **SupplementGuideAgent** - Supplement information (non-medical)
4. **TrackerAgent** - Progress tracking, adherence analysis, adjustments
5. **SchedulerAgent** - Schedule management, rescheduling, reminders
6. **GeneralAssistantAgent** - Motivation, casual conversation, general queries

### Classification Strategy

The AgentOrchestrator uses a fast classifier LLM (Claude Haiku) to route queries:

```python
Classification Prompt:
"Classify this fitness query into ONE category:
- workout: Exercise plans, form, demonstrations, logging sets
- diet: Meal plans, nutrition, recipes, food substitutions
- supplement: Supplement guidance and information
- tracker: Progress tracking, adherence, metrics
- scheduler: Schedule changes, reminders, timing
- general: Motivation, casual conversation, general questions

Respond with ONLY the category name."
```

The classifier uses:
- Model: Claude Haiku (fast, low-cost)
- Temperature: 0.1 (consistent routing)
- Max tokens: 10 (single word response)
- Caching: Voice mode caches by first 50 chars of query

## Components and Interfaces

### 1. WorkoutPlannerAgent

**File**: `backend/app/agents/workout_planner.py`

**Purpose**: Handles all workout-related queries including exercise plans, form guidance, demonstrations, and workout logging.

**Tools**:

```python
@tool
async def get_current_workout(context: AgentContext, db: AsyncSession) -> str:
    """Get today's workout plan for the user
    
    Returns:
        JSON string with workout details
    """
    
@tool
async def show_exercise_demo(exercise_name: str, db: AsyncSession) -> str:
    """Get GIF demonstration URL for an exercise
    
    Args:
        exercise_name: Name of the exercise
        
    Returns:
        URL to demonstration GIF
    """
    
@tool
async def log_set_completion(
    user_id: str,
    exercise: str,
    reps: int,
    weight: float,
    db: AsyncSession
) -> str:
    """Log a completed workout set
    
    Args:
        user_id: User identifier
        exercise: Exercise name
        reps: Number of repetitions
        weight: Weight used in kg
        
    Returns:
        Confirmation message
    """
    
@tool
async def suggest_workout_modification(
    context: AgentContext,
    reason: str,
    intensity_change: str
) -> str:
    """Suggest modifications to current workout
    
    Args:
        context: User context with fitness level and energy
        reason: Why modification needed
        intensity_change: "increase" | "decrease" | "maintain"
        
    Returns:
        Suggested modifications
    """
```

**System Prompt Structure**:
```
You are a professional workout planning assistant.

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Energy Level: {energy_level}

Current Workout Plan:
{current_workout_plan}

Guidelines:
- Be motivating but realistic
- Reference their specific plan
- Adjust based on energy level
- Never give medical advice
- Use tools to fetch data or log progress

[Voice mode: Keep responses under 30 seconds when spoken]
[Text mode: Provide detailed explanations with markdown]
```

### 2. DietPlannerAgent

**File**: `backend/app/agents/diet_planner.py`

**Purpose**: Handles all nutrition and meal planning queries including meal plans, recipes, substitutions, and nutritional information.

**Tools**:

```python
@tool
async def get_current_meal_plan(context: AgentContext, db: AsyncSession) -> str:
    """Get today's meal plan
    
    Returns:
        JSON string with meal details
    """
    
@tool
async def suggest_meal_substitution(
    context: AgentContext,
    meal_type: str,
    reason: str,
    db: AsyncSession
) -> str:
    """Suggest meal substitution
    
    Args:
        context: User context with dietary preferences
        meal_type: "breakfast" | "lunch" | "dinner" | "snack"
        reason: Why substitution needed
        
    Returns:
        Suggested alternative meals
    """
    
@tool
async def get_recipe_details(dish_name: str, db: AsyncSession) -> str:
    """Get recipe for a dish
    
    Args:
        dish_name: Name of the dish
        
    Returns:
        Recipe with ingredients and instructions
    """
    
@tool
async def calculate_nutrition(dish_name: str, db: AsyncSession) -> str:
    """Calculate nutritional information
    
    Args:
        dish_name: Name of the dish
        
    Returns:
        Macros and calories
    """
```

**System Prompt Structure**:
```
You are a professional nutrition and meal planning assistant.

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Dietary Preferences: {dietary_preferences}
- Allergies: {allergies}
- Restrictions: {restrictions}

Current Meal Plan:
{current_meal_plan}

Guidelines:
- Respect dietary preferences and restrictions
- Provide nutritional information
- Suggest practical alternatives
- Never give medical advice
- Use tools to fetch data

[Voice mode: Keep responses under 30 seconds when spoken]
[Text mode: Provide detailed nutritional breakdowns with markdown]
```

### 3. SupplementGuideAgent

**File**: `backend/app/agents/supplement_guide.py`

**Purpose**: Provides non-medical supplement information and guidance.

**Tools**:

```python
@tool
async def get_supplement_info(supplement_name: str) -> str:
    """Get information about a supplement
    
    Args:
        supplement_name: Name of supplement
        
    Returns:
        General information about the supplement
    """
    
@tool
async def check_supplement_interactions(supplements: List[str]) -> str:
    """Check for potential interactions
    
    Args:
        supplements: List of supplement names
        
    Returns:
        Potential interaction information
    """
```

**System Prompt Structure**:
```
You are a supplement information assistant providing NON-MEDICAL guidance.

CRITICAL DISCLAIMERS:
- You provide general information only
- You are NOT a medical professional
- Users should consult healthcare providers for medical advice
- You do NOT diagnose conditions or prescribe supplements

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}

Guidelines:
- Always include disclaimers
- Recommend consulting healthcare professionals
- Provide evidence-based information
- Be clear about limitations

[Voice mode: Keep responses under 30 seconds, include disclaimer]
[Text mode: Provide detailed information with prominent disclaimers]
```

### 4. TrackerAgent

**File**: `backend/app/agents/tracker.py`

**Purpose**: Tracks progress, analyzes adherence, and suggests adaptive adjustments.

**Tools**:

```python
@tool
async def get_workout_adherence(
    user_id: str,
    days: int,
    db: AsyncSession
) -> str:
    """Get workout adherence statistics
    
    Args:
        user_id: User identifier
        days: Number of days to analyze
        
    Returns:
        Adherence statistics
    """
    
@tool
async def get_progress_metrics(user_id: str, db: AsyncSession) -> str:
    """Get progress metrics (weight, measurements, etc.)
    
    Args:
        user_id: User identifier
        
    Returns:
        Progress metrics
    """
    
@tool
async def suggest_plan_adjustment(
    context: AgentContext,
    adherence_data: dict
) -> str:
    """Suggest plan adjustments based on adherence
    
    Args:
        context: User context
        adherence_data: Adherence statistics
        
    Returns:
        Suggested adjustments
    """
```

**System Prompt Structure**:
```
You are a progress tracking and adjustment assistant.

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}

Guidelines:
- Analyze patterns in behavior
- Suggest adaptive adjustments
- Be supportive and non-judgmental
- Focus on progress, not perfection
- Use tools to fetch data

[Voice mode: Keep responses under 30 seconds when spoken]
[Text mode: Provide detailed analytics with markdown]
```

### 5. SchedulerAgent

**File**: `backend/app/agents/scheduler.py`

**Purpose**: Manages workout and meal schedules, handles rescheduling, and manages reminder preferences.

**Tools**:

```python
@tool
async def get_upcoming_schedule(user_id: str, db: AsyncSession) -> str:
    """Get upcoming workouts and meals
    
    Args:
        user_id: User identifier
        
    Returns:
        Upcoming schedule
    """
    
@tool
async def reschedule_workout(
    workout_id: str,
    new_time: str,
    db: AsyncSession
) -> str:
    """Reschedule a workout
    
    Args:
        workout_id: Workout identifier
        new_time: New scheduled time (ISO format)
        
    Returns:
        Confirmation message
    """
    
@tool
async def update_reminder_preferences(
    user_id: str,
    reminder_type: str,
    enabled: bool,
    db: AsyncSession
) -> str:
    """Update reminder settings
    
    Args:
        user_id: User identifier
        reminder_type: Type of reminder
        enabled: Whether to enable
        
    Returns:
        Confirmation message
    """
```

**System Prompt Structure**:
```
You are a scheduling and reminder management assistant.

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}

Guidelines:
- Help optimize timing
- Handle conflicts gracefully
- Respect user preferences
- Use tools to fetch and update schedules

[Voice mode: Keep responses under 30 seconds when spoken]
[Text mode: Provide detailed schedule information with markdown]
```

### 6. GeneralAssistantAgent

**File**: `backend/app/agents/general_assistant.py`

**Purpose**: Handles general queries, provides motivation, and manages casual conversation.

**Tools**:

```python
@tool
async def get_user_stats(user_id: str, db: AsyncSession) -> str:
    """Get general user statistics
    
    Args:
        user_id: User identifier
        
    Returns:
        General statistics
    """
    
@tool
async def provide_motivation(context: AgentContext, db: AsyncSession) -> str:
    """Provide motivational message based on progress
    
    Args:
        context: User context with progress data
        
    Returns:
        Motivational message
    """
```

**System Prompt Structure**:
```
You are a friendly fitness assistant providing motivation and general support.

User Profile:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}

Guidelines:
- Be friendly and supportive
- Provide motivation based on progress
- Handle casual conversation naturally
- Use tools when relevant

[Voice mode: Keep responses under 30 seconds, be conversational]
[Text mode: Provide detailed responses with markdown]
```

### 7. Updated AgentOrchestrator

**File**: `backend/app/services/agent_orchestrator.py`

**Updates Required**:

1. **Update AgentType enum**:
```python
class AgentType(str, Enum):
    WORKOUT = "workout"
    DIET = "diet"
    SUPPLEMENT = "supplement"
    TRACKER = "tracker"
    SCHEDULER = "scheduler"
    GENERAL = "general"
    TEST = "test"
```

2. **Implement _classify_query**:
```python
async def _classify_query(self, query: str) -> AgentType:
    """Classify query using fast LLM"""
    
    # Check cache
    cache_key = query[:50].lower().strip()
    if cache_key in self._classification_cache:
        return self._classification_cache[cache_key]
    
    # Classify with fast LLM
    classifier = self._init_classifier_llm()
    
    messages = [
        SystemMessage(content="""Classify this fitness query into ONE category:
- workout: Exercise plans, form, demonstrations, logging sets
- diet: Meal plans, nutrition, recipes, food substitutions
- supplement: Supplement guidance and information
- tracker: Progress tracking, adherence, metrics
- scheduler: Schedule changes, reminders, timing
- general: Motivation, casual conversation, general questions

Respond with ONLY the category name."""),
        HumanMessage(content=query)
    ]
    
    result = await classifier.ainvoke(messages)
    agent_type_str = result.content.strip().lower()
    
    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        logger.warning(f"Unknown agent type: {agent_type_str}, defaulting to GENERAL")
        agent_type = AgentType.GENERAL
    
    # Cache in voice mode
    if self.mode == "voice":
        self._classification_cache[cache_key] = agent_type
    
    return agent_type
```

3. **Update _create_agent**:
```python
def _create_agent(self, agent_type: AgentType, context: AgentContext):
    """Factory method to create specialized agents"""
    from app.agents.workout_planner import WorkoutPlannerAgent
    from app.agents.diet_planner import DietPlannerAgent
    from app.agents.supplement_guide import SupplementGuideAgent
    from app.agents.tracker import TrackerAgent
    from app.agents.scheduler import SchedulerAgent
    from app.agents.general_assistant import GeneralAssistantAgent
    from app.agents.test_agent import TestAgent
    
    agent_map = {
        AgentType.WORKOUT: WorkoutPlannerAgent,
        AgentType.DIET: DietPlannerAgent,
        AgentType.SUPPLEMENT: SupplementGuideAgent,
        AgentType.TRACKER: TrackerAgent,
        AgentType.SCHEDULER: SchedulerAgent,
        AgentType.GENERAL: GeneralAssistantAgent,
        AgentType.TEST: TestAgent,
    }
    
    agent_class = agent_map.get(agent_type, GeneralAssistantAgent)
    return agent_class(context=context, db_session=self.db_session)
```

## Data Models

### Agent Tool Response Format

All tools return JSON strings that can be parsed by the LLM:

```python
{
    "success": bool,
    "data": dict | list | str,
    "error": Optional[str],
    "metadata": {
        "timestamp": str,
        "source": str
    }
}
```

### Workout Log Entry

```python
{
    "id": UUID,
    "user_id": UUID,
    "workout_id": UUID,
    "exercise": str,
    "reps": int,
    "weight": float,
    "completed_at": datetime
}
```

### Meal Plan Entry

```python
{
    "id": UUID,
    "user_id": UUID,
    "meal_type": str,  # breakfast, lunch, dinner, snack
    "dish_name": str,
    "calories": int,
    "protein": float,
    "carbs": float,
    "fats": float,
    "scheduled_time": datetime
}
```

### Schedule Entry

```python
{
    "id": UUID,
    "user_id": UUID,
    "type": str,  # workout, meal
    "scheduled_time": datetime,
    "completed": bool,
    "rescheduled_from": Optional[datetime]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:
- Voice mode response time properties (1.6, 2.6, 3.6, 4.6, 5.6, 6.6) can be combined into one property
- Text mode formatting properties (1.7, 2.7, 3.7, 4.7, 5.7, 6.7) can be combined into one property
- Classification routing properties (7.1-7.6) can be combined into one comprehensive property
- Database operation properties across agents can be consolidated

### Core Properties

Property 1: Agent Data Retrieval
*For any* agent and any user context, when the agent needs to retrieve user data, the agent should successfully fetch the data from the database using async operations
**Validates: Requirements 1.1, 2.1, 4.2, 5.1, 6.4**

Property 2: Agent Data Persistence
*For any* agent and any data modification, when the agent writes data to the database, the data should persist correctly and be retrievable in subsequent queries
**Validates: Requirements 1.3, 5.2, 5.3, 8.2**

Property 3: Voice Mode Response Conciseness
*For any* agent in voice mode, the response should be concise enough to be spoken in under 30 seconds (approximately 75 words or less)
**Validates: Requirements 1.6, 2.6, 3.6, 4.6, 5.6, 6.6**

Property 4: Text Mode Markdown Formatting
*For any* agent in text mode, the response should contain markdown formatting elements (headers, lists, bold, or code blocks)
**Validates: Requirements 1.7, 2.7, 3.7, 4.7, 5.7, 6.7**

Property 5: Classification Routing Accuracy
*For any* query with clear domain indicators (workout keywords, diet keywords, etc.), the AgentOrchestrator should route to the correct specialized agent matching the domain
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

Property 6: Classification Caching in Voice Mode
*For any* query in voice mode, when the same query (first 50 characters) is classified twice, the second classification should use the cached result without calling the LLM
**Validates: Requirements 7.8, 9.4**

Property 7: Dietary Constraint Satisfaction
*For any* user with dietary restrictions or allergies, when the Diet_Planning_Agent suggests meals or substitutions, none of the suggestions should violate the user's restrictions
**Validates: Requirements 2.2, 2.5**

Property 8: Supplement Disclaimer Inclusion
*For any* response from the Supplement_Guidance_Agent, the response should contain disclaimer text about non-medical guidance and consulting healthcare professionals
**Validates: Requirements 3.3, 3.4, 3.7**

Property 9: Adherence Calculation Accuracy
*For any* user with workout logs, when the Tracking_Adjustment_Agent calculates adherence, the percentage should equal (completed_workouts / scheduled_workouts) * 100
**Validates: Requirements 4.1**

Property 10: Schedule Conflict Detection
*For any* scheduling request that conflicts with an existing schedule entry, the Scheduler_Agent should detect the conflict and handle it appropriately
**Validates: Requirements 5.5**

Property 11: Database Error Handling
*For any* agent tool that encounters a database error, the tool should return an error response with an informative message rather than raising an unhandled exception
**Validates: Requirements 8.4, 8.6**

Property 12: Conversation History Truncation
*For any* agent with conversation history longer than the limit, the agent should only include the last N messages (5 for voice, 10 for text) when building the message chain
**Validates: Requirements 9.5**

Property 13: Agent Caching in Voice Mode
*For any* AgentOrchestrator in voice mode, when the same agent type is requested twice, the second request should reuse the cached agent instance
**Validates: Requirements 9.3**

Property 14: Classification Fallback
*For any* query that cannot be confidently classified, the AgentOrchestrator should default to routing to the General_Assistant_Agent
**Validates: Requirements 7.9**

## Error Handling

### Database Errors

All agent tools must handle database errors gracefully:

```python
try:
    # Database operation
    result = await db.execute(query)
    await db.commit()
    return json.dumps({
        "success": True,
        "data": result
    })
except SQLAlchemyError as e:
    logger.error(f"Database error in tool: {e}")
    await db.rollback()
    return json.dumps({
        "success": False,
        "error": "Unable to complete operation. Please try again."
    })
```

### LLM Errors

The AgentOrchestrator must handle LLM failures:

```python
try:
    result = await agent.process_text(query)
    return result
except Exception as e:
    logger.error(f"Agent processing error: {e}")
    return AgentResponse(
        content="I'm having trouble processing your request. Please try again.",
        agent_type="error",
        tools_used=[],
        metadata={"error": str(e)}
    )
```

### Classification Errors

If classification fails, default to General_Assistant_Agent:

```python
try:
    agent_type = AgentType(agent_type_str)
except ValueError:
    logger.warning(f"Unknown agent type: {agent_type_str}, defaulting to GENERAL")
    agent_type = AgentType.GENERAL
```

### Tool Execution Errors

Tools must return error responses rather than raising exceptions:

```python
@tool
async def example_tool(param: str, db: AsyncSession) -> str:
    """Example tool with error handling"""
    try:
        # Tool logic
        result = await perform_operation(param, db)
        return json.dumps({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return json.dumps({
            "success": False,
            "error": "Operation failed. Please try again."
        })
```

## Testing Strategy

### Unit Tests

Each agent requires unit tests covering:

1. **Tool Functionality**: Each tool works correctly with valid inputs
2. **Text Mode Processing**: Agent responds correctly in text mode
3. **Voice Mode Processing**: Agent responds concisely in voice mode
4. **System Prompt Generation**: Prompts include correct context
5. **Error Handling**: Tools handle errors gracefully

Example test structure:

```python
@pytest.mark.asyncio
async def test_workout_agent_get_current_workout(db_session, test_user):
    """Test workout retrieval tool"""
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    agent = WorkoutPlannerAgent(context=context, db_session=db_session)
    tools = agent.get_tools()
    
    # Find get_current_workout tool
    workout_tool = next(t for t in tools if t.name == "get_current_workout")
    
    # Call tool
    result = await workout_tool.ainvoke({"context": context, "db": db_session})
    
    # Verify result
    assert "success" in result
    data = json.loads(result)
    assert data["success"] is True
```

### Integration Tests

Integration tests verify agent routing and end-to-end functionality:

```python
@pytest.mark.asyncio
async def test_agent_routing_workout_query(db_session, test_user):
    """Test workout queries route to workout agent"""
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What's my workout today?"
    )
    
    assert orchestrator.last_agent_type == AgentType.WORKOUT
    assert len(response.content) > 0
    assert response.agent_type == "workout"
```

### Property-Based Tests

Property tests verify universal properties across many inputs:

```python
from hypothesis import given, strategies as st

@given(
    fitness_level=st.sampled_from(["beginner", "intermediate", "advanced"]),
    goal=st.sampled_from(["fat_loss", "muscle_gain", "general_fitness"])
)
@pytest.mark.asyncio
async def test_voice_mode_response_conciseness(fitness_level, goal, db_session, test_user):
    """Property: Voice responses should be concise (<75 words)"""
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level=fitness_level,
        primary_goal=goal
    )
    
    agent = WorkoutPlannerAgent(context=context, db_session=db_session)
    response = await agent.process_voice("What should I do today?")
    
    word_count = len(response.split())
    assert word_count <= 75, f"Voice response too long: {word_count} words"
```

### Performance Tests

Performance tests verify latency requirements:

```python
@pytest.mark.asyncio
async def test_voice_mode_latency(db_session, test_user):
    """Test voice mode meets <2s latency requirement"""
    orchestrator = AgentOrchestrator(db_session=db_session, mode="voice")
    await orchestrator.warm_up()
    
    import time
    latencies = []
    
    for _ in range(100):
        start = time.time()
        await orchestrator.route_query(
            user_id=str(test_user.id),
            query="Quick workout tip?",
            voice_mode=True
        )
        latency = time.time() - start
        latencies.append(latency)
    
    # Check 95th percentile
    latencies.sort()
    p95 = latencies[94]  # 95th percentile of 100 samples
    assert p95 < 2.0, f"Voice latency too high: {p95}s"
```

### Test Organization

```
backend/tests/
├── test_workout_agent.py           # Workout agent unit tests
├── test_diet_agent.py              # Diet agent unit tests
├── test_supplement_agent.py        # Supplement agent unit tests
├── test_tracker_agent.py           # Tracker agent unit tests
├── test_scheduler_agent.py         # Scheduler agent unit tests
├── test_general_agent.py           # General agent unit tests
├── test_agent_orchestrator.py      # Orchestrator unit tests
├── test_agent_routing.py           # Integration tests for routing
├── test_agent_properties.py        # Property-based tests
└── test_agent_performance.py       # Performance tests
```

### Test Configuration

All tests use pytest with async support:

```bash
# Run all agent tests
poetry run pytest backend/tests/test_*_agent.py -v

# Run integration tests
poetry run pytest backend/tests/test_agent_routing.py -v

# Run property tests (100 iterations minimum)
poetry run pytest backend/tests/test_agent_properties.py -v --hypothesis-iterations=100

# Run performance tests
poetry run pytest backend/tests/test_agent_performance.py -v
```

### Dual Testing Approach

This design uses both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs (minimum 100 iterations)
- Both are complementary and necessary for comprehensive coverage

Unit tests focus on:
- Specific tool behaviors with known inputs
- Integration between agents and orchestrator
- Error handling scenarios

Property tests focus on:
- Response format consistency across all agents
- Performance characteristics across many queries
- Constraint satisfaction (dietary restrictions, etc.)
- Classification accuracy across diverse queries

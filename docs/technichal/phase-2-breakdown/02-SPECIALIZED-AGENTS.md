# Sub-Doc 2: Specialized Agent Implementation

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Sub-Doc 1 (LangChain Foundation)

---

## Objective

Implement 6 specialized AI agents that handle domain-specific fitness queries:
1. **Workout Planner Agent** - Exercise plans, form guidance, demonstrations
2. **Diet Planner Agent** - Meal plans, nutrition, recipes
3. **Supplement Guidance Agent** - Supplement information (non-medical)
4. **Tracking & Adjustment Agent** - Progress tracking, plan adjustments
5. **Scheduling & Reminder Agent** - Schedule management, timing
6. **General Assistant Agent** - Motivation, casual conversation

Each agent will have:
- Domain-specific tools (LangChain `@tool` decorated functions)
- Specialized system prompts
- Database integration for user data
- Support for both text and voice modes

---

## Prerequisites Verification

Before starting, verify Sub-Doc 1 is complete:

```bash
# 1. Base agent exists
python -c "from app.agents.base import BaseAgent; print('✓')"

# 2. Orchestrator exists
python -c "from app.services.agent_orchestrator import AgentOrchestrator; print('✓')"

# 3. Test agent works
poetry run pytest backend/tests/test_langchain_foundation.py -v

# 4. Context loader works
python -c "from app.services.context_loader import load_agent_context; print('✓')"
```

---

## Agent Implementation Pattern

Each agent follows this structure:

```python
from typing import List, AsyncIterator
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from app.agents.base import BaseAgent
from app.agents.context import AgentResponse


class SpecializedAgent(BaseAgent):
    """Agent for specific domain"""
    
    async def process_text(self, query: str) -> AgentResponse:
        """Full text processing with tools"""
        tools = self.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._system_prompt(voice_mode=False)),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=5
        )
        
        result = await agent_executor.ainvoke({
            "input": query,
            "chat_history": self._format_chat_history()
        })
        
        return AgentResponse(
            content=result["output"],
            agent_type="specialized",
            tools_used=result.get("intermediate_steps", [])
        )
    
    async def process_voice(self, query: str) -> str:
        """Concise voice response without tools"""
        messages = self._build_messages(query, voice_mode=True)
        result = await self.llm.ainvoke(messages)
        return result.content
    
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """Stream text response"""
        messages = self._build_messages(query, voice_mode=False)
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    def get_tools(self) -> List:
        """Domain-specific tools"""
        # Define tools here
        pass
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """Domain-specific prompt"""
        # Define prompt here
        pass
```

---

## Agent 1: Workout Planner Agent

**File:** `backend/app/agents/workout_planner.py`

### Tools

```python
@tool
async def get_current_workout() -> str:
    """Get today's workout plan for the user"""
    # Query WorkoutSchedule from database
    pass

@tool
async def show_exercise_demo(exercise_name: str) -> str:
    """Get GIF demonstration URL for an exercise
    
    Args:
        exercise_name: Name of the exercise
    """
    # Query Exercise table for demo_gif_url
    pass

@tool
async def log_set_completion(exercise: str, reps: int, weight: float) -> str:
    """Log a completed workout set
    
    Args:
        exercise: Exercise name
        reps: Number of repetitions
        weight: Weight used in kg
    """
    # Insert into WorkoutLog table
    pass

@tool
async def suggest_workout_modification(reason: str, intensity_change: str) -> str:
    """Suggest modifications to current workout
    
    Args:
        reason: Why modification needed
        intensity_change: "increase" | "decrease" | "maintain"
    """
    # Use LLM to generate smart modifications
    pass
```

### System Prompt

```python
def _system_prompt(self, voice_mode: bool = False) -> str:
    base = f"""You are a professional workout planning assistant.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

Current Workout Plan:
{json.dumps(self.context.current_workout_plan, indent=2)}

Guidelines:
- Be motivating but realistic
- Reference their specific plan
- Adjust based on energy level
- Never give medical advice
- Use tools to fetch data or log progress
"""
    
    if voice_mode:
        base += "\n- Keep responses under 30 seconds when spoken\n- Be conversational"
    else:
        base += "\n- Provide detailed explanations\n- Use markdown formatting"
    
    return base
```

**Verification:**
```bash
poetry run pytest backend/tests/test_workout_agent.py -v
```

---

## Agent 2: Diet Planner Agent

**File:** `backend/app/agents/diet_planner.py`

### Tools

```python
@tool
async def get_current_meal_plan() -> str:
    """Get today's meal plan"""
    pass

@tool
async def suggest_meal_substitution(meal_type: str, reason: str) -> str:
    """Suggest meal substitution
    
    Args:
        meal_type: "breakfast" | "lunch" | "dinner" | "snack"
        reason: Why substitution needed
    """
    pass

@tool
async def get_recipe_details(dish_name: str) -> str:
    """Get recipe for a dish
    
    Args:
        dish_name: Name of the dish
    """
    pass

@tool
async def calculate_nutrition(dish_name: str) -> str:
    """Calculate nutritional information
    
    Args:
        dish_name: Name of the dish
    """
    pass
```

### System Prompt

Focus on nutrition, dietary preferences, allergies, and meal timing.

**Verification:**
```bash
poetry run pytest backend/tests/test_diet_agent.py -v
```

---

## Agent 3: Supplement Guidance Agent

**File:** `backend/app/agents/supplement_guide.py`

### Tools

```python
@tool
async def get_supplement_info(supplement_name: str) -> str:
    """Get information about a supplement
    
    Args:
        supplement_name: Name of supplement
    """
    pass

@tool
async def check_supplement_interactions(supplements: List[str]) -> str:
    """Check for potential interactions
    
    Args:
        supplements: List of supplement names
    """
    pass
```

### System Prompt

**CRITICAL:** Emphasize non-medical guidance, recommend consulting healthcare professionals.

**Verification:**
```bash
poetry run pytest backend/tests/test_supplement_agent.py -v
```

---

## Agent 4: Tracking & Adjustment Agent

**File:** `backend/app/agents/tracker.py`

### Tools

```python
@tool
async def get_workout_adherence(days: int = 7) -> str:
    """Get workout adherence statistics
    
    Args:
        days: Number of days to analyze
    """
    pass

@tool
async def get_progress_metrics() -> str:
    """Get progress metrics (weight, measurements, etc.)"""
    pass

@tool
async def suggest_plan_adjustment(adherence_data: dict) -> str:
    """Suggest plan adjustments based on adherence
    
    Args:
        adherence_data: Adherence statistics
    """
    pass
```

### System Prompt

Focus on progress tracking, pattern detection, and adaptive adjustments.

**Verification:**
```bash
poetry run pytest backend/tests/test_tracker_agent.py -v
```

---

## Agent 5: Scheduling & Reminder Agent

**File:** `backend/app/agents/scheduler.py`

### Tools

```python
@tool
async def get_upcoming_schedule() -> str:
    """Get upcoming workouts and meals"""
    pass

@tool
async def reschedule_workout(workout_id: str, new_time: str) -> str:
    """Reschedule a workout
    
    Args:
        workout_id: Workout identifier
        new_time: New scheduled time
    """
    pass

@tool
async def update_reminder_preferences(reminder_type: str, enabled: bool) -> str:
    """Update reminder settings
    
    Args:
        reminder_type: Type of reminder
        enabled: Whether to enable
    """
    pass
```

### System Prompt

Focus on schedule management, timing optimization, and reminder preferences.

**Verification:**
```bash
poetry run pytest backend/tests/test_scheduler_agent.py -v
```

---

## Agent 6: General Assistant Agent

**File:** `backend/app/agents/general_assistant.py`

### Tools

```python
@tool
async def get_user_stats() -> str:
    """Get general user statistics"""
    pass

@tool
async def provide_motivation() -> str:
    """Provide motivational message based on progress"""
    pass
```

### System Prompt

Friendly, motivating, handles casual conversation and general queries.

**Verification:**
```bash
poetry run pytest backend/tests/test_general_agent.py -v
```

---

## Update Agent Orchestrator

**File:** `backend/app/services/agent_orchestrator.py`

Update the `_classify_query` method to use actual classification:

```python
async def _classify_query(self, query: str) -> AgentType:
    """Classify query using LLM"""
    
    # Check cache
    if self.mode == "voice":
        cache_key = query[:50]
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]
    
    # Classify with fast LLM
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
    
    # Use fast classifier LLM
    from app.agents.test_agent import TestAgent
    test_agent = TestAgent(context=AgentContext(
        user_id="classifier",
        fitness_level="beginner",
        primary_goal="general_fitness"
    ))
    
    result = await test_agent.classifier_llm.ainvoke(messages)
    agent_type_str = result.content.strip().lower()
    
    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        logger.warning(f"Unknown agent type: {agent_type_str}, defaulting to GENERAL")
        agent_type = AgentType.GENERAL
    
    # Cache
    if self.mode == "voice":
        self._classification_cache[cache_key] = agent_type
    
    return agent_type
```

Update the `_create_agent` method:

```python
def _create_agent(self, agent_type: AgentType, context: AgentContext):
    """Factory method to create specialized agents"""
    from app.agents.workout_planner import WorkoutPlannerAgent
    from app.agents.diet_planner import DietPlannerAgent
    from app.agents.supplement_guide import SupplementGuideAgent
    from app.agents.tracker import TrackerAgent
    from app.agents.scheduler import SchedulerAgent
    from app.agents.general_assistant import GeneralAssistantAgent
    
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
    return agent_class(context=context, db_session=self.db)
```

---

## Integration Tests

**File:** `backend/tests/test_specialized_agents.py`

```python
"""Integration tests for all specialized agents"""
import pytest
from app.services.agent_orchestrator import AgentOrchestrator, AgentType


@pytest.mark.asyncio
async def test_workout_agent_routing(db_session, test_user):
    """Test workout queries route to workout agent"""
    orchestrator = AgentOrchestrator(db_session=db_session)
    
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What's my workout today?"
    )
    
    assert orchestrator.last_agent_type == AgentType.WORKOUT
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_diet_agent_routing(db_session, test_user):
    """Test diet queries route to diet agent"""
    orchestrator = AgentOrchestrator(db_session=db_session)
    
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What should I eat for breakfast?"
    )
    
    assert orchestrator.last_agent_type == AgentType.DIET


@pytest.mark.asyncio
async def test_all_agents_respond(db_session, test_user):
    """Test all agents can respond"""
    orchestrator = AgentOrchestrator(db_session=db_session)
    
    queries = {
        AgentType.WORKOUT: "Show me bench press form",
        AgentType.DIET: "Give me a high protein meal",
        AgentType.SUPPLEMENT: "Tell me about creatine",
        AgentType.TRACKER: "How's my progress this week?",
        AgentType.SCHEDULER: "When is my next workout?",
        AgentType.GENERAL: "I'm feeling motivated today!"
    }
    
    for agent_type, query in queries.items():
        response = await orchestrator.route_query(
            user_id=str(test_user.id),
            query=query,
            agent_type=agent_type
        )
        
        assert len(response.content) > 0
        assert response.agent_type == agent_type.value
```

---

## Verification Checklist

- [ ] All 6 agents implemented
- [ ] Each agent has domain-specific tools
- [ ] Each agent has specialized system prompt
- [ ] Orchestrator updated with agent map
- [ ] Classification logic implemented
- [ ] All agent tests pass
- [ ] Integration tests pass
- [ ] Agents work in both text and voice modes

**Final Test:**
```bash
poetry run pytest backend/tests/test_specialized_agents.py -v
```

---

## Success Criteria

Sub-Doc 2 is complete when:

✅ All 6 specialized agents implemented  
✅ Each agent has working tools  
✅ Orchestrator routes correctly  
✅ Classification works accurately  
✅ All tests pass  
✅ Both text and voice modes work  

**Estimated Time:** 5-7 days

**Next:** [03-TEXT-CHAT-API.md](./03-TEXT-CHAT-API.md)

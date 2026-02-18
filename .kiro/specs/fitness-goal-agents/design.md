# Design Document: Fitness and Goal Setting Agents

## Overview

The Fitness and Goal Setting Agents feature implements the first two specialized onboarding agents that guide users through fitness assessment (Steps 1-2) and goal setting (Step 3). These agents provide conversational, personalized guidance using LangChain and Anthropic Claude to understand the user's current fitness level, exercise experience, physical limitations, and fitness objectives.

This feature builds directly on the Onboarding Agent Foundation (Spec 1), which provides the base agent architecture, orchestration service, and API endpoints. The two agents implemented here demonstrate the complete pattern for conversational onboarding: collecting information through natural dialogue, saving structured data to agent context, and seamlessly handing off to the next agent.

### Key Design Principles

1. **Conversational Data Collection**: Extract structured data from natural language without rigid forms
2. **Progressive Context Building**: Each agent adds to shared context for subsequent agents
3. **Completion Intent Detection**: Recognize when users are ready to move forward without explicit commands
4. **Graceful Error Handling**: Validate data and handle errors without disrupting conversation flow
5. **Context-Aware Responses**: Use previous agent data to provide personalized guidance

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              OnboardingAgentOrchestrator                     │
│         (from onboarding-agent-foundation)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ Fitness          │      │ Goal Setting     │
│ Assessment Agent │─────>│ Agent            │
│ (Steps 1-2)      │      │ (Step 3)         │
└──────────────────┘      └──────────────────┘
        │                         │
        ▼                         ▼
┌──────────────────────────────────────────┐
│         Agent Context Storage            │
│  fitness_assessment: {...}               │
│  goal_setting: {...}                     │
└──────────────────────────────────────────┘
```

### Agent Interaction Flow

```
User: "I'm a beginner"
    ↓
FitnessAssessmentAgent
    ↓
LangChain Tool-Calling Agent
    ↓
LLM (Claude Sonnet 4) + Tools
    ↓
save_fitness_assessment tool
    ↓
agent_context["fitness_assessment"] = {
    fitness_level: "beginner",
    ...
}
    ↓
step_complete=True, next_action="advance_step"
    ↓
Orchestrator advances to GoalSettingAgent
    ↓
User: "I want to build muscle"
    ↓
GoalSettingAgent (reads fitness_level from context)
    ↓
save_fitness_goals tool
    ↓
agent_context["goal_setting"] = {
    primary_goal: "muscle_gain",
    ...
}
```

## Components and Interfaces

### 1. Fitness Assessment Agent

#### Class Definition

```python
from app.agents.onboarding.base import BaseOnboardingAgent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from datetime import datetime
from uuid import UUID

class FitnessAssessmentAgent(BaseOnboardingAgent):
    """
    Specialized agent for assessing user's fitness level and experience.
    
    This agent handles Steps 1-2 of onboarding, collecting information about:
    - Current fitness level (beginner/intermediate/advanced)
    - Exercise experience and frequency
    - Physical limitations (equipment, injuries - non-medical)
    
    The agent uses conversational AI to extract structured data from natural
    language responses and saves it to agent_context for use by subsequent agents.
    """
    
    agent_type = "fitness_assessment"
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about fitness assessment.
        
        Uses LangChain's tool-calling agent to:
        1. Understand user's fitness information from natural language
        2. Ask clarifying questions when needed
        3. Call save_fitness_assessment tool when information is complete
        4. Set step_complete=True to trigger advancement
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Build prompt with system instructions
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(),
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.get_tools(),
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # TODO: Load from conversation_history
        })
        
        # Check if step is complete
        step_complete = await self._check_if_complete(user_id)
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action="advance_step" if step_complete else "continue_conversation"
        )

    
    def get_tools(self) -> List:
        """
        Get fitness assessment specific tools.
        
        Returns:
            List containing save_fitness_assessment tool
        """
        @tool
        async def save_fitness_assessment(
            fitness_level: str,
            experience_details: dict,
            limitations: list
        ) -> dict:
            """
            Save fitness assessment data to agent context.
            
            Call this tool when you have collected:
            - Fitness level (beginner/intermediate/advanced)
            - Exercise experience details (frequency, duration, types)
            - Physical limitations (equipment, injuries - non-medical)
            
            Args:
                fitness_level: User's fitness level (beginner/intermediate/advanced)
                experience_details: Dict with keys: frequency, duration, types
                limitations: List of limitation strings
                
            Returns:
                Dict with status and message
            """
            # Validate fitness_level
            valid_levels = ["beginner", "intermediate", "advanced"]
            fitness_level_lower = fitness_level.lower().strip()
            
            if fitness_level_lower not in valid_levels:
                return {
                    "status": "error",
                    "message": f"Invalid fitness_level. Must be one of: {valid_levels}"
                }
            
            # Prepare data
            assessment_data = {
                "fitness_level": fitness_level_lower,
                "experience_details": experience_details,
                "limitations": [lim.strip() for lim in limitations],
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context
            try:
                await self.save_context(user_id, assessment_data)
                return {
                    "status": "success",
                    "message": "Fitness assessment saved successfully"
                }
            except Exception as e:
                logger.error(f"Error saving fitness assessment: {e}")
                return {
                    "status": "error",
                    "message": "Failed to save fitness assessment. Please try again."
                }
        
        return [save_fitness_assessment]
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for fitness assessment agent.
        
        Returns:
            Hardcoded system prompt defining agent role and behavior
        """
        return """You are a Fitness Assessment Agent helping users determine their fitness level.

Your role:
- Ask friendly questions about their exercise experience
- Assess their fitness level (beginner/intermediate/advanced)
- Identify any physical limitations (equipment, injuries - non-medical)
- Be encouraging and non-judgmental

Guidelines:
- Keep questions conversational, ask 1-2 questions at a time
- Don't overwhelm with too many questions at once
- Never provide medical advice
- If medical topics are mentioned, acknowledge but redirect to fitness questions
- When you have collected fitness level, experience details, and limitations, call save_fitness_assessment tool
- After saving successfully, let the user know we'll move to goal setting

Fitness Level Definitions:
- Beginner: Little to no exercise experience, or returning after long break
- Intermediate: Regular exercise for 6+ months, comfortable with basic movements
- Advanced: Consistent training for 2+ years, experienced with various exercises

When to call save_fitness_assessment:
- User has clearly indicated their fitness level
- You understand their exercise experience (frequency, duration, types)
- You know their limitations (equipment, injuries, etc.)
- User confirms the information is correct or says they're ready to move on
"""
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if fitness assessment step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains fitness_assessment data
        """
        from sqlalchemy import select
        from app.models.onboarding import OnboardingState
        
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            return "fitness_assessment" in state.agent_context
        
        return False
```


### 2. Goal Setting Agent

#### Class Definition

```python
class GoalSettingAgent(BaseOnboardingAgent):
    """
    Specialized agent for defining user's fitness goals.
    
    This agent handles Step 3 of onboarding, collecting information about:
    - Primary fitness goal (fat_loss/muscle_gain/general_fitness)
    - Secondary goals (optional)
    - Target weight and body fat percentage (optional)
    
    The agent accesses fitness_level from the previous agent's context to
    provide realistic goal recommendations appropriate for the user's level.
    """
    
    agent_type = "goal_setting"
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about fitness goals.
        
        Uses LangChain's tool-calling agent to:
        1. Understand user's fitness goals from natural language
        2. Reference fitness level from previous agent context
        3. Set realistic expectations based on fitness level
        4. Call save_fitness_goals tool when information is complete
        5. Set step_complete=True to trigger advancement
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Build prompt with context from fitness assessment
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(),
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.get_tools(),
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # TODO: Load from conversation_history
        })
        
        # Check if step is complete
        step_complete = await self._check_if_complete(user_id)
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action="advance_step" if step_complete else "continue_conversation"
        )
    
    def get_tools(self) -> List:
        """
        Get goal setting specific tools.
        
        Returns:
            List containing save_fitness_goals tool
        """
        @tool
        async def save_fitness_goals(
            primary_goal: str,
            secondary_goal: str | None = None,
            target_weight_kg: float | None = None,
            target_body_fat_percentage: float | None = None
        ) -> dict:
            """
            Save fitness goals to agent context.
            
            Call this tool when you have collected:
            - Primary fitness goal (fat_loss/muscle_gain/general_fitness)
            - Optional secondary goal
            - Optional target weight in kilograms
            - Optional target body fat percentage
            
            Args:
                primary_goal: Primary fitness goal
                secondary_goal: Optional secondary goal
                target_weight_kg: Optional target weight (30-300 kg)
                target_body_fat_percentage: Optional target body fat (3-50%)
                
            Returns:
                Dict with status and message
            """
            # Validate primary_goal
            valid_goals = ["fat_loss", "muscle_gain", "general_fitness"]
            primary_goal_lower = primary_goal.lower().strip().replace(" ", "_")
            
            if primary_goal_lower not in valid_goals:
                return {
                    "status": "error",
                    "message": f"Invalid primary_goal. Must be one of: {valid_goals}"
                }
            
            # Validate target_weight_kg if provided
            if target_weight_kg is not None:
                if not (30 <= target_weight_kg <= 300):
                    return {
                        "status": "error",
                        "message": "target_weight_kg must be between 30 and 300"
                    }
            
            # Validate target_body_fat_percentage if provided
            if target_body_fat_percentage is not None:
                if not (3 <= target_body_fat_percentage <= 50):
                    return {
                        "status": "error",
                        "message": "target_body_fat_percentage must be between 3 and 50"
                    }
            
            # Prepare data
            goals_data = {
                "primary_goal": primary_goal_lower,
                "secondary_goal": secondary_goal.lower().strip().replace(" ", "_") if secondary_goal else None,
                "target_weight_kg": target_weight_kg,
                "target_body_fat_percentage": target_body_fat_percentage,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context
            try:
                await self.save_context(user_id, goals_data)
                return {
                    "status": "success",
                    "message": "Fitness goals saved successfully"
                }
            except Exception as e:
                logger.error(f"Error saving fitness goals: {e}")
                return {
                    "status": "error",
                    "message": "Failed to save fitness goals. Please try again."
                }
        
        return [save_fitness_goals]
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for goal setting agent with context from fitness assessment.
        
        Returns:
            System prompt including fitness level and limitations from previous agent
        """
        # Get fitness assessment context
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        limitations = self.context.get("fitness_assessment", {}).get("limitations", [])
        
        limitations_str = ", ".join(limitations) if limitations else "none mentioned"
        
        return f"""You are a Goal Setting Agent helping users define their fitness objectives.

Context from previous steps:
- Fitness Level: {fitness_level}
- Limitations: {limitations_str}

Your role:
- Understand their primary fitness goal (fat loss, muscle gain, or general fitness)
- Identify any secondary goals
- Set realistic expectations based on their {fitness_level} fitness level
- Explain how the system will help achieve these goals

Guidelines:
- Be realistic but encouraging
- Explain what each goal means
- Help prioritize if they have multiple goals
- Reference their fitness level when setting expectations
- Ask about optional target metrics (weight, body fat %) but don't require them
- When you have collected primary goal and user confirms, call save_fitness_goals tool
- After saving successfully, let the user know we'll create their workout plan next

Goal Definitions:
- Fat Loss: Reduce body fat while maintaining muscle mass
- Muscle Gain: Build muscle mass and strength
- General Fitness: Improve overall health, endurance, and well-being

Realistic Expectations by Fitness Level:
- Beginner: Focus on building habits and foundational strength
- Intermediate: Can pursue specific goals with structured programming
- Advanced: Can handle aggressive goals with proper recovery

When to call save_fitness_goals:
- User has clearly stated their primary goal
- You've discussed realistic expectations
- User confirms the goal or says they're ready to move on
- Optional: User has provided target metrics (weight, body fat %)
"""
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if goal setting step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains goal_setting data
        """
        from sqlalchemy import select
        from app.models.onboarding import OnboardingState
        
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            return "goal_setting" in state.agent_context
        
        return False
```

### 3. Base Onboarding Agent Extension

The agents extend the BaseOnboardingAgent class from Spec 1, which provides:

- `__init__(db: AsyncSession, context: dict)`: Constructor with database session and agent context
- `_init_llm()`: LLM initialization with Claude Sonnet 4
- `save_context(user_id: UUID, agent_data: dict)`: Save data to agent_context in OnboardingState
- Abstract methods that must be implemented: `process_message`, `get_tools`, `get_system_prompt`

The key difference from the base agent is that onboarding agents:
- Use LangChain's tool-calling agent pattern
- Have specific tools for saving structured data
- Check completion status after processing messages
- Set `step_complete` and `next_action` in responses

## Data Models

### Agent Context Structure

#### Fitness Assessment Context

```python
{
    "fitness_assessment": {
        "fitness_level": "intermediate",  # beginner/intermediate/advanced
        "experience_details": {
            "frequency": "3 times per week",
            "duration": "45-60 minutes",
            "types": ["weightlifting", "cardio"]
        },
        "limitations": [
            "no_equipment_at_home",
            "previous_knee_injury"
        ],
        "completed_at": "2024-01-15T10:30:00Z"
    }
}
```

#### Goal Setting Context

```python
{
    "goal_setting": {
        "primary_goal": "muscle_gain",  # fat_loss/muscle_gain/general_fitness
        "secondary_goal": "fat_loss",   # optional
        "target_weight_kg": 75.0,       # optional, 30-300
        "target_body_fat_percentage": 15.0,  # optional, 3-50
        "completed_at": "2024-01-15T10:35:00Z"
    }
}
```

### Combined Context After Both Agents

```python
{
    "fitness_assessment": {
        "fitness_level": "intermediate",
        "experience_details": {...},
        "limitations": [...],
        "completed_at": "2024-01-15T10:30:00Z"
    },
    "goal_setting": {
        "primary_goal": "muscle_gain",
        "secondary_goal": "fat_loss",
        "target_weight_kg": 75.0,
        "target_body_fat_percentage": 15.0,
        "completed_at": "2024-01-15T10:35:00Z"
    }
}
```

This combined context is available to all subsequent agents (Workout Planning, Diet Planning, Scheduling).


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Tool Input Validation

*For any* call to save_fitness_assessment or save_fitness_goals with invalid parameters (fitness_level not in valid set, target_weight_kg outside range 30-300, target_body_fat_percentage outside range 3-50), the tool should return an error status without saving data to agent_context.

**Validates: Requirements 3.3, 3.7, 6.3, 6.7, 11.1, 11.3, 13.2, 13.3**

### Property 2: Tool Success Persistence

*For any* successful call to save_fitness_assessment or save_fitness_goals with valid parameters, the data should be persisted to agent_context in OnboardingState with a completed_at timestamp in ISO 8601 format, and the tool should return success status.

**Validates: Requirements 3.4, 3.5, 3.6, 6.4, 6.5, 6.6, 11.5**

### Property 3: Completion Detection and Step Advancement

*For any* agent that has successfully saved its data to agent_context, when process_message is called, the response should have step_complete=True and next_action="advance_step", and the OnboardingState current_step should be incremented with current_agent updated to reflect the new agent type.

**Validates: Requirements 1.4, 1.5, 4.5, 4.6, 8.3, 8.4, 8.5, 14.1, 14.2, 14.3, 14.4, 14.5**

### Property 4: Context Handover Integrity

*For any* GoalSettingAgent instantiation, the agent should have access to fitness_assessment data from agent_context, and the system prompt should include fitness_level and limitations from that context.

**Validates: Requirements 4.2, 7.1, 7.2, 7.3, 7.5**

### Property 5: Data Normalization

*For any* string data saved to agent_context (fitness_level, primary_goal, secondary_goal), the data should be normalized to lowercase with whitespace trimmed, and limitations should be stored as a list of trimmed strings.

**Validates: Requirements 13.1, 13.4, 13.6**

### Property 6: Agent Response Validity

*For any* call to process_message on FitnessAssessmentAgent or GoalSettingAgent, the returned AgentResponse should contain all required fields (message, agent_type, step_complete, next_action) with correct types.

**Validates: Requirements 1.2, 4.4**

### Property 7: Completion Intent Recognition

*For any* user message containing completion phrases ("that's all", "I'm done", "let's move on", "next", "looks good", "yes"), if the agent has collected all required information, the agent should call the appropriate save tool.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 8: Goal Type Parsing

*For any* natural language input expressing a fitness goal (e.g., "lose weight", "build muscle", "get fit"), the GoalSettingAgent should correctly map it to one of the valid goal types (fat_loss, muscle_gain, general_fitness).

**Validates: Requirements 2.1, 2.4, 5.1**

### Property 9: Fitness Level Classification

*For any* natural language input expressing fitness experience (e.g., "I'm new to this", "I've been working out for years"), the FitnessAssessmentAgent should correctly classify it as beginner, intermediate, or advanced.

**Validates: Requirements 2.1, 2.4**

### Property 10: Transaction Integrity on Failure

*For any* tool execution that encounters a database error or validation failure, the agent_context should remain unchanged (no partial updates), and the tool should return an error status allowing retry.

**Validates: Requirements 11.2, 11.3, 11.4**

## Error Handling

### Error Categories

1. **Validation Errors**
   - Invalid fitness_level (not beginner/intermediate/advanced)
   - Invalid primary_goal (not fat_loss/muscle_gain/general_fitness)
   - target_weight_kg out of range (30-300)
   - target_body_fat_percentage out of range (3-50)
   - Missing required parameters

2. **Database Errors**
   - Connection failures
   - Transaction commit failures
   - OnboardingState not found

3. **LLM Errors**
   - API rate limiting
   - API failures
   - Parsing errors in tool calls

4. **Context Errors**
   - Missing fitness_assessment context when GoalSettingAgent starts
   - Corrupted agent_context data

### Error Handling Strategy

**Tool Validation Errors**:
```python
if fitness_level_lower not in valid_levels:
    return {
        "status": "error",
        "message": f"Invalid fitness_level. Must be one of: {valid_levels}"
    }
```

**Database Errors**:
```python
try:
    await self.save_context(user_id, assessment_data)
    return {"status": "success", "message": "..."}
except Exception as e:
    logger.error(f"Error saving fitness assessment: {e}")
    return {
        "status": "error",
        "message": "Failed to save. Please try again."
    }
```

**Missing Context Handling**:
```python
def get_system_prompt(self) -> str:
    fitness_level = self.context.get("fitness_assessment", {}).get(
        "fitness_level",
        "unknown"  # Graceful default
    )
    # ... use fitness_level in prompt
```

**LLM Errors**:
```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=self.get_tools(),
    verbose=True,
    handle_parsing_errors=True  # Gracefully handle parsing errors
)
```

### Error Response Format

All tool errors return consistent structure:
```python
{
    "status": "error",
    "message": "Human-readable error description"
}
```

All tool successes return:
```python
{
    "status": "success",
    "message": "Operation completed successfully"
}
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using Hypothesis

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

- **Library**: Hypothesis for Python
- **Minimum iterations**: 100 per property test
- **Test tagging**: Each property test must reference its design document property
- **Tag format**: `# Feature: fitness-goal-agents, Property {number}: {property_text}`

### Unit Testing Focus

Unit tests should focus on:
- Specific examples that demonstrate correct behavior (e.g., "I'm a beginner" → fitness_level="beginner")
- Integration points between agents and orchestrator
- Edge cases (empty context, missing fields, ambiguous input)
- Error conditions (invalid parameters, database failures)

Avoid writing too many unit tests for scenarios that property tests already cover. For example, don't write 10 unit tests for different invalid fitness levels when Property 1 already validates all invalid inputs.

### Test Organization

```
backend/tests/
├── test_fitness_goal_agents/
│   ├── test_fitness_assessment_agent.py    # Unit tests for FitnessAssessmentAgent
│   ├── test_goal_setting_agent.py          # Unit tests for GoalSettingAgent
│   ├── test_agent_tools.py                 # Unit tests for save tools
│   ├── test_context_handover.py            # Integration tests for context passing
│   ├── test_properties.py                  # Property-based tests
│   └── conftest.py                         # Shared fixtures
```

### Property Test Examples

**Property 1: Tool Input Validation**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    fitness_level=st.text().filter(lambda x: x.lower() not in ["beginner", "intermediate", "advanced"]),
    experience_details=st.dictionaries(st.text(), st.text()),
    limitations=st.lists(st.text())
)
async def test_save_fitness_assessment_invalid_level_property(
    fitness_level: str,
    experience_details: dict,
    limitations: list,
    db_session: AsyncSession,
    test_user: User
):
    """
    Feature: fitness-goal-agents, Property 1: Tool Input Validation
    
    For any invalid fitness_level, tool returns error without saving.
    """
    agent = FitnessAssessmentAgent(db_session, {})
    tool = agent.get_tools()[0]
    
    result = await tool.ainvoke({
        "fitness_level": fitness_level,
        "experience_details": experience_details,
        "limitations": limitations
    })
    
    assert result["status"] == "error"
    assert "Invalid fitness_level" in result["message"]
    
    # Verify no data saved
    state = await get_onboarding_state(test_user.id, db_session)
    assert "fitness_assessment" not in (state.agent_context or {})
```

**Property 2: Tool Success Persistence**
```python
@given(
    fitness_level=st.sampled_from(["beginner", "intermediate", "advanced"]),
    experience_details=st.dictionaries(
        st.sampled_from(["frequency", "duration", "types"]),
        st.text(min_size=1)
    ),
    limitations=st.lists(st.text(min_size=1), max_size=5)
)
async def test_save_fitness_assessment_success_property(
    fitness_level: str,
    experience_details: dict,
    limitations: list,
    db_session: AsyncSession,
    test_user: User
):
    """
    Feature: fitness-goal-agents, Property 2: Tool Success Persistence
    
    For any valid parameters, tool saves data with timestamp and returns success.
    """
    agent = FitnessAssessmentAgent(db_session, {})
    tool = agent.get_tools()[0]
    
    result = await tool.ainvoke({
        "fitness_level": fitness_level,
        "experience_details": experience_details,
        "limitations": limitations
    })
    
    assert result["status"] == "success"
    
    # Verify data saved
    state = await get_onboarding_state(test_user.id, db_session)
    assert "fitness_assessment" in state.agent_context
    
    saved_data = state.agent_context["fitness_assessment"]
    assert saved_data["fitness_level"] == fitness_level.lower()
    assert "completed_at" in saved_data
    
    # Verify ISO 8601 timestamp
    from datetime import datetime
    datetime.fromisoformat(saved_data["completed_at"])  # Should not raise
```

**Property 5: Data Normalization**
```python
@given(
    fitness_level=st.sampled_from(["BEGINNER", "Intermediate", "aDvAnCeD"]),
    primary_goal=st.sampled_from(["FAT_LOSS", "Muscle Gain", "general FITNESS"])
)
async def test_data_normalization_property(
    fitness_level: str,
    primary_goal: str,
    db_session: AsyncSession,
    test_user: User
):
    """
    Feature: fitness-goal-agents, Property 5: Data Normalization
    
    For any string data, it should be normalized to lowercase with whitespace trimmed.
    """
    # Test fitness_level normalization
    fitness_agent = FitnessAssessmentAgent(db_session, {})
    fitness_tool = fitness_agent.get_tools()[0]
    
    await fitness_tool.ainvoke({
        "fitness_level": fitness_level,
        "experience_details": {},
        "limitations": []
    })
    
    state = await get_onboarding_state(test_user.id, db_session)
    assert state.agent_context["fitness_assessment"]["fitness_level"] == fitness_level.lower().strip()
    
    # Test primary_goal normalization
    goal_agent = GoalSettingAgent(db_session, state.agent_context)
    goal_tool = goal_agent.get_tools()[0]
    
    await goal_tool.ainvoke({
        "primary_goal": primary_goal
    })
    
    await db_session.refresh(state)
    assert state.agent_context["goal_setting"]["primary_goal"] == primary_goal.lower().strip().replace(" ", "_")
```

### Unit Test Examples

**Agent Instantiation Test**
```python
async def test_fitness_assessment_agent_instantiation(db_session: AsyncSession):
    """Test that FitnessAssessmentAgent inherits from BaseOnboardingAgent."""
    agent = FitnessAssessmentAgent(db_session, {})
    
    assert isinstance(agent, BaseOnboardingAgent)
    assert agent.agent_type == "fitness_assessment"
    assert agent.db == db_session
```

**Context Handover Test**
```python
async def test_goal_agent_accesses_fitness_context(
    db_session: AsyncSession,
    test_user: User
):
    """Test that GoalSettingAgent can access fitness_assessment context."""
    # Setup: Save fitness assessment
    fitness_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "limitations": ["no_equipment"]
        }
    }
    
    # Create goal agent with context
    goal_agent = GoalSettingAgent(db_session, fitness_context)
    
    # Verify system prompt includes fitness level
    prompt = goal_agent.get_system_prompt()
    assert "intermediate" in prompt
    assert "no_equipment" in prompt
```

**Medical Topic Handling Test**
```python
async def test_fitness_agent_handles_medical_topics(
    db_session: AsyncSession,
    test_user: User
):
    """Test that agent redirects medical topics to fitness questions."""
    agent = FitnessAssessmentAgent(db_session, {})
    
    response = await agent.process_message(
        "I have diabetes, what should I do?",
        test_user.id
    )
    
    # Response should acknowledge but not provide medical advice
    assert "medical" not in response.message.lower() or "doctor" in response.message.lower()
    assert response.agent_type == "fitness_assessment"
```

**Completion Detection Test**
```python
async def test_completion_intent_detection(
    db_session: AsyncSession,
    test_user: User
):
    """Test that agent detects completion intent from user messages."""
    agent = FitnessAssessmentAgent(db_session, {})
    
    # First, save some data
    tool = agent.get_tools()[0]
    await tool.ainvoke({
        "fitness_level": "beginner",
        "experience_details": {"frequency": "3x/week"},
        "limitations": []
    })
    
    # Now check completion
    is_complete = await agent._check_if_complete(test_user.id)
    assert is_complete is True
```

### Integration Test Example

```python
async def test_end_to_end_fitness_to_goal_flow(
    authenticated_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession
):
    """Test complete flow from fitness assessment through goal setting."""
    # Step 1: Start fitness assessment
    response1 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I'm a beginner, I workout 2 times a week"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["agent_type"] == "fitness_assessment"
    
    # Step 2: Complete fitness assessment
    response2 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I have no equipment at home. That's all for now."}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["step_complete"] is True
    
    # Step 3: Verify advancement to goal setting
    response3 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I want to build muscle"}
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["agent_type"] == "goal_setting"
    
    # Step 4: Verify context handover
    state = await get_onboarding_state(test_user.id, db_session)
    assert "fitness_assessment" in state.agent_context
    assert state.agent_context["fitness_assessment"]["fitness_level"] == "beginner"
```

### Coverage Requirements

- Minimum 80% code coverage for new agent code
- 100% coverage for tool validation logic
- All error handling paths must be tested
- All system prompts must have content verification tests

### Test Execution

```bash
# Run all tests for this feature
poetry run pytest backend/tests/test_fitness_goal_agents/

# Run only unit tests
poetry run pytest backend/tests/test_fitness_goal_agents/ -m "not property"

# Run only property tests
poetry run pytest backend/tests/test_fitness_goal_agents/test_properties.py

# Run with coverage
poetry run pytest backend/tests/test_fitness_goal_agents/ --cov=app.agents.onboarding --cov-report=html

# Run specific test
poetry run pytest backend/tests/test_fitness_goal_agents/test_fitness_assessment_agent.py::test_fitness_assessment_agent_instantiation
```


## Implementation Notes

### Dependencies

This feature builds on the onboarding-agent-foundation spec and requires:

```toml
[tool.poetry.dependencies]
langchain = "^0.1.0"
langchain-anthropic = "^0.1.0"
langchain-core = "^0.1.0"

[tool.poetry.group.dev.dependencies]
hypothesis = "^6.92.0"
```

These should already be installed from Spec 1. No new dependencies required.

### File Structure

```
backend/app/
├── agents/
│   └── onboarding/
│       ├── __init__.py
│       ├── base.py                        # From Spec 1
│       ├── fitness_assessment.py          # NEW - FitnessAssessmentAgent
│       └── goal_setting.py                # NEW - GoalSettingAgent
├── services/
│   └── onboarding_orchestrator.py         # From Spec 1 - no changes needed
└── api/v1/endpoints/
    └── onboarding.py                      # From Spec 1 - no changes needed
```

### Integration with Existing Code

**Orchestrator Integration**:

The OnboardingAgentOrchestrator from Spec 1 already has the routing logic:
```python
def _step_to_agent(self, step: int) -> OnboardingAgentType:
    if step <= 2:
        return OnboardingAgentType.FITNESS_ASSESSMENT
    elif step == 3:
        return OnboardingAgentType.GOAL_SETTING
    # ...
```

And the factory method:
```python
async def _create_agent(self, agent_type: OnboardingAgentType, context: dict):
    from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
    from app.agents.onboarding.goal_setting import GoalSettingAgent
    
    agent_classes = {
        OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
        OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
        # ...
    }
    
    agent_class = agent_classes[agent_type]
    return agent_class(self.db, context)
```

No changes needed to the orchestrator - it will automatically route to the new agents.

**API Integration**:

The `/api/v1/onboarding/chat` endpoint from Spec 1 already handles:
- Routing messages to the current agent
- Saving conversation history
- Returning agent responses

No changes needed to the API - it will work with the new agents.

### Configuration

Use existing configuration from `app/core/config.py`:

```python
settings.LLM_MODEL  # "claude-sonnet-4-5-20250929"
settings.LLM_TEMPERATURE  # 0.7
settings.LLM_MAX_TOKENS  # 4096
settings.ANTHROPIC_API_KEY  # API key
```

### Logging

Add logging for agent operations:

```python
import logging

logger = logging.getLogger(__name__)

# In tools
logger.info(f"Saving fitness assessment for user {user_id}")
logger.error(f"Error saving fitness assessment: {e}")

# In process_message
logger.debug(f"Processing message for {self.agent_type}: {message[:50]}...")
```

### Performance Considerations

**LLM Call Optimization**:
- Each `process_message` call makes one LLM API call
- Average latency: 1-2 seconds
- Tool calls add minimal overhead (database writes are fast)

**Context Loading**:
- Agent context loaded once per request by orchestrator
- Cached in memory during request processing
- No additional database queries needed

**Database Operations**:
- Tool saves use single UPDATE query
- Transaction committed immediately after save
- No complex joins or queries

### Security Considerations

**Input Validation**:
- All tool parameters validated before database operations
- String inputs trimmed and normalized
- Numeric inputs range-checked

**Data Privacy**:
- No PII beyond user_id in agent_context
- Fitness data is non-medical and non-sensitive
- All data encrypted at rest (database level)

**API Security**:
- All endpoints require JWT authentication (from Spec 1)
- Users can only access their own onboarding state
- No cross-user data leakage possible

### Monitoring and Observability

**Metrics to Track**:
- Agent response time (p50, p95, p99)
- Tool call success rate
- Completion rate per agent
- Average messages per agent before completion

**Logging Events**:
- Agent instantiation
- Tool calls (success/failure)
- Completion detection
- Context handover

**Alerts**:
- High error rate in tool calls
- LLM API failures
- Database connection issues

## Future Enhancements

This implementation enables future enhancements:

1. **Conversation History**: Load and use conversation_history in agent prompts for better context
2. **Clarification Detection**: Detect when user needs help understanding questions
3. **Multi-language Support**: Translate system prompts and responses
4. **Voice Integration**: Adapt agents for voice-based onboarding
5. **Progress Indicators**: Show users how far through onboarding they are
6. **Skip Options**: Allow users to skip optional questions
7. **Edit Previous Steps**: Allow users to go back and change earlier answers

## Conclusion

The Fitness and Goal Setting Agents provide a conversational, intelligent onboarding experience for the first three steps of user onboarding. The agents use LangChain and Claude Sonnet 4 to extract structured data from natural language, validate inputs, and seamlessly hand off context to subsequent agents.

The implementation follows the patterns established in the Onboarding Agent Foundation (Spec 1) and provides a template for implementing the remaining three agents (Workout Planning, Diet Planning, Scheduling) in subsequent specifications.

Key achievements:
- Natural language data collection without rigid forms
- Context-aware goal recommendations based on fitness level
- Robust error handling and validation
- Comprehensive testing strategy with property-based tests
- Seamless integration with existing infrastructure

This feature is production-ready and provides the foundation for the remaining onboarding agents.

# Design Document: Planning Agents with Proposal Workflow

## Overview

The Planning Agents with Proposal Workflow feature implements the Workout Planning Agent (Steps 4-5) and Diet Planning Agent (Steps 6-7) that actively generate personalized plans and present them to users for approval. Unlike the previous agents that only collect information, these agents create structured workout and meal plans, explain their reasoning, detect approval intent from natural language, and allow iterative modifications before saving.

This feature builds directly on the Onboarding Agent Foundation (Spec 1) and Fitness & Goal Agents (Spec 2), which provide the base agent architecture, orchestration service, and context from fitness assessment and goal setting. The planning agents demonstrate a more complex pattern: preference collection → plan generation → proposal presentation → approval detection → iterative refinement → final save.

### Key Design Principles

1. **Active Plan Generation**: Agents create structured plans using specialized services
2. **Conversational Approval**: Detect approval intent from natural language without explicit commands
3. **Iterative Refinement**: Allow multiple modification cycles until user is satisfied
4. **Explainable Plans**: Present plans with clear reasoning and rationale
5. **Context-Driven Personalization**: Use all previous agent data to tailor plans

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
│ Workout Planning │      │ Diet Planning    │
│ Agent            │─────>│ Agent            │
│ (Steps 4-5)      │      │ (Steps 6-7)      │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ WorkoutPlan      │      │ MealPlan         │
│ Generator        │      │ Generator        │
│ Service          │      │ Service          │
└──────────────────┘      └──────────────────┘
```

### Plan Generation and Approval Flow

```
User: "I prefer gym workouts"
    ↓
WorkoutPlanningAgent collects preferences
    ↓
Agent calls generate_workout_plan tool
    ↓
WorkoutPlanGenerator.generate_plan()
    ↓
Plan created based on:
  - fitness_level (from context)
  - primary_goal (from context)
  - preferences (from conversation)
    ↓
Agent presents plan with explanation
    ↓
User: "Yes, looks perfect!"
    ↓
Agent detects approval intent
    ↓
Agent calls save_workout_plan(plan, user_approved=True)
    ↓
Plan saved to agent_context["workout_planning"]
    ↓
step_complete=True, advance to Diet Planning
```


### Modification Flow

```
User: "Can we do 3 days instead of 4?"
    ↓
Agent detects modification request
    ↓
Agent calls modify_workout_plan(current_plan, modifications)
    ↓
WorkoutPlanGenerator.modify_plan()
    ↓
Modified plan created
    ↓
Agent presents modified plan with changes highlighted
    ↓
User: "Perfect!"
    ↓
Agent detects approval intent
    ↓
Agent calls save_workout_plan(modified_plan, user_approved=True)
    ↓
Plan saved to agent_context
```

## Components and Interfaces

### 1. Workout Planning Agent

#### Class Definition

```python
from app.agents.onboarding.base import BaseOnboardingAgent
from app.services.workout_plan_generator import WorkoutPlanGenerator
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from datetime import datetime
from uuid import UUID
from typing import List

class WorkoutPlanningAgent(BaseOnboardingAgent):
    """
    Specialized agent for workout planning during onboarding.
    
    This agent handles Steps 4-5 of onboarding:
    - Collects workout preferences (location, equipment, frequency, duration)
    - Generates personalized workout plan using WorkoutPlanGenerator
    - Presents plan with explanation and rationale
    - Detects approval intent from user responses
    - Allows modifications and iterative refinement
    - Saves approved plan to agent_context
    
    The agent uses context from fitness_assessment and goal_setting to
    create plans tailored to the user's fitness level and goals.
    """
    
    agent_type = "workout_planning"
    
    def __init__(self, db: AsyncSession, context: dict):
        """
        Initialize workout planning agent.
        
        Args:
            db: Async database session
            context: Agent context containing fitness_assessment and goal_setting data
        """
        super().__init__(db, context)
        self.workout_generator = WorkoutPlanGenerator()
        self.current_plan = None  # Store generated plan for modifications
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about workout preferences and plan approval.
        
        Uses LangChain's tool-calling agent to:
        1. Collect workout preferences (location, equipment, frequency, duration)
        2. Generate workout plan when preferences are complete
        3. Present plan with explanation
        4. Detect approval intent ("yes", "looks good", etc.)
        5. Handle modification requests ("can we change...", "I'd prefer...")
        6. Save plan when user approves
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Build prompt with context from previous agents
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(user_id),
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.get_tools(user_id),
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

    
    def get_tools(self, user_id: UUID) -> List:
        """
        Get workout planning specific tools.
        
        Returns:
            List containing generate_workout_plan, save_workout_plan, and modify_workout_plan tools
        """
        
        @tool
        async def generate_workout_plan(
            frequency: int,
            location: str,
            duration_minutes: int,
            equipment: list
        ) -> dict:
            """
            Generate a personalized workout plan based on preferences.
            
            Call this tool after collecting:
            - Workout frequency (days per week)
            - Location (home/gym)
            - Duration per session (minutes)
            - Available equipment
            
            Args:
                frequency: Workout days per week (2-7)
                location: "home" or "gym"
                duration_minutes: Session duration (20-180 minutes)
                equipment: List of available equipment (e.g., ["dumbbells", "barbell"])
                
            Returns:
                Dict representation of WorkoutPlan with exercises, sets, reps, etc.
            """
            try:
                # Get context from previous agents
                fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "beginner")
                primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "general_fitness")
                limitations = self.context.get("fitness_assessment", {}).get("limitations", [])
                
                # Generate plan
                plan = await self.workout_generator.generate_plan(
                    fitness_level=fitness_level,
                    primary_goal=primary_goal,
                    frequency=frequency,
                    location=location,
                    duration_minutes=duration_minutes,
                    equipment=equipment,
                    limitations=limitations
                )
                
                # Store for potential modifications
                self.current_plan = plan
                
                return plan.dict()
                
            except ValueError as e:
                return {
                    "error": str(e),
                    "message": "Invalid parameters for workout plan generation"
                }
            except Exception as e:
                logger.error(f"Error generating workout plan: {e}")
                return {
                    "error": "generation_failed",
                    "message": "Failed to generate workout plan. Please try again."
                }
        
        @tool
        async def save_workout_plan(
            plan_data: dict,
            user_approved: bool
        ) -> dict:
            """
            Save approved workout plan to agent context.
            
            ONLY call this tool when user explicitly approves the plan by saying:
            - "Yes", "Looks good", "Perfect", "I approve", "Let's do it"
            - "Sounds great", "That works", "I'm happy with this"
            
            Do NOT call this tool unless user has clearly approved.
            
            Args:
                plan_data: The workout plan dictionary to save
                user_approved: Must be True to save (safety check)
                
            Returns:
                Dict with status and message
            """
            if not user_approved:
                return {
                    "status": "error",
                    "message": "Cannot save plan without user approval"
                }
            
            # Prepare data with metadata
            workout_data = {
                "preferences": {
                    "location": plan_data.get("location"),
                    "frequency": plan_data.get("frequency"),
                    "duration_minutes": plan_data.get("duration_minutes"),
                    "equipment": plan_data.get("equipment", [])
                },
                "proposed_plan": plan_data,
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context
            try:
                await self.save_context(user_id, workout_data)
                return {
                    "status": "success",
                    "message": "Workout plan saved successfully"
                }
            except Exception as e:
                logger.error(f"Error saving workout plan: {e}")
                return {
                    "status": "error",
                    "message": "Failed to save workout plan. Please try again."
                }
        
        @tool
        async def modify_workout_plan(
            current_plan: dict,
            modifications: dict
        ) -> dict:
            """
            Modify the workout plan based on user feedback.
            
            Use this when user requests changes like:
            - "Can we do 3 days instead of 4?"
            - "I don't have time for 90 minute sessions"
            - "Can we add more cardio?"
            - "I'd prefer upper/lower split"
            
            Args:
                current_plan: The current workout plan dictionary
                modifications: Dict with requested changes (e.g., {"frequency": 3})
                
            Returns:
                Dict representation of modified WorkoutPlan
            """
            try:
                # Apply modifications
                modified_plan = await self.workout_generator.modify_plan(
                    current_plan=current_plan,
                    modifications=modifications
                )
                
                # Store for potential further modifications
                self.current_plan = modified_plan
                
                return modified_plan.dict()
                
            except ValueError as e:
                return {
                    "error": str(e),
                    "message": "Invalid modifications requested"
                }
            except Exception as e:
                logger.error(f"Error modifying workout plan: {e}")
                return {
                    "error": "modification_failed",
                    "message": "Failed to modify workout plan. Please try again."
                }
        
        return [generate_workout_plan, save_workout_plan, modify_workout_plan]

    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for workout planning agent with context from previous steps.
        
        Returns:
            System prompt including fitness level, primary goal, and limitations
        """
        # Get context from previous agents
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "unknown")
        limitations = self.context.get("fitness_assessment", {}).get("limitations", [])
        
        limitations_str = ", ".join(limitations) if limitations else "none mentioned"
        
        return f"""You are a Workout Planning Agent creating personalized workout plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Limitations: {limitations_str}

Your role:
- Ask about workout preferences (location, equipment, frequency, duration)
- Generate a workout plan tailored to their level and goals
- Present the plan with clear explanation of structure and rationale
- Detect approval intent from user responses
- Handle modification requests
- Save plan ONLY after user explicitly approves

Guidelines:
- Ask 1-2 questions at a time about preferences
- Once you have location, equipment, frequency, and duration, call generate_workout_plan
- Present the plan in a clear, readable format
- Explain WHY you chose this structure (training split, frequency, exercises)
- Explain HOW it aligns with their {primary_goal} goal and {fitness_level} level
- After presenting, explicitly ask: "Does this workout plan work for you?"

Approval Detection:
- User says "yes", "looks good", "perfect", "I approve", "let's do it" → Call save_workout_plan with user_approved=True
- User says "sounds great", "that works", "I'm happy with this" → Call save_workout_plan with user_approved=True
- User asks questions → Answer questions, don't save yet
- User requests changes → Call modify_workout_plan with requested changes

Modification Handling:
- Extract what user wants to change (frequency, duration, exercises, split)
- Call modify_workout_plan with current plan and modifications
- Present modified plan and highlight what changed
- Ask for approval again

Realistic Recommendations by Fitness Level:
- Beginner ({fitness_level == 'beginner'}): 2-4 days/week, full body or upper/lower split, 45-60 min sessions
- Intermediate ({fitness_level == 'intermediate'}): 3-5 days/week, push/pull/legs or upper/lower, 60-75 min sessions
- Advanced ({fitness_level == 'advanced'}): 4-6 days/week, body part splits or specialized programs, 60-90 min sessions

Goal-Specific Guidance:
- Muscle Gain: Focus on progressive overload, 8-12 rep range, compound movements
- Fat Loss: Mix of resistance training and cardio, circuit training options, higher volume
- General Fitness: Balanced approach with strength, cardio, and flexibility

After Saving:
- Confirm the plan is saved
- Let user know we'll move to nutrition planning next
- Briefly preview what's coming: "Now let's create your meal plan to support these workouts"
"""
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if workout planning step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains workout_planning data with user_approved=True
        """
        from sqlalchemy import select
        from app.models.onboarding import OnboardingState
        
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            workout_data = state.agent_context.get("workout_planning", {})
            return workout_data.get("user_approved", False) is True
        
        return False
```


### 2. Diet Planning Agent

#### Class Definition

```python
from app.services.meal_plan_generator import MealPlanGenerator

class DietPlanningAgent(BaseOnboardingAgent):
    """
    Specialized agent for diet planning during onboarding.
    
    This agent handles Steps 6-7 of onboarding:
    - Collects dietary preferences (diet type, allergies, dislikes, meal frequency)
    - Generates personalized meal plan using MealPlanGenerator
    - Presents plan with calorie/macro explanation and sample meals
    - Detects approval intent from user responses
    - Allows modifications and iterative refinement
    - Saves approved plan to agent_context
    
    The agent uses context from fitness_assessment, goal_setting, and workout_planning
    to create meal plans that support the user's training and goals.
    """
    
    agent_type = "diet_planning"
    
    def __init__(self, db: AsyncSession, context: dict):
        """
        Initialize diet planning agent.
        
        Args:
            db: Async database session
            context: Agent context containing fitness_assessment, goal_setting, and workout_planning data
        """
        super().__init__(db, context)
        self.meal_generator = MealPlanGenerator()
        self.current_plan = None  # Store generated plan for modifications
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about dietary preferences and meal plan approval.
        
        Uses LangChain's tool-calling agent to:
        1. Collect dietary preferences (diet type, allergies, dislikes, meal frequency)
        2. Generate meal plan when preferences are complete
        3. Present plan with calorie/macro breakdown and sample meals
        4. Detect approval intent
        5. Handle modification requests
        6. Save plan when user approves
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Build prompt with context from previous agents
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(user_id),
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.get_tools(user_id),
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []
        })
        
        # Check if step is complete
        step_complete = await self._check_if_complete(user_id)
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action="advance_step" if step_complete else "continue_conversation"
        )
    
    def get_tools(self, user_id: UUID) -> List:
        """
        Get diet planning specific tools.
        
        Returns:
            List containing generate_meal_plan, save_meal_plan, and modify_meal_plan tools
        """
        
        @tool
        async def generate_meal_plan(
            diet_type: str,
            allergies: list,
            dislikes: list,
            meal_frequency: int,
            meal_prep_level: str
        ) -> dict:
            """
            Generate a personalized meal plan based on dietary preferences.
            
            Call this tool after collecting:
            - Diet type (omnivore/vegetarian/vegan/pescatarian)
            - Allergies and intolerances
            - Foods user dislikes
            - Preferred number of meals per day
            - Meal prep willingness (low/medium/high)
            
            Args:
                diet_type: Type of diet (omnivore/vegetarian/vegan/pescatarian)
                allergies: List of allergies/intolerances (e.g., ["dairy", "eggs"])
                dislikes: List of disliked foods (e.g., ["broccoli", "fish"])
                meal_frequency: Number of meals per day (2-6)
                meal_prep_level: Cooking/prep willingness (low/medium/high)
                
            Returns:
                Dict representation of MealPlan with calories, macros, sample meals
            """
            try:
                # Get context from previous agents
                fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "beginner")
                primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "general_fitness")
                workout_plan = self.context.get("workout_planning", {}).get("proposed_plan", {})
                
                # Generate plan
                plan = await self.meal_generator.generate_plan(
                    fitness_level=fitness_level,
                    primary_goal=primary_goal,
                    workout_plan=workout_plan,
                    diet_type=diet_type,
                    allergies=allergies,
                    dislikes=dislikes,
                    meal_frequency=meal_frequency,
                    meal_prep_level=meal_prep_level
                )
                
                # Store for potential modifications
                self.current_plan = plan
                
                return plan.dict()
                
            except ValueError as e:
                return {
                    "error": str(e),
                    "message": "Invalid parameters for meal plan generation"
                }
            except Exception as e:
                logger.error(f"Error generating meal plan: {e}")
                return {
                    "error": "generation_failed",
                    "message": "Failed to generate meal plan. Please try again."
                }
        
        @tool
        async def save_meal_plan(
            plan_data: dict,
            user_approved: bool
        ) -> dict:
            """
            Save approved meal plan to agent context.
            
            ONLY call this tool when user explicitly approves the plan by saying:
            - "Yes", "Looks good", "Perfect", "I approve", "Let's do it"
            - "Sounds great", "That works", "I'm happy with this"
            
            Do NOT call this tool unless user has clearly approved.
            
            Args:
                plan_data: The meal plan dictionary to save
                user_approved: Must be True to save (safety check)
                
            Returns:
                Dict with status and message
            """
            if not user_approved:
                return {
                    "status": "error",
                    "message": "Cannot save plan without user approval"
                }
            
            # Prepare data with metadata
            diet_data = {
                "preferences": {
                    "diet_type": plan_data.get("diet_type"),
                    "allergies": plan_data.get("allergies", []),
                    "dislikes": plan_data.get("dislikes", []),
                    "meal_frequency": plan_data.get("meal_frequency"),
                    "meal_prep_level": plan_data.get("meal_prep_level")
                },
                "proposed_plan": plan_data,
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context
            try:
                await self.save_context(user_id, diet_data)
                return {
                    "status": "success",
                    "message": "Meal plan saved successfully"
                }
            except Exception as e:
                logger.error(f"Error saving meal plan: {e}")
                return {
                    "status": "error",
                    "message": "Failed to save meal plan. Please try again."
                }
        
        @tool
        async def modify_meal_plan(
            current_plan: dict,
            modifications: dict
        ) -> dict:
            """
            Modify the meal plan based on user feedback.
            
            Use this when user requests changes like:
            - "Can we increase protein?"
            - "I want 4 meals instead of 3"
            - "Can we lower the calories a bit?"
            - "I'd prefer more variety in the sample meals"
            
            Args:
                current_plan: The current meal plan dictionary
                modifications: Dict with requested changes (e.g., {"meal_frequency": 4})
                
            Returns:
                Dict representation of modified MealPlan
            """
            try:
                # Apply modifications
                modified_plan = await self.meal_generator.modify_plan(
                    current_plan=current_plan,
                    modifications=modifications
                )
                
                # Store for potential further modifications
                self.current_plan = modified_plan
                
                return modified_plan.dict()
                
            except ValueError as e:
                return {
                    "error": str(e),
                    "message": "Invalid modifications requested"
                }
            except Exception as e:
                logger.error(f"Error modifying meal plan: {e}")
                return {
                    "error": "modification_failed",
                    "message": "Failed to modify meal plan. Please try again."
                }
        
        return [generate_meal_plan, save_meal_plan, modify_meal_plan]

    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for diet planning agent with context from previous steps.
        
        Returns:
            System prompt including fitness level, primary goal, and workout plan summary
        """
        # Get context from previous agents
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "unknown")
        workout_plan = self.context.get("workout_planning", {}).get("proposed_plan", {})
        workout_frequency = workout_plan.get("frequency", "unknown")
        
        return f"""You are a Diet Planning Agent creating personalized meal plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Workout Frequency: {workout_frequency} days/week

Your role:
- Ask about dietary preferences and restrictions
- Generate a meal plan aligned with their goals and workout plan
- Present the plan with calorie/macro breakdown and sample meals
- Detect approval intent from user responses
- Handle modification requests
- Save plan ONLY after user explicitly approves

Guidelines:
- Ask 1-2 questions at a time about diet preferences
- Once you have diet type, allergies, dislikes, meal frequency, and meal prep level, call generate_meal_plan
- Present the plan clearly with:
  * Daily calorie target
  * Protein/Carbs/Fats breakdown (in grams)
  * 3-5 sample meal ideas
  * Meal timing suggestions relative to workouts
- Explain WHY these calories/macros support their {primary_goal} goal
- Explain HOW the plan complements their {workout_frequency} day/week training
- After presenting, explicitly ask: "Does this meal plan work for you?"

Approval Detection:
- User says "yes", "looks good", "perfect", "I approve", "let's do it" → Call save_meal_plan with user_approved=True
- User says "sounds great", "that works", "I'm happy with this" → Call save_meal_plan with user_approved=True
- User asks questions → Answer questions, don't save yet
- User requests changes → Call modify_meal_plan with requested changes

Modification Handling:
- Extract what user wants to change (calories, macros, meal frequency, sample meals)
- Call modify_meal_plan with current plan and modifications
- Present modified plan and highlight what changed
- Ask for approval again

Dietary Restrictions:
- STRICTLY respect allergies and intolerances
- Avoid disliked foods in sample meals
- Vegetarian: No meat or fish
- Vegan: No animal products
- Pescatarian: No meat, but fish is okay

Calorie/Macro Targets by Goal:
- Muscle Gain: Calorie surplus (+300-500), High protein (2.0-2.2g/kg), Moderate carbs, Moderate fats
- Fat Loss: Calorie deficit (-300-500), High protein (1.8-2.0g/kg), Moderate carbs, Lower fats
- General Fitness: Maintenance calories, Balanced macros (1.6-1.8g/kg protein)

Workout Integration:
- Higher training volume ({workout_frequency} days) → Higher carbs for energy
- Lower training volume → Moderate carbs
- Suggest pre/post workout meal timing

After Saving:
- Confirm the plan is saved
- Let user know we'll set up their schedule next
- Briefly preview: "Now let's schedule your workouts and meals for the week"
"""
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if diet planning step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains diet_planning data with user_approved=True
        """
        from sqlalchemy import select
        from app.models.onboarding import OnboardingState
        
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            diet_data = state.agent_context.get("diet_planning", {})
            return diet_data.get("user_approved", False) is True
        
        return False
```


### 3. Workout Plan Generator Service

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict
from enum import Enum

class ExerciseType(str, Enum):
    """Types of exercises."""
    COMPOUND = "compound"
    ISOLATION = "isolation"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"

class Exercise(BaseModel):
    """Individual exercise in a workout."""
    name: str
    type: ExerciseType
    sets: int
    reps: str  # e.g., "8-12", "15-20", "AMRAP"
    rest_seconds: int
    notes: str = ""
    
class WorkoutDay(BaseModel):
    """Single day's workout."""
    day_name: str  # e.g., "Day 1: Upper Body Push"
    exercises: List[Exercise]
    total_duration_minutes: int

class WorkoutPlan(BaseModel):
    """Complete workout plan."""
    frequency: int = Field(ge=2, le=7, description="Days per week")
    duration_minutes: int = Field(ge=20, le=180, description="Minutes per session")
    location: str  # "home" or "gym"
    equipment: List[str]
    training_split: str  # e.g., "Upper/Lower", "Push/Pull/Legs", "Full Body"
    workout_days: List[WorkoutDay]
    progression_strategy: str
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        if v.lower() not in ["home", "gym"]:
            raise ValueError("location must be 'home' or 'gym'")
        return v.lower()

class WorkoutPlanGenerator:
    """
    Service for generating personalized workout plans.
    
    Creates workout plans based on:
    - Fitness level (beginner/intermediate/advanced)
    - Primary goal (fat_loss/muscle_gain/general_fitness)
    - Preferences (frequency, location, equipment, duration)
    - Limitations (from fitness assessment)
    """
    
    async def generate_plan(
        self,
        fitness_level: str,
        primary_goal: str,
        frequency: int,
        location: str,
        duration_minutes: int,
        equipment: List[str],
        limitations: List[str] = None
    ) -> WorkoutPlan:
        """
        Generate a workout plan based on user profile and preferences.
        
        Args:
            fitness_level: beginner/intermediate/advanced
            primary_goal: fat_loss/muscle_gain/general_fitness
            frequency: Workout days per week (2-7)
            location: home or gym
            duration_minutes: Session duration (20-180)
            equipment: Available equipment list
            limitations: Physical limitations to consider
            
        Returns:
            WorkoutPlan object with complete program
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        self._validate_inputs(fitness_level, primary_goal, frequency, duration_minutes)
        
        # Determine training split based on frequency and level
        training_split = self._determine_training_split(frequency, fitness_level)
        
        # Generate workout days
        workout_days = self._generate_workout_days(
            training_split=training_split,
            fitness_level=fitness_level,
            primary_goal=primary_goal,
            location=location,
            equipment=equipment,
            duration_minutes=duration_minutes,
            limitations=limitations or []
        )
        
        # Determine progression strategy
        progression_strategy = self._determine_progression_strategy(fitness_level, primary_goal)
        
        return WorkoutPlan(
            frequency=frequency,
            duration_minutes=duration_minutes,
            location=location,
            equipment=equipment,
            training_split=training_split,
            workout_days=workout_days,
            progression_strategy=progression_strategy
        )
    
    async def modify_plan(
        self,
        current_plan: dict,
        modifications: dict
    ) -> WorkoutPlan:
        """
        Modify an existing workout plan based on user feedback.
        
        Args:
            current_plan: Current WorkoutPlan as dict
            modifications: Dict with requested changes
                Examples:
                - {"frequency": 3}  # Change to 3 days/week
                - {"duration_minutes": 45}  # Shorter sessions
                - {"training_split": "Full Body"}  # Change split
                
        Returns:
            Modified WorkoutPlan object
            
        Raises:
            ValueError: If modifications are invalid
        """
        # Parse current plan
        plan = WorkoutPlan(**current_plan)
        
        # Apply modifications
        if "frequency" in modifications:
            plan.frequency = modifications["frequency"]
            # Regenerate split and days for new frequency
            plan.training_split = self._determine_training_split(
                plan.frequency,
                self._infer_fitness_level(plan)
            )
        
        if "duration_minutes" in modifications:
            plan.duration_minutes = modifications["duration_minutes"]
            # Adjust exercises per day to fit new duration
        
        if "training_split" in modifications:
            plan.training_split = modifications["training_split"]
        
        # Regenerate workout days with modifications
        # (Implementation would regenerate based on new parameters)
        
        return plan
    
    def _validate_inputs(
        self,
        fitness_level: str,
        primary_goal: str,
        frequency: int,
        duration_minutes: int
    ) -> None:
        """Validate input parameters."""
        valid_levels = ["beginner", "intermediate", "advanced"]
        if fitness_level not in valid_levels:
            raise ValueError(f"fitness_level must be one of {valid_levels}")
        
        valid_goals = ["fat_loss", "muscle_gain", "general_fitness"]
        if primary_goal not in valid_goals:
            raise ValueError(f"primary_goal must be one of {valid_goals}")
        
        if not (2 <= frequency <= 7):
            raise ValueError("frequency must be between 2 and 7 days per week")
        
        if not (20 <= duration_minutes <= 180):
            raise ValueError("duration_minutes must be between 20 and 180")
    
    def _determine_training_split(self, frequency: int, fitness_level: str) -> str:
        """Determine appropriate training split based on frequency and level."""
        if fitness_level == "beginner":
            if frequency <= 3:
                return "Full Body"
            else:
                return "Upper/Lower"
        
        elif fitness_level == "intermediate":
            if frequency <= 3:
                return "Full Body"
            elif frequency == 4:
                return "Upper/Lower"
            else:
                return "Push/Pull/Legs"
        
        else:  # advanced
            if frequency <= 3:
                return "Full Body"
            elif frequency == 4:
                return "Upper/Lower"
            elif frequency == 5:
                return "Push/Pull/Legs"
            else:
                return "Body Part Split"
    
    def _generate_workout_days(
        self,
        training_split: str,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int,
        limitations: List[str]
    ) -> List[WorkoutDay]:
        """Generate workout days based on split and parameters."""
        # This is a simplified example - real implementation would be more comprehensive
        
        if training_split == "Full Body":
            return self._generate_full_body_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        elif training_split == "Upper/Lower":
            return self._generate_upper_lower_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        elif training_split == "Push/Pull/Legs":
            return self._generate_ppl_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        else:
            return self._generate_body_part_split_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
    
    def _determine_progression_strategy(self, fitness_level: str, primary_goal: str) -> str:
        """Determine progression strategy based on level and goal."""
        if fitness_level == "beginner":
            return "Linear progression: Add weight or reps each week. Focus on form mastery."
        elif fitness_level == "intermediate":
            if primary_goal == "muscle_gain":
                return "Progressive overload: Increase volume weekly. Deload every 4-6 weeks."
            else:
                return "Progressive overload with periodization. Track performance metrics."
        else:  # advanced
            return "Periodized training with mesocycles. Auto-regulation based on performance."
    
    # Helper methods for generating specific workout days
    def _generate_full_body_days(self, *args) -> List[WorkoutDay]:
        """Generate full body workout days."""
        # Implementation details...
        pass
    
    def _generate_upper_lower_days(self, *args) -> List[WorkoutDay]:
        """Generate upper/lower split workout days."""
        # Implementation details...
        pass
    
    def _generate_ppl_days(self, *args) -> List[WorkoutDay]:
        """Generate push/pull/legs workout days."""
        # Implementation details...
        pass
    
    def _generate_body_part_split_days(self, *args) -> List[WorkoutDay]:
        """Generate body part split workout days."""
        # Implementation details...
        pass
```


### 4. Meal Plan Generator Service

```python
class MealType(str, Enum):
    """Types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class SampleMeal(BaseModel):
    """Sample meal idea."""
    meal_type: MealType
    name: str
    ingredients: List[str]
    approximate_calories: int
    approximate_protein_g: int
    approximate_carbs_g: int
    approximate_fats_g: int
    prep_time_minutes: int

class MealPlan(BaseModel):
    """Complete meal plan."""
    diet_type: str  # omnivore/vegetarian/vegan/pescatarian
    allergies: List[str]
    dislikes: List[str]
    meal_frequency: int = Field(ge=2, le=6, description="Meals per day")
    meal_prep_level: str  # low/medium/high
    daily_calories: int = Field(ge=1200, le=5000)
    protein_g: int
    carbs_g: int
    fats_g: int
    sample_meals: List[SampleMeal]
    meal_timing_suggestions: str
    
    @field_validator('diet_type')
    @classmethod
    def validate_diet_type(cls, v: str) -> str:
        valid_types = ["omnivore", "vegetarian", "vegan", "pescatarian"]
        if v.lower() not in valid_types:
            raise ValueError(f"diet_type must be one of {valid_types}")
        return v.lower()
    
    @field_validator('meal_prep_level')
    @classmethod
    def validate_meal_prep_level(cls, v: str) -> str:
        valid_levels = ["low", "medium", "high"]
        if v.lower() not in valid_levels:
            raise ValueError(f"meal_prep_level must be one of {valid_levels}")
        return v.lower()

class MealPlanGenerator:
    """
    Service for generating personalized meal plans.
    
    Creates meal plans based on:
    - Fitness level and primary goal
    - Workout plan (frequency and intensity)
    - Dietary preferences and restrictions
    - Meal frequency and prep willingness
    """
    
    # Standard calorie multipliers for TDEE estimation
    ACTIVITY_MULTIPLIERS = {
        2: 1.2,   # 2 days/week - lightly active
        3: 1.375, # 3 days/week - moderately active
        4: 1.55,  # 4 days/week - very active
        5: 1.725, # 5+ days/week - extremely active
        6: 1.725,
        7: 1.9
    }
    
    async def generate_plan(
        self,
        fitness_level: str,
        primary_goal: str,
        workout_plan: dict,
        diet_type: str,
        allergies: List[str],
        dislikes: List[str],
        meal_frequency: int,
        meal_prep_level: str
    ) -> MealPlan:
        """
        Generate a meal plan based on user profile and preferences.
        
        Args:
            fitness_level: beginner/intermediate/advanced
            primary_goal: fat_loss/muscle_gain/general_fitness
            workout_plan: Workout plan dict with frequency and intensity
            diet_type: omnivore/vegetarian/vegan/pescatarian
            allergies: List of allergies/intolerances
            dislikes: List of disliked foods
            meal_frequency: Meals per day (2-6)
            meal_prep_level: low/medium/high
            
        Returns:
            MealPlan object with complete nutrition strategy
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        self._validate_inputs(diet_type, meal_frequency, meal_prep_level)
        
        # Calculate calorie target based on goal and workout plan
        workout_frequency = workout_plan.get("frequency", 3)
        daily_calories = self._calculate_calorie_target(primary_goal, workout_frequency)
        
        # Calculate macro breakdown
        protein_g, carbs_g, fats_g = self._calculate_macros(
            daily_calories=daily_calories,
            primary_goal=primary_goal,
            workout_frequency=workout_frequency
        )
        
        # Generate sample meals
        sample_meals = self._generate_sample_meals(
            diet_type=diet_type,
            allergies=allergies,
            dislikes=dislikes,
            meal_frequency=meal_frequency,
            meal_prep_level=meal_prep_level,
            daily_calories=daily_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g
        )
        
        # Generate meal timing suggestions
        meal_timing = self._generate_meal_timing(meal_frequency, workout_frequency)
        
        return MealPlan(
            diet_type=diet_type,
            allergies=allergies,
            dislikes=dislikes,
            meal_frequency=meal_frequency,
            meal_prep_level=meal_prep_level,
            daily_calories=daily_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
            sample_meals=sample_meals,
            meal_timing_suggestions=meal_timing
        )
    
    async def modify_plan(
        self,
        current_plan: dict,
        modifications: dict
    ) -> MealPlan:
        """
        Modify an existing meal plan based on user feedback.
        
        Args:
            current_plan: Current MealPlan as dict
            modifications: Dict with requested changes
                Examples:
                - {"daily_calories": 2200}  # Adjust calories
                - {"protein_g": 180}  # Increase protein
                - {"meal_frequency": 4}  # Change meal count
                
        Returns:
            Modified MealPlan object
            
        Raises:
            ValueError: If modifications are invalid
        """
        # Parse current plan
        plan = MealPlan(**current_plan)
        
        # Apply modifications
        if "daily_calories" in modifications:
            plan.daily_calories = modifications["daily_calories"]
            # Recalculate macros proportionally
            plan.protein_g, plan.carbs_g, plan.fats_g = self._recalculate_macros(
                plan.daily_calories,
                plan.protein_g,
                plan.carbs_g,
                plan.fats_g
            )
        
        if "protein_g" in modifications:
            plan.protein_g = modifications["protein_g"]
            # Adjust other macros to maintain calorie target
        
        if "meal_frequency" in modifications:
            plan.meal_frequency = modifications["meal_frequency"]
            # Regenerate sample meals for new frequency
        
        # Regenerate sample meals if needed
        # (Implementation would regenerate based on new parameters)
        
        return plan
    
    def _validate_inputs(
        self,
        diet_type: str,
        meal_frequency: int,
        meal_prep_level: str
    ) -> None:
        """Validate input parameters."""
        valid_diet_types = ["omnivore", "vegetarian", "vegan", "pescatarian"]
        if diet_type not in valid_diet_types:
            raise ValueError(f"diet_type must be one of {valid_diet_types}")
        
        if not (2 <= meal_frequency <= 6):
            raise ValueError("meal_frequency must be between 2 and 6")
        
        valid_prep_levels = ["low", "medium", "high"]
        if meal_prep_level not in valid_prep_levels:
            raise ValueError(f"meal_prep_level must be one of {valid_prep_levels}")
    
    def _calculate_calorie_target(self, primary_goal: str, workout_frequency: int) -> int:
        """Calculate daily calorie target based on goal and activity level."""
        # Simplified calculation - real implementation would use user's weight, age, etc.
        # Using average TDEE of 2000 calories as baseline
        base_tdee = 2000
        activity_multiplier = self.ACTIVITY_MULTIPLIERS.get(workout_frequency, 1.375)
        tdee = int(base_tdee * activity_multiplier)
        
        if primary_goal == "muscle_gain":
            return tdee + 400  # Surplus for muscle gain
        elif primary_goal == "fat_loss":
            return tdee - 400  # Deficit for fat loss
        else:  # general_fitness
            return tdee  # Maintenance
    
    def _calculate_macros(
        self,
        daily_calories: int,
        primary_goal: str,
        workout_frequency: int
    ) -> tuple[int, int, int]:
        """Calculate protein, carbs, and fats in grams."""
        # Protein calculation (2.0g/kg for muscle gain, 1.8g/kg for fat loss, 1.6g/kg for maintenance)
        # Using 75kg as average weight - real implementation would use actual weight
        avg_weight_kg = 75
        
        if primary_goal == "muscle_gain":
            protein_g = int(avg_weight_kg * 2.0)
        elif primary_goal == "fat_loss":
            protein_g = int(avg_weight_kg * 1.8)
        else:
            protein_g = int(avg_weight_kg * 1.6)
        
        # Protein calories
        protein_calories = protein_g * 4
        
        # Remaining calories for carbs and fats
        remaining_calories = daily_calories - protein_calories
        
        # Fat calculation (25-30% of total calories)
        fat_percentage = 0.28
        fat_calories = int(remaining_calories * fat_percentage)
        fats_g = int(fat_calories / 9)
        
        # Carbs get the rest
        carb_calories = remaining_calories - fat_calories
        carbs_g = int(carb_calories / 4)
        
        return protein_g, carbs_g, fats_g
    
    def _generate_sample_meals(
        self,
        diet_type: str,
        allergies: List[str],
        dislikes: List[str],
        meal_frequency: int,
        meal_prep_level: str,
        daily_calories: int,
        protein_g: int,
        carbs_g: int,
        fats_g: int
    ) -> List[SampleMeal]:
        """Generate 3-5 sample meal ideas that fit the plan."""
        # This is a simplified example - real implementation would have a meal database
        
        sample_meals = []
        
        # Example breakfast
        if "dairy" not in allergies and diet_type != "vegan":
            sample_meals.append(SampleMeal(
                meal_type=MealType.BREAKFAST,
                name="Protein Oatmeal Bowl",
                ingredients=["oats", "protein powder", "banana", "almond butter", "berries"],
                approximate_calories=int(daily_calories / meal_frequency),
                approximate_protein_g=int(protein_g / meal_frequency),
                approximate_carbs_g=int(carbs_g / meal_frequency),
                approximate_fats_g=int(fats_g / meal_frequency),
                prep_time_minutes=10
            ))
        
        # Add more sample meals based on diet_type, allergies, dislikes, meal_prep_level
        # (Implementation would generate 3-5 diverse meal ideas)
        
        return sample_meals
    
    def _generate_meal_timing(self, meal_frequency: int, workout_frequency: int) -> str:
        """Generate meal timing suggestions."""
        if meal_frequency == 3:
            return "Breakfast (7-8am), Lunch (12-1pm), Dinner (6-7pm). Have a carb-rich meal 2-3 hours before workouts."
        elif meal_frequency == 4:
            return "Breakfast (7-8am), Lunch (12-1pm), Snack (3-4pm), Dinner (7-8pm). Time snack around workouts for energy."
        elif meal_frequency == 5:
            return "Breakfast (7am), Snack (10am), Lunch (1pm), Snack (4pm), Dinner (7pm). Pre-workout snack 1-2 hours before training."
        else:
            return f"Distribute {meal_frequency} meals evenly throughout the day, spacing them 3-4 hours apart."
    
    def _recalculate_macros(
        self,
        new_calories: int,
        old_protein: int,
        old_carbs: int,
        old_fats: int
    ) -> tuple[int, int, int]:
        """Recalculate macros proportionally when calories change."""
        old_calories = (old_protein * 4) + (old_carbs * 4) + (old_fats * 9)
        ratio = new_calories / old_calories
        
        new_protein = int(old_protein * ratio)
        new_carbs = int(old_carbs * ratio)
        new_fats = int(old_fats * ratio)
        
        return new_protein, new_carbs, new_fats
```


## Data Models

### Agent Context Structure

#### Workout Planning Context

```python
{
    "workout_planning": {
        "preferences": {
            "location": "gym",
            "frequency": 4,
            "duration_minutes": 60,
            "equipment": ["barbell", "dumbbells", "cables"]
        },
        "proposed_plan": {
            "frequency": 4,
            "duration_minutes": 60,
            "location": "gym",
            "equipment": ["barbell", "dumbbells", "cables"],
            "training_split": "Upper/Lower",
            "workout_days": [...],
            "progression_strategy": "Progressive overload..."
        },
        "user_approved": True,
        "completed_at": "2024-01-15T10:45:00Z"
    }
}
```

#### Diet Planning Context

```python
{
    "diet_planning": {
        "preferences": {
            "diet_type": "omnivore",
            "allergies": ["dairy"],
            "dislikes": ["broccoli"],
            "meal_frequency": 4,
            "meal_prep_level": "medium"
        },
        "proposed_plan": {
            "diet_type": "omnivore",
            "allergies": ["dairy"],
            "dislikes": ["broccoli"],
            "meal_frequency": 4,
            "meal_prep_level": "medium",
            "daily_calories": 2400,
            "protein_g": 150,
            "carbs_g": 300,
            "fats_g": 67,
            "sample_meals": [...],
            "meal_timing_suggestions": "..."
        },
        "user_approved": True,
        "completed_at": "2024-01-15T11:00:00Z"
    }
}
```

### Combined Context After All Planning Agents

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
        "completed_at": "2024-01-15T10:35:00Z"
    },
    "workout_planning": {
        "preferences": {...},
        "proposed_plan": {...},
        "user_approved": True,
        "completed_at": "2024-01-15T10:45:00Z"
    },
    "diet_planning": {
        "preferences": {...},
        "proposed_plan": {...},
        "user_approved": True,
        "completed_at": "2024-01-15T11:00:00Z"
    }
}
```

This combined context is available to the Scheduling Agent (Spec 4) and all post-onboarding agents.


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Plan Approval Saves Data with Metadata

*For any* approved workout or meal plan, when the save tool is called with user_approved=True, the data should be persisted to agent_context with both user_approved=True and a completed_at timestamp in ISO 8601 format.

**Validates: Requirements 3.7, 3.8, 6.7, 6.8**

### Property 2: Step Completion After Approval

*For any* planning agent (workout or diet), when a plan is saved with user_approved=True, the agent's _check_if_complete method should return True, and the next process_message call should set step_complete=True and next_action="advance_step".

**Validates: Requirements 1.9, 1.10, 4.10, 4.11**

### Property 3: Fitness Level Determines Frequency Range

*For any* workout plan generated with a given fitness_level, the recommended frequency should fall within the appropriate range: beginner (2-4 days), intermediate (3-5 days), or advanced (4-6 days).

**Validates: Requirements 2.2, 2.3, 2.4**

### Property 4: Muscle Gain Plans Emphasize Hypertrophy Rep Ranges

*For any* workout plan generated with primary_goal="muscle_gain", the majority of resistance exercises should have rep ranges in the 8-12 range (hypertrophy zone).

**Validates: Requirements 2.5**

### Property 5: Fat Loss Plans Include Cardio

*For any* workout plan generated with primary_goal="fat_loss", the plan should include at least one cardio or conditioning component per week.

**Validates: Requirements 2.6**

### Property 6: Exercise Selection Matches Location and Equipment

*For any* workout plan generated, if location="home" and equipment is limited (fewer than 3 items), then at least 60% of exercises should be bodyweight exercises; if location="gym", then at least 60% of exercises should utilize equipment.

**Validates: Requirements 2.8, 2.9**

### Property 7: Workout Duration Constraint

*For any* workout plan generated with duration_minutes=D, the total estimated duration for each workout day (sum of sets × reps × rest_seconds for all exercises) should not exceed D minutes.

**Validates: Requirements 2.10**

### Property 8: Workout Plan Structural Completeness

*For any* WorkoutPlan object created, it should contain all required fields: frequency, duration_minutes, training_split, workout_days (with exercises), and progression_strategy, and each exercise should have name, sets, reps, and rest_seconds.

**Validates: Requirements 2.11, 2.12, 13.1, 13.4**

### Property 9: Workout Plan Validation Ranges

*For any* WorkoutPlan object created, frequency should be between 2 and 7 (inclusive), and duration_minutes should be between 20 and 180 (inclusive); attempting to create a plan outside these ranges should raise ValueError.

**Validates: Requirements 13.2, 13.3**

### Property 10: Calorie Targets Align with Goals

*For any* meal plan generated, if primary_goal="muscle_gain", daily_calories should be TDEE + 300-500; if primary_goal="fat_loss", daily_calories should be TDEE - 300-500; if primary_goal="general_fitness", daily_calories should equal TDEE (within 50 calories).

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 11: Dietary Restrictions Respected

*For any* meal plan generated, if diet_type="vegetarian", sample meals should not contain meat or fish; if diet_type="vegan", sample meals should not contain any animal products (meat, fish, dairy, eggs, honey).

**Validates: Requirements 5.5, 5.6**

### Property 12: Allergen and Dislike Exclusion

*For any* meal plan generated with allergies or dislikes specified, none of the sample meals should contain ingredients from the allergies or dislikes lists.

**Validates: Requirements 5.7, 5.8**

### Property 13: Meal Frequency Matches Plan

*For any* meal plan generated with meal_frequency=N, the meal_timing_suggestions should reference N meals, and if sample meals are categorized by meal type, the distribution should support N meals per day.

**Validates: Requirements 5.9**

### Property 14: High Training Volume Increases Calories

*For any* two meal plans generated with the same primary_goal but different workout frequencies, the plan with higher workout frequency (5+ days) should have higher daily_calories and carbs_g than the plan with lower frequency (2-3 days).

**Validates: Requirements 5.10**

### Property 15: Meal Plan Structural Completeness

*For any* MealPlan object created, it should contain all required fields: daily_calories, protein_g, carbs_g, fats_g, meal_frequency, sample_meals (with at least 3 meals), and meal_timing_suggestions.

**Validates: Requirements 5.11, 5.12, 13.5, 13.9**

### Property 16: Meal Plan Validation Ranges

*For any* MealPlan object created, daily_calories should be between 1200 and 5000 (inclusive), and meal_frequency should be between 2 and 6 (inclusive); attempting to create a plan outside these ranges should raise ValueError.

**Validates: Requirements 13.6, 13.8**

### Property 17: Macro Sum Equals Calories (Critical Invariant)

*For any* MealPlan object created, the sum of (protein_g × 4) + (carbs_g × 4) + (fats_g × 9) should equal daily_calories within 10% tolerance (to account for rounding).

**Validates: Requirements 13.7**

### Property 18: Save Tool Rejects Unapproved Plans

*For any* call to save_workout_plan or save_meal_plan with user_approved=False, the tool should return an error status without saving data to agent_context.

**Validates: Requirements 3.6**

### Property 19: Generate Tool Returns Valid Plan Structure

*For any* successful call to generate_workout_plan or generate_meal_plan, the returned dictionary should be deserializable into a valid WorkoutPlan or MealPlan object respectively.

**Validates: Requirements 3.4, 3.11**

### Property 20: Context Handover to Diet Planning

*For any* DietPlanningAgent instantiation, if agent_context contains workout_planning data, the agent should have access to the workout plan's frequency and use it to adjust calorie calculations.

**Validates: Requirements 12.6, 12.7**


## Error Handling

### Error Categories

1. **Plan Generation Errors**
   - Invalid fitness_level (not beginner/intermediate/advanced)
   - Invalid primary_goal (not fat_loss/muscle_gain/general_fitness)
   - Invalid frequency (not 2-7)
   - Invalid duration_minutes (not 20-180)
   - Invalid diet_type (not omnivore/vegetarian/vegan/pescatarian)
   - Invalid meal_frequency (not 2-6)
   - Invalid daily_calories (not 1200-5000)
   - Conflicting constraints (e.g., vegan + pescatarian)

2. **Tool Execution Errors**
   - Save called without user approval (user_approved=False)
   - Save called before plan generation
   - Modify called with invalid modifications
   - Database connection failures
   - Transaction commit failures

3. **Service Errors**
   - WorkoutPlanGenerator exceptions
   - MealPlanGenerator exceptions
   - Macro calculation errors
   - Exercise database lookup failures

4. **LLM Errors**
   - API rate limiting
   - API failures
   - Parsing errors in tool calls
   - Approval detection failures

### Error Handling Strategy

**Plan Generation Validation Errors**:
```python
def _validate_inputs(self, fitness_level: str, primary_goal: str, frequency: int, duration_minutes: int):
    valid_levels = ["beginner", "intermediate", "advanced"]
    if fitness_level not in valid_levels:
        raise ValueError(f"fitness_level must be one of {valid_levels}")
    
    valid_goals = ["fat_loss", "muscle_gain", "general_fitness"]
    if primary_goal not in valid_goals:
        raise ValueError(f"primary_goal must be one of {valid_goals}")
    
    if not (2 <= frequency <= 7):
        raise ValueError("frequency must be between 2 and 7 days per week")
    
    if not (20 <= duration_minutes <= 180):
        raise ValueError("duration_minutes must be between 20 and 180")
```

**Tool Execution Errors**:
```python
@tool
async def save_workout_plan(plan_data: dict, user_approved: bool) -> dict:
    if not user_approved:
        return {
            "status": "error",
            "message": "Cannot save plan without user approval"
        }
    
    try:
        await self.save_context(user_id, workout_data)
        return {"status": "success", "message": "Workout plan saved successfully"}
    except Exception as e:
        logger.error(f"Error saving workout plan: {e}")
        return {
            "status": "error",
            "message": "Failed to save workout plan. Please try again."
        }
```

**Service Exception Handling**:
```python
@tool
async def generate_workout_plan(frequency: int, location: str, duration_minutes: int, equipment: list) -> dict:
    try:
        plan = await self.workout_generator.generate_plan(...)
        return plan.dict()
    except ValueError as e:
        return {
            "error": str(e),
            "message": "Invalid parameters for workout plan generation"
        }
    except Exception as e:
        logger.error(f"Error generating workout plan: {e}")
        return {
            "error": "generation_failed",
            "message": "Failed to generate workout plan. Please try again."
        }
```

**Macro Calculation Validation**:
```python
def _calculate_macros(self, daily_calories: int, primary_goal: str, workout_frequency: int) -> tuple[int, int, int]:
    protein_g, carbs_g, fats_g = # ... calculations
    
    # Validate macro sum equals calories (within 10%)
    calculated_calories = (protein_g * 4) + (carbs_g * 4) + (fats_g * 9)
    tolerance = daily_calories * 0.1
    
    if abs(calculated_calories - daily_calories) > tolerance:
        logger.warning(f"Macro sum {calculated_calories} differs from target {daily_calories}")
        # Adjust macros proportionally to match target
        protein_g, carbs_g, fats_g = self._adjust_macros_to_target(
            protein_g, carbs_g, fats_g, daily_calories
        )
    
    return protein_g, carbs_g, fats_g
```

### Error Response Format

All tool errors return consistent structure:
```python
{
    "status": "error",
    "message": "Human-readable error description",
    "error": "error_code"  # Optional
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
- **Tag format**: `# Feature: planning-agents-proposal-workflow, Property {number}: {property_text}`

### Unit Testing Focus

Unit tests should focus on:
- Specific examples that demonstrate correct behavior (e.g., beginner plan generation)
- Integration points between agents and plan generators
- Edge cases (minimum/maximum frequencies, empty equipment lists, multiple allergies)
- Error conditions (invalid parameters, database failures, unapproved saves)
- Approval detection examples (specific phrases that should trigger saves)
- Modification workflow (request change → modify → present → approve)

Avoid writing too many unit tests for scenarios that property tests already cover. For example, don't write 10 unit tests for different frequency values when Property 3 already validates all frequency ranges.

### Test Organization

```
backend/tests/
├── test_planning_agents/
│   ├── test_workout_planning_agent.py      # Unit tests for WorkoutPlanningAgent
│   ├── test_diet_planning_agent.py         # Unit tests for DietPlanningAgent
│   ├── test_workout_plan_generator.py      # Unit tests for WorkoutPlanGenerator
│   ├── test_meal_plan_generator.py         # Unit tests for MealPlanGenerator
│   ├── test_agent_tools.py                 # Unit tests for agent tools
│   ├── test_approval_detection.py          # Unit tests for approval intent detection
│   ├── test_modification_workflow.py       # Integration tests for modification flow
│   ├── test_properties.py                  # Property-based tests
│   └── conftest.py                         # Shared fixtures
```

### Property Test Examples

**Property 3: Fitness Level Determines Frequency Range**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    fitness_level=st.sampled_from(["beginner", "intermediate", "advanced"]),
    primary_goal=st.sampled_from(["fat_loss", "muscle_gain", "general_fitness"]),
    location=st.sampled_from(["home", "gym"]),
    duration_minutes=st.integers(min_value=20, max_value=180),
    equipment=st.lists(st.sampled_from(["dumbbells", "barbell", "resistance_bands"]), max_size=5)
)
async def test_fitness_level_frequency_range_property(
    fitness_level: str,
    primary_goal: str,
    location: str,
    duration_minutes: int,
    equipment: list
):
    """
    Feature: planning-agents-proposal-workflow, Property 3: Fitness Level Determines Frequency Range
    
    For any workout plan with a given fitness_level, frequency should be in appropriate range.
    """
    generator = WorkoutPlanGenerator()
    
    # Generate plan with recommended frequency for this level
    if fitness_level == "beginner":
        frequency = 3  # Middle of 2-4 range
    elif fitness_level == "intermediate":
        frequency = 4  # Middle of 3-5 range
    else:  # advanced
        frequency = 5  # Middle of 4-6 range
    
    plan = await generator.generate_plan(
        fitness_level=fitness_level,
        primary_goal=primary_goal,
        frequency=frequency,
        location=location,
        duration_minutes=duration_minutes,
        equipment=equipment
    )
    
    # Verify frequency is in appropriate range
    if fitness_level == "beginner":
        assert 2 <= plan.frequency <= 4
    elif fitness_level == "intermediate":
        assert 3 <= plan.frequency <= 5
    else:  # advanced
        assert 4 <= plan.frequency <= 6
```

**Property 17: Macro Sum Equals Calories (Critical)**
```python
@given(
    primary_goal=st.sampled_from(["fat_loss", "muscle_gain", "general_fitness"]),
    workout_frequency=st.integers(min_value=2, max_value=7),
    diet_type=st.sampled_from(["omnivore", "vegetarian", "vegan", "pescatarian"]),
    meal_frequency=st.integers(min_value=2, max_value=6)
)
async def test_macro_sum_equals_calories_property(
    primary_goal: str,
    workout_frequency: int,
    diet_type: str,
    meal_frequency: int
):
    """
    Feature: planning-agents-proposal-workflow, Property 17: Macro Sum Equals Calories
    
    For any meal plan, (protein×4) + (carbs×4) + (fats×9) should equal daily_calories within 10%.
    """
    generator = MealPlanGenerator()
    
    workout_plan = {"frequency": workout_frequency}
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal=primary_goal,
        workout_plan=workout_plan,
        diet_type=diet_type,
        allergies=[],
        dislikes=[],
        meal_frequency=meal_frequency,
        meal_prep_level="medium"
    )
    
    # Calculate calories from macros
    calculated_calories = (plan.protein_g * 4) + (plan.carbs_g * 4) + (plan.fats_g * 9)
    
    # Verify within 10% tolerance
    tolerance = plan.daily_calories * 0.1
    assert abs(calculated_calories - plan.daily_calories) <= tolerance, \
        f"Macro sum {calculated_calories} differs from target {plan.daily_calories} by more than 10%"
```

**Property 11: Dietary Restrictions Respected**
```python
@given(
    diet_type=st.sampled_from(["vegetarian", "vegan"]),
    primary_goal=st.sampled_from(["fat_loss", "muscle_gain", "general_fitness"]),
    meal_frequency=st.integers(min_value=2, max_value=6)
)
async def test_dietary_restrictions_property(
    diet_type: str,
    primary_goal: str,
    meal_frequency: int
):
    """
    Feature: planning-agents-proposal-workflow, Property 11: Dietary Restrictions Respected
    
    For any vegetarian/vegan plan, sample meals should not contain restricted ingredients.
    """
    generator = MealPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal=primary_goal,
        workout_plan={"frequency": 4},
        diet_type=diet_type,
        allergies=[],
        dislikes=[],
        meal_frequency=meal_frequency,
        meal_prep_level="medium"
    )
    
    # Define restricted ingredients
    meat_fish = ["chicken", "beef", "pork", "fish", "salmon", "tuna", "turkey"]
    animal_products = meat_fish + ["dairy", "milk", "cheese", "eggs", "yogurt", "honey"]
    
    # Check all sample meals
    for meal in plan.sample_meals:
        ingredients_lower = [ing.lower() for ing in meal.ingredients]
        
        if diet_type == "vegetarian":
            # Should not contain meat or fish
            for restricted in meat_fish:
                assert restricted not in ingredients_lower, \
                    f"Vegetarian meal contains {restricted}"
        
        elif diet_type == "vegan":
            # Should not contain any animal products
            for restricted in animal_products:
                assert restricted not in ingredients_lower, \
                    f"Vegan meal contains {restricted}"
```


### Unit Test Examples

**Workout Plan Generation Test**
```python
async def test_generate_beginner_muscle_gain_plan():
    """Test generating a workout plan for beginner with muscle gain goal."""
    generator = WorkoutPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="beginner",
        primary_goal="muscle_gain",
        frequency=3,
        location="gym",
        duration_minutes=60,
        equipment=["dumbbells", "barbell"],
        limitations=[]
    )
    
    assert plan.frequency == 3
    assert plan.training_split == "Full Body"
    assert len(plan.workout_days) == 3
    
    # Verify exercises emphasize compound movements
    all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
    compound_exercises = [ex for ex in all_exercises if ex.type == ExerciseType.COMPOUND]
    assert len(compound_exercises) >= len(all_exercises) * 0.6  # At least 60% compound
```

**Meal Plan Generation Test**
```python
async def test_generate_fat_loss_meal_plan():
    """Test generating a meal plan for fat loss goal."""
    generator = MealPlanGenerator()
    
    workout_plan = {"frequency": 4}
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal="fat_loss",
        workout_plan=workout_plan,
        diet_type="omnivore",
        allergies=[],
        dislikes=[],
        meal_frequency=4,
        meal_prep_level="medium"
    )
    
    # Verify calorie deficit
    # Assuming TDEE ~2200 for intermediate with 4 days training
    assert 1700 <= plan.daily_calories <= 1900  # TDEE - 300-500
    
    # Verify high protein for fat loss
    assert plan.protein_g >= 135  # 1.8g/kg for 75kg person
    
    # Verify 4 sample meals
    assert len(plan.sample_meals) >= 3
```

**Approval Detection Test**
```python
async def test_approval_intent_detection(
    db_session: AsyncSession,
    test_user: User
):
    """Test that agent detects approval phrases and saves plan."""
    # Setup: Generate a plan first
    agent = WorkoutPlanningAgent(db_session, {
        "fitness_assessment": {"fitness_level": "intermediate"},
        "goal_setting": {"primary_goal": "muscle_gain"}
    })
    
    # Simulate plan generation
    tool = agent.get_tools(test_user.id)[0]  # generate_workout_plan
    plan = await tool.ainvoke({
        "frequency": 4,
        "location": "gym",
        "duration_minutes": 60,
        "equipment": ["barbell", "dumbbells"]
    })
    
    # Test approval detection
    response = await agent.process_message(
        "Yes, looks perfect!",
        test_user.id
    )
    
    # Verify plan was saved
    state = await get_onboarding_state(test_user.id, db_session)
    assert "workout_planning" in state.agent_context
    assert state.agent_context["workout_planning"]["user_approved"] is True
    assert response.step_complete is True
```

**Modification Workflow Test**
```python
async def test_modification_workflow(
    db_session: AsyncSession,
    test_user: User
):
    """Test that agent can modify plan based on user feedback."""
    agent = WorkoutPlanningAgent(db_session, {
        "fitness_assessment": {"fitness_level": "intermediate"},
        "goal_setting": {"primary_goal": "muscle_gain"}
    })
    
    # Generate initial plan
    generate_tool = agent.get_tools(test_user.id)[0]
    initial_plan = await generate_tool.ainvoke({
        "frequency": 4,
        "location": "gym",
        "duration_minutes": 60,
        "equipment": ["barbell"]
    })
    
    # Request modification
    modify_tool = agent.get_tools(test_user.id)[2]  # modify_workout_plan
    modified_plan = await modify_tool.ainvoke({
        "current_plan": initial_plan,
        "modifications": {"frequency": 3}
    })
    
    # Verify modification applied
    assert modified_plan["frequency"] == 3
    assert modified_plan["training_split"] != initial_plan["training_split"]  # Should change split
```

**Error Handling Test**
```python
async def test_save_without_approval_fails():
    """Test that save tool rejects plans without user approval."""
    agent = WorkoutPlanningAgent(mock_db, {})
    save_tool = agent.get_tools(test_user.id)[1]  # save_workout_plan
    
    result = await save_tool.ainvoke({
        "plan_data": {"frequency": 4},
        "user_approved": False
    })
    
    assert result["status"] == "error"
    assert "approval" in result["message"].lower()
```

**Allergen Exclusion Test**
```python
async def test_allergen_exclusion():
    """Test that meal plans exclude allergenic ingredients."""
    generator = MealPlanGenerator()
    
    plan = await generator.generate_plan(
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        workout_plan={"frequency": 4},
        diet_type="omnivore",
        allergies=["dairy", "eggs"],
        dislikes=[],
        meal_frequency=4,
        meal_prep_level="medium"
    )
    
    # Verify no sample meals contain dairy or eggs
    for meal in plan.sample_meals:
        ingredients_lower = [ing.lower() for ing in meal.ingredients]
        assert "dairy" not in ingredients_lower
        assert "milk" not in ingredients_lower
        assert "cheese" not in ingredients_lower
        assert "eggs" not in ingredients_lower
```

### Integration Test Example

```python
async def test_end_to_end_planning_flow(
    authenticated_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession
):
    """Test complete flow from workout planning through diet planning."""
    # Setup: Complete fitness assessment and goal setting
    state = OnboardingState(
        user_id=test_user.id,
        current_step=4,
        agent_context={
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": []
            },
            "goal_setting": {
                "primary_goal": "muscle_gain"
            }
        }
    )
    db_session.add(state)
    await db_session.commit()
    
    # Step 1: Start workout planning
    response1 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I prefer gym workouts, 4 days a week, 60 minutes per session"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["agent_type"] == "workout_planning"
    
    # Step 2: Approve workout plan
    response2 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "Yes, looks perfect!"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["step_complete"] is True
    
    # Step 3: Start diet planning
    response3 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "I'm omnivore, no allergies, I eat 4 meals a day"}
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["agent_type"] == "diet_planning"
    
    # Step 4: Approve meal plan
    response4 = await authenticated_client.post(
        "/api/v1/onboarding/chat",
        json={"message": "This meal plan looks great!"}
    )
    assert response4.status_code == 200
    data4 = response4.json()
    assert data4["step_complete"] is True
    
    # Verify both plans saved
    await db_session.refresh(state)
    assert "workout_planning" in state.agent_context
    assert "diet_planning" in state.agent_context
    assert state.agent_context["workout_planning"]["user_approved"] is True
    assert state.agent_context["diet_planning"]["user_approved"] is True
```

### Coverage Requirements

- Minimum 80% code coverage for new agent and service code
- 100% coverage for plan validation logic
- 100% coverage for macro calculation logic
- All error handling paths must be tested
- All tool functions must have validation tests

### Test Execution

```bash
# Run all tests for this feature
poetry run pytest backend/tests/test_planning_agents/

# Run only unit tests
poetry run pytest backend/tests/test_planning_agents/ -m "not property"

# Run only property tests
poetry run pytest backend/tests/test_planning_agents/test_properties.py

# Run with coverage
poetry run pytest backend/tests/test_planning_agents/ --cov=app.agents.onboarding --cov=app.services --cov-report=html

# Run specific test
poetry run pytest backend/tests/test_planning_agents/test_workout_planning_agent.py::test_generate_beginner_muscle_gain_plan
```

## Implementation Notes

### Dependencies

This feature builds on Specs 1 and 2 and requires:

```toml
[tool.poetry.dependencies]
langchain = "^0.1.0"
langchain-anthropic = "^0.1.0"
langchain-core = "^0.1.0"

[tool.poetry.group.dev.dependencies]
hypothesis = "^6.92.0"
```

These should already be installed from previous specs. No new dependencies required.

### File Structure

```
backend/app/
├── agents/
│   └── onboarding/
│       ├── __init__.py
│       ├── base.py                        # From Spec 1
│       ├── fitness_assessment.py          # From Spec 2
│       ├── goal_setting.py                # From Spec 2
│       ├── workout_planning.py            # NEW - WorkoutPlanningAgent
│       └── diet_planning.py               # NEW - DietPlanningAgent
├── services/
│   ├── onboarding_orchestrator.py         # From Spec 1
│   ├── workout_plan_generator.py          # NEW - WorkoutPlanGenerator
│   └── meal_plan_generator.py             # NEW - MealPlanGenerator
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
    elif step <= 5:
        return OnboardingAgentType.WORKOUT_PLANNING  # Routes to new agent
    elif step <= 7:
        return OnboardingAgentType.DIET_PLANNING     # Routes to new agent
    # ...
```

No changes needed to the orchestrator - it will automatically route to the new planning agents.

**API Integration**:

The `/api/v1/onboarding/chat` endpoint from Spec 1 already handles all agent interactions. No changes needed.

### Configuration

Use existing configuration from `app/core/config.py`. No new configuration required.

### Logging

Add logging for plan generation and approval:

```python
import logging

logger = logging.getLogger(__name__)

# In plan generators
logger.info(f"Generating workout plan for {fitness_level} level, {primary_goal} goal")
logger.debug(f"Plan parameters: frequency={frequency}, location={location}")

# In tools
logger.info(f"Saving workout plan for user {user_id}")
logger.warning(f"Save attempted without approval for user {user_id}")

# In agents
logger.debug(f"Processing message for {self.agent_type}: {message[:50]}...")
logger.info(f"Plan approved and saved for user {user_id}")
```

### Performance Considerations

**Plan Generation**:
- Workout plan generation: < 500ms (mostly computation)
- Meal plan generation: < 500ms (mostly computation)
- No external API calls required

**LLM Calls**:
- Each `process_message` makes one LLM API call
- Average latency: 1-2 seconds
- Tool calls add minimal overhead

**Database Operations**:
- Plan saves use single UPDATE query
- Context loaded once per request
- No complex queries

### Security Considerations

**Input Validation**:
- All plan parameters validated before generation
- Pydantic models enforce type safety
- Range checks on numeric inputs

**Data Privacy**:
- Plans contain no PII beyond user_id
- All data encrypted at rest
- Plans are user-specific and isolated

**API Security**:
- All endpoints require JWT authentication (from Spec 1)
- Users can only access their own plans
- No cross-user data leakage

### Monitoring and Observability

**Metrics to Track**:
- Plan generation time (p50, p95, p99)
- Approval rate (% of plans approved on first presentation)
- Modification rate (% of plans modified before approval)
- Tool call success rate
- Average messages per agent before completion

**Logging Events**:
- Plan generation (success/failure)
- Plan modifications
- Approval detection
- Tool calls (success/failure)
- Context handover

**Alerts**:
- High error rate in plan generation
- Macro calculation validation failures
- Database connection issues
- LLM API failures

## Future Enhancements

This implementation enables future enhancements:

1. **Plan Versioning**: Track plan modifications over time
2. **Plan Templates**: Pre-built plans for common scenarios
3. **Exercise Database**: Comprehensive exercise library with videos/GIFs
4. **Meal Database**: Extensive meal library with nutrition data
5. **AI-Powered Modifications**: LLM suggests modifications based on feedback
6. **Progressive Overload Tracking**: Automatic weight/rep progression
7. **Macro Flexibility**: Allow users to adjust macro ratios
8. **Multi-language Support**: Translate plans and explanations

## Conclusion

The Planning Agents with Proposal Workflow feature provides intelligent, conversational plan generation for workout and meal planning. The agents use specialized services to create personalized plans, present them with clear explanations, detect approval intent from natural language, and allow iterative refinement until users are satisfied.

The implementation follows the patterns established in Specs 1 and 2, extends the base agent architecture with plan generation capabilities, and provides comprehensive testing with both unit and property-based tests.

Key achievements:
- Active plan generation using specialized services
- Conversational approval detection without explicit commands
- Iterative modification workflow for plan refinement
- Context-driven personalization using all previous agent data
- Robust validation and error handling
- Critical invariants verified through property-based testing (macro sum = calories)

This feature is production-ready and provides the foundation for the final onboarding agent (Scheduling) in Spec 4.

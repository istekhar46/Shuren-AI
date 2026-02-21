# Technical Requirements Document (TRD)
## Specialized Onboarding Agent System

---

## 1. Document Purpose

This TRD defines the technical architecture and implementation requirements for the specialized onboarding agent system. Unlike the current implementation where onboarding is a simple form-based flow, this system uses dedicated AI agents for each onboarding step to provide personalized guidance, propose plans, and progressively build user context.

---

## 2. System Overview

### 2.1 Current State
The existing onboarding system:
- Uses a single generic flow with step-by-step data collection
- Stores data in `OnboardingState` table with JSONB `step_data`
- Has a single `OnboardingService` that validates and saves step data
- Creates user profile only after all steps are complete

### 2.2 Target State
The new specialized onboarding agent system:
- Each step is handled by a dedicated AI agent with domain expertise
- Agents ask personalized questions based on previous context
- Agents propose plans (workout/meal) for user approval
- Each agent updates the user profile incrementally
- Context is passed between agents as onboarding progresses
- Post-onboarding, only General Assistant Agent is available

---

## 3. Architecture Design

### 3.1 Onboarding Agent Types

```python
class OnboardingAgentType(str, Enum):
    FITNESS_ASSESSMENT = "fitness_assessment"      # Step 1-2: Fitness level
    GOAL_SETTING = "goal_setting"                  # Step 3: Goals
    WORKOUT_PLANNING = "workout_planning"          # Step 4-5: Workout preferences & plan
    DIET_PLANNING = "diet_planning"                # Step 6-7: Diet preferences & meal plan
    SCHEDULING = "scheduling"                      # Step 8-9: Schedules
```

### 3.2 Agent Responsibilities

#### Fitness Assessment Agent (Steps 1-2)
**Purpose**: Assess user's current fitness level and experience

**Responsibilities**:
- Ask about current fitness level (beginner/intermediate/advanced)
- Inquire about exercise experience
- Assess physical limitations (non-medical)
- Save fitness level to user profile

**System Prompt**:
```
You are a Fitness Assessment Agent helping users determine their fitness level.

Your role:
- Ask friendly questions about their exercise experience
- Assess their fitness level (beginner/intermediate/advanced)
- Identify any physical limitations (equipment, injuries - non-medical)
- Be encouraging and non-judgmental

Guidelines:
- Keep questions conversational
- Don't overwhelm with too many questions at once
- Never provide medical advice
- Save assessment results when user confirms
```

**Tools Available**:
- `save_fitness_assessment(fitness_level, experience_details, limitations)`

#### Goal Setting Agent (Step 3)
**Purpose**: Define user's fitness goals

**Responsibilities**:
- Understand primary fitness goal (fat loss/muscle gain/general fitness)
- Identify secondary goals if any
- Set realistic expectations
- Save goals to user profile

**System Prompt**:
```
You are a Goal Setting Agent helping users define their fitness objectives.

Your role:
- Understand their primary fitness goal
- Identify any secondary goals
- Set realistic expectations based on their fitness level
- Explain how the system will help achieve these goals

Guidelines:
- Be realistic but encouraging
- Explain what each goal means
- Help prioritize if they have multiple goals
- Save goals when user confirms
```

**Tools Available**:
- `save_fitness_goals(primary_goal, secondary_goal, target_weight, target_body_fat)`

#### Workout Planning Agent (Steps 4-5)
**Purpose**: Gather workout preferences and propose workout plan

**Responsibilities**:
- Ask about workout preferences (home/gym, equipment available)
- Inquire about workout frequency preference
- Ask about time constraints
- **Generate and propose a workout plan**
- Get user approval before saving
- Save workout plan to user profile

**System Prompt**:
```
You are a Workout Planning Agent creating personalized workout plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Limitations: {limitations}

Your role:
- Ask about workout preferences (location, equipment, frequency)
- Understand time constraints
- Generate a workout plan tailored to their level and goals
- Present the plan for approval
- Explain the reasoning behind the plan
- Save plan only after user approves

Guidelines:
- Propose realistic workout frequency based on their level
- Consider equipment availability
- Explain exercise selection rationale
- Allow modifications if user requests
- Get explicit approval before saving
```

**Tools Available**:
- `generate_workout_plan(preferences) -> WorkoutPlan`
- `save_workout_plan(workout_plan, user_approved=True)` - Called when user says "yes", "looks good", "approve", etc.
- `modify_workout_plan(workout_plan, modifications) -> WorkoutPlan`

**Conversational Approval Flow**:
```
Agent: "Here's your 4-day workout plan: [displays plan]. Does this work for you?"

User: "Yes, looks perfect!"
    ↓
Agent detects approval intent
    ↓
Agent calls: save_workout_plan(plan_data, user_approved=True)
    ↓
Plan saved to user profile
    ↓
Agent: "Excellent! Your workout plan is saved. Now let's talk about your nutrition."
    ↓
System advances to Diet Planning Agent
```

#### Diet Planning Agent (Steps 6-7)
**Purpose**: Gather diet preferences and propose meal plan

**Responsibilities**:
- Ask about dietary preferences (veg/non-veg/vegan)
- Identify allergies and intolerances
- Understand meal prep willingness
- **Generate and propose a meal plan**
- Get user approval before saving
- Save meal plan to user profile

**System Prompt**:
```
You are a Diet Planning Agent creating personalized meal plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Workout Plan: {workout_summary}

Your role:
- Ask about dietary preferences and restrictions
- Understand meal prep capabilities
- Generate a meal plan aligned with their goals
- Present the plan with sample meals
- Explain macro breakdown and reasoning
- Save plan only after user approves

Guidelines:
- Respect dietary restrictions strictly
- Propose realistic meal frequency
- Explain calorie and macro targets
- Show sample meal options
- Allow modifications if user requests
- Get explicit approval before saving
```

**Tools Available**:
- `generate_meal_plan(preferences, goal, workout_plan) -> MealPlan`
- `save_meal_plan(meal_plan, user_approved=True)` - Called when user says "yes", "looks good", "approve", etc.
- `modify_meal_plan(meal_plan, modifications) -> MealPlan`

**Conversational Approval Flow**:
```
Agent: "Here's your personalized meal plan: [displays plan with macros and sample meals]. Does this meal plan work for you?"

User: "Yes, this looks good!"
    ↓
Agent detects approval intent
    ↓
Agent calls: save_meal_plan(plan_data, user_approved=True)
    ↓
Plan saved to user profile
    ↓
Agent: "Perfect! Your meal plan is saved. Now let's set up your daily schedule."
    ↓
System advances to Scheduling Agent
```

#### Scheduling Agent (Steps 8-9)
**Purpose**: Set up workout, meal, and hydration schedules

**Responsibilities**:
- Set workout schedule (days and times)
- Set meal timing schedule
- Configure hydration reminders
- Save all schedules to user profile

**System Prompt**:
```
You are a Scheduling Agent helping users set up their daily routines.

Context from previous steps:
- Workout Plan: {workout_plan}
- Meal Plan: {meal_plan}

Your role:
- Set workout days and times
- Set meal timing for each meal
- Configure hydration reminders
- Ensure schedule is realistic and sustainable

Guidelines:
- Consider their daily routine
- Suggest optimal timing based on goals
- Be flexible with timing preferences
- Explain importance of consistency
- Save schedules when user confirms
```

**Tools Available**:
- `save_workout_schedule(days, times)`
- `save_meal_schedule(meal_times)`
- `save_hydration_preferences(frequency, target_ml)`

---

## 4. Data Model Changes

### 4.1 OnboardingState Table (Enhanced)

```python
class OnboardingState(Base):
    __tablename__ = "onboarding_states"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True, nullable=False)
    current_step = Column(Integer, nullable=False, default=0)
    current_agent = Column(String(50))  # NEW: Current agent handling the step
    is_complete = Column(Boolean, default=False)
    step_data = Column(JSONB, default={})
    agent_context = Column(JSONB, default={})  # NEW: Context passed between agents
    conversation_history = Column(JSONB, default=[])  # NEW: Chat history per step
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 4.2 Agent Context Structure

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
        "target_weight_kg": 75,
        "completed_at": "2024-01-15T10:35:00Z"
    },
    "workout_planning": {
        "preferences": {
            "location": "gym",
            "frequency": 4,
            "duration_minutes": 60
        },
        "proposed_plan": {...},
        "user_approved": true,
        "completed_at": "2024-01-15T10:45:00Z"
    },
    "diet_planning": {
        "preferences": {
            "diet_type": "non_veg",
            "allergies": ["dairy"],
            "meal_frequency": 4
        },
        "proposed_plan": {...},
        "user_approved": true,
        "completed_at": "2024-01-15T11:00:00Z"
    },
    "scheduling": {
        "workout_schedule": [...],
        "meal_schedule": [...],
        "hydration_preferences": {...},
        "completed_at": "2024-01-15T11:10:00Z"
    }
}
```

---

## 5. API Design

### 5.1 New Endpoints

#### POST /api/v1/onboarding/chat
**Purpose**: Chat with current onboarding agent

```python
@router.post("/chat", response_model=OnboardingChatResponse)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OnboardingChatResponse:
    """
    Chat with the current onboarding agent.
    
    The agent is determined by the current onboarding step.
    Agent has access to all previous context.
    """
```

**Request**:
```json
{
    "message": "I workout 3 times a week currently",
    "step": 1
}
```

**Response**:
```json
{
    "agent_type": "fitness_assessment",
    "message": "Great! 3 times a week shows good consistency. What types of exercises do you usually do?",
    "current_step": 1,
    "step_complete": false,
    "next_action": "continue_conversation",
    "context_summary": {
        "fitness_level": "intermediate",
        "workout_frequency": 3
    }
}
```

#### POST /api/v1/onboarding/chat
**Purpose**: Chat with current onboarding agent (handles all interactions including plan approval)

The agent uses tools to save plans when user approves them conversationally.

**Request**:
```json
{
    "message": "Yes, looks perfect!",
    "step": 4
}
```

**Response**:
```json
{
    "agent_type": "workout_planning",
    "message": "Excellent! Your workout plan is saved. Now let's talk about your nutrition.",
    "current_step": 4,
    "step_complete": true,
    "next_action": "advance_to_next_agent"
}
```

#### GET /api/v1/onboarding/current-agent
**Purpose**: Get current agent info and context

```python
@router.get("/current-agent", response_model=CurrentAgentResponse)
async def get_current_agent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CurrentAgentResponse:
    """
    Get information about the current onboarding agent.
    
    Returns agent type, step number, and context summary.
    """
```

**Response**:
```json
{
    "agent_type": "workout_planning",
    "current_step": 4,
    "agent_description": "I'll help you create a personalized workout plan",
    "context_summary": {
        "fitness_level": "intermediate",
        "primary_goal": "muscle_gain",
        "limitations": []
    },
    "expected_actions": ["chat", "approve_plan"]
}
```

---

## 6. Service Layer Implementation

### 6.1 OnboardingAgentOrchestrator

```python
class OnboardingAgentOrchestrator:
    """
    Orchestrates onboarding agents based on current step.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agents = {}
    
    async def get_current_agent(
        self,
        user_id: UUID
    ) -> BaseOnboardingAgent:
        """
        Get the appropriate agent for current onboarding step.
        """
        # Load onboarding state
        state = await self._load_onboarding_state(user_id)
        
        # Determine agent based on step
        agent_type = self._step_to_agent(state.current_step)
        
        # Load context from previous steps
        context = state.agent_context or {}
        
        # Create and return agent
        return await self._create_agent(agent_type, context)
    
    def _step_to_agent(self, step: int) -> OnboardingAgentType:
        """Map step number to agent type"""
        if step <= 2:
            return OnboardingAgentType.FITNESS_ASSESSMENT
        elif step == 3:
            return OnboardingAgentType.GOAL_SETTING
        elif step <= 5:
            return OnboardingAgentType.WORKOUT_PLANNING
        elif step <= 7:
            return OnboardingAgentType.DIET_PLANNING
        elif step <= 9:
            return OnboardingAgentType.SCHEDULING
        else:
            raise ValueError(f"Invalid step: {step}")
    
    async def _create_agent(
        self,
        agent_type: OnboardingAgentType,
        context: dict
    ) -> BaseOnboardingAgent:
        """Create agent instance with context"""
        agent_classes = {
            OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
            OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
            OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
            OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
            OnboardingAgentType.SCHEDULING: SchedulingAgent,
        }
        
        agent_class = agent_classes[agent_type]
        return agent_class(self.db, context)
```

### 6.2 Base Onboarding Agent

```python
class BaseOnboardingAgent(ABC):
    """
    Base class for all onboarding agents.
    """
    
    def __init__(self, db: AsyncSession, context: dict):
        self.db = db
        self.context = context
        self.llm = self._init_llm()
    
    @abstractmethod
    async def process_message(self, message: str, user_id: UUID) -> AgentResponse:
        """Process user message and return response"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return agent-specific tools"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return agent-specific system prompt"""
        pass
    
    def _init_llm(self):
        """Initialize LLM with agent config"""
        from langchain_anthropic import ChatAnthropic
        
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0.7,
            max_tokens=2048
        )
    
    async def save_context(self, user_id: UUID, agent_data: dict):
        """Save agent context to onboarding state"""
        stmt = select(OnboardingState).where(OnboardingState.user_id == user_id)
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state:
            agent_context = state.agent_context or {}
            agent_context[self.agent_type] = agent_data
            state.agent_context = agent_context
            await self.db.commit()
```

### 6.3 Example: Workout Planning Agent Implementation

```python
class WorkoutPlanningAgent(BaseOnboardingAgent):
    """
    Specialized agent for workout planning during onboarding.
    """
    
    agent_type = "workout_planning"
    
    async def process_message(self, message: str, user_id: UUID) -> AgentResponse:
        """Process user message about workout preferences"""
        
        # Build prompt with context
        system_prompt = self.get_system_prompt()
        
        # Create agent with tools
        from langchain.agents import create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(),
            prompt=ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{input}"),
                ("assistant", "{agent_scratchpad}")
            ])
        )
        
        # Execute agent
        result = await agent.ainvoke({"input": message})
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=self._check_if_complete(),
            next_action=self._determine_next_action()
        )
    
    def get_system_prompt(self) -> str:
        """Build system prompt with context"""
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "unknown")
        
        return f"""
You are a Workout Planning Agent creating personalized workout plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Limitations: {self.context.get("fitness_assessment", {}).get("limitations", [])}

Your role:
- Ask about workout preferences (location, equipment, frequency)
- Understand time constraints
- Generate a workout plan tailored to their level and goals
- Present the plan for approval
- Explain the reasoning behind the plan
- When user approves (says "yes", "looks good", "perfect", etc.), call save_workout_plan tool

Guidelines:
- Propose realistic workout frequency based on their level
- Consider equipment availability
- Explain exercise selection rationale
- Detect approval intent from user messages
- Call save_workout_plan ONLY after user explicitly approves

Current conversation stage: {self._get_conversation_stage()}
        """
    
    def get_tools(self) -> List:
        """Workout planning specific tools"""
        
        @tool
        async def generate_workout_plan(
            frequency: int,
            location: str,
            duration_minutes: int
        ) -> dict:
            """Generate a workout plan based on preferences"""
            # Call workout generation service
            from app.services.workout_service import WorkoutService
            
            workout_service = WorkoutService(self.db)
            plan = await workout_service.generate_plan(
                fitness_level=self.context["fitness_assessment"]["fitness_level"],
                goal=self.context["goal_setting"]["primary_goal"],
                frequency=frequency,
                location=location,
                duration_minutes=duration_minutes
            )
            return plan.dict()
        
        @tool
        async def save_workout_plan(plan_data: dict, user_approved: bool):
            """
            Save approved workout plan to user profile.
            
            Call this tool when user explicitly approves the plan by saying:
            - "Yes", "Looks good", "Perfect", "I approve", "Let's do it", etc.
            
            Do NOT call this tool unless user has clearly approved.
            """
            if not user_approved:
                return {"error": "Plan not approved by user"}
            
            # Save to context
            await self.save_context(user_id, {
                "proposed_plan": plan_data,
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            return {"status": "saved", "message": "Workout plan saved successfully"}
        
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
            """
            from app.services.workout_service import WorkoutService
            
            workout_service = WorkoutService(self.db)
            modified_plan = await workout_service.modify_plan(
                current_plan=current_plan,
                modifications=modifications
            )
            return modified_plan.dict()
        
        return [generate_workout_plan, save_workout_plan, modify_workout_plan]
```

---

## 7. Frontend Integration

### 7.1 Onboarding Chat UI

The frontend should display:
- Current agent name and description
- Chat interface for conversation
- Context summary panel showing progress
- Plan preview when agent proposes a plan
- Approve/Modify buttons for plan approval

### 7.2 State Management

```typescript
interface OnboardingState {
    currentStep: number;
    currentAgent: string;
    agentDescription: string;
    contextSummary: Record<string, any>;
    conversationHistory: Message[];
    proposedPlan: WorkoutPlan | MealPlan | null;
    isComplete: boolean;
}
```

### 7.3 Example Flow

```
User: "I want to build muscle"
Agent (Goal Setting): "Great goal! Building muscle requires consistent training and proper nutrition. Is this your primary goal, or do you have other objectives too?"

User: "That's my main goal"
Agent: "Perfect! I've set muscle gain as your primary goal. Let's move on to creating your workout plan."

[System advances to Workout Planning Agent]

Agent (Workout Planning): "Hi! I'm your Workout Planning Agent. Based on your intermediate fitness level and muscle gain goal, I'll help create a plan. First, where do you prefer to workout - at home or in a gym?"

User: "I have a gym membership"
Agent: "Excellent! Gym access gives us more options. How many days per week can you realistically commit to training?"

User: "4 days"
Agent: "Perfect! 4 days is ideal for muscle gain. Let me create a plan for you..."

[Agent generates plan]

Agent: "Here's your personalized 4-day workout plan:
- Day 1: Upper Body Push (Chest, Shoulders, Triceps)
- Day 2: Lower Body (Quads, Hamstrings, Glutes)
- Day 3: Rest
- Day 4: Upper Body Pull (Back, Biceps)
- Day 5: Lower Body & Core
- Days 6-7: Rest

Each session is 60-75 minutes. This split allows optimal recovery while hitting each muscle group twice per week. Does this work for you?"

User: "Yes, looks good!"
Agent: "Great! I'll save this plan. Now let's talk about your nutrition..."

[System advances to Diet Planning Agent]
```

---

## 8. Post-Onboarding Behavior

### 8.1 General Assistant Agent Access

After onboarding is complete:
- Only General Assistant Agent is available for chat
- General Assistant has full access to user profile
- Can answer queries about workouts, meals, schedules
- Cannot modify core plans without explicit user request

### 8.2 Profile Locking

```python
async def complete_onboarding(user_id: UUID):
    """
    Complete onboarding and lock profile.
    """
    # Verify all agents completed their steps
    state = await get_onboarding_state(user_id)
    
    if not all_steps_complete(state):
        raise OnboardingIncompleteError()
    
    # Create locked user profile
    profile = await create_user_profile(user_id, state.agent_context)
    profile.is_locked = True
    
    # Mark onboarding complete
    state.is_complete = True
    state.current_agent = "general_assistant"
    
    await db.commit()
    
    return profile
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create base onboarding agent classes
- [ ] Implement OnboardingAgentOrchestrator
- [ ] Update OnboardingState model with new fields
- [ ] Create new API endpoints

### Phase 2: Agent Implementation (Week 3-4)
- [ ] Implement Fitness Assessment Agent
- [ ] Implement Goal Setting Agent
- [ ] Implement Workout Planning Agent
- [ ] Implement Diet Planning Agent
- [ ] Implement Scheduling Agent

### Phase 3: Plan Generation (Week 5-6)
- [ ] Build workout plan generation service
- [ ] Build meal plan generation service
- [ ] Integrate with existing services
- [ ] Add plan approval workflow

### Phase 4: Testing & Refinement (Week 7-8)
- [ ] End-to-end onboarding testing
- [ ] Agent prompt refinement
- [ ] Context handover testing
- [ ] Performance optimization

---

## 10. Success Metrics

- Onboarding completion rate > 80%
- Average onboarding time < 15 minutes
- User satisfaction with proposed plans > 85%
- Plan modification requests < 20%
- Context handover accuracy 100%

---

## 11. Security & Privacy

- All onboarding data encrypted at rest
- Agent context contains no PII beyond user_id
- Conversation history retained for 30 days only
- User can request data deletion at any time
- No medical advice or diagnosis in any agent responses

---

## 12. Conclusion

This specialized onboarding agent system provides a personalized, conversational onboarding experience that:
- Guides users through each step with domain expertise
- Proposes tailored plans for user approval
- Builds context progressively across agents
- Creates a complete user profile incrementally
- Transitions smoothly to post-onboarding General Assistant

The architecture is extensible, allowing new agents or steps to be added without disrupting the existing flow.

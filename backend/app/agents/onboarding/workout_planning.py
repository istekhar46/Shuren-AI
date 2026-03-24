"""
Workout Planning Agent for onboarding.

This agent handles steps 4-5 of the onboarding process, creating personalized
workout plans based on user's fitness level, goals, and constraints.
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select

from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import AgentResponse
from app.services.workout_plan_generator import WorkoutPlanGenerator

logger = logging.getLogger(__name__)


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
    
    def __init__(self, db, context: dict):
        """
        Initialize workout planning agent.
        
        Args:
            db: Async database session
            context: Agent context containing fitness_assessment and goal_setting data
        """
        super().__init__(db, context)
        self.workout_generator = WorkoutPlanGenerator()
        self.current_plan = None  # Store generated plan for modifications
        self._current_user_id = None  # Store user_id for tool access
    
    def _get_agent_tools(self) -> List:
        """
        Get workout planning specific tools.
        
        Returns:
            List containing generate_workout_plan, save_workout_plan, and modify_workout_plan tools
        """
        from pydantic import BaseModel, Field
        from app.services.workout_plan_generator import WorkoutPlan
        
        # Capture self reference for use in tools
        agent_instance = self
        
        # Define Pydantic schema for tool arguments
        class WorkoutPlanInput(BaseModel):
            """Input schema for workout plan generation."""
            frequency: int = Field(
                description="Determine the optimal workout days per week (2-7) based on user goal and fitness level (do not ask user)."
            )
            location: str = Field(
                description="Workout location: home or gym"
            )
            preferred_time: str = Field(
                description="Time of day preference: morning or evening"
            )
            duration_minutes: int = Field(
                description="Determine the optimal session duration in minutes (20-180) based on user goal and fitness level (do not ask user)."
            )
            equipment: List[str] = Field(
                description="List of available equipment (e.g., dumbbells, barbell, resistance bands)"
            )
        
        @tool(args_schema=WorkoutPlanInput)
        async def generate_workout_plan(
            frequency: int,
            location: str,
            preferred_time: str,
            duration_minutes: int,
            equipment: List[str]
        ) -> dict:
            """
            Generate a personalized workout plan based on preferences.
            
            Call this tool after collecting:
            - Location (home/gym)
            - Preferred time of day (morning/evening)
            - Available equipment
            
            Args:
                frequency: Agent-determined workout days per week (2-7)
                location: "home" or "gym"
                preferred_time: Time of day preference (e.g., "morning" or "evening")
                duration_minutes: Agent-determined session duration (20-180 minutes)
                equipment: List of available equipment (e.g., ["dumbbells", "barbell"])
                
            Returns:
                Dict representation of WorkoutPlan with exercises, sets, reps, etc.
            """
            try:
                # Get context from previous agents
                fitness_level = agent_instance.context.agent_context.get("fitness_assessment", {}).get("fitness_level", "beginner")
                primary_goal = agent_instance.context.agent_context.get("fitness_assessment", {}).get("primary_goal", "general_fitness")
                goal_category = agent_instance.context.agent_context.get("fitness_assessment", {}).get("goal_category", "general_fitness")
                limitations = agent_instance.context.agent_context.get("fitness_assessment", {}).get("limitations", [])
                
                logger.info(
                    f"Generating workout plan for user {agent_instance._current_user_id}: "
                    f"level={fitness_level}, goal={primary_goal}, frequency={frequency}"
                )
                
                # Generate plan
                plan = await agent_instance.workout_generator.generate_plan(
                    fitness_level=fitness_level,
                    primary_goal=goal_category, # Use the strict category for math
                    frequency=frequency,
                    location=location,
                    duration_minutes=duration_minutes,
                    equipment=equipment,
                    limitations=limitations
                )
                
                # Store for potential modifications
                agent_instance.current_plan = plan
                
                return plan.dict()
                
            except ValueError as e:
                logger.warning(f"Validation error generating workout plan: {e}")
                return {
                    "error": str(e),
                    "message": "Invalid parameters for workout plan generation"
                }
            except Exception as e:
                logger.error(f"Error generating workout plan: {e}", exc_info=True)
                return {
                    "error": "generation_failed",
                    "message": "Failed to generate workout plan. Please try again."
                }
        
        class SaveWorkoutPlanInput(BaseModel):
            """Input schema for saving workout plan."""
            plan_data: WorkoutPlan = Field(
                description="The exact generated workout plan object to save"
            )
            workout_days: List[str] = Field(
                description="Agent-determined list of days (e.g., ['Monday', 'Wednesday', 'Friday']) based on optimal frequency."
            )
            workout_times: List[str] = Field(
                description="List of times in HH:MM format (e.g., ['06:00', '18:00']) corresponding to the preferred time of day (e.g., use 07:00 for morning, 18:00 for evening)."
            )
            user_approved: bool = Field(
                description="Must be True to save (safety check)"
            )

        @tool(args_schema=SaveWorkoutPlanInput)
        async def save_workout_plan(
            plan_data: WorkoutPlan,
            workout_days: List[str],
            workout_times: List[str],
            user_approved: bool
        ) -> dict:
            """
            Save approved workout plan and schedule to agent context.
            
            ONLY call this tool when user explicitly approves the plan by saying:
            - "Yes", "Looks good", "Perfect", "I approve", "Let's do it"
            - "Sounds great", "That works", "I'm happy with this"
            
            You (the agent) must determine the workout_days and workout_times based on the
            recommended frequency and context (e.g., if user prefers morning, use 07:00).
            DO NOT ask the user for specific days and times. Present your recommended schedule.
            
            Args:
                plan_data: The workout plan dictionary to save
                workout_days: List of days (e.g., ["Monday", "Wednesday", "Friday"])
                workout_times: List of times in HH:MM format (e.g., ["07:00", "07:00", "07:00"])
                user_approved: Must be True to save (safety check)
                
            Returns:
                Dict with status and message
            """
            if not user_approved:
                logger.warning("Attempted to save workout plan without user approval")
                return {
                    "status": "error",
                    "message": "Cannot save plan without user approval"
                }
            
            # Validate schedule
            if len(workout_days) != len(workout_times):
                return {
                    "status": "error",
                    "message": "Workout days and times must have the same length"
                }
            
            # Use strictly structured output
            actual_plan = plan_data.model_dump() if hasattr(plan_data, "model_dump") else plan_data.dict()
            
            # Prepare data with metadata and schedule
            workout_data = {
                "plan": actual_plan,
                "schedule": {
                    "days": workout_days,
                    "times": workout_times
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context and mark step 2 complete, advance to step 3
            try:
                from sqlalchemy import select, update
                from app.models.onboarding import OnboardingState
                
                # Fetch existing state to manually deep merge to avoid JSONB op(||) wipeout
                stmt_select = select(OnboardingState).where(OnboardingState.user_id == agent_instance._current_user_id)
                result = await agent_instance.db.execute(stmt_select)
                state = result.scalars().first()
                if not state:
                    return {"status": "error", "message": "Onboarding state not found"}
                    
                agent_context = state.agent_context or {}
                existing_workout_planning = agent_context.get("workout_planning", {})
                
                # Safely merge
                if isinstance(existing_workout_planning, dict):
                    merged_workout_planning = {**existing_workout_planning, **workout_data}
                else:
                    merged_workout_planning = workout_data
                    
                agent_context["workout_planning"] = merged_workout_planning
                
                # Update onboarding state with new data
                stmt = (
                    update(OnboardingState)
                    .where(OnboardingState.user_id == agent_instance._current_user_id)
                    .values(
                        agent_context=agent_context,
                        step_2_complete=True,
                        current_step=3,
                        current_agent="diet_planning"
                    )
                )
                await agent_instance.db.execute(stmt)
                await agent_instance.db.commit()
                
                logger.info(f"Workout plan and schedule saved successfully for user {agent_instance._current_user_id}")
                return {
                    "status": "success",
                    "message": "Workout plan and schedule saved successfully. Moving to diet planning."
                }
            except Exception as e:
                logger.error(
                    f"Error saving workout plan for user {agent_instance._current_user_id}: {e}",
                    exc_info=True
                )
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
                logger.info(
                    f"Modifying workout plan for user {agent_instance._current_user_id}: "
                    f"modifications={modifications}"
                )
                
                # Apply modifications
                modified_plan = await agent_instance.workout_generator.modify_plan(
                    current_plan=current_plan,
                    modifications=modifications
                )
                
                # Store for potential further modifications
                agent_instance.current_plan = modified_plan
                
                return modified_plan.dict()
                
            except ValueError as e:
                logger.warning(f"Validation error modifying workout plan: {e}")
                return {
                    "error": str(e),
                    "message": "Invalid modifications requested"
                }
            except Exception as e:
                logger.error(f"Error modifying workout plan: {e}", exc_info=True)
                return {
                    "error": "modification_failed",
                    "message": "Failed to modify workout plan. Please try again."
                }
        
        return [generate_workout_plan, save_workout_plan, modify_workout_plan]
    
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
        # Store user_id for tool access
        self._current_user_id = user_id
        
        # Build chat history from context
        from langchain_core.messages import HumanMessage, AIMessage
        chat_history = []
        for msg in self.context.conversation_history[-15:]:
            try:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            except (KeyError, TypeError):
                continue
        
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
        
        # Execute agent with actual conversation history
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": chat_history
        })
        
        # Check if step is complete
        step_complete = await self._check_if_complete(user_id)
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action="advance_step" if step_complete else "continue_conversation"
        )
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if workout planning step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains workout_planning data with user_approved=True
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id,
            OnboardingState.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            workout_data = state.agent_context.get("workout_planning", {})
            return workout_data.get("user_approved", False) is True
        
        return False
    
    async def stream_response(self, message: str, conversation_history: list = None):
        """
        Stream response chunks for real-time display with tool calling support.
        
        Uses structured state tracking to avoid asking repetitive questions.
        Extracts information from conversation history before generating response.
        
        Args:
            message: User's message text
            conversation_history: Optional list of conversation history messages
            
        Yields:
            str: Response chunks as they are generated
        """
        from uuid import UUID
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import HumanMessage, AIMessage
        
        # If conversation history is provided, create a new context with it
        if conversation_history is not None:
            from app.agents.context import OnboardingAgentContext
            self.context = OnboardingAgentContext(
                user_id=self.context.user_id,
                conversation_history=conversation_history,
                agent_context=self.context.agent_context,
                loaded_at=self.context.loaded_at
            )
        
        # STRUCTURED STATE TRACKING: Extract information from conversation
        collected_info = self.get_collected_info(self.context.user_id)
        
        # Define required fields for workout planning
        required_fields = {
            "location": "workout location - must be either 'home' or 'gym'",
            "equipment": "available equipment as a list (e.g., ['dumbbells', 'barbell', 'machines'] or ['bodyweight'])",
            "preferred_time": "preferred time of day to work out (e.g., 'morning' or 'evening')"
        }
        
        # Extract info from conversation if not already collected
        if not collected_info or any(field not in collected_info for field in required_fields.keys()):
            logger.info(f"Extracting workout preferences from conversation for user {self.context.user_id}")
            extracted = await self.extract_info_from_conversation(
                conversation_history or [],
                required_fields
            )
            
            # Merge extracted info with existing collected info
            collected_info = {**collected_info, **{k: v for k, v in extracted.items() if v is not None}}
            
            # Save extracted info to context immediately
            if any(v is not None for v in extracted.values()):
                await self.save_context(UUID(self.context.user_id), collected_info)
                logger.info(f"Saved extracted workout preferences: {extracted}")
        
        # Check what information is still missing
        missing_fields = [field for field in required_fields.keys() 
                         if field not in collected_info or collected_info[field] is None]
        
        logger.info(
            f"Workout planning state check",
            extra={
                "user_id": self.context.user_id,
                "collected_info": collected_info,
                "missing_fields": missing_fields
            }
        )
        
        # Store user_id for tool access
        self._current_user_id = UUID(self.context.user_id)
        
        # Build chat history from context
        chat_history = []
        for msg in self.context.conversation_history[-15:]:
            try:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            except (KeyError, TypeError):
                continue
        
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
        
        # Stream response using agent executor
        async for event in agent_executor.astream_events(
            {"input": message, "chat_history": chat_history},
            version="v1"
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    
    def _get_agent_system_prompt(self) -> str:
        """
        Get system prompt for workout planning agent with context from previous steps.
        
        Returns:
            System prompt including fitness level, primary goal, and limitations
        """
        # Get context from previous agents (updated for 4-step flow)
        fitness_data = self.context.agent_context.get("fitness_assessment", {})
        fitness_level = fitness_data.get("fitness_level", "unknown")
        primary_goal = fitness_data.get("primary_goal", "unknown")
        limitations = fitness_data.get("limitations", [])
        weight_kg = fitness_data.get("weight_kg", "unknown")
        height_cm = fitness_data.get("height_cm", "unknown")
        age = fitness_data.get("age", "unknown")
        gender = fitness_data.get("gender", "unknown")
        
        # Debug logging
        logger.info(
            f"Workout Planning Agent - Loading context",
            extra={
                "agent_context_keys": list(self.context.agent_context.keys()),
                "fitness_level": fitness_level,
                "primary_goal": primary_goal,
                "weight_kg": weight_kg,
                "full_agent_context": self.context.agent_context
            }
        )
        
        limitations_str = ", ".join(limitations) if limitations else "none mentioned"
        
        # Get collected workout preferences
        collected_info = self.get_collected_info(self.context.user_id)
        location = collected_info.get("location", "not provided")
        equipment = collected_info.get("equipment", "not provided")
        preferred_time = collected_info.get("preferred_time", "not provided")
        
        return f"""You are a serious, professional Workout Planning Coach creating highly personalized, evidence-based workout plans. Do not act like a basic assistant—act like a top-tier athletic trainer.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal (User's words): {primary_goal}
- Limitations: {limitations_str}
- Weight: {weight_kg} kg
- Height: {height_cm} cm
- Age: {age}
- Gender: {gender}

Already collected workout preferences:
- Location: {location}
- Equipment: {equipment}
- Preferred Time of Day: {preferred_time}

IMPORTANT INSTRUCTIONS:
1. FIRST: Review the conversation history carefully before asking any questions.
2. DO NOT ask the user for their preferred workout frequency or schedule constraints (e.g., "how many days a week?"). YOU are the coach. It is your job to use the `research` tool to determine the optimal workout frequency (days/week) and session duration based on their goal and fitness level.
3. Review the "Already collected workout preferences" above.
4. Ask the user for their preferred `location` (home/gym) and `preferred_time` of day (e.g., morning or evening).
5. EQUIPMENT RULE: If the user says they train at a **gym**, DO NOT ask about available equipment — assume all standard gym equipment is available (barbells, dumbbells, machines, cables, cardio equipment, etc.). Only ask about specific equipment if the user chooses **home** workouts.
6. Build on information already provided rather than repeating questions.
7. BEFORE generating a workout plan, YOU MUST use the `research` tool to find the optimal, scientifically-backed training frequency and programming for the user's specific fitness level and goal.
8. Once you have location (and equipment if home) and preferred time, call the `generate_workout_plan` tool. Provide the optimal frequency and duration you determined from your research. For gym users, set equipment to all standard gym equipment.
9. IMPORTANT: AFTER the `generate_workout_plan` tool returns the JSON data, you MUST write a detailed message explaining your professional recommendation. Explain the plan, the optimal frequency you chose, and the training split in clear markdown format.
10. Present the recommended schedule (e.g., "M/W/F at 7:00 AM" if they chose morning) alongside the plan. Do NOT ask them to pick days and times—give them your prescribed schedule based on their preferred time of day (e.g., 07:00 for morning, 18:00 for evening).
11. Ask for their approval on this comprehensive plan.
12. After approval, call `save_workout_plan` with the plan_data, your determined `workout_days`, your determined `workout_times`, and `user_approved=True`.

Your role (Step 2 - Workout Planning):
- Research and determine the optimal training frequency and session duration.
- Ask the user ONLY for: location (home/gym) and preferred time of day.
- If gym: assume full equipment access. If home: ask what equipment they have.
- Generate the complete plan using the `generate_workout_plan` tool.
- Present the plan and prescribed schedule clearly as an expert recommendation.
- Handle modification requests (e.g., if they push back on a prescribed 5-day frequency, adapt it).
- Get user approval.
- Call `save_workout_plan` to persist the plan and schedule.

Workflow:
1. Collect missing preferences (location, preferred time of day; equipment ONLY if home workout).
2. Look up optimal frequency and programming via `research`.
3. Generate the plan using the `generate_workout_plan` tool.
4. Present the plan clearly with your expert rationale. Detail the prescribed days and times.
5. If the user requests changes, use the `modify_workout_plan` tool to adjust.
6. Get explicit approval from the user.
7. Call `save_workout_plan` with the full plan and schedule.

Guidelines:
- Act like an expert coach. Be confident in your prescriptions.
- Be concise—ask 1-2 questions at a time for your missing fields ONLY.
- Tell them WHY you chose this structure (training split, frequency, exercises) based on your research and their variables.
- After presenting the prescribed plan and schedule, ask: "Are you ready to commit to this workout plan?"

Approval Detection:
- User says "yes", "looks good", "perfect", "I approve", "let's do it" → Call `save_workout_plan`.
- User says "sounds great", "that works", "I'm happy with this" → Call `save_workout_plan`.
- User asks questions → Answer questions, don't save yet.
- User requests changes → Call `modify_workout_plan` with requested changes.

Realistic Recommendations by Fitness Level (To Guide Your Research):
- Beginner ({fitness_level == 'beginner'}): 2-4 days/week, full body or upper/lower split, 45-60 min sessions
- Intermediate ({fitness_level == 'intermediate'}): 3-5 days/week, push/pull/legs or upper/lower, 60-75 min sessions
- Advanced ({fitness_level == 'advanced'}): 4-6 days/week, body part splits or specialized programs, 60-90 min sessions

Goal-Specific Guidance (To Guide Your Research):
- Muscle Gain: Focus on progressive overload, 8-12 rep range, compound movements
- Fat Loss: Mix of resistance training and cardio, circuit training options, higher volume
- General Fitness: Balanced approach with strength, cardio, and flexibility

After Saving:
- Confirm the plan and schedule are saved.
- Let the user know we'll move to diet planning next: "Now let's create your meal plan to fuel these workouts."
"""

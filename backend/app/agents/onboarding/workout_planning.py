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
    
    def get_tools(self) -> List:
        """
        Get workout planning specific tools.
        
        Returns:
            List containing generate_workout_plan, save_workout_plan, and modify_workout_plan tools
        """
        from pydantic import BaseModel, Field
        
        # Capture self reference for use in tools
        agent_instance = self
        
        # Define Pydantic schema for tool arguments
        class WorkoutPlanInput(BaseModel):
            """Input schema for workout plan generation."""
            frequency: int = Field(
                description="Workout days per week (2-7)"
            )
            location: str = Field(
                description="Workout location: home or gym"
            )
            duration_minutes: int = Field(
                description="Session duration in minutes (20-180)"
            )
            equipment: List[str] = Field(
                description="List of available equipment (e.g., dumbbells, barbell, resistance bands)"
            )
        
        @tool(args_schema=WorkoutPlanInput)
        async def generate_workout_plan(
            frequency: int,
            location: str,
            duration_minutes: int,
            equipment: List[str]
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
                fitness_level = agent_instance.context.get("fitness_assessment", {}).get("fitness_level", "beginner")
                primary_goal = agent_instance.context.get("goal_setting", {}).get("primary_goal", "general_fitness")
                limitations = agent_instance.context.get("fitness_assessment", {}).get("limitations", [])
                
                logger.info(
                    f"Generating workout plan for user {agent_instance._current_user_id}: "
                    f"level={fitness_level}, goal={primary_goal}, frequency={frequency}"
                )
                
                # Generate plan
                plan = await agent_instance.workout_generator.generate_plan(
                    fitness_level=fitness_level,
                    primary_goal=primary_goal,
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
                logger.warning("Attempted to save workout plan without user approval")
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
                await agent_instance.save_context(
                    agent_instance._current_user_id,
                    workout_data
                )
                logger.info(f"Workout plan saved successfully for user {agent_instance._current_user_id}")
                return {
                    "status": "success",
                    "message": "Workout plan saved successfully"
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
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # Conversation history is included via _build_messages in stream_response
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
            OnboardingState.user_id == user_id
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
            "frequency": "number of workout days per week (integer between 3-6)",
            "duration_minutes": "workout session duration in minutes (integer between 30-120)"
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
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for workout planning agent with context from previous steps.
        
        Returns:
            System prompt including fitness level, primary goal, and limitations
        """
        # Get context from previous agents
        fitness_level = self.context.agent_context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        primary_goal = self.context.agent_context.get("goal_setting", {}).get("primary_goal", "unknown")
        limitations = self.context.agent_context.get("fitness_assessment", {}).get("limitations", [])
        
        # Debug logging
        logger.info(
            f"Workout Planning Agent - Loading context",
            extra={
                "agent_context_keys": list(self.context.agent_context.keys()),
                "fitness_level": fitness_level,
                "primary_goal": primary_goal,
                "full_agent_context": self.context.agent_context
            }
        )
        
        limitations_str = ", ".join(limitations) if limitations else "none mentioned"
        
        # Get collected workout preferences
        collected_info = self.get_collected_info(self.context.user_id)
        location = collected_info.get("location", "not provided")
        equipment = collected_info.get("equipment", "not provided")
        frequency = collected_info.get("frequency", "not provided")
        duration = collected_info.get("duration_minutes", "not provided")
        
        return f"""You are a Workout Planning Agent creating personalized workout plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Limitations: {limitations_str}

Already collected workout preferences:
- Location: {location}
- Equipment: {equipment}
- Frequency: {frequency} days/week
- Duration: {duration} minutes/session

IMPORTANT INSTRUCTIONS:
1. Review the "Already collected workout preferences" above
2. ONLY ask for information that shows "not provided"
3. NEVER ask for information that has already been collected
4. Once ALL preferences are collected, call generate_workout_plan tool
5. After presenting a plan, wait for user approval before calling save_workout_plan

Your role:
- Ask ONLY for missing workout preferences
- Generate a workout plan when all preferences are available
- Present the plan with clear explanation
- Detect approval intent from user responses
- Handle modification requests
- Save plan ONLY after user explicitly approves

Guidelines:
- Be concise - ask 1-2 questions at a time for missing information only
- Once you have location, equipment, frequency, and duration, generate the plan
- After generating, present it clearly and wait for approval
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

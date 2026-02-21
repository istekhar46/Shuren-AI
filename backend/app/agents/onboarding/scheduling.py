"""
Scheduling Agent for onboarding.

This agent handles step 4 of the onboarding process, setting up hydration
reminders and collecting supplement preferences (informational only).
"""

import logging
from typing import List
from uuid import UUID

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select

from app.agents.onboarding.base import BaseOnboardingAgent
from app.agents.tools.scheduling_tools import create_scheduling_tools
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import AgentResponse

logger = logging.getLogger(__name__)


class SchedulingAgent(BaseOnboardingAgent):
    """
    Agent for setting hydration and supplement preferences (Step 4).
    
    This agent helps users establish healthy habits by:
    - Configuring hydration reminder preferences
    - Collecting supplement interest and current usage (informational only)
    
    Note: Workout and meal schedules are now collected in Steps 2 and 3
    by WorkoutPlanningAgent and DietPlanningAgent respectively.
    
    The agent provides education about supplements but does NOT prescribe
    or recommend specific supplements - that's outside our scope.
    """
    
    agent_type = "scheduling"
    
    def get_tools(self) -> List:
        """
        Get scheduling-specific tools.
        
        Returns:
            List containing save_hydration_preferences and 
            save_supplement_preferences tools
        """
        # Tools are created with db and user_id bound
        # They will be bound in process_message when user_id is available
        return []
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for scheduling with context from previous agents.
        
        Returns:
            System prompt for hydration and supplement preferences
        """
        # Extract workout plan context
        workout_plan = self.context.agent_context.get("workout_planning", {}).get("plan", {})
        workout_frequency = workout_plan.get("frequency", "unknown")
        
        # Extract meal plan context
        meal_plan = self.context.agent_context.get("diet_planning", {}).get("plan", {})
        meal_frequency = meal_plan.get("meal_frequency", "unknown")
        daily_calories = meal_plan.get("daily_calories", "unknown")
        
        # Extract fitness level for context
        fitness_level = self.context.agent_context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        
        # Get collected scheduling information
        collected_info = self.get_collected_info(self.context.user_id)
        water_reminders = collected_info.get("water_reminder_frequency", "not provided")
        water_target = collected_info.get("water_target_ml", "not provided")
        supplement_interest = collected_info.get("supplement_interest", "not provided")
        
        return f"""You are a Scheduling Agent helping users establish healthy hydration habits and understand supplement basics.

Context from previous steps:
- Fitness Level: {fitness_level}
- Workout Plan: {workout_frequency} days per week
- Meal Plan: {meal_frequency} meals per day, {daily_calories} calories
- Note: Workout and meal schedules were already collected in previous steps

Already collected preferences:
- Water Reminders: {water_reminders}
- Water Target: {water_target}
- Supplement Interest: {supplement_interest}

IMPORTANT INSTRUCTIONS:
1. FIRST: Review the conversation history carefully before asking any questions
2. DO NOT ask questions that the user has already answered in previous messages
3. Review the "Already collected preferences" above
4. ONLY ask for information that shows "not provided" AND hasn't been mentioned in conversation
5. Build on information already provided rather than repeating questions
6. Once all info is collected, save the preferences

Your role (Step 4 - Final Step):
1. Configure hydration reminders - Ask about water intake goals and reminder frequency
2. Collect supplement information - Ask if interested in learning about supplements and what they currently take (informational only)

Guidelines for Hydration:
- Ask about their daily water intake goal (suggest 2-3 liters based on activity level)
- Ask how often they want reminders (every 1-4 hours)
- Explain importance of hydration for fitness and recovery
- Suggest more frequent reminders on workout days
- When you have frequency and target, call save_hydration_preferences tool

Guidelines for Supplements:
- Ask if they're interested in learning about supplements for their fitness goals
- Ask what supplements they currently take (if any)
- Emphasize this is INFORMATIONAL ONLY - we don't prescribe or recommend specific supplements
- Explain common supplements (protein, creatine, etc.) but don't make recommendations
- When you have their interest level and current supplements, call save_supplement_preferences tool
- This tool will mark step_4_complete=True and complete onboarding

Conversation Flow:
1. Start by explaining this is the final step - setting up hydration and supplement preferences
2. Begin with hydration preferences (target and reminder frequency)
3. Move to supplement information once hydration is saved
4. After both are saved, confirm onboarding is complete and they're ready to start their fitness journey

Tone:
- Practical and educational
- Supportive and encouraging
- Clear that supplement info is educational, not prescriptive
- Celebratory when completing onboarding

Important:
- Call save_hydration_preferences when you have complete hydration info
- Call save_supplement_preferences when you have supplement info (this completes onboarding)
- After save_supplement_preferences is called, congratulate them on completing onboarding
- Do NOT ask about workout or meal schedules - those were collected in previous steps"""
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about scheduling preferences.
        
        Uses LangChain's tool-calling agent to:
        1. Understand user's schedule preferences from natural language
        2. Reference workout and meal plans from previous agent context
        3. Suggest optimal timing based on their plans
        4. Call save tools when information is complete
        5. Set step_complete=True when all schedules are saved
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Store user_id for tool access
        self._current_user_id = user_id
        
        # Create tools with db and user_id bound
        tools = create_scheduling_tools(self.db, user_id)
        
        # Build prompt with context
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # Conversation history is included via _build_messages in stream_response
        })
        
        # Check if step is complete (all three schedules saved)
        step_complete = await self._check_if_complete(user_id)
        
        # If complete, set next action to complete onboarding
        next_action = "complete_onboarding" if step_complete else "continue_conversation"
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action=next_action
        )
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if scheduling step is complete.
        
        Scheduling is complete when both preferences are saved:
        - hydration (hydration preferences)
        - supplements (supplement preferences)
        
        Note: step_4_complete flag is set by save_supplement_preferences tool.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if both hydration and supplements are saved in agent_context
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if not state:
            return False
        
        # Check step_4_complete flag (set by save_supplement_preferences)
        return state.step_4_complete or False
    
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
        
        # Store user_id for tool access
        self._current_user_id = UUID(self.context.user_id)
        
        # STRUCTURED STATE TRACKING: Extract information from conversation
        collected_info = self.get_collected_info(self.context.user_id)
        
        # Define required fields for scheduling
        required_fields = {
            "water_reminder_frequency": "how often to remind about water (e.g., 'hourly', 'every 2 hours')",
            "water_target_ml": "daily water intake goal in milliliters (e.g., 2000, 3000)",
            "supplement_interest": "whether interested in learning about supplements (yes/no)",
            "current_supplements": "list of supplements currently taking (optional)"
        }
        
        # Extract info from conversation if not already collected
        if not collected_info or "hydration" not in collected_info:
            logger.info(f"Extracting hydration and supplement preferences from conversation for user {self.context.user_id}")
            extracted = await self.extract_info_from_conversation(
                conversation_history or [],
                required_fields
            )
            
            # Merge extracted info with existing collected info
            collected_info = {**collected_info, **{k: v for k, v in extracted.items() if v is not None}}
            
            # Save extracted info to context immediately
            if any(v is not None for v in extracted.values()):
                await self.save_context(UUID(self.context.user_id), collected_info)
                logger.info(f"Saved extracted hydration and supplement preferences: {extracted}")
        
        logger.info(
            f"Scheduling state check",
            extra={
                "user_id": self.context.user_id,
                "collected_info": collected_info
            }
        )
        
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
        
        # Create tools with db and user_id bound
        tools = create_scheduling_tools(self.db, self._current_user_id)
        
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
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
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

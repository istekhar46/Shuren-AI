"""
Goal Setting Agent for onboarding.

This agent handles step 3 of the onboarding process, helping users define
clear, achievable fitness goals with specific targets.
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

logger = logging.getLogger(__name__)


class GoalSettingAgent(BaseOnboardingAgent):
    """
    Agent for defining fitness goals (Step 3).
    
    This agent helps users articulate their fitness goals in a structured way:
    - Primary goal (muscle gain, fat loss, general fitness, endurance)
    - Secondary goals if applicable
    - Specific quantifiable targets (weight, body composition, performance)
    - Timeline and expectations
    
    The agent ensures goals are realistic and achievable based on the user's
    fitness level assessed in previous steps.
    """
    
    agent_type = "goal_setting"
    
    def get_tools(self) -> List:
        """
        Get goal setting specific tools.
        
        Returns:
            List containing save_fitness_goals tool
        """
        # Capture self reference for use in tool
        agent_instance = self
        
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
                await agent_instance.save_context(
                    agent_instance._current_user_id,
                    goals_data
                )
                return {
                    "status": "success",
                    "message": "Fitness goals saved successfully"
                }
            except Exception as e:
                logger.error(
                    f"Error saving fitness goals for user "
                    f"{agent_instance._current_user_id}: {e}"
                )
                return {
                    "status": "error",
                    "message": "Failed to save fitness goals. Please try again."
                }
        
        return [save_fitness_goals]
    
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
        # Store user_id for tool access
        self._current_user_id = user_id
        
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
        Check if goal setting step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains goal_setting data
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            return "goal_setting" in state.agent_context
        
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
        
        # Store user_id for tool access
        self._current_user_id = UUID(self.context.user_id)
        
        # STRUCTURED STATE TRACKING: Extract information from conversation
        collected_info = self.get_collected_info(self.context.user_id)
        
        # Define required fields for goal setting
        required_fields = {
            "primary_goal": "primary fitness goal - must be one of: fat_loss, muscle_gain, or general_fitness",
            "secondary_goal": "optional secondary fitness goal",
            "target_weight_kg": "optional target weight in kilograms (number)",
            "target_body_fat_percentage": "optional target body fat percentage (number)"
        }
        
        # Extract info from conversation if not already collected
        if not collected_info or "primary_goal" not in collected_info:
            logger.info(f"Extracting fitness goals from conversation for user {self.context.user_id}")
            extracted = await self.extract_info_from_conversation(
                conversation_history or [],
                required_fields
            )
            
            # Merge extracted info with existing collected info
            collected_info = {**collected_info, **{k: v for k, v in extracted.items() if v is not None}}
            
            # Save extracted info to context immediately
            if any(v is not None for v in extracted.values()):
                await self.save_context(UUID(self.context.user_id), collected_info)
                logger.info(f"Saved extracted fitness goals: {extracted}")
        
        # Check what information is still missing
        has_primary_goal = "primary_goal" in collected_info and collected_info["primary_goal"] is not None
        
        logger.info(
            f"Goal setting state check",
            extra={
                "user_id": self.context.user_id,
                "collected_info": collected_info,
                "has_primary_goal": has_primary_goal
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
        Get system prompt for goal setting with context from fitness assessment.
        
        Returns:
            System prompt including fitness level and limitations from previous agent
        """
        # Get fitness assessment context
        fitness_level = self.context.agent_context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        limitations = self.context.agent_context.get("fitness_assessment", {}).get("limitations", [])
        
        limitations_str = ", ".join(limitations) if limitations else "none mentioned"
        
        # Get collected goal information
        collected_info = self.get_collected_info(self.context.user_id)
        primary_goal = collected_info.get("primary_goal", "not provided")
        secondary_goal = collected_info.get("secondary_goal", "not provided")
        target_weight = collected_info.get("target_weight_kg", "not provided")
        target_bf = collected_info.get("target_body_fat_percentage", "not provided")
        
        return f"""You are a Goal Setting Agent helping users define their fitness objectives.

Context from previous steps:
- Fitness Level: {fitness_level}
- Limitations: {limitations_str}

Already collected goal information:
- Primary Goal: {primary_goal}
- Secondary Goal: {secondary_goal}
- Target Weight: {target_weight} kg
- Target Body Fat: {target_bf}%

IMPORTANT INSTRUCTIONS:
1. Review the "Already collected goal information" above
2. ONLY ask for information that shows "not provided"
3. NEVER ask for information that has already been collected
4. Primary goal is REQUIRED - if not provided, ask for it
5. Secondary goal and targets are OPTIONAL - don't require them
6. Once primary goal is confirmed, call save_fitness_goals tool

Your role:
- Ask ONLY for missing required information (primary goal)
- Understand their fitness objectives
- Set realistic expectations based on their {fitness_level} fitness level
- Explain how the system will help achieve these goals

Guidelines:
- Be realistic but encouraging
- Explain what each goal means
- Help prioritize if they have multiple goals
- Reference their fitness level when setting expectations
- Ask about optional target metrics (weight, body fat %) but don't require them
- When you have primary goal and user confirms, call save_fitness_goals tool
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

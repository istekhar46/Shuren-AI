"""
Fitness Assessment Agent for onboarding.

This agent handles steps 0-2 of the onboarding process, assessing the user's
current fitness level, exercise experience, and physical limitations.
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


class FitnessAssessmentAgent(BaseOnboardingAgent):
    """
    Agent for assessing user's fitness level (Steps 0-2).
    
    This agent conducts a conversational assessment to determine:
    - Current fitness level (beginner/intermediate/advanced)
    - Exercise experience and history
    - Physical limitations (equipment, injuries - non-medical)
    - Exercise preferences and constraints
    
    The agent uses a friendly, encouraging tone and avoids overwhelming
    users with too many questions at once.
    """
    
    agent_type = "fitness_assessment"
    
    def get_tools(self) -> List:
        """
        Get fitness assessment specific tools.
        
        Returns:
            List containing save_fitness_assessment tool
        """
        from pydantic import BaseModel, Field
        
        # Capture self reference for use in tool
        agent_instance = self
        
        # Define Pydantic schema for tool arguments
        class FitnessAssessmentInput(BaseModel):
            """Input schema for fitness assessment data."""
            fitness_level: str = Field(
                description="User's fitness level: beginner, intermediate, or advanced"
            )
            experience_details: dict = Field(
                description="Dict with keys: frequency, duration, types of exercise"
            )
            limitations: List[str] = Field(
                description="List of physical limitations (equipment, injuries - non-medical)"
            )
        
        @tool(args_schema=FitnessAssessmentInput)
        async def save_fitness_assessment(
            fitness_level: str,
            experience_details: dict,
            limitations: List[str]
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
                await agent_instance.save_context(
                    agent_instance._current_user_id,
                    assessment_data
                )
                return {
                    "status": "success",
                    "message": "Fitness assessment saved successfully"
                }
            except Exception as e:
                logger.error(
                    f"Error saving fitness assessment for user "
                    f"{agent_instance._current_user_id}: {e}"
                )
                return {
                    "status": "error",
                    "message": "Failed to save fitness assessment. Please try again."
                }
        
        return [save_fitness_assessment]
    
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
        # Store user_id for tool access
        self._current_user_id = user_id
        
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
        Check if fitness assessment step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains fitness_assessment data
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            return "fitness_assessment" in state.agent_context
        
        return False
    
    async def stream_response(self, message: str, conversation_history: list = None):
        """
        Stream response chunks for real-time display with tool calling support.
        
        Uses LangChain's agent executor with streaming to yield response chunks
        as they are generated while also executing tools when needed.
        
        Args:
            message: User's message text
            conversation_history: Optional list of conversation history messages
            
        Yields:
            str: Response chunks as they are generated
        """
        from uuid import UUID
        
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
        # This allows tools to be called during streaming
        async for event in agent_executor.astream_events(
            {"input": message, "chat_history": chat_history},
            version="v1"
        ):
            kind = event["event"]
            
            # Stream LLM tokens as they're generated
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for fitness assessment.
        
        Defines the agent's role, behavior, and guidelines for conducting
        fitness assessments in a conversational manner.
        
        Returns:
            System prompt string for fitness assessment agent
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

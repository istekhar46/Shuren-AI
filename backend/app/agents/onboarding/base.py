"""
Base agent class for onboarding-specific AI agents.

This module provides the abstract base class for all onboarding agents,
ensuring consistent behavior and interface across the onboarding flow.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
from uuid import UUID
import logging
import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.agents.context import OnboardingAgentContext
from app.core.config import settings
from app.schemas.onboarding import AgentResponse

logger = logging.getLogger(__name__)


class BaseOnboardingAgent(ABC):
    """
    Abstract base class for all onboarding agents.
    
    Provides common functionality for LLM integration, context management,
    and database operations. All specialized onboarding agents must extend
    this class and implement the abstract methods.
    
    Attributes:
        db: Async database session for database operations
        context: OnboardingAgentContext with conversation history and agent state
        llm: LLM instance (ChatAnthropic, ChatOpenAI, or ChatGoogleGenerativeAI)
        agent_type: String identifier for this agent type
    """
    
    # Subclasses must define their agent_type
    agent_type: str = None
    
    def __init__(self, db: AsyncSession, context: OnboardingAgentContext):
        """
        Initialize agent with database session and context.
        
        Args:
            db: Async database session for database operations
            context: OnboardingAgentContext with conversation history and agent state
        """
        self.db = db
        self.context = context
        self.llm = self._init_llm()
    
    def _init_llm(self):
        """
        Initialize the LLM for this agent based on configured provider.
        
        Uses the LLM provider specified in settings (Anthropic, OpenAI, or Google)
        with configuration optimized for conversational onboarding interactions.
        
        Returns:
            LLM instance (ChatAnthropic, ChatOpenAI, or ChatGoogleGenerativeAI)
            
        Raises:
            ValueError: If required API key is not configured for the active provider
        """
        from app.core.config import LLMProvider
        
        # Get the required API key for the configured provider
        api_key = settings.get_required_llm_api_key()
        
        # Initialize the appropriate LLM based on provider
        if settings.LLM_PROVIDER == LLMProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=settings.LLM_MODEL,
                anthropic_api_key=api_key,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif settings.LLM_PROVIDER == LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=api_key,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif settings.LLM_PROVIDER == LLMProvider.GOOGLE:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    
    def _build_messages(self, message: str) -> List:
        """
        Build message chain for LLM including system prompt, history, and current query.
        
        This method constructs the complete message list for the LLM by combining:
        1. System prompt (defines agent role and behavior)
        2. Conversation history (last 15 messages for context)
        3. Current user message
        
        Args:
            message: Current user message
            
        Returns:
            List of LangChain messages (SystemMessage, HumanMessage, AIMessage)
        """
        messages = [SystemMessage(content=self.get_system_prompt())]
        
        # Add conversation history (limit to last 15 messages to prevent token overflow)
        for msg in self.context.conversation_history[-15:]:
            try:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            except (KeyError, TypeError) as e:
                logger.warning(f"Skipping malformed message in conversation history: {e}")
                continue
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        return messages
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message and return agent response.
        
        This method must be implemented by all specialized agents to handle
        user messages specific to their domain (fitness assessment, goal setting, etc.).
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        pass
    
    @abstractmethod
    async def stream_response(self, message: str):
        """
        Stream response chunks for real-time display.
        
        This method enables streaming responses for better user experience,
        allowing the UI to display text as it's generated rather than waiting
        for the complete response.
        
        Args:
            message: User's message text
            
        Yields:
            str: Response chunks as they are generated
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """
        Get agent-specific tools for LLM function calling.
        
        Each specialized agent defines its own set of tools for interacting
        with the database and performing domain-specific operations.
        
        Returns:
            List of LangChain tools available to this agent
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Each specialized agent defines its own system prompt that includes
        domain expertise, role definition, and behavioral guidelines.
        
        Returns:
            System prompt string defining agent role and behavior
        """
        pass
    
    def get_collected_info(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get information already collected by this agent from agent_context.
        
        This allows the agent to check what information has already been
        gathered without re-asking the user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary of collected information for this agent, or empty dict
        """
        return self.context.agent_context.get(self.agent_type, {})
    
    def has_required_info(self, required_fields: List[str]) -> tuple[bool, List[str]]:
        """
        Check if all required information has been collected.
        
        Args:
            required_fields: List of field names that are required
            
        Returns:
            Tuple of (all_present, missing_fields)
        """
        collected = self.get_collected_info(self.context.user_id)
        missing = [field for field in required_fields if field not in collected or collected[field] is None]
        return (len(missing) == 0, missing)
    
    async def extract_info_from_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        fields_to_extract: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract structured information from conversation history.
        
        This method analyzes the conversation and extracts specific pieces of
        information that the user has provided, returning them in structured format.
        
        Args:
            conversation_history: List of conversation messages
            fields_to_extract: Dict mapping field names to descriptions
                Example: {"location": "workout location (home/gym)", "frequency": "days per week"}
                
        Returns:
            Dictionary with extracted information (None for fields not found)
        """
        if not conversation_history:
            return {field: None for field in fields_to_extract.keys()}
        
        # Build extraction prompt
        fields_desc = "\n".join([f"- {field}: {desc}" for field, desc in fields_to_extract.items()])
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-10:]])
        
        extraction_prompt = f"""Analyze this conversation and extract the following information if the user has provided it.
Return ONLY a valid JSON object with the field names as keys. Use null for any information not found.

Fields to extract:
{fields_desc}

Conversation:
{conversation_text}

Return format (JSON only, no other text):
{json.dumps({field: None for field in fields_to_extract.keys()}, indent=2)}"""
        
        try:
            messages = [HumanMessage(content=extraction_prompt)]
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            content = response.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            extracted = json.loads(content)
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract info from conversation: {e}")
            return {field: None for field in fields_to_extract.keys()}
    
    async def save_context(self, user_id: UUID, agent_data: dict) -> None:
        """
        Save agent-specific context to OnboardingState.
        
        Updates the agent_context field in the database with data collected
        by this agent. The context is stored under this agent's type key,
        allowing subsequent agents to access the information.
        
        Args:
            user_id: UUID of the user
            agent_data: Dictionary of data to save for this agent
            
        Raises:
            ValueError: If no onboarding state exists for the user
        """
        from app.models.onboarding import OnboardingState
        
        # Load current state
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if not state:
            raise ValueError(f"No onboarding state found for user {user_id}")
        
        # Update agent_context
        agent_context = state.agent_context or {}
        agent_context[self.agent_type] = agent_data
        
        # Debug logging
        logger.info(
            f"Saving context for agent {self.agent_type}",
            extra={
                "user_id": str(user_id),
                "agent_type": self.agent_type,
                "agent_data": agent_data,
                "full_agent_context": agent_context
            }
        )
        
        # Update in database
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(agent_context=agent_context)
        )
        await self.db.execute(stmt)
        await self.db.commit()

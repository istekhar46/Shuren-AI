"""
Base agent class for onboarding-specific AI agents.

This module provides the abstract base class for all onboarding agents,
ensuring consistent behavior and interface across the onboarding flow.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from langchain_anthropic import ChatAnthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.onboarding import AgentResponse


class BaseOnboardingAgent(ABC):
    """
    Abstract base class for all onboarding agents.
    
    Provides common functionality for LLM integration, context management,
    and database operations. All specialized onboarding agents must extend
    this class and implement the abstract methods.
    
    Attributes:
        db: Async database session for database operations
        context: Agent context dictionary from OnboardingState
        llm: ChatAnthropic instance for LLM interactions
        agent_type: String identifier for this agent type
    """
    
    # Subclasses must define their agent_type
    agent_type: str = None
    
    def __init__(self, db: AsyncSession, context: dict):
        """
        Initialize agent with database session and context.
        
        Args:
            db: Async database session for database operations
            context: Agent context dictionary from OnboardingState
        """
        self.db = db
        self.context = context
        self.llm = self._init_llm()
    
    def _init_llm(self) -> ChatAnthropic:
        """
        Initialize the LLM for this agent.
        
        Uses Claude Sonnet 4.5 with configuration optimized for
        conversational onboarding interactions.
        
        Returns:
            ChatAnthropic instance configured for onboarding
            
        Raises:
            ValueError: If ANTHROPIC_API_KEY is not configured
        """
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. "
                "Please set it in your environment or .env file."
            )
        
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.7,
            max_tokens=2048
        )
    
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
        
        # Update in database
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(agent_context=agent_context)
        )
        await self.db.execute(stmt)
        await self.db.commit()

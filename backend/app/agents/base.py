"""
Base agent class for all specialized AI agents in the Shuren system.

This module provides the abstract base class that all specialized agents extend,
ensuring consistent LLM integration, message handling, and interface across agents.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import AgentContext, AgentResponse
from app.core.config import settings


class BaseAgent(ABC):
    """
    Abstract base class for all specialized AI agents.
    
    This class provides common functionality for LLM integration, message building,
    and conversation history management. All specialized agents (Workout Planning,
    Diet Planning, etc.) must extend this class and implement the abstract methods.
    
    Attributes:
        context: Immutable AgentContext containing all user data
        db_session: Optional async database session for agent operations
    """
    
    def __init__(
        self,
        context: AgentContext,
        db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize the base agent with context and database session.
        
        Args:
            context: AgentContext containing user data and state
            db_session: Optional async database session for database operations
        """
        self.context = context
        self.db_session = db_session
        self.llm = self._init_llm()
    
    def _init_llm(self):
        """
        Initialize the LLM based on the configured provider.
        
        Supports multiple LLM providers (Anthropic, OpenAI, Google) based on
        the LLM_PROVIDER configuration setting. Each provider is initialized
        with the appropriate API key and model parameters.
        
        Returns:
            LangChain chat model instance (ChatAnthropic, ChatOpenAI, or ChatGoogleGenerativeAI)
            
        Raises:
            ValueError: If the configured LLM provider is not supported
        """
        provider = settings.LLM_PROVIDER
        
        if provider == "anthropic":
            return ChatAnthropic(
                model=settings.LLM_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS
            )
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers are: anthropic, openai, google"
            )
    
    def _init_classifier_llm(self):
        """
        Initialize a fast classifier LLM for query routing.
        
        Uses the configured classifier model (defaults to Claude Haiku) for fast,
        low-latency query classification. This LLM is optimized for quick routing
        decisions with minimal tokens and low temperature for consistent results.
        
        The classifier model is configurable via CLASSIFIER_MODEL setting, allowing
        flexibility to use different models based on performance and cost requirements.
        
        Returns:
            ChatAnthropic: Classifier model configured for fast query routing
        """
        return ChatAnthropic(
            model=settings.CLASSIFIER_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.CLASSIFIER_TEMPERATURE,
            max_tokens=10
        )
    
    def _format_chat_history(self) -> List:
        """
        Convert conversation history to LangChain messages.
        
        Transforms the conversation history from the AgentContext into a list
        of LangChain message objects (HumanMessage and AIMessage). This method
        limits the history to the last 10 messages to prevent context overflow
        and maintain reasonable token usage.
        
        The conversation history format in AgentContext is:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
        
        Returns:
            List: List of LangChain messages (HumanMessage and AIMessage) from history,
                  limited to last 10 messages
        """
        messages = []
        
        # Limit to last 10 messages to prevent context overflow
        for msg in self.context.conversation_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def _build_messages(self, query: str, voice_mode: bool = False) -> List:
        """
        Build message chain for LLM including system prompt, history, and current query.
        
        Constructs a list of LangChain messages that includes:
        1. System prompt (from _system_prompt method)
        2. Conversation history (limited based on mode)
        3. Current user query
        
        The conversation history is limited to prevent context overflow:
        - Voice mode: Last 5 messages (for low-latency responses)
        - Text mode: Last 10 messages (for richer context)
        
        Args:
            query: Current user query to process
            voice_mode: Whether this is a voice interaction (affects history limit)
            
        Returns:
            List: List of LangChain messages (SystemMessage, HumanMessage, AIMessage)
        """
        messages = [
            SystemMessage(content=self._system_prompt(voice_mode))
        ]
        
        # Add conversation history (limited for voice)
        history_limit = 5 if voice_mode else 10
        for msg in self.context.conversation_history[-history_limit:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        return messages
    
    @abstractmethod
    async def process_text(self, query: str) -> AgentResponse:
        """
        Process a text query and return a detailed response.
        
        This method is used for text-based interactions where full context
        and detailed responses are appropriate.
        
        Args:
            query: User's text query
            
        Returns:
            AgentResponse with content, agent type, tools used, and metadata
        """
        pass
    
    @abstractmethod
    async def process_voice(self, query: str) -> str:
        """
        Process a voice query and return a concise response.
        
        This method is optimized for voice interactions where responses
        should be brief and conversational. Returns plain string instead
        of AgentResponse for simplicity.
        
        Args:
            query: User's voice query (transcribed to text)
            
        Returns:
            str: Concise response text suitable for text-to-speech
        """
        pass
    
    @abstractmethod
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """
        Stream response chunks for real-time display.
        
        This method enables streaming responses for better user experience,
        allowing the UI to display text as it's generated rather than waiting
        for the complete response.
        
        Args:
            query: User's query
            
        Yields:
            str: Response chunks as they are generated
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """
        Get the list of tools/functions available to this agent.
        
        Each specialized agent defines its own set of tools for interacting
        with the database and external services (e.g., workout plan retrieval,
        meal plan updates, etc.).
        
        Returns:
            List: List of LangChain tools available to this agent
        """
        pass
    
    @abstractmethod
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for this agent.
        
        Each specialized agent defines its own system prompt that includes
        domain expertise, user context, and behavioral guidelines. The prompt
        may vary based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction (affects prompt style)
            
        Returns:
            str: System prompt for the LLM
        """
        pass

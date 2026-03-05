"""
Base agent class for all specialized AI agents in the Shuren system.

This module provides the abstract base class that all specialized agents extend,
ensuring consistent LLM integration, message handling, and interface across agents.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Union, Dict, Any
import logging
import json

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import AgentContext, AgentResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        system_msg_content = self._system_prompt(voice_mode)
        
        # Add tool usage instructions
        system_msg_content += "\n\nAvailable Common Tools:\n"
        system_msg_content += "- get_current_datetime: Get the precise current time, date, or day of week. Use this when you need temporal context for queries like 'tomorrow'.\n"
        
        from app.core.config import settings

        if settings.TAVILY_API_KEY or settings.PPLX_API_KEY:
            system_msg_content += "- research: Search for evidence-based information using web search. Use this tool BEFORE generating workout or meal plans to ensure accuracy and research-backed results.\n"
        
        messages = [
            SystemMessage(content=system_msg_content)
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
    
    async def process_voice(self, query: str) -> str:
        """
        Process a voice query and return a concise response.
        
        This method is optimized for voice interactions where responses
        should be brief and conversational (under 75 words).
        
        Args:
            query: User's voice query (transcribed to text)
            
        Returns:
            str: Concise response text suitable for text-to-speech
        """
        # Build messages with limited history for voice mode
        messages = self._build_messages(query, voice_mode=True)
        
        # Call LLM without tools for faster response
        response = await self.llm.ainvoke(messages)
        
        # Return plain string for voice
        return response.content
    
    async def stream_response(self, query: str) -> AsyncIterator[Union[str, Dict[str, Any]]]:
        """
        Stream response chunks for real-time display, handling tools if needed.
        
        Builds messages and uses the LLM's streaming capability to yield
        response chunks as they are generated. If a tool call is detected,
        it will execute the tool and then stream the final response.
        
        Args:
            query: User's query
            
        Yields:
            Union[str, dict]: Response chunks (str) or status updates (dict)
        """
        # Build messages
        messages = self._build_messages(query, voice_mode=False)
        
        # Get tools for this agent
        tools = self.get_tools()
        llm_with_tools = self.llm.bind_tools(tools)
        
        # First pass to capture the response (might be streaming text or tool calls)
        response_message = None
        has_tool_calls = False
        
        async for chunk in llm_with_tools.astream(messages):
            # Accumulate chunk
            if response_message is None:
                response_message = chunk
            else:
                response_message += chunk
                
            # Yield content if it exists
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
                
            # Check if this chunk has tool calls
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                has_tool_calls = True
        
        # If tools were called, execute them and stream the final answer
        if has_tool_calls and hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            # We must append the full AIMessage with tool calls to history
            messages.append(response_message)
            
            from langchain_core.messages import ToolMessage
            for tool_call in response_message.tool_calls:
                # Signal the tool execution to the frontend
                yield {"status": "searching", "tool": tool_call['name'], "args": tool_call['args']}
                
                # Find and execute the tool
                tool_found = False
                for t in tools:
                    if t.name == tool_call['name']:
                        tool_found = True
                        logger.info(f"Agent executing tool: {tool_call['name']} with args: {tool_call['args']}")
                        try:
                            tool_result = await t.ainvoke(tool_call['args'])
                            logger.info(f"Tool {tool_call['name']} executed successfully")
                            messages.append(ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call['id']
                            ))
                        except Exception as e:
                            logger.error(f"Tool execution error for {tool_call['name']}: {str(e)}", exc_info=True)
                            messages.append(ToolMessage(
                                content=f"Error executing tool: {e}",
                                tool_call_id=tool_call['id']
                            ))
                
                if not tool_found:
                    messages.append(ToolMessage(
                        content=f"Tool '{tool_call['name']}' not found.",
                        tool_call_id=tool_call['id']
                    ))
                            
            # Now stream the final response based on tool results
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
    
    def get_common_tools(self) -> List:
        """
        Get the list of common tools available to all agents.
        
        Includes standard utilities like current time and optionally conditional 
        tools like the search 'research' tool if API keys are provided.
        
        Returns:
            List: List of LangChain tools available to all agents
        """
        @tool
        def get_current_datetime() -> str:
            """Get the current date, time, and day of the week.
            
            Returns:
                JSON string with the current datetime, date, day of week, and time.
            """
            from datetime import datetime
            
            now = datetime.now()
            
            # Map Python weekday() to 0=Monday, ... 6=Sunday
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_of_week_num = now.weekday()
            
            import json
            return json.dumps({
                "success": True,
                "data": {
                    "datetime": now.isoformat(),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "day_of_week": day_names[day_of_week_num],
                    "day_of_week_num": day_of_week_num
                },
                "metadata": {
                    "timestamp": now.isoformat(),
                    "source": "common_tools"
                }
            })

        tools = [get_current_datetime]

        # Conditional Business Logic for research tool
        from app.core.config import settings
        
        tavily_key = settings.TAVILY_API_KEY
        pplx_key = settings.PPLX_API_KEY

        if tavily_key or pplx_key:
            @tool
            async def research(query: str, provider: str = "auto") -> str:
                """Research a topic using web search to get evidence-based, up-to-date information.

                Use this tool BEFORE generating workout plans, meal plans, exercise recommendations,
                or nutritional advice to ensure responses are backed by current research and evidence.

                Args:
                    query: The research question (be specific for better results).
                    provider: Search provider - "tavily" for fast factual lookups,
                              "perplexity" for deep synthesized research with citations,
                              or "auto" (uses best available).

                Returns:
                    JSON string with research results including content and source citations.
                """
                # Local imports for tool execution
                import json
                from datetime import datetime
                
                # Resolve provider
                target = provider.lower()
                if target == "auto":
                    target = "tavily" if bool(tavily_key) else "perplexity"
                
                logger.info(f"Research tool invoked: query='{query}', selected_provider='{target}'")
                
                if target == "tavily":
                    if not bool(tavily_key):
                        logger.warning("Research attempt failed: Tavily API key missing")
                        return json.dumps({"success": False, "error": "Tavily provider not configured in .env"})
                    try:
                        from langchain_tavily import TavilySearch
                        from langchain_tavily.tavily_search import TavilySearchAPIWrapper
                        
                        logger.debug(f"Executing Tavily search for: {query}")
                        wrapper = TavilySearchAPIWrapper(tavily_api_key=tavily_key)
                        tavily = TavilySearch(api_wrapper=wrapper, max_results=5)
                        results = await tavily.ainvoke(query)
                        
                        result_count = len(results) if isinstance(results, list) else 1
                        logger.info(f"Tavily search successful: {result_count} results found for query='{query}'")
                        
                        return json.dumps({
                            "success": True,
                            "provider": "tavily",
                            "data": results,
                            "metadata": {"timestamp": datetime.utcnow().isoformat(), "query": query}
                        })
                    except Exception as e:
                        logger.error(f"Tavily search exception for query='{query}': {str(e)}", exc_info=True)
                        return json.dumps({"success": False, "error": f"Tavily search failed: {str(e)}"})

                elif target == "perplexity":
                    if not bool(pplx_key):
                        logger.warning("Research attempt failed: Perplexity API key missing")
                        return json.dumps({"success": False, "error": "Perplexity provider not configured in .env"})
                    try:
                        from langchain_perplexity import ChatPerplexity
                        
                        logger.debug(f"Executing Perplexity research for: {query}")
                        chat = ChatPerplexity(model="sonar", temperature=0.3, pplx_api_key=pplx_key)
                        response = await chat.ainvoke(query)
                        
                        logger.info(f"Perplexity research successful: response length={len(response.content)} for query='{query}'")
                        
                        return json.dumps({
                            "success": True,
                            "provider": "perplexity",
                            "data": {
                                "answer": response.content,
                                "citations": response.additional_kwargs.get("search_results", [])
                            },
                            "metadata": {"timestamp": datetime.utcnow().isoformat(), "query": query}
                        })
                    except Exception as e:
                        logger.error(f"Perplexity research exception for query='{query}': {str(e)}", exc_info=True)
                        return json.dumps({"success": False, "error": f"Perplexity research failed: {str(e)}"})
                
                return json.dumps({"success": False, "error": f"Invalid provider '{provider}'. Use 'tavily', 'perplexity', or 'auto'."})

            tools.append(research)

        return tools

    def get_tools(self) -> List:
        """
        Get the combined list of common tools and specialized agent tools.
        
        Returns:
            List: List of LangChain tools available to this agent
        """
        return self.get_common_tools() + self._get_agent_tools()
        
    @abstractmethod
    def _get_agent_tools(self) -> List:
        """
        Get the list of specialized tools/functions available to this specific agent.
        
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

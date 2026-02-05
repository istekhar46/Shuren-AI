"""
Agent Orchestrator Service

This module provides the AgentOrchestrator class that routes user queries
to the appropriate specialized agent based on query classification.
"""

import logging
from enum import Enum
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """
    Enumeration of all available agent types in the Shuren system.
    
    Each agent type represents a specialized domain expert that handles
    specific types of user queries and interactions.
    """
    
    # Specialized Agents (to be implemented in Sub-Doc 2)
    WORKOUT_PLANNING = "workout_planning"
    DIET_PLANNING = "diet_planning"
    SUPPLEMENT_GUIDANCE = "supplement_guidance"
    TRACKING_ADJUSTMENT = "tracking_adjustment"
    SCHEDULING_REMINDER = "scheduling_reminder"
    CONVERSATIONAL_GENERAL = "conversational_general"
    
    # Test Agent (for framework validation)
    TEST = "test"


class AgentOrchestrator:
    """
    Orchestrates routing of user queries to appropriate specialized agents.
    
    The orchestrator manages agent lifecycle, query classification, and caching
    strategies based on the interaction mode (text vs voice).
    
    In voice mode, agents and classifications are cached for performance to meet
    the <2s latency requirement. In text mode, fresh agents are created for each
    interaction.
    
    Attributes:
        db_session: Async database session for data operations
        mode: Interaction mode - "text" or "voice"
        _agent_cache: Cache of agent instances (voice mode only)
        _classification_cache: Cache of query classifications
        last_agent_type: Tracks the last agent type used
    """
    
    def __init__(self, db_session: AsyncSession, mode: str = "text"):
        """
        Initialize the AgentOrchestrator.
        
        Args:
            db_session: Async SQLAlchemy session for database operations
            mode: Interaction mode - "text" or "voice" (default: "text")
        
        Raises:
            ValueError: If mode is not "text" or "voice"
        """
        if mode not in ["text", "voice"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'text' or 'voice'")
        
        self.db_session = db_session
        self.mode = mode
        
        # Initialize caches based on mode
        # Voice mode caches agents for performance (<2s latency requirement)
        # Text mode creates fresh agents each time
        self._agent_cache: Optional[Dict[AgentType, any]] = {} if mode == "voice" else None
        
        # Classification cache used in voice mode to avoid repeated LLM calls
        # Cache key is first 50 characters of query
        self._classification_cache: Dict[str, AgentType] = {}
        
        # Track last agent type used for context continuity
        self.last_agent_type: Optional[AgentType] = None
    
    async def route_query(
        self,
        user_id: str,
        query: str,
        agent_type: Optional[AgentType] = None,
        voice_mode: bool = False
    ) -> "AgentResponse":
        """
        Route a user query to the appropriate agent and return the response.
        
        This is the main entry point for processing user queries. It handles:
        1. Loading user context from the database
        2. Classifying the query to determine the appropriate agent (if not specified)
        3. Getting or creating the agent instance
        4. Processing the query based on the mode (text vs voice)
        5. Returning the agent's response
        
        Args:
            user_id: User's unique identifier
            query: User's query text
            agent_type: Optional explicit agent type (if None, will classify)
            voice_mode: Whether this is a voice interaction (default: False)
        
        Returns:
            AgentResponse: Structured response from the agent
        
        Raises:
            ValueError: If user not found or invalid agent type
        
        Example:
            >>> orchestrator = AgentOrchestrator(db_session, mode="text")
            >>> response = await orchestrator.route_query(
            ...     user_id="user-123",
            ...     query="What should I eat today?",
            ...     voice_mode=False
            ... )
            >>> print(response.content)
        """
        # Import here to avoid circular dependency
        from app.services.context_loader import load_agent_context
        from app.agents.context import AgentResponse
        
        # Step 1: Load user context from database
        context = await load_agent_context(
            db=self.db_session,
            user_id=user_id,
            include_history=True
        )
        
        # Step 2: Classify query if agent_type not provided
        if agent_type is None:
            agent_type = await self._classify_query(query)
        
        # Step 3: Get or create agent instance
        agent = self._get_or_create_agent(agent_type, context)
        
        # Step 4: Process based on mode
        if voice_mode:
            # Voice mode: return concise string response wrapped in AgentResponse
            response_content = await agent.process_voice(query)
            response = AgentResponse(
                content=response_content,
                agent_type=agent_type.value,
                tools_used=[],
                metadata={
                    "mode": "voice",
                    "user_id": user_id,
                    "fitness_level": context.fitness_level
                }
            )
        else:
            # Text mode: return full AgentResponse
            response = await agent.process_text(query)
        
        # Step 5: Track last agent type used
        self.last_agent_type = agent_type
        
        return response
    
    async def _classify_query(self, query: str) -> AgentType:
        """
        Classify a user query to determine the appropriate agent type.
        
        This is a placeholder implementation that always returns AgentType.TEST.
        The actual classification logic using the classifier LLM will be implemented
        in Sub-Doc 2 (Specialized Agents).
        
        In voice mode, classifications are cached by the first 50 characters of the
        query to avoid repeated LLM calls and improve latency.
        
        Args:
            query: User's query text
        
        Returns:
            AgentType: The classified agent type (currently always TEST)
        
        TODO: Sub-Doc 2 - Implement actual query classification using classifier LLM
        TODO: Sub-Doc 2 - Add classification logic for all specialized agents
        TODO: Sub-Doc 2 - Use Claude Haiku with temperature=0.1 for fast routing
        
        Example:
            >>> agent_type = await orchestrator._classify_query("What workout should I do?")
            >>> assert agent_type == AgentType.TEST  # Placeholder behavior
        """
        # Create cache key from first 50 characters of query
        cache_key = query[:50].lower().strip()
        
        # Check classification cache
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]
        
        # Placeholder: Always return TEST agent type
        # TODO: Sub-Doc 2 - Replace with actual classifier LLM call
        classified_type = AgentType.TEST
        
        # Cache result in voice mode for performance
        if self.mode == "voice":
            self._classification_cache[cache_key] = classified_type
        
        return classified_type

    def _get_or_create_agent(self, agent_type: AgentType, context: "AgentContext"):
        """
        Get an existing agent from cache or create a new one.
        
        In voice mode, agents are cached in memory to avoid re-initialization
        overhead and meet the <2s latency requirement. In text mode, fresh
        agents are created for each interaction.
        
        Args:
            agent_type: Type of agent to get or create
            context: AgentContext containing user data
        
        Returns:
            Agent instance (BaseAgent subclass)
        
        Example:
            >>> agent = orchestrator._get_or_create_agent(AgentType.TEST, context)
            >>> response = await agent.process_text("Hello")
        """
        # Check agent cache if voice mode
        if self.mode == "voice" and self._agent_cache is not None:
            # Return cached agent if exists
            if agent_type in self._agent_cache:
                return self._agent_cache[agent_type]
        
        # Create new agent if not cached
        agent = self._create_agent(agent_type, context)
        
        # Cache agent in voice mode
        if self.mode == "voice" and self._agent_cache is not None:
            self._agent_cache[agent_type] = agent
        
        return agent
    
    def _create_agent(self, agent_type: AgentType, context: "AgentContext") -> "BaseAgent":
        """
        Factory method to create agent instances based on agent type.
        
        This method maps AgentType enum values to their corresponding agent
        class implementations and instantiates them with the provided context
        and database session.
        
        Currently only the TEST agent is implemented. Specialized agents will
        be added in Sub-Doc 2.
        
        Args:
            agent_type: Type of agent to create
            context: AgentContext containing user data
        
        Returns:
            BaseAgent: Instance of the requested agent type
        
        Raises:
            ValueError: If agent_type is not supported
        
        TODO: Sub-Doc 2 - Add WorkoutPlanningAgent
        TODO: Sub-Doc 2 - Add DietPlanningAgent
        TODO: Sub-Doc 2 - Add SupplementGuidanceAgent
        TODO: Sub-Doc 2 - Add TrackingAdjustmentAgent
        TODO: Sub-Doc 2 - Add SchedulingReminderAgent
        TODO: Sub-Doc 2 - Add ConversationalGeneralAgent
        
        Example:
            >>> agent = orchestrator._create_agent(AgentType.TEST, context)
            >>> assert isinstance(agent, TestAgent)
        """
        # Import agents here to avoid circular dependencies
        from app.agents.test_agent import TestAgent
        
        # Define agent mapping
        # Maps AgentType enum values to their corresponding agent classes
        agent_map = {
            AgentType.TEST: TestAgent,
            # TODO: Sub-Doc 2 - Add specialized agents
            # AgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
            # AgentType.DIET_PLANNING: DietPlanningAgent,
            # AgentType.SUPPLEMENT_GUIDANCE: SupplementGuidanceAgent,
            # AgentType.TRACKING_ADJUSTMENT: TrackingAdjustmentAgent,
            # AgentType.SCHEDULING_REMINDER: SchedulingReminderAgent,
            # AgentType.CONVERSATIONAL_GENERAL: ConversationalGeneralAgent,
        }
        
        # Get agent class from map
        agent_class = agent_map.get(agent_type)
        
        if agent_class is None:
            raise ValueError(
                f"Unsupported agent type: {agent_type.value}. "
                f"Available types: {', '.join([t.value for t in agent_map.keys()])}"
            )
        
        # Create and return agent instance
        return agent_class(context=context, db_session=self.db_session)
    
    async def warm_up(self) -> None:
        """
        Warm up the LLM connection by making a dummy call.
        
        This method pre-establishes the LLM connection to reduce latency on the
        first real query. It's particularly important in voice mode where the
        <2s latency requirement is critical.
        
        The warm-up only runs in voice mode since text mode doesn't have the
        same strict latency requirements. If warm-up fails, it logs a warning
        but doesn't raise an exception since it's not critical to functionality.
        
        This method:
        1. Checks if in voice mode (no-op for text mode)
        2. Creates a minimal AgentContext for testing
        3. Creates a test agent instance
        4. Makes a dummy LLM call with a simple message
        5. Logs success or warning on failure
        
        Raises:
            No exceptions raised - failures are logged as warnings
        
        Example:
            >>> orchestrator = AgentOrchestrator(db_session, mode="voice")
            >>> await orchestrator.warm_up()
            >>> # LLM connection is now pre-established
        """
        # Only warm up in voice mode
        if self.mode != "voice":
            return
        
        try:
            # Import dependencies
            from app.agents.context import AgentContext
            from langchain_core.messages import HumanMessage
            
            # Create minimal context for warm-up
            # This doesn't need to be a real user - just enough to initialize the agent
            minimal_context = AgentContext(
                user_id="warmup-test",
                fitness_level="beginner",
                primary_goal="general_fitness",
                energy_level="medium"
            )
            
            # Create test agent
            test_agent = self._create_agent(AgentType.TEST, minimal_context)
            
            # Make dummy LLM call to establish connection
            # Use a simple message that will get a quick response
            await test_agent.llm.ainvoke([HumanMessage(content="hello")])
            
            # Log success
            logger.info("LLM connection warmed up successfully")
            
        except Exception as e:
            # Log warning but don't raise - warm-up failure is not critical
            # The system will still work, just with slightly higher latency on first query
            logger.warning(f"LLM warm-up failed: {e}. First query may have higher latency.")


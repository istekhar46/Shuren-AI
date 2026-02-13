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
    
    # Specialized Agents
    WORKOUT = "workout"
    DIET = "diet"
    SUPPLEMENT = "supplement"
    TRACKER = "tracker"
    SCHEDULER = "scheduler"
    GENERAL = "general"
    
    # Test Agent (for framework validation and backward compatibility)
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
    
    def _enforce_access_control(
        self,
        user: "User",
        onboarding_state: Optional["OnboardingState"],
        agent_type: Optional[AgentType],
        onboarding_mode: bool
    ) -> None:
        """
        Enforce strict agent access control based on onboarding status.
        
        This method implements the core access control logic that ensures:
        - Specialized agents are ONLY accessible during onboarding
        - General agent is ONLY accessible post-onboarding
        - Proper error messages guide users to correct endpoints
        
        Args:
            user: User model instance
            onboarding_state: OnboardingState model instance (can be None)
            agent_type: Requested agent type (can be None if classification needed)
            onboarding_mode: Whether this is an onboarding interaction
        
        Raises:
            ValueError: If access control rules are violated
        
        Access Control Matrix:
            During Onboarding (onboarding_mode=True):
                - Specialized agents (WORKOUT, DIET, SCHEDULER, SUPPLEMENT): ✅ Allowed
                - General agent: ❌ Blocked
                - Tracker agent: ❌ Blocked
                - Test agent: ✅ Allowed (testing only)
            
            Post-Onboarding (onboarding_mode=False):
                - Specialized agents: ❌ Blocked
                - General agent: ✅ Allowed (forced)
                - Tracker agent: ✅ Allowed (via general agent)
                - Test agent: ✅ Allowed (testing only)
        """
        user_id = str(user.id)
        
        # Check if onboarding state exists
        if not onboarding_state:
            logger.error(f"Onboarding state not found for user: {user_id}")
            raise ValueError(
                f"Onboarding state not found for user: {user_id}. "
                "User must complete registration and initialize onboarding first."
            )
        
        # Define specialized agents (onboarding-only)
        specialized_agents = {
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SCHEDULER,
            AgentType.SUPPLEMENT
        }
        
        # CASE 1: During Onboarding (onboarding_mode=True)
        if onboarding_mode:
            # Reject if onboarding already completed
            if onboarding_state.is_complete:
                logger.warning(
                    f"Access control violation: user={user_id}, "
                    f"reason=onboarding_already_completed, "
                    f"completed_at={onboarding_state.updated_at}"
                )
                raise ValueError(
                    "Onboarding already completed. "
                    "Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. "
                    f"User: {user_id}, Onboarding completed at: {onboarding_state.updated_at}"
                )
            
            # Reject if general agent requested during onboarding
            if agent_type == AgentType.GENERAL:
                logger.warning(
                    f"Access control violation: user={user_id}, "
                    f"reason=general_agent_during_onboarding, "
                    f"current_step={onboarding_state.current_step}/9"
                )
                raise ValueError(
                    "General agent is not available during onboarding. "
                    "Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. "
                    f"Current state: {onboarding_state.current_step}/9. "
                    f"User: {user_id}"
                )
            
            # Reject if tracker agent requested during onboarding
            if agent_type == AgentType.TRACKER:
                logger.warning(
                    f"Access control violation: user={user_id}, "
                    f"reason=tracker_agent_during_onboarding"
                )
                raise ValueError(
                    "Tracker agent is not available during onboarding. "
                    "Progress tracking begins after onboarding completion. "
                    f"User: {user_id}"
                )
            
            # Allow specialized agents and test agent
            # (agent_type will be validated later in _create_agent)
            logger.debug(
                f"Access control passed: user={user_id}, "
                f"agent_type={agent_type.value if agent_type else 'to_be_classified'}, "
                f"onboarding_mode=True, "
                f"onboarding_step={onboarding_state.current_step}/9"
            )
        
        # CASE 2: Post-Onboarding (onboarding_mode=False)
        else:
            # Reject if onboarding not completed
            if not onboarding_state.is_complete:
                logger.warning(
                    f"Access control violation: user={user_id}, "
                    f"reason=onboarding_not_completed, "
                    f"current_step={onboarding_state.current_step}/9"
                )
                raise ValueError(
                    "Complete onboarding first before accessing regular chat. "
                    f"Current progress: {onboarding_state.current_step}/9 states completed. "
                    f"Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. "
                    f"User: {user_id}"
                )
            
            # Reject if specialized agent explicitly requested
            if agent_type and agent_type in specialized_agents:
                logger.warning(
                    f"Access control violation: user={user_id}, "
                    f"reason=specialized_agent_post_onboarding, "
                    f"requested_agent={agent_type.value}"
                )
                raise ValueError(
                    f"Specialized agent '{agent_type.value}' is not available after onboarding completion. "
                    "Only the general agent is accessible for post-onboarding interactions. "
                    "The general agent can answer questions about workouts, meals, and schedules. "
                    f"User: {user_id}"
                )
            
            # Allow general agent and tracker agent (tracker via general agent delegation)
            # Test agent also allowed for testing
            logger.debug(
                f"Access control passed: user={user_id}, "
                f"agent_type={agent_type.value if agent_type else 'general'}, "
                f"onboarding_mode=False, "
                f"onboarding_complete=True"
            )
    def _log_routing_decision(
        self,
        user_id: str,
        agent_type: AgentType,
        onboarding_mode: bool,
        onboarding_state: Optional["OnboardingState"],
        classification_used: bool,
        routing_time_ms: int
    ) -> None:
        """
        Log agent routing decision with comprehensive context.

        This method logs all routing decisions with detailed context for debugging,
        analytics, and monitoring. It includes user information, agent selection,
        onboarding status, and performance metrics.

        The log entry provides a complete audit trail of how queries are routed
        through the system, enabling:
        - Debugging routing issues
        - Analyzing agent usage patterns
        - Monitoring performance metrics
        - Tracking onboarding progress

        Args:
            user_id: User's unique identifier
            agent_type: Selected agent type
            onboarding_mode: Whether this is onboarding mode
            onboarding_state: OnboardingState instance (can be None)
            classification_used: Whether classification was used to determine agent
            routing_time_ms: Time taken for routing decision in milliseconds

        Example Log Output:
            INFO: Agent routing: user=user-123, agent_type=workout,
                  onboarding_mode=True, onboarding_complete=False,
                  onboarding_step=2/9, mode=voice, classification_used=True,
                  routing_time_ms=45
        """
        logger.info(
            f"Agent routing: user={user_id}, "
            f"agent_type={agent_type.value}, "
            f"onboarding_mode={onboarding_mode}, "
            f"onboarding_complete={onboarding_state.is_complete if onboarding_state else 'N/A'}, "
            f"onboarding_step={onboarding_state.current_step if onboarding_state else 'N/A'}/9, "
            f"mode={self.mode}, "
            f"classification_used={classification_used}, "
            f"routing_time_ms={routing_time_ms}"
        )

    
    def _init_classifier_llm(self):
        """
        Initialize a fast classifier LLM for query routing.
        
        Uses the configured classifier model for fast, low-latency query classification.
        The classifier uses a low temperature (0.1) for consistent routing decisions.
        
        If CLASSIFIER_MODEL is set to a Gemini model, uses Google's API.
        Otherwise, defaults to Anthropic Claude Haiku for fast classification.
        
        The classifier model is configurable via CLASSIFIER_MODEL setting, allowing
        flexibility to use different models based on performance and cost requirements.
        
        Returns:
            Chat model instance configured for fast query routing
        """
        from langchain_anthropic import ChatAnthropic
        from langchain_google_genai import ChatGoogleGenerativeAI
        from app.core.config import settings
        
        # Check if classifier model is a Gemini model
        if "gemini" in settings.CLASSIFIER_MODEL.lower():
            return ChatGoogleGenerativeAI(
                model=settings.CLASSIFIER_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=settings.CLASSIFIER_TEMPERATURE,
                max_output_tokens=10
            )
        else:
            # Default to Anthropic Claude Haiku
            return ChatAnthropic(
                model=settings.CLASSIFIER_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.CLASSIFIER_TEMPERATURE,
                max_tokens=10
            )
    def _enforce_access_control(
            self,
            user: "User",
            onboarding_state: Optional["OnboardingState"],
            agent_type: Optional[AgentType],
            onboarding_mode: bool
        ) -> None:
            """
            Enforce strict agent access control based on onboarding status.

            This method implements the core access control logic that ensures:
            - Specialized agents are ONLY accessible during onboarding
            - General agent is ONLY accessible post-onboarding
            - Proper error messages guide users to correct endpoints

            Args:
                user: User model instance
                onboarding_state: OnboardingState model instance (can be None)
                agent_type: Requested agent type (can be None if classification needed)
                onboarding_mode: Whether this is an onboarding interaction

            Raises:
                ValueError: If access control rules are violated

            Access Control Matrix:
                During Onboarding (onboarding_mode=True):
                    - Specialized agents (WORKOUT, DIET, SCHEDULER, SUPPLEMENT): ✅ Allowed
                    - General agent: ❌ Blocked
                    - Tracker agent: ❌ Blocked
                    - Test agent: ✅ Allowed (testing only)

                Post-Onboarding (onboarding_mode=False):
                    - Specialized agents: ❌ Blocked
                    - General agent: ✅ Allowed (forced)
                    - Tracker agent: ✅ Allowed (via general agent)
                    - Test agent: ✅ Allowed (testing only)
            """
            user_id = str(user.id)

            # Check if onboarding state exists
            if not onboarding_state:
                logger.error(f"Onboarding state not found for user: {user_id}")
                raise ValueError(
                    f"Onboarding state not found for user: {user_id}. "
                    "User must complete registration and initialize onboarding first."
                )

            # Define specialized agents (onboarding-only)
            specialized_agents = {
                AgentType.WORKOUT,
                AgentType.DIET,
                AgentType.SCHEDULER,
                AgentType.SUPPLEMENT
            }

            # CASE 1: During Onboarding (onboarding_mode=True)
            if onboarding_mode:
                # Reject if onboarding already completed
                if onboarding_state.is_complete:
                    logger.warning(
                        f"Access control violation: user={user_id}, "
                        f"reason=onboarding_already_completed, "
                        f"completed_at={onboarding_state.updated_at}"
                    )
                    raise ValueError(
                        "Onboarding already completed. "
                        "Use the regular chat endpoint (POST /api/v1/chat) instead of the onboarding endpoint. "
                        f"User: {user_id}, Onboarding completed at: {onboarding_state.updated_at}"
                    )

                # Reject if general agent requested during onboarding
                if agent_type == AgentType.GENERAL:
                    logger.warning(
                        f"Access control violation: user={user_id}, "
                        f"reason=general_agent_during_onboarding, "
                        f"current_step={onboarding_state.current_step}/9"
                    )
                    raise ValueError(
                        "General agent is not available during onboarding. "
                        "Specialized agents (workout, diet, scheduler, supplement) handle onboarding states. "
                        f"Current state: {onboarding_state.current_step}/9. "
                        f"User: {user_id}"
                    )

                # Reject if tracker agent requested during onboarding
                if agent_type == AgentType.TRACKER:
                    logger.warning(
                        f"Access control violation: user={user_id}, "
                        f"reason=tracker_agent_during_onboarding"
                    )
                    raise ValueError(
                        "Tracker agent is not available during onboarding. "
                        "Progress tracking begins after onboarding completion. "
                        f"User: {user_id}"
                    )

                # Allow specialized agents and test agent
                # (agent_type will be validated later in _create_agent)
                logger.debug(
                    f"Access control passed: user={user_id}, "
                    f"agent_type={agent_type.value if agent_type else 'to_be_classified'}, "
                    f"onboarding_mode=True, "
                    f"onboarding_step={onboarding_state.current_step}/9"
                )

            # CASE 2: Post-Onboarding (onboarding_mode=False)
            else:
                # Reject if onboarding not completed
                if not onboarding_state.is_complete:
                    logger.warning(
                        f"Access control violation: user={user_id}, "
                        f"reason=onboarding_not_completed, "
                        f"current_step={onboarding_state.current_step}/9"
                    )
                    raise ValueError(
                        "Complete onboarding first before accessing regular chat. "
                        f"Current progress: {onboarding_state.current_step}/9 states completed. "
                        f"Use the onboarding chat endpoint (POST /api/v1/chat/onboarding) to continue. "
                        f"User: {user_id}"
                    )

                # Reject if specialized agent explicitly requested
                if agent_type and agent_type in specialized_agents:
                    logger.warning(
                        f"Access control violation: user={user_id}, "
                        f"reason=specialized_agent_post_onboarding, "
                        f"requested_agent={agent_type.value}"
                    )
                    raise ValueError(
                        f"Specialized agent '{agent_type.value}' is not available after onboarding completion. "
                        "Only the general agent is accessible for post-onboarding interactions. "
                        "The general agent can answer questions about workouts, meals, and schedules. "
                        f"User: {user_id}"
                    )

                # Allow general agent and tracker agent (tracker via general agent delegation)
                # Test agent also allowed for testing
                logger.debug(
                    f"Access control passed: user={user_id}, "
                    f"agent_type={agent_type.value if agent_type else 'general'}, "
                    f"onboarding_mode=False, "
                    f"onboarding_complete=True"
                )
    
    def _log_routing_decision(
        self,
        user_id: str,
        agent_type: AgentType,
        onboarding_mode: bool,
        onboarding_state: Optional["OnboardingState"],
        classification_used: bool,
        routing_time_ms: int
    ) -> None:
        """
        Log agent routing decision with comprehensive context.
        
        This method logs all routing decisions with detailed context for debugging,
        analytics, and monitoring. It includes user information, agent selection,
        onboarding status, and performance metrics.
        
        The log entry provides a complete audit trail of how queries are routed
        through the system, enabling:
        - Debugging routing issues
        - Analyzing agent usage patterns
        - Monitoring performance metrics
        - Tracking onboarding progress
        
        Args:
            user_id: User's unique identifier
            agent_type: Selected agent type
            onboarding_mode: Whether this is onboarding mode
            onboarding_state: OnboardingState instance (can be None)
            classification_used: Whether classification was used to determine agent
            routing_time_ms: Time taken for routing decision in milliseconds
        
        Example Log Output:
            INFO: Agent routing: user=user-123, agent_type=workout, 
                  onboarding_mode=True, onboarding_complete=False, 
                  onboarding_step=2/9, mode=voice, classification_used=True, 
                  routing_time_ms=45
        """
        logger.info(
            f"Agent routing: user={user_id}, "
            f"agent_type={agent_type.value}, "
            f"onboarding_mode={onboarding_mode}, "
            f"onboarding_complete={onboarding_state.is_complete if onboarding_state else 'N/A'}, "
            f"onboarding_step={onboarding_state.current_step if onboarding_state else 'N/A'}/9, "
            f"mode={self.mode}, "
            f"classification_used={classification_used}, "
            f"routing_time_ms={routing_time_ms}"
        )

    
    async def route_query(
        self,
        user_id: str,
        query: str,
        agent_type: Optional[AgentType] = None,
        voice_mode: bool = False,
        onboarding_mode: bool = False
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
            onboarding_mode: Whether this is during onboarding (default: False)

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
        from app.models.user import User
        from app.models.onboarding import OnboardingState
        from sqlalchemy import select
        import time
        
        # Start performance timing
        start_time = time.time()
        classification_time_ms = 0
        agent_creation_time_ms = 0

        # Step 1: Load user context from database
        context = await load_agent_context(
            db=self.db_session,
            user_id=user_id,
            include_history=True,
            onboarding_mode=onboarding_mode
        )
        
        # Step 1.5: Load user and onboarding state for access control
        result = await self.db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Load onboarding state
        onboarding_result = await self.db_session.execute(
            select(OnboardingState).where(OnboardingState.user_id == user_id)
        )
        onboarding_state = onboarding_result.scalar_one_or_none()
        
        # Step 2: Enforce access control (NEW)
        self._enforce_access_control(
            user=user,
            onboarding_state=onboarding_state,
            agent_type=agent_type,
            onboarding_mode=onboarding_mode
        )
        
        # Step 3: Classify query if agent_type not provided
        classification_used = False
        if agent_type is None:
            classification_start = time.time()
            agent_type = await self._classify_query(query, onboarding_mode)
            classification_time_ms = int((time.time() - classification_start) * 1000)
            classification_used = True
            logger.debug(f"Classification time: {classification_time_ms}ms")
        
        # Step 3.5: Force GENERAL agent post-onboarding (NEW)
        if not onboarding_mode:
            if agent_type != AgentType.GENERAL and agent_type != AgentType.TEST:
                logger.info(
                    f"Query classified as {agent_type.value}, "
                    f"forcing to general agent (post-onboarding)"
                )
                agent_type = AgentType.GENERAL

        # Step 4: Get or create agent instance
        agent_creation_start = time.time()
        agent = self._get_or_create_agent(agent_type, context)
        agent_creation_time_ms = int((time.time() - agent_creation_start) * 1000)
        logger.debug(f"Agent creation time: {agent_creation_time_ms}ms")

        # Step 5: Process based on mode
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
                    "fitness_level": context.fitness_level,
                    "onboarding_mode": onboarding_mode
                }
            )
        else:
            # Text mode: return full AgentResponse
            response = await agent.process_text(query)
            # Add onboarding_mode to metadata
            if not response.metadata:
                response.metadata = {}
            response.metadata["onboarding_mode"] = onboarding_mode

        # Step 6: Track last agent type used
        self.last_agent_type = agent_type
        
        # Step 7: Log routing decision with performance metrics
        total_routing_time_ms = int((time.time() - start_time) * 1000)
        logger.debug(
            f"Performance metrics: classification={classification_time_ms}ms, "
            f"agent_creation={agent_creation_time_ms}ms, "
            f"total_routing={total_routing_time_ms}ms"
        )
        
        self._log_routing_decision(
            user_id=user_id,
            agent_type=agent_type,
            onboarding_mode=onboarding_mode,
            onboarding_state=onboarding_state,
            classification_used=classification_used,
            routing_time_ms=total_routing_time_ms
        )

        return response

    
    async def _classify_query(
        self,
        query: str,
        onboarding_mode: bool = False
    ) -> AgentType:
        """
        Classify a user query to determine the appropriate agent type.

        Uses a fast classifier LLM (Claude Haiku) to analyze the query and route
        it to the most appropriate specialized agent. The classifier uses a low
        temperature (0.1) for consistent routing decisions.

        Uses different classification prompts based on onboarding mode:
        - During onboarding: Only returns specialized agents
        - Post-onboarding: Returns any agent type (but will be overridden to GENERAL)

        In voice mode, classifications are cached by the first 50 characters of the
        query to avoid repeated LLM calls and improve latency.

        Args:
            query: User's query text
            onboarding_mode: Whether this is during onboarding (default: False)

        Returns:
            AgentType: The classified agent type, defaults based on mode on failure

        Example:
            >>> agent_type = await orchestrator._classify_query("What workout should I do?")
            >>> assert agent_type == AgentType.WORKOUT
            >>> agent_type = await orchestrator._classify_query("What workout should I do?", onboarding_mode=True)
            >>> assert agent_type in [AgentType.WORKOUT, AgentType.DIET, AgentType.SCHEDULER, AgentType.SUPPLEMENT]
        """
        # Create cache key from first 50 characters of query
        # Include onboarding_mode in cache key for proper separation
        cache_key = f"{onboarding_mode}:{query[:50].lower().strip()}"

        # Check classification cache
        if cache_key in self._classification_cache:
            logger.debug(f"Using cached classification for query: {cache_key}")
            return self._classification_cache[cache_key]

        # Initialize classifier LLM
        classifier = self._init_classifier_llm()

        # Build classification messages based on mode
        from langchain_core.messages import SystemMessage, HumanMessage

        if onboarding_mode:
            # Onboarding classification: Only specialized agents
            classification_prompt = """Classify this onboarding query into ONE category:
    - workout: Fitness level, exercise plans, workout preferences, equipment, injuries, limitations
    - diet: Dietary preferences, meal plans, nutrition, food restrictions, allergies, intolerances
    - scheduler: Meal timing, workout schedule, hydration reminders, timing preferences
    - supplement: Supplement preferences, guidance, current usage

    Respond with ONLY the category name."""
        else:
            # Post-onboarding classification: All agents (but will be overridden to general)
            classification_prompt = """Classify this fitness query into ONE category:
    - workout: Exercise plans, form, demonstrations, logging sets, workout routines, training
    - diet: Meal plans, nutrition, recipes, food substitutions, calories, macros, eating
    - supplement: Supplement guidance and information, vitamins, protein powder
    - tracker: Progress tracking, adherence, metrics, weight tracking, measurements
    - scheduler: Schedule changes, reminders, timing, rescheduling workouts or meals
    - general: Motivation, casual conversation, general questions, greetings

    Respond with ONLY the category name."""

        messages = [
            SystemMessage(content=classification_prompt),
            HumanMessage(content=query)
        ]

        try:
            # Call classifier LLM
            result = await classifier.ainvoke(messages)
            agent_type_str = result.content.strip().lower()

            logger.debug(
                f"Classifier returned: {agent_type_str} for query: {query[:50]}, "
                f"onboarding_mode={onboarding_mode}"
            )

            # Parse response to AgentType enum
            try:
                classified_type = AgentType(agent_type_str)
            except ValueError:
                # Default based on mode
                if onboarding_mode:
                    # Default to WORKOUT during onboarding (first agent)
                    logger.warning(
                        f"Unknown agent type from classifier: {agent_type_str}, "
                        f"defaulting to WORKOUT for onboarding query: {query[:50]}"
                    )
                    classified_type = AgentType.WORKOUT
                else:
                    # Default to GENERAL post-onboarding
                    logger.warning(
                        f"Unknown agent type from classifier: {agent_type_str}, "
                        f"defaulting to GENERAL for query: {query[:50]}"
                    )
                    classified_type = AgentType.GENERAL

            # Cache result in voice mode for performance
            if self.mode == "voice":
                self._classification_cache[cache_key] = classified_type
                logger.debug(f"Cached classification: {classified_type.value} for key: {cache_key}")

            return classified_type

        except Exception as e:
            # Log error and default based on mode
            logger.error(
                f"Classification failed for query '{query[:50]}': {e}. "
                f"Defaulting based on onboarding_mode={onboarding_mode}"
            )
            return AgentType.WORKOUT if onboarding_mode else AgentType.GENERAL


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
        
        All 6 specialized agents are now implemented along with the TestAgent
        for backward compatibility.
        
        Args:
            agent_type: Type of agent to create
            context: AgentContext containing user data
        
        Returns:
            BaseAgent: Instance of the requested agent type
        
        Raises:
            ValueError: If agent_type is not supported
        
        Example:
            >>> agent = orchestrator._create_agent(AgentType.WORKOUT, context)
            >>> assert isinstance(agent, WorkoutPlannerAgent)
        """
        # Import agents here to avoid circular dependencies
        from app.agents.test_agent import TestAgent
        from app.agents.workout_planner import WorkoutPlannerAgent
        from app.agents.diet_planner import DietPlannerAgent
        from app.agents.supplement_guide import SupplementGuideAgent
        from app.agents.tracker import TrackerAgent
        from app.agents.scheduler import SchedulerAgent
        from app.agents.general_assistant import GeneralAssistantAgent
        
        # Define agent mapping
        # Maps AgentType enum values to their corresponding agent classes
        agent_map = {
            AgentType.WORKOUT: WorkoutPlannerAgent,
            AgentType.DIET: DietPlannerAgent,
            AgentType.SUPPLEMENT: SupplementGuideAgent,
            AgentType.TRACKER: TrackerAgent,
            AgentType.SCHEDULER: SchedulerAgent,
            AgentType.GENERAL: GeneralAssistantAgent,
            AgentType.TEST: TestAgent,  # Keep for backward compatibility
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


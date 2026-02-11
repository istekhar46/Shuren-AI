"""
LiveKit Voice Agent Worker for Shuren Fitness Coaching.

This module implements the FitnessVoiceAgent class that handles real-time
voice interactions with users through LiveKit's infrastructure. The agent
integrates STT (Deepgram), TTS (Cartesia), and LLM (configurable) with
the existing LangChain orchestrator for complex reasoning.

The voice agent achieves <2 second latency by:
- Pre-loading user context and orchestrator before connecting to rooms
- Using cached data for quick queries via function tools
- Processing workout logs asynchronously in background

NOTE: For testing purposes, the complex FitnessVoiceAgent is currently commented out.
      A simple test agent is used instead to verify the LiveKit voice pipeline works.
      To restore full functionality, uncomment the FitnessVoiceAgent code and update
      the entrypoint() function.
"""

import sys
import os
import json
from pathlib import Path

# Add backend directory to Python path for imports
# This allows running the worker directly: python app/livekit_agents/voice_agent_worker.py
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from livekit import agents, rtc, api
from livekit.agents import (
    JobContext,
    cli,
    AgentServer,
    RunContext,
)
# Import voice.Agent and voice.AgentSession from livekit.agents.voice
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, cartesia, openai, google, silero

from app.agents.context import AgentContext
from app.services.agent_orchestrator import AgentOrchestrator
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# SIMPLE TEST AGENT - For testing LiveKit voice pipeline
# ============================================================================

class SimpleTestAgent(Agent):
    """
    Simple test agent to verify LiveKit voice pipeline works correctly.
    
    This is a minimal agent with basic functionality to test:
    - STT (Speech-to-Text) with Deepgram
    - LLM (Language Model) processing
    - TTS (Text-to-Speech) with Cartesia
    - Function tool calling
    
    Once the pipeline is verified, switch back to FitnessVoiceAgent.
    """
    
    def __init__(self):
        """Initialize the simple test agent."""
        instructions = """
        You are a friendly AI fitness assistant for testing purposes.
        
        Keep your responses SHORT and CONCISE - under 20 seconds when spoken.
        Be warm, encouraging, and helpful.
        
        You can:
        - Greet users and have basic conversations
        - Tell fitness jokes when asked
        - Provide the current time
        - Answer simple fitness questions
        
        Remember: Keep it simple and conversational!
        """
        
        super().__init__(
            instructions=instructions,
            allow_interruptions=True,
        )
        
        logger.info("SimpleTestAgent created for testing LiveKit voice pipeline")
    
    @function_tool()
    async def tell_fitness_joke(self, context: RunContext) -> str:
        """
        Tell a fitness-related joke to lighten the mood.
        
        Use this when the user asks for a joke or wants to laugh.
        
        Returns:
            str: A fitness joke
        """
        jokes = [
            "Why did the bodybuilder bring a ladder to the gym? Because he wanted to reach new heights!",
            "What's a runner's favorite subject in school? Jog-raphy!",
            "Why don't weightlifters ever get lost? Because they always find their whey!",
            "What do you call a fitness tracker that tells jokes? A fit-bit of humor!",
        ]
        
        import random
        joke = random.choice(jokes)
        
        logger.info(f"Telling fitness joke: {joke[:50]}...")
        return joke
    
    @function_tool()
    async def get_current_time(self, context: RunContext) -> str:
        """
        Get the current time.
        
        Use this when the user asks what time it is.
        
        Returns:
            str: Current time in a friendly format
        """
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        logger.info(f"Providing current time: {time_str}")
        return f"It's currently {time_str}."


# ============================================================================
# COMPLEX FITNESS AGENT - Commented out for testing
# ============================================================================
# 
# To restore full functionality, change "if False:" to "if True:" below
#
if False:  # Set to True to enable FitnessVoiceAgent
    class FitnessVoiceAgent(Agent):
        """
        Voice agent for real-time fitness coaching interactions.
        
        This agent handles voice-based conversations with users, providing quick
        responses for simple queries (workout/meal lookups, logging) and delegating
        complex queries to the LangChain orchestrator.
        
        The agent maintains pre-loaded user context and orchestrator to minimize
        latency and meet the <2s response time requirement.
        
        Attributes:
            user_id: User's unique identifier
        agent_type: Type of agent (workout, diet, supplement, general)
        orchestrator: LangChain AgentOrchestrator for complex queries
        user_context: Pre-loaded AgentContext with user data
        _log_queue: Async queue for workout log entries
        _log_worker_task: Background task for log processing
    """
    
    def __init__(self, user_id: str, agent_type: str = "general"):
        """
        Initialize the FitnessVoiceAgent.
        
        Creates a new voice agent instance with the specified user and agent type.
        The agent must call initialize_orchestrator() before connecting to a room
        to pre-load context and warm up the LLM connection.
        
        Args:
            user_id: User's unique identifier (UUID as string)
            agent_type: Type of agent - workout, diet, supplement, or general
                       (default: "general")
        
        Example:
            >>> agent = FitnessVoiceAgent(user_id="user-123", agent_type="workout")
            >>> await agent.initialize_orchestrator()
            >>> # Agent is now ready to handle voice interactions
        """
        # Store user and agent identifiers BEFORE calling super().__init__
        self.user_id = user_id
        self.agent_type = agent_type
        
        # Initialize orchestrator and context (will be loaded in initialize_orchestrator)
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.user_context: Optional[AgentContext] = None
        
        # Initialize async queue for workout logging
        self._log_queue: asyncio.Queue = asyncio.Queue()
        
        # Initialize background log worker task
        self._log_worker_task: Optional[asyncio.Task] = None
        
        # Get base instructions for the agent type
        instructions = self._get_base_instructions_static(agent_type)
        
        # Initialize parent Agent class with instructions only
        # STT, LLM, TTS, VAD are configured in AgentSession, not in Agent
        super().__init__(
            instructions=instructions,
            allow_interruptions=True,
        )
        
        logger.info(
            f"FitnessVoiceAgent created for user {user_id} "
            f"with agent_type '{agent_type}'"
        )

    @staticmethod
    def _get_base_instructions_static(agent_type: str) -> str:
        """
        Static method to generate base instructions for the LLM based on agent type.
        
        This is a static version of _get_base_instructions that can be called
        during __init__ before the instance is fully initialized.
        
        Args:
            agent_type: Type of agent (workout, diet, supplement, general)
        
        Returns:
            str: Formatted instructions for the LLM
        """
        # Common instructions for all agent types
        common_instructions = """
        You are a friendly AI fitness coach for Shuren, speaking with a user in real-time voice conversation.

        RESPONSE GUIDELINES:
        - Keep responses CONCISE - under 30 seconds when spoken aloud
        - Use a conversational, encouraging tone
        - Provide actionable guidance, not just information
        - Be supportive and motivating without being pushy
        - Adapt to the user's fitness level and goals

        AVAILABLE TOOLS:
        - get_todays_workout(): Get today's workout plan from cached data
        - get_todays_meals(): Get today's meal plan from cached data
        - log_workout_set(exercise, reps, weight): Log a completed workout set
        - ask_specialist_agent(query, specialist): Delegate complex queries to specialized agents

        WHEN TO USE TOOLS:
        - Use get_todays_workout/get_todays_meals for quick lookups
        - Use log_workout_set when user reports completing a set
        - Use ask_specialist_agent for complex questions requiring detailed analysis

        DELEGATION STRATEGY:
        - For complex workout programming questions → ask_specialist_agent(query, "workout")
        - For detailed nutrition or meal planning → ask_specialist_agent(query, "diet")
        - For supplement questions → ask_specialist_agent(query, "supplement")
        - Keep simple queries (today's plan, logging) handled directly
        """
        
        # Agent-specific instructions
        agent_specific = {
            "workout": """
        YOUR ROLE: Workout Coaching Specialist
        You focus on exercise guidance, form tips, workout execution, and progress tracking.

        EXPERTISE:
        - Guiding users through their workout sessions
        - Providing exercise form cues and safety tips
        - Logging workout sets and tracking progress
        - Answering quick questions about today's workout
        - Motivating users during challenging sets

        DELEGATE TO SPECIALISTS:
        - Complex workout plan modifications → workout specialist
        - Nutrition questions → diet specialist
        - Supplement questions → supplement specialist
        """,
                    "diet": """
        YOUR ROLE: Nutrition Coaching Specialist
        You focus on meal guidance, nutrition tips, and dietary adherence.

        EXPERTISE:
        - Helping users understand their meal plan
        - Providing quick meal suggestions and substitutions
        - Answering questions about today's meals
        - Offering nutrition tips and motivation
        - Supporting dietary adherence

        DELEGATE TO SPECIALISTS:
        - Complex meal plan modifications → diet specialist
        - Workout questions → workout specialist
        - Supplement questions → supplement specialist
        """,
                    "supplement": """
        YOUR ROLE: Supplement Guidance Specialist
        You focus on supplement information and guidance (non-medical).

        EXPERTISE:
        - Providing general supplement information
        - Answering questions about common supplements
        - Explaining supplement timing and usage
        - Clarifying supplement-related queries

        IMPORTANT: You provide guidance only, not medical advice.

        DELEGATE TO SPECIALISTS:
        - Workout questions → workout specialist
        - Nutrition questions → diet specialist
        - Complex supplement protocols → supplement specialist
        """,
                    "general": """
        YOUR ROLE: General Fitness Assistant
        You provide overall fitness coaching and motivation across all domains.

        EXPERTISE:
        - Answering general fitness questions
        - Providing motivation and encouragement
        - Helping with workout and meal adherence
        - Offering lifestyle and habit guidance
        - Routing complex questions to specialists

        DELEGATE TO SPECIALISTS:
        - Detailed workout questions → workout specialist
        - Detailed nutrition questions → diet specialist
        - Supplement questions → supplement specialist
        """
        }
        
        # Get agent-specific instructions or default to general
        specific = agent_specific.get(agent_type, agent_specific["general"])
        
        # Combine common and specific instructions
        full_instructions = common_instructions + "\n" + specific
        
        return full_instructions.strip()

    async def initialize_orchestrator(self) -> None:
        """
        Initialize the agent orchestrator and pre-load user context.
        
        This method must be called before connecting to a LiveKit room to ensure
        fast response times. It performs the following steps:
        1. Creates an async database session
        2. Loads user context from the database
        3. Initializes the AgentOrchestrator in voice mode
        4. Warms up the LLM connection with a dummy call
        
        Pre-loading context and warming up the LLM connection ensures the agent
        can respond within the <2 second latency requirement.
        
        Raises:
            ValueError: If user profile not found in database
            Exception: If orchestrator initialization fails
        
        Example:
            >>> agent = FitnessVoiceAgent(user_id="user-123")
            >>> await agent.initialize_orchestrator()
            >>> assert agent.orchestrator is not None
            >>> assert agent.user_context is not None
        """
        from app.db.session import AsyncSessionLocal
        from app.services.context_loader import load_agent_context
        
        logger.info(f"Initializing orchestrator for user {self.user_id}")
        
        try:
            # Create async database session
            async with AsyncSessionLocal() as db_session:
                # Step 1: Load user context from database
                self.user_context = await load_agent_context(
                    db=db_session,
                    user_id=self.user_id,
                    include_history=True
                )
                
                logger.info(
                    f"Loaded context for user {self.user_id}: "
                    f"fitness_level={self.user_context.fitness_level}, "
                    f"primary_goal={self.user_context.primary_goal}"
                )
                
                # Step 2: Initialize AgentOrchestrator in voice mode
                self.orchestrator = AgentOrchestrator(
                    db_session=db_session,
                    mode="voice"
                )
                
                logger.info(f"AgentOrchestrator initialized in voice mode")
                
                # Step 3: Pre-warm LLM connection to reduce first-query latency
                await self.orchestrator.warm_up()
                
                logger.info(
                    f"Orchestrator initialization complete for user {self.user_id}"
                )
                
        except ValueError as e:
            # User profile not found
            logger.error(
                f"Failed to load user context for {self.user_id}: {e}"
            )
            raise
        except Exception as e:
            # Other initialization errors
            logger.error(
                f"Failed to initialize orchestrator for {self.user_id}: {e}",
                exc_info=True
            )
            raise

    @function_tool()
    async def get_todays_workout(self) -> str:
        """
        Get today's workout plan from cached user context.
        
        This function tool provides quick access to the user's workout plan
        without making database queries. It returns a formatted string with
        the workout name and exercises for easy voice delivery.
        
        Use this tool when the user asks about:
        - "What's my workout today?"
        - "What exercises should I do?"
        - "Show me today's workout"
        
        Returns:
            str: Formatted workout description or error message
        
        Example:
            >>> # User asks: "What's my workout today?"
            >>> result = await agent.get_todays_workout()
            >>> # Returns: "Today's workout is Upper Body Push..."
        """
        try:
            # Check if context is loaded
            if self.user_context is None:
                logger.warning(
                    f"get_todays_workout called but context not loaded for user {self.user_id}"
                )
                return (
                    "I'm having trouble accessing your workout plan right now. "
                    "Please try again in a moment."
                )
            
            # Get workout plan from cached context
            workout_plan = self.user_context.current_workout_plan
            
            # Check if workout plan exists
            if not workout_plan or not workout_plan.get("exercises"):
                return (
                    "I don't see a workout plan set up for you yet. "
                    "Would you like me to help create one?"
                )
            
            # Format workout as readable string
            workout_name = workout_plan.get("name", "Your workout")
            exercises = workout_plan.get("exercises", [])
            
            # Build response
            response_parts = [f"Today's workout is {workout_name}."]
            
            if exercises:
                response_parts.append("Here are your exercises:")
                for idx, exercise in enumerate(exercises, 1):
                    exercise_name = exercise.get("name", "Unknown exercise")
                    sets = exercise.get("sets", "")
                    reps = exercise.get("reps", "")
                    
                    if sets and reps:
                        response_parts.append(
                            f"{idx}. {exercise_name}: {sets} sets of {reps} reps"
                        )
                    else:
                        response_parts.append(f"{idx}. {exercise_name}")
            
            result = " ".join(response_parts)
            
            logger.info(
                f"get_todays_workout returned workout for user {self.user_id}: "
                f"{workout_name}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error in get_todays_workout for user {self.user_id}: {e}",
                exc_info=True
            )
            return (
                "I encountered an error retrieving your workout. "
                "Please try asking again."
            )

    @function_tool()
    async def get_todays_meals(self) -> str:
        """
        Get today's meal plan from cached user context.
        
        This function tool provides quick access to the user's meal plan
        without making database queries. It returns meal data as a JSON string
        for structured information delivery.
        
        Use this tool when the user asks about:
        - "What should I eat today?"
        - "What's on my meal plan?"
        - "Show me today's meals"
        
        Returns:
            str: JSON string with meal plan data or error message
        
        Example:
            >>> # User asks: "What should I eat today?"
            >>> result = await agent.get_todays_meals()
            >>> # Returns JSON with breakfast, lunch, dinner, snacks
        """
        import json
        
        try:
            # Check if context is loaded
            if self.user_context is None:
                logger.warning(
                    f"get_todays_meals called but context not loaded for user {self.user_id}"
                )
                return (
                    "I'm having trouble accessing your meal plan right now. "
                    "Please try again in a moment."
                )
            
            # Get meal plan from cached context
            meal_plan = self.user_context.current_meal_plan
            
            # Check if meal plan exists
            if not meal_plan or not meal_plan.get("meals"):
                return (
                    "I don't see a meal plan set up for you yet. "
                    "Would you like me to help create one?"
                )
            
            # Format meal plan as JSON string
            meals = meal_plan.get("meals", [])
            
            # Build structured response
            meal_data = {
                "plan_name": meal_plan.get("name", "Your meal plan"),
                "meals": []
            }
            
            for meal in meals:
                meal_info = {
                    "meal_type": meal.get("meal_type", "Unknown"),
                    "name": meal.get("name", ""),
                    "calories": meal.get("calories", 0),
                    "protein_g": meal.get("protein_g", 0),
                    "carbs_g": meal.get("carbs_g", 0),
                    "fat_g": meal.get("fat_g", 0)
                }
                meal_data["meals"].append(meal_info)
            
            # Convert to JSON string
            result = json.dumps(meal_data, indent=2)
            
            logger.info(
                f"get_todays_meals returned meal plan for user {self.user_id}: "
                f"{len(meals)} meals"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error in get_todays_meals for user {self.user_id}: {e}",
                exc_info=True
            )
            return (
                "I encountered an error retrieving your meal plan. "
                "Please try asking again."
            )

    @function_tool()
    async def log_workout_set(
        self,
        exercise: str,
        reps: int,
        weight: float
    ) -> str:
        """
        Log a completed workout set for the user.
        
        This function tool queues workout set data for asynchronous database
        persistence. It returns an immediate confirmation without waiting for
        the database write, ensuring non-blocking voice interactions.
        
        Use this tool when the user reports completing a set:
        - "I just did 10 reps of bench press at 135 pounds"
        - "Log 12 squats at 185"
        - "Completed 8 deadlifts with 225 pounds"
        
        Args:
            exercise: Name of the exercise (e.g., "Bench Press", "Squats")
            reps: Number of repetitions completed
            weight: Weight used in kilograms (will be converted if needed)
        
        Returns:
            str: Immediate confirmation message
        
        Example:
            >>> # User says: "I just did 10 bench press at 135 pounds"
            >>> result = await agent.log_workout_set("Bench Press", 10, 61.2)
            >>> # Returns: "Logged 10 reps of Bench Press at 61.2 kg. Great work!"
        """
        try:
            # Create log entry with timestamp
            log_entry = {
                "exercise": exercise,
                "reps": reps,
                "weight": weight,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Queue entry for async processing
            await self._log_queue.put(log_entry)
            
            logger.info(
                f"Queued workout log for user {self.user_id}: "
                f"{exercise} - {reps} reps @ {weight} kg"
            )
            
            # Return immediate confirmation
            return (
                f"Logged {reps} reps of {exercise} at {weight} kg. "
                f"Great work! Keep it up!"
            )
            
        except Exception as e:
            logger.error(
                f"Error in log_workout_set for user {self.user_id}: {e}",
                exc_info=True
            )
            return (
                "I had trouble logging that set. "
                "Don't worry, you can tell me again and I'll make sure to record it."
            )

    @function_tool()
    async def ask_specialist_agent(
        self,
        query: str,
        specialist: str
    ) -> str:
        """
        Delegate complex queries to specialized agents via the orchestrator.
        
        This function tool routes queries that require detailed analysis or
        specialized knowledge to the appropriate LangChain agent. It handles
        complex workout programming, detailed nutrition planning, and supplement
        guidance that goes beyond simple data retrieval.
        
        Use this tool for complex questions requiring:
        - Detailed workout plan modifications
        - Nutrition analysis and meal planning
        - Supplement protocols and guidance
        - Progress analysis and adjustments
        
        Args:
            query: The user's complex question
            specialist: Agent type - must be one of: "workout", "diet", "supplement"
        
        Returns:
            str: Response from the specialized agent or error message
        
        Example:
            >>> # User asks: "Should I increase my protein intake for muscle gain?"
            >>> result = await agent.ask_specialist_agent(
            ...     "Should I increase my protein intake for muscle gain?",
            ...     "diet"
            ... )
            >>> # Returns detailed nutrition guidance from diet specialist
        """
        try:
            # Validate specialist type
            valid_specialists = ["workout", "diet", "supplement"]
            if specialist not in valid_specialists:
                logger.warning(
                    f"Invalid specialist type '{specialist}' requested by user {self.user_id}"
                )
                return (
                    f"I can only connect you with workout, diet, or supplement specialists. "
                    f"Please specify one of those."
                )
            
            # Check if orchestrator is initialized
            if self.orchestrator is None:
                logger.error(
                    f"ask_specialist_agent called but orchestrator not initialized "
                    f"for user {self.user_id}"
                )
                return (
                    "I'm having trouble connecting to the specialist right now. "
                    "Please try again in a moment."
                )
            
            logger.info(
                f"Routing query to {specialist} specialist for user {self.user_id}: "
                f"{query[:50]}..."
            )
            
            # Route query to orchestrator with voice_mode=True
            from app.services.agent_orchestrator import AgentType
            
            # Map specialist string to AgentType enum
            agent_type_map = {
                "workout": AgentType.WORKOUT,
                "diet": AgentType.DIET,
                "supplement": AgentType.SUPPLEMENT
            }
            
            agent_type = agent_type_map[specialist]
            
            # Call orchestrator
            response = await self.orchestrator.route_query(
                user_id=self.user_id,
                query=query,
                agent_type=agent_type,
                voice_mode=True
            )
            
            logger.info(
                f"Received response from {specialist} specialist for user {self.user_id}"
            )
            
            # Return response content
            return response.content
            
        except Exception as e:
            logger.error(
                f"Error in ask_specialist_agent for user {self.user_id}: {e}",
                exc_info=True
            )
            return (
                "I'm having trouble getting an answer to that question right now. "
                "Could you try rephrasing it, or ask me something else?"
            )

    async def start_log_worker(self) -> None:
        """
        Start the background log worker task.
        
        Creates an asyncio task that processes workout log entries from the queue
        and persists them to the database asynchronously. This ensures workout
        logging doesn't block voice interactions.
        
        The log worker runs continuously in the background until the agent is
        cleaned up via the cleanup() method.
        
        Example:
            >>> agent = FitnessVoiceAgent(user_id="user-123")
            >>> await agent.initialize_orchestrator()
            >>> await agent.start_log_worker()
            >>> # Log worker is now running in background
        """
        logger.info(f"Starting log worker for user {self.user_id}")
        
        # Create asyncio task for _log_worker
        self._log_worker_task = asyncio.create_task(self._log_worker())
        
        logger.info(f"Log worker started for user {self.user_id}")

    async def _log_worker(self) -> None:
        """
        Background worker that processes workout log entries from the queue.
        
        This method runs in an infinite loop, continuously monitoring the log queue
        for new entries. When an entry is found, it:
        1. Retrieves the entry from the queue
        2. Creates an async database session
        3. Creates a WorkoutLog instance
        4. Persists to the database
        5. Marks the queue task as done
        
        The worker handles errors gracefully:
        - asyncio.CancelledError: Breaks the loop for graceful shutdown
        - Other exceptions: Logs error and continues processing
        
        This ensures workout logging is non-blocking and resilient to errors.
        """
        from app.db.session import AsyncSessionLocal
        from app.models.workout_log import WorkoutLog
        
        logger.info(f"Log worker running for user {self.user_id}")
        
        while True:
            try:
                # Await log entry from queue
                log_entry = await self._log_queue.get()
                
                logger.debug(
                    f"Log worker processing entry for user {self.user_id}: "
                    f"{log_entry['exercise']}"
                )
                
                # Create async database session
                async with AsyncSessionLocal() as db:
                    # Create WorkoutLog instance from entry
                    log = WorkoutLog(
                        user_id=UUID(self.user_id),
                        exercise=log_entry["exercise"],
                        reps=log_entry["reps"],
                        weight_kg=log_entry["weight"],
                        logged_at=datetime.fromisoformat(log_entry["timestamp"])
                    )
                    
                    # Add to session and commit
                    db.add(log)
                    await db.commit()
                    
                    logger.info(
                        f"Log worker persisted entry for user {self.user_id}: "
                        f"{log_entry['exercise']} - {log_entry['reps']} reps @ "
                        f"{log_entry['weight']} kg"
                    )
                
                # Mark queue task as done
                self._log_queue.task_done()
                
            except asyncio.CancelledError:
                # Graceful shutdown requested
                logger.info(
                    f"Log worker cancelled for user {self.user_id}, shutting down"
                )
                break
                
            except Exception as e:
                # Log error and continue processing
                logger.error(
                    f"Log worker error for user {self.user_id}: {e}",
                    exc_info=True
                )
                # Mark task as done even on error to prevent queue blocking
                self._log_queue.task_done()
                # Continue processing next entry

    async def cleanup(self) -> None:
        """
        Clean up agent resources and stop background tasks.
        
        This method should be called when the agent session completes to ensure
        proper resource cleanup. It:
        1. Cancels the log worker task if it exists
        2. Waits for the task to complete with CancelledError handling
        3. Logs cleanup completion
        
        The cleanup is graceful and handles cases where the log worker was never
        started or has already completed.
        
        Example:
            >>> agent = FitnessVoiceAgent(user_id="user-123")
            >>> await agent.start_log_worker()
            >>> # ... agent session runs ...
            >>> await agent.cleanup()
            >>> # All resources released
        """
        logger.info(f"Cleaning up agent for user {self.user_id}")
        
        # Cancel log worker task if it exists
        if self._log_worker_task is not None:
            logger.info(f"Cancelling log worker for user {self.user_id}")
            
            # Cancel the task
            self._log_worker_task.cancel()
            
            try:
                # Await task with CancelledError handling
                await self._log_worker_task
            except asyncio.CancelledError:
                # Expected when cancelling task
                logger.info(f"Log worker cancelled successfully for user {self.user_id}")
            except Exception as e:
                # Unexpected error during cleanup
                logger.error(
                    f"Error during log worker cleanup for user {self.user_id}: {e}",
                    exc_info=True
                )
        
        logger.info(f"Cleanup complete for user {self.user_id}")

# End of FitnessVoiceAgent class - disabled for testing (if False block)


# ============================================================================
# HELPER FUNCTIONS - Used by both test and production agents
# ============================================================================

def _get_configured_stt():
    """
    Get configured STT instance.
    
    Returns:
        STT instance configured for Deepgram
    """
    return deepgram.STT(
        model="nova-2-general",
        language="en-US"
    )


def _get_configured_tts():
    """
    Get configured TTS instance.
    
    Returns:
        TTS instance configured for Cartesia
    """
    return cartesia.TTS(
        voice="248be419-c632-4f23-adf1-5324ed7dbf1d"
    )


def _get_configured_llm():
    """
    Get configured LLM instance based on VOICE_LLM_PROVIDER setting.
    
    This helper function creates and returns an LLM instance configured for
    the voice agent based on the VOICE_LLM_PROVIDER setting. It supports
    OpenAI, Anthropic, and Google providers.
    
    The function configures the LLM with:
    - Temperature: 0.7 for balanced creativity
    - Model: Provider-specific model
    - API key: From settings
    
    Returns:
        LLM instance configured for the selected provider
    
    Raises:
        ValueError: If VOICE_LLM_PROVIDER is not supported
    """
    provider = settings.VOICE_LLM_PROVIDER.lower()
    
    if provider == "openai":
        # OpenAI GPT-4o - native support in LiveKit Agents SDK
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required when VOICE_LLM_PROVIDER is 'openai'"
            )
        
        logger.info("Configuring OpenAI GPT-4o for voice agent")
        
        return openai.LLM(
            model="gpt-4o",
            temperature=0.7
        )
    
    elif provider == "anthropic":
        # Anthropic Claude - may need OpenAI-compatible endpoint
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when VOICE_LLM_PROVIDER is 'anthropic'"
            )
        
        logger.info("Configuring Anthropic Claude for voice agent")
        
        # Note: LiveKit Agents SDK may not have native Anthropic support
        # Using OpenAI-compatible endpoint if available
        return openai.LLM(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            base_url="https://api.anthropic.com/v1"
        )
    
    elif provider == "google":
        # Google Gemini - Use the official LiveKit Google plugin
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is required when VOICE_LLM_PROVIDER is 'google'"
            )
        
        logger.info("Configuring Google Gemini for voice agent via LiveKit Google Plugin")
        
        return google.LLM(
            api_key=settings.GOOGLE_API_KEY
        )
    
    else:
        raise ValueError(
            f"Unsupported VOICE_LLM_PROVIDER: {provider}. "
            f"Supported providers: openai, anthropic, google"
        )


async def entrypoint(ctx: JobContext) -> None:
    """
    Main entrypoint function for the voice agent worker.
    
    This function is called by the LiveKit agent worker when a room connection
    is requested. It handles the complete lifecycle of a voice agent session.
    
    The modern LiveKit Agents SDK (v1.x) uses AgentSession which handles:
    - Connection management
    - STT/TTS/LLM pipeline
    - Turn detection and interruptions
    - Session lifecycle
    
    Args:
        ctx: JobContext from LiveKit containing room and metadata
    """
    logger.info(f"Voice agent entrypoint called for room {ctx.room.name}")
    
    try:
        # Step 1: Fetch room metadata from LiveKit API
        livekit_api = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        
        # Fetch room details
        response = await livekit_api.room.list_rooms(
            api.ListRoomsRequest(names=[ctx.room.name])
        )
        
        if not response.rooms:
            logger.error(f"Room {ctx.room.name} not found in LiveKit")
            return
        
        room_info = response.rooms[0]
        metadata_str = room_info.metadata
        
        if not metadata_str:
            logger.error(f"No metadata found in room {ctx.room.name}")
            return
        
        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse room metadata: {e}")
            return
        
        # Step 2: Extract user_id and agent_type from metadata
        user_id = metadata.get("user_id")
        agent_type = metadata.get("agent_type", "general")
        
        # Validate user_id exists
        if not user_id:
            logger.error(
                f"user_id missing from room metadata in room {ctx.room.name}"
            )
            return
        
        logger.info(
            f"Starting voice agent session for user {user_id} "
            f"with agent_type '{agent_type}'"
        )
        
        # ========================================================================
        # TESTING MODE: Using SimpleTestAgent instead of FitnessVoiceAgent
        # ========================================================================
        # To restore full functionality, uncomment the FitnessVoiceAgent code above
        # and replace the SimpleTestAgent() below with the commented code
        
        logger.info("Using SimpleTestAgent for testing LiveKit voice pipeline")
        
        # Create simple test agent (no database, no orchestrator)
        test_agent = SimpleTestAgent()
        
        """
        # PRODUCTION CODE - Uncomment to restore full functionality:
        
        # Step 3: Create FitnessVoiceAgent instance
        # This creates the agent with STT, LLM, TTS, VAD already configured
        fitness_agent = FitnessVoiceAgent(user_id=user_id, agent_type=agent_type)
        
        # Step 4: Pre-load orchestrator and context before connecting
        try:
            await fitness_agent.initialize_orchestrator()
        except ValueError as e:
            # User profile not found or incomplete
            logger.warning(
                f"Could not load full context for user {user_id}: {e}. "
                f"Will connect and inform user to complete onboarding."
            )
            
            # Connect to room without full context
            await ctx.connect()
            
            # Send a message to the user
            await ctx.room.local_participant.publish_data(
                payload=json.dumps({
                    "type": "error",
                    "message": "Please complete your onboarding profile before using voice sessions. "
                               "You can do this from the Profile page in the app."
                }).encode('utf-8'),
                reliable=True
            )
            
            logger.info(f"Informed user {user_id} about incomplete profile")
            return
        
        # Step 5: Start background log worker
        await fitness_agent.start_log_worker()
        
        logger.info("FitnessVoiceAgent initialized and log worker started")
        
        # Step 6: Setup cleanup handler for when room disconnects
        @ctx.room.on("disconnected")
        def on_room_disconnected():
            # Handle cleanup when room disconnects
            logger.info(f"Room disconnected for user {user_id}, triggering cleanup")
            # Schedule cleanup as a task since this is a sync callback
            asyncio.create_task(fitness_agent.cleanup())
        """
        
        # Step 7: Connect to the room and wait for a participant
        await ctx.connect()
        logger.info(f"Connected to room {ctx.room.name}")
        
        # Wait for a participant to join (this is important!)
        await ctx.wait_for_participant()
        logger.info(f"Participant joined room {ctx.room.name}")
        
        # Step 8: Create AgentSession with configured components
        # AgentSession manages the entire voice AI pipeline
        logger.info("Creating AgentSession")
        
        session = AgentSession(
            vad=silero.VAD.load(),
            stt=_get_configured_stt(),
            llm=_get_configured_llm(),
            tts=_get_configured_tts(),
        )
        
        logger.info("AgentSession created")
        
        # Step 9: Start the session with the agent
        logger.info(f"Starting voice session for user {user_id}")
        
        await session.start(
            agent=test_agent,  # Using SimpleTestAgent for testing
            # agent=fitness_agent,  # Uncomment for production
            room=ctx.room
        )
        
        # Step 10: Generate an initial greeting to the user
        # This triggers the agent to speak first
        await session.generate_reply(
            instructions="Greet the user warmly and introduce yourself as a test fitness assistant."
        )
        
        logger.info(f"Voice session started successfully for user {user_id}")
        
    except Exception as e:
        logger.error(
            f"Error in voice agent entrypoint: {e}",
            exc_info=True
        )
        raise


# Create AgentServer instance at module level for multiprocessing compatibility
server = AgentServer()


@server.rtc_session()
async def rtc_session_handler(ctx: JobContext):
    """
    RTC session handler for voice agent worker.
    
    This handler is called by the LiveKit agent worker when a room connection
    is requested. It wraps the entrypoint function to handle the complete
    lifecycle of a voice agent session.
    
    Args:
        ctx: JobContext from LiveKit containing room and metadata
    """
    await entrypoint(ctx)


# Main worker process entry point
if __name__ == "__main__":
    """
    Main entry point for the LiveKit voice agent worker process.
    
    This block runs when the module is executed directly (not imported).
    It configures and starts the LiveKit agent worker using the AgentServer API.
    
    The worker listens for room connection requests from the LiveKit server
    and invokes the entrypoint function for each new session.
    
    Usage:
        python app/livekit_agents/voice_agent_worker.py dev
        python app/livekit_agents/voice_agent_worker.py start
    
    Environment Variables Required:
        - LIVEKIT_URL: LiveKit server URL
        - LIVEKIT_API_KEY: LiveKit API key
        - LIVEKIT_API_SECRET: LiveKit API secret
        - DEEPGRAM_API_KEY: Deepgram STT API key
        - CARTESIA_API_KEY: Cartesia TTS API key
        - VOICE_LLM_PROVIDER: LLM provider (openai, anthropic, google)
        - OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY: LLM API key
        - DATABASE_URL: PostgreSQL connection string
        - REDIS_URL: Redis connection string
    """
    logger.info("Starting LiveKit voice agent worker")
    logger.info(f"Worker configuration: num_idle_workers={settings.LIVEKIT_WORKER_NUM_IDLE}")
    logger.info(f"LLM provider: {settings.VOICE_LLM_PROVIDER}")
    
    # Run the agent server with CLI
    cli.run_app(server)
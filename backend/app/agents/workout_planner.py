"""
Workout Planner Agent for exercise guidance, form demonstrations, and workout logging.

This module provides the WorkoutPlannerAgent that handles all workout-related queries
including exercise plans, form guidance, demonstrations, and workout logging.
"""

import json
import logging
from datetime import datetime, date
from typing import AsyncIterator, List, Literal

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse
from app.agents.onboarding_tools import call_onboarding_step
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, ExerciseLibrary
from app.models.preferences import WorkoutSchedule

logger = logging.getLogger(__name__)


class WorkoutPlannerAgent(BaseAgent):
    """
    Specialized agent for workout planning and exercise guidance.
    
    This agent handles:
    - Retrieving current workout plans
    - Providing exercise demonstrations
    - Logging workout progress
    - Suggesting workout modifications
    
    The agent provides motivating but realistic guidance and adjusts
    recommendations based on user's fitness level and energy state.
    """
    
    async def process_text(self, query: str) -> AgentResponse:
        """
        Process a text query and return a detailed response with tool calling.
        
        Builds messages with full conversation history, creates a tool-calling
        agent, and returns a structured AgentResponse with markdown formatting.
        
        Args:
            query: User's text query
            
        Returns:
            AgentResponse with content, agent type, tools used, and metadata
        """
        # Build messages with full history for text mode
        messages = self._build_messages(query, voice_mode=False)
        
        # Get tools for this agent
        tools = self.get_tools()
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        # Call LLM with tools
        response = await llm_with_tools.ainvoke(messages)
        
        # Track which tools were called
        tools_used = []
        
        # If LLM wants to call tools, execute them
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tools_used.append(tool_call['name'])
                
                # Find and execute the tool
                for t in tools:
                    if t.name == tool_call['name']:
                        try:
                            tool_result = await t.ainvoke(tool_call['args'])
                            # Add tool result to messages and get final response
                            messages.append(response)
                            messages.append(HumanMessage(content=f"Tool result: {tool_result}"))
                            response = await self.llm.ainvoke(messages)
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            response.content = f"I encountered an error while processing your request. Please try again."
        
        # Return structured response
        return AgentResponse(
            content=response.content,
            agent_type="workout",
            tools_used=tools_used,
            metadata={
                "mode": "text",
                "user_id": self.context.user_id,
                "fitness_level": self.context.fitness_level,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def process_voice(self, query: str) -> str:
        """
        Process a voice query and return a concise response.
        
        Builds messages with limited conversation history for low-latency,
        calls the LLM without tools, and returns a plain string suitable
        for text-to-speech (under 75 words).
        
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
    
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """
        Stream response chunks for real-time display.
        
        Builds messages and uses the LLM's streaming capability to yield
        response chunks as they are generated.
        
        Args:
            query: User's query
            
        Yields:
            str: Response chunks as they are generated
        """
        # Build messages
        messages = self._build_messages(query, voice_mode=False)
        
        # Stream response chunks
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    def get_tools(self) -> List:
        """
        Get the list of tools available to the workout planner agent.
        
        Returns:
            List: List of LangChain tools for workout operations
        """
        # Create closures to pass context and db_session to tools
        context = self.context
        db_session = self.db_session
        
        @tool
        async def get_current_workout() -> str:
            """Get today's workout plan for the user.
            
            Returns:
                JSON string with workout details including exercises, sets, reps, and rest periods
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Get today's day of week (0=Monday, 6=Sunday)
                today = date.today().weekday()
                
                # Query workout schedule for today
                stmt = select(WorkoutSchedule).where(
                    WorkoutSchedule.day_of_week == today
                ).join(
                    WorkoutSchedule.profile
                ).where(
                    WorkoutSchedule.profile.has(user_id=context.user_id)
                )
                
                result = await db_session.execute(stmt)
                schedule = result.scalar_one_or_none()
                
                if not schedule:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No workout scheduled for today. It's a rest day!"
                        }
                    })
                
                # Get workout plan for user
                stmt = select(WorkoutPlan).where(
                    WorkoutPlan.user_id == context.user_id,
                    WorkoutPlan.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                workout_plan = result.scalar_one_or_none()
                
                if not workout_plan:
                    return json.dumps({
                        "success": False,
                        "error": "No workout plan found for user"
                    })
                
                # Get workout day matching today
                # Map day_of_week to day_number (assuming 1-based day_number)
                day_number = today + 1
                
                workout_day = None
                for day in workout_plan.workout_days:
                    if day.day_number == day_number and day.deleted_at is None:
                        workout_day = day
                        break
                
                if not workout_day:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No specific workout programmed for today"
                        }
                    })
                
                # Build exercise list
                exercises = []
                for exercise in workout_day.exercises:
                    if exercise.deleted_at is None:
                        exercise_data = {
                            "name": exercise.exercise_library.exercise_name,
                            "sets": exercise.sets,
                            "reps": exercise.reps_target or f"{exercise.reps_min}-{exercise.reps_max}",
                            "weight_kg": float(exercise.weight_kg) if exercise.weight_kg else None,
                            "rest_seconds": exercise.rest_seconds,
                            "notes": exercise.notes
                        }
                        exercises.append(exercise_data)
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "day_name": workout_day.day_name,
                        "workout_type": workout_day.workout_type,
                        "muscle_groups": workout_day.muscle_groups,
                        "estimated_duration_minutes": workout_day.estimated_duration_minutes,
                        "exercises": exercises
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "workout_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_current_workout: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve workout plan. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_current_workout: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def show_exercise_demo(exercise_name: str) -> str:
            """Get GIF demonstration URL for an exercise.
            
            Args:
                exercise_name: Name of the exercise to demonstrate
                
            Returns:
                JSON string with GIF URL or error message
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Query exercise library for the exercise
                stmt = select(ExerciseLibrary).where(
                    ExerciseLibrary.exercise_name.ilike(f"%{exercise_name}%"),
                    ExerciseLibrary.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                exercise = result.scalar_one_or_none()
                
                if not exercise:
                    return json.dumps({
                        "success": False,
                        "error": f"Exercise '{exercise_name}' not found in library"
                    })
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "exercise_name": exercise.exercise_name,
                        "gif_url": exercise.gif_url,
                        "video_url": exercise.video_url,
                        "description": exercise.description,
                        "instructions": exercise.instructions,
                        "difficulty_level": exercise.difficulty_level,
                        "primary_muscle_group": exercise.primary_muscle_group
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "workout_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in show_exercise_demo: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve exercise demonstration. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in show_exercise_demo: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def log_set_completion(exercise: str, reps: int, weight: float) -> str:
            """Log a completed workout set.
            
            Args:
                exercise: Exercise name
                reps: Number of repetitions completed
                weight: Weight used in kg
                
            Returns:
                JSON string with confirmation message
            """
            try:
                # Note: WorkoutLog model doesn't exist yet in the schema
                # For now, return a success message indicating the log would be recorded
                # This will need to be implemented when WorkoutLog model is added
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "message": f"Logged: {exercise} - {reps} reps @ {weight}kg",
                        "exercise": exercise,
                        "reps": reps,
                        "weight_kg": weight,
                        "logged_at": datetime.utcnow().isoformat()
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "workout_planner_agent",
                        "note": "WorkoutLog model pending implementation"
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in log_set_completion: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to log workout set. Please try again."
                })
        
        @tool
        async def suggest_workout_modification(reason: str, intensity_change: str) -> str:
            """Suggest modifications to current workout based on user needs.
            
            Args:
                reason: Why modification is needed (e.g., "low energy", "injury", "time constraint")
                intensity_change: Desired intensity change - "increase", "decrease", or "maintain"
                
            Returns:
                JSON string with modification suggestions
            """
            try:
                # Generate suggestions based on context and reason
                fitness_level = context.fitness_level
                energy_level = context.energy_level
                primary_goal = context.primary_goal
                
                suggestions = []
                
                # Base suggestions on intensity change
                if intensity_change == "decrease":
                    suggestions.append("Reduce weight by 10-15%")
                    suggestions.append("Decrease sets from 4 to 3")
                    suggestions.append("Increase rest periods by 30 seconds")
                    suggestions.append("Focus on form over weight")
                elif intensity_change == "increase":
                    suggestions.append("Increase weight by 5-10%")
                    suggestions.append("Add an extra set to key exercises")
                    suggestions.append("Reduce rest periods by 15 seconds")
                    suggestions.append("Add drop sets to final set")
                else:  # maintain
                    suggestions.append("Keep current weight and volume")
                    suggestions.append("Focus on tempo and control")
                    suggestions.append("Ensure full range of motion")
                
                # Add context-specific suggestions
                if energy_level == "low":
                    suggestions.append("Consider shorter workout duration")
                    suggestions.append("Prioritize compound movements")
                
                if fitness_level == "beginner":
                    suggestions.append("Maintain proper form throughout")
                    suggestions.append("Don't rush between sets")
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "reason": reason,
                        "intensity_change": intensity_change,
                        "suggestions": suggestions,
                        "context": {
                            "fitness_level": fitness_level,
                            "energy_level": energy_level,
                            "primary_goal": primary_goal
                        }
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "workout_planner_agent"
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in suggest_workout_modification: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to generate workout modifications. Please try again."
                })
        
        # Create onboarding tools using @tool decorator
        @tool
        async def save_fitness_level_tool(fitness_level: str) -> str:
            """Save user's fitness level during onboarding (State 1).
            
            Args:
                fitness_level: User's current fitness level - must be "beginner", "intermediate", or "advanced"
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_fitness_level(fitness_level)
            return json.dumps(result)
        
        @tool
        async def save_fitness_goals_tool(goals: list) -> str:
            """Save user's fitness goals during onboarding (State 2).
            
            Args:
                goals: List of goal objects with goal_type and priority
                       Example: [{"goal_type": "fat_loss", "priority": 1}]
                       Valid goal_types: "fat_loss", "muscle_gain", "general_fitness"
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_fitness_goals(goals)
            return json.dumps(result)
        
        @tool
        async def save_workout_constraints_tool(
            equipment: list,
            injuries: list,
            limitations: list,
            target_weight_kg: float = None,
            target_body_fat_percentage: float = None
        ) -> str:
            """Save workout constraints and optional targets during onboarding (State 3).
            
            Args:
                equipment: Available equipment list (e.g., ["dumbbells", "resistance_bands"])
                injuries: Current injuries list (can be empty)
                limitations: Physical limitations list (can be empty)
                target_weight_kg: Optional target weight in kg (30-300)
                target_body_fat_percentage: Optional target body fat % (1-50)
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_workout_constraints(
                equipment=equipment,
                injuries=injuries,
                limitations=limitations,
                target_weight_kg=target_weight_kg,
                target_body_fat_percentage=target_body_fat_percentage
            )
            return json.dumps(result)
        
        return [
            get_current_workout,
            show_exercise_demo,
            log_set_completion,
            suggest_workout_modification,
            save_fitness_level_tool,
            save_fitness_goals_tool,
            save_workout_constraints_tool
        ]
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the workout planner agent.
        
        Creates a specialized system prompt that includes user context,
        workout expertise, and behavioral guidelines. The prompt varies
        based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        base_prompt = f"""You are a professional workout planning assistant for the Shuren fitness coaching system.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

Your Expertise:
- Exercise programming and progression
- Form guidance and technique
- Workout modifications and adaptations
- Exercise demonstrations and alternatives

Guidelines:
- Be motivating but realistic about expectations
- Reference the user's specific workout plan when available
- Adjust recommendations based on their energy level and fitness level
- Never provide medical advice or diagnose injuries
- Use tools to fetch workout data or log progress when needed
- Encourage proper form over heavy weight
- Promote sustainable, long-term fitness habits

Available Tools:
- get_current_workout: Retrieve today's workout plan
- show_exercise_demo: Get exercise demonstration GIFs and instructions
- log_set_completion: Record completed sets with reps and weight
- suggest_workout_modification: Generate workout adjustments based on needs
"""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction (under 30 seconds when spoken, approximately 75 words)."
        else:
            base_prompt += "\n\nIMPORTANT: Provide detailed explanations with markdown formatting for text interaction. Use headers, lists, and emphasis to improve readability."
        
        return base_prompt

    async def save_fitness_level(
        self,
        fitness_level: Literal["beginner", "intermediate", "advanced"]
    ) -> dict:
        """Save user's fitness level (State 1).
        
        This tool is used during onboarding to capture the user's current
        fitness level, which determines workout intensity and progression.
        
        Args:
            fitness_level: User's current fitness level
        
        Returns:
            Success/error response dict with structure:
            - success (bool): Whether the operation succeeded
            - message (str): Success message or error description
            - current_state (int): Current onboarding state (if success)
            - next_state (int|None): Next state number (if success)
            - error (str): Error message (if failed)
            - field (str): Field that caused error (if validation failed)
            - error_code (str): Error code for categorization (if failed)
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=1,
            data={"fitness_level": fitness_level},
            agent_type="workout_planning"
        )
    
    async def save_fitness_goals(
        self,
        goals: list[dict]
    ) -> dict:
        """Save user's fitness goals (State 2).
        
        This tool is used during onboarding to capture the user's fitness
        goals, which guide workout plan creation and progression tracking.
        
        Args:
            goals: List of goal objects with goal_type and priority
                   Example: [{"goal_type": "fat_loss", "priority": 1}]
                   Valid goal_types: "fat_loss", "muscle_gain", "general_fitness"
        
        Returns:
            Success/error response dict (see save_fitness_level for structure)
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=2,
            data={"goals": goals},
            agent_type="workout_planning"
        )
    
    async def save_workout_constraints(
        self,
        equipment: list[str],
        injuries: list[str],
        limitations: list[str],
        target_weight_kg: float | None = None,
        target_body_fat_percentage: float | None = None
    ) -> dict:
        """Save workout constraints and optional targets (State 3).
        
        This tool is used during onboarding to capture equipment availability,
        physical constraints, and optional target metrics. This information
        ensures workouts are safe and appropriate for the user.
        
        Args:
            equipment: Available equipment (e.g., ["dumbbells", "resistance_bands"])
            injuries: Current injuries (can be empty list)
            limitations: Physical limitations (can be empty list)
            target_weight_kg: Optional target weight (30-300 kg)
            target_body_fat_percentage: Optional target body fat % (1-50)
        
        Returns:
            Success/error response dict (see save_fitness_level for structure)
        """
        data = {
            "equipment": equipment,
            "injuries": injuries,
            "limitations": limitations
        }
        
        if target_weight_kg is not None:
            data["target_weight_kg"] = target_weight_kg
        
        if target_body_fat_percentage is not None:
            data["target_body_fat_percentage"] = target_body_fat_percentage
        
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=3,
            data=data,
            agent_type="workout_planning"
        )

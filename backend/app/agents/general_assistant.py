"""
General Assistant Agent for motivation, casual conversation, and general queries.

This module provides the GeneralAssistantAgent that handles general fitness queries,
provides motivation, and manages casual conversation with a friendly, supportive tone.
"""

import json
import logging
from datetime import datetime
from typing import AsyncIterator, List

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse
from app.models.user import User
from app.models.profile import UserProfile
from app.models.workout import WorkoutPlan
from app.models.preferences import FitnessGoal
from app.services.workout_service import WorkoutService
from app.services.meal_service import MealService
from app.services.schedule_service import ScheduleService

logger = logging.getLogger(__name__)


class GeneralAssistantAgent(BaseAgent):
    """
    Specialized agent for general assistance, motivation, and casual conversation.
    
    This agent handles:
    - General fitness questions
    - Motivational messages based on progress
    - Casual conversation
    - General user statistics
    
    The agent maintains a friendly and supportive tone to encourage
    sustainable, long-term fitness habits.
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
                            if response not in messages:
                                messages.append(response)
                            messages.append(ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call['id']
                            ))
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            if response not in messages:
                                messages.append(response)
                            messages.append(ToolMessage(
                                content=f"Error executing tool: {e}",
                                tool_call_id=tool_call['id']
                            ))
            
            # Get final response after tools
            response = await self.llm.ainvoke(messages)
        
        # Return structured response
        return AgentResponse(
            content=response.content,
            agent_type="general",
            tools_used=tools_used,
            metadata={
                "mode": "text",
                "user_id": self.context.user_id,
                "fitness_level": self.context.fitness_level,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    
    def _get_agent_tools(self) -> List:
        """
        Get the list of tools available to the general assistant agent.
        
        Returns:
            List: List of LangChain tools for general operations
        """
        # Create closures to pass context and db_session to tools
        context = self.context
        db_session = self.db_session
        
        @tool
        async def get_user_stats() -> str:
            """Get general user statistics including profile info and fitness goals.
            
            Returns:
                JSON string with user statistics
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Get user profile
                stmt = select(UserProfile).where(
                    UserProfile.user_id == context.user_id,
                    UserProfile.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    return json.dumps({
                        "success": False,
                        "error": "User profile not found"
                    })
                
                # Get fitness goals
                goals = []
                for goal in profile.fitness_goals:
                    if goal.deleted_at is None:
                        goals.append({
                            "type": goal.goal_type,
                            "priority": goal.priority,
                            "target_value": float(goal.target_value) if goal.target_value else None,
                            "target_unit": goal.target_unit,
                            "target_date": goal.target_date.isoformat() if goal.target_date else None
                        })
                
                # Get workout plan info
                workout_plan_exists = False
                workout_days_per_week = 0
                
                stmt = select(WorkoutPlan).where(
                    WorkoutPlan.user_id == context.user_id,
                    WorkoutPlan.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                workout_plan = result.scalar_one_or_none()
                
                if workout_plan:
                    workout_plan_exists = True
                    workout_days_per_week = workout_plan.days_per_week
                
                # Get user info
                stmt = select(User).where(
                    User.id == context.user_id,
                    User.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                user = result.scalar_one_or_none()
                
                user_name = user.full_name if user else "User"
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "user_name": user_name,
                        "fitness_level": profile.fitness_level,
                        "goals": goals,
                        "has_workout_plan": workout_plan_exists,
                        "workout_days_per_week": workout_days_per_week,
                        "profile_created": profile.created_at.isoformat()
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_user_stats: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve user statistics. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_user_stats: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def provide_motivation() -> str:
            """Provide motivational message based on user context and progress.
            
            Returns:
                JSON string with motivational message
            """
            try:
                # Generate motivation based on context
                fitness_level = context.fitness_level
                primary_goal = context.primary_goal
                energy_level = context.energy_level
                
                # Build motivational messages based on context
                messages = []
                
                # Goal-specific motivation
                if primary_goal == "fat_loss":
                    messages.append("Every workout brings you closer to your fat loss goals!")
                    messages.append("Consistency is key - you're building sustainable habits.")
                elif primary_goal == "muscle_gain":
                    messages.append("Your dedication to muscle building is paying off!")
                    messages.append("Progressive overload and patience - you're on the right track.")
                elif primary_goal == "general_fitness":
                    messages.append("Your commitment to overall health is inspiring!")
                    messages.append("Fitness is a journey, not a destination - enjoy the process.")
                
                # Fitness level encouragement
                if fitness_level == "beginner":
                    messages.append("Starting your fitness journey takes courage - be proud!")
                    messages.append("Every expert was once a beginner. You're doing great!")
                elif fitness_level == "intermediate":
                    messages.append("Your progress shows your dedication - keep pushing!")
                    messages.append("You've built a solid foundation - time to level up!")
                elif fitness_level == "advanced":
                    messages.append("Your commitment to excellence is remarkable!")
                    messages.append("Leading by example - your discipline inspires others!")
                
                # Energy-based encouragement
                if energy_level == "low":
                    messages.append("Even on low energy days, showing up is a victory!")
                    messages.append("Listen to your body - rest is part of progress.")
                elif energy_level == "high":
                    messages.append("Great energy today - make the most of it!")
                    messages.append("Your positive energy is contagious - keep it up!")
                
                # General encouragement
                messages.append("You're stronger than you think!")
                messages.append("Progress, not perfection - you're doing amazing!")
                messages.append("Your future self will thank you for today's effort!")
                
                # Select a few messages
                import random
                selected_messages = random.sample(messages, min(3, len(messages)))
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "messages": selected_messages,
                        "context": {
                            "fitness_level": fitness_level,
                            "primary_goal": primary_goal,
                            "energy_level": energy_level
                        }
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in provide_motivation: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to generate motivation. Please try again."
                })
        
        @tool
        async def get_workout_info(target_date: str = None) -> str:
            """Get the workout plan for the user for a specific date.
            
            Args:
                target_date: Optional ISO format date string (e.g., '2023-12-25'). If not provided, returns today's plan.
            
            Returns:
                JSON string with workout details including exercises, sets, reps, and rest periods.
                If no workout scheduled, returns a rest day message.
            """
            try:
                result = await WorkoutService.get_workout_dict_for_date(
                    user_id=context.user_id,
                    db_session=db_session,
                    target_date=target_date
                )
                
                if result is None:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No workout scheduled for today. It's a rest day!"
                        }
                    })
                
                return json.dumps({
                    "success": True,
                    "data": result,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except ValueError as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_workout_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve workout information. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_workout_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def get_meal_info(target_date: str = None) -> str:
            """Get the meal plan for the user for a specific date.
            
            Args:
                target_date: Optional ISO format date string (e.g., '2023-12-25'). If not provided, returns today's plan.
            
            Returns:
                JSON string with meal details including dishes, timing, and nutritional information.
                If no meal plan configured, returns a helpful message.
            """
            try:
                result = await MealService.get_meal_plan_for_date(
                    user_id=context.user_id,
                    db_session=db_session,
                    target_date=target_date
                )
                
                if result is None:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No meal plan configured yet. Please complete your meal planning setup."
                        }
                    })
                
                return json.dumps({
                    "success": True,
                    "data": result,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except ValueError as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_meal_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve meal information. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_meal_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def get_schedule_info() -> str:
            """Get upcoming workout and meal schedules for the user.
            
            Returns:
                JSON string with upcoming schedules including days, times, and notification settings.
            """
            try:
                result = await ScheduleService.get_upcoming_schedule(
                    user_id=context.user_id,
                    db_session=db_session
                )
                
                return json.dumps({
                    "success": True,
                    "data": result,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except ValueError as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_schedule_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve schedule information. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_schedule_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def get_exercise_demo(exercise_name: str) -> str:
            """Get exercise demonstration details from the exercise library.
            
            Args:
                exercise_name: Name of the exercise to demonstrate
            
            Returns:
                JSON string with GIF URL, video URL, instructions, and difficulty level.
                If exercise not found, returns a helpful error message.
            """
            try:
                result = await WorkoutService.get_exercise_demo(
                    exercise_name=exercise_name,
                    db_session=db_session
                )
                
                if result is None:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": f"Exercise '{exercise_name}' not found in library. Try a different name or check spelling."
                        }
                    })
                
                return json.dumps({
                    "success": True,
                    "data": result,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "general_assistant_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_exercise_demo: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve exercise demonstration. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_exercise_demo: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        

        return [
            get_user_stats, 
            provide_motivation,
            get_workout_info,
            get_meal_info,
            get_schedule_info,
            get_exercise_demo
        ]
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the general assistant agent.
        
        Creates a specialized system prompt that includes user context,
        friendly tone, and behavioral guidelines. The prompt varies
        based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        base_prompt = f"""You are a friendly fitness assistant for the Shuren fitness coaching system, providing motivation and general support.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

Your Role:
- Provide motivation and encouragement
- Answer general fitness questions
- Handle casual conversation naturally
- Be a supportive companion on their fitness journey

Guidelines:
- Be warm, friendly, and supportive
- Celebrate progress and effort, not just results
- Provide evidence-based fitness information
- Encourage sustainable, long-term habits
- Never provide medical advice or diagnose conditions
- Use tools when relevant to personalize responses
- Maintain a positive, optimistic tone
- Be conversational and relatable

Available Tools:
- get_user_stats: Retrieve general user statistics and profile information
- provide_motivation: Generate personalized motivational messages
- research: Search for evidence-based fitness and nutrition information using web search.
- get_workout_info: Get the workout plan for any given date with exercises, sets, reps, and rest periods
- get_meal_info: Get the meal plan for any given date with dishes, timing, and nutritional information
- get_schedule_info: Get upcoming workout and meal schedules with days and times
- get_exercise_demo: Get exercise demonstration details (GIF, video, instructions) by exercise name
- get_current_datetime: Get the current date and time (use this to determine relative dates)

When to Use Tools:
- Use research when users ask health, fitness, or nutrition questions that require current evidence-based information.
- Use get_workout_info when users ask about a specific day's workout, exercises, or training plan
- Use get_meal_info when users ask about a specific day's meals, nutrition, or eating plan
- Use get_schedule_info when users ask about upcoming workouts, meal times, or their schedule
- Use get_exercise_demo when users ask how to perform a specific exercise or need form guidance
- Use get_user_stats for general profile information and fitness goals
- Use provide_motivation for encouragement and motivational messages

Remember:
- Fitness is a journey, not a destination
- Progress over perfection
- Every step forward counts
- Rest and recovery are part of success
- Consistency beats intensity

CRITICAL INSTRUCTION: You must ONLY use real data fetched from your tools. If you cannot retrieve the real data using your tools, or if the tools return no data, DO NOT make up or guess information. Instead, state clearly that you do not have the relevant data regarding that query.
"""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction (under 30 seconds when spoken, approximately 75 words). Be warm and encouraging."
        else:
            base_prompt += "\n\nIMPORTANT: Provide detailed responses with markdown formatting for text interaction. Use headers, lists, bold text, and emojis to make responses engaging and easy to read."
        
        return base_prompt

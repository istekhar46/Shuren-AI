"""
Scheduling and Reminder Agent for managing workout and meal schedules.

This module provides the SchedulerAgent that handles all scheduling-related queries
including viewing upcoming schedules, rescheduling workouts, and managing reminder preferences.
"""

import json
import logging
from datetime import datetime, time, timedelta
from typing import AsyncIterator, List

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse
from app.agents.onboarding_tools import call_onboarding_step
from app.models.preferences import WorkoutSchedule, MealSchedule, HydrationPreference
from app.models.profile import UserProfile

logger = logging.getLogger(__name__)


class SchedulerAgent(BaseAgent):
    """
    Specialized agent for scheduling and reminder management.
    
    This agent handles:
    - Retrieving upcoming workout and meal schedules
    - Rescheduling workouts
    - Updating reminder preferences
    - Managing notification settings
    
    The agent helps users optimize timing based on their preferences
    and constraints while handling schedule conflicts gracefully.
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
            agent_type="scheduler",
            tools_used=tools_used,
            metadata={
                "mode": "text",
                "user_id": self.context.user_id,
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
        Get the list of tools available to the scheduler agent.
        
        Returns:
            List: List of LangChain tools for scheduling operations
        """
        # Create closures to pass context and db_session to tools
        context = self.context
        db_session = self.db_session
        
        @tool
        async def get_upcoming_schedule() -> str:
            """Get upcoming workouts and meals for the user.
            
            Returns:
                JSON string with upcoming schedule including workouts and meals
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
                
                # Get workout schedules
                stmt = select(WorkoutSchedule).where(
                    WorkoutSchedule.profile_id == profile.id,
                    WorkoutSchedule.deleted_at.is_(None)
                ).order_by(WorkoutSchedule.day_of_week)
                
                result = await db_session.execute(stmt)
                workout_schedules = result.scalars().all()
                
                # Get meal schedules
                stmt = select(MealSchedule).where(
                    MealSchedule.profile_id == profile.id,
                    MealSchedule.deleted_at.is_(None)
                ).order_by(MealSchedule.scheduled_time)
                
                result = await db_session.execute(stmt)
                meal_schedules = result.scalars().all()
                
                # Format workout schedules
                workouts = []
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for schedule in workout_schedules:
                    workouts.append({
                        "id": str(schedule.id),
                        "day": day_names[schedule.day_of_week],
                        "day_of_week": schedule.day_of_week,
                        "time": schedule.scheduled_time.strftime("%H:%M"),
                        "notifications_enabled": schedule.enable_notifications
                    })
                
                # Format meal schedules
                meals = []
                for schedule in meal_schedules:
                    meals.append({
                        "id": str(schedule.id),
                        "meal_name": schedule.meal_name,
                        "time": schedule.scheduled_time.strftime("%H:%M"),
                        "notifications_enabled": schedule.enable_notifications
                    })
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "workouts": workouts,
                        "meals": meals
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scheduler_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_upcoming_schedule: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve schedule. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_upcoming_schedule: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def reschedule_workout(workout_schedule_id: str, new_day_of_week: int, new_time: str) -> str:
            """Reschedule a workout to a different day or time.
            
            Args:
                workout_schedule_id: ID of the workout schedule to reschedule
                new_day_of_week: New day of week (0=Monday, 6=Sunday)
                new_time: New time in HH:MM format (24-hour)
                
            Returns:
                JSON string with confirmation message or conflict information
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Validate day_of_week
                if not (0 <= new_day_of_week <= 6):
                    return json.dumps({
                        "success": False,
                        "error": "Invalid day_of_week. Must be between 0 (Monday) and 6 (Sunday)"
                    })
                
                # Parse time
                try:
                    time_parts = new_time.split(":")
                    new_time_obj = time(hour=int(time_parts[0]), minute=int(time_parts[1]))
                except (ValueError, IndexError):
                    return json.dumps({
                        "success": False,
                        "error": "Invalid time format. Use HH:MM (24-hour format)"
                    })
                
                # Get the workout schedule
                stmt = select(WorkoutSchedule).where(
                    WorkoutSchedule.id == workout_schedule_id,
                    WorkoutSchedule.deleted_at.is_(None)
                )
                result = await db_session.execute(stmt)
                workout_schedule = result.scalar_one_or_none()
                
                if not workout_schedule:
                    return json.dumps({
                        "success": False,
                        "error": "Workout schedule not found"
                    })
                
                # Check for conflicts with other workouts on the same day
                stmt = select(WorkoutSchedule).where(
                    and_(
                        WorkoutSchedule.profile_id == workout_schedule.profile_id,
                        WorkoutSchedule.day_of_week == new_day_of_week,
                        WorkoutSchedule.id != workout_schedule_id,
                        WorkoutSchedule.deleted_at.is_(None)
                    )
                )
                result = await db_session.execute(stmt)
                conflicting_workout = result.scalar_one_or_none()
                
                if conflicting_workout:
                    return json.dumps({
                        "success": False,
                        "error": "Conflict detected",
                        "data": {
                            "message": f"Another workout is already scheduled on this day at {conflicting_workout.scheduled_time.strftime('%H:%M')}",
                            "conflicting_time": conflicting_workout.scheduled_time.strftime("%H:%M")
                        }
                    })
                
                # Update the schedule
                old_day = workout_schedule.day_of_week
                old_time = workout_schedule.scheduled_time.strftime("%H:%M")
                
                workout_schedule.day_of_week = new_day_of_week
                workout_schedule.scheduled_time = new_time_obj
                
                await db_session.commit()
                await db_session.refresh(workout_schedule)
                
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "message": f"Workout rescheduled from {day_names[old_day]} at {old_time} to {day_names[new_day_of_week]} at {new_time}",
                        "old_schedule": {
                            "day": day_names[old_day],
                            "time": old_time
                        },
                        "new_schedule": {
                            "day": day_names[new_day_of_week],
                            "time": new_time
                        }
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scheduler_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in reschedule_workout: {e}")
                await db_session.rollback()
                return json.dumps({
                    "success": False,
                    "error": "Unable to reschedule workout. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in reschedule_workout: {e}")
                await db_session.rollback()
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def update_reminder_preferences(reminder_type: str, enabled: bool) -> str:
            """Update reminder notification preferences.
            
            Args:
                reminder_type: Type of reminder - "workout", "meal", or "hydration"
                enabled: Whether to enable (True) or disable (False) notifications
                
            Returns:
                JSON string with confirmation message
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Validate reminder_type
                valid_types = ["workout", "meal", "hydration"]
                if reminder_type not in valid_types:
                    return json.dumps({
                        "success": False,
                        "error": f"Invalid reminder_type. Must be one of: {', '.join(valid_types)}"
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
                
                updated_count = 0
                
                # Update based on reminder type
                if reminder_type == "workout":
                    stmt = select(WorkoutSchedule).where(
                        WorkoutSchedule.profile_id == profile.id,
                        WorkoutSchedule.deleted_at.is_(None)
                    )
                    result = await db_session.execute(stmt)
                    schedules = result.scalars().all()
                    
                    for schedule in schedules:
                        schedule.enable_notifications = enabled
                        updated_count += 1
                
                elif reminder_type == "meal":
                    stmt = select(MealSchedule).where(
                        MealSchedule.profile_id == profile.id,
                        MealSchedule.deleted_at.is_(None)
                    )
                    result = await db_session.execute(stmt)
                    schedules = result.scalars().all()
                    
                    for schedule in schedules:
                        schedule.enable_notifications = enabled
                        updated_count += 1
                
                elif reminder_type == "hydration":
                    stmt = select(HydrationPreference).where(
                        HydrationPreference.profile_id == profile.id,
                        HydrationPreference.deleted_at.is_(None)
                    )
                    result = await db_session.execute(stmt)
                    hydration_pref = result.scalar_one_or_none()
                    
                    if hydration_pref:
                        hydration_pref.enable_notifications = enabled
                        updated_count = 1
                
                await db_session.commit()
                
                status = "enabled" if enabled else "disabled"
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "message": f"{reminder_type.capitalize()} reminders {status}",
                        "reminder_type": reminder_type,
                        "enabled": enabled,
                        "updated_count": updated_count
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "scheduler_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in update_reminder_preferences: {e}")
                await db_session.rollback()
                return json.dumps({
                    "success": False,
                    "error": "Unable to update reminder preferences. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in update_reminder_preferences: {e}")
                await db_session.rollback()
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        # Create onboarding tools using @tool decorator
        @tool
        async def save_meal_schedule_tool(meals: list) -> str:
            """Save meal timing schedule during onboarding (State 6).
            
            Args:
                meals: List of meal objects with meal_name, scheduled_time, and optional enable_notifications
                       Example: [
                           {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": true},
                           {"meal_name": "Lunch", "scheduled_time": "13:00"}
                       ]
                       scheduled_time format: "HH:MM" (24-hour format)
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_meal_schedule(meals)
            return json.dumps(result)
        
        @tool
        async def save_workout_schedule_tool(workouts: list) -> str:
            """Save workout schedule during onboarding (State 7).
            
            Args:
                workouts: List of workout objects with day_of_week, scheduled_time, and optional enable_notifications
                          Example: [
                              {"day_of_week": 1, "scheduled_time": "07:00", "enable_notifications": true},
                              {"day_of_week": 3, "scheduled_time": "07:00"}
                          ]
                          day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
                          scheduled_time format: "HH:MM" (24-hour format)
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_workout_schedule(workouts)
            return json.dumps(result)
        
        @tool
        async def save_hydration_schedule_tool(
            daily_water_target_ml: int,
            reminder_frequency_minutes: int
        ) -> str:
            """Save hydration preferences during onboarding (State 8).
            
            Args:
                daily_water_target_ml: Daily water intake goal in ml (500-10000)
                reminder_frequency_minutes: How often to remind in minutes (15-480)
                
            Returns:
                JSON string with success/error response
            """
            result = await self.save_hydration_schedule(
                daily_water_target_ml=daily_water_target_ml,
                reminder_frequency_minutes=reminder_frequency_minutes
            )
            return json.dumps(result)
        
        return [
            get_upcoming_schedule,
            reschedule_workout,
            update_reminder_preferences,
            save_meal_schedule_tool,
            save_workout_schedule_tool,
            save_hydration_schedule_tool
        ]
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the scheduler agent.
        
        Creates a specialized system prompt that includes user context,
        scheduling expertise, and behavioral guidelines. The prompt varies
        based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        base_prompt = f"""You are a scheduling and reminder management assistant for the Shuren fitness coaching system.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}

Your Expertise:
- Schedule optimization and time management
- Workout and meal timing coordination
- Reminder and notification management
- Conflict resolution and rescheduling

Guidelines:
- Help users optimize their schedule based on preferences and constraints
- Handle schedule conflicts gracefully with clear explanations
- Respect user preferences for notification timing
- Provide practical suggestions for schedule adjustments
- Be flexible and understanding of real-life scheduling challenges
- Use tools to fetch and update schedule information

Available Tools:
- get_upcoming_schedule: Retrieve upcoming workouts and meals
- reschedule_workout: Move a workout to a different day or time
- update_reminder_preferences: Enable or disable notifications for workouts, meals, or hydration
"""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction (under 30 seconds when spoken, approximately 75 words)."
        else:
            base_prompt += "\n\nIMPORTANT: Provide detailed schedule information with markdown formatting for text interaction. Use headers, lists, and emphasis to improve readability."
        
        return base_prompt

    async def save_meal_schedule(
        self,
        meals: list[dict]
    ) -> dict:
        """Save meal timing schedule (State 6).
        
        This tool is used during onboarding to capture when the user wants
        to eat their meals throughout the day. This information is used for
        meal reminders and planning.
        
        Args:
            meals: List of meal objects with meal_name, scheduled_time, and optional enable_notifications
                   Example: [
                       {"meal_name": "Breakfast", "scheduled_time": "08:00", "enable_notifications": true},
                       {"meal_name": "Lunch", "scheduled_time": "13:00", "enable_notifications": true}
                   ]
                   scheduled_time format: "HH:MM" (24-hour format)
        
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
            step=6,
            data={"meals": meals},
            agent_type="scheduler"
        )
    
    async def save_workout_schedule(
        self,
        workouts: list[dict]
    ) -> dict:
        """Save workout schedule (State 7).
        
        This tool is used during onboarding to capture when the user wants
        to work out during the week. This information is used for workout
        reminders and planning.
        
        Args:
            workouts: List of workout objects with day_of_week, scheduled_time, and optional enable_notifications
                      Example: [
                          {"day_of_week": 1, "scheduled_time": "07:00", "enable_notifications": true},
                          {"day_of_week": 3, "scheduled_time": "07:00", "enable_notifications": true}
                      ]
                      day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
                      scheduled_time format: "HH:MM" (24-hour format)
        
        Returns:
            Success/error response dict (see save_meal_schedule for structure)
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=7,
            data={"workouts": workouts},
            agent_type="scheduler"
        )
    
    async def save_hydration_schedule(
        self,
        daily_water_target_ml: int,
        reminder_frequency_minutes: int
    ) -> dict:
        """Save hydration preferences (State 8).
        
        This tool is used during onboarding to capture the user's daily
        water intake goal and how often they want to be reminded to drink water.
        
        Args:
            daily_water_target_ml: Daily water intake goal in ml (500-10000)
            reminder_frequency_minutes: How often to remind in minutes (15-480)
        
        Returns:
            Success/error response dict (see save_meal_schedule for structure)
        """
        return await call_onboarding_step(
            db=self.db_session,
            user_id=self.context.user_id,
            step=8,
            data={
                "daily_water_target_ml": daily_water_target_ml,
                "reminder_frequency_minutes": reminder_frequency_minutes
            },
            agent_type="scheduler"
        )

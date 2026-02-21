"""
Tracking and Adjustment Agent for progress tracking, adherence analysis, and plan adjustments.

This module provides the TrackerAgent that handles all progress tracking queries
including workout adherence, progress metrics, and adaptive plan adjustments.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import AsyncIterator, List

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class TrackerAgent(BaseAgent):
    """
    Specialized agent for progress tracking and adaptive adjustments.
    
    This agent handles:
    - Calculating workout adherence statistics
    - Retrieving progress metrics (weight, measurements)
    - Suggesting adaptive plan adjustments
    - Analyzing behavior patterns
    
    The agent provides supportive, non-judgmental feedback and focuses
    on progress rather than perfection.
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
            agent_type="tracker",
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
        Get the list of tools available to the tracker agent.
        
        Returns:
            List: List of LangChain tools for tracking and adjustment operations
        """
        # Create closures to pass context and db_session to tools
        context = self.context
        db_session = self.db_session
        
        @tool
        async def get_workout_adherence(days: int = 30) -> str:
            """Get workout adherence statistics for the specified number of days.
            
            Args:
                days: Number of days to analyze (default: 30)
                
            Returns:
                JSON string with adherence statistics including completion percentage
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Note: WorkoutLog model doesn't exist yet in the schema
                # For now, we'll return mock data structure that would be used
                # This will need to be implemented when WorkoutLog model is added
                
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Mock adherence calculation
                # In real implementation, this would query WorkoutLog and WorkoutSchedule
                # adherence_percentage = (completed_workouts / scheduled_workouts) * 100
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "period_days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "scheduled_workouts": 0,
                        "completed_workouts": 0,
                        "adherence_percentage": 0.0,
                        "missed_workouts": 0,
                        "streak_days": 0,
                        "note": "WorkoutLog model pending implementation"
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "tracker_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_workout_adherence: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve adherence statistics. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_workout_adherence: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def get_progress_metrics() -> str:
            """Get user's progress metrics including weight, measurements, and tracked data.
            
            Returns:
                JSON string with progress metrics and historical data
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Note: Progress tracking models (weight logs, measurements) don't exist yet
                # For now, we'll return mock data structure that would be used
                # This will need to be implemented when progress tracking models are added
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "current_weight_kg": None,
                        "starting_weight_kg": None,
                        "weight_change_kg": None,
                        "measurements": {
                            "chest_cm": None,
                            "waist_cm": None,
                            "hips_cm": None,
                            "arms_cm": None,
                            "thighs_cm": None
                        },
                        "body_composition": {
                            "body_fat_percentage": None,
                            "muscle_mass_kg": None
                        },
                        "performance_metrics": {
                            "strength_improvements": [],
                            "endurance_improvements": []
                        },
                        "last_updated": None,
                        "note": "Progress tracking models pending implementation"
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "tracker_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_progress_metrics: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve progress metrics. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_progress_metrics: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def suggest_plan_adjustment(adherence_percentage: float, reason: str) -> str:
            """Suggest adaptive plan adjustments based on adherence patterns.
            
            Args:
                adherence_percentage: Current adherence percentage (0-100)
                reason: Reason for adjustment (e.g., "low adherence", "too challenging", "time constraints")
                
            Returns:
                JSON string with supportive adjustment suggestions
            """
            try:
                # Generate adaptive suggestions based on adherence and context
                fitness_level = context.fitness_level
                primary_goal = context.primary_goal
                
                suggestions = []
                adjustment_type = "maintain"
                
                # Analyze adherence and generate suggestions
                if adherence_percentage < 50:
                    adjustment_type = "reduce"
                    suggestions.append("Consider reducing workout frequency to build consistency")
                    suggestions.append("Focus on shorter, more manageable workout sessions")
                    suggestions.append("Identify and address barriers to workout completion")
                    suggestions.append("Set smaller, achievable goals to rebuild momentum")
                elif adherence_percentage < 70:
                    adjustment_type = "optimize"
                    suggestions.append("Review workout timing to find better schedule fit")
                    suggestions.append("Consider workout duration adjustments")
                    suggestions.append("Identify which workouts are being missed most often")
                    suggestions.append("Explore alternative exercises that fit your lifestyle better")
                elif adherence_percentage >= 90:
                    adjustment_type = "progress"
                    suggestions.append("Excellent consistency! Consider progressive overload")
                    suggestions.append("You may be ready to increase workout intensity")
                    suggestions.append("Consider adding variety to prevent plateaus")
                    suggestions.append("Explore advanced training techniques")
                else:
                    adjustment_type = "maintain"
                    suggestions.append("Great adherence! Keep up the current routine")
                    suggestions.append("Focus on progressive improvements within current structure")
                    suggestions.append("Monitor for signs of overtraining or burnout")
                
                # Add context-specific suggestions
                if "time constraints" in reason.lower():
                    suggestions.append("Consider time-efficient workout formats (supersets, circuits)")
                    suggestions.append("Explore home workout options to save commute time")
                
                if "too challenging" in reason.lower():
                    suggestions.append("Reduce weight or intensity by 10-15%")
                    suggestions.append("Focus on mastering form before increasing difficulty")
                
                if "motivation" in reason.lower():
                    suggestions.append("Try new exercises or workout styles for variety")
                    suggestions.append("Consider finding a workout partner for accountability")
                    suggestions.append("Set short-term milestone goals to maintain engagement")
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "adherence_percentage": adherence_percentage,
                        "adjustment_type": adjustment_type,
                        "reason": reason,
                        "suggestions": suggestions,
                        "supportive_message": self._generate_supportive_message(adherence_percentage),
                        "context": {
                            "fitness_level": fitness_level,
                            "primary_goal": primary_goal
                        }
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "tracker_agent"
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in suggest_plan_adjustment: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to generate plan adjustments. Please try again."
                })
        
        return [get_workout_adherence, get_progress_metrics, suggest_plan_adjustment]
    
    def _generate_supportive_message(self, adherence_percentage: float) -> str:
        """Generate a supportive, non-judgmental message based on adherence.
        
        Args:
            adherence_percentage: Current adherence percentage (0-100)
            
        Returns:
            str: Supportive message
        """
        if adherence_percentage < 50:
            return "Building consistency takes time. Every workout completed is progress, no matter how small. Let's find a sustainable approach that works for your life."
        elif adherence_percentage < 70:
            return "You're making solid progress! Let's optimize your routine to make it even more sustainable and enjoyable."
        elif adherence_percentage >= 90:
            return "Outstanding consistency! Your dedication is paying off. You're ready to take your training to the next level."
        else:
            return "Great work maintaining your routine! Consistency is the foundation of long-term success."
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the tracker agent.
        
        Creates a specialized system prompt that includes user context,
        tracking expertise, and behavioral guidelines. The prompt varies
        based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        base_prompt = f"""You are a progress tracking and adjustment assistant for the Shuren fitness coaching system.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}

Your Expertise:
- Progress tracking and analytics
- Adherence pattern analysis
- Adaptive plan adjustments
- Behavior change support
- Motivational coaching

Guidelines:
- Be supportive and non-judgmental about adherence patterns
- Focus on progress, not perfection
- Analyze patterns in user behavior over time
- Suggest adaptive adjustments without guilt or punishment
- Celebrate consistency and small wins
- Help identify and address barriers to adherence
- Use tools to fetch adherence data and progress metrics when needed
- Provide data-driven insights with empathy

Available Tools:
- get_workout_adherence: Calculate adherence statistics for specified period
- get_progress_metrics: Retrieve weight, measurements, and tracked metrics
- suggest_plan_adjustment: Generate adaptive adjustment suggestions based on patterns

Core Principles:
- Life happens - missed workouts are data, not failures
- Sustainable progress beats perfect adherence
- Small consistent actions compound over time
- Adjust plans to fit reality, not the other way around
"""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction (under 30 seconds when spoken, approximately 75 words)."
        else:
            base_prompt += "\n\nIMPORTANT: Provide detailed analytics with markdown formatting for text interaction. Use headers, lists, charts, and emphasis to improve readability."
        
        return base_prompt

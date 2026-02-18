"""
Scheduling Agent for onboarding.

This agent handles steps 8-9 of the onboarding process, setting up workout
schedules, meal timing, and hydration reminder preferences.
"""

import logging
from typing import List
from uuid import UUID

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select

from app.agents.onboarding.base import BaseOnboardingAgent
from app.agents.tools.scheduling_tools import create_scheduling_tools
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import AgentResponse

logger = logging.getLogger(__name__)


class SchedulingAgent(BaseOnboardingAgent):
    """
    Agent for setting schedules and reminders (Steps 8-9).
    
    This agent helps users establish sustainable routines by:
    - Setting workout days and preferred times based on workout plan
    - Scheduling meal times based on meal plan frequency
    - Configuring hydration reminder preferences
    
    The agent ensures schedules are realistic and fit the user's lifestyle,
    promoting long-term adherence rather than unsustainable perfection.
    """
    
    agent_type = "scheduling"
    
    def get_tools(self) -> List:
        """
        Get scheduling-specific tools.
        
        Returns:
            List containing save_workout_schedule, save_meal_schedule, 
            and save_hydration_preferences tools
        """
        # Tools are created with db and user_id bound
        # They will be bound in process_message when user_id is available
        return []
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for scheduling with context from previous agents.
        
        Returns:
            System prompt including workout plan and meal plan context
        """
        # Extract workout plan context
        workout_plan = self.context.get("workout_planning", {}).get("proposed_plan", {})
        workout_frequency = workout_plan.get("frequency", "unknown")
        workout_duration = workout_plan.get("duration_minutes", "unknown")
        
        # Extract meal plan context
        meal_plan = self.context.get("diet_planning", {}).get("proposed_plan", {})
        meal_frequency = meal_plan.get("meal_frequency", "unknown")
        daily_calories = meal_plan.get("daily_calories", "unknown")
        
        # Extract fitness level for context
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        
        return f"""You are a Scheduling Agent helping users establish sustainable fitness routines.

Context from previous steps:
- Fitness Level: {fitness_level}
- Workout Plan: {workout_frequency} days per week, {workout_duration} minutes per session
- Meal Plan: {meal_frequency} meals per day, {daily_calories} calories daily

Your role:
1. Set up workout schedule - Ask about preferred workout days and times
2. Plan meal timing - Ask about preferred times for each of the {meal_frequency} meals
3. Configure hydration reminders - Ask about water intake goals and reminder frequency

Guidelines for Workout Schedule:
- Ask which {workout_frequency} days of the week they prefer to workout
- Ask what time of day works best for each workout day
- Consider their work schedule, family commitments, and energy levels
- Suggest morning workouts for consistency, but be flexible
- Ensure rest days are distributed throughout the week
- When you have all {workout_frequency} days and times, call save_workout_schedule tool

Guidelines for Meal Timing:
- Ask about preferred times for their {meal_frequency} meals
- Ensure meals are spaced at least 2 hours apart for proper digestion
- Consider their work schedule and workout times
- Suggest pre-workout and post-workout meal timing for optimal nutrition
- Meals should be in chronological order throughout the day
- When you have all {meal_frequency} meal times, call save_meal_schedule tool

Guidelines for Hydration:
- Ask about their daily water intake goal (suggest 2-3 liters based on activity)
- Ask how often they want reminders (every 1-4 hours)
- Explain importance of hydration for fitness and recovery
- Suggest more frequent reminders on workout days
- When you have frequency and target, call save_hydration_preferences tool

Conversation Flow:
1. Start by explaining you'll help set up their daily schedule
2. Begin with workout schedule (days and times)
3. Move to meal timing once workout schedule is saved
4. Finish with hydration preferences once meal schedule is saved
5. After all three are saved, confirm completion and let them know they're ready to complete onboarding

Tone:
- Practical and understanding
- Flexible and adaptable to their lifestyle
- Supportive of their constraints
- Encouraging about building sustainable habits
- Emphasize that schedules can be adjusted later as life happens

Important:
- Call the save tools when you have complete information
- Don't proceed to next topic until current schedule is saved
- After all three schedules are saved, the system will automatically advance to completion"""
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about scheduling preferences.
        
        Uses LangChain's tool-calling agent to:
        1. Understand user's schedule preferences from natural language
        2. Reference workout and meal plans from previous agent context
        3. Suggest optimal timing based on their plans
        4. Call save tools when information is complete
        5. Set step_complete=True when all schedules are saved
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Store user_id for tool access
        self._current_user_id = user_id
        
        # Create tools with db and user_id bound
        tools = create_scheduling_tools(self.db, user_id)
        
        # Build prompt with context
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # TODO: Load from conversation_history
        })
        
        # Check if step is complete (all three schedules saved)
        step_complete = await self._check_if_complete(user_id)
        
        # If complete, set next action to complete onboarding
        next_action = "complete_onboarding" if step_complete else "continue_conversation"
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action=next_action
        )
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if scheduling step is complete.
        
        Scheduling is complete when all three schedules are saved:
        - workout_schedule
        - meal_schedule
        - hydration_preferences
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if all three schedules are saved in agent_context
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if not state or not state.agent_context:
            return False
        
        scheduling_context = state.agent_context.get("scheduling", {})
        
        # Check if all three schedules are present
        has_workout = "workout_schedule" in scheduling_context
        has_meals = "meal_schedule" in scheduling_context
        has_hydration = "hydration_preferences" in scheduling_context
        
        return has_workout and has_meals and has_hydration

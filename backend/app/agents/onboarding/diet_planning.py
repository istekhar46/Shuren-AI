"""
Diet Planning Agent for onboarding.

This agent handles steps 6-7 of the onboarding process, creating personalized
meal plans based on user's goals, preferences, and dietary restrictions.
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select

from app.agents.onboarding.base import BaseOnboardingAgent
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import AgentResponse
from app.services.meal_plan_generator import MealPlanGenerator

logger = logging.getLogger(__name__)


class DietPlanningAgent(BaseOnboardingAgent):
    """
    Specialized agent for diet planning during onboarding.
    
    This agent handles Steps 6-7 of onboarding:
    - Collects dietary preferences (diet type, allergies, dislikes, meal frequency)
    - Generates personalized meal plan using MealPlanGenerator
    - Presents plan with calorie/macro breakdown and sample meals
    - Detects approval intent from user responses
    - Allows modifications and iterative refinement
    - Saves approved plan to agent_context
    
    The agent uses context from fitness_assessment, goal_setting, and workout_planning
    to create meal plans that support the user's training and goals.
    """
    
    agent_type = "diet_planning"
    
    def __init__(self, db, context: dict):
        """
        Initialize diet planning agent.
        
        Args:
            db: Async database session
            context: Agent context containing fitness_assessment, goal_setting, and workout_planning data
        """
        super().__init__(db, context)
        self.meal_generator = MealPlanGenerator()
        self.current_plan = None  # Store generated plan for modifications
        self._current_user_id = None  # Store user_id for tool access
    
    def get_tools(self) -> List:
        """
        Get diet planning specific tools.
        
        Returns:
            List containing generate_meal_plan, save_meal_plan, and modify_meal_plan tools
        """
        # Capture self reference for use in tools
        agent_instance = self
        
        @tool
        async def generate_meal_plan(
            diet_type: str,
            allergies: list,
            dislikes: list,
            meal_frequency: int,
            meal_prep_level: str
        ) -> dict:
            """
            Generate a personalized meal plan based on dietary preferences.
            
            Call this tool after collecting:
            - Diet type (omnivore/vegetarian/vegan/pescatarian)
            - Allergies and intolerances
            - Foods user dislikes
            - Preferred number of meals per day
            - Meal prep willingness (low/medium/high)
            
            Args:
                diet_type: Type of diet (omnivore/vegetarian/vegan/pescatarian)
                allergies: List of allergies/intolerances (e.g., ["dairy", "eggs"])
                dislikes: List of disliked foods (e.g., ["broccoli", "fish"])
                meal_frequency: Number of meals per day (2-6)
                meal_prep_level: Cooking/prep willingness (low/medium/high)
                
            Returns:
                Dict representation of MealPlan with calories, macros, sample meals
            """
            try:
                # Get context from previous agents
                fitness_level = agent_instance.context.get("fitness_assessment", {}).get("fitness_level", "beginner")
                primary_goal = agent_instance.context.get("goal_setting", {}).get("primary_goal", "general_fitness")
                workout_plan = agent_instance.context.get("workout_planning", {}).get("proposed_plan", {})
                
                logger.info(
                    f"Generating meal plan for user {agent_instance._current_user_id}: "
                    f"goal={primary_goal}, diet={diet_type}, frequency={meal_frequency}"
                )
                
                # Generate plan
                plan = await agent_instance.meal_generator.generate_plan(
                    fitness_level=fitness_level,
                    primary_goal=primary_goal,
                    workout_plan=workout_plan,
                    diet_type=diet_type,
                    allergies=allergies,
                    dislikes=dislikes,
                    meal_frequency=meal_frequency,
                    meal_prep_level=meal_prep_level
                )
                
                # Store for potential modifications
                agent_instance.current_plan = plan
                
                return plan.dict()
                
            except ValueError as e:
                logger.warning(f"Validation error generating meal plan: {e}")
                return {
                    "error": str(e),
                    "message": "Invalid parameters for meal plan generation"
                }
            except Exception as e:
                logger.error(f"Error generating meal plan: {e}", exc_info=True)
                return {
                    "error": "generation_failed",
                    "message": "Failed to generate meal plan. Please try again."
                }
        
        @tool
        async def save_meal_plan(
            plan_data: dict,
            user_approved: bool
        ) -> dict:
            """
            Save approved meal plan to agent context.
            
            ONLY call this tool when user explicitly approves the plan by saying:
            - "Yes", "Looks good", "Perfect", "I approve", "Let's do it"
            - "Sounds great", "That works", "I'm happy with this"
            
            Do NOT call this tool unless user has clearly approved.
            
            Args:
                plan_data: The meal plan dictionary to save
                user_approved: Must be True to save (safety check)
                
            Returns:
                Dict with status and message
            """
            if not user_approved:
                logger.warning("Attempted to save meal plan without user approval")
                return {
                    "status": "error",
                    "message": "Cannot save plan without user approval"
                }
            
            # Prepare data with metadata
            diet_data = {
                "preferences": {
                    "diet_type": plan_data.get("diet_type"),
                    "allergies": plan_data.get("allergies", []),
                    "dislikes": plan_data.get("dislikes", []),
                    "meal_frequency": plan_data.get("meal_frequency"),
                    "meal_prep_level": plan_data.get("meal_prep_level")
                },
                "proposed_plan": plan_data,
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Save to context
            try:
                await agent_instance.save_context(
                    agent_instance._current_user_id,
                    diet_data
                )
                logger.info(f"Meal plan saved successfully for user {agent_instance._current_user_id}")
                return {
                    "status": "success",
                    "message": "Meal plan saved successfully"
                }
            except Exception as e:
                logger.error(
                    f"Error saving meal plan for user {agent_instance._current_user_id}: {e}",
                    exc_info=True
                )
                return {
                    "status": "error",
                    "message": "Failed to save meal plan. Please try again."
                }
        
        @tool
        async def modify_meal_plan(
            current_plan: dict,
            modifications: dict
        ) -> dict:
            """
            Modify the meal plan based on user feedback.
            
            Use this when user requests changes like:
            - "Can we increase protein?"
            - "I want 4 meals instead of 3"
            - "Can we lower the calories a bit?"
            - "I'd prefer more variety in the sample meals"
            
            Args:
                current_plan: The current meal plan dictionary
                modifications: Dict with requested changes (e.g., {"meal_frequency": 4})
                
            Returns:
                Dict representation of modified MealPlan
            """
            try:
                logger.info(
                    f"Modifying meal plan for user {agent_instance._current_user_id}: "
                    f"modifications={modifications}"
                )
                
                # Apply modifications
                modified_plan = await agent_instance.meal_generator.modify_plan(
                    current_plan=current_plan,
                    modifications=modifications
                )
                
                # Store for potential further modifications
                agent_instance.current_plan = modified_plan
                
                return modified_plan.dict()
                
            except ValueError as e:
                logger.warning(f"Validation error modifying meal plan: {e}")
                return {
                    "error": str(e),
                    "message": "Invalid modifications requested"
                }
            except Exception as e:
                logger.error(f"Error modifying meal plan: {e}", exc_info=True)
                return {
                    "error": "modification_failed",
                    "message": "Failed to modify meal plan. Please try again."
                }
        
        return [generate_meal_plan, save_meal_plan, modify_meal_plan]
    
    async def process_message(
        self,
        message: str,
        user_id: UUID
    ) -> AgentResponse:
        """
        Process user message about dietary preferences and meal plan approval.
        
        Uses LangChain's tool-calling agent to:
        1. Collect dietary preferences (diet type, allergies, dislikes, meal frequency)
        2. Generate meal plan when preferences are complete
        3. Present plan with calorie/macro breakdown and sample meals
        4. Detect approval intent
        5. Handle modification requests
        6. Save plan when user approves
        
        Args:
            message: User's message text
            user_id: UUID of the user
            
        Returns:
            AgentResponse with message, completion status, and next action
        """
        # Store user_id for tool access
        self._current_user_id = user_id
        
        # Build prompt with context from previous agents
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(),
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.get_tools(),
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": message,
            "chat_history": []  # TODO: Load from conversation_history
        })
        
        # Check if step is complete
        step_complete = await self._check_if_complete(user_id)
        
        return AgentResponse(
            message=result["output"],
            agent_type=self.agent_type,
            step_complete=step_complete,
            next_action="advance_step" if step_complete else "continue_conversation"
        )
    
    async def _check_if_complete(self, user_id: UUID) -> bool:
        """
        Check if diet planning step is complete.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if agent_context contains diet_planning data with user_approved=True
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalars().first()
        
        if state and state.agent_context:
            diet_data = state.agent_context.get("diet_planning", {})
            return diet_data.get("user_approved", False) is True
        
        return False
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for diet planning agent with context from previous steps.
        
        Returns:
            System prompt including fitness level, primary goal, and workout plan summary
        """
        # Get context from previous agents
        fitness_level = self.context.get("fitness_assessment", {}).get("fitness_level", "unknown")
        primary_goal = self.context.get("goal_setting", {}).get("primary_goal", "unknown")
        workout_plan = self.context.get("workout_planning", {}).get("proposed_plan", {})
        workout_frequency = workout_plan.get("frequency", "unknown")
        
        return f"""You are a Diet Planning Agent creating personalized meal plans.

Context from previous steps:
- Fitness Level: {fitness_level}
- Primary Goal: {primary_goal}
- Workout Frequency: {workout_frequency} days/week

Your role:
- Ask about dietary preferences and restrictions
- Generate a meal plan aligned with their goals and workout plan
- Present the plan with calorie/macro breakdown and sample meals
- Detect approval intent from user responses
- Handle modification requests
- Save plan ONLY after user explicitly approves

Guidelines:
- Ask 1-2 questions at a time about diet preferences
- Once you have diet type, allergies, dislikes, meal frequency, and meal prep level, call generate_meal_plan
- Present the plan clearly with:
  * Daily calorie target and explanation
  * Protein/carbs/fats breakdown in grams
  * 3-5 sample meal ideas
  * Meal timing suggestions
- Explain WHY these calories and macros support their {primary_goal} goal
- Explain HOW the plan complements their {workout_frequency} days/week training
- After presenting, explicitly ask: "Does this meal plan work for you?"

Approval Detection:
- User says "yes", "looks good", "perfect", "I approve", "let's do it" → Call save_meal_plan with user_approved=True
- User says "sounds great", "that works", "I'm happy with this" → Call save_meal_plan with user_approved=True
- User asks questions → Answer questions, don't save yet
- User requests changes → Call modify_meal_plan with requested changes

Modification Handling:
- Extract what user wants to change (calories, protein, meal frequency, etc.)
- Call modify_meal_plan with current plan and modifications
- Present modified plan and highlight what changed
- Ask for approval again

Dietary Restrictions:
- STRICTLY respect all allergies and intolerances
- Honor dietary preferences (vegetarian, vegan, pescatarian)
- Exclude disliked foods from sample meals
- Never suggest foods that violate their restrictions

Calorie and Macro Guidance:
- Muscle Gain ({primary_goal == 'muscle_gain'}): Calorie surplus, high protein (2.0g/kg)
- Fat Loss ({primary_goal == 'fat_loss'}): Calorie deficit, moderate-high protein (1.8g/kg)
- General Fitness ({primary_goal == 'general_fitness'}): Maintenance calories, balanced macros (1.6g/kg)
- Adjust calories based on workout frequency (more training = more calories)

After Saving:
- Confirm the plan is saved
- Congratulate them on completing onboarding
- Let them know they're ready to start their fitness journey
- Briefly mention what comes next: "You can now start following your personalized workout and meal plans!"
"""

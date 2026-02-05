"""
Diet Planner Agent for nutrition guidance, meal planning, and recipe information.

This module provides the DietPlannerAgent that handles all nutrition and meal planning
queries including meal plans, recipes, substitutions, and nutritional information.
"""

import json
import logging
from datetime import datetime, date
from typing import AsyncIterator, List

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse
from app.models.dish import Dish, DishIngredient, Ingredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule, DietaryPreference

logger = logging.getLogger(__name__)


class DietPlannerAgent(BaseAgent):
    """
    Specialized agent for diet planning and nutrition guidance.
    
    This agent handles:
    - Retrieving current meal plans
    - Suggesting meal substitutions
    - Providing recipe details
    - Calculating nutritional information
    
    The agent respects dietary preferences, allergies, and restrictions
    from the user profile and provides practical nutritional guidance.
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
            agent_type="diet",
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
        Get the list of tools available to the diet planner agent.
        
        Returns:
            List: List of LangChain tools for diet and nutrition operations
        """
        # Create closures to pass context and db_session to tools
        context = self.context
        db_session = self.db_session
        
        @tool
        async def get_current_meal_plan() -> str:
            """Get today's meal plan for the user.
            
            Returns:
                JSON string with meal details including dishes, timing, and nutritional information
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Get today's day of week (0=Monday, 6=Sunday)
                today = date.today().weekday()
                
                # Get user's profile to access meal templates
                from app.models.profile import UserProfile
                
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
                
                # Get active meal template
                stmt = select(MealTemplate).where(
                    MealTemplate.profile_id == profile.id,
                    MealTemplate.is_active == True,
                    MealTemplate.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                meal_template = result.scalar_one_or_none()
                
                if not meal_template:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No meal plan configured yet. Please complete your meal planning setup."
                        }
                    })
                
                # Get today's meals from template
                stmt = select(TemplateMeal).where(
                    TemplateMeal.template_id == meal_template.id,
                    TemplateMeal.day_of_week == today,
                    TemplateMeal.is_primary == True,
                    TemplateMeal.deleted_at.is_(None)
                ).join(TemplateMeal.dish).join(TemplateMeal.meal_schedule)
                
                result = await db_session.execute(stmt)
                template_meals = result.scalars().all()
                
                if not template_meals:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No meals scheduled for today"
                        }
                    })
                
                # Build meal list with details
                meals = []
                total_calories = 0
                total_protein = 0
                total_carbs = 0
                total_fats = 0
                
                for template_meal in template_meals:
                    dish = template_meal.dish
                    meal_schedule = template_meal.meal_schedule
                    
                    meal_data = {
                        "meal_name": meal_schedule.meal_name,
                        "scheduled_time": meal_schedule.scheduled_time.strftime("%H:%M"),
                        "dish_name": dish.name,
                        "dish_name_hindi": dish.name_hindi,
                        "calories": float(dish.calories),
                        "protein_g": float(dish.protein_g),
                        "carbs_g": float(dish.carbs_g),
                        "fats_g": float(dish.fats_g),
                        "serving_size_g": float(dish.serving_size_g),
                        "prep_time_minutes": dish.prep_time_minutes,
                        "cook_time_minutes": dish.cook_time_minutes,
                        "is_vegetarian": dish.is_vegetarian,
                        "is_vegan": dish.is_vegan
                    }
                    
                    meals.append(meal_data)
                    
                    # Accumulate totals
                    total_calories += float(dish.calories)
                    total_protein += float(dish.protein_g)
                    total_carbs += float(dish.carbs_g)
                    total_fats += float(dish.fats_g)
                
                # Get meal plan targets
                stmt = select(MealPlan).where(
                    MealPlan.profile_id == profile.id,
                    MealPlan.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                meal_plan = result.scalar_one_or_none()
                
                targets = {}
                if meal_plan:
                    targets = {
                        "daily_calorie_target": meal_plan.daily_calorie_target,
                        "protein_percentage": float(meal_plan.protein_percentage),
                        "carbs_percentage": float(meal_plan.carbs_percentage),
                        "fats_percentage": float(meal_plan.fats_percentage)
                    }
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "day_of_week": today,
                        "meals": meals,
                        "daily_totals": {
                            "calories": round(total_calories, 2),
                            "protein_g": round(total_protein, 2),
                            "carbs_g": round(total_carbs, 2),
                            "fats_g": round(total_fats, 2)
                        },
                        "targets": targets
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "diet_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_current_meal_plan: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve meal plan. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_current_meal_plan: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def suggest_meal_substitution(meal_type: str, reason: str) -> str:
            """Suggest meal substitution based on dietary preferences and restrictions.
            
            Args:
                meal_type: Type of meal to substitute - "breakfast", "lunch", "dinner", "snack"
                reason: Why substitution is needed (e.g., "don't like the dish", "missing ingredients", "want variety")
                
            Returns:
                JSON string with suggested alternative meals
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Get user's profile and dietary preferences
                from app.models.profile import UserProfile
                
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
                
                # Get dietary preferences
                stmt = select(DietaryPreference).where(
                    DietaryPreference.profile_id == profile.id,
                    DietaryPreference.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                dietary_pref = result.scalar_one_or_none()
                
                # Build query for alternative dishes
                stmt = select(Dish).where(
                    Dish.meal_type == meal_type,
                    Dish.is_active == True,
                    Dish.deleted_at.is_(None)
                )
                
                # Apply dietary restrictions
                if dietary_pref:
                    diet_type = dietary_pref.diet_type
                    
                    if diet_type == "vegetarian":
                        stmt = stmt.where(Dish.is_vegetarian == True)
                    elif diet_type == "vegan":
                        stmt = stmt.where(Dish.is_vegan == True)
                    
                    # Filter out dishes with allergens
                    allergies = dietary_pref.allergies
                    if allergies:
                        for allergen in allergies:
                            stmt = stmt.where(~Dish.contains_allergens.contains([allergen]))
                
                # Order by popularity and limit to top 5
                stmt = stmt.order_by(Dish.popularity_score.desc()).limit(5)
                
                result = await db_session.execute(stmt)
                alternative_dishes = result.scalars().all()
                
                if not alternative_dishes:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "message": "No suitable alternatives found matching your dietary preferences"
                        }
                    })
                
                # Build suggestions list
                suggestions = []
                for dish in alternative_dishes:
                    suggestion = {
                        "dish_name": dish.name,
                        "dish_name_hindi": dish.name_hindi,
                        "description": dish.description,
                        "cuisine_type": dish.cuisine_type,
                        "calories": float(dish.calories),
                        "protein_g": float(dish.protein_g),
                        "carbs_g": float(dish.carbs_g),
                        "fats_g": float(dish.fats_g),
                        "prep_time_minutes": dish.prep_time_minutes,
                        "cook_time_minutes": dish.cook_time_minutes,
                        "difficulty_level": dish.difficulty_level,
                        "is_vegetarian": dish.is_vegetarian,
                        "is_vegan": dish.is_vegan,
                        "is_gluten_free": dish.is_gluten_free,
                        "is_dairy_free": dish.is_dairy_free
                    }
                    suggestions.append(suggestion)
                
                # Include dietary context
                dietary_context = {}
                if dietary_pref:
                    dietary_context = {
                        "diet_type": dietary_pref.diet_type,
                        "allergies": dietary_pref.allergies,
                        "intolerances": dietary_pref.intolerances,
                        "dislikes": dietary_pref.dislikes
                    }
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "meal_type": meal_type,
                        "reason": reason,
                        "suggestions": suggestions,
                        "dietary_context": dietary_context
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "diet_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in suggest_meal_substitution: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to generate meal substitutions. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in suggest_meal_substitution: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def get_recipe_details(dish_name: str) -> str:
            """Get recipe details including ingredients and cooking instructions.
            
            Args:
                dish_name: Name of the dish to get recipe for
                
            Returns:
                JSON string with recipe ingredients and cooking instructions
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Query dish by name (case-insensitive)
                stmt = select(Dish).where(
                    Dish.name.ilike(f"%{dish_name}%"),
                    Dish.is_active == True,
                    Dish.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                dish = result.scalar_one_or_none()
                
                if not dish:
                    return json.dumps({
                        "success": False,
                        "error": f"Dish '{dish_name}' not found in recipe database"
                    })
                
                # Get ingredients for this dish
                stmt = select(DishIngredient).where(
                    DishIngredient.dish_id == dish.id,
                    DishIngredient.deleted_at.is_(None)
                ).join(DishIngredient.ingredient)
                
                result = await db_session.execute(stmt)
                dish_ingredients = result.scalars().all()
                
                # Build ingredients list
                ingredients = []
                for dish_ingredient in dish_ingredients:
                    ingredient = dish_ingredient.ingredient
                    ingredient_data = {
                        "name": ingredient.name,
                        "name_hindi": ingredient.name_hindi,
                        "quantity": float(dish_ingredient.quantity),
                        "unit": dish_ingredient.unit,
                        "preparation_note": dish_ingredient.preparation_note,
                        "is_optional": dish_ingredient.is_optional,
                        "category": ingredient.category,
                        "is_allergen": ingredient.is_allergen,
                        "allergen_type": ingredient.allergen_type
                    }
                    ingredients.append(ingredient_data)
                
                # Build recipe response
                recipe_data = {
                    "dish_name": dish.name,
                    "dish_name_hindi": dish.name_hindi,
                    "description": dish.description,
                    "cuisine_type": dish.cuisine_type,
                    "meal_type": dish.meal_type,
                    "serving_size_g": float(dish.serving_size_g),
                    "prep_time_minutes": dish.prep_time_minutes,
                    "cook_time_minutes": dish.cook_time_minutes,
                    "total_time_minutes": dish.prep_time_minutes + dish.cook_time_minutes,
                    "difficulty_level": dish.difficulty_level,
                    "ingredients": ingredients,
                    "nutritional_info": {
                        "calories": float(dish.calories),
                        "protein_g": float(dish.protein_g),
                        "carbs_g": float(dish.carbs_g),
                        "fats_g": float(dish.fats_g),
                        "fiber_g": float(dish.fiber_g) if dish.fiber_g else None
                    },
                    "dietary_tags": {
                        "is_vegetarian": dish.is_vegetarian,
                        "is_vegan": dish.is_vegan,
                        "is_gluten_free": dish.is_gluten_free,
                        "is_dairy_free": dish.is_dairy_free,
                        "is_nut_free": dish.is_nut_free
                    },
                    "contains_allergens": dish.contains_allergens
                }
                
                return json.dumps({
                    "success": True,
                    "data": recipe_data,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "diet_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in get_recipe_details: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve recipe details. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in get_recipe_details: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        @tool
        async def calculate_nutrition(dish_name: str) -> str:
            """Calculate nutritional information for a dish.
            
            Args:
                dish_name: Name of the dish to calculate nutrition for
                
            Returns:
                JSON string with macros (protein, carbs, fats) and calories
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Query dish by name (case-insensitive)
                stmt = select(Dish).where(
                    Dish.name.ilike(f"%{dish_name}%"),
                    Dish.is_active == True,
                    Dish.deleted_at.is_(None)
                )
                
                result = await db_session.execute(stmt)
                dish = result.scalar_one_or_none()
                
                if not dish:
                    return json.dumps({
                        "success": False,
                        "error": f"Dish '{dish_name}' not found in nutrition database"
                    })
                
                # Calculate macro percentages
                total_calories = float(dish.calories)
                protein_g = float(dish.protein_g)
                carbs_g = float(dish.carbs_g)
                fats_g = float(dish.fats_g)
                
                # Calories from macros (protein: 4 cal/g, carbs: 4 cal/g, fats: 9 cal/g)
                protein_calories = protein_g * 4
                carbs_calories = carbs_g * 4
                fats_calories = fats_g * 9
                
                # Calculate percentages
                protein_percentage = (protein_calories / total_calories * 100) if total_calories > 0 else 0
                carbs_percentage = (carbs_calories / total_calories * 100) if total_calories > 0 else 0
                fats_percentage = (fats_calories / total_calories * 100) if total_calories > 0 else 0
                
                nutrition_data = {
                    "dish_name": dish.name,
                    "dish_name_hindi": dish.name_hindi,
                    "serving_size_g": float(dish.serving_size_g),
                    "per_serving": {
                        "calories": total_calories,
                        "protein_g": protein_g,
                        "carbs_g": carbs_g,
                        "fats_g": fats_g,
                        "fiber_g": float(dish.fiber_g) if dish.fiber_g else None
                    },
                    "macro_percentages": {
                        "protein_percent": round(protein_percentage, 1),
                        "carbs_percent": round(carbs_percentage, 1),
                        "fats_percent": round(fats_percentage, 1)
                    },
                    "calories_from_macros": {
                        "protein_calories": round(protein_calories, 1),
                        "carbs_calories": round(carbs_calories, 1),
                        "fats_calories": round(fats_calories, 1)
                    },
                    "per_100g": {
                        "calories": round(total_calories / float(dish.serving_size_g) * 100, 1),
                        "protein_g": round(protein_g / float(dish.serving_size_g) * 100, 1),
                        "carbs_g": round(carbs_g / float(dish.serving_size_g) * 100, 1),
                        "fats_g": round(fats_g / float(dish.serving_size_g) * 100, 1)
                    }
                }
                
                return json.dumps({
                    "success": True,
                    "data": nutrition_data,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "diet_planner_agent"
                    }
                })
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in calculate_nutrition: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to calculate nutrition. Please try again."
                })
            except Exception as e:
                logger.error(f"Unexpected error in calculate_nutrition: {e}")
                return json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred. Please try again."
                })
        
        return [get_current_meal_plan, suggest_meal_substitution, get_recipe_details, calculate_nutrition]
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the diet planner agent.
        
        Creates a specialized system prompt that includes user context,
        nutrition expertise, and behavioral guidelines. The prompt varies
        based on whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        # Get dietary preferences from context if available
        dietary_info = ""
        if hasattr(self.context, 'dietary_preferences'):
            dietary_info = f"""
Dietary Preferences:
- Diet Type: {getattr(self.context, 'diet_type', 'Not specified')}
- Allergies: {', '.join(getattr(self.context, 'allergies', [])) or 'None'}
- Restrictions: {', '.join(getattr(self.context, 'restrictions', [])) or 'None'}
"""
        
        base_prompt = f"""You are a professional nutrition and meal planning assistant for the Shuren fitness coaching system.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
{dietary_info}

Your Expertise:
- Meal planning and nutrition guidance
- Recipe recommendations and substitutions
- Macronutrient calculations
- Dietary restriction management
- Practical cooking advice

Guidelines:
- Respect all dietary preferences, allergies, and restrictions
- Provide nutritional information when relevant
- Suggest practical meal alternatives
- Never provide medical advice or diagnose conditions
- Use tools to fetch meal data or nutritional information when needed
- Focus on sustainable, enjoyable eating habits
- Consider cultural food preferences (Indian cuisine focus)

Available Tools:
- get_current_meal_plan: Retrieve today's meal plan
- suggest_meal_substitution: Generate alternative meal suggestions
- get_recipe_details: Get recipe ingredients and cooking instructions
- calculate_nutrition: Calculate macros and calories for dishes
"""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction (under 30 seconds when spoken, approximately 75 words)."
        else:
            base_prompt += "\n\nIMPORTANT: Provide detailed nutritional breakdowns with markdown formatting for text interaction. Use headers, lists, and emphasis to improve readability."
        
        return base_prompt

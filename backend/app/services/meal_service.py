"""Meal service for managing meal plans, templates, and recipes."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishIngredient, Ingredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile


class MealService:
    """Service for meal-related database operations."""
    
    @staticmethod
    async def get_today_meal_plan(
        user_id: UUID,
        db_session: AsyncSession
    ) -> Optional[dict[str, Any]]:
        """Get today's meal plan for a user.
        
        Queries MealTemplate, TemplateMeal, Dish, MealSchedule, and MealPlan tables
        to build a complete meal plan for today with nutritional information.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            
        Returns:
            Dict with meal details or None if no meal plan configured
            
        Raises:
            ValueError: If user profile not found
        """
        # Get user's profile to verify existence
        profile_result = await db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.meal_schedules),
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_templates)
            )
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"User profile not found for user_id: {user_id}")
        
        # Check if user has meal plan configured
        if not profile.meal_plan:
            return None
        
        # Check if user has meal templates
        if not profile.meal_templates:
            return None
        
        # Get current day of week (0=Monday, 6=Sunday)
        current_day = datetime.now().weekday()
        
        # Find active meal template
        active_template = None
        for template in profile.meal_templates:
            if template.is_active and template.deleted_at is None:
                active_template = template
                break
        
        if not active_template:
            return None
        
        # Get template meals for today with dish and meal schedule details
        template_meals_result = await db_session.execute(
            select(TemplateMeal)
            .where(
                TemplateMeal.template_id == active_template.id,
                TemplateMeal.day_of_week == current_day,
                TemplateMeal.is_primary == True,
                TemplateMeal.deleted_at.is_(None)
            )
            .options(
                selectinload(TemplateMeal.dish),
                selectinload(TemplateMeal.meal_schedule)
            )
        )
        template_meals = template_meals_result.scalars().all()
        
        if not template_meals:
            return None
        
        # Build meals list
        meals = []
        daily_calories = 0.0
        daily_protein = 0.0
        daily_carbs = 0.0
        daily_fats = 0.0
        
        for template_meal in template_meals:
            dish = template_meal.dish
            meal_schedule = template_meal.meal_schedule
            
            # Skip if dish or meal_schedule is soft deleted
            if dish.deleted_at is not None or meal_schedule.deleted_at is not None:
                continue
            
            # Add to daily totals
            daily_calories += float(dish.calories)
            daily_protein += float(dish.protein_g)
            daily_carbs += float(dish.carbs_g)
            daily_fats += float(dish.fats_g)
            
            meals.append({
                "meal_name": meal_schedule.meal_name,
                "scheduled_time": meal_schedule.scheduled_time.isoformat() if meal_schedule.scheduled_time else None,
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
            })
        
        # Build response dict matching design spec
        return {
            "day_of_week": current_day,
            "meals": meals,
            "daily_totals": {
                "calories": daily_calories,
                "protein_g": daily_protein,
                "carbs_g": daily_carbs,
                "fats_g": daily_fats
            },
            "targets": {
                "daily_calorie_target": profile.meal_plan.daily_calorie_target,
                "protein_percentage": float(profile.meal_plan.protein_percentage),
                "carbs_percentage": float(profile.meal_plan.carbs_percentage),
                "fats_percentage": float(profile.meal_plan.fats_percentage)
            }
        }
    
    @staticmethod
    async def get_recipe_details(
        dish_name: str,
        db_session: AsyncSession
    ) -> Optional[dict[str, Any]]:
        """Get recipe details including ingredients and cooking instructions.
        
        Queries Dish, DishIngredient, and Ingredient tables with case-insensitive
        partial match to find recipe details.
        
        Args:
            dish_name: Name of dish (case-insensitive partial match)
            db_session: Database session
            
        Returns:
            Dict with recipe details or None if not found
        """
        # Query Dish with case-insensitive partial match
        dish_result = await db_session.execute(
            select(Dish)
            .where(
                func.lower(Dish.name).contains(func.lower(dish_name)),
                Dish.deleted_at.is_(None),
                Dish.is_active == True
            )
            .options(
                selectinload(Dish.dish_ingredients)
                .selectinload(DishIngredient.ingredient)
            )
            .limit(1)
        )
        dish = dish_result.scalar_one_or_none()
        
        if not dish:
            return None
        
        # Build ingredients list
        ingredients = []
        for dish_ingredient in dish.dish_ingredients:
            if dish_ingredient.deleted_at is None and dish_ingredient.ingredient.deleted_at is None:
                ingredients.append({
                    "name": dish_ingredient.ingredient.name,
                    "name_hindi": dish_ingredient.ingredient.name_hindi,
                    "quantity": float(dish_ingredient.quantity),
                    "unit": dish_ingredient.unit,
                    "preparation_note": dish_ingredient.preparation_note,
                    "is_optional": dish_ingredient.is_optional
                })
        
        # Build response dict matching design spec
        return {
            "dish_name": dish.name,
            "dish_name_hindi": dish.name_hindi,
            "description": dish.description,
            "cuisine_type": dish.cuisine_type,
            "meal_type": dish.meal_type,
            "difficulty_level": dish.difficulty_level,
            "prep_time_minutes": dish.prep_time_minutes,
            "cook_time_minutes": dish.cook_time_minutes,
            "serving_size_g": float(dish.serving_size_g),
            "nutrition": {
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
            "ingredients": ingredients
        }

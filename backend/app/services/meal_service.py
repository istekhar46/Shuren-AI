"""Meal service for managing meal plans, templates, and recipes."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile
from fastapi import HTTPException
from app.schemas.meal import (
    MealPlanResponse,
    MealPlanUpdate,
    MealScheduleItemResponse,
    MealScheduleResponse,
    MealScheduleItemUpdate
)


class MealService:
    """Service for meal-related database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize meal service."""
        self.db_session = db

    async def get_meal_plan(self, user_id: UUID) -> Optional[MealPlanResponse]:
        """Get the user's meal plan and associated properties."""
        profile_result = await self.db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_schedules)
            )
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile or not profile.meal_plan:
            return None
            
        mp = profile.meal_plan
        meals_per_day = len(profile.meal_schedules) if profile.meal_schedules else 0
        
        # MealPlanResponse maps directly
        return MealPlanResponse(
            id=mp.id,
            meals_per_day=meals_per_day,
            daily_calories_target=mp.daily_calorie_target,
            daily_calories_min=int(mp.daily_calorie_target * 0.9),
            daily_calories_max=int(mp.daily_calorie_target * 1.1),
            protein_grams_target=mp.protein_grams,
            carbs_grams_target=mp.carbs_grams,
            fats_grams_target=mp.fats_grams,
            protein_percentage=mp.protein_percentage,
            carbs_percentage=mp.carbs_percentage,
            fats_percentage=mp.fats_percentage,
            plan_rationale="AI-optimized breakdown",
            created_at=mp.created_at,
            updated_at=mp.updated_at
        )

    async def update_meal_plan(self, user_id: UUID, updates: dict[str, Any]) -> MealPlanResponse:
        """Update meal plan details."""
        profile_result = await self.db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(selectinload(UserProfile.meal_plan))
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        if not profile.meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
            
        mp = profile.meal_plan
        if "daily_calories_target" in updates:
            mp.daily_calorie_target = updates["daily_calories_target"]
        if "protein_grams_target" in updates:
            mp.protein_grams = updates["protein_grams_target"]
        if "carbs_grams_target" in updates:
            mp.carbs_grams = updates["carbs_grams_target"]
        if "fats_grams_target" in updates:
            mp.fats_grams = updates["fats_grams_target"]
            
        await self.db_session.commit()
        return await self.get_meal_plan(user_id)

    async def get_meal_schedule(self, user_id: UUID) -> list[MealScheduleItemResponse]:
        """Get the user's meal schedule execution."""
        profile_result = await self.db_session.execute(
            select(UserProfile).where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            ).options(selectinload(UserProfile.meal_schedules))
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        schedules = []
        for i, ms in enumerate(sorted(profile.meal_schedules, key=lambda x: x.scheduled_time)):
            # Ignore soft-deleted items
            if ms.deleted_at is not None:
                continue
            schedules.append(MealScheduleItemResponse(
                id=ms.id,
                meal_number=i + 1,
                meal_name=ms.meal_name,
                scheduled_time=ms.scheduled_time,
                notification_offset_minutes=-30,  # Default fallback
                earliest_time=ms.scheduled_time,
                latest_time=ms.scheduled_time,
                is_active=True
            ))
            
        return schedules

    async def update_meal_schedule(self, user_id: UUID, updates: list[dict[str, Any]]) -> list[MealScheduleItemResponse]:
        """Update items in the meal schedule block."""
        profile_result = await self.db_session.execute(
            select(UserProfile).where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            ).options(selectinload(UserProfile.meal_schedules))
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        # For simplicity in this mock, we map schedule updates by index mapping
        active_schedules = sorted([m for m in profile.meal_schedules if m.deleted_at is None], key=lambda x: x.scheduled_time)
        
        for update_item in updates:
            idx = update_item.get("meal_number", 1) - 1
            if 0 <= idx < len(active_schedules):
                ms = active_schedules[idx]
                if "scheduled_time" in update_item:
                    import datetime
                    if isinstance(update_item["scheduled_time"], str):
                        ms.scheduled_time = datetime.datetime.strptime(update_item["scheduled_time"], "%H:%M:%S").time()
                    else:
                        ms.scheduled_time = update_item["scheduled_time"]
                if "meal_name" in update_item:
                    ms.meal_name = update_item["meal_name"]
                    
        await self.db_session.commit()
        return await self.get_meal_schedule(user_id)
        
    @staticmethod
    async def get_meal_plan_for_date(
        user_id: UUID,
        db_session: AsyncSession,
        target_date: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Get the meal plan for a specific date (defaults to today).
        
        Queries MealTemplate, TemplateMeal, Dish, MealSchedule, and MealPlan tables
        to build a complete meal plan for the given date with nutritional information.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            target_date: Optional ISO format date string (YYYY-MM-DD). If None, uses today.
            
            
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
        
        # Get target day of week (0=Monday, 6=Sunday)
        if target_date:
            try:
                # Parse to handle either ISO format or just YYYY-MM-DD
                dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                current_day = dt.weekday()
            except ValueError:
                raise ValueError(f"Invalid date format: {target_date}. Please use ISO format (e.g., YYYY-MM-DD).")
        else:
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
    async def update_meal_dish(
        user_id: UUID,
        db_session: AsyncSession,
        target_date: str,
        meal_name: str,
        new_dish_name: str
    ) -> dict[str, Any]:
        """Update a specific meal with a new dish in the user's meal plan.
        
        Args:
            user_id: User's UUID
            db_session: Database session
            target_date: ISO format date string
            meal_name: Name of the meal slot (e.g., 'breakfast', 'dinner', 'snack')
            new_dish_name: Name of the new dish to substitute
            
        Returns:
            Dict indicating success and potentially the new meal plan
        """
        # Parse date to get day of week
        try:
            dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            current_day = dt.weekday()
        except ValueError:
            raise ValueError(f"Invalid date format: {target_date}. Please use ISO format (e.g., YYYY-MM-DD).")
        
        # Verify user profile exists
        profile_result = await db_session.execute(
            select(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.meal_templates)
            )
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"User profile not found")
        
        # Find active meal template
        active_template = None
        for template in profile.meal_templates:
            if template.is_active and template.deleted_at is None:
                active_template = template
                break
                
        if not active_template:
            raise ValueError("No active meal template found for user")
            
        # Get new dish
        dish_result = await db_session.execute(
            select(Dish)
            .where(
                func.lower(Dish.name).contains(func.lower(new_dish_name)),
                Dish.deleted_at.is_(None),
                Dish.is_active == True
            )
            .limit(1)
        )
        new_dish = dish_result.scalar_one_or_none()
        if not new_dish:
            raise ValueError(f"Dish '{new_dish_name}' not found")
            
        # Get target TemplateMeal by meal_schedule meal_name
        template_meals_result = await db_session.execute(
            select(TemplateMeal)
            .where(
                TemplateMeal.template_id == active_template.id,
                TemplateMeal.day_of_week == current_day,
                TemplateMeal.is_primary == True,
                TemplateMeal.deleted_at.is_(None)
            )
            .options(selectinload(TemplateMeal.meal_schedule))
        )
        template_meals = template_meals_result.scalars().all()
        
        target_template_meal = None
        for tm in template_meals:
            if tm.meal_schedule.deleted_at is None and tm.meal_schedule.meal_name.lower() == meal_name.lower() or meal_name.lower() in tm.meal_schedule.meal_name.lower():
                target_template_meal = tm
                break
                
        if not target_template_meal:
            raise ValueError(f"Meal slot '{meal_name}' not found in the plan for the specified day")
            
        # Update dish
        target_template_meal.dish_id = new_dish.id
        await db_session.commit()
        
        return {"success": True, "message": f"Successfully updated {meal_name} to {new_dish.name}"}

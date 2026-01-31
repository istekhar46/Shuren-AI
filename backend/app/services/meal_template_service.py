"""Meal template service for managing weekly meal plans with dish assignments."""

from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ProfileLockedException
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealSchedule
from app.models.profile import UserProfile
from app.services.dish_service import DishService


class MealTemplateService:
    """Service for managing meal templates."""
    
    def __init__(self, db: AsyncSession):
        """Initialize MealTemplateService with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.dish_service = DishService(db)
    
    async def get_active_template(self, profile_id: UUID) -> Optional[MealTemplate]:
        """Get user's currently active meal template.
        
        Determines the current week number based on a 4-week rotation
        and retrieves the corresponding template with all related data.
        
        Args:
            profile_id: UUID of the user profile
            
        Returns:
            MealTemplate object if found, None otherwise
        """
        # Determine current week number (1-4 rotation)
        week_of_year = date.today().isocalendar()[1]
        current_week = ((week_of_year - 1) % 4) + 1
        
        result = await self.db.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile_id,
                MealTemplate.week_number == current_week,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish),
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.meal_schedule)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_today_meals(self, profile_id: UUID) -> dict:
        """Get today's meals with dish recommendations.
        
        Retrieves all meals scheduled for today with primary and alternative
        dish options. Calculates nutritional totals for the day.
        
        Args:
            profile_id: UUID of the user profile
            
        Returns:
            Dict containing today's date, meals, and nutritional totals
            
        Raises:
            HTTPException: If no active meal template is found
        """
        template = await self.get_active_template(profile_id)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active meal template found"
            )
        
        # Get today's day of week (0=Monday, 6=Sunday)
        today = date.today()
        day_of_week = today.weekday()
        
        # Filter template meals for today
        today_meals = [
            tm for tm in template.template_meals
            if tm.day_of_week == day_of_week
        ]
        
        # Group by meal schedule
        meals_by_schedule = {}
        for tm in today_meals:
            schedule_id = tm.meal_schedule_id
            if schedule_id not in meals_by_schedule:
                meals_by_schedule[schedule_id] = {
                    'meal_schedule': tm.meal_schedule,
                    'primary': None,
                    'alternatives': []
                }
            
            if tm.is_primary:
                meals_by_schedule[schedule_id]['primary'] = tm.dish
            else:
                meals_by_schedule[schedule_id]['alternatives'].append(tm.dish)
        
        # Build response
        meals = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for schedule_data in meals_by_schedule.values():
            primary_dish = schedule_data['primary']
            if primary_dish:
                meals.append({
                    'meal_name': schedule_data['meal_schedule'].meal_name,
                    'scheduled_time': schedule_data['meal_schedule'].scheduled_time,
                    'day_of_week': day_of_week,
                    'primary_dish': primary_dish,
                    'alternative_dishes': schedule_data['alternatives']
                })
                
                total_calories += float(primary_dish.calories)
                total_protein += float(primary_dish.protein_g)
                total_carbs += float(primary_dish.carbs_g)
                total_fats += float(primary_dish.fats_g)
        
        # Sort by scheduled time
        meals.sort(key=lambda m: m['scheduled_time'])
        
        return {
            'date': today.isoformat(),
            'day_of_week': day_of_week,
            'day_name': today.strftime('%A'),
            'meals': meals,
            'total_calories': total_calories,
            'total_protein_g': total_protein,
            'total_carbs_g': total_carbs,
            'total_fats_g': total_fats
        }
    
    async def get_next_meal(self, profile_id: UUID) -> Optional[dict]:
        """Get next upcoming meal with dish recommendations.
        
        Finds the next meal after the current time and calculates
        how many minutes until that meal.
        
        Args:
            profile_id: UUID of the user profile
            
        Returns:
            Dict containing next meal details, or None if no more meals today
        """
        today_meals_data = await self.get_today_meals(profile_id)
        current_time = datetime.now().time()
        
        # Find next meal after current time
        for meal in today_meals_data['meals']:
            if meal['scheduled_time'] > current_time:
                # Calculate time until meal
                now = datetime.now()
                meal_datetime = datetime.combine(date.today(), meal['scheduled_time'])
                time_diff = meal_datetime - now
                minutes_until = int(time_diff.total_seconds() / 60)
                
                return {
                    'meal_name': meal['meal_name'],
                    'scheduled_time': meal['scheduled_time'],
                    'time_until_meal_minutes': minutes_until,
                    'primary_dish': meal['primary_dish'],
                    'alternative_dishes': meal['alternative_dishes']
                }
        
        return None
    
    async def get_template_by_week(
        self,
        profile_id: UUID,
        week_number: int
    ) -> Optional[MealTemplate]:
        """Get specific week template.
        
        Retrieves a meal template for a specific week number (1-4)
        with all related meals, dishes, and schedules.
        
        Args:
            profile_id: UUID of the user profile
            week_number: Week number (1-4)
            
        Returns:
            MealTemplate object if found, None otherwise
        """
        result = await self.db.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile_id,
                MealTemplate.week_number == week_number,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish),
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.meal_schedule)
            )
        )
        return result.scalar_one_or_none()
    
    async def generate_template(
        self,
        profile_id: UUID,
        week_number: int,
        preferences: Optional[str] = None
    ) -> MealTemplate:
        """Generate new meal template for user.
        
        Creates a complete weekly meal template with specific dish assignments
        for each meal slot. Generates primary dish and 2 alternatives per slot.
        
        Args:
            profile_id: UUID of the user profile
            week_number: Week number (1-4) for the template
            preferences: Optional user preferences for generation
            
        Returns:
            MealTemplate object with all template meals
            
        Raises:
            ProfileLockedException: If profile is locked
            HTTPException: If profile not found or missing required data
        """
        # Check profile lock
        profile = await self._get_profile(profile_id)
        if profile.is_locked:
            raise ProfileLockedException()
        
        # Get user's meal plan and schedules
        meal_plan = profile.meal_plan
        meal_schedules = profile.meal_schedules
        dietary_prefs = profile.dietary_preferences
        
        if not meal_plan or not meal_schedules:
            raise HTTPException(
                status_code=400,
                detail="User must have meal plan and schedules configured"
            )
        
        # Calculate per-meal targets
        meals_per_day = len(meal_schedules)
        daily_calories = meal_plan.daily_calorie_target
        daily_protein = float(meal_plan.protein_percentage) / 100 * daily_calories / 4  # 4 cal/g
        
        # Create template
        template = MealTemplate(
            profile_id=profile_id,
            week_number=week_number,
            is_active=True,
            generated_by='ai_agent',
            generation_reason=preferences or 'Initial template generation'
        )
        self.db.add(template)
        await self.db.flush()
        
        # Generate meals for each day of the week
        for day in range(7):  # 0=Monday to 6=Sunday
            for schedule in meal_schedules:
                # Determine meal type and targets
                meal_type = self._determine_meal_type(schedule.meal_name)
                cal_target, protein_target = self._calculate_meal_targets(
                    schedule.meal_name,
                    daily_calories,
                    daily_protein,
                    meals_per_day
                )
                
                # Get suitable dishes (1 primary + 2 alternatives)
                dishes = await self.dish_service.get_dishes_for_meal_slot(
                    meal_type=meal_type,
                    target_calories=cal_target,
                    target_protein=protein_target,
                    dietary_preferences={
                        'diet_type': dietary_prefs.diet_type,
                        'allergies': dietary_prefs.allergies
                    },
                    count=3
                )
                
                if not dishes:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Could not find suitable dishes for {schedule.meal_name}"
                    )
                
                # Create template meals
                for idx, dish in enumerate(dishes):
                    template_meal = TemplateMeal(
                        template_id=template.id,
                        meal_schedule_id=schedule.id,
                        dish_id=dish.id,
                        day_of_week=day,
                        is_primary=(idx == 0),
                        alternative_order=idx + 1
                    )
                    self.db.add(template_meal)
        
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def swap_dish(
        self,
        profile_id: UUID,
        day_of_week: int,
        meal_name: str,
        new_dish_id: UUID
    ) -> MealTemplate:
        """Swap a dish in the template.
        
        Replaces the primary dish for a specific meal slot with a new dish.
        Validates profile lock status and ensures the new dish exists.
        
        Args:
            profile_id: UUID of the user profile
            day_of_week: Day of week (0=Monday, 6=Sunday)
            meal_name: Name of the meal to swap
            new_dish_id: UUID of the new dish
            
        Returns:
            Updated MealTemplate object
            
        Raises:
            ProfileLockedException: If profile is locked
            HTTPException: If template, meal schedule, dish, or template meal not found
        """
        # Check profile lock
        profile = await self._get_profile(profile_id)
        if profile.is_locked:
            raise ProfileLockedException()
        
        # Get active template
        template = await self.get_active_template(profile_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active template found"
            )
        
        # Find meal schedule by name
        meal_schedule = next(
            (s for s in profile.meal_schedules if s.meal_name == meal_name),
            None
        )
        if not meal_schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Meal schedule '{meal_name}' not found"
            )
        
        # Verify new dish exists and is suitable
        new_dish = await self.dish_service.get_dish(new_dish_id)
        if not new_dish:
            raise HTTPException(
                status_code=404,
                detail="Dish not found"
            )
        
        # Find and update primary template meal
        result = await self.db.execute(
            select(TemplateMeal)
            .where(
                TemplateMeal.template_id == template.id,
                TemplateMeal.meal_schedule_id == meal_schedule.id,
                TemplateMeal.day_of_week == day_of_week,
                TemplateMeal.is_primary == True
            )
        )
        template_meal = result.scalar_one_or_none()
        
        if not template_meal:
            raise HTTPException(
                status_code=404,
                detail="Template meal not found"
            )
        
        # Update dish
        template_meal.dish_id = new_dish_id
        
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    def _determine_meal_type(self, meal_name: str) -> str:
        """Determine meal type from meal name.
        
        Maps meal schedule names to dish meal types.
        
        Args:
            meal_name: Name of the meal from schedule
            
        Returns:
            Meal type string for dish filtering
        """
        meal_name_lower = meal_name.lower()
        
        if 'pre' in meal_name_lower and 'workout' in meal_name_lower:
            return 'pre_workout'
        elif 'post' in meal_name_lower and 'workout' in meal_name_lower:
            return 'post_workout'
        elif 'breakfast' in meal_name_lower:
            return 'breakfast'
        elif 'lunch' in meal_name_lower:
            return 'lunch'
        elif 'dinner' in meal_name_lower:
            return 'dinner'
        else:
            return 'snack'
    
    def _calculate_meal_targets(
        self,
        meal_name: str,
        daily_calories: int,
        daily_protein: float,
        meals_per_day: int
    ) -> tuple[float, float]:
        """Calculate calorie and protein targets for a meal.
        
        Uses predefined distribution percentages based on meal type.
        Falls back to equal distribution if meal type not recognized.
        
        Args:
            meal_name: Name of the meal from schedule
            daily_calories: Total daily calorie target
            daily_protein: Total daily protein target in grams
            meals_per_day: Number of meals per day
            
        Returns:
            Tuple of (calorie_target, protein_target)
        """
        meal_type = self._determine_meal_type(meal_name)
        
        # Distribution percentages (calories, protein)
        distributions = {
            'pre_workout': (0.10, 0.10),  # 10% calories, 10% protein
            'post_workout': (0.15, 0.20),  # 15% calories, 20% protein
            'breakfast': (0.30, 0.30),     # 30% calories, 30% protein
            'lunch': (0.35, 0.30),         # 35% calories, 30% protein
            'dinner': (0.30, 0.25),        # 30% calories, 25% protein
            'snack': (0.10, 0.10)          # 10% calories, 10% protein
        }
        
        cal_pct, protein_pct = distributions.get(
            meal_type,
            (1.0 / meals_per_day, 1.0 / meals_per_day)
        )
        
        return (
            daily_calories * cal_pct,
            daily_protein * protein_pct
        )
    
    async def _get_profile(self, profile_id: UUID) -> UserProfile:
        """Get user profile with relationships.
        
        Helper method to retrieve a user profile with all necessary
        relationships eagerly loaded.
        
        Args:
            profile_id: UUID of the user profile
            
        Returns:
            UserProfile object
            
        Raises:
            HTTPException: If profile is not found
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(
                UserProfile.id == profile_id,
                UserProfile.deleted_at.is_(None)
            )
            .options(
                selectinload(UserProfile.meal_plan),
                selectinload(UserProfile.meal_schedules),
                selectinload(UserProfile.dietary_preferences)
            )
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        return profile

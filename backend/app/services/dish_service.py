"""Dish service for managing dishes and ingredients."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishIngredient, Ingredient


class DishService:
    """Service for managing dishes and ingredients."""
    
    def __init__(self, db: AsyncSession):
        """Initialize DishService with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_dish(
        self,
        dish_id: UUID,
        include_ingredients: bool = False
    ) -> Optional[Dish]:
        """Get dish by ID with optional ingredients.
        
        Args:
            dish_id: UUID of the dish to retrieve
            include_ingredients: Whether to eagerly load ingredients
            
        Returns:
            Dish object if found, None otherwise
        """
        query = select(Dish).where(
            Dish.id == dish_id,
            Dish.deleted_at.is_(None),
            Dish.is_active == True
        )
        
        if include_ingredients:
            query = query.options(
                selectinload(Dish.dish_ingredients).selectinload(DishIngredient.ingredient)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_dishes(
        self,
        meal_type: Optional[str] = None,
        diet_type: Optional[str] = None,
        max_prep_time: Optional[int] = None,
        max_calories: Optional[int] = None,
        exclude_allergens: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dish]:
        """Search dishes with filters.
        
        Args:
            meal_type: Filter by meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)
            diet_type: Filter by diet type (vegetarian, vegan)
            max_prep_time: Maximum total preparation + cooking time in minutes
            max_calories: Maximum calories per serving
            exclude_allergens: List of allergens to exclude
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination
            
        Returns:
            List of Dish objects matching the filters
        """
        query = select(Dish).where(
            Dish.deleted_at.is_(None),
            Dish.is_active == True
        )
        
        # Apply filters
        if meal_type:
            query = query.where(Dish.meal_type == meal_type)
        
        if diet_type == 'vegetarian':
            query = query.where(Dish.is_vegetarian == True)
        elif diet_type == 'vegan':
            query = query.where(Dish.is_vegan == True)
        
        if max_prep_time:
            query = query.where(
                Dish.prep_time_minutes + Dish.cook_time_minutes <= max_prep_time
            )
        
        if max_calories:
            query = query.where(Dish.calories <= max_calories)
        
        if exclude_allergens:
            for allergen in exclude_allergens:
                query = query.where(~Dish.contains_allergens.contains([allergen]))
        
        # Order by popularity
        query = query.order_by(Dish.popularity_score.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_dishes_for_meal_slot(
        self,
        meal_type: str,
        target_calories: float,
        target_protein: float,
        dietary_preferences: dict,
        count: int = 3
    ) -> List[Dish]:
        """Get suitable dishes for a specific meal slot.
        
        Finds dishes that match the meal type and fall within acceptable
        nutritional ranges (±15% for calories, ±20% for protein).
        
        Args:
            meal_type: Type of meal (breakfast, lunch, dinner, snack, pre_workout, post_workout)
            target_calories: Target calories for this meal
            target_protein: Target protein in grams for this meal
            dietary_preferences: Dict containing diet_type and allergies
            count: Number of dishes to return (default 3)
            
        Returns:
            List of Dish objects suitable for the meal slot
        """
        # Calculate acceptable ranges (±15% for calories, ±20% for protein)
        cal_min = target_calories * 0.85
        cal_max = target_calories * 1.15
        protein_min = target_protein * 0.80
        protein_max = target_protein * 1.20
        
        query = select(Dish).where(
            Dish.deleted_at.is_(None),
            Dish.is_active == True,
            Dish.meal_type == meal_type,
            Dish.calories.between(cal_min, cal_max),
            Dish.protein_g.between(protein_min, protein_max)
        )
        
        # Apply dietary filters
        diet_type = dietary_preferences.get('diet_type')
        if diet_type == 'vegetarian':
            query = query.where(Dish.is_vegetarian == True)
        elif diet_type == 'vegan':
            query = query.where(Dish.is_vegan == True)
        
        # Exclude allergens
        allergies = dietary_preferences.get('allergies', [])
        for allergen in allergies:
            query = query.where(~Dish.contains_allergens.contains([allergen]))
        
        # Order by popularity and limit
        query = query.order_by(Dish.popularity_score.desc()).limit(count)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

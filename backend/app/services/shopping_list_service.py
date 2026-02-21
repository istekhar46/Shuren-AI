"""Shopping list service for aggregating ingredients from meal templates."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishIngredient, Ingredient
from app.models.meal_template import MealTemplate, TemplateMeal
from app.schemas.shopping_list import (
    ShoppingListCategory,
    ShoppingListIngredient,
    ShoppingListResponse,
)


class ShoppingListService:
    """Service for generating shopping lists from meal templates."""
    
    # Category display order for organized shopping
    CATEGORY_ORDER = [
        'protein',
        'vegetable',
        'fruit',
        'grain',
        'dairy',
        'spice',
        'oil',
        'other'
    ]
    
    def __init__(self, db: AsyncSession):
        """Initialize ShoppingListService with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def generate_shopping_list(
        self,
        profile_id: UUID,
        weeks: int = 1
    ) -> ShoppingListResponse:
        """Generate shopping list for user's meal template.
        
        Aggregates all ingredients from primary dishes in the user's active
        meal template, calculates total quantities needed for the specified
        number of weeks, and organizes them by category.
        
        Args:
            profile_id: UUID of the user profile
            weeks: Number of weeks to generate list for (1-4, default 1)
            
        Returns:
            ShoppingListResponse with categorized ingredients
            
        Raises:
            HTTPException: If no active meal template is found or weeks is invalid
        """
        if weeks < 1 or weeks > 4:
            raise HTTPException(
                status_code=400,
                detail="Weeks must be between 1 and 4"
            )
        
        # Determine current week number (1-4 rotation)
        week_of_year = date.today().isocalendar()[1]
        current_week = ((week_of_year - 1) % 4) + 1
        
        # Get active meal template with all relationships
        result = await self.db.execute(
            select(MealTemplate)
            .where(
                MealTemplate.profile_id == profile_id,
                MealTemplate.week_number == current_week,
                MealTemplate.deleted_at.is_(None)
            )
            .options(
                selectinload(MealTemplate.template_meals)
                .selectinload(TemplateMeal.dish)
                .selectinload(Dish.dish_ingredients)
                .selectinload(DishIngredient.ingredient)
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="No active meal template found"
            )
        
        # Aggregate ingredients from primary dishes only
        ingredient_data = self._aggregate_ingredients(template, weeks)
        
        # Group by category and sort
        categories = self._group_by_category(ingredient_data)
        
        # Calculate date range
        today = date.today()
        end_date = today + timedelta(days=weeks * 7 - 1)
        
        return ShoppingListResponse(
            week_number=current_week,
            start_date=today.isoformat(),
            end_date=end_date.isoformat(),
            categories=categories,
            total_items=sum(len(cat.ingredients) for cat in categories)
        )
    
    def _aggregate_ingredients(
        self,
        template: MealTemplate,
        weeks: int
    ) -> Dict[UUID, Dict]:
        """Aggregate ingredients from all primary dishes in template.
        
        Collects all ingredients from primary dishes, calculates total
        quantities needed for the specified number of weeks (7 days per week),
        and tracks which dishes use each ingredient.
        
        Args:
            template: MealTemplate with loaded relationships
            weeks: Number of weeks to calculate for
            
        Returns:
            Dict mapping ingredient_id to aggregated ingredient data
        """
        # Use defaultdict to aggregate quantities
        ingredient_aggregates: Dict[UUID, Dict] = defaultdict(lambda: {
            'ingredient': None,
            'total_quantity': Decimal('0'),
            'unit': None,
            'is_optional': False,
            'used_in_dishes': set()
        })
        
        # Filter for primary dishes only
        primary_meals = [
            tm for tm in template.template_meals
            if tm.is_primary
        ]
        
        # Aggregate ingredients from each primary dish
        # Note: template_meals already contains 7 days of meals (one per day_of_week)
        # So we only need to multiply by weeks, not by weeks × 7
        for template_meal in primary_meals:
            dish = template_meal.dish
            
            for dish_ingredient in dish.dish_ingredients:
                ingredient_id = dish_ingredient.ingredient_id
                ingredient = dish_ingredient.ingredient
                
                # Initialize or update aggregate
                agg = ingredient_aggregates[ingredient_id]
                
                if agg['ingredient'] is None:
                    agg['ingredient'] = ingredient
                    agg['unit'] = dish_ingredient.unit
                
                # Add quantity (multiply by weeks only, since we already have 7 days)
                quantity = dish_ingredient.quantity * weeks
                agg['total_quantity'] += quantity
                
                # Track if any dish marks this as optional
                if dish_ingredient.is_optional:
                    agg['is_optional'] = True
                
                # Track which dishes use this ingredient
                agg['used_in_dishes'].add(dish.name)
        
        return dict(ingredient_aggregates)
    
    def _group_by_category(
        self,
        ingredient_data: Dict[UUID, Dict]
    ) -> List[ShoppingListCategory]:
        """Group ingredients by category and sort.
        
        Organizes ingredients into categories following a logical shopping
        order (protein, vegetable, fruit, grain, dairy, spice, oil, other).
        
        Args:
            ingredient_data: Dict of aggregated ingredient data
            
        Returns:
            List of ShoppingListCategory objects sorted by category order
        """
        # Group by category
        categories_dict: Dict[str, List[ShoppingListIngredient]] = defaultdict(list)
        
        for ingredient_id, data in ingredient_data.items():
            ingredient = data['ingredient']
            category = ingredient.category
            
            shopping_ingredient = ShoppingListIngredient(
                ingredient_id=ingredient_id,
                name=ingredient.name,
                name_hindi=ingredient.name_hindi,
                category=category,
                total_quantity=data['total_quantity'],
                unit=data['unit'],
                is_optional=data['is_optional'],
                used_in_dishes=sorted(list(data['used_in_dishes']))
            )
            
            categories_dict[category].append(shopping_ingredient)
        
        # Sort categories by predefined order
        sorted_categories = []
        for category_name in self.CATEGORY_ORDER:
            if category_name in categories_dict:
                # Sort ingredients within category by name
                ingredients = sorted(
                    categories_dict[category_name],
                    key=lambda x: x.name
                )
                sorted_categories.append(
                    ShoppingListCategory(
                        category=category_name,
                        ingredients=ingredients
                    )
                )
        
        # Add any categories not in predefined order
        for category_name, ingredients in categories_dict.items():
            if category_name not in self.CATEGORY_ORDER:
                ingredients = sorted(ingredients, key=lambda x: x.name)
                sorted_categories.append(
                    ShoppingListCategory(
                        category=category_name,
                        ingredients=ingredients
                    )
                )
        
        return sorted_categories

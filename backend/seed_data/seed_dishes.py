"""
Dish seeding script for meal planning system.

This script populates the database with dishes and ingredients from seed data.
It is idempotent and can be run multiple times safely.

Usage:
    poetry run python seed_dishes.py
"""

import asyncio
import sys
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.dish import Dish, Ingredient, DishIngredient
from seed_data.dishes import ALL_DISHES
from seed_data.ingredients import INGREDIENTS


# Cache for ingredients to avoid repeated database queries
ingredient_cache: Dict[str, Ingredient] = {}


async def get_or_create_ingredient(
    db: AsyncSession,
    name: str
) -> Optional[Ingredient]:
    """
    Get an ingredient from cache or database, or create it if it doesn't exist.
    
    Args:
        db: Database session
        name: Ingredient name
        
    Returns:
        Ingredient instance or None if not found in seed data
    """
    # Check cache first
    if name in ingredient_cache:
        return ingredient_cache[name]
    
    # Check database
    result = await db.execute(
        select(Ingredient).where(Ingredient.name == name)
    )
    ingredient = result.scalar_one_or_none()
    
    if ingredient:
        ingredient_cache[name] = ingredient
        return ingredient
    
    # Find in seed data
    ingredient_data = next(
        (ing for ing in INGREDIENTS if ing['name'] == name),
        None
    )
    
    if not ingredient_data:
        print(f"  ⚠️  Warning: Ingredient '{name}' not found in seed data")
        return None
    
    # Create new ingredient
    ingredient = Ingredient(
        name=ingredient_data['name'],
        name_hindi=ingredient_data.get('name_hindi'),
        category=ingredient_data['category'],
        calories_per_100g=Decimal(str(ingredient_data.get('calories_per_100g', 0))) if ingredient_data.get('calories_per_100g') else None,
        protein_per_100g=Decimal(str(ingredient_data.get('protein_per_100g', 0))) if ingredient_data.get('protein_per_100g') else None,
        carbs_per_100g=Decimal(str(ingredient_data.get('carbs_per_100g', 0))) if ingredient_data.get('carbs_per_100g') else None,
        fats_per_100g=Decimal(str(ingredient_data.get('fats_per_100g', 0))) if ingredient_data.get('fats_per_100g') else None,
        typical_unit=ingredient_data['typical_unit'],
        is_allergen=ingredient_data.get('is_allergen', False),
        allergen_type=ingredient_data.get('allergen_type'),
        is_active=True
    )
    
    db.add(ingredient)
    await db.flush()  # Get the ID without committing
    
    ingredient_cache[name] = ingredient
    return ingredient


async def dish_exists(db: AsyncSession, name: str) -> bool:
    """
    Check if a dish already exists in the database.
    
    Args:
        db: Database session
        name: Dish name
        
    Returns:
        True if dish exists, False otherwise
    """
    result = await db.execute(
        select(Dish).where(Dish.name == name)
    )
    return result.scalar_one_or_none() is not None


async def create_dish(db: AsyncSession, dish_data: dict) -> Optional[Dish]:
    """
    Create a dish with all its ingredients.
    
    Args:
        db: Database session
        dish_data: Dictionary containing dish information
        
    Returns:
        Created Dish instance or None if creation failed
    """
    try:
        # Create dish
        dish = Dish(
            name=dish_data['name'],
            name_hindi=dish_data.get('name_hindi'),
            description=dish_data.get('description'),
            cuisine_type=dish_data['cuisine_type'],
            meal_type=dish_data['meal_type'],
            dish_category=dish_data.get('dish_category'),
            serving_size_g=Decimal(str(dish_data['serving_size_g'])),
            calories=Decimal(str(dish_data['calories'])),
            protein_g=Decimal(str(dish_data['protein_g'])),
            carbs_g=Decimal(str(dish_data['carbs_g'])),
            fats_g=Decimal(str(dish_data['fats_g'])),
            fiber_g=Decimal(str(dish_data['fiber_g'])) if dish_data.get('fiber_g') else None,
            prep_time_minutes=dish_data['prep_time_minutes'],
            cook_time_minutes=dish_data['cook_time_minutes'],
            difficulty_level=dish_data['difficulty_level'],
            is_vegetarian=dish_data.get('is_vegetarian', False),
            is_vegan=dish_data.get('is_vegan', False),
            is_gluten_free=dish_data.get('is_gluten_free', False),
            is_dairy_free=dish_data.get('is_dairy_free', False),
            is_nut_free=dish_data.get('is_nut_free', False),
            contains_allergens=dish_data.get('contains_allergens', []),
            is_active=True,
            popularity_score=dish_data.get('popularity_score', 0)
        )
        
        db.add(dish)
        await db.flush()  # Get the dish ID
        
        # Create dish-ingredient relationships
        ingredients_data = dish_data.get('ingredients', [])
        for ing_data in ingredients_data:
            ingredient = await get_or_create_ingredient(db, ing_data['name'])
            
            if not ingredient:
                continue  # Skip if ingredient not found
            
            dish_ingredient = DishIngredient(
                dish_id=dish.id,
                ingredient_id=ingredient.id,
                quantity=Decimal(str(ing_data['quantity'])),
                unit=ing_data['unit'],
                preparation_note=ing_data.get('preparation_note'),
                is_optional=ing_data.get('is_optional', False)
            )
            
            db.add(dish_ingredient)
        
        return dish
        
    except Exception as e:
        print(f"  ❌ Error creating dish '{dish_data['name']}': {str(e)}")
        return None


async def seed_dishes():
    """
    Main seeding function that populates the database with dishes and ingredients.
    """
    print("=" * 80)
    print("🍽️  Starting Dish Seeding Process")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Statistics
            dishes_created = 0
            dishes_skipped = 0
            dishes_failed = 0
            ingredients_created = 0
            
            print(f"📊 Total dishes to process: {len(ALL_DISHES)}")
            print()
            
            # Process each dish
            for idx, dish_data in enumerate(ALL_DISHES, 1):
                dish_name = dish_data['name']
                
                # Check if dish already exists
                if await dish_exists(db, dish_name):
                    print(f"[{idx}/{len(ALL_DISHES)}] ⏭️  Skipping '{dish_name}' (already exists)")
                    dishes_skipped += 1
                    continue
                
                print(f"[{idx}/{len(ALL_DISHES)}] 🔨 Creating '{dish_name}'...")
                
                # Track ingredients before creation
                ingredients_before = len(ingredient_cache)
                
                # Create dish
                dish = await create_dish(db, dish_data)
                
                if dish:
                    await db.commit()
                    dishes_created += 1
                    
                    # Track new ingredients
                    ingredients_after = len(ingredient_cache)
                    new_ingredients = ingredients_after - ingredients_before
                    if new_ingredients > 0:
                        ingredients_created += new_ingredients
                    
                    print(f"  ✅ Created successfully")
                else:
                    await db.rollback()
                    dishes_failed += 1
            
            print()
            print("=" * 80)
            print("📈 Seeding Summary")
            print("=" * 80)
            print(f"✅ Dishes created:     {dishes_created}")
            print(f"⏭️  Dishes skipped:     {dishes_skipped}")
            print(f"❌ Dishes failed:      {dishes_failed}")
            print(f"🥕 Ingredients created: {ingredients_created}")
            print(f"📦 Total ingredients:   {len(ingredient_cache)}")
            print()
            
            if dishes_failed > 0:
                print("⚠️  Some dishes failed to create. Check the logs above for details.")
                return 1
            
            print("🎉 Seeding completed successfully!")
            return 0
            
        except Exception as e:
            print()
            print("=" * 80)
            print("❌ FATAL ERROR")
            print("=" * 80)
            print(f"Error: {str(e)}")
            print()
            import traceback
            traceback.print_exc()
            await db.rollback()
            return 1


def main():
    """Entry point for the seeding script."""
    try:
        exit_code = asyncio.run(seed_dishes())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print("⚠️  Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

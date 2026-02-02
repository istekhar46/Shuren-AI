"""Seed ingredients into the database."""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.dish import Ingredient
from seed_data.ingredients import INGREDIENTS

async def seed_ingredients():
    """Seed ingredients into the database."""
    print("=" * 70)
    print("🥕 Starting Ingredient Seeding Process")
    print("=" * 70)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if ingredients already exist
            result = await db.execute(select(Ingredient))
            existing = result.scalars().all()
            
            if existing:
                print(f"⚠️  Found {len(existing)} existing ingredients")
                print("   Skipping ingredient seeding")
                return
            
            print(f"📊 Total ingredients to process: {len(INGREDIENTS)}")
            print()
            
            created_count = 0
            for idx, ingredient_data in enumerate(INGREDIENTS, 1):
                try:
                    # Create ingredient
                    ingredient = Ingredient(**ingredient_data)
                    db.add(ingredient)
                    
                    print(f"[{idx}/{len(INGREDIENTS)}] ✅ Created '{ingredient.name}'")
                    created_count += 1
                    
                except Exception as e:
                    print(f"[{idx}/{len(INGREDIENTS)}] ❌ Error creating '{ingredient_data.get('name', 'Unknown')}': {e}")
                    continue
            
            # Commit all ingredients
            await db.commit()
            
            print()
            print("=" * 70)
            print(f"✅ Ingredient seeding completed successfully!")
            print(f"   Created: {created_count}/{len(INGREDIENTS)} ingredients")
            print("=" * 70)
            
        except Exception as e:
            print()
            print("=" * 70)
            print("❌ FATAL ERROR")
            print("=" * 70)
            print(f"Error: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_ingredients())

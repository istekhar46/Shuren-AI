"""Verify database schema has the new columns."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine


async def verify_schema():
    """Verify the new columns exist in the database."""
    async with engine.connect() as conn:
        # Check onboarding_states columns
        result = await conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'onboarding_states'
            AND column_name IN ('current_step', 'step_1_complete', 'step_2_complete', 'step_3_complete', 'step_4_complete')
            ORDER BY column_name;
        """))
        
        print("✓ onboarding_states columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (default: {row[2]})")
        
        # Check meal_templates columns
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'meal_templates'
            AND column_name IN ('plan_name', 'daily_calorie_target', 'protein_grams', 'carbs_grams', 'fats_grams', 'weekly_template')
            ORDER BY column_name;
        """))
        
        print("\n✓ meal_templates columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(verify_schema())

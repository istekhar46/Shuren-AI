"""Verify workout_plans table has deleted_at column."""
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def verify():
    """Check workout_plans table structure."""
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'workout_plans' 
            ORDER BY ordinal_position
        """))
        
        print("\nworkout_plans table columns:")
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check if deleted_at exists
        has_deleted_at = any(col[0] == 'deleted_at' for col in columns)
        if has_deleted_at:
            print("\n✓ deleted_at column exists!")
        else:
            print("\n✗ deleted_at column NOT found!")

if __name__ == "__main__":
    asyncio.run(verify())

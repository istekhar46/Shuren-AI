"""Verify exercise library data."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def verify_exercises():
    """Verify the exercise library data."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT exercise_name, exercise_type, difficulty_level, is_compound FROM exercise_library ORDER BY exercise_type, exercise_name")
        )
        rows = result.fetchall()
        
        print(f"\n✅ Total exercises in library: {len(rows)}\n")
        
        # Group by type
        compound = [row for row in rows if row[3]]
        isolation = [row for row in rows if not row[3] and row[1] == 'strength']
        cardio = [row for row in rows if row[1] == 'cardio']
        
        print(f"📊 Breakdown:")
        print(f"  - Compound movements: {len(compound)}")
        print(f"  - Isolation exercises: {len(isolation)}")
        print(f"  - Cardio exercises: {len(cardio)}")
        
        print(f"\n💪 Compound Movements:")
        for row in compound:
            print(f"  - {row[0]} ({row[2]})")
        
        print(f"\n🎯 Isolation Exercises:")
        for row in isolation:
            print(f"  - {row[0]} ({row[2]})")
        
        print(f"\n🏃 Cardio Exercises:")
        for row in cardio:
            print(f"  - {row[0]} ({row[2]})")


if __name__ == "__main__":
    asyncio.run(verify_exercises())

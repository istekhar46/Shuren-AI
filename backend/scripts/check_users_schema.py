"""Check users table schema."""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def check_schema():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        print("Users table columns:")
        for row in result.fetchall():
            print(f"  - {row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(check_schema())

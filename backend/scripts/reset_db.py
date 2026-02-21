"""Drop all tables and reset database to clean state."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def reset_database():
    """Drop all tables in public schema."""
    print("Dropping all tables from database...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Drop all tables in public schema
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            print("✓ All tables dropped")
            
        print("\n✓ Database reset complete!")
        print("Now run: poetry run alembic upgrade head")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_database())

"""Quick script to check database connection and tables."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def check_database():
    """Check database connection and list tables."""
    print(f"Connecting to: {settings.DATABASE_URL[:50]}...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.connect() as conn:
            # Check if we can connect
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Connected to PostgreSQL: {version[:50]}...")
            
            # Check alembic version
            try:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version_num = result.scalar()
                print(f"✓ Alembic version: {version_num}")
            except Exception as e:
                print(f"✗ No alembic_version table: {e}")
            
            # List all tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"\n✓ Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\n✗ No tables found in database!")
                
    except Exception as e:
        print(f"✗ Database error: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database())

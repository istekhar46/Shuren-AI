"""Test database connection and verify tables exist."""
import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

async def test_connection():
    """Test database connection and list tables."""
    print(f"Testing database connection...")
    print(f"Database URL: {settings.async_database_url[:50]}...")
    
    try:
        async with engine.begin() as conn:
            # Test connection
            result = await conn.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
            
            # List tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n✓ Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n✗ No tables found in database!")
                print("  Run migrations: poetry run alembic upgrade head")
            
            # Check if users table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """))
            users_exists = result.scalar()
            
            if users_exists:
                print("\n✓ Users table exists")
                
                # Count users
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"  Total users: {count}")
            else:
                print("\n✗ Users table does NOT exist!")
                
    except Exception as e:
        print(f"\n✗ Database connection failed!")
        print(f"  Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())

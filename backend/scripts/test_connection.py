"""Simple script to test database connection."""
import asyncio
import asyncpg


async def test_connection():
    """Test connection to local databases."""
    print("="*60)
    print("Testing Database Connections")
    print("="*60)
    print()
    
    # Test development database
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='ist@123',
            database='shuren_dev_db'
        )
        
        # Get database name
        db_name = await conn.fetchval("SELECT current_database()")
        print(f"✅ Connected to development database: {db_name}")
        
        # Count tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        print(f"   Tables: {len(tables)}")
        for table in tables[:5]:  # Show first 5 tables
            print(f"   - {table['tablename']}")
        if len(tables) > 5:
            print(f"   ... and {len(tables) - 5} more")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to development database: {e}")
        return False
    
    print()
    
    # Test test database
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='ist@123',
            database='shuren_test_db'
        )
        
        db_name = await conn.fetchval("SELECT current_database()")
        print(f"✅ Connected to test database: {db_name}")
        
        # Count tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        print(f"   Tables: {len(tables)} (should be 0 - tests create/drop tables)")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to test database: {e}")
        return False
    
    print()
    print("="*60)
    print("✅ All database connections successful!")
    print("="*60)
    print()
    print("Your setup is complete! You can now:")
    print("  1. Start the server: run_local.bat")
    print("  2. Run tests: poetry run pytest")
    print()
    
    return True


if __name__ == "__main__":
    asyncio.run(test_connection())

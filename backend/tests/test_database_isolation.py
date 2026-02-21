"""Test to verify database isolation between development and testing.

This test ensures that:
1. Tests use the separate test database (shuren_test_db)
2. Test database is isolated from development database
3. Tables are properly created and dropped for each test
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_isolation(db_session: AsyncSession):
    """Verify that tests use the correct test database.
    
    This test checks that we're connected to 'shuren_test_db' and not
    the development or production database.
    """
    # Get current database name
    result = await db_session.execute(text("SELECT current_database()"))
    db_name = result.scalar()
    
    # Verify we're using the test database
    assert db_name == "shuren_test_db", (
        f"Tests should use 'shuren_test_db' but connected to '{db_name}'. "
        f"This means tests might be affecting your development or production database!"
    )
    
    print(f"✓ Tests are correctly using database: {db_name}")


@pytest.mark.asyncio
async def test_tables_exist(db_session: AsyncSession):
    """Verify that tables are created for the test."""
    # Check if users table exists
    result = await db_session.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        )
    """))
    
    table_exists = result.scalar()
    assert table_exists, "Users table should exist in test database"
    
    print("✓ Tables are properly created for tests")


@pytest.mark.asyncio
async def test_database_is_clean(db_session: AsyncSession):
    """Verify that the database starts clean for each test.
    
    This test should always pass because conftest.py drops all tables
    after each test, ensuring a clean slate.
    """
    # Count users in database
    result = await db_session.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()
    
    # Should be 0 unless fixtures created users
    # (test_user fixture creates 1 user, but we're not using it here)
    assert user_count == 0, (
        f"Database should be empty at test start, but found {user_count} users. "
        f"This indicates test isolation is broken."
    )
    
    print("✓ Database starts clean for each test")


@pytest.mark.asyncio  
async def test_connection_info(db_session: AsyncSession):
    """Display connection information for debugging."""
    # Get connection details
    result = await db_session.execute(text("""
        SELECT 
            current_database() as database,
            current_user as user,
            inet_server_addr() as host,
            inet_server_port() as port
    """))
    
    row = result.fetchone()
    
    print("\n" + "="*50)
    print("Database Connection Info:")
    print("="*50)
    print(f"Database: {row[0]}")
    print(f"User: {row[1]}")
    print(f"Host: {row[2] or 'localhost (Unix socket)'}")
    print(f"Port: {row[3] or 'N/A'}")
    print("="*50)
    
    # Verify it's the test database
    assert row[0] == "shuren_test_db", "Should be connected to test database"

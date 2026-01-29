"""Async database session management for PostgreSQL.

This module provides:
- Async SQLAlchemy engine with asyncpg driver
- Async session factory
- FastAPI dependency for database session injection
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from app.core.config import settings


# Convert postgres:// to postgresql+asyncpg:// if needed
# Aiven and some providers use postgres:// but SQLAlchemy async requires postgresql+asyncpg://
def get_async_database_url(url: str) -> str:
    """Convert database URL to async format if needed."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Create async engine
# - echo=settings.DEBUG: Log SQL queries in debug mode
# - pool_pre_ping=True: Verify connections before using them
# - pool_size=5: Connection pool size for production
engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create async session factory
# - expire_on_commit=False: Prevent additional queries after commit
# - class_=AsyncSession: Use async session class
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session.
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    The session is automatically closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

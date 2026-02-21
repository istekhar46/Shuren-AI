"""Async database session management for PostgreSQL.

This module provides:
- Async SQLAlchemy engine with asyncpg driver
- Async session factory
- FastAPI dependency for database session injection
- Logging configuration to suppress harmless cancellation warnings
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from app.core.config import settings


# Suppress SQLAlchemy pool termination warnings during cancellation
# This is a known issue: https://github.com/sqlalchemy/sqlalchemy/issues/8145
# The error is harmless - it occurs when a client cancels an SSE stream
# and SQLAlchemy tries to terminate the connection gracefully
# The connection is properly cleaned up by the pool despite the warning
logging.getLogger('sqlalchemy.pool.impl.AsyncAdaptedQueuePool').setLevel(logging.CRITICAL)


# Convert postgres:// to postgresql+asyncpg:// if needed
# Aiven and some providers use postgres:// but SQLAlchemy async requires postgresql+asyncpg://
def get_async_database_url(url: str) -> str:
    """Convert database URL to async format if needed.
    
    Also removes sslmode parameter as asyncpg doesn't support it.
    SSL is enabled by default when connecting to cloud databases.
    """
    # Convert postgres:// to postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove sslmode parameter - asyncpg handles SSL automatically
    # when connecting to cloud databases
    import re
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)
    # Clean up any trailing ? or & characters
    url = re.sub(r'[?&]$', '', url)
    
    return url


# Create async engine
# - echo=settings.DEBUG: Log SQL queries in debug mode
# - pool_pre_ping=True: Verify connections before using them
# - pool_size=5: Connection pool size for production
# - pool_recycle=3600: Recycle connections after 1 hour (prevents timeout)
# - pool_timeout=30: Wait up to 30 seconds for a connection from the pool
# - pool_reset_on_return="rollback": Reset connection state on return to pool
# - connect_args: asyncpg-specific connection arguments
#   - server_settings: PostgreSQL server settings
#     - jit=off: Disable JIT compilation for better connection stability
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,
    pool_reset_on_return="rollback",  # Ensure clean connection state
    connect_args={
        "server_settings": {
            "jit": "off"  # Disable JIT for better stability
        },
        "timeout": 60  # Connection timeout in seconds
    }
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

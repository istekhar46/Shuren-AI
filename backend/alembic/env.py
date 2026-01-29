"""Alembic environment configuration for async database migrations.

This module configures Alembic to work with SQLAlchemy async engine
and imports all models for autogenerate support.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import settings to get database URL
import sys
from pathlib import Path

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.base import Base

# Import all models to ensure they're registered with Base.metadata
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile, UserProfileVersion
from app.models.preferences import (
    FitnessGoal,
    PhysicalConstraint,
    DietaryPreference,
    MealPlan,
    MealSchedule,
    WorkoutSchedule,
    HydrationPreference,
    LifestyleBaseline
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with the one from settings
# Convert to async format - asyncpg supports sslmode parameter natively
database_url = settings.DATABASE_URL

# Convert postgres:// or postgresql:// to postgresql+asyncpg://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine.

    In this scenario we need to create an async Engine
    and associate a connection with the context.

    """
    # Get the configuration section
    configuration = config.get_section(config.config_ini_section, {})
    
    # Handle SSL configuration for asyncpg
    # asyncpg doesn't accept 'sslmode' as a connection parameter
    # We need to pass SSL context via connect_args
    database_url = configuration.get("sqlalchemy.url", "")
    
    if "sslmode=require" in database_url:
        # Remove sslmode from URL and add it to connect_args
        database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
        configuration["sqlalchemy.url"] = database_url
        # asyncpg will use SSL by default when connecting to a server that requires it
        # No need to explicitly configure SSL context for 'require' mode
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This is the entry point for online migrations.
    It delegates to the async function.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

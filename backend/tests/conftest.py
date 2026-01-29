"""
Pytest configuration and shared fixtures for the Shuren backend test suite.

This module provides:
- Test database setup with separate test schema
- Async test client fixture
- Authenticated user fixtures
- Sample onboarding data fixtures
- Database session management for tests
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile


# Test database URL - use separate database or schema for testing
# This prevents test data from polluting the development database
def get_test_database_url() -> str:
    """Get test database URL from settings or create test-specific URL."""
    db_url = settings.DATABASE_URL
    
    # Convert to async format
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove sslmode parameter if present (asyncpg uses ssl parameter instead)
    if "?sslmode=" in db_url:
        # Extract sslmode value and convert to ssl parameter
        parts = db_url.split("?")
        base_url = parts[0]
        params = parts[1] if len(parts) > 1 else ""
        
        # Remove sslmode from params
        param_list = [p for p in params.split("&") if not p.startswith("sslmode=")]
        
        # Reconstruct URL
        if param_list:
            db_url = f"{base_url}?{'&'.join(param_list)}"
        else:
            db_url = base_url
    
    # Replace database name with test database
    # Example: postgresql+asyncpg://user:pass@host/db -> postgresql+asyncpg://user:pass@host/test_db
    if "//" in db_url and "/" in db_url.split("//")[1]:
        parts = db_url.rsplit("/", 1)
        db_name = parts[1].split("?")[0]  # Remove query params if any
        test_db_name = f"test_{db_name}"
        db_url = db_url.replace(f"/{db_name}", f"/{test_db_name}", 1)
    
    return db_url


# Create test engine with NullPool to avoid connection issues in tests
test_engine = create_async_engine(
    get_test_database_url(),
    echo=False,
    poolclass=NullPool  # Disable connection pooling for tests
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session.
    
    This fixture ensures all async tests share the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session.
    
    This fixture:
    - Creates all tables before each test
    - Provides a clean database session
    - Drops all tables after each test
    
    Usage:
        async def test_something(db_session: AsyncSession):
            user = User(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database session override.
    
    This fixture:
    - Overrides the get_db dependency to use test database
    - Provides an async HTTP client for API testing
    
    Usage:
        async def test_endpoint(client: AsyncClient):
            response = await client.get("/api/v1/users")
            assert response.status_code == 200
    """
    # Override get_db dependency to use test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with email/password authentication.
    
    Returns:
        User: A test user with email "testuser@example.com" and password "testpassword123"
    
    Usage:
        async def test_user_profile(test_user: User, db_session: AsyncSession):
            profile = await get_user_profile(test_user.id, db_session)
            assert profile is not None
    """
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create onboarding state for the user
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def oauth_user(db_session: AsyncSession) -> User:
    """Create a test user with Google OAuth authentication.
    
    Returns:
        User: A test user authenticated via Google OAuth
    
    Usage:
        async def test_oauth_flow(oauth_user: User):
            assert oauth_user.oauth_provider == "google"
            assert oauth_user.hashed_password is None
    """
    user = User(
        id=uuid4(),
        email="oauthuser@example.com",
        hashed_password=None,
        full_name="OAuth User",
        oauth_provider="google",
        oauth_provider_user_id="google-test-id-123",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create onboarding state for the user
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: User
) -> tuple[AsyncClient, User]:
    """Create an authenticated test client with JWT token.
    
    Returns:
        tuple: (AsyncClient with Authorization header, User)
    
    Usage:
        async def test_protected_endpoint(authenticated_client):
            client, user = authenticated_client
            response = await client.get("/api/v1/profiles/me")
            assert response.status_code == 200
    """
    token = create_access_token({"user_id": str(test_user.id)})
    client.headers["Authorization"] = f"Bearer {token}"
    return client, test_user


@pytest.fixture
def sample_onboarding_data() -> dict:
    """Provide sample onboarding data for all 11 steps.
    
    Returns:
        dict: Complete onboarding data with all required fields
    
    Usage:
        def test_onboarding_completion(sample_onboarding_data):
            data = sample_onboarding_data
            assert data["step_1"]["age"] == 28
    """
    return {
        "step_1": {
            "age": 28,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 75
        },
        "step_2": {
            "fitness_level": "intermediate"
        },
        "step_3": {
            "goals": [
                {
                    "goal_type": "muscle_gain",
                    "target_weight_kg": 80,
                    "priority": 1
                }
            ]
        },
        "step_4": {
            "constraints": [
                {
                    "constraint_type": "equipment",
                    "description": "Home gym with dumbbells and pull-up bar",
                    "severity": "low"
                }
            ]
        },
        "step_5": {
            "diet_type": "omnivore",
            "allergies": [],
            "intolerances": ["lactose"],
            "dislikes": ["mushrooms"]
        },
        "step_6": {
            "daily_calorie_target": 2500,
            "protein_percentage": 30,
            "carbs_percentage": 45,
            "fats_percentage": 25
        },
        "step_7": {
            "meal_schedules": [
                {"meal_name": "breakfast", "scheduled_time": "08:00", "enable_notifications": True},
                {"meal_name": "lunch", "scheduled_time": "13:00", "enable_notifications": True},
                {"meal_name": "dinner", "scheduled_time": "19:00", "enable_notifications": True}
            ]
        },
        "step_8": {
            "workout_schedules": [
                {"day_of_week": 1, "scheduled_time": "18:00", "enable_notifications": True},
                {"day_of_week": 3, "scheduled_time": "18:00", "enable_notifications": True},
                {"day_of_week": 5, "scheduled_time": "18:00", "enable_notifications": True}
            ]
        },
        "step_9": {
            "daily_water_target_ml": 3000,
            "reminder_frequency_minutes": 60,
            "enable_notifications": True
        },
        "step_10": {
            "energy_level": 7,
            "stress_level": 5,
            "sleep_quality": 6
        },
        "step_11": {
            "confirmation": True
        }
    }


@pytest.fixture
def minimal_onboarding_data() -> dict:
    """Provide minimal valid onboarding data for testing.
    
    Returns:
        dict: Minimal onboarding data with only required fields
    """
    return {
        "step_1": {
            "age": 25,
            "gender": "female",
            "height_cm": 165,
            "weight_kg": 60
        },
        "step_2": {
            "fitness_level": "beginner"
        },
        "step_3": {
            "goals": [
                {
                    "goal_type": "general_fitness",
                    "priority": 1
                }
            ]
        },
        "step_4": {
            "constraints": []
        },
        "step_5": {
            "diet_type": "vegetarian",
            "allergies": [],
            "intolerances": [],
            "dislikes": []
        },
        "step_6": {
            "daily_calorie_target": 1800,
            "protein_percentage": 25,
            "carbs_percentage": 50,
            "fats_percentage": 25
        },
        "step_7": {
            "meal_schedules": [
                {"meal_name": "breakfast", "scheduled_time": "07:00", "enable_notifications": False},
                {"meal_name": "lunch", "scheduled_time": "12:00", "enable_notifications": False},
                {"meal_name": "dinner", "scheduled_time": "18:00", "enable_notifications": False}
            ]
        },
        "step_8": {
            "workout_schedules": [
                {"day_of_week": 0, "scheduled_time": "06:00", "enable_notifications": False}
            ]
        },
        "step_9": {
            "daily_water_target_ml": 2000,
            "reminder_frequency_minutes": 120,
            "enable_notifications": False
        },
        "step_10": {
            "energy_level": 5,
            "stress_level": 5,
            "sleep_quality": 5
        },
        "step_11": {
            "confirmation": True
        }
    }


@pytest_asyncio.fixture
async def completed_onboarding_user(
    db_session: AsyncSession,
    sample_onboarding_data: dict
) -> tuple[User, UserProfile]:
    """Create a user with completed onboarding and locked profile.
    
    Returns:
        tuple: (User, UserProfile) with complete onboarding data
    
    Usage:
        async def test_profile_operations(completed_onboarding_user):
            user, profile = completed_onboarding_user
            assert profile.is_locked is True
    """
    # Create user
    user = User(
        id=uuid4(),
        email="completed@example.com",
        hashed_password=hash_password("password123"),
        full_name="Completed User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create completed onboarding state
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=11,
        is_complete=True,
        step_data=sample_onboarding_data,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(onboarding_state)
    
    # Create locked profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level=sample_onboarding_data["step_2"]["fitness_level"],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest.fixture
def invalid_onboarding_data() -> dict:
    """Provide invalid onboarding data for validation testing.
    
    Returns:
        dict: Invalid onboarding data that should fail validation
    """
    return {
        "step_1": {
            "age": 15,  # Too young
            "gender": "invalid",
            "height_cm": 300,  # Unrealistic
            "weight_kg": -10  # Negative weight
        },
        "step_6": {
            "daily_calorie_target": 500,  # Too low
            "protein_percentage": 50,
            "carbs_percentage": 30,
            "fats_percentage": 30  # Sum > 100
        },
        "step_10": {
            "energy_level": 15,  # Out of range (1-10)
            "stress_level": 0,  # Out of range
            "sleep_quality": -5  # Negative
        }
    }

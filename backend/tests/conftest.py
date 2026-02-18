"""
Pytest configuration and shared fixtures for the Shuren backend test suite.

This module provides:
- Test database setup with session-scoped connection
- Async test client fixture
- Authenticated user fixtures
- Sample onboarding data fixtures
- Database session management for tests

Based on SQLAlchemy async testing best practices:
https://asphalt.readthedocs.io/projects/sqlalchemy/en/stable/testing.html
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection, create_async_engine

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
    """Get test database URL from settings or create test-specific URL.
    
    For local development, uses a local test database.
    For remote databases (like Aiven), uses transaction isolation.
    """
    db_url = settings.DATABASE_URL
    
    # For local testing, use local PostgreSQL database
    # This avoids DNS issues with remote databases
    local_test_db = "postgresql+asyncpg://postgres:ist%40123@localhost:5432/shuren_test_db"
    
    # Check if we're using a remote database (Aiven, AWS, etc.)
    if any(domain in db_url for domain in ['aivencloud.com', 'amazonaws.com', 'azure.com', 'cloud.google.com']):
        # Use local database for testing instead of remote
        return local_test_db
    
    # Check if already using local database (localhost or 127.0.0.1)
    if 'localhost' in db_url or '127.0.0.1' in db_url:
        # Always use shuren_test_db for local testing
        return local_test_db
    
    # Convert to async format for other databases
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove sslmode parameter if present (asyncpg uses ssl parameter instead)
    if "?sslmode=" in db_url:
        parts = db_url.split("?")
        base_url = parts[0]
        params = parts[1] if len(parts) > 1 else ""
        param_list = [p for p in params.split("&") if not p.startswith("sslmode=")]
        if param_list:
            db_url = f"{base_url}?{'&'.join(param_list)}"
        else:
            db_url = base_url
    
    # For other databases, create a test database name
    if "//" in db_url and "/" in db_url.split("//")[1]:
        parts = db_url.rsplit("/", 1)
        db_name = parts[1].split("?")[0]  # Remove query params if any
        test_db_name = f"test_{db_name}"
        db_url = db_url.replace(f"/{db_name}", f"/{test_db_name}", 1)
    
    return db_url


# Create test engine - use NullPool to avoid pooling issues with async
from sqlalchemy.pool import NullPool

test_engine = create_async_engine(
    get_test_database_url(),
    echo=False,
    poolclass=NullPool  # No pooling - we use a single session-scoped connection
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session.
    
    This fixture ensures all async tests share the same event loop.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with automatic rollback.
    
    This fixture:
    - Creates all tables before each test
    - Provides a clean database session  
    - Drops all tables after each test
    
    Uses local PostgreSQL database to avoid DNS issues with remote databases.
    
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
    async with test_engine.connect() as conn:
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
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
    
    # Create onboarding state for the user with agent foundation fields
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        current_agent=None,
        agent_context={},
        conversation_history=[],
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
    
    # Create onboarding state for the user with agent foundation fields
    onboarding_state = OnboardingState(
        id=uuid4(),
        user_id=user.id,
        current_step=0,
        is_complete=False,
        step_data={},
        current_agent=None,
        agent_context={},
        conversation_history=[],
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


@pytest_asyncio.fixture
async def authenticated_client_with_profile(
    client: AsyncClient,
    completed_onboarding_user: tuple[User, "UserProfile"]
) -> tuple[AsyncClient, User]:
    """Create an authenticated test client with a user that has a completed profile.
    
    This fixture is needed for endpoints that require user context loading,
    which depends on having a user profile in the database.
    
    Returns:
        tuple: (AsyncClient with Authorization header, User with profile)
    
    Usage:
        async def test_chat_endpoint(authenticated_client_with_profile):
            client, user = authenticated_client_with_profile
            response = await client.post("/api/v1/chat/chat", json={"message": "Hello"})
            assert response.status_code == 200
    """
    user, profile = completed_onboarding_user
    token = create_access_token({"user_id": str(user.id)})
    client.headers["Authorization"] = f"Bearer {token}"
    return client, user


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


# ============================================================================
# Meal Dish Management Fixtures (Task 9.6)
# ============================================================================
#
# These fixtures provide test data for the meal dish management feature:
#
# - sample_ingredients: 10 common ingredients (proteins, grains, vegetables, etc.)
# - sample_dishes: 12 dishes covering all meal types (breakfast, lunch, dinner, 
#                  snacks, pre/post-workout) with both vegetarian and non-vegetarian
# - user_with_meal_template: User with complete meal template (week 1) and 
#                            meal schedules
# - vegetarian_user: User with vegetarian dietary preferences
# - user_with_allergies: User with dairy and egg allergies
#
# Usage:
#   async def test_something(sample_dishes, vegetarian_user):
#       dishes = sample_dishes
#       user, profile = vegetarian_user
#       # ... test logic
#
# ============================================================================


@pytest_asyncio.fixture
async def sample_ingredients(db_session: AsyncSession) -> list:
    """Create sample ingredients for testing.
    
    Returns:
        list: List of Ingredient objects with various categories
    
    Usage:
        async def test_ingredients(sample_ingredients):
            assert len(sample_ingredients) >= 10
    """
    from app.models.dish import Ingredient
    from decimal import Decimal
    
    ingredients_data = [
        # Proteins
        {"name": "chicken_breast", "name_hindi": "चिकन ब्रेस्ट", "category": "protein", 
         "calories_per_100g": Decimal("165"), "protein_per_100g": Decimal("31"), 
         "carbs_per_100g": Decimal("0"), "fats_per_100g": Decimal("3.6"), 
         "typical_unit": "g", "is_allergen": False},
        {"name": "eggs", "name_hindi": "अंडे", "category": "protein", 
         "calories_per_100g": Decimal("155"), "protein_per_100g": Decimal("13"), 
         "carbs_per_100g": Decimal("1.1"), "fats_per_100g": Decimal("11"), 
         "typical_unit": "piece", "is_allergen": True, "allergen_type": "eggs"},
        {"name": "paneer", "name_hindi": "पनीर", "category": "dairy", 
         "calories_per_100g": Decimal("265"), "protein_per_100g": Decimal("18"), 
         "carbs_per_100g": Decimal("1.2"), "fats_per_100g": Decimal("20"), 
         "typical_unit": "g", "is_allergen": True, "allergen_type": "dairy"},
        
        # Grains
        {"name": "brown_rice", "name_hindi": "ब्राउन राइस", "category": "grain", 
         "calories_per_100g": Decimal("111"), "protein_per_100g": Decimal("2.6"), 
         "carbs_per_100g": Decimal("23"), "fats_per_100g": Decimal("0.9"), 
         "typical_unit": "g", "is_allergen": False},
        {"name": "oats", "name_hindi": "ओट्स", "category": "grain", 
         "calories_per_100g": Decimal("389"), "protein_per_100g": Decimal("17"), 
         "carbs_per_100g": Decimal("66"), "fats_per_100g": Decimal("7"), 
         "typical_unit": "g", "is_allergen": False},
        
        # Vegetables
        {"name": "spinach", "name_hindi": "पालक", "category": "vegetable", 
         "calories_per_100g": Decimal("23"), "protein_per_100g": Decimal("2.9"), 
         "carbs_per_100g": Decimal("3.6"), "fats_per_100g": Decimal("0.4"), 
         "typical_unit": "g", "is_allergen": False},
        {"name": "tomato", "name_hindi": "टमाटर", "category": "vegetable", 
         "calories_per_100g": Decimal("18"), "protein_per_100g": Decimal("0.9"), 
         "carbs_per_100g": Decimal("3.9"), "fats_per_100g": Decimal("0.2"), 
         "typical_unit": "g", "is_allergen": False},
        
        # Fruits
        {"name": "banana", "name_hindi": "केला", "category": "fruit", 
         "calories_per_100g": Decimal("89"), "protein_per_100g": Decimal("1.1"), 
         "carbs_per_100g": Decimal("23"), "fats_per_100g": Decimal("0.3"), 
         "typical_unit": "piece", "is_allergen": False},
        
        # Oils and spices
        {"name": "olive_oil", "name_hindi": "जैतून का तेल", "category": "oil", 
         "calories_per_100g": Decimal("884"), "protein_per_100g": Decimal("0"), 
         "carbs_per_100g": Decimal("0"), "fats_per_100g": Decimal("100"), 
         "typical_unit": "ml", "is_allergen": False},
        {"name": "turmeric", "name_hindi": "हल्दी", "category": "spice", 
         "calories_per_100g": Decimal("312"), "protein_per_100g": Decimal("9.7"), 
         "carbs_per_100g": Decimal("67"), "fats_per_100g": Decimal("3.2"), 
         "typical_unit": "tsp", "is_allergen": False},
    ]
    
    ingredients = []
    for data in ingredients_data:
        ingredient = Ingredient(
            id=uuid4(),
            **data,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(ingredient)
        ingredients.append(ingredient)
    
    await db_session.commit()
    for ingredient in ingredients:
        await db_session.refresh(ingredient)
    
    return ingredients


@pytest_asyncio.fixture
async def sample_dishes(db_session: AsyncSession, sample_ingredients: list) -> list:
    """Create sample dishes for testing.
    
    Returns:
        list: List of 10-20 Dish objects with various meal types
    
    Usage:
        async def test_dishes(sample_dishes):
            breakfast_dishes = [d for d in sample_dishes if d.meal_type == 'breakfast']
            assert len(breakfast_dishes) > 0
    """
    from app.models.dish import Dish, DishIngredient
    from decimal import Decimal
    
    # Get ingredients by name for easy reference
    ingredients_map = {ing.name: ing for ing in sample_ingredients}
    
    dishes_data = [
        # Breakfast dishes
        {
            "name": "Scrambled Eggs with Toast",
            "name_hindi": "अंडे का भुर्जी",
            "cuisine_type": "continental",
            "meal_type": "breakfast",
            "serving_size_g": Decimal("200"),
            "calories": Decimal("350"),
            "protein_g": Decimal("25"),
            "carbs_g": Decimal("30"),
            "fats_g": Decimal("15"),
            "prep_time_minutes": 5,
            "cook_time_minutes": 10,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "ingredients": [
                {"name": "eggs", "quantity": Decimal("3"), "unit": "piece"},
                {"name": "olive_oil", "quantity": Decimal("5"), "unit": "ml"},
            ]
        },
        {
            "name": "Oatmeal with Banana",
            "name_hindi": "ओट्स और केला",
            "cuisine_type": "continental",
            "meal_type": "breakfast",
            "serving_size_g": Decimal("250"),
            "calories": Decimal("300"),
            "protein_g": Decimal("12"),
            "carbs_g": Decimal("50"),
            "fats_g": Decimal("6"),
            "prep_time_minutes": 2,
            "cook_time_minutes": 5,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "is_vegan": True,
            "ingredients": [
                {"name": "oats", "quantity": Decimal("50"), "unit": "g"},
                {"name": "banana", "quantity": Decimal("1"), "unit": "piece"},
            ]
        },
        {
            "name": "Paneer Bhurji",
            "name_hindi": "पनीर भुर्जी",
            "cuisine_type": "north_indian",
            "meal_type": "breakfast",
            "serving_size_g": Decimal("200"),
            "calories": Decimal("400"),
            "protein_g": Decimal("22"),
            "carbs_g": Decimal("15"),
            "fats_g": Decimal("28"),
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "difficulty_level": "medium",
            "is_vegetarian": True,
            "contains_allergens": ["dairy"],
            "ingredients": [
                {"name": "paneer", "quantity": Decimal("150"), "unit": "g"},
                {"name": "tomato", "quantity": Decimal("50"), "unit": "g"},
                {"name": "turmeric", "quantity": Decimal("1"), "unit": "tsp"},
            ]
        },
        
        # Lunch dishes
        {
            "name": "Grilled Chicken with Rice",
            "name_hindi": "ग्रिल्ड चिकन और चावल",
            "cuisine_type": "continental",
            "meal_type": "lunch",
            "serving_size_g": Decimal("350"),
            "calories": Decimal("500"),
            "protein_g": Decimal("45"),
            "carbs_g": Decimal("50"),
            "fats_g": Decimal("10"),
            "prep_time_minutes": 10,
            "cook_time_minutes": 25,
            "difficulty_level": "medium",
            "is_vegetarian": False,
            "ingredients": [
                {"name": "chicken_breast", "quantity": Decimal("200"), "unit": "g"},
                {"name": "brown_rice", "quantity": Decimal("100"), "unit": "g"},
                {"name": "olive_oil", "quantity": Decimal("10"), "unit": "ml"},
            ]
        },
        {
            "name": "Spinach Dal with Rice",
            "name_hindi": "पालक दाल",
            "cuisine_type": "north_indian",
            "meal_type": "lunch",
            "serving_size_g": Decimal("300"),
            "calories": Decimal("380"),
            "protein_g": Decimal("18"),
            "carbs_g": Decimal("60"),
            "fats_g": Decimal("8"),
            "prep_time_minutes": 15,
            "cook_time_minutes": 30,
            "difficulty_level": "medium",
            "is_vegetarian": True,
            "is_vegan": True,
            "ingredients": [
                {"name": "spinach", "quantity": Decimal("100"), "unit": "g"},
                {"name": "brown_rice", "quantity": Decimal("100"), "unit": "g"},
                {"name": "turmeric", "quantity": Decimal("1"), "unit": "tsp"},
            ]
        },
        
        # Dinner dishes
        {
            "name": "Paneer Tikka with Vegetables",
            "name_hindi": "पनीर टिक्का",
            "cuisine_type": "north_indian",
            "meal_type": "dinner",
            "serving_size_g": Decimal("300"),
            "calories": Decimal("450"),
            "protein_g": Decimal("25"),
            "carbs_g": Decimal("35"),
            "fats_g": Decimal("22"),
            "prep_time_minutes": 20,
            "cook_time_minutes": 20,
            "difficulty_level": "medium",
            "is_vegetarian": True,
            "contains_allergens": ["dairy"],
            "ingredients": [
                {"name": "paneer", "quantity": Decimal("200"), "unit": "g"},
                {"name": "tomato", "quantity": Decimal("50"), "unit": "g"},
                {"name": "spinach", "quantity": Decimal("50"), "unit": "g"},
            ]
        },
        {
            "name": "Chicken Curry with Rice",
            "name_hindi": "चिकन करी",
            "cuisine_type": "north_indian",
            "meal_type": "dinner",
            "serving_size_g": Decimal("400"),
            "calories": Decimal("550"),
            "protein_g": Decimal("40"),
            "carbs_g": Decimal("55"),
            "fats_g": Decimal("15"),
            "prep_time_minutes": 15,
            "cook_time_minutes": 35,
            "difficulty_level": "medium",
            "is_vegetarian": False,
            "ingredients": [
                {"name": "chicken_breast", "quantity": Decimal("200"), "unit": "g"},
                {"name": "brown_rice", "quantity": Decimal("100"), "unit": "g"},
                {"name": "tomato", "quantity": Decimal("100"), "unit": "g"},
                {"name": "turmeric", "quantity": Decimal("1"), "unit": "tsp"},
            ]
        },
        
        # Snacks
        {
            "name": "Boiled Eggs",
            "name_hindi": "उबले अंडे",
            "cuisine_type": "continental",
            "meal_type": "snack",
            "serving_size_g": Decimal("100"),
            "calories": Decimal("155"),
            "protein_g": Decimal("13"),
            "carbs_g": Decimal("1"),
            "fats_g": Decimal("11"),
            "prep_time_minutes": 2,
            "cook_time_minutes": 10,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "contains_allergens": ["eggs"],
            "ingredients": [
                {"name": "eggs", "quantity": Decimal("2"), "unit": "piece"},
            ]
        },
        {
            "name": "Banana Smoothie",
            "name_hindi": "केला स्मूदी",
            "cuisine_type": "continental",
            "meal_type": "snack",
            "serving_size_g": Decimal("250"),
            "calories": Decimal("200"),
            "protein_g": Decimal("8"),
            "carbs_g": Decimal("35"),
            "fats_g": Decimal("3"),
            "prep_time_minutes": 5,
            "cook_time_minutes": 0,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "is_vegan": True,
            "ingredients": [
                {"name": "banana", "quantity": Decimal("2"), "unit": "piece"},
                {"name": "oats", "quantity": Decimal("20"), "unit": "g"},
            ]
        },
        
        # Pre-workout
        {
            "name": "Banana with Oats",
            "name_hindi": "केला और ओट्स",
            "cuisine_type": "continental",
            "meal_type": "pre_workout",
            "serving_size_g": Decimal("150"),
            "calories": Decimal("250"),
            "protein_g": Decimal("8"),
            "carbs_g": Decimal("45"),
            "fats_g": Decimal("4"),
            "prep_time_minutes": 3,
            "cook_time_minutes": 2,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "is_vegan": True,
            "ingredients": [
                {"name": "banana", "quantity": Decimal("1"), "unit": "piece"},
                {"name": "oats", "quantity": Decimal("30"), "unit": "g"},
            ]
        },
        
        # Post-workout
        {
            "name": "Chicken and Rice Bowl",
            "name_hindi": "चिकन राइस बाउल",
            "cuisine_type": "continental",
            "meal_type": "post_workout",
            "serving_size_g": Decimal("300"),
            "calories": Decimal("450"),
            "protein_g": Decimal("40"),
            "carbs_g": Decimal("45"),
            "fats_g": Decimal("8"),
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "difficulty_level": "easy",
            "is_vegetarian": False,
            "ingredients": [
                {"name": "chicken_breast", "quantity": Decimal("180"), "unit": "g"},
                {"name": "brown_rice", "quantity": Decimal("100"), "unit": "g"},
            ]
        },
        {
            "name": "Paneer and Rice Bowl",
            "name_hindi": "पनीर राइस बाउल",
            "cuisine_type": "north_indian",
            "meal_type": "post_workout",
            "serving_size_g": Decimal("300"),
            "calories": Decimal("480"),
            "protein_g": Decimal("28"),
            "carbs_g": Decimal("45"),
            "fats_g": Decimal("18"),
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "difficulty_level": "easy",
            "is_vegetarian": True,
            "contains_allergens": ["dairy"],
            "ingredients": [
                {"name": "paneer", "quantity": Decimal("150"), "unit": "g"},
                {"name": "brown_rice", "quantity": Decimal("100"), "unit": "g"},
                {"name": "spinach", "quantity": Decimal("50"), "unit": "g"},
            ]
        },
    ]
    
    dishes = []
    for dish_data in dishes_data:
        # Extract ingredients data
        ingredients_data = dish_data.pop("ingredients")
        
        # Create dish
        dish = Dish(
            id=uuid4(),
            **dish_data,
            is_active=True,
            popularity_score=50,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish)
        dishes.append(dish)
        
        # Create dish ingredients
        for ing_data in ingredients_data:
            ingredient = ingredients_map.get(ing_data["name"])
            if ingredient:
                dish_ingredient = DishIngredient(
                    id=uuid4(),
                    dish_id=dish.id,
                    ingredient_id=ingredient.id,
                    quantity=ing_data["quantity"],
                    unit=ing_data["unit"],
                    is_optional=False,
                    created_at=datetime.now(timezone.utc)
                )
                db_session.add(dish_ingredient)
    
    await db_session.commit()
    for dish in dishes:
        await db_session.refresh(dish)
    
    return dishes


@pytest_asyncio.fixture
async def user_with_meal_template(
    db_session: AsyncSession,
    sample_dishes: list
) -> tuple[User, UserProfile]:
    """Create a user with a complete meal template.
    
    Returns:
        tuple: (User, UserProfile) with meal template and template meals
    
    Usage:
        async def test_template(user_with_meal_template):
            user, profile = user_with_meal_template
            # Profile has meal_templates relationship populated
    """
    from app.models.profile import UserProfile
    from app.models.preferences import MealSchedule
    from app.models.meal_template import MealTemplate, TemplateMeal
    from datetime import time
    
    # Create user
    user = User(
        id=uuid4(),
        email="template_user@example.com",
        hashed_password=hash_password("password123"),
        full_name="Template User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level="intermediate",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create meal schedules
    meal_schedules = [
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="lunch",
            scheduled_time=time(13, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="dinner",
            scheduled_time=time(19, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
    ]
    for schedule in meal_schedules:
        db_session.add(schedule)
    
    # Create meal template
    template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(template)
    
    # Create template meals (assign dishes to meal slots)
    # Get dishes by meal type
    breakfast_dishes = [d for d in sample_dishes if d.meal_type == "breakfast"]
    lunch_dishes = [d for d in sample_dishes if d.meal_type == "lunch"]
    dinner_dishes = [d for d in sample_dishes if d.meal_type == "dinner"]
    
    # Assign dishes for each day of the week
    for day in range(7):  # 0=Monday to 6=Sunday
        # Breakfast
        if breakfast_dishes:
            template_meal = TemplateMeal(
                id=uuid4(),
                template_id=template.id,
                meal_schedule_id=meal_schedules[0].id,
                dish_id=breakfast_dishes[day % len(breakfast_dishes)].id,
                day_of_week=day,
                is_primary=True,
                alternative_order=1,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(template_meal)
        
        # Lunch
        if lunch_dishes:
            template_meal = TemplateMeal(
                id=uuid4(),
                template_id=template.id,
                meal_schedule_id=meal_schedules[1].id,
                dish_id=lunch_dishes[day % len(lunch_dishes)].id,
                day_of_week=day,
                is_primary=True,
                alternative_order=1,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(template_meal)
        
        # Dinner
        if dinner_dishes:
            template_meal = TemplateMeal(
                id=uuid4(),
                template_id=template.id,
                meal_schedule_id=meal_schedules[2].id,
                dish_id=dinner_dishes[day % len(dinner_dishes)].id,
                day_of_week=day,
                is_primary=True,
                alternative_order=1,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(template_meal)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest_asyncio.fixture
async def vegetarian_user(db_session: AsyncSession) -> tuple[User, UserProfile]:
    """Create a vegetarian user with dietary preferences.
    
    Returns:
        tuple: (User, UserProfile) with vegetarian diet type
    
    Usage:
        async def test_vegetarian_dishes(vegetarian_user):
            user, profile = vegetarian_user
            # Use for testing vegetarian dish filtering
    """
    from app.models.profile import UserProfile
    from app.models.preferences import DietaryPreference
    
    # Create user
    user = User(
        id=uuid4(),
        email="vegetarian@example.com",
        hashed_password=hash_password("password123"),
        full_name="Vegetarian User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="beginner",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create dietary preferences
    dietary_prefs = DietaryPreference(
        id=uuid4(),
        profile_id=profile.id,
        diet_type="vegetarian",
        allergies=[],
        intolerances=[],
        dislikes=[],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(dietary_prefs)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest_asyncio.fixture
async def user_with_allergies(db_session: AsyncSession) -> tuple[User, UserProfile]:
    """Create a user with food allergies.
    
    Returns:
        tuple: (User, UserProfile) with dairy and egg allergies
    
    Usage:
        async def test_allergen_filtering(user_with_allergies):
            user, profile = user_with_allergies
            # Use for testing allergen exclusion
    """
    from app.models.profile import UserProfile
    from app.models.preferences import DietaryPreference
    
    # Create user
    user = User(
        id=uuid4(),
        email="allergies@example.com",
        hashed_password=hash_password("password123"),
        full_name="User With Allergies",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="intermediate",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create dietary preferences with allergies
    dietary_prefs = DietaryPreference(
        id=uuid4(),
        profile_id=profile.id,
        diet_type="omnivore",
        allergies=["dairy", "eggs"],
        intolerances=["lactose"],
        dislikes=["mushrooms"],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(dietary_prefs)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest.fixture
def mock_gemini_client(monkeypatch):
    """Mock Google Gemini API client to avoid quota issues and API calls.
    
    This fixture mocks the ChatGoogleGenerativeAI class from langchain_google_genai
    to return canned responses instead of making actual API calls.
    
    Returns:
        MagicMock: Mocked Gemini client that returns predefined responses
    
    Usage:
        def test_agent_with_gemini(mock_gemini_client):
            # Gemini API calls will be mocked automatically
            result = agent.process_query("meal plan")
            assert result is not None
    """
    from unittest.mock import MagicMock, AsyncMock
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.content = "Mocked Gemini response: Here's a sample meal plan based on your preferences."
    
    # Create mock client
    mock_client = MagicMock()
    mock_client.invoke = MagicMock(return_value=mock_response)
    mock_client.ainvoke = AsyncMock(return_value=mock_response)
    
    # Mock the ChatGoogleGenerativeAI class
    def mock_gemini_constructor(*args, **kwargs):
        return mock_client
    
    monkeypatch.setattr(
        "langchain_google_genai.ChatGoogleGenerativeAI",
        mock_gemini_constructor
    )
    
    return mock_client

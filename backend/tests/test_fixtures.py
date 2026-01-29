"""
Tests to verify pytest fixtures and configuration work correctly.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.user import User
from app.models.profile import UserProfile


@pytest.mark.asyncio
async def test_db_session_fixture(db_session: AsyncSession):
    """Test that db_session fixture provides a working database session."""
    assert db_session is not None
    assert isinstance(db_session, AsyncSession)


@pytest.mark.asyncio
async def test_client_fixture(client: AsyncClient):
    """Test that client fixture provides a working async HTTP client."""
    assert client is not None
    assert isinstance(client, AsyncClient)


@pytest.mark.asyncio
async def test_test_user_fixture(test_user: User, db_session: AsyncSession):
    """Test that test_user fixture creates a valid user."""
    assert test_user is not None
    assert test_user.email == "testuser@example.com"
    assert test_user.full_name == "Test User"
    assert test_user.is_active is True
    assert test_user.hashed_password is not None
    
    # Verify user exists in database
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.id == test_user.id))
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.email == test_user.email


@pytest.mark.asyncio
async def test_oauth_user_fixture(oauth_user: User, db_session: AsyncSession):
    """Test that oauth_user fixture creates a valid OAuth user."""
    assert oauth_user is not None
    assert oauth_user.email == "oauthuser@example.com"
    assert oauth_user.oauth_provider == "google"
    assert oauth_user.oauth_provider_user_id == "google-test-id-123"
    assert oauth_user.hashed_password is None


@pytest.mark.asyncio
async def test_authenticated_client_fixture(authenticated_client):
    """Test that authenticated_client fixture provides client with auth token."""
    client, user = authenticated_client
    assert client is not None
    assert user is not None
    assert "Authorization" in client.headers
    assert client.headers["Authorization"].startswith("Bearer ")


def test_sample_onboarding_data_fixture(sample_onboarding_data: dict):
    """Test that sample_onboarding_data fixture provides complete data."""
    assert sample_onboarding_data is not None
    assert "step_1" in sample_onboarding_data
    assert "step_2" in sample_onboarding_data
    assert "step_11" in sample_onboarding_data
    
    # Verify step 1 data
    assert sample_onboarding_data["step_1"]["age"] == 28
    assert sample_onboarding_data["step_1"]["gender"] == "male"
    
    # Verify step 6 macros sum to 100
    step_6 = sample_onboarding_data["step_6"]
    macro_sum = (
        step_6["protein_percentage"] +
        step_6["carbs_percentage"] +
        step_6["fats_percentage"]
    )
    assert macro_sum == 100


def test_minimal_onboarding_data_fixture(minimal_onboarding_data: dict):
    """Test that minimal_onboarding_data fixture provides valid minimal data."""
    assert minimal_onboarding_data is not None
    assert "step_1" in minimal_onboarding_data
    assert minimal_onboarding_data["step_2"]["fitness_level"] == "beginner"


@pytest.mark.asyncio
async def test_completed_onboarding_user_fixture(
    completed_onboarding_user,
    db_session: AsyncSession
):
    """Test that completed_onboarding_user fixture creates user with profile."""
    user, profile = completed_onboarding_user
    
    assert user is not None
    assert profile is not None
    assert profile.user_id == user.id
    assert profile.is_locked is True
    assert profile.fitness_level is not None
    
    # Verify profile exists in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(UserProfile).where(UserProfile.id == profile.id)
    )
    db_profile = result.scalar_one_or_none()
    assert db_profile is not None
    assert db_profile.is_locked is True


def test_invalid_onboarding_data_fixture(invalid_onboarding_data: dict):
    """Test that invalid_onboarding_data fixture provides invalid data."""
    assert invalid_onboarding_data is not None
    
    # Verify step 1 has invalid data
    assert invalid_onboarding_data["step_1"]["age"] == 15  # Too young
    assert invalid_onboarding_data["step_1"]["weight_kg"] == -10  # Negative
    
    # Verify step 6 macros sum > 100
    step_6 = invalid_onboarding_data["step_6"]
    macro_sum = (
        step_6["protein_percentage"] +
        step_6["carbs_percentage"] +
        step_6["fats_percentage"]
    )
    assert macro_sum > 100
    
    # Verify step 10 has out-of-range values
    assert invalid_onboarding_data["step_10"]["energy_level"] > 10

"""
Tests for FastAPI authentication dependencies.

Validates JWT token extraction, validation, and user fetching.
"""

import pytest
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.db.base import Base
from app.models.user import User


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create only the users table (avoid JSONB issues with SQLite)
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create, checkfirst=True)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.drop, checkfirst=True)
    
    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, test_db: AsyncSession, test_user: User):
        """Test that get_current_user returns user for valid token."""
        # Create valid token
        token = create_access_token({"user_id": str(test_user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Call dependency
        user = await get_current_user(credentials, test_db)
        
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.full_name == test_user.full_name
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, test_db: AsyncSession, test_user: User):
        """Test that get_current_user raises 401 for expired token."""
        # Create expired token
        token = create_access_token(
            {"user_id": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_signature(self, test_db: AsyncSession, test_user: User):
        """Test that get_current_user raises 401 for token with invalid signature."""
        # Create token with wrong signature (manually crafted)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        )
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(self, test_db: AsyncSession):
        """Test that get_current_user raises 401 for token without user_id."""
        # Create token without user_id
        token = create_access_token({"some_other_field": "value"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "missing user_id" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_malformed_user_id(self, test_db: AsyncSession):
        """Test that get_current_user raises 401 for token with malformed user_id."""
        # Create token with invalid UUID
        token = create_access_token({"user_id": "not-a-valid-uuid"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "malformed user_id" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, test_db: AsyncSession):
        """Test that get_current_user raises 401 for token with non-existent user."""
        # Create token with random UUID that doesn't exist in database
        random_uuid = uuid4()
        token = create_access_token({"user_id": str(random_uuid)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_soft_deleted_user(self, test_db: AsyncSession, test_user: User):
        """Test that get_current_user raises 401 for soft-deleted user."""
        # Soft delete the user
        from datetime import datetime, timezone
        test_user.deleted_at = datetime.now(timezone.utc)
        await test_db.commit()
        
        # Create valid token
        token = create_access_token({"user_id": str(test_user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found or has been deleted" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_includes_www_authenticate_header(self, test_db: AsyncSession):
        """Test that 401 responses include WWW-Authenticate header."""
        # Create token with invalid user_id
        token = create_access_token({"user_id": "invalid"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Should raise HTTPException with WWW-Authenticate header
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers is not None
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

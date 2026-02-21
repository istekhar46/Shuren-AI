"""Tests for database foundation (base model and session management)."""

import pytest
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base, BaseModel
from app.db.session import get_db, get_async_database_url


class TestModel(BaseModel):
    """Test model for verifying BaseModel functionality."""
    __tablename__ = "test_models"
    
    name = Column(String(100), nullable=False)


class TestDatabaseURL:
    """Tests for database URL conversion."""
    
    def test_postgres_url_conversion(self):
        """Test that postgres:// URLs are converted to postgresql+asyncpg://"""
        url = "postgres://user:pass@localhost:5432/db"
        result = get_async_database_url(url)
        assert result == "postgresql+asyncpg://user:pass@localhost:5432/db"
    
    def test_postgresql_url_conversion(self):
        """Test that postgresql:// URLs are converted to postgresql+asyncpg://"""
        url = "postgresql://user:pass@localhost:5432/db"
        result = get_async_database_url(url)
        assert result == "postgresql+asyncpg://user:pass@localhost:5432/db"
    
    def test_already_async_url(self):
        """Test that postgresql+asyncpg:// URLs are not modified."""
        url = "postgresql+asyncpg://user:pass@localhost:5432/db"
        result = get_async_database_url(url)
        assert result == url


class TestBaseModel:
    """Tests for BaseModel functionality."""
    
    def test_base_model_has_id_field(self):
        """Test that BaseModel includes id field as UUID primary key."""
        assert hasattr(BaseModel, 'id')
        assert BaseModel.id.primary_key
    
    def test_base_model_has_timestamp_fields(self):
        """Test that BaseModel includes created_at, updated_at, deleted_at fields."""
        assert hasattr(BaseModel, 'created_at')
        assert hasattr(BaseModel, 'updated_at')
        assert hasattr(BaseModel, 'deleted_at')
    
    def test_base_model_is_abstract(self):
        """Test that BaseModel is marked as abstract."""
        assert BaseModel.__abstract__ is True
    
    def test_created_at_has_server_default(self):
        """Test that created_at has server_default for automatic timestamp."""
        assert BaseModel.created_at.server_default is not None
    
    def test_updated_at_has_onupdate(self):
        """Test that updated_at has onupdate for automatic timestamp on modification."""
        assert BaseModel.updated_at.onupdate is not None


@pytest.mark.asyncio
async def test_get_db_dependency():
    """Test that get_db dependency yields an AsyncSession."""
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        # Verify session is usable
        assert session.is_active
        break  # Only test first yield


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

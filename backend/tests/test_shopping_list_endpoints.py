"""
Tests for shopping list endpoints.

Validates shopping list generation from meal templates.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.shopping_list import router
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.shopping_list import ShoppingListResponse


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock authenticated user with profile."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True
    )
    user.profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False
    )
    return user


@pytest.fixture
def app(mock_db, mock_user):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/meals/shopping-list", tags=["shopping_list"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetShoppingList:
    """Tests for GET /shopping-list endpoint."""
    
    def test_get_shopping_list_success(self, client, mock_db, mock_user):
        """Test successful shopping list generation."""
        from unittest.mock import patch
        
        # Mock the shopping list response
        mock_response = ShoppingListResponse(
            week_number=1,
            start_date=date.today().isoformat(),
            end_date=(date.today()).isoformat(),
            categories=[],
            total_items=0
        )
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 200
            assert "week_number" in response.json()
            assert "categories" in response.json()
            assert "total_items" in response.json()
    
    def test_get_shopping_list_with_weeks_parameter(self, client, mock_db, mock_user):
        """Test shopping list generation with weeks parameter."""
        from unittest.mock import patch
        
        mock_response = ShoppingListResponse(
            week_number=1,
            start_date=date.today().isoformat(),
            end_date=(date.today()).isoformat(),
            categories=[],
            total_items=0
        )
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/?weeks=2")
            
            assert response.status_code == 200
            mock_service.generate_shopping_list.assert_called_once()
            call_args = mock_service.generate_shopping_list.call_args
            assert call_args.kwargs['weeks'] == 2
    
    def test_get_shopping_list_invalid_weeks(self, client):
        """Test shopping list with invalid weeks parameter."""
        response = client.get("/api/v1/meals/shopping-list/?weeks=5")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_shopping_list_no_template(self, client, mock_db, mock_user):
        """Test shopping list when no active template exists."""
        from unittest.mock import patch
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="No active meal template found")
            )
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 404

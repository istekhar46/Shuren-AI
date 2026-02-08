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
        from datetime import timedelta
        
        # Mock the shopping list response with categories
        mock_response = ShoppingListResponse(
            week_number=1,
            start_date=date.today().isoformat(),
            end_date=(date.today() + timedelta(days=6)).isoformat(),
            categories=[
                {
                    "category": "protein",
                    "ingredients": [
                        {
                            "ingredient_id": str(uuid4()),
                            "name": "chicken_breast",
                            "category": "protein",
                            "total_quantity": 1500,
                            "unit": "g",
                            "used_in_dishes": ["Grilled Chicken", "Chicken Curry"]
                        }
                    ]
                }
            ],
            total_items=1
        )
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 200
            data = response.json()
            assert "week_number" in data
            assert "categories" in data
            assert "total_items" in data
            assert data["total_items"] == 1
            assert len(data["categories"]) == 1
    
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
    
    def test_get_shopping_list_default_weeks(self, client, mock_db, mock_user):
        """Test shopping list with default weeks parameter (1)."""
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
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 200
            call_args = mock_service.generate_shopping_list.call_args
            assert call_args.kwargs['weeks'] == 1
    
    def test_get_shopping_list_invalid_weeks_too_high(self, client):
        """Test shopping list with invalid weeks parameter (too high)."""
        response = client.get("/api/v1/meals/shopping-list/?weeks=5")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_shopping_list_invalid_weeks_zero(self, client):
        """Test shopping list with invalid weeks parameter (zero)."""
        response = client.get("/api/v1/meals/shopping-list/?weeks=0")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_shopping_list_invalid_weeks_negative(self, client):
        """Test shopping list with invalid weeks parameter (negative)."""
        response = client.get("/api/v1/meals/shopping-list/?weeks=-1")
        
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
            data = response.json()
            assert "no active meal template found" in data["detail"].lower()
    
    def test_get_shopping_list_multiple_categories(self, client, mock_db, mock_user):
        """Test shopping list with multiple ingredient categories."""
        from unittest.mock import patch
        from datetime import timedelta
        
        mock_response = ShoppingListResponse(
            week_number=1,
            start_date=date.today().isoformat(),
            end_date=(date.today() + timedelta(days=6)).isoformat(),
            categories=[
                {
                    "category": "protein",
                    "ingredients": [
                        {
                            "ingredient_id": str(uuid4()),
                            "name": "chicken_breast",
                            "category": "protein",
                            "total_quantity": 1500,
                            "unit": "g",
                            "used_in_dishes": ["Grilled Chicken"]
                        }
                    ]
                },
                {
                    "category": "vegetable",
                    "ingredients": [
                        {
                            "ingredient_id": str(uuid4()),
                            "name": "broccoli",
                            "category": "vegetable",
                            "total_quantity": 500,
                            "unit": "g",
                            "used_in_dishes": ["Stir Fry"]
                        }
                    ]
                }
            ],
            total_items=2
        )
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["categories"]) == 2
            assert data["total_items"] == 2
    
    def test_get_shopping_list_includes_date_range(self, client, mock_db, mock_user):
        """Test that shopping list includes start and end dates."""
        from unittest.mock import patch
        from datetime import timedelta
        
        start = date.today()
        end = start + timedelta(days=6)
        
        mock_response = ShoppingListResponse(
            week_number=1,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            categories=[],
            total_items=0
        )
        
        with patch('app.api.v1.endpoints.shopping_list.ShoppingListService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_shopping_list = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/meals/shopping-list/")
            
            assert response.status_code == 200
            data = response.json()
            assert "start_date" in data
            assert "end_date" in data
            assert data["start_date"] == start.isoformat()
            assert data["end_date"] == end.isoformat()


class TestShoppingListEndpointsAuthentication:
    """Tests for authentication requirements on shopping list endpoints."""
    
    def test_shopping_list_requires_authentication(self, app):
        """Test that shopping list endpoint requires authentication."""
        # Create client without authentication override
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/meals/shopping-list", tags=["shopping_list"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/meals/shopping-list/")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]

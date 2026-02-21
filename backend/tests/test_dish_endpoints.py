"""
Tests for dish endpoints.

Validates dish search and detail retrieval functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.dishes import router
from app.models.user import User
from app.models.profile import UserProfile
from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.preferences import DietaryPreference


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
    user.profile.dietary_preferences = DietaryPreference(
        id=uuid4(),
        profile_id=user.profile.id,
        diet_type="omnivore",
        allergies=["peanuts"],
        intolerances=[],
        dislikes=[]
    )
    return user


@pytest.fixture
def app(mock_db, mock_user):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/dishes", tags=["dishes"])
    
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


@pytest.fixture
def sample_dish():
    """Create a sample dish for testing."""
    dish = Dish(
        id=uuid4(),
        name="Egg Omelette with Multigrain Toast",
        name_hindi="अंडे का ऑमलेट",
        description="A protein-rich breakfast",
        cuisine_type="north_indian",
        meal_type="breakfast",
        dish_category="main_course",
        serving_size_g=250,
        calories=350,
        protein_g=25,
        carbs_g=30,
        fats_g=15,
        fiber_g=5,
        prep_time_minutes=5,
        cook_time_minutes=10,
        difficulty_level="easy",
        is_vegetarian=True,
        is_vegan=False,
        is_gluten_free=False,
        is_dairy_free=True,
        is_nut_free=True,
        contains_allergens=["eggs", "wheat"],
        is_active=True,
        popularity_score=85,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    dish.dish_ingredients = []
    return dish


@pytest.fixture
def sample_ingredient():
    """Create a sample ingredient for testing."""
    return Ingredient(
        id=uuid4(),
        name="eggs",
        name_hindi="अंडे",
        category="protein",
        typical_unit="piece",
        is_allergen=True,
        allergen_type="eggs",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestSearchDishes:
    """Tests for GET /api/v1/dishes/search endpoint."""
    
    def test_search_dishes_success(self, client, mock_user, sample_dish):
        """Test successful dish search without filters."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Egg Omelette with Multigrain Toast"
            assert data[0]["meal_type"] == "breakfast"
            assert data[0]["calories"] == 350
    
    def test_search_dishes_with_meal_type_filter(self, client, mock_user, sample_dish):
        """Test dish search with meal type filter."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search?meal_type=breakfast")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["meal_type"] == "breakfast"
            
            # Verify service was called with correct parameters
            mock_service.search_dishes.assert_called_once()
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["meal_type"] == "breakfast"
    
    def test_search_dishes_with_diet_type_filter(self, client, mock_user, sample_dish):
        """Test dish search with diet type filter."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search?diet_type=vegetarian")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["is_vegetarian"] is True
            
            # Verify service was called with correct parameters
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["diet_type"] == "vegetarian"
    
    def test_search_dishes_with_max_prep_time(self, client, mock_user, sample_dish):
        """Test dish search with maximum preparation time filter."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search?max_prep_time=30")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            total_time = data[0]["prep_time_minutes"] + data[0]["cook_time_minutes"]
            assert total_time <= 30
            
            # Verify service was called with correct parameters
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["max_prep_time"] == 30
    
    def test_search_dishes_with_max_calories(self, client, mock_user, sample_dish):
        """Test dish search with maximum calories filter."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search?max_calories=500")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["calories"] <= 500
            
            # Verify service was called with correct parameters
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["max_calories"] == 500
    
    def test_search_dishes_with_pagination(self, client, mock_user, sample_dish):
        """Test dish search with pagination parameters."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search?limit=10&offset=20")
            
            assert response.status_code == 200
            
            # Verify service was called with correct parameters
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["limit"] == 10
            assert call_kwargs["offset"] == 20
    
    def test_search_dishes_excludes_user_allergens(self, client, mock_user, sample_dish):
        """Test that search excludes dishes with user's allergens."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get("/api/v1/dishes/search")
            
            assert response.status_code == 200
            
            # Verify service was called with user's allergens
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert "peanuts" in call_kwargs["exclude_allergens"]
    
    def test_search_dishes_invalid_limit(self, client):
        """Test search with invalid limit parameter."""
        response = client.get("/api/v1/dishes/search?limit=150")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_dishes_invalid_offset(self, client):
        """Test search with invalid offset parameter."""
        response = client.get("/api/v1/dishes/search?offset=-1")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_dishes_empty_results(self, client, mock_user):
        """Test search with no matching dishes."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[])
            
            response = client.get("/api/v1/dishes/search?meal_type=breakfast")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
    
    def test_search_dishes_multiple_filters(self, client, mock_user, sample_dish):
        """Test search with multiple filters combined."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.search_dishes = AsyncMock(return_value=[sample_dish])
            
            response = client.get(
                "/api/v1/dishes/search"
                "?meal_type=breakfast"
                "&diet_type=vegetarian"
                "&max_prep_time=30"
                "&max_calories=400"
                "&limit=20"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            
            # Verify all filters were passed to service
            call_kwargs = mock_service.search_dishes.call_args.kwargs
            assert call_kwargs["meal_type"] == "breakfast"
            assert call_kwargs["diet_type"] == "vegetarian"
            assert call_kwargs["max_prep_time"] == 30
            assert call_kwargs["max_calories"] == 400
            assert call_kwargs["limit"] == 20


class TestGetDish:
    """Tests for GET /api/v1/dishes/{dish_id} endpoint."""
    
    def test_get_dish_success(self, client, mock_user, sample_dish, sample_ingredient):
        """Test successful dish retrieval with ingredients."""
        # Add ingredient to dish
        dish_ingredient = DishIngredient(
            id=uuid4(),
            dish_id=sample_dish.id,
            ingredient_id=sample_ingredient.id,
            quantity=3,
            unit="piece",
            preparation_note="beaten",
            is_optional=False
        )
        dish_ingredient.ingredient = sample_ingredient
        sample_dish.dish_ingredients = [dish_ingredient]
        
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_dish = AsyncMock(return_value=sample_dish)
            
            response = client.get(f"/api/v1/dishes/{sample_dish.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(sample_dish.id)
            assert data["name"] == "Egg Omelette with Multigrain Toast"
            assert data["calories"] == 350
            assert "ingredients" in data
            assert len(data["ingredients"]) == 1
            assert data["ingredients"][0]["ingredient"]["name"] == "eggs"
            assert data["ingredients"][0]["quantity"] == 3
            assert data["ingredients"][0]["unit"] == "piece"
    
    def test_get_dish_not_found(self, client, mock_user):
        """Test 404 when dish doesn't exist."""
        dish_id = uuid4()
        
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_dish = AsyncMock(return_value=None)
            
            response = client.get(f"/api/v1/dishes/{dish_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_get_dish_includes_all_fields(self, client, mock_user, sample_dish):
        """Test that dish response includes all expected fields."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_dish = AsyncMock(return_value=sample_dish)
            
            response = client.get(f"/api/v1/dishes/{sample_dish.id}")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields are present
            required_fields = [
                "id", "name", "name_hindi", "description",
                "cuisine_type", "meal_type", "dish_category",
                "serving_size_g", "calories", "protein_g", "carbs_g", "fats_g",
                "prep_time_minutes", "cook_time_minutes",
                "difficulty_level", "is_vegetarian", "is_vegan",
                "is_gluten_free", "is_dairy_free", "is_nut_free",
                "contains_allergens"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
    
    def test_get_dish_with_allergen_info(self, client, mock_user, sample_dish):
        """Test that dish response includes allergen information."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_dish = AsyncMock(return_value=sample_dish)
            
            response = client.get(f"/api/v1/dishes/{sample_dish.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "contains_allergens" in data
            assert "eggs" in data["contains_allergens"]
            assert "wheat" in data["contains_allergens"]
    
    def test_get_dish_service_called_with_ingredients(self, client, mock_user, sample_dish):
        """Test that service is called with include_ingredients=True."""
        with patch('app.api.v1.endpoints.dishes.DishService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_dish = AsyncMock(return_value=sample_dish)
            
            response = client.get(f"/api/v1/dishes/{sample_dish.id}")
            
            assert response.status_code == 200
            
            # Verify service was called with include_ingredients=True
            mock_service.get_dish.assert_called_once_with(
                sample_dish.id,
                include_ingredients=True
            )


class TestDishEndpointsAuthentication:
    """Tests for authentication requirements on dish endpoints."""
    
    def test_search_dishes_requires_authentication(self, app):
        """Test that search endpoint requires authentication."""
        # Create client without authentication override
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/dishes", tags=["dishes"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/dishes/search")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]
    
    def test_get_dish_requires_authentication(self, app):
        """Test that get dish endpoint requires authentication."""
        # Create client without authentication override
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/dishes", tags=["dishes"])
        client = TestClient(test_app)
        
        dish_id = uuid4()
        response = client.get(f"/api/v1/dishes/{dish_id}")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]

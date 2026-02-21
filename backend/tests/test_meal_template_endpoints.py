"""
Tests for meal template endpoints.

Validates meal template retrieval, regeneration, and dish swapping.
"""

import pytest
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.meal_templates import router
from app.models.user import User
from app.models.profile import UserProfile
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealSchedule
from app.models.dish import Dish
from app.core.exceptions import ProfileLockedException


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
    app.include_router(router, prefix="/api/v1/meals", tags=["meal_templates"])
    
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
def mock_template():
    """Create a mock meal template."""
    from datetime import datetime
    template = MealTemplate(
        id=uuid4(),
        profile_id=uuid4(),
        week_number=1,
        is_active=True,
        generated_by='ai_agent',
        generation_reason='Test template',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    template.template_meals = []
    return template


class TestGetTodayMeals:
    """Tests for GET /api/v1/meals/today endpoint."""
    
    def test_get_today_meals_success(self, client, mock_user):
        """Test successful retrieval of today's meals."""
        from datetime import date
        
        mock_meals_data = {
            "date": date.today().isoformat(),
            "day_of_week": date.today().weekday(),
            "day_name": date.today().strftime('%A'),
            "meals": [
                {
                    "meal_name": "Breakfast",
                    "scheduled_time": "08:00:00",
                    "day_of_week": date.today().weekday(),
                    "primary_dish": {
                        "id": str(uuid4()),
                        "name": "Egg Omelette",
                        "name_hindi": "अंडे का आमलेट",
                        "meal_type": "breakfast",
                        "cuisine_type": "continental",
                        "calories": 350,
                        "protein_g": 25,
                        "carbs_g": 30,
                        "fats_g": 15,
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 10,
                        "difficulty_level": "easy",
                        "is_vegetarian": True,
                        "is_vegan": False
                    },
                    "alternative_dishes": []
                }
            ],
            "total_calories": 2200,
            "total_protein_g": 165,
            "total_carbs_g": 250,
            "total_fats_g": 60
        }
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_today_meals = AsyncMock(return_value=mock_meals_data)
            
            response = client.get("/api/v1/meals/today")
            
            assert response.status_code == 200
            data = response.json()
            assert "date" in data
            assert "meals" in data
            assert len(data["meals"]) == 1
            assert data["meals"][0]["meal_name"] == "Breakfast"
            assert data["total_calories"] == 2200
    
    def test_get_today_meals_no_template(self, client, mock_user):
        """Test 404 when no active template exists."""
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_today_meals = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="No active meal template found")
            )
            
            response = client.get("/api/v1/meals/today")
            
            assert response.status_code == 404


class TestGetNextMeal:
    """Tests for GET /api/v1/meals/next endpoint."""
    
    def test_get_next_meal_success(self, client, mock_user):
        """Test successful retrieval of next meal."""
        mock_next_meal = {
            "meal_name": "Lunch",
            "scheduled_time": "13:00:00",
            "time_until_meal_minutes": 45,
            "primary_dish": {
                "id": str(uuid4()),
                "name": "Grilled Chicken",
                "name_hindi": "ग्रिल्ड चिकन",
                "meal_type": "lunch",
                "cuisine_type": "continental",
                "calories": 550,
                "protein_g": 45,
                "carbs_g": 40,
                "fats_g": 20,
                "prep_time_minutes": 10,
                "cook_time_minutes": 20,
                "difficulty_level": "medium",
                "is_vegetarian": False,
                "is_vegan": False
            },
            "alternative_dishes": []
        }
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_next_meal = AsyncMock(return_value=mock_next_meal)
            
            response = client.get("/api/v1/meals/next")
            
            assert response.status_code == 200
            data = response.json()
            assert data["meal_name"] == "Lunch"
            assert data["time_until_meal_minutes"] == 45
            assert "primary_dish" in data
    
    def test_get_next_meal_none_remaining(self, client, mock_user):
        """Test 404 when no more meals scheduled today."""
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_next_meal = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/meals/next")
            
            assert response.status_code == 404
            data = response.json()
            assert "no more meals" in data["detail"].lower()


class TestGetMealTemplate:
    """Tests for GET /api/v1/meals/template endpoint."""
    
    def test_get_active_template(self, client, mock_user, mock_template):
        """Test retrieval of active template without week number."""
        mock_template.template_meals = []
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_active_template = AsyncMock(return_value=mock_template)
            
            response = client.get("/api/v1/meals/template")
            
            assert response.status_code == 200
            data = response.json()
            assert data["week_number"] == 1
            assert data["is_active"] is True
            assert "days" in data
    
    def test_get_template_by_week(self, client, mock_user, mock_template):
        """Test retrieval of specific week template."""
        mock_template.template_meals = []
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=mock_template)
            
            response = client.get("/api/v1/meals/template?week_number=2")
            
            assert response.status_code == 200
            data = response.json()
            assert "week_number" in data
    
    def test_get_template_not_found(self, client, mock_user):
        """Test 404 when template doesn't exist."""
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/meals/template?week_number=3")
            
            assert response.status_code == 404
    
    def test_get_template_invalid_week_number(self, client):
        """Test validation error for invalid week number."""
        response = client.get("/api/v1/meals/template?week_number=5")
        
        assert response.status_code == 422  # Validation error


class TestRegenerateMealTemplate:
    """Tests for POST /api/v1/meals/template/regenerate endpoint."""
    
    def test_regenerate_success(self, client, mock_user, mock_template):
        """Test successful template regeneration."""
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=None)
            mock_service.generate_template = AsyncMock(return_value=mock_template)
            
            response = client.post(
                "/api/v1/meals/template/regenerate",
                json={
                    "preferences": "More chicken dishes",
                    "week_number": 1
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["week_number"] == 1
            assert data["is_active"] is True
            assert "days" in data
            assert len(data["days"]) == 7
    
    def test_regenerate_without_week_number(self, client, mock_user, mock_template):
        """Test regeneration without specifying week number (uses current week)."""
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=None)
            mock_service.generate_template = AsyncMock(return_value=mock_template)
            
            response = client.post(
                "/api/v1/meals/template/regenerate",
                json={}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "week_number" in data
    
    def test_regenerate_profile_locked(self, client, mock_user):
        """Test 403 when profile is locked."""
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=None)
            mock_service.generate_template = AsyncMock(
                side_effect=ProfileLockedException()
            )
            
            response = client.post(
                "/api/v1/meals/template/regenerate",
                json={"week_number": 1}
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "locked" in data["detail"].lower()
    
    def test_regenerate_missing_meal_plan(self, client, mock_user):
        """Test 400 when user doesn't have meal plan configured."""
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=None)
            mock_service.generate_template = AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail="User must have meal plan and schedules configured"
                )
            )
            
            response = client.post(
                "/api/v1/meals/template/regenerate",
                json={"week_number": 1}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "meal plan" in data["detail"].lower()
    
    def test_regenerate_replaces_existing_template(self, client, mock_user, mock_template):
        """Test that regeneration soft-deletes existing template."""
        existing_template = MealTemplate(
            id=uuid4(),
            profile_id=mock_user.profile.id,
            week_number=1,
            is_active=True
        )
        
        with patch('app.api.v1.endpoints.meal_templates.MealTemplateService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_template_by_week = AsyncMock(return_value=existing_template)
            mock_service.generate_template = AsyncMock(return_value=mock_template)
            
            response = client.post(
                "/api/v1/meals/template/regenerate",
                json={"week_number": 1}
            )
            
            assert response.status_code == 201
            # Verify existing template was soft-deleted
            assert existing_template.deleted_at is not None


class TestMealTemplateEndpointsAuthentication:
    """Tests for authentication requirements on meal template endpoints."""
    
    def test_today_meals_requires_authentication(self, app):
        """Test that today meals endpoint requires authentication."""
        # Create client without authentication override
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/meals", tags=["meal_templates"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/meals/today")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]
    
    def test_next_meal_requires_authentication(self, app):
        """Test that next meal endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/meals", tags=["meal_templates"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/meals/next")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]
    
    def test_get_template_requires_authentication(self, app):
        """Test that get template endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/meals", tags=["meal_templates"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/meals/template")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]
    
    def test_regenerate_requires_authentication(self, app):
        """Test that regenerate endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/meals", tags=["meal_templates"])
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/meals/template/regenerate",
            json={"week_number": 1}
        )
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 403]

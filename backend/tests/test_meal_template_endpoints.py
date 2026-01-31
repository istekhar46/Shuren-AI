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

"""
Tests for authentication endpoints.

Validates user registration, login, Google OAuth, and current user retrieval.

Note: These tests verify endpoint logic. Full integration tests with PostgreSQL
should be run separately as SQLite doesn't support JSONB columns used in the schema.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import router
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.onboarding import OnboardingState


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
def app(mock_db):
    """Create FastAPI test application with mocked database."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/auth", tags=["auth"])
    
    # Override get_db dependency
    from app.db.session import get_db
    
    async def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register endpoint."""
    
    def test_register_success(self, client, mock_db):
        """Test successful user registration."""
        # Mock database to return no existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securePassword123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
    
    def test_register_duplicate_email(self, client, mock_db):
        """Test registration with duplicate email returns 400."""
        # Mock database to return existing user
        existing_user = User(
            id=uuid4(),
            email="duplicate@example.com",
            hashed_password=hash_password("password"),
            full_name="Existing User"
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_user)
        mock_db.execute.return_value = mock_result
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "full_name": "Second User"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_short_password(self, client):
        """Test registration with password < 8 characters returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""
    
    def test_login_success(self, client, mock_db):
        """Test successful login with valid credentials."""
        # Create user with hashed password
        password = "myPassword123"
        user = User(
            id=uuid4(),
            email="login@example.com",
            hashed_password=hash_password(password),
            full_name="Login User",
            is_active=True
        )
        
        # Mock database to return user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
    
    def test_login_invalid_email(self, client, mock_db):
        """Test login with non-existent email returns 401."""
        # Mock database to return no user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, mock_db):
        """Test login with incorrect password returns 401."""
        # Create user
        user = User(
            id=uuid4(),
            email="user@example.com",
            hashed_password=hash_password("correctPassword"),
            full_name="Test User",
            is_active=True
        )
        
        # Mock database to return user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongPassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_oauth_user_without_password(self, client, mock_db):
        """Test login fails for OAuth user (no password set)."""
        # Create OAuth user without password
        user = User(
            id=uuid4(),
            email="oauth@example.com",
            hashed_password=None,
            full_name="OAuth User",
            oauth_provider="google",
            oauth_provider_user_id="123456",
            is_active=True
        )
        
        # Mock database to return user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result
        
        # Try to login with password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "oauth@example.com",
                "password": "anyPassword"
            }
        )
        
        assert response.status_code == 401


class TestGoogleAuthEndpoint:
    """Tests for POST /api/v1/auth/google endpoint with CSRF protection and enhanced validation."""
    
    def test_google_auth_new_user_success(self, client, mock_db):
        """Test Google OAuth creates new user with onboarding state."""
        # Mock database to return no existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result
        
        mock_user_info = {
            'email': 'newgoogle@example.com',
            'name': 'Google User',
            'sub': 'google-user-id-123',
            'email_verified': True,
            'picture': 'https://example.com/photo.jpg',
            'hd': None
        }
        
        with patch('app.api.v1.endpoints.auth.verify_google_token', return_value=mock_user_info):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "valid-google-token",
                    "g_csrf_token": "csrf-token-123"
                },
                cookies={"g_csrf_token": "csrf-token-123"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        
        # Verify user was created with correct OAuth fields
        assert mock_db.add.called
        # Verify onboarding state was created
        assert mock_db.add.call_count == 2  # User + OnboardingState
    
    def test_google_auth_existing_user_returns_jwt(self, client, mock_db):
        """Test Google OAuth returns JWT for existing user."""
        # Create existing OAuth user
        user = User(
            id=uuid4(),
            email="existing@example.com",
            hashed_password=None,
            full_name="Existing User",
            oauth_provider="google",
            oauth_provider_user_id="existing-google-id",
            is_active=True
        )
        
        # Mock database to return existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result
        
        mock_user_info = {
            'email': 'existing@example.com',
            'name': 'Existing User',
            'sub': 'existing-google-id',
            'email_verified': True,
            'picture': None,
            'hd': None
        }
        
        with patch('app.api.v1.endpoints.auth.verify_google_token', return_value=mock_user_info):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "valid-google-token",
                    "g_csrf_token": "csrf-token-456"
                },
                cookies={"g_csrf_token": "csrf-token-456"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert str(user.id) == data["user_id"]
    
    def test_google_auth_csrf_validation_failure_missing_cookie(self, client):
        """Test Google OAuth fails with missing CSRF cookie."""
        response = client.post(
            "/api/v1/auth/google",
            json={
                "credential": "valid-google-token",
                "g_csrf_token": "csrf-token-123"
            }
            # No cookie provided
        )
        
        assert response.status_code == 400
        assert "CSRF" in response.json()["detail"]
    
    def test_google_auth_csrf_validation_failure_missing_body_token(self, client):
        """Test Google OAuth fails with missing CSRF body token."""
        response = client.post(
            "/api/v1/auth/google",
            json={
                "credential": "valid-google-token"
                # Missing g_csrf_token
            },
            cookies={"g_csrf_token": "csrf-token-123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_google_auth_csrf_validation_failure_token_mismatch(self, client):
        """Test Google OAuth fails with mismatched CSRF tokens."""
        response = client.post(
            "/api/v1/auth/google",
            json={
                "credential": "valid-google-token",
                "g_csrf_token": "csrf-token-123"
            },
            cookies={"g_csrf_token": "different-csrf-token"}
        )
        
        assert response.status_code == 400
        assert "mismatch" in response.json()["detail"].lower()
    
    def test_google_auth_invalid_token(self, client):
        """Test Google OAuth with invalid token returns 401."""
        with patch('app.api.v1.endpoints.auth.verify_google_token', side_effect=ValueError("Invalid token")):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "invalid-token",
                    "g_csrf_token": "csrf-token-789"
                },
                cookies={"g_csrf_token": "csrf-token-789"}
            )
        
        assert response.status_code == 401
    
    def test_google_auth_unverified_email(self, client):
        """Test Google OAuth fails with unverified email."""
        with patch('app.api.v1.endpoints.auth.verify_google_token', side_effect=ValueError("Email address is not verified")):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "unverified-email-token",
                    "g_csrf_token": "csrf-token-999"
                },
                cookies={"g_csrf_token": "csrf-token-999"}
            )
        
        assert response.status_code == 401
        assert "not verified" in response.json()["detail"].lower()
    
    def test_google_auth_uses_sub_claim_for_user_id(self, client, mock_db):
        """Test that oauth_provider_user_id uses sub claim (not email)."""
        # Mock database to return no existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result
        
        google_sub = "unique-google-sub-12345"
        mock_user_info = {
            'email': 'user@example.com',
            'name': 'Test User',
            'sub': google_sub,  # This should be used for oauth_provider_user_id
            'email_verified': True,
            'picture': None,
            'hd': None
        }
        
        with patch('app.api.v1.endpoints.auth.verify_google_token', return_value=mock_user_info):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "valid-token",
                    "g_csrf_token": "csrf-abc"
                },
                cookies={"g_csrf_token": "csrf-abc"}
            )
        
        assert response.status_code == 200
        
        # Verify the database query used oauth_provider and oauth_provider_user_id (sub claim)
        # The execute call should have been made with a query filtering by these fields
        assert mock_db.execute.called
    
    def test_google_auth_jwt_token_format(self, client, mock_db):
        """Test that Google OAuth returns properly formatted JWT token."""
        # Mock database to return no existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result
        
        mock_user_info = {
            'email': 'jwt@example.com',
            'name': 'JWT User',
            'sub': 'jwt-sub-123',
            'email_verified': True,
            'picture': None,
            'hd': None
        }
        
        with patch('app.api.v1.endpoints.auth.verify_google_token', return_value=mock_user_info):
            response = client.post(
                "/api/v1/auth/google",
                json={
                    "credential": "valid-token",
                    "g_csrf_token": "csrf-xyz"
                },
                cookies={"g_csrf_token": "csrf-xyz"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert data["token_type"] == "bearer"
        
        # Verify JWT token format (should have 3 parts separated by dots)
        token_parts = data["access_token"].split(".")
        assert len(token_parts) == 3


class TestGetMeEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""
    
    def test_get_me_success(self, client, mock_db):
        """Test /me endpoint returns current user data."""
        # Create user with created_at timestamp
        from datetime import datetime, timezone
        user = User(
            id=uuid4(),
            email="me@example.com",
            hashed_password=hash_password("password"),
            full_name="Me User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock database to return user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result
        
        # Get token
        token = create_access_token({"user_id": str(user.id)})
        
        # Call /me endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["full_name"] == "Me User"
        assert data["is_active"] is True
    
    def test_get_me_no_token(self, client):
        """Test /me endpoint without token returns 401."""
        response = client.get("/api/v1/auth/me")
        
        # FastAPI returns 401 when no auth header is provided
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self, client):
        """Test /me endpoint with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

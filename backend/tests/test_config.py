"""
Tests for configuration management.

Validates that the Settings class properly loads and validates configuration.
"""

import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_settings_loads_from_env(monkeypatch):
    """Test that Settings loads configuration from environment variables."""
    # Set required environment variables
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    
    # Create settings instance
    settings = Settings()
    
    # Verify required fields are loaded
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"
    assert settings.JWT_SECRET_KEY == "test-secret-key"
    assert settings.GOOGLE_CLIENT_ID == "test-client-id"
    assert settings.GOOGLE_CLIENT_SECRET == "test-client-secret"


def test_settings_default_values(monkeypatch):
    """Test that Settings uses correct default values."""
    # Set only required fields
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    
    settings = Settings()
    
    # Verify default values
    assert settings.APP_NAME == "Shuren Backend"
    assert settings.DEBUG is False
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS == 24
    assert settings.LOG_LEVEL == "INFO"


def test_settings_requires_database_url(monkeypatch):
    """Test that Settings raises ValidationError when DATABASE_URL is missing."""
    # Disable .env file loading and clear all environment variables
    monkeypatch.setattr("pydantic_settings.sources.DotEnvSettingsSource.__call__", lambda *args, **kwargs: {})
    
    # Set all required fields except DATABASE_URL
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    # Verify DATABASE_URL is in the error
    assert "DATABASE_URL" in str(exc_info.value)


def test_settings_requires_jwt_secret(monkeypatch):
    """Test that Settings raises ValidationError when JWT_SECRET_KEY is missing."""
    # Disable .env file loading
    monkeypatch.setattr("pydantic_settings.sources.DotEnvSettingsSource.__call__", lambda *args, **kwargs: {})
    
    # Set all required fields except JWT_SECRET_KEY
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    # Verify JWT_SECRET_KEY is in the error
    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_cors_origins_list_property(monkeypatch):
    """Test that cors_origins_list property correctly parses CORS_ORIGINS."""
    # Set required fields
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,https://example.com")
    
    settings = Settings()
    
    # Verify CORS origins are parsed correctly
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://example.com"
    ]


def test_settings_custom_jwt_expiration(monkeypatch):
    """Test that JWT_ACCESS_TOKEN_EXPIRE_HOURS can be customized."""
    # Set required fields with custom JWT expiration
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "48")
    
    settings = Settings()
    
    # Verify custom expiration is used
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS == 48

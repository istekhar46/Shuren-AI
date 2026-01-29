"""
Configuration management using Pydantic BaseSettings.

This module provides centralized configuration for the Shuren backend application.
All settings are loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All configuration values are validated by Pydantic at startup.
    Sensitive values (secrets) must be provided via environment variables.
    """
    
    # Application Configuration
    APP_NAME: str = "Shuren Backend"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str
    
    # JWT Authentication Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # Redis Configuration (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Singleton instance of settings
# This is imported throughout the application for configuration access
settings = Settings()

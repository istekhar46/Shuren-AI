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
    def async_database_url(self) -> str:
        """
        Convert DATABASE_URL to asyncpg format if needed.
        
        SQLAlchemy with asyncpg requires postgresql+asyncpg:// protocol.
        This property automatically converts legacy postgres:// or postgresql://
        formats to the correct asyncpg format and removes sslmode parameter
        (asyncpg handles SSL automatically for cloud databases).
        
        Returns:
            str: Database URL with postgresql+asyncpg:// protocol
        """
        url = self.DATABASE_URL
        
        # Convert protocol to asyncpg format
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Remove sslmode parameter - asyncpg handles SSL automatically
        import re
        url = re.sub(r'[?&]sslmode=[^&]*', '', url)
        # Clean up any trailing ? or & characters
        url = re.sub(r'[?&]$', '', url)
        
        return url
    
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

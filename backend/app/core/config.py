"""
Configuration management using Pydantic BaseSettings.

This module provides centralized configuration for the Shuren backend application.
All settings are loaded from environment variables or .env file.
"""

from enum import Enum
from pydantic_settings import BaseSettings
from typing import List, Optional


class LLMProvider(str, Enum):
    """
    Supported LLM providers for agent interactions.
    
    This enum defines the available LLM providers that can be used for
    agent responses. Each provider requires its corresponding API key
    to be configured in the environment.
    
    Attributes:
        ANTHROPIC: Anthropic Claude models (default provider)
        OPENAI: OpenAI GPT models
        GOOGLE: Google Gemini models
    """
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All configuration values are validated by Pydantic at startup.
    Sensitive values (secrets) must be provided via environment variables.
    """
    
    # Application Configuration
    APP_NAME: str = "Shuren Backend"
    """Application name for logging and identification."""
    
    DEBUG: bool = False
    """Enable debug mode for development (default: False)."""
    
    # Database Configuration
    DATABASE_URL: str
    """PostgreSQL database connection URL (required)."""
    
    # JWT Authentication Configuration
    JWT_SECRET_KEY: str
    """Secret key for JWT token signing (required, keep secure)."""
    
    JWT_ALGORITHM: str = "HS256"
    """Algorithm for JWT token signing (default: HS256)."""
    
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    """JWT access token expiration time in hours (default: 24)."""
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str
    """Google OAuth client ID for authentication (required)."""
    
    GOOGLE_CLIENT_SECRET: str
    """Google OAuth client secret for authentication (required)."""
    
    # Redis Configuration (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    """Redis connection URL for caching (default: localhost:6379/0)."""
    
    # LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    """Active LLM provider for agent interactions (default: anthropic)."""
    
    LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    """LLM model name/identifier for the active provider."""
    
    LLM_TEMPERATURE: float = 0.7
    """Temperature for LLM responses (0.0-1.0, default: 0.7)."""
    
    LLM_MAX_TOKENS: int = 4096
    """Maximum tokens for LLM responses (default: 4096)."""
    
    # LLM API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    """Anthropic API key (required if LLM_PROVIDER is anthropic)."""
    
    OPENAI_API_KEY: Optional[str] = None
    """OpenAI API key (required if LLM_PROVIDER is openai)."""
    
    GOOGLE_API_KEY: Optional[str] = None
    """Google API key (required if LLM_PROVIDER is google)."""
    
    # Classifier Configuration (for fast query routing)
    CLASSIFIER_MODEL: str = "claude-haiku-4-5-20251001"
    """Fast classifier model for query routing (default: Claude Haiku)."""
    
    CLASSIFIER_TEMPERATURE: float = 0.1
    """Temperature for classifier (low for consistency, default: 0.1)."""
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    """Comma-separated list of allowed CORS origins."""
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    
    # LiveKit Configuration
    LIVEKIT_URL: str
    """LiveKit server URL (wss://...)."""
    
    LIVEKIT_API_KEY: str
    """LiveKit API key."""
    
    LIVEKIT_API_SECRET: str
    """LiveKit API secret."""
    
    LIVEKIT_WORKER_NUM_IDLE: int = 2
    """Number of idle agent workers to maintain."""
    
    # Voice Service Configuration
    DEEPGRAM_API_KEY: Optional[str] = None
    """Deepgram API key for Speech-to-Text (required for voice agents)."""
    
    CARTESIA_API_KEY: Optional[str] = None
    """Cartesia API key for Text-to-Speech (required for voice agents)."""
    
    VOICE_CONTEXT_CACHE_TTL: int = 3600
    """Voice agent context cache TTL in seconds (default: 3600 = 1 hour)."""
    
    VOICE_MAX_RESPONSE_TOKENS: int = 150
    """Maximum tokens for voice responses to keep them concise (default: 150)."""
    
    VOICE_LLM_PROVIDER: str = "google"
    """LLM provider for voice agent function calling (openai, anthropic, google)."""
    
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
        """
        Parse CORS_ORIGINS string into a list.
        
        Converts the comma-separated CORS_ORIGINS string into a list
        of individual origin URLs for FastAPI CORS middleware.
        
        Returns:
            List[str]: List of allowed CORS origin URLs
            
        Example:
            >>> settings.CORS_ORIGINS = "http://localhost:3000,http://localhost:8080"
            >>> settings.cors_origins_list
            ['http://localhost:3000', 'http://localhost:8080']
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def get_required_llm_api_key(self) -> str:
        """
        Get the API key for the configured LLM provider.
        
        Validates that the required API key is configured for the active
        LLM provider and returns it. This method is called during agent
        initialization to ensure proper configuration.
        
        Returns:
            str: The API key for the active LLM provider
            
        Raises:
            ValueError: If the required API key is not configured for the active provider
            
        Example:
            >>> settings.LLM_PROVIDER = LLMProvider.ANTHROPIC
            >>> settings.ANTHROPIC_API_KEY = "sk-ant-xxx"
            >>> api_key = settings.get_required_llm_api_key()
            >>> assert api_key == "sk-ant-xxx"
        """
        if self.LLM_PROVIDER == LLMProvider.ANTHROPIC:
            if not self.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'"
                )
            return self.ANTHROPIC_API_KEY
        elif self.LLM_PROVIDER == LLMProvider.OPENAI:
            if not self.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'"
                )
            return self.OPENAI_API_KEY
        elif self.LLM_PROVIDER == LLMProvider.GOOGLE:
            if not self.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY is required when LLM_PROVIDER is 'google'"
                )
            return self.GOOGLE_API_KEY
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Singleton instance of settings
# This is imported throughout the application for configuration access
settings = Settings()

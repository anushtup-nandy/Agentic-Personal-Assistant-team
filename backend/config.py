"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # AI API Configuration
    gemini_api_key: str
    ollama_base_url: str = "http://localhost:11434"
    
    # Database
    database_url: str = "sqlite:///./agent_assistant.db"
    
    # Application
    app_env: str = "development"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Security
    secret_key: str
    
    # Vector Store
    chroma_persist_directory: str = "./data/chroma"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


# Global settings instance
settings = Settings()

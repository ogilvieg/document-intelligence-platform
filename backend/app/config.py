"""Application configuration using Pydantic Settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # FastAPI Configuration
    environment: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database Configuration
    # Set RDS_DATABASE_URL to use AWS RDS PostgreSQL directly (preferred).
    # Named RDS_DATABASE_URL (not DATABASE_URL) to avoid collision with
    # Render's auto-injected DATABASE_URL for linked Postgres services.
    # If not set, falls back to Supabase (backwards compatible).
    rds_database_url: Optional[str] = None

    # Supabase Configuration (legacy — only required when DATABASE_URL is not set)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Document Processing
    max_file_size_mb: int = 10
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # Security
    api_key: str = ""  # Optional: Set to enable API key authentication
    
    # Observability
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

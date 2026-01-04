"""Application configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "mindnest123"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://mindnest:mindnest@localhost:5432/mindnest"

    # Google AI
    google_api_key: str = ""
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"

    # LLM Models
    llm_model: str = "gemini-2.5-flash-lite"
    llm_model_pro: str = "gemini-2.5-pro"

    # App
    secret_key: str = "change-me-in-production"
    debug: bool = True

    # Graphiti
    semaphore_limit: int = 10  # Concurrent LLM operations

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

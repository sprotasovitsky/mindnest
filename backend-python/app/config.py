"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "mindnest123"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://mindnest:mindnest@localhost:5432/mindnest"

    # Google AI
    google_api_key: str = ""
    google_application_credentials: str = ""
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"

    # LLM Models
    llm_model: str = "gemini-2.5-flash-lite"  # Fast, cost-effective
    llm_model_balanced: str = "gemini-2.5-flash"  # Balanced speed/quality
    llm_model_pro: str = "gemini-2.5-pro"  # Best quality

    # Model for Graphiti entity extraction (can be overridden via env var)
    graphiti_model: str = "gemini-2.5-flash"  # Best balance of speed and quality for entity extraction
    # Embeddings configured in Graphiti: gemini-embedding-001 (3072 dimensions)

    # Search
    search_limit: int = 40  # Max edges/nodes returned from search

    # Chat history
    chat_history_limit: int = 10  # Number of recent messages to include in LLM context

    # App
    secret_key: str = Field(default="change-me-in-production")
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

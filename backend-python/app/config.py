"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
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

    # Vertex AI credentials
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"
    gcp_service_account_email: str = ""
    gcp_private_key: str = ""  # PEM format

    # LLM Models
    llm_model: str = "gemini-2.5-flash-lite"  # Fast, cost-effective
    llm_model_balanced: str = "gemini-2.5-flash"  # Balanced speed/quality
    llm_model_pro: str = "gemini-3-flash-preview"  # Best quality (requires Vertex AI, not API key)

    # Model for Graphiti entity extraction (can be overridden via env var)
    graphiti_model: str = "gemini-2.5-flash"  # Best balance of speed and quality for entity extraction
    # Embeddings configured in Graphiti: gemini-embedding-001 (3072 dimensions)

    # Search
    search_limit: int = 40  # Max edges/nodes returned from search

    # Chat history
    chat_history_limit: int = 10  # Number of recent messages to include in LLM context

    # Security
    secret_key: str = Field(default="")
    debug: bool = False

    # CORS - comma-separated list of allowed origins
    allowed_origins: str = "http://localhost:3000,http://localhost:8080,https://mindnest.one,https://*.mindnest.one"

    # Rate limiting (production defaults)
    rate_limit_login: str = "5/minute"
    rate_limit_register: str = "3/minute"
    rate_limit_chat: str = "30/minute"
    rate_limit_verify_email: str = "10/minute"
    rate_limit_resend_verification: str = "3/minute"
    rate_limit_password_reset: str = "5/minute"
    rate_limit_change_password: str = "5/minute"

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "MindNest <hello@mindnest.one>"
    frontend_url: str = "https://mindnest.one"

    # Token expiration settings
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 15
    reset_code_expire_minutes: int = 10
    reset_code_max_attempts: int = 5
    resend_email_cooldown_seconds: int = 60

    # Token limits for unverified users
    unverified_token_limit: int = 1_000_000  # 1M tokens

    # Social login - separate client IDs for each platform
    google_ios_client_id: str = ""      # iOS client ID
    google_android_client_id: str = ""  # Android client ID
    apple_client_id: str = ""           # Bundle ID (com.mindnest.app.dev/staging/prod)

    def get_google_client_ids(self) -> list[str]:
        """Get all valid Google client IDs for token verification."""
        ids = []
        if self.google_ios_client_id:
            ids.append(self.google_ios_client_id)
        if self.google_android_client_id:
            ids.append(self.google_android_client_id)
        return ids

    def get_apple_client_ids(self) -> list[str]:
        """Get all valid Apple client IDs (bundle IDs) for token verification."""
        ids = []
        if self.apple_client_id:
            ids.append(self.apple_client_id)
        return ids

    def get_rate_limit(self, limit_type: str) -> str:
        """Get rate limit based on debug mode. Higher limits for local dev."""
        if self.debug:
            # Relaxed limits for local development/testing
            debug_limits = {
                "login": "100/minute",
                "register": "100/minute",
                "chat": "200/minute",
                "verify_email": "100/minute",
                "resend_verification": "100/minute",
                "password_reset": "100/minute",
                "change_password": "100/minute",
            }
            return debug_limits.get(limit_type, "100/minute")

        # Production limits
        limits = {
            "login": self.rate_limit_login,
            "register": self.rate_limit_register,
            "chat": self.rate_limit_chat,
            "verify_email": self.rate_limit_verify_email,
            "resend_verification": self.rate_limit_resend_verification,
            "password_reset": self.rate_limit_password_reset,
            "change_password": self.rate_limit_change_password,
        }
        return limits.get(limit_type, "30/minute")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that secret_key is set in production."""
        if not v or v == "change-me-in-production":
            import os
            if os.getenv("DEBUG", "").lower() not in ("true", "1", "yes"):
                raise ValueError(
                    "SECRET_KEY must be set in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            # In debug mode, use a default key (not secure, but allows local dev)
            return "dev-secret-key-not-for-production"
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    def get_allowed_origins(self) -> list[str]:
        """Parse allowed_origins into a list."""
        if not self.allowed_origins:
            return []
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

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
    neo4j_password: str = Field(default="")  # Required in production

    # PostgreSQL
    database_url: str = Field(default="")  # Required in production

    # Vertex AI credentials
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"
    gcp_service_account_email: str = ""
    gcp_private_key: str = ""  # PEM format

    # LLM Models
    llm_model: str = "gemini-3.1-flash-lite-preview"  # Classifier — was gemini-2.5-flash-lite, upgraded to 3.1 for better BOTH detection
    llm_model_balanced: str = "gemini-3.1-flash-lite-preview"  # Balanced
    llm_model_pro: str = "gemini-3.1-flash-lite-preview"  # Chat responses

    # Model for Graphiti entity extraction (can be overridden via env var)
    graphiti_model: str = "gemini-3.1-flash-lite-preview"  # Entity extraction — thinking_level=MEDIUM
    # Embeddings configured in Graphiti: gemini-embedding-001 (3072 dimensions)

    # Graphiti features
    auto_update_communities: bool = True  # Patched locally: fixed semaphore_gather unpacking bug in graphiti-core 0.28.1

    # Search
    search_limit: int = 40  # Max edges/nodes returned from search
    iterative_search_max: int = 3  # Max additional search rounds (0 = single search, no iterations)
    llm_thinking_level: str = "MEDIUM"  # Thinking level for gemini-3+ models (NONE/MINIMAL/LOW/MEDIUM/HIGH)
    llm_max_output_tokens: int = 0  # Max output tokens for chat responses (0 = no limit; only useful when thinking is off)

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
    access_token_expire_minutes: int = 15  # Production: 15 min
    access_token_expire_minutes_debug: int = 120  # Debug: 2 hours for long tests
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 15
    reset_code_expire_minutes: int = 10
    reset_code_max_attempts: int = 5
    resend_email_cooldown_seconds: int = 60

    # Langfuse observability
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3001"
    app_version: str = "dev"  # Set via APP_VERSION env var in production

    # OAuth 2.0 settings (for MCP clients)
    oauth_issuer: str = ""  # Set via env var per environment
    oauth_resource_uri: str = ""  # Usually same as issuer
    oauth_authorization_code_expire_seconds: int = 600  # 10 min
    oauth_access_token_expire_seconds: int = 86400  # 24 hours
    oauth_refresh_token_expire_days: int = 30

    # Token limits for unverified users
    unverified_token_limit: int = 1_000_000  # 1M tokens

    # Social login - separate client IDs for each platform
    google_ios_client_id: str = ""      # iOS client ID
    google_android_client_id: str = ""  # Android client ID
    google_web_client_id: str = ""      # Web client ID
    apple_client_id: str = ""           # Bundle ID (com.mindnest.app.dev/staging/prod)

    def get_google_client_ids(self) -> list[str]:
        """Get all valid Google client IDs for token verification."""
        ids = []
        if self.google_ios_client_id:
            ids.append(self.google_ios_client_id)
        if self.google_android_client_id:
            ids.append(self.google_android_client_id)
        if self.google_web_client_id:
            ids.append(self.google_web_client_id)
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
                "chat": "1000/minute",  # High limit for test scenarios
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

    @field_validator("oauth_issuer")
    @classmethod
    def validate_oauth_issuer(cls, v: str) -> str:
        """Validate or set default OAuth issuer based on environment."""
        if not v:
            import os
            if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
                return "http://localhost:8000"
            # In production, leave empty - will be set via env var
            return ""
        return v

    @field_validator("oauth_resource_uri")
    @classmethod
    def validate_oauth_resource_uri(cls, v: str) -> str:
        """Validate or set default OAuth resource URI based on environment."""
        if not v:
            import os
            if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
                return "http://localhost:8000"
            return ""
        return v

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

    @field_validator("neo4j_password")
    @classmethod
    def validate_neo4j_password(cls, v: str) -> str:
        """Validate that neo4j_password is set."""
        if not v:
            import os
            if os.getenv("DEBUG", "").lower() not in ("true", "1", "yes"):
                raise ValueError("NEO4J_PASSWORD must be set in production")
            # In debug mode, use a default (for local docker-compose)
            return "mindnest123"
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that database_url is set."""
        if not v:
            import os
            if os.getenv("DEBUG", "").lower() not in ("true", "1", "yes"):
                raise ValueError("DATABASE_URL must be set in production")
            # In debug mode, use a default (for local docker-compose)
            return "postgresql+asyncpg://mindnest:mindnest@localhost:5432/mindnest"
        return v

    def get_allowed_origins(self) -> list[str]:
        """Parse allowed_origins into a list."""
        if not self.allowed_origins:
            return []
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def get_oauth_issuer(self) -> str:
        """Get OAuth issuer URL, raising error if not configured in production."""
        if self.oauth_issuer:
            return self.oauth_issuer
        if self.debug:
            return "http://localhost:8000"
        raise ValueError(
            "OAUTH_ISSUER must be set in production. "
            "Set it to your API URL (e.g., https://api.mindnest.one)"
        )

    def get_oauth_resource_uri(self) -> str:
        """Get OAuth resource URI, defaulting to issuer if not set."""
        if self.oauth_resource_uri:
            return self.oauth_resource_uri
        return self.get_oauth_issuer()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

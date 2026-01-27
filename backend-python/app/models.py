"""SQLAlchemy models for PostgreSQL."""

from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from .database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Nullable for social-only users
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Email verification
    email_verified: Mapped[bool] = mapped_column(default=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Token usage tracking (for unverified user limits)
    tokens_used: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """Project model."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """Project member model (many-to-many: users <-> projects)."""
    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )


class ChatMessage(Base):
    """Chat message history."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_reply: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)  # DATA or QUESTION
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship()
    user: Mapped["User"] = relationship()


class PasswordResetCode(Base):
    """Password reset code model (6-digit codes with SHA-256 hash)."""
    __tablename__ = "password_reset_codes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hash of 6-digit code
    attempts: Mapped[int] = mapped_column(Integer, default=0)  # Max 5 attempts
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship()


class SocialAuthProvider(Base):
    """Social auth provider model (Google, Apple Sign-In)."""
    __tablename__ = "social_auth_providers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google', 'apple'
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # May be relay email for Apple
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_social_provider_user"),
    )


# ============================================================================
# OAuth 2.0 Models (for MCP authentication)
# ============================================================================


class OAuthClient(Base):
    """OAuth 2.0 registered client.

    Stores dynamically registered OAuth clients (per RFC 7591).
    Clients can also be fetched from Client ID Metadata Documents.
    """
    __tablename__ = "oauth_clients"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    client_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # Could be URL for metadata document clients
    client_secret_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256 hash, null for public clients
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    redirect_uris: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)  # Array of allowed redirect URIs
    grant_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=["authorization_code", "refresh_token"])
    response_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=["code"])
    token_endpoint_auth_method: Mapped[str] = mapped_column(String(50), nullable=False, default="none")  # none, client_secret_basic, client_secret_post
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=True)  # True if registered via dynamic registration
    metadata_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL to Client ID Metadata Document
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class OAuthAuthorizationCode(Base):
    """OAuth 2.0 authorization code.

    Short-lived code used to exchange for tokens.
    Includes PKCE challenge for security.
    """
    __tablename__ = "oauth_authorization_codes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 hash of code
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, default="read")
    code_challenge: Mapped[str] = mapped_column(String(128), nullable=False)  # PKCE code_challenge
    code_challenge_method: Mapped[str] = mapped_column(String(10), nullable=False, default="S256")  # Only S256 supported
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Client state for CSRF protection
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # Set when code is exchanged

    # Relationships
    user: Mapped["User"] = relationship()


class OAuthRefreshToken(Base):
    """OAuth 2.0 refresh token with rotation support.

    Refresh tokens are rotated on each use to detect replay attacks.
    family_id groups tokens from the same authorization.
    """
    __tablename__ = "oauth_refresh_tokens"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 hash
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, default="read")
    family_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)  # Groups related tokens for rotation
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # Set when revoked or rotated

    # Relationships
    user: Mapped["User"] = relationship()


class OAuthConsent(Base):
    """Stored user consent for OAuth client.

    Allows skipping consent screen if user has already approved the client.
    """
    __tablename__ = "oauth_consents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False)  # Consented scopes
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "client_id", name="uq_oauth_consent_user_client"),
    )


# ============================================================================
# MCP Logging
# ============================================================================


class McpLog(Base):
    """MCP action log.

    Logs MCP tool invocations for auditing and analytics.
    Note: Message/query content is NOT stored, only metadata like lengths.
    """
    __tablename__ = "mcp_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    oauth_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # list_projects, search_knowledge, send_message
    project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    request_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Metadata only, no content
    response_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user: Mapped["User"] = relationship()

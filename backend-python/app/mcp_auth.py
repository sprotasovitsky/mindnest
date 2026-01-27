"""MCP Authentication.

Provides dependencies for validating OAuth tokens used by MCP clients.
Only OAuth 2.0 authentication is supported (no API keys).
"""

import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import User
from .oauth_service import get_user_from_oauth_token

logger = logging.getLogger(__name__)


class McpAuth:
    """Container for authenticated MCP user and OAuth credentials."""

    def __init__(
        self,
        user: User,
        oauth_client_id: str,
        oauth_scope: str,
    ):
        self.user = user
        self.oauth_client_id = oauth_client_id
        self.oauth_scope = oauth_scope

    @property
    def is_oauth_auth(self) -> bool:
        """Check if authenticated via OAuth (always True for MCP)."""
        return True


def get_www_authenticate_header() -> str:
    """Get WWW-Authenticate header value for 401 responses.

    Per RFC 9728, includes resource_metadata URL for OAuth discovery.
    """
    settings = get_settings()
    try:
        resource = settings.get_oauth_resource_uri()
        # RFC 9728: resource_metadata points to Protected Resource Metadata
        return f'Bearer resource_metadata="{resource}/.well-known/oauth-protected-resource"'
    except ValueError:
        return "Bearer"


async def _validate_oauth_token(
    token: str,
    db: AsyncSession,
) -> Optional[McpAuth]:
    """Validate OAuth Bearer token and return auth info.

    Args:
        token: The Bearer token value
        db: Database session

    Returns:
        McpAuth if valid, None otherwise
    """
    user, payload = await get_user_from_oauth_token(db, token)

    if not user or not payload:
        return None

    client_id = payload.get("client_id", "unknown")
    scope = payload.get("scope", "read")

    logger.info(f"OAuth authenticated: user {user.id} via client {client_id}")

    return McpAuth(
        user=user,
        oauth_client_id=client_id,
        oauth_scope=scope,
    )


async def get_mcp_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> McpAuth:
    """Validate MCP authentication via OAuth Bearer token.

    This is a FastAPI dependency for MCP operations.
    Only OAuth 2.0 authentication is supported.

    Args:
        request: FastAPI request
        authorization: Bearer token from Authorization header
        db: Database session

    Returns:
        McpAuth containing user and OAuth info

    Raises:
        HTTPException: If authentication fails (401 with OAuth discovery info)
    """
    # Try OAuth Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        auth = await _validate_oauth_token(token, db)
        if auth:
            return auth

    # No valid authentication found - return 401 with OAuth discovery
    www_authenticate = get_www_authenticate_header()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="OAuth authentication required",
        headers={"WWW-Authenticate": www_authenticate},
    )


def _get_insufficient_scope_header(required_scope: str) -> str:
    """Get WWW-Authenticate header for insufficient scope (403).

    Per RFC 6750, includes the required scope for step-up authorization.
    """
    settings = get_settings()
    try:
        resource = settings.get_oauth_resource_uri()
        return (
            f'Bearer error="insufficient_scope", '
            f'scope="{required_scope}", '
            f'resource="{resource}", '
            f'resource_metadata="{resource}/.well-known/oauth-protected-resource"'
        )
    except ValueError:
        return f'Bearer error="insufficient_scope", scope="{required_scope}"'


async def get_mcp_auth_read(
    auth: McpAuth = Depends(get_mcp_auth),
) -> McpAuth:
    """Validate MCP authentication and require read scope.

    This is a FastAPI dependency for read-only MCP operations.

    Args:
        auth: McpAuth from get_mcp_auth

    Returns:
        McpAuth containing user and OAuth info

    Raises:
        HTTPException: If authentication fails or lacks read scope
    """
    scope = auth.oauth_scope or ""
    if "read" in scope.split():
        return auth

    # Return 403 with scope info for step-up authorization
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Read scope required",
        headers={"WWW-Authenticate": _get_insufficient_scope_header("read")},
    )


async def get_mcp_auth_write(
    auth: McpAuth = Depends(get_mcp_auth),
) -> McpAuth:
    """Validate MCP authentication and require write scope.

    This is a FastAPI dependency for write MCP operations.

    Args:
        auth: McpAuth from get_mcp_auth

    Returns:
        McpAuth containing user and OAuth info

    Raises:
        HTTPException: If authentication fails or lacks write scope
    """
    scope = auth.oauth_scope or ""
    if "write" in scope.split():
        return auth

    # Return 403 with scope info for step-up authorization
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Write scope required",
        headers={"WWW-Authenticate": _get_insufficient_scope_header("read write")},
    )

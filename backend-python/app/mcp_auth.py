"""MCP Authentication.

Provides dependencies for validating API keys used by MCP clients.
"""

import logging
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import ApiKey, User
from .routers.api_keys import hash_api_key

logger = logging.getLogger(__name__)


class ApiKeyAuth:
    """Container for authenticated API key and user."""

    def __init__(self, user: User, api_key: ApiKey):
        self.user = user
        self.api_key = api_key


async def get_user_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyAuth:
    """Validate API key and return user.

    This is a FastAPI dependency for read-only MCP operations.
    Requires an API key with at least 'read' scope.

    Args:
        x_api_key: API key from X-API-Key header
        db: Database session

    Returns:
        ApiKeyAuth containing user and api_key

    Raises:
        HTTPException: If API key is invalid, expired, or revoked
    """
    # Hash the provided key
    key_hash = hash_api_key(x_api_key)

    # Find the API key
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        logger.warning(f"Invalid API key attempted: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check if revoked
    if api_key.revoked_at is not None:
        logger.warning(f"Revoked API key attempted: {api_key.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
        )

    # Check if expired
    now = datetime.now(timezone.utc)
    if api_key.expires_at is not None and api_key.expires_at < now:
        logger.warning(f"Expired API key attempted: {api_key.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == api_key.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        logger.error(f"API key {api_key.id} has no associated user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Update last_used_at
    api_key.last_used_at = now
    await db.commit()

    logger.info(f"API key authenticated: {api_key.id} for user {user.id}")

    return ApiKeyAuth(user=user, api_key=api_key)


async def get_user_from_api_key_write(
    auth: ApiKeyAuth = Depends(get_user_from_api_key),
) -> ApiKeyAuth:
    """Validate API key and require write scope.

    This is a FastAPI dependency for write MCP operations.
    Requires an API key with 'write' in scopes.

    Args:
        auth: ApiKeyAuth from get_user_from_api_key

    Returns:
        ApiKeyAuth containing user and api_key

    Raises:
        HTTPException: If API key doesn't have write scope
    """
    if "write" not in auth.api_key.scopes:
        logger.warning(
            f"Write operation attempted with read-only key: {auth.api_key.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not have write permission",
        )

    return auth

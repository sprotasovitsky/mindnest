"""API Keys Router.

Handles creation, listing, and revocation of API keys for MCP access.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models import ApiKey
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateApiKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: str = Field(default="read", pattern="^(read|read,write)$")


class CreateApiKeyResponse(BaseModel):
    """Response with the full API key (shown only once)."""
    id: str
    name: str
    key: str  # Full key - shown only once
    key_prefix: str
    scopes: str
    created_at: datetime


class ApiKeyResponse(BaseModel):
    """API key info (without the actual key)."""
    id: str
    name: str
    key_prefix: str
    scopes: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyListResponse(BaseModel):
    """List of API keys."""
    keys: list[ApiKeyResponse]


# ============================================================================
# Helper Functions
# ============================================================================

KEY_PREFIX = "mn_live_"


def generate_api_key() -> str:
    """Generate a new API key.

    Format: mn_live_ + 32 hex chars = 40 chars total
    """
    return KEY_PREFIX + secrets.token_hex(16)


def hash_api_key(key: str) -> str:
    """Hash API key with SHA-256.

    Uses the secret_key as additional salt for security.
    """
    settings = get_settings()
    salted = f"{settings.secret_key}:{key}"
    return hashlib.sha256(salted.encode()).hexdigest()


def get_key_prefix(key: str) -> str:
    """Get the prefix of an API key for identification."""
    return key[:8]  # "mn_live_"


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=CreateApiKeyResponse)
async def create_api_key(
    request: Request,
    data: CreateApiKeyRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateApiKeyResponse:
    """Create a new API key.

    The full key is returned only once in this response.
    Store it securely - it cannot be retrieved again.
    """
    # Generate new key
    full_key = generate_api_key()
    key_hash = hash_api_key(full_key)
    key_prefix = get_key_prefix(full_key)

    # Create API key record
    api_key = ApiKey(
        user_id=user.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        name=data.name.strip(),
        scopes=data.scopes,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"API key created: {api_key.id} for user {user.id}")

    return CreateApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,  # Full key - shown only once
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
    )


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyListResponse:
    """List all API keys for the current user.

    Does not return the actual keys, only metadata.
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user.id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return ApiKeyListResponse(
        keys=[
            ApiKeyResponse(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                scopes=k.scopes,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
            )
            for k in keys
        ]
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke an API key.

    The key will no longer be usable for authentication.
    """
    # Find the key
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == user.id,
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Revoke the key
    api_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"API key revoked: {key_id} by user {user.id}")

    return {"message": "API key revoked"}

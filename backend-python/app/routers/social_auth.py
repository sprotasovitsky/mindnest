"""Social Authentication API Router.

Handles Google and Apple Sign-In authentication.
Social login users get email_verified=true immediately.
"""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..database import get_db
from ..models import User, SocialAuthProvider
from .auth import (
    AuthResponse,
    create_access_token,
    create_refresh_token,
    get_user_by_email,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["social-auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def _get_social_auth_limit() -> str:
    """Get social auth rate limit based on debug mode."""
    settings = get_settings()
    if settings.debug:
        return "100/minute"
    return "10/minute"


class SocialLoginRequest(BaseModel):
    """Social login request."""
    provider: str = Field(..., pattern="^(google|apple)$")
    id_token: str
    name: Optional[str] = None  # Name from social provider
    is_access_token: bool = False  # True if token is access_token (web)


class SocialLoginResponse(AuthResponse):
    """Social login response (same as AuthResponse)."""
    pass


async def verify_google_token(id_token: str) -> Optional[dict]:
    """Verify Google ID token and return user info.

    Checks token audience against configured iOS and Android client IDs.
    Returns dict with: sub (user_id), email, name, email_verified
    """
    settings = get_settings()
    valid_client_ids = settings.get_google_client_ids()
    if not valid_client_ids:
        logger.error("Google client IDs not configured (GOOGLE_IOS_CLIENT_ID, GOOGLE_ANDROID_CLIENT_ID)")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )

            if response.status_code != 200:
                logger.warning(f"Google token verification failed: {response.text}")
                return None

            data = response.json()

            # Verify audience matches one of our client IDs (iOS or Android)
            if data.get("aud") not in valid_client_ids:
                logger.warning(
                    f"Google token audience mismatch: expected one of {valid_client_ids}, "
                    f"got {data.get('aud')}"
                )
                return None

            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name"),
                "email_verified": data.get("email_verified") == "true",
            }
    except Exception as e:
        logger.error(f"Google token verification error: {e}")
        return None


async def verify_google_access_token(access_token: str) -> Optional[dict]:
    """Verify Google access token using userinfo endpoint (for web).

    Web clients may only get access_token, not id_token.
    Returns dict with: sub (user_id), email, name, email_verified
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                logger.warning(f"Google access token verification failed: {response.text}")
                return None

            data = response.json()

            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name"),
                "email_verified": data.get("email_verified", False),
            }
    except Exception as e:
        logger.error(f"Google access token verification error: {e}")
        return None


async def verify_apple_token(id_token: str) -> Optional[dict]:
    """Verify Apple ID token and return user info.

    Apple uses JWT tokens that need to be verified against Apple's public keys.
    Returns dict with: sub (user_id), email
    """
    import jwt
    from jwt import PyJWKClient

    settings = get_settings()
    valid_client_ids = settings.get_apple_client_ids()
    if not valid_client_ids:
        logger.error("Apple client IDs not configured")
        return None

    try:
        # Apple's JWKS endpoint
        jwks_client = PyJWKClient("https://appleid.apple.com/auth/keys")
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        # Try each valid audience (bundle ID)
        data = None
        for client_id in valid_client_ids:
            try:
                data = jwt.decode(
                    id_token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience=client_id,
                    issuer="https://appleid.apple.com",
                )
                break  # Found valid audience
            except jwt.InvalidAudienceError:
                continue

        if not data:
            logger.warning("Apple token audience mismatch")
            return None

        return {
            "sub": data.get("sub"),
            "email": data.get("email"),  # May be relay email
            "name": None,  # Apple doesn't return name in token
            "email_verified": True,  # Apple always verifies email
        }
    except Exception as e:
        logger.error(f"Apple token verification error: {e}")
        return None


async def get_or_create_social_user(
    db: AsyncSession,
    provider: str,
    provider_user_id: str,
    email: Optional[str],
    name: Optional[str],
) -> User:
    """Get existing user by social provider or create new one.

    If user exists with same email but different provider, link the provider.
    """
    # Check if social provider already linked
    result = await db.execute(
        select(SocialAuthProvider).where(
            SocialAuthProvider.provider == provider,
            SocialAuthProvider.provider_user_id == provider_user_id,
        )
    )
    social_auth = result.scalar_one_or_none()

    if social_auth:
        # Return existing user
        result = await db.execute(
            select(User).where(User.id == social_auth.user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return user

    # Check if user exists with same email
    user = None
    if email:
        user = await get_user_by_email(db, email)

    if not user:
        # Create new user (social-only, no password)
        user = User(
            email=email.lower() if email else f"{provider}_{provider_user_id}@social.local",
            password_hash=None,  # No password for social users
            name=name or "User",
            email_verified=True,  # Social login = verified
        )
        db.add(user)
        await db.flush()  # Get user.id

    # Link social provider to user
    social_auth = SocialAuthProvider(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
    )
    db.add(social_auth)

    # Mark user as verified (social login = trusted email)
    user.email_verified = True

    await db.commit()
    await db.refresh(user)

    return user


@router.post("/social", response_model=SocialLoginResponse)
@limiter.limit(_get_social_auth_limit)
async def social_login(
    request: Request,
    data: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> SocialLoginResponse:
    """Authenticate using Google or Apple Sign-In.

    - Verifies the ID token with the provider
    - Creates a new user or links to existing user
    - Social login users are automatically email_verified=true
    """
    logger.info(f"Social login attempt: {data.provider}, is_access_token={data.is_access_token}")

    # Verify token with provider
    if data.provider == "google":
        if data.is_access_token:
            # Web clients may only have access_token
            user_info = await verify_google_access_token(data.id_token)
        else:
            user_info = await verify_google_token(data.id_token)
    elif data.provider == "apple":
        user_info = await verify_apple_token(data.id_token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    if not user_info or not user_info.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Get or create user
    user = await get_or_create_social_user(
        db=db,
        provider=data.provider,
        provider_user_id=user_info["sub"],
        email=user_info.get("email"),
        name=data.name or user_info.get("name"),
    )

    # Create tokens with login_method for account deletion logic
    access_token, expires_in = create_access_token(
        user.id, user.email, user.name, login_method=data.provider
    )
    refresh_token = create_refresh_token(user.id, login_method=data.provider)

    logger.info(f"Social login successful for user: {user.id}")

    return SocialLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user_id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
    )

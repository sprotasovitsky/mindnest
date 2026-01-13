"""Authentication API Router.

Handles user registration, login, and token refresh.
Uses PostgreSQL for user storage and bcrypt for password hashing.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..database import get_db
from ..models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limiter - will be configured from app state
limiter = Limiter(key_func=get_remote_address)


def mask_email(email: str) -> str:
    """Mask email for logging (GDPR compliance)."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


class PasswordValidator:
    """Password validation rules."""

    MIN_LENGTH = 8
    REQUIRE_DIGIT = True
    REQUIRE_LETTER = True

    @classmethod
    def validate(cls, password: str) -> tuple[bool, str]:
        """Validate password and return (is_valid, error_message)."""
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"
        if cls.REQUIRE_DIGIT and not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if cls.REQUIRE_LETTER and not re.search(r"[a-zA-Z]", password):
            return False, "Password must contain at least one letter"
        return True, ""


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error)
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    user_id: str
    email: str
    name: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User info response."""
    id: str
    email: str
    name: str


# Token configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, email: str, name: str) -> tuple[str, int]:
    """Create JWT access token. Returns (token, expires_in_seconds)."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    # Handle legacy SHA-256 hashes (salt:hash format)
    if ":" in hashed_password and len(hashed_password) < 100:
        # Legacy format - users need to re-register or use password reset
        logger.warning("Legacy password hash detected, migration needed")
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/register", response_model=AuthResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user."""
    logger.info(f"Registering user: {mask_email(data.email)}")

    # Check if user exists
    existing_user = await get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user with bcrypt hash
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create tokens
    access_token, expires_in = create_access_token(user.id, user.email, user.name)
    refresh_token = create_refresh_token(user.id)

    logger.info(f"User registered: {user.id}")

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login user."""
    logger.info(f"Login attempt: {mask_email(data.email)}")

    # Get user
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create tokens
    access_token, expires_in = create_access_token(user.id, user.email, user.name)
    refresh_token = create_refresh_token(user.id)

    logger.info(f"User logged in: {user.id}")

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """Refresh access token using refresh token."""
    settings = get_settings()

    try:
        payload = jwt.decode(data.refresh_token, settings.secret_key, algorithms=["HS256"])

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Get user to ensure they still exist
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Create new access token
        access_token, expires_in = create_access_token(user.id, user.email, user.name)

        logger.info(f"Token refreshed for user: {user.id}")

        return RefreshResponse(
            access_token=access_token,
            expires_in=expires_in,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except jwt.JWTError as e:
        logger.warning(f"Invalid refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


async def get_user_from_token_db(db: AsyncSession, token: str) -> Optional[User]:
    """Extract user from JWT token (with database lookup)."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Only accept access tokens
        if payload.get("type") not in ("access", None):  # None for backward compat
            return None

        user_id = payload.get("sub")
        if user_id:
            return await get_user_by_id(db, user_id)
    except Exception as e:
        logger.warning(f"Invalid token: {e}")
    return None


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return payload."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Only accept access tokens
        if payload.get("type") not in ("access", None):  # None for backward compat
            return None

        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
        }
    except Exception as e:
        logger.warning(f"Invalid token: {e}")
    return None

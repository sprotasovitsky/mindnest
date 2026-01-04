"""Authentication API Router.

Handles user registration and login.
Uses PostgreSQL for user storage.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from ..config import get_settings
from ..database import get_db
from ..models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=4)
    name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response with token."""
    token: str
    user_id: str
    email: str
    name: str


class UserResponse(BaseModel):
    """User info response."""
    id: str
    email: str
    name: str


def create_token(user_id: str, email: str) -> str:
    """Create JWT token for user."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    # Format: salt:hash
    if ":" not in hashed_password:
        return False
    salt, stored_hash = hashed_password.split(":", 1)
    computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)


def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"


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
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user."""
    logger.info(f"Registering user: {request.email}")

    # Check if user exists
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        name=request.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create token
    token = create_token(user.id, user.email)

    logger.info(f"User registered: {user.id}")

    return AuthResponse(
        token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login user."""
    logger.info(f"Login attempt: {request.email}")

    # Get user
    user = await get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create token
    token = create_token(user.id, user.email)

    logger.info(f"User logged in: {user.id}")

    return AuthResponse(
        token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


async def get_user_from_token_db(db: AsyncSession, token: str) -> Optional[User]:
    """Extract user from JWT token (with database lookup)."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
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
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
        }
    except Exception as e:
        logger.warning(f"Invalid token: {e}")
    return None

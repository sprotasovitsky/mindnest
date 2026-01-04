"""Authentication API Router.

Handles user registration and login.
Uses PostgreSQL for user storage.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from jose import jwt

from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory user storage (for MVP - replace with PostgreSQL later)
# Structure: {email: {id, email, name, password_hash}}
_users_db: dict[str, dict] = {}


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


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    return _users_db.get(email.lower())


def create_user(email: str, password: str, name: str) -> dict:
    """Create new user."""
    user_id = str(uuid4())
    user = {
        "id": user_id,
        "email": email.lower(),
        "name": name,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow().isoformat(),
    }
    _users_db[email.lower()] = user
    return user


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest) -> AuthResponse:
    """Register a new user."""
    logger.info(f"Registering user: {request.email}")

    # Check if user exists
    if get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = create_user(request.email, request.password, request.name)

    # Create token
    token = create_token(user["id"], user["email"])

    logger.info(f"User registered: {user['id']}")

    return AuthResponse(
        token=token,
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    """Login user."""
    logger.info(f"Login attempt: {request.email}")

    # Get user
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create token
    token = create_token(user["id"], user["email"])

    logger.info(f"User logged in: {user['id']}")

    return AuthResponse(
        token=token,
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
    )


def get_user_from_token(token: str) -> Optional[dict]:
    """Extract user from JWT token."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("email")
        if email:
            return get_user_by_email(email)
    except Exception as e:
        logger.warning(f"Invalid token: {e}")
    return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token."""
    user = get_user_from_token(token)
    return user["id"] if user else None

"""Authentication API Router.

Handles user registration, login, token refresh, and email verification.
Uses PostgreSQL for user storage and bcrypt for password hashing.
"""

import hashlib
import logging
import random
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..database import get_db
from ..models import User, PasswordResetCode
from ..email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limiter - will be configured from app state
limiter = Limiter(key_func=get_remote_address)


def _get_register_limit() -> str:
    """Get register rate limit based on debug mode."""
    return get_settings().get_rate_limit("register")


def _get_login_limit() -> str:
    """Get login rate limit based on debug mode."""
    return get_settings().get_rate_limit("login")


def _get_verify_email_limit() -> str:
    """Get verify email rate limit based on debug mode."""
    return get_settings().get_rate_limit("verify_email")


def _get_resend_verification_limit() -> str:
    """Get resend verification rate limit based on debug mode."""
    return get_settings().get_rate_limit("resend_verification")


def _get_password_reset_limit() -> str:
    """Get password reset rate limit based on debug mode."""
    return get_settings().get_rate_limit("password_reset")


def _get_change_password_limit() -> str:
    """Get change password rate limit based on debug mode."""
    return get_settings().get_rate_limit("change_password")


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
    email_verified: bool = False


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


class UserInfoResponse(BaseModel):
    """User info with verification status and token usage."""
    id: str
    email: str
    name: str
    email_verified: bool
    tokens_used: int
    token_limit: int  # 0 if verified (unlimited)


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str = Field(..., min_length=32, max_length=64)


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Password reset request (step 1: request code)."""
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Verify reset code request (step 2: verify code)."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class VerifyResetCodeResponse(BaseModel):
    """Verify reset code response."""
    reset_token: str  # Temporary token for password reset


class ResetPasswordRequest(BaseModel):
    """Reset password request (step 3: set new password)."""
    reset_token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error)
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request (for authenticated users)."""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error)
        return v


def create_access_token(user_id: str, email: str, name: str) -> tuple[str, int]:
    """Create JWT access token. Returns (token, expires_in_seconds)."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token, settings.access_token_expire_minutes * 60


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
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
@limiter.limit(_get_register_limit)
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

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    # Create user with bcrypt hash
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        name=data.name,
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_sent_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send verification email (fire and forget, don't block registration)
    await EmailService.send_verification_email(user.email, user.name, verification_token)

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
        email_verified=user.email_verified,
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(_get_login_limit)
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

    # Verify password (social-only users have no password)
    if not user.password_hash or not verify_password(data.password, user.password_hash):
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
        email_verified=user.email_verified,
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


@router.post("/verify-email")
@limiter.limit(_get_verify_email_limit)
async def verify_email(
    request: Request,
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify email with token."""
    # Find user by verification token
    result = await db.execute(
        select(User).where(User.email_verification_token == data.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Check if already verified
    if user.email_verified:
        return {"message": "Email already verified"}

    # Verify the email
    user.email_verified = True
    user.email_verification_token = None
    await db.commit()

    logger.info(f"Email verified for user: {user.id}")
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
@limiter.limit(_get_resend_verification_limit)
async def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resend verification email."""
    user = await get_user_by_email(db, data.email)

    # Always return success to prevent email enumeration
    if not user or user.email_verified:
        return {"message": "If the email exists, a verification link will be sent"}

    # Rate limit: don't send if sent recently
    settings = get_settings()
    if user.email_verification_sent_at:
        elapsed = (datetime.utcnow() - user.email_verification_sent_at).total_seconds()
        if elapsed < settings.resend_email_cooldown_seconds:
            return {"message": "If the email exists, a verification link will be sent"}

    # Generate new token
    token = secrets.token_urlsafe(32)
    user.email_verification_token = token
    user.email_verification_sent_at = datetime.utcnow()
    await db.commit()

    # Send email
    await EmailService.send_verification_email(user.email, user.name, token)

    return {"message": "If the email exists, a verification link will be sent"}


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserInfoResponse:
    """Get current user info including verification status."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.split(" ", 1)[1]
    user = await get_user_from_token_db(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    settings = get_settings()
    return UserInfoResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        tokens_used=user.tokens_used,
        token_limit=0 if user.email_verified else settings.unverified_token_limit,
    )


def generate_reset_code() -> str:
    """Generate a 6-digit numeric code."""
    return f"{random.randint(0, 999999):06d}"


def hash_code(code: str) -> str:
    """Hash code with SHA-256."""
    return hashlib.sha256(code.encode()).hexdigest()


def create_reset_token(user_id: str) -> str:
    """Create a short-lived token for password reset."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.reset_token_expire_minutes)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "password_reset",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_reset_token(token: str) -> Optional[str]:
    """Verify reset token and return user_id if valid."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


@router.post("/request-password-reset")
@limiter.limit(_get_password_reset_limit)
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request password reset code (step 1)."""
    logger.info(f"Password reset requested for: {mask_email(data.email)}")

    # Always return success to prevent email enumeration
    user = await get_user_by_email(db, data.email)
    if not user:
        return {"message": "If the email exists, a reset code will be sent"}

    # Check if user has a password (social-only users can't reset)
    if not user.password_hash:
        logger.info(f"Password reset requested for social-only user: {user.id}")
        return {"message": "If the email exists, a reset code will be sent"}

    # Rate limit: max 3 codes per hour per email
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_codes = await db.execute(
        select(PasswordResetCode).where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.created_at > one_hour_ago,
        )
    )
    if len(recent_codes.scalars().all()) >= 3:
        logger.warning(f"Too many password reset requests for user: {user.id}")
        return {"message": "If the email exists, a reset code will be sent"}

    # Generate and hash code
    code = generate_reset_code()
    code_hash = hash_code(code)

    # Create reset code record
    settings = get_settings()
    reset_code = PasswordResetCode(
        user_id=user.id,
        code_hash=code_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.reset_code_expire_minutes),
    )
    db.add(reset_code)
    await db.commit()

    # Send email with code
    await EmailService.send_password_reset_code(user.email, user.name, code)

    logger.info(f"Password reset code sent to user: {user.id}")
    return {"message": "If the email exists, a reset code will be sent"}


@router.post("/verify-reset-code", response_model=VerifyResetCodeResponse)
@limiter.limit(_get_password_reset_limit)
async def verify_reset_code(
    request: Request,
    data: VerifyResetCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyResetCodeResponse:
    """Verify reset code (step 2)."""
    logger.info(f"Verifying reset code for: {mask_email(data.email)}")

    # Get user
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or code",
        )

    # Find valid reset code for this user
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PasswordResetCode).where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.expires_at > now,
            PasswordResetCode.used_at.is_(None),
        ).order_by(PasswordResetCode.created_at.desc())
    )
    reset_codes = result.scalars().all()

    # Check code against all valid codes
    settings = get_settings()
    code_hash = hash_code(data.code)
    valid_code = None
    for rc in reset_codes:
        # Increment attempts
        rc.attempts += 1

        if rc.attempts > settings.reset_code_max_attempts:
            continue  # Too many attempts on this code

        if rc.code_hash == code_hash:
            valid_code = rc
            break

    await db.commit()

    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )

    # Mark code as used
    valid_code.used_at = now
    await db.commit()

    # Create reset token
    reset_token = create_reset_token(user.id)

    logger.info(f"Reset code verified for user: {user.id}")
    return VerifyResetCodeResponse(reset_token=reset_token)


@router.post("/reset-password")
@limiter.limit(_get_password_reset_limit)
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset password with token (step 3)."""
    # Verify reset token
    user_id = verify_reset_token(data.reset_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user.password_hash = hash_password(data.new_password)
    await db.commit()

    logger.info(f"Password reset for user: {user.id}")
    return {"message": "Password reset successfully"}


@router.post("/change-password")
@limiter.limit(_get_change_password_limit)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change password for authenticated user."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.split(" ", 1)[1]
    user = await get_user_from_token_db(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Check if user has a password (social-only users can't change password)
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for social login accounts",
        )

    # Verify current password
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check new password is different
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    user.password_hash = hash_password(data.new_password)
    await db.commit()

    logger.info(f"Password changed for user: {user.id}")
    return {"message": "Password changed successfully"}


# ============================================================================
# Account Deletion
# ============================================================================


class DeleteAccountRequest(BaseModel):
    """Request schema for account deletion."""

    password: str | None = None  # Required only for users with password


@router.delete("/account")
@limiter.limit(_get_change_password_limit)
async def delete_account(
    request: Request,
    data: DeleteAccountRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete user account and all associated data.

    - For users with password: requires password confirmation
    - For social-only users: no password required
    - Deletes: User, SocialAuthProvider, ChatMessages, ProjectMembers
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.split(" ", 1)[1]
    user = await get_user_from_token_db(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # If user has password, require password confirmation
    if user.password_hash:
        if not data or not data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required to delete account",
            )
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )

    # Delete associated data in a single transaction
    user_id = user.id

    # 1. Find projects where user is the only member (to be deleted)
    # Must do this BEFORE deleting memberships
    result = await db.execute(
        select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id, ProjectMember.role == "owner"
        )
    )
    owned_project_ids = [row[0] for row in result.fetchall()]

    # Find projects with no other members (only current user)
    projects_to_delete = []
    for project_id in owned_project_ids:
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id != user_id,
            )
        )
        other_members = result.scalars().all()
        if not other_members:
            projects_to_delete.append(project_id)

    # 2. Delete social auth providers
    from .social_auth import SocialAuthProvider
    await db.execute(
        delete(SocialAuthProvider).where(SocialAuthProvider.user_id == user_id)
    )

    # 3. Delete chat messages
    await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))

    # 4. Delete project memberships
    await db.execute(delete(ProjectMember).where(ProjectMember.user_id == user_id))

    # 5. Delete orphaned projects (only had this user as member)
    if projects_to_delete:
        await db.execute(delete(Project).where(Project.id.in_(projects_to_delete)))

    # 6. Finally, delete the user
    await db.execute(delete(User).where(User.id == user_id))

    # Commit all changes atomically
    await db.commit()

    logger.info(f"Account deleted: {user_id}")
    return {"message": "Account deleted successfully"}

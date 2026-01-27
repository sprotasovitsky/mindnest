"""OAuth 2.0 Router.

Implements OAuth 2.0 Authorization Code flow with PKCE for MCP clients.
Based on RFC 6749, RFC 7636 (PKCE), RFC 7591 (Dynamic Client Registration).
"""

import logging
from datetime import datetime, timedelta, timezone
from html import escape as html_escape
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models import (
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthConsent,
    OAuthRefreshToken,
    User,
)
from ..oauth_service import (
    create_oauth_access_token,
    create_oauth_refresh_token,
    generate_token,
    get_or_create_client,
    hash_token,
    parse_scope,
    revoke_token_family,
    revoke_tokens_for_client,
    validate_pkce_challenge,
    validate_redirect_uri,
    validate_scope,
)
from .auth import create_access_token, get_user_from_token_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth", tags=["oauth"])


# ============================================================================
# Request/Response Models
# ============================================================================


class TokenRequest(BaseModel):
    """Token endpoint request."""

    grant_type: str = Field(..., description="authorization_code or refresh_token")
    code: Optional[str] = Field(None, description="Authorization code (for authorization_code grant)")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI (for authorization_code grant)")
    client_id: Optional[str] = Field(None, description="Client ID")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier")
    refresh_token: Optional[str] = Field(None, description="Refresh token (for refresh_token grant)")
    scope: Optional[str] = Field(None, description="Requested scope (for refresh_token grant)")


class TokenResponse(BaseModel):
    """Token endpoint response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str


class ClientRegistrationRequest(BaseModel):
    """Dynamic client registration request (RFC 7591)."""

    redirect_uris: list[str] = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1, max_length=255)
    grant_types: Optional[list[str]] = Field(default=["authorization_code", "refresh_token"])
    response_types: Optional[list[str]] = Field(default=["code"])
    token_endpoint_auth_method: Optional[str] = Field(default="none")


class ClientRegistrationResponse(BaseModel):
    """Dynamic client registration response."""

    client_id: str
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    token_endpoint_auth_method: str


class RevokeRequest(BaseModel):
    """Token revocation request (RFC 7009)."""

    token: str
    token_type_hint: Optional[str] = Field(None, description="access_token or refresh_token")


# ============================================================================
# Authorization Endpoint
# ============================================================================


@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(..., description="Client ID"),
    redirect_uri: str = Query(..., description="Redirect URI"),
    scope: str = Query("read", description="Requested scope"),
    state: Optional[str] = Query(None, description="Client state for CSRF"),
    code_challenge: str = Query(..., description="PKCE code challenge"),
    code_challenge_method: str = Query("S256", description="PKCE method (must be S256)"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """OAuth 2.0 authorization endpoint.

    Shows login page if not authenticated, then consent page.
    """
    # SECURITY FIX: Validate client and redirect_uri FIRST before any error redirects
    # Per RFC 6749 Section 4.1.2.1: redirect_uri must be validated before redirecting
    client = await get_or_create_client(db, client_id, redirect_uri)
    if not client:
        # Don't redirect to unvalidated URI - show error page
        return HTMLResponse(
            content=_error_page("Unknown or invalid client"),
            status_code=400,
        )

    # Validate redirect_uri against client's registered URIs
    if not validate_redirect_uri(client, redirect_uri):
        # Don't redirect to invalid URI - show error page
        return HTMLResponse(
            content=_error_page("Invalid redirect_uri"),
            status_code=400,
        )

    # Now that redirect_uri is validated, we can safely redirect errors to it

    # Validate response_type
    if response_type != "code":
        return _error_response(
            redirect_uri,
            "unsupported_response_type",
            "Only 'code' response_type is supported",
            state,
        )

    # Validate PKCE method
    if code_challenge_method != "S256":
        return _error_response(
            redirect_uri,
            "invalid_request",
            "Only S256 code_challenge_method is supported",
            state,
        )

    # Validate scope
    is_valid, granted_scope = validate_scope(scope)
    if not is_valid:
        return _error_response(
            redirect_uri,
            "invalid_scope",
            "Invalid scope requested",
            state,
        )

    # Check if user is authenticated
    auth_header = request.headers.get("Authorization", "")
    auth_cookie = request.cookies.get("auth_token", "")

    user = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user = await get_user_from_token_db(db, token)
    elif auth_cookie:
        user = await get_user_from_token_db(db, auth_cookie)

    if not user:
        # Show login page
        return HTMLResponse(
            content=_login_page(
                client_id=client_id,
                client_name=client.client_name,
                redirect_uri=redirect_uri,
                scope=granted_scope,
                state=state,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
            ),
            status_code=200,
        )

    # Check if user has already consented
    consent = await _get_consent(db, user.id, client_id, granted_scope)
    if consent:
        # User already consented - generate code and redirect
        code = await _create_authorization_code(
            db=db,
            client_id=client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            scope=granted_scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            state=state,
        )
        return _redirect_with_code(redirect_uri, code, state)

    # Show consent page
    return HTMLResponse(
        content=_consent_page(
            client_name=client.client_name,
            scope=granted_scope,
            user_name=user.name,
            user_email=user.email,
            # Pass authorization params to form
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        ),
        status_code=200,
    )


@router.post("/authorize/login")
async def authorize_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("read"),
    state: Optional[str] = Form(None),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Handle login form submission during OAuth flow."""
    from .auth import get_user_by_email, verify_password

    # Validate user credentials
    user = await get_user_by_email(db, email)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        # Show login page with error
        client = await get_or_create_client(db, client_id, redirect_uri)
        client_name = client.client_name if client else "Unknown Client"
        return HTMLResponse(
            content=_login_page(
                client_id=client_id,
                client_name=client_name,
                redirect_uri=redirect_uri,
                scope=scope,
                state=state,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                error="Invalid email or password",
            ),
            status_code=200,
        )

    # Get client for consent page
    client = await get_or_create_client(db, client_id, redirect_uri)
    if not client:
        return HTMLResponse(content=_error_page("Unknown client"), status_code=400)

    # SECURITY: Create a session token for the authenticated user
    # This token will be validated in /authorize/decision to prevent bypass attacks
    session_token = create_access_token(user_id=str(user.id))

    # Check if user has already consented
    consent = await _get_consent(db, user.id, client_id, scope)
    if consent:
        # Generate code and redirect
        code = await _create_authorization_code(
            db=db,
            client_id=client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            state=state,
        )
        return _redirect_with_code(redirect_uri, code, state)

    # Show consent page with session cookie
    response = HTMLResponse(
        content=_consent_page(
            client_name=client.client_name,
            scope=scope,
            user_name=user.name,
            user_email=user.email,
            user_id=user.id,  # Pass user_id for decision
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        ),
        status_code=200,
    )
    # Set secure session cookie for OAuth flow
    response.set_cookie(
        key="auth_token",
        value=session_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=600,  # 10 minutes - enough for consent flow
    )
    return response


@router.post("/authorize/decision")
async def authorize_decision(
    request: Request,
    decision: str = Form(...),
    user_id: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("read"),
    state: Optional[str] = Form(None),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
    remember: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """Handle user's consent decision.

    SECURITY: This endpoint validates that the authenticated user matches the user_id
    in the form to prevent authorization bypass attacks.
    """
    # SECURITY FIX: Verify the user is authenticated and matches the claimed user_id
    # This prevents attackers from submitting decisions for other users
    auth_header = request.headers.get("Authorization", "")
    auth_cookie = request.cookies.get("auth_token", "")

    authenticated_user = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        authenticated_user = await get_user_from_token_db(db, token)
    elif auth_cookie:
        authenticated_user = await get_user_from_token_db(db, auth_cookie)

    # Verify authentication exists and matches the claimed user_id
    if not authenticated_user:
        logger.warning(f"OAuth decision attempt without authentication for user_id={user_id}")
        return HTMLResponse(
            content=_error_page("Authentication required. Please start the authorization flow again."),
            status_code=401,
        )

    if str(authenticated_user.id) != user_id:
        logger.warning(
            f"OAuth decision user_id mismatch: authenticated={authenticated_user.id}, claimed={user_id}"
        )
        return HTMLResponse(
            content=_error_page("Session mismatch. Please start the authorization flow again."),
            status_code=403,
        )

    # User is authenticated and matches - use the authenticated user
    user = authenticated_user

    # Get client
    client = await get_or_create_client(db, client_id, redirect_uri)
    if not client:
        return HTMLResponse(content=_error_page("Unknown client"), status_code=400)

    if decision == "deny":
        return _error_response(redirect_uri, "access_denied", "User denied access", state)

    # User allowed - save consent if remember is checked
    if remember:
        await _save_consent(db, user.id, client_id, scope)

    # Generate authorization code
    code = await _create_authorization_code(
        db=db,
        client_id=client_id,
        user_id=user.id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        state=state,
    )

    return _redirect_with_code(redirect_uri, code, state)


# ============================================================================
# Token Endpoint
# ============================================================================


@router.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth 2.0 token endpoint.

    Supports authorization_code and refresh_token grants.
    """
    if grant_type == "authorization_code":
        return await _handle_authorization_code_grant(
            db=db,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            code_verifier=code_verifier,
        )
    elif grant_type == "refresh_token":
        return await _handle_refresh_token_grant(
            db=db,
            refresh_token=refresh_token,
            client_id=client_id,
            scope=scope,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported_grant_type",
        )


async def _handle_authorization_code_grant(
    db: AsyncSession,
    code: Optional[str],
    redirect_uri: Optional[str],
    client_id: Optional[str],
    code_verifier: Optional[str],
) -> TokenResponse:
    """Handle authorization_code grant."""
    if not code or not redirect_uri or not client_id or not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_request",
        )

    # Find authorization code
    code_hash = hash_token(code)
    result = await db.execute(
        select(OAuthAuthorizationCode).where(
            OAuthAuthorizationCode.code_hash == code_hash,
        )
    )
    auth_code = result.scalar_one_or_none()

    if not auth_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Check if code is expired
    if auth_code.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Check if code was already used
    if auth_code.used_at is not None:
        # Potential replay attack - revoke all tokens that may have been issued
        logger.warning(f"Authorization code reuse detected: {auth_code.id}")
        # Revoke all tokens for this user-client pair issued from compromised code
        await revoke_tokens_for_client(db, auth_code.user_id, auth_code.client_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Validate client_id and redirect_uri match
    if auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Validate PKCE
    if not validate_pkce_challenge(
        code_verifier,
        auth_code.code_challenge,
        auth_code.code_challenge_method,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Mark code as used
    auth_code.used_at = datetime.now(timezone.utc)
    await db.commit()

    # Get user
    result = await db.execute(select(User).where(User.id == auth_code.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Create tokens
    access_token, expires_in = create_oauth_access_token(
        user_id=user.id,
        client_id=client_id,
        scope=auth_code.scope,
        user_email=user.email,
        user_name=user.name,
    )

    raw_refresh_token, family_id, refresh_expires_at = create_oauth_refresh_token(
        user_id=user.id,
        client_id=client_id,
        scope=auth_code.scope,
    )

    # Store refresh token
    refresh_token_record = OAuthRefreshToken(
        token_hash=hash_token(raw_refresh_token),
        client_id=client_id,
        user_id=user.id,
        scope=auth_code.scope,
        family_id=family_id,
        expires_at=refresh_expires_at,
    )
    db.add(refresh_token_record)
    await db.commit()

    logger.info(f"OAuth tokens issued for user {user.id} via client {client_id}")

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in,
        refresh_token=raw_refresh_token,
        scope=auth_code.scope,
    )


async def _handle_refresh_token_grant(
    db: AsyncSession,
    refresh_token: Optional[str],
    client_id: Optional[str],
    scope: Optional[str],
) -> TokenResponse:
    """Handle refresh_token grant with rotation."""
    if not refresh_token or not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_request",
        )

    # Find refresh token
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(OAuthRefreshToken).where(
            OAuthRefreshToken.token_hash == token_hash,
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Check if token is revoked
    if token_record.revoked_at is not None:
        # Token was already used - potential replay attack!
        # Revoke all tokens in this family
        await revoke_token_family(db, token_record.family_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Check if token is expired
    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Validate client_id
    if token_record.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Validate scope (can only reduce scope, not expand)
    granted_scope = token_record.scope
    if scope:
        requested_scopes = parse_scope(scope)
        allowed_scopes = parse_scope(token_record.scope)
        if not requested_scopes.issubset(allowed_scopes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_scope",
            )
        granted_scope = " ".join(sorted(requested_scopes))

    # Revoke current refresh token (rotation)
    token_record.revoked_at = datetime.now(timezone.utc)

    # Get user
    result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_grant",
        )

    # Create new tokens
    access_token, expires_in = create_oauth_access_token(
        user_id=user.id,
        client_id=client_id,
        scope=granted_scope,
        user_email=user.email,
        user_name=user.name,
    )

    raw_refresh_token, _, refresh_expires_at = create_oauth_refresh_token(
        user_id=user.id,
        client_id=client_id,
        scope=granted_scope,
        family_id=token_record.family_id,  # Same family for rotation tracking
    )

    # Store new refresh token
    new_refresh_token = OAuthRefreshToken(
        token_hash=hash_token(raw_refresh_token),
        client_id=client_id,
        user_id=user.id,
        scope=granted_scope,
        family_id=token_record.family_id,
        expires_at=refresh_expires_at,
    )
    db.add(new_refresh_token)
    await db.commit()

    logger.info(f"OAuth tokens refreshed for user {user.id} via client {client_id}")

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in,
        refresh_token=raw_refresh_token,
        scope=granted_scope,
    )


# ============================================================================
# Client Registration Endpoint (RFC 7591)
# ============================================================================


@router.post("/register", response_model=ClientRegistrationResponse)
async def register_client(
    data: ClientRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> ClientRegistrationResponse:
    """Dynamic client registration (RFC 7591)."""
    # Generate client_id
    client_id = f"mn_{generate_token(16)}"

    # Create client
    client = OAuthClient(
        client_id=client_id,
        client_name=data.client_name,
        redirect_uris=data.redirect_uris,
        grant_types=data.grant_types or ["authorization_code", "refresh_token"],
        response_types=data.response_types or ["code"],
        token_endpoint_auth_method=data.token_endpoint_auth_method or "none",
        is_dynamic=True,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    logger.info(f"Registered OAuth client: {client_id}")

    return ClientRegistrationResponse(
        client_id=client.client_id,
        client_name=client.client_name,
        redirect_uris=client.redirect_uris,
        grant_types=client.grant_types,
        response_types=client.response_types,
        token_endpoint_auth_method=client.token_endpoint_auth_method,
    )


# ============================================================================
# Token Revocation Endpoint (RFC 7009)
# ============================================================================


@router.post("/revoke")
async def revoke_token(
    data: RevokeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke an access or refresh token."""
    token_hash = hash_token(data.token)

    # Try to find as refresh token
    result = await db.execute(
        select(OAuthRefreshToken).where(OAuthRefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Revoked refresh token: {refresh_token.id}")

    # Always return 200 per RFC 7009 (even if token not found)
    return {"status": "ok"}


# ============================================================================
# Helper Functions
# ============================================================================


async def _get_consent(
    db: AsyncSession,
    user_id: str,
    client_id: str,
    scope: str,
) -> Optional[OAuthConsent]:
    """Check if user has consented to this client with this scope."""
    result = await db.execute(
        select(OAuthConsent).where(
            OAuthConsent.user_id == user_id,
            OAuthConsent.client_id == client_id,
        )
    )
    consent = result.scalar_one_or_none()

    if not consent:
        return None

    # Check if consented scope covers requested scope
    consented_scopes = parse_scope(consent.scope)
    requested_scopes = parse_scope(scope)

    if requested_scopes.issubset(consented_scopes):
        return consent

    return None


async def _save_consent(
    db: AsyncSession,
    user_id: str,
    client_id: str,
    scope: str,
) -> None:
    """Save or update user consent."""
    result = await db.execute(
        select(OAuthConsent).where(
            OAuthConsent.user_id == user_id,
            OAuthConsent.client_id == client_id,
        )
    )
    consent = result.scalar_one_or_none()

    if consent:
        # Expand scope if needed
        existing_scopes = parse_scope(consent.scope)
        new_scopes = parse_scope(scope)
        combined_scopes = existing_scopes | new_scopes
        consent.scope = " ".join(sorted(combined_scopes))
        consent.updated_at = datetime.now(timezone.utc)
    else:
        consent = OAuthConsent(
            user_id=user_id,
            client_id=client_id,
            scope=scope,
        )
        db.add(consent)

    await db.commit()


async def _create_authorization_code(
    db: AsyncSession,
    client_id: str,
    user_id: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str,
    code_challenge_method: str,
    state: Optional[str],
) -> str:
    """Create and store an authorization code."""
    settings = get_settings()

    # Generate code
    code = generate_token(32)
    code_hash = hash_token(code)

    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.oauth_authorization_code_expire_seconds
    )

    # Store code
    auth_code = OAuthAuthorizationCode(
        code_hash=code_hash,
        client_id=client_id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        state=state,
        expires_at=expires_at,
    )
    db.add(auth_code)
    await db.commit()

    return code


def _redirect_with_code(redirect_uri: str, code: str, state: Optional[str]) -> RedirectResponse:
    """Create redirect response with authorization code."""
    url = f"{redirect_uri}?code={code}"
    if state:
        url += f"&state={state}"
    return RedirectResponse(url=url, status_code=302)


def _error_response(
    redirect_uri: str,
    error: str,
    error_description: str,
    state: Optional[str],
) -> RedirectResponse:
    """Create redirect response with error."""
    url = f"{redirect_uri}?error={error}&error_description={error_description}"
    if state:
        url += f"&state={state}"
    return RedirectResponse(url=url, status_code=302)


def _error_page(message: str) -> str:
    """Generate error HTML page."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Error - MindNest</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
        }}
        h1 {{ color: #dc2626; margin-bottom: 16px; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Error</h1>
        <p>{message}</p>
    </div>
</body>
</html>"""


def _login_page(
    client_id: str,
    client_name: str,
    redirect_uri: str,
    scope: str,
    state: Optional[str],
    code_challenge: str,
    code_challenge_method: str,
    error: Optional[str] = None,
) -> str:
    """Generate login HTML page with XSS-safe escaping."""
    # Escape all user-controlled parameters to prevent XSS
    safe_client_id = html_escape(client_id)
    safe_client_name = html_escape(client_name)
    safe_redirect_uri = html_escape(redirect_uri)
    safe_scope = html_escape(scope)
    safe_code_challenge = html_escape(code_challenge)
    safe_code_challenge_method = html_escape(code_challenge_method)

    error_html = f'<div class="error">{html_escape(error)}</div>' if error else ""
    state_input = f'<input type="hidden" name="state" value="{html_escape(state)}">' if state else ""

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Sign in - MindNest</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
            margin: 20px;
        }}
        .logo {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .logo h1 {{
            color: #1a1a1a;
            margin: 0;
            font-size: 28px;
        }}
        .client-info {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .client-info p {{
            margin: 0;
            color: #666;
            font-size: 14px;
        }}
        .client-name {{
            font-weight: 600;
            color: #333;
        }}
        .error {{
            background: #fee2e2;
            color: #dc2626;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }}
        .form-group {{
            margin-bottom: 16px;
        }}
        label {{
            display: block;
            margin-bottom: 6px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }}
        input[type="email"],
        input[type="password"] {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }}
        input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.1s;
        }}
        button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        button:active {{
            transform: translateY(0);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>MindNest</h1>
        </div>
        <div class="client-info">
            <p>Sign in to continue to</p>
            <p class="client-name">{safe_client_name}</p>
        </div>
        {error_html}
        <form method="POST" action="/oauth/authorize/login">
            <input type="hidden" name="client_id" value="{safe_client_id}">
            <input type="hidden" name="redirect_uri" value="{safe_redirect_uri}">
            <input type="hidden" name="scope" value="{safe_scope}">
            {state_input}
            <input type="hidden" name="code_challenge" value="{safe_code_challenge}">
            <input type="hidden" name="code_challenge_method" value="{safe_code_challenge_method}">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>"""


def _consent_page(
    client_name: str,
    scope: str,
    user_name: str,
    user_email: str,
    client_id: str,
    redirect_uri: str,
    state: Optional[str],
    code_challenge: str,
    code_challenge_method: str,
    user_id: Optional[str] = None,
) -> str:
    """Generate consent HTML page with XSS-safe escaping."""
    # Escape all user-controlled parameters to prevent XSS
    safe_client_name = html_escape(client_name)
    safe_user_name = html_escape(user_name)
    safe_user_email = html_escape(user_email)
    safe_client_id = html_escape(client_id)
    safe_redirect_uri = html_escape(redirect_uri)
    safe_scope = html_escape(scope)
    safe_code_challenge = html_escape(code_challenge)
    safe_code_challenge_method = html_escape(code_challenge_method)

    scopes = parse_scope(scope)
    scope_descriptions = {
        "read": "View your projects and knowledge",
        "write": "Add and modify your knowledge",
    }
    # Escape unknown scope values that might come from user input
    scope_items = "\n".join(
        f'<li>{html_escape(scope_descriptions.get(s, s))}</li>' for s in sorted(scopes)
    )
    state_input = f'<input type="hidden" name="state" value="{html_escape(state)}">' if state else ""
    user_id_input = f'<input type="hidden" name="user_id" value="{html_escape(user_id)}">' if user_id else ""

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Authorize - MindNest</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
            margin: 20px;
        }}
        .logo {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .logo h1 {{
            color: #1a1a1a;
            margin: 0;
            font-size: 28px;
        }}
        .user-info {{
            text-align: center;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid #eee;
        }}
        .user-info p {{
            margin: 4px 0;
            color: #666;
        }}
        .user-name {{
            font-weight: 600;
            color: #333;
        }}
        .client-request {{
            margin-bottom: 24px;
        }}
        .client-request h2 {{
            font-size: 18px;
            color: #333;
            margin: 0 0 8px 0;
        }}
        .client-name {{
            color: #667eea;
            font-weight: 600;
        }}
        .permissions {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
        }}
        .permissions h3 {{
            font-size: 14px;
            color: #666;
            margin: 0 0 12px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .permissions ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .permissions li {{
            color: #333;
            margin-bottom: 8px;
        }}
        .remember {{
            margin-bottom: 24px;
        }}
        .remember label {{
            display: flex;
            align-items: center;
            cursor: pointer;
            color: #666;
            font-size: 14px;
        }}
        .remember input {{
            margin-right: 8px;
        }}
        .buttons {{
            display: flex;
            gap: 12px;
        }}
        button {{
            flex: 1;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.1s;
        }}
        .btn-allow {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .btn-allow:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        .btn-deny {{
            background: #f1f1f1;
            color: #666;
        }}
        .btn-deny:hover {{
            background: #e5e5e5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>MindNest</h1>
        </div>
        <div class="user-info">
            <p class="user-name">{safe_user_name}</p>
            <p>{safe_user_email}</p>
        </div>
        <div class="client-request">
            <h2><span class="client-name">{safe_client_name}</span> wants to access your account</h2>
        </div>
        <div class="permissions">
            <h3>This will allow the application to:</h3>
            <ul>
                {scope_items}
            </ul>
        </div>
        <form method="POST" action="/oauth/authorize/decision">
            {user_id_input}
            <input type="hidden" name="client_id" value="{safe_client_id}">
            <input type="hidden" name="redirect_uri" value="{safe_redirect_uri}">
            <input type="hidden" name="scope" value="{safe_scope}">
            {state_input}
            <input type="hidden" name="code_challenge" value="{safe_code_challenge}">
            <input type="hidden" name="code_challenge_method" value="{safe_code_challenge_method}">
            <div class="remember">
                <label>
                    <input type="checkbox" name="remember" value="true">
                    Remember this decision
                </label>
            </div>
            <div class="buttons">
                <button type="submit" name="decision" value="deny" class="btn-deny">Deny</button>
                <button type="submit" name="decision" value="allow" class="btn-allow">Allow</button>
            </div>
        </form>
    </div>
</body>
</html>"""

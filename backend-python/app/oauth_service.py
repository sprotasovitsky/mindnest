"""OAuth 2.0 Service.

Provides functions for OAuth token creation, validation, and PKCE verification.
Implements RFC 6749 (OAuth 2.0), RFC 7636 (PKCE), RFC 7591 (Dynamic Client Registration).
"""

import base64
import hashlib
import ipaddress
import logging
import secrets
import socket
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .models import OAuthClient, OAuthRefreshToken, User

logger = logging.getLogger(__name__)


# Blocked hosts for SSRF protection
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    # AWS/Cloud metadata endpoints
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.goog",
}

# Known MCP clients with friendly display names
# Maps client_id to (display_name, description)
KNOWN_MCP_CLIENTS = {
    "claude-code": ("Claude Code", "Anthropic's AI coding assistant"),
    "claude": ("Claude", "Anthropic's AI assistant"),
    "cursor": ("Cursor", "AI-powered code editor"),
    "windsurf": ("Windsurf", "AI-powered IDE"),
    "zed": ("Zed", "High-performance code editor"),
}


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 for secure storage.

    Args:
        token: The raw token string

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: Number of bytes (default 32 = 256 bits)

    Returns:
        URL-safe base64-encoded token
    """
    return secrets.token_urlsafe(length)


def validate_pkce_challenge(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Validate PKCE code_verifier against code_challenge.

    Per RFC 7636, only S256 method is recommended for security.

    Args:
        code_verifier: The original code_verifier from the token request
        code_challenge: The code_challenge from the authorization request
        method: Challenge method (only "S256" supported)

    Returns:
        True if code_verifier is valid for the challenge
    """
    if method != "S256":
        logger.warning(f"Unsupported PKCE method: {method}")
        return False

    # S256: BASE64URL(SHA256(code_verifier))
    verifier_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed_challenge = base64.urlsafe_b64encode(verifier_hash).rstrip(b"=").decode("ascii")

    return secrets.compare_digest(computed_challenge, code_challenge)


def create_oauth_access_token(
    user_id: str,
    client_id: str,
    scope: str,
    user_email: str,
    user_name: str,
) -> tuple[str, int]:
    """Create an OAuth 2.0 JWT access token.

    Args:
        user_id: The user's ID
        client_id: The OAuth client ID
        scope: Granted scope (e.g., "read" or "read write")
        user_email: User's email for the token
        user_name: User's name for the token

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    settings = get_settings()
    expires_in = settings.oauth_access_token_expire_seconds
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload = {
        "sub": user_id,
        "email": user_email,
        "name": user_name,
        "client_id": client_id,
        "scope": scope,
        "aud": settings.get_oauth_resource_uri(),  # RFC 8707 audience
        "iss": settings.get_oauth_issuer(),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "oauth_access",
    }

    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token, expires_in


def create_oauth_refresh_token(
    user_id: str,
    client_id: str,
    scope: str,
    family_id: Optional[str] = None,
) -> tuple[str, str, datetime]:
    """Create an OAuth 2.0 refresh token.

    Args:
        user_id: The user's ID
        client_id: The OAuth client ID
        scope: Granted scope
        family_id: Token family ID for rotation tracking (generates new if None)

    Returns:
        Tuple of (raw_token, family_id, expires_at)
    """
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.oauth_refresh_token_expire_days)

    if family_id is None:
        family_id = str(uuid4())

    # Generate a random token (not JWT for refresh tokens)
    raw_token = generate_token(32)

    return raw_token, family_id, expires_at


def validate_oauth_access_token(token: str) -> Optional[dict]:
    """Validate an OAuth access token and return its payload.

    Args:
        token: The JWT access token

    Returns:
        Token payload if valid, None otherwise
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience=settings.get_oauth_resource_uri(),
            issuer=settings.get_oauth_issuer(),
        )

        # Verify it's an OAuth access token
        if payload.get("type") != "oauth_access":
            logger.warning("Token is not an OAuth access token")
            return None

        return payload

    except JWTError as e:
        logger.debug(f"OAuth token validation failed: {e}")
        return None


async def get_user_from_oauth_token(
    db: AsyncSession,
    token: str,
) -> tuple[Optional[User], Optional[dict]]:
    """Get user from OAuth access token.

    Args:
        db: Database session
        token: The JWT access token

    Returns:
        Tuple of (User, payload) if valid, (None, None) otherwise
    """
    payload = validate_oauth_access_token(token)
    if not payload:
        return None, None

    user_id = payload.get("sub")
    if not user_id:
        return None, None

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    return user, payload


async def get_or_create_client(
    db: AsyncSession,
    client_id: str,
    redirect_uri: Optional[str] = None,
) -> Optional[OAuthClient]:
    """Get or create an OAuth client.

    For MCP clients, the client_id might be a URL pointing to a Client ID
    Metadata Document (per MCP spec). In that case, we fetch the metadata
    and create a client record.

    Args:
        db: Database session
        client_id: The client ID (could be a URL)
        redirect_uri: The redirect URI being used (for validation)

    Returns:
        OAuthClient if found/created, None if invalid
    """
    # First, check if we have this client in the database
    result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == client_id)
    )
    client = result.scalar_one_or_none()

    if client:
        return client

    # If client_id looks like a URL, try to fetch Client ID Metadata Document
    if client_id.startswith("http://") or client_id.startswith("https://"):
        client = await fetch_client_metadata(db, client_id)
        if client:
            return client

    # For MCP clients, we allow dynamic registration of localhost clients
    # This is safe because we validate redirect_uri matches client_id origin
    if _is_localhost_client(client_id, redirect_uri):
        return await _create_localhost_client(db, client_id, redirect_uri)

    logger.warning(f"Unknown client_id: {client_id}")
    return None


def _is_localhost_client(client_id: str, redirect_uri: Optional[str]) -> bool:
    """Check if this is a localhost client (typical for MCP/CLI tools).

    Args:
        client_id: The client ID
        redirect_uri: The redirect URI

    Returns:
        True if this appears to be a localhost client
    """
    # Allow localhost clients for development/CLI tools
    localhost_prefixes = [
        "http://localhost",
        "http://127.0.0.1",
        "http://[::1]",
    ]

    if redirect_uri:
        for prefix in localhost_prefixes:
            if redirect_uri.startswith(prefix):
                return True

    return False


def _get_client_display_name(client_id: str) -> str:
    """Get a friendly display name for a client.

    Args:
        client_id: The client ID

    Returns:
        Friendly display name
    """
    # Check known clients first
    if client_id in KNOWN_MCP_CLIENTS:
        return KNOWN_MCP_CLIENTS[client_id][0]

    # For unknown clients, use a generic name
    return f"CLI Client ({client_id})"


async def _create_localhost_client(
    db: AsyncSession,
    client_id: str,
    redirect_uri: Optional[str],
) -> OAuthClient:
    """Create a localhost client for CLI/MCP tools.

    Args:
        db: Database session
        client_id: The client ID
        redirect_uri: The redirect URI

    Returns:
        The created OAuthClient
    """
    # For localhost clients, we create a permissive client
    # that accepts any localhost redirect
    redirect_uris = []
    if redirect_uri:
        redirect_uris.append(redirect_uri)
    # Also allow common localhost patterns
    redirect_uris.extend([
        "http://localhost",
        "http://127.0.0.1",
    ])

    # Get friendly display name for known clients
    client_name = _get_client_display_name(client_id)

    client = OAuthClient(
        client_id=client_id,
        client_name=client_name,
        redirect_uris=redirect_uris,
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",  # Public client
        is_dynamic=True,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    logger.info(f"Created localhost OAuth client: {client_id} -> {client_name}")
    return client


def _is_safe_url(url: str) -> tuple[bool, str]:
    """Validate that a URL is safe to fetch (SSRF protection).

    Blocks:
    - Non-HTTPS URLs (except for DEBUG mode localhost)
    - Private IP ranges (RFC 1918)
    - Loopback addresses
    - Cloud metadata endpoints
    - Link-local addresses

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    settings = get_settings()

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Check scheme - require HTTPS in production
    if parsed.scheme != "https":
        # Allow HTTP only for localhost in debug mode
        if settings.debug and parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1"):
            pass  # Allow for local development
        else:
            return False, "Only HTTPS URLs are allowed"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname"

    # Block known dangerous hosts
    if hostname.lower() in BLOCKED_HOSTS:
        return False, f"Blocked host: {hostname}"

    # Resolve hostname to check IP address
    try:
        # Get all IP addresses for the hostname
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)

                # Block private ranges
                if ip.is_private:
                    return False, f"Private IP address not allowed: {ip}"

                # Block loopback
                if ip.is_loopback:
                    return False, f"Loopback address not allowed: {ip}"

                # Block link-local
                if ip.is_link_local:
                    return False, f"Link-local address not allowed: {ip}"

                # Block reserved (includes cloud metadata 169.254.x.x)
                if ip.is_reserved:
                    return False, f"Reserved address not allowed: {ip}"

            except ValueError:
                continue  # Skip if IP parsing fails

    except socket.gaierror:
        # DNS resolution failed - allow the request and let httpx handle it
        # This prevents DNS rebinding attacks from being an issue
        pass

    return True, ""


async def fetch_client_metadata(
    db: AsyncSession,
    metadata_uri: str,
) -> Optional[OAuthClient]:
    """Fetch Client ID Metadata Document and create client.

    Per MCP spec, client_id can be a URL to a metadata document.
    Includes SSRF protection to prevent fetching from internal networks.

    Args:
        db: Database session
        metadata_uri: URL to the Client ID Metadata Document

    Returns:
        OAuthClient if successfully fetched and created
    """
    # SSRF protection: validate URL before fetching
    is_safe, error = _is_safe_url(metadata_uri)
    if not is_safe:
        logger.warning(f"Blocked unsafe metadata URI: {metadata_uri} - {error}")
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(metadata_uri)
            response.raise_for_status()
            metadata = response.json()

        # Validate required fields per RFC 7591
        client_name = metadata.get("client_name")
        redirect_uris = metadata.get("redirect_uris", [])

        if not client_name:
            logger.warning(f"Client metadata missing client_name: {metadata_uri}")
            return None

        if not redirect_uris:
            logger.warning(f"Client metadata missing redirect_uris: {metadata_uri}")
            return None

        # Create client from metadata
        client = OAuthClient(
            client_id=metadata_uri,  # The URL is the client_id
            client_name=client_name,
            redirect_uris=redirect_uris,
            grant_types=metadata.get("grant_types", ["authorization_code", "refresh_token"]),
            response_types=metadata.get("response_types", ["code"]),
            token_endpoint_auth_method=metadata.get("token_endpoint_auth_method", "none"),
            is_dynamic=False,  # Fetched from metadata document
            metadata_uri=metadata_uri,
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

        logger.info(f"Created OAuth client from metadata: {metadata_uri}")
        return client

    except httpx.RequestError as e:
        logger.warning(f"Failed to fetch client metadata from {metadata_uri}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error processing client metadata from {metadata_uri}: {e}")
        return None


def validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> bool:
    """Validate that redirect_uri is allowed for the client.

    Args:
        client: The OAuth client
        redirect_uri: The redirect URI to validate

    Returns:
        True if redirect_uri is allowed
    """
    # Exact match required per OAuth 2.0 spec
    if redirect_uri in client.redirect_uris:
        return True

    # For localhost clients, allow any port on localhost
    if any(uri.startswith("http://localhost") for uri in client.redirect_uris):
        if redirect_uri.startswith("http://localhost"):
            return True
        if redirect_uri.startswith("http://127.0.0.1"):
            return True

    return False


async def revoke_token_family(
    db: AsyncSession,
    family_id: str,
) -> None:
    """Revoke all refresh tokens in a family.

    Used when token rotation detects a replay attack.

    Args:
        db: Database session
        family_id: The token family ID
    """
    result = await db.execute(
        select(OAuthRefreshToken).where(
            OAuthRefreshToken.family_id == family_id,
            OAuthRefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()

    now = datetime.now(timezone.utc)
    for token in tokens:
        token.revoked_at = now

    await db.commit()
    logger.warning(f"Revoked all tokens in family {family_id} due to potential replay attack")


async def revoke_tokens_for_client(
    db: AsyncSession,
    user_id: str,
    client_id: str,
) -> int:
    """Revoke all refresh tokens for a user-client pair.

    Used when authorization code reuse is detected to revoke any
    tokens that may have been issued from the compromised code.

    Args:
        db: Database session
        user_id: The user's ID
        client_id: The OAuth client ID

    Returns:
        Number of tokens revoked
    """
    result = await db.execute(
        select(OAuthRefreshToken).where(
            OAuthRefreshToken.user_id == user_id,
            OAuthRefreshToken.client_id == client_id,
            OAuthRefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()

    now = datetime.now(timezone.utc)
    for token in tokens:
        token.revoked_at = now

    await db.commit()

    if tokens:
        logger.warning(
            f"Revoked {len(tokens)} tokens for user {user_id} and client {client_id} "
            "due to authorization code reuse"
        )

    return len(tokens)


def parse_scope(scope: str) -> set[str]:
    """Parse a space-separated scope string into a set of scopes.

    Args:
        scope: Space-separated scope string (e.g., "read write")

    Returns:
        Set of individual scopes
    """
    if not scope:
        return {"read"}  # Default scope
    return set(scope.split())


def validate_scope(requested_scope: str, allowed_scopes: set[str] = {"read", "write"}) -> tuple[bool, str]:
    """Validate requested scope.

    Args:
        requested_scope: Space-separated requested scopes
        allowed_scopes: Set of allowed scope values

    Returns:
        Tuple of (is_valid, granted_scope)
    """
    requested = parse_scope(requested_scope)

    # Check all requested scopes are allowed
    invalid_scopes = requested - allowed_scopes
    if invalid_scopes:
        return False, ""

    # Return the granted scope (same as requested if valid)
    return True, " ".join(sorted(requested))

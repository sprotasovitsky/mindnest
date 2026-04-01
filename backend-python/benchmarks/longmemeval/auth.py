"""Authentication helpers for LongMemEval benchmark.

Provides:
- JWT login for Chat test (POST /api/auth/login)
- Headless PKCE OAuth flow for MCP test (/oauth/authorize/login → /oauth/authorize/decision → /oauth/token)
"""

import base64
import hashlib
import logging
import os
import re
import secrets
import urllib.parse
from typing import Optional

import httpx

from .config import BenchmarkConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Chat test auth — plain JWT login
# ---------------------------------------------------------------------------

def login_jwt(config: BenchmarkConfig) -> str:
    """Authenticate with email/password and return the Bearer access token."""
    url = f"{config.api_url}/api/auth/login"
    resp = httpx.post(url, json={"email": config.email, "password": config.password}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Login response missing access_token: {data}")
    logger.info("JWT login successful")
    return token


# ---------------------------------------------------------------------------
# MCP test auth — headless PKCE OAuth flow
# ---------------------------------------------------------------------------

def _generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge_S256)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _extract_code_from_location(location: str) -> Optional[str]:
    """Parse the `code` query parameter from a redirect Location header."""
    parsed = urllib.parse.urlparse(location)
    params = urllib.parse.parse_qs(parsed.query)
    codes = params.get("code")
    return codes[0] if codes else None


def _extract_form_field(html: str, name: str) -> Optional[str]:
    """Extract hidden input value from HTML by field name."""
    pattern = rf'<input[^>]+name="{re.escape(name)}"[^>]+value="([^"]*)"'
    m = re.search(pattern, html)
    if m:
        return m.group(1)
    # Also try value before name
    pattern2 = rf'<input[^>]+value="([^"]*)"[^>]+name="{re.escape(name)}"'
    m2 = re.search(pattern2, html)
    return m2.group(1) if m2 else None


def login_oauth_pkce(config: BenchmarkConfig, scope: str = "read write") -> str:
    """Execute headless OAuth PKCE flow and return Bearer access token.

    Flow:
      1. POST /oauth/authorize/login → may redirect with code or show consent page
      2. If consent page: POST /oauth/authorize/decision with allow
      3. POST /oauth/token with code + code_verifier → access_token
    """
    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    base = config.api_url

    # Use a client that does NOT follow redirects so we can capture Location
    with httpx.Client(follow_redirects=False, timeout=30) as client:
        # Step 1: POST /oauth/authorize/login
        login_data = {
            "email": config.email,
            "password": config.password,
            "client_id": config.mcp_client_id,
            "redirect_uri": config.mcp_redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        resp1 = client.post(f"{base}/oauth/authorize/login", data=login_data)

        code: Optional[str] = None

        if resp1.status_code in (301, 302, 303, 307, 308):
            # User already consented → code in Location header
            location = resp1.headers.get("location", "")
            code = _extract_code_from_location(location)
            if not code:
                raise RuntimeError(f"Redirect had no code in Location: {location!r}")
            logger.info("OAuth: code obtained from login redirect (prior consent)")

        elif resp1.status_code == 200:
            # Show consent page — extract hidden fields and POST decision
            html = resp1.text
            session_cookie = resp1.cookies.get("auth_token")

            user_id = _extract_form_field(html, "user_id")
            client_id = _extract_form_field(html, "client_id") or config.mcp_client_id
            redirect_uri = _extract_form_field(html, "redirect_uri") or config.mcp_redirect_uri
            consent_scope = _extract_form_field(html, "scope") or scope
            consent_state = _extract_form_field(html, "state") or state
            consent_challenge = _extract_form_field(html, "code_challenge") or challenge
            consent_method = _extract_form_field(html, "code_challenge_method") or "S256"

            if not user_id:
                raise RuntimeError("Could not extract user_id from consent page HTML")

            decision_data = {
                "decision": "allow",
                "user_id": user_id,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": consent_scope,
                "state": consent_state,
                "code_challenge": consent_challenge,
                "code_challenge_method": consent_method,
                "remember": "true",
            }
            cookies = {}
            if session_cookie:
                cookies["auth_token"] = session_cookie

            resp2 = client.post(
                f"{base}/oauth/authorize/decision",
                data=decision_data,
                cookies=cookies,
            )

            location = resp2.headers.get("location", "")
            code = _extract_code_from_location(location)
            if not code:
                raise RuntimeError(
                    f"Decision response {resp2.status_code} had no code. "
                    f"Location: {location!r}  Body: {resp2.text[:200]}"
                )
            logger.info("OAuth: code obtained after consent decision")

        else:
            raise RuntimeError(
                f"Unexpected status {resp1.status_code} from /oauth/authorize/login: "
                f"{resp1.text[:300]}"
            )

        # Step 3: Exchange code for token
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.mcp_redirect_uri,
            "client_id": config.mcp_client_id,
            "code_verifier": verifier,
        }
        resp3 = client.post(f"{base}/oauth/token", data=token_data)
        resp3.raise_for_status()
        token_json = resp3.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise RuntimeError(f"Token response missing access_token: {token_json}")

    logger.info("OAuth PKCE flow completed — access token obtained")
    return access_token

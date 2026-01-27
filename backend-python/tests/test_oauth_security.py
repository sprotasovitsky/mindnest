"""Security tests for OAuth 2.0 implementation.

Tests for:
1. XSS protection in HTML pages
2. SSRF protection in metadata fetching
3. Authorization code reuse handling
"""

import pytest
from html import escape as html_escape
from unittest.mock import AsyncMock, patch, MagicMock
import socket

# Test XSS protection
class TestXSSProtection:
    """Test that user-controlled parameters are properly escaped."""

    def test_html_escape_works(self):
        """Verify html.escape works as expected."""
        malicious = '"><script>alert(1)</script><input value="'
        escaped = html_escape(malicious)
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
        assert '"' not in escaped or "&quot;" in escaped

    def test_xss_payloads_escaped(self):
        """Test common XSS payloads are escaped."""
        payloads = [
            '<script>alert("XSS")</script>',
            '" onload="alert(1)"',
            "' onclick='alert(1)'",
            '<img src=x onerror=alert(1)>',
            '"><iframe src="javascript:alert(1)">',
            "javascript:alert(1)",
        ]

        for payload in payloads:
            escaped = html_escape(payload)
            # Escaped string should not contain unescaped < or >
            assert "<script" not in escaped.lower() or "&lt;" in escaped
            assert "<img" not in escaped.lower() or "&lt;" in escaped
            assert "<iframe" not in escaped.lower() or "&lt;" in escaped


# Test SSRF protection
class TestSSRFProtection:
    """Test URL validation for SSRF protection."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.debug = False
        return settings

    def test_blocked_hosts(self):
        """Verify blocked hosts list contains critical entries."""
        from app.oauth_service import BLOCKED_HOSTS

        assert "localhost" in BLOCKED_HOSTS
        assert "127.0.0.1" in BLOCKED_HOSTS
        assert "169.254.169.254" in BLOCKED_HOSTS  # AWS metadata
        assert "metadata.google.internal" in BLOCKED_HOSTS  # GCP metadata

    def test_is_safe_url_blocks_http(self):
        """HTTP URLs should be blocked in production."""
        from app.oauth_service import _is_safe_url

        with patch('app.oauth_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.debug = False
            mock_get_settings.return_value = mock_settings

            is_safe, error = _is_safe_url("http://example.com/metadata")
            assert not is_safe
            assert "HTTPS" in error

    def test_is_safe_url_blocks_localhost(self):
        """Localhost URLs should be blocked."""
        from app.oauth_service import _is_safe_url

        with patch('app.oauth_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.debug = False
            mock_get_settings.return_value = mock_settings

            # Test localhost variations
            localhost_urls = [
                "https://localhost/metadata",
                "https://127.0.0.1/metadata",
                "https://0.0.0.0/metadata",
            ]

            for url in localhost_urls:
                is_safe, error = _is_safe_url(url)
                assert not is_safe, f"URL {url} should be blocked"

    def test_is_safe_url_blocks_cloud_metadata(self):
        """Cloud metadata endpoints should be blocked."""
        from app.oauth_service import _is_safe_url

        with patch('app.oauth_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.debug = False
            mock_get_settings.return_value = mock_settings

            # AWS metadata
            is_safe, error = _is_safe_url("https://169.254.169.254/latest/meta-data/")
            assert not is_safe

            # GCP metadata
            is_safe, error = _is_safe_url("https://metadata.google.internal/")
            assert not is_safe

    def test_is_safe_url_blocks_private_ips(self):
        """Private IP ranges should be blocked."""
        from app.oauth_service import _is_safe_url

        with patch('app.oauth_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.debug = False
            mock_get_settings.return_value = mock_settings

            # Mock socket.getaddrinfo to return private IPs
            private_ips = [
                ("10.0.0.1", "10.x.x.x range"),
                ("172.16.0.1", "172.16.x.x range"),
                ("192.168.1.1", "192.168.x.x range"),
            ]

            for ip, description in private_ips:
                with patch('socket.getaddrinfo') as mock_getaddrinfo:
                    mock_getaddrinfo.return_value = [
                        (socket.AF_INET, socket.SOCK_STREAM, 0, '', (ip, 443))
                    ]

                    is_safe, error = _is_safe_url(f"https://internal-service.example.com/")
                    assert not is_safe, f"Private IP {ip} ({description}) should be blocked"
                    assert "Private" in error

    def test_is_safe_url_allows_valid_https(self):
        """Valid HTTPS URLs to public hosts should be allowed."""
        from app.oauth_service import _is_safe_url

        with patch('app.oauth_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.debug = False
            mock_get_settings.return_value = mock_settings

            # Mock DNS resolution to return public IP
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_getaddrinfo.return_value = [
                    (socket.AF_INET, socket.SOCK_STREAM, 0, '', ("93.184.216.34", 443))  # example.com
                ]

                is_safe, error = _is_safe_url("https://example.com/metadata.json")
                assert is_safe, f"Valid HTTPS URL should be allowed: {error}"


# Test token revocation on code reuse
class TestAuthCodeReuse:
    """Test that tokens are revoked when auth code reuse is detected."""

    @pytest.mark.asyncio
    async def test_revoke_tokens_for_client_function_exists(self):
        """Verify revoke_tokens_for_client function exists and is callable."""
        from app.oauth_service import revoke_tokens_for_client

        assert callable(revoke_tokens_for_client)

    @pytest.mark.asyncio
    async def test_revoke_tokens_for_client_revokes_tokens(self):
        """Test that revoke_tokens_for_client actually revokes tokens."""
        from app.oauth_service import revoke_tokens_for_client
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        # Create mock tokens
        mock_token1 = MagicMock()
        mock_token1.revoked_at = None
        mock_token2 = MagicMock()
        mock_token2.revoked_at = None

        # Create mock DB session
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_token1, mock_token2]
        mock_db.execute.return_value = mock_result

        # Call function
        count = await revoke_tokens_for_client(mock_db, "user-123", "client-456")

        # Verify tokens were revoked
        assert mock_token1.revoked_at is not None
        assert mock_token2.revoked_at is not None
        assert count == 2
        mock_db.commit.assert_called_once()


# Integration-style tests (require running server)
class TestOAuthEndpoints:
    """Test OAuth endpoints (requires running server)."""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_well_known_endpoints_exist(self, base_url):
        """Test that well-known endpoints are accessible."""
        import httpx

        try:
            # Test protected resource endpoint
            response = httpx.get(f"{base_url}/.well-known/oauth-protected-resource", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "resource" in data or "error" in data

            # Test authorization server endpoint
            response = httpx.get(f"{base_url}/.well-known/oauth-authorization-server", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "issuer" in data or "error" in data

        except httpx.ConnectError:
            pytest.skip("Server not running - skipping integration test")

    def test_authorize_endpoint_returns_login_page(self, base_url):
        """Test that /oauth/authorize returns a login page."""
        import httpx

        try:
            response = httpx.get(
                f"{base_url}/oauth/authorize",
                params={
                    "response_type": "code",
                    "client_id": "test-client",
                    "redirect_uri": "http://localhost:3000/callback",
                    "scope": "read",
                    "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                    "code_challenge_method": "S256",
                },
                follow_redirects=False,
                timeout=5,
            )

            # Should return HTML login page
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert "MindNest" in response.text
            assert "Sign in" in response.text or "Login" in response.text

        except httpx.ConnectError:
            pytest.skip("Server not running - skipping integration test")

    def test_xss_payload_is_escaped_in_login_page(self, base_url):
        """Test that XSS payloads in parameters are escaped."""
        import httpx

        xss_payload = '"><script>alert("XSS")</script><input value="'

        try:
            response = httpx.get(
                f"{base_url}/oauth/authorize",
                params={
                    "response_type": "code",
                    "client_id": xss_payload,
                    "redirect_uri": "http://localhost:3000/callback",
                    "scope": "read",
                    "state": xss_payload,
                    "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                    "code_challenge_method": "S256",
                },
                follow_redirects=False,
                timeout=5,
            )

            # The response should NOT contain unescaped script tags
            # This is the critical security check - unescaped <script> would execute
            assert "<script>" not in response.text

            # Should contain escaped version, proving the payload was received and escaped
            # The text "alert(" is safe when inside escaped tags like &lt;script&gt;alert(...)&lt;/script&gt;
            assert "&lt;script&gt;" in response.text or "&#" in response.text

        except httpx.ConnectError:
            pytest.skip("Server not running - skipping integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

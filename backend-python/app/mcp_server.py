"""MCP Server Setup.

Configures the Model Context Protocol (MCP) server for Claude Code integration.
Uses fastapi-mcp to expose MCP tool endpoints as MCP tools.

Authentication is handled via OAuth 2.0 at the transport level using AuthConfig.
Token validation happens at tool level (mcp_auth.py).
"""

import logging
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .mcp_auth import get_www_authenticate_header

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def verify_oauth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify OAuth token presence at MCP transport level.

    This dependency triggers OAuth flow in Claude Code when token is missing.
    Full token validation happens at tool level (mcp_auth.py).
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid access token",
            headers={"WWW-Authenticate": get_www_authenticate_header()},
        )

    return credentials.credentials


def setup_mcp_server(app: FastAPI) -> None:
    """Setup MCP server on the FastAPI app.

    Exposes /api/mcp/* endpoints as MCP tools at /mcp endpoint.
    OAuth 2.0 authentication is required at the transport level.

    Args:
        app: FastAPI application instance
    """
    try:
        from fastapi_mcp import AuthConfig, FastApiMCP

        settings = get_settings()
        issuer = settings.get_oauth_issuer()

        # Create MCP server with OAuth config
        # This makes /mcp endpoint require authentication
        mcp = FastApiMCP(
            app,
            name="MindNest",
            description="AI-first knowledge and task management platform",
            include_tags=["mcp"],
            auth_config=AuthConfig(
                issuer=issuer,
                authorize_url=f"{issuer}/oauth/authorize",
                oauth_metadata_url=f"{issuer}/.well-known/oauth-authorization-server",
                # Dependencies to verify token at transport level
                dependencies=[Depends(verify_oauth_token)],
            ),
        )

        # Mount at /mcp endpoint
        mcp.mount_http()

        logger.info("MCP server mounted at /mcp (OAuth 2.0 authentication at transport level)")

    except ImportError:
        logger.warning(
            "fastapi-mcp not installed. MCP server not available. "
            "Install with: pip install fastapi-mcp"
        )
    except Exception as e:
        logger.error(f"Failed to setup MCP server: {e}")

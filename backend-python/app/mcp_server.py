"""MCP Server Setup.

Configures the Model Context Protocol (MCP) server for Claude Code integration.
Uses fastapi-mcp to expose MCP tool endpoints as MCP tools.

Authentication is handled via OAuth 2.0 at the endpoint level (mcp_auth.py).
"""

import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_mcp_server(app: FastAPI) -> None:
    """Setup MCP server on the FastAPI app.

    Exposes /api/mcp/* endpoints as MCP tools at /mcp endpoint.
    Authentication is handled by OAuth 2.0 at the endpoint level.

    Args:
        app: FastAPI application instance
    """
    try:
        from fastapi_mcp import FastApiMCP

        # Create MCP server without auth config
        # OAuth authentication is handled by the endpoints themselves
        mcp = FastApiMCP(
            app,
            name="MindNest",
            description="AI-first knowledge and task management platform",
            include_tags=["mcp"],
            # No auth_config - OAuth is handled at endpoint level via mcp_auth.py
        )

        # Mount at /mcp endpoint
        mcp.mount_http()

        logger.info("MCP server mounted at /mcp (OAuth 2.0 authentication)")

    except ImportError:
        logger.warning(
            "fastapi-mcp not installed. MCP server not available. "
            "Install with: pip install fastapi-mcp"
        )
    except Exception as e:
        logger.error(f"Failed to setup MCP server: {e}")

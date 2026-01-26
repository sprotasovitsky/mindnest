"""MCP Server Setup.

Configures the Model Context Protocol (MCP) server for Claude Code integration.
Uses fastapi-mcp to expose MCP tool endpoints as MCP tools.
"""

import logging
from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader

from .mcp_auth import get_user_from_api_key

logger = logging.getLogger(__name__)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def setup_mcp_server(app: FastAPI) -> None:
    """Setup MCP server on the FastAPI app.

    Exposes /api/mcp/* endpoints as MCP tools at /mcp endpoint.
    Requires X-API-Key header for authentication.

    Args:
        app: FastAPI application instance
    """
    try:
        from fastapi_mcp import FastApiMCP, AuthConfig

        # Create MCP server with authentication
        # Only expose endpoints tagged with "mcp"
        mcp = FastApiMCP(
            app,
            name="MindNest",
            description="AI-first knowledge and task management platform",
            include_tags=["mcp"],
            auth_config=AuthConfig(
                dependencies=[Depends(api_key_header)],
            ),
        )

        # Mount at /mcp endpoint
        mcp.mount_http()

        logger.info("MCP server mounted at /mcp")

    except ImportError:
        logger.warning(
            "fastapi-mcp not installed. MCP server not available. "
            "Install with: pip install fastapi-mcp"
        )
    except Exception as e:
        logger.error(f"Failed to setup MCP server: {e}")

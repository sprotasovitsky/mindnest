"""MindNest Backend - FastAPI Application.

Main entry point for the MindNest backend,
powered by Graphiti for knowledge graph management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .database import init_db, close_db
from .graphiti_client import get_knowledge_graph, close_knowledge_graph
from .llm import close_client as close_llm_client
from .routers import chat, auth, projects, social_auth, api_keys, mcp_tools, oauth
from .mcp_server import setup_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    - On startup: Initialize Graphiti and build indices
    - On shutdown: Close Graphiti connection
    """
    # Startup
    logger.info("Starting MindNest backend...")
    settings = get_settings()

    if not settings.gcp_service_account_email or not settings.gcp_private_key:
        logger.warning("Vertex AI credentials not set! LLM features will not work.")

    # Initialize PostgreSQL
    try:
        await init_db()
        logger.info("PostgreSQL database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise

    # Initialize Graphiti
    try:
        kg = await get_knowledge_graph()
        logger.info("Graphiti knowledge graph initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Graphiti: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down MindNest backend...")
    await close_knowledge_graph()
    await close_db()
    close_llm_client()
    logger.info("All connections closed")


# Create FastAPI app
app = FastAPI(
    title="MindNest API",
    description="AI-first knowledge and task management platform powered by Graphiti",
    version="2.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom validation error handler - strips sensitive data (passwords) from errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without exposing sensitive input data."""
    # Extract only safe error info (no input data which may contain passwords)
    errors = []
    for error in exc.errors():
        safe_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            # Deliberately NOT including "input" - may contain passwords
        }
        errors.append(safe_error)

    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )

# Configure CORS with allowed origins from settings
settings = get_settings()
allowed_origins = settings.get_allowed_origins()

# Log CORS configuration
if allowed_origins:
    logger.info(f"CORS allowed origins: {allowed_origins}")
else:
    logger.warning("No CORS origins configured - all origins will be blocked!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-API-Key"],
)

# Include routers
app.include_router(auth.router)
app.include_router(social_auth.router)
app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(api_keys.router)
app.include_router(mcp_tools.router)
app.include_router(oauth.router)

# Setup MCP server (exposes /api/mcp/* as MCP tools at /mcp)
setup_mcp_server(app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MindNest API",
        "version": "2.0.0",
        "engine": "Graphiti",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# OAuth 2.0 Well-Known Endpoints (RFC 9728, RFC 8414)
# ============================================================================


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """OAuth 2.0 Protected Resource Metadata (RFC 9728).

    Tells clients where to find the authorization server.
    """
    settings = get_settings()
    try:
        issuer = settings.get_oauth_issuer()
        resource = settings.get_oauth_resource_uri()
    except ValueError:
        # OAuth not configured - return 404
        return {"error": "OAuth not configured"}

    return {
        "resource": resource,
        "authorization_servers": [issuer],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["read", "write"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414).

    Provides OAuth endpoints and supported features.
    """
    settings = get_settings()
    try:
        issuer = settings.get_oauth_issuer()
    except ValueError:
        # OAuth not configured - return 404
        return {"error": "OAuth not configured"}

    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "registration_endpoint": f"{issuer}/oauth/register",
        "revocation_endpoint": f"{issuer}/oauth/revoke",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["read", "write"],
        # MCP-specific
        "service_documentation": "https://mindnest.one/docs",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

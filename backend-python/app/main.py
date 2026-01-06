"""MindNest Backend - FastAPI Application.

Main entry point for the MindNest backend,
powered by Graphiti for knowledge graph management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db, close_db
from .graphiti_client import get_knowledge_graph, close_knowledge_graph
from .llm import close_client as close_llm_client
from .routers import chat, auth, projects

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    - On startup: Initialize Graphiti and build indices
    - On shutdown: Close Graphiti connection
    """
    # Startup
    logger.info("Starting MindNest backend...")
    settings = get_settings()

    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set! LLM features will not work.")

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(chat.router)


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


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

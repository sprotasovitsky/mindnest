"""Chat API Router.

Handles chat messages and response generation.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from ..llm import generate_text
from ..prompts import format_response_prompt
from .auth import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from Authorization header (optional).

    Returns minimal user info from token (no DB lookup).
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return decode_token(authorization[7:])


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., min_length=1, max_length=10000)
    projectId: Optional[str] = Field(None, min_length=1)  # Legacy format
    project_id: Optional[str] = Field(None, min_length=1)
    user_id: Optional[str] = None
    user_name: Optional[str] = None

    def get_project_id(self) -> str:
        """Get project ID from either field."""
        return self.projectId or self.project_id or ""


class ChatResponse(BaseModel):
    """Chat response."""

    reply: str
    sources: list[str] = []
    confidence: float = 1.0
    entities_extracted: int = 0


class SearchRequest(BaseModel):
    """Search request."""

    query: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    """Search response."""

    facts: list[dict]
    entities: list[dict]


async def process_message(
    request: ChatRequest,
    kg: KnowledgeGraph,
    user: Optional[dict] = None,
) -> ChatResponse:
    """Process a chat message.

    1. Add message to knowledge graph (Graphiti extracts entities/edges)
    2. Retrieve relevant context from the graph
    3. Generate response using the LLM
    """
    project_id = request.get_project_id()
    user_id = request.user_id or (user["id"] if user else "anonymous")
    user_name = request.user_name or (user.get("name") if user else None)

    logger.info(f"Processing message for project {project_id}: {request.message[:50]}...")

    # Step 1: Add message to knowledge graph
    add_result = await kg.add_message(
        message=request.message,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
    )

    if not add_result["success"]:
        logger.warning(f"Failed to add message to graph: {add_result.get('error')}")

    # Step 2: Get context from knowledge graph
    context = await kg.get_context_for_response(
        query=request.message,
        project_id=project_id,
    )

    # Step 3: Generate response
    prompt = format_response_prompt(
        message=request.message,
        facts=context.get("facts", []),
        entities=context.get("entities", []),
        user_name=user_name,
        project_id=project_id,
    )

    try:
        reply = await generate_text(prompt)
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        reply = "Sorry, I encountered an error generating a response. Please try again."

    return ChatResponse(
        reply=reply,
        sources=[f["fact"] for f in context["facts"][:5]],
        confidence=1.0 if context["facts"] else 0.7,
        entities_extracted=add_result.get("nodes_created", 0),
    )


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Process a chat message."""
    return await process_message(request, kg, user)


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> SearchResponse:
    """Search the knowledge graph."""
    logger.info(f"Searching in project {request.project_id}: {request.query[:50]}...")

    result = await kg.search(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

    return SearchResponse(
        facts=result["facts"],
        entities=result["entities"],
    )


@router.get("/health")
async def health_check(
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "graphiti_initialized": kg._initialized,
        "timestamp": datetime.now().isoformat(),
    }

"""Chat API Router.

New simplified flow:
1. Classify message (DATA/QUESTION/COMMAND)
2. DATA → add to graph + short ack
3. QUESTION → search graph + LLM answer
4. COMMAND → (future: actions) for now treat as DATA
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from ..classifier import classify_message, MessageType
from ..config import get_settings
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from ..llm import generate_text
from ..prompts import format_response_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from Authorization header (optional)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    from .auth import decode_token
    return decode_token(authorization[7:])


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=10000)
    projectId: Optional[str] = Field(None, min_length=1)
    project_id: Optional[str] = Field(None, min_length=1)
    user_id: Optional[str] = None
    user_name: Optional[str] = None

    def get_project_id(self) -> str:
        return self.projectId or self.project_id or ""


class ChatResponse(BaseModel):
    """Chat response."""
    reply: str
    sources: list[str] = []
    confidence: float = 1.0
    entities_extracted: int = 0
    message_type: str = ""
    debug_context: Optional[dict] = None  # For debugging


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    """Search response."""
    edges: list[dict]
    nodes: list[dict]


async def process_message(
    request: ChatRequest,
    kg: KnowledgeGraph,
    user: Optional[dict] = None,
) -> ChatResponse:
    """Process a chat message with classification-based flow."""
    project_id = request.get_project_id()
    user_id = request.user_id or (user["id"] if user else "anonymous")
    user_name = request.user_name or (user.get("name") if user else None)

    # Step 1: Classify message
    classification = await classify_message(request.message, user_name)
    logger.info(f"Classified as {classification.message_type}: {request.message[:50]}...")

    # Step 2: Process based on type
    if classification.message_type == MessageType.QUESTION:
        return await _handle_question(
            request, kg, project_id, user_name, classification.search_query
        )
    else:  # DATA (includes corrections, updates, commands)
        return await _handle_data(request, kg, project_id, user_id, user_name)


async def _handle_data(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
) -> ChatResponse:
    """Handle DATA message - add to graph with context-aware response.

    Now includes search to provide context for better responses,
    especially for corrections and updates.
    """
    # Add to knowledge graph first
    add_result = await kg.add_episode(
        message=request.message,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
    )

    if not add_result["success"]:
        logger.warning(f"Failed to add to graph: {add_result.get('error')}")

    # Search for context to generate better response
    search_result = await kg.search(request.message, project_id, limit=20)
    edges = search_result.get("edges", []) if search_result["success"] else []
    nodes = search_result.get("nodes", []) if search_result["success"] else []

    # Format for prompts
    facts = [{"fact": e["fact"], **e} for e in edges]
    entities = [{"name": n["name"], "summary": n["summary"], **n} for n in nodes]

    # Generate response with context
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
    )

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        reply = "Got it! I've recorded that information."

    return ChatResponse(
        reply=reply,
        sources=[e["fact"] for e in edges[:3]],
        confidence=1.0,
        entities_extracted=add_result.get("nodes_created", 0),
        message_type="DATA",
    )


async def _handle_question(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_name: Optional[str],
    search_query: Optional[str],
) -> ChatResponse:
    """Handle QUESTION message - search and answer."""
    # Use classifier's search query or fall back to original message
    query = search_query or request.message

    # Search knowledge graph
    search_result = await kg.search(query, project_id)

    if not search_result["success"]:
        logger.warning(f"Search failed: {search_result.get('error')}")

    edges = search_result.get("edges", [])
    nodes = search_result.get("nodes", [])

    # Log what we're sending to LLM
    logger.info(f"=== CONTEXT FOR LLM ===")
    logger.info(f"Query used: {query}")
    logger.info(f"Edges ({len(edges)}):")
    for e in edges[:10]:
        logger.info(f"  - {e['fact']}")
    logger.info(f"Nodes ({len(nodes)}):")
    for n in nodes:
        logger.info(f"  - {n['name']}: {n['summary'][:100] if n.get('summary') else 'no summary'}...")

    # Format for prompts (convert to old format for compatibility)
    facts = [{"fact": e["fact"], **e} for e in edges]
    entities = [{"name": n["name"], "summary": n["summary"], **n} for n in nodes]

    # Generate answer using Pro model for better reasoning
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
    )

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        reply = "Sorry, I encountered an error. Please try again."

    return ChatResponse(
        reply=reply,
        sources=[e["fact"] for e in edges[:5]],
        confidence=1.0 if edges else 0.7,
        entities_extracted=0,
        message_type="QUESTION",
        debug_context={
            "query_used": query,
            "edges": edges[:15],
            "nodes": nodes,
            "prompt": prompt,
        },
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
    result = await kg.search(request.query, request.project_id, request.limit)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

    return SearchResponse(
        edges=result["edges"],
        nodes=result["nodes"],
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

"""Chat API Router.

Classification-based flow with background processing:
1. Classify message (DATA/QUESTION)
2. DATA → pending cache + background graph update + quick response
3. QUESTION → search graph + pending + LLM answer
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from ..classifier import classify_message, MessageType
from ..config import get_settings
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from ..llm import generate_text
from ..pending_cache import get_pending_cache
from ..prompts import format_response_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _format_context(edges: list[dict], nodes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Format search results for LLM prompts."""
    facts = [{"fact": e["fact"], **e} for e in edges]
    entities = [{"name": n["name"], "summary": n["summary"], **n} for n in nodes]
    return facts, entities


def _log_context(query: str, edges: list[dict], nodes: list[dict]) -> None:
    """Log search context for debugging."""
    logger.info(f"=== CONTEXT FOR LLM ===")
    logger.info(f"Query used: {query}")
    logger.info(f"Edges ({len(edges)}):")
    for e in edges[:10]:
        logger.info(f"  - {e['fact']}")
    logger.info(f"Nodes ({len(nodes)}):")
    for n in nodes[:10]:
        logger.info(f"  - {n['name']}: {n['summary'][:100] if n.get('summary') else 'no summary'}...")


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
    debug_context: Optional[dict] = None


async def _add_to_graph_background(
    message_id: str,
    message: str,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
) -> None:
    """Background task: add to graph, then remove from pending."""
    cache = get_pending_cache()
    kg = await get_knowledge_graph()

    try:
        logger.info(f"Background: adding to graph {message_id[:8]}...")
        result = await kg.add_episode(
            message=message,
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
        )
        if result["success"]:
            logger.info(f"Background: completed {message_id[:8]}, nodes={result.get('nodes_created', 0)}")
        else:
            logger.warning(f"Background: failed {message_id[:8]}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Background: error {message_id[:8]}: {e}")
    finally:
        await cache.remove(project_id, message_id)
        logger.debug(f"Background: removed from pending {message_id[:8]}")


async def process_message(
    request: ChatRequest,
    kg: KnowledgeGraph,
    background_tasks: BackgroundTasks,
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
    else:  # DATA
        return await _handle_data(
            request, kg, project_id, user_id, user_name, background_tasks
        )


async def _handle_data(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """Handle DATA message with pending cache and background processing."""
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())

    # 1. Instantly add to pending cache
    await cache.add(
        project_id=project_id,
        message_id=message_id,
        user_name=user_name or "User",
        text=request.message,
    )
    logger.info(f"Added to pending cache: {message_id[:8]}...")

    # 2. Schedule background graph update
    background_tasks.add_task(
        _add_to_graph_background,
        message_id=message_id,
        message=request.message,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
    )

    # 3. Search graph for existing context
    search_result = await kg.search(request.message, project_id)
    edges = search_result.get("edges", []) if search_result["success"] else []
    nodes = search_result.get("nodes", []) if search_result["success"] else []

    # 4. Get pending messages (including the one we just added)
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    # 5. Generate response with graph + pending
    facts, entities = _format_context(edges, nodes)
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
        pending_context=pending_context,
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
        entities_extracted=0,  # Will be updated in background
        message_type="DATA",
    )


async def _handle_question(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_name: Optional[str],
    search_query: Optional[str],
) -> ChatResponse:
    """Handle QUESTION message - search graph + pending and answer."""
    cache = get_pending_cache()
    query = search_query or request.message

    # Search knowledge graph
    search_result = await kg.search(query, project_id)

    if not search_result["success"]:
        logger.warning(f"Search failed: {search_result.get('error')}")

    edges = search_result.get("edges", [])
    nodes = search_result.get("nodes", [])

    _log_context(query, edges, nodes)

    # Get pending messages for this project
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    if pending:
        logger.info(f"Including {len(pending)} pending messages in context")

    # Generate response with graph + pending
    facts, entities = _format_context(edges, nodes)
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
        pending_context=pending_context,
    )

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        reply = "Sorry, I encountered an error. Please try again."

    return ChatResponse(
        reply=reply,
        sources=[e["fact"] for e in edges[:5]],
        confidence=1.0 if edges or pending else 0.7,
        entities_extracted=0,
        message_type="QUESTION",
        debug_context={
            "query_used": query,
            "edges_count": len(edges),
            "nodes_count": len(nodes),
            "pending_count": len(pending),
        },
    )


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Process a chat message."""
    return await process_message(request, kg, background_tasks, user)


class BuildCommunitiesRequest(BaseModel):
    """Request to build communities."""
    project_id: str = Field(..., min_length=1)


@router.post("/build-communities")
async def build_communities(
    request: BuildCommunitiesRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Build communities for a project."""
    result = await kg.build_communities(request.project_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Build failed"))
    return {"status": "communities_built", "project_id": request.project_id}


@router.get("/health")
async def health_check(
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Health check endpoint."""
    cache = get_pending_cache()
    return {
        "status": "healthy",
        "graphiti_initialized": kg._initialized,
        "pending_cache": cache.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }

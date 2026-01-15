"""Chat API Router.

Classification-based flow with background processing:
1. Classify message (DATA/QUESTION)
2. DATA → pending cache + background graph update + quick response
3. QUESTION → search graph + pending + history + LLM answer
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..classifier import classify_message, MessageType
from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from ..llm import generate_text
from ..models import ChatMessage, Project, User
from ..pending_cache import get_pending_cache
from ..prompts import format_response_prompt, format_onboarding_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


async def check_token_limit(user: User, db: AsyncSession) -> None:
    """Check if unverified user has exceeded token limit.

    Raises HTTPException 403 if limit exceeded.
    """
    if user.email_verified:
        return  # No limit for verified users

    settings = get_settings()
    if user.tokens_used >= settings.unverified_token_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "token_limit_exceeded",
                "message": "Please verify your email to continue using MindNest",
                "tokens_used": user.tokens_used,
                "limit": settings.unverified_token_limit,
            },
        )


async def update_token_usage(user: User, tokens: int, db: AsyncSession) -> None:
    """Update token usage for user.

    Only tracks usage for unverified users.
    """
    if user.email_verified:
        return  # Don't track for verified users

    user.tokens_used += tokens
    await db.commit()
    logger.debug(f"Updated token usage for {user.id}: +{tokens} = {user.tokens_used}")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def _get_chat_limit() -> str:
    """Get chat rate limit based on debug mode."""
    return get_settings().get_rate_limit("chat")


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


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=10000)
    projectId: Optional[str] = Field(None, min_length=1)
    project_id: Optional[str] = Field(None, min_length=1)

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


class ChatHistoryItem(BaseModel):
    """Single chat history item."""
    id: str
    user_message: str
    assistant_reply: str
    message_type: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: list[ChatHistoryItem]
    total: int


async def save_chat_message(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    user_message: str,
    assistant_reply: str,
    message_type: str,
) -> ChatMessage:
    """Save a chat message to history."""
    chat_msg = ChatMessage(
        project_id=project_id,
        user_id=user_id,
        user_message=user_message,
        assistant_reply=assistant_reply,
        message_type=message_type,
    )
    db.add(chat_msg)
    await db.commit()
    return chat_msg


async def get_chat_history_from_db(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    limit: int = 10,
) -> list[ChatMessage]:
    """Get recent chat history for a user in a project."""
    query = (
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .where(ChatMessage.user_id == user_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    messages = list(result.scalars().all())
    # Return in chronological order (oldest first)
    return list(reversed(messages))


def format_history_for_prompt(messages: list[ChatMessage]) -> str:
    """Format chat history for LLM prompt."""
    if not messages:
        return ""

    lines = []
    for msg in messages:
        lines.append(f"User: {msg.user_message}")
        lines.append(f"Assistant: {msg.assistant_reply}")
        lines.append("")

    return "\n".join(lines)


async def get_project(db: AsyncSession, project_id: str) -> Optional[Project]:
    """Get project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def update_project_description(db: AsyncSession, project_id: str, description: str) -> bool:
    """Update project description."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.description = description
        await db.commit()
        return True
    return False


def parse_description_confirmation(reply: str) -> Optional[str]:
    """Parse DESCRIPTION_CONFIRMED from LLM reply.

    Returns the description if confirmed, None otherwise.
    """
    marker = "DESCRIPTION_CONFIRMED:"
    if marker in reply:
        # Extract description after the marker
        parts = reply.split(marker, 1)
        if len(parts) > 1:
            # Get the description (first line after marker)
            description_part = parts[1].strip()
            # Description ends at double newline or end of string
            if "\n\n" in description_part:
                return description_part.split("\n\n")[0].strip()
            return description_part.split("\n")[0].strip()
    return None


async def process_onboarding(
    message: str,
    chat_history: str,
    user_name: Optional[str],
) -> str:
    """Process message in onboarding mode."""
    settings = get_settings()
    prompt = format_onboarding_prompt(
        message=message,
        chat_history=chat_history,
        user_name=user_name,
    )
    return await generate_text(prompt, model=settings.llm_model_pro)


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
    user: User,
    chat_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Process a chat message with classification-based flow."""
    project_id = request.get_project_id()
    user_id = user.id
    user_name = user.name

    # Step 1: Classify message
    classification = await classify_message(request.message, user_name)
    logger.info(f"Classified as {classification.message_type}: {request.message[:50]}...")

    # Step 2: Process based on type
    if classification.message_type == MessageType.QUESTION:
        return await _handle_question(
            request, kg, project_id, user_name, classification.search_query, chat_history, project_description
        )
    else:  # DATA
        return await _handle_data(
            request, kg, project_id, user_id, user_name, background_tasks, chat_history, project_description
        )


async def _handle_data(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    background_tasks: BackgroundTasks,
    chat_history: str = "",
    project_description: Optional[str] = None,
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

    # 5. Generate response with graph + pending + history + project context
    facts, entities = _format_context(edges, nodes)
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
        pending_context=pending_context,
        chat_history=chat_history,
        project_description=project_description,
    )

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
        if not reply or not reply.strip():
            logger.warning("LLM returned empty response for DATA message")
            reply = "Got it! I've recorded that information."
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
    chat_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Handle QUESTION message - search graph + pending and answer."""
    cache = get_pending_cache()
    query = search_query or request.message

    # Get pending messages FIRST (before search, to avoid race condition)
    # Background tasks may complete during search and remove messages from pending
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    if pending:
        logger.info(f"Including {len(pending)} pending messages in context")

    # Search knowledge graph
    search_result = await kg.search(query, project_id)

    if not search_result["success"]:
        logger.warning(f"Search failed: {search_result.get('error')}")

    edges = search_result.get("edges", [])
    nodes = search_result.get("nodes", [])

    _log_context(query, edges, nodes)

    # Generate response with graph + pending + history + project context
    facts, entities = _format_context(edges, nodes)
    settings = get_settings()
    prompt = format_response_prompt(
        message=request.message,
        facts=facts,
        entities=entities,
        user_name=user_name,
        project_id=project_id,
        pending_context=pending_context,
        chat_history=chat_history,
        project_description=project_description,
    )

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
        if not reply or not reply.strip():
            logger.warning("LLM returned empty response for QUESTION message")
            reply = "Sorry, I couldn't generate a response. Please try again."
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
@limiter.limit(_get_chat_limit)
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    """Process a chat message. Requires authentication."""
    # Check token limit for unverified users
    await check_token_limit(user, db)

    project_id = chat_request.get_project_id()
    user_id = user.id
    user_name = user.name

    # Get chat history for context (user-specific)
    settings = get_settings()
    history_messages = await get_chat_history_from_db(db, project_id, user_id, settings.chat_history_limit)
    chat_history = format_history_for_prompt(history_messages)

    # Check if project needs onboarding (no description set)
    project = await get_project(db, project_id)
    needs_onboarding = project is None or not project.description

    if needs_onboarding:
        # Onboarding flow
        logger.info(f"Onboarding mode for project {project_id}")
        try:
            reply = await process_onboarding(
                message=chat_request.message,
                chat_history=chat_history,
                user_name=user_name,
            )

            # Check if description was confirmed
            confirmed_description = parse_description_confirmation(reply)
            if confirmed_description:
                logger.info(f"Description confirmed for project {project_id}: {confirmed_description[:50]}...")
                await update_project_description(db, project_id, confirmed_description)
                # Clean up the reply - remove the marker
                reply = reply.replace(f"DESCRIPTION_CONFIRMED: {confirmed_description}", "").strip()
                if reply.startswith("\n"):
                    reply = reply.lstrip("\n")

            response = ChatResponse(
                reply=reply,
                sources=[],
                confidence=1.0,
                entities_extracted=0,
                message_type="ONBOARDING",
            )
        except Exception as e:
            logger.error(f"Onboarding error: {e}")
            response = ChatResponse(
                reply="Hi! Please tell me what this project is about so I can help you better.",
                sources=[],
                confidence=1.0,
                entities_extracted=0,
                message_type="ONBOARDING",
            )
    else:
        # Normal flow - project has description
        response = await process_message(
            chat_request, kg, background_tasks, user, chat_history, project.description
        )

    # Save message to history (don't block on save errors)
    try:
        await save_chat_message(
            db=db,
            project_id=project_id,
            user_id=user_id,
            user_message=chat_request.message,
            assistant_reply=response.reply,
            message_type=response.message_type,
        )
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")

    # Update token usage for unverified users
    # Rough estimate: 4 characters per token
    estimated_tokens = (len(chat_request.message) + len(response.reply)) // 4
    await update_token_usage(user, estimated_tokens, db)

    return response


class BuildCommunitiesRequest(BaseModel):
    """Request to build communities."""
    project_id: str = Field(..., min_length=1)


@router.post("/build-communities")
async def build_communities(
    request: BuildCommunitiesRequest,
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: User = Depends(get_current_user),  # Requires authentication
) -> dict:
    """Build communities for a project. Requires authentication."""
    result = await kg.build_communities(request.project_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Build failed"))
    return {"status": "communities_built", "project_id": request.project_id}


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    project_id: str = Query(..., description="Project ID to get history for"),
    limit: int = Query(default=50, le=100, description="Max messages to return"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),  # Requires authentication
) -> ChatHistoryResponse:
    """Get chat history for a project. Requires authentication."""
    messages = await get_chat_history_from_db(db, project_id, user.id, limit)
    return ChatHistoryResponse(
        messages=[
            ChatHistoryItem(
                id=msg.id,
                user_message=msg.user_message,
                assistant_reply=msg.assistant_reply,
                message_type=msg.message_type,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
        total=len(messages),
    )


@router.get("/health")
async def health_check(
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
) -> dict:
    """Health check endpoint (public)."""
    cache = get_pending_cache()
    return {
        "status": "healthy",
        "graphiti_initialized": kg._initialized,
        "pending_cache": cache.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }

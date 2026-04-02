"""Chat API Router.

Classification-based flow with background processing:
1. Classify message (DATA/QUESTION/BOTH) with data extraction
2. DATA/BOTH → save data_to_save to Graphiti (background)
3. QUESTION/BOTH → search graph + pending + history + LLM answer
"""

# Classifier gets last N messages for context resolution
CLASSIFIER_HISTORY_LIMIT = 4

import asyncio
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

from sqlalchemy.orm import selectinload

from ..classifier import classify_message, MessageType
from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..graphiti_client import get_knowledge_graph, KnowledgeGraph
from ..llm import generate_text
from ..models import ChatMessage, Project, ProjectMember, User
from ..pending_cache import get_pending_cache
from ..prompts import format_response_prompt, format_onboarding_prompt, load_prompt

logger = logging.getLogger(__name__)


async def verify_project_membership(
    db: AsyncSession, user: User, project_id: str
) -> Project:
    """Verify user is a member of the project.

    Returns the project if user is a member.
    Raises HTTPException 404 if project not found.
    Raises HTTPException 403 if user is not a member.
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    is_member = any(m.user_id == user.id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    return project


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


def _format_context(
    edges: list[dict], nodes: list[dict], communities: list[dict] | None = None
) -> tuple[list[dict], list[dict], list[dict]]:
    """Format search results for LLM prompts."""
    facts = [{"fact": e["fact"], **e} for e in edges]
    entities = [{"name": n["name"], "summary": n["summary"], **n} for n in nodes]
    comm = communities or []
    return facts, entities, comm


async def _multi_query_search(
    kg: KnowledgeGraph,
    queries: list[str],
    project_id: str,
) -> dict:
    """Execute multiple search queries in parallel and merge/dedup results."""
    if not queries:
        return {"success": True, "edges": [], "nodes": [], "communities": []}

    if len(queries) == 1:
        return await kg.search(queries[0], project_id)

    # Execute all queries in parallel
    tasks = [kg.search(q, project_id) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged_edges: dict[str, dict] = {}  # fact text -> edge dict (dedup by fact)
    merged_nodes: dict[str, dict] = {}  # name -> node dict (dedup by name)
    merged_communities: dict[str, dict] = {}  # name -> community dict (dedup by name)
    any_success = False

    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"Multi-query search error: {r}")
            continue
        if not r.get("success"):
            continue
        any_success = True
        for edge in r.get("edges", []):
            merged_edges.setdefault(edge["fact"], edge)
        for node in r.get("nodes", []):
            merged_nodes.setdefault(node["name"], node)
        for comm in r.get("communities", []):
            merged_communities.setdefault(comm["name"], comm)

    return {
        "success": any_success,
        "edges": list(merged_edges.values()),
        "nodes": list(merged_nodes.values()),
        "communities": list(merged_communities.values()),
    }


def _log_context(
    query: str,
    edges: list[dict],
    nodes: list[dict],
    communities: list[dict] | None = None,
) -> None:
    """Log search context for debugging."""
    comm = communities or []
    logger.info(f"=== GRAPHITI SEARCH RESULTS ===")
    logger.info(f"Query: {query}")
    logger.info(f"Results: {len(edges)} edges, {len(nodes)} nodes, {len(comm)} communities")

    logger.info(f"--- Edges ({len(edges)}) ---")
    for i, e in enumerate(edges):
        logger.info(f"  [{i+1}] {e['fact']}")

    logger.info(f"--- Nodes ({len(nodes)}) ---")
    for i, n in enumerate(nodes):
        summary = n.get('summary') or 'no summary'
        logger.info(f"  [{i+1}] {n['name']}: {summary[:200]}")

    if comm:
        logger.info(f"--- Communities ({len(comm)}) ---")
        for i, c in enumerate(comm):
            summary = c.get('summary') or 'no summary'
            logger.info(f"  [{i+1}] {c.get('name', '?')}: {summary[:200]}")


def _log_prompt_stats(prompt: str, message_type: str) -> None:
    """Log prompt size stats sent to LLM."""
    char_count = len(prompt)
    approx_tokens = char_count // 4
    logger.info(f"=== PROMPT TO LLM ({message_type}) ===")
    logger.info(f"Prompt size: {char_count} chars (~{approx_tokens} tokens)")
    # Log last section (the actual user message part) for verification
    lines = prompt.split('\n')
    if len(lines) > 5:
        logger.info(f"Prompt ends with: ...{lines[-3]}")


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


def format_history_for_classifier(messages: list[ChatMessage]) -> str:
    """Format last N messages for classifier context resolution.

    Used to expand references like "recipe 1", "this list", etc.
    """
    if not messages:
        return ""

    # Take last CLASSIFIER_HISTORY_LIMIT messages
    recent = messages[-CLASSIFIER_HISTORY_LIMIT:] if len(messages) > CLASSIFIER_HISTORY_LIMIT else messages

    lines = []
    for msg in recent:
        lines.append(f"[User]: {msg.user_message}")
        lines.append(f"[Assistant]: {msg.assistant_reply}")
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
    classifier_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Process a chat message with classification-based flow."""
    project_id = request.get_project_id()
    user_id = user.id
    user_name = user.name

    # Step 1: Classify message with context for reference resolution
    classification = await classify_message(
        message=request.message,
        user_name=user_name,
        chat_history=classifier_history,
    )
    logger.info(
        f"Classified as {classification.message_type}: "
        f"data_to_save={'yes' if classification.data_to_save else 'no'}, "
        f"search_queries={classification.search_queries or 'none'}"
    )

    # Step 2: Process based on type
    if classification.message_type == MessageType.QUESTION:
        # Pure question - no data to save
        return await _handle_question(
            request, kg, project_id, user_name,
            classification.search_queries, chat_history, project_description
        )
    elif classification.message_type == MessageType.BOTH:
        # Mixed message - save data AND answer question
        return await _handle_both(
            request, kg, project_id, user_id, user_name,
            background_tasks, classification.data_to_save,
            classification.search_queries, chat_history, project_description
        )
    else:
        # Pure data - save and acknowledge
        return await _handle_data(
            request, kg, project_id, user_id, user_name,
            background_tasks, classification.data_to_save,
            chat_history, project_description
        )


async def _handle_data(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    background_tasks: BackgroundTasks,
    data_to_save: Optional[str],
    chat_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Handle DATA message with pending cache and background processing."""
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())

    # Use extracted data_to_save, or fall back to original message
    graphiti_message = data_to_save or request.message

    # 1. Instantly add to pending cache
    await cache.add(
        project_id=project_id,
        message_id=message_id,
        user_name=user_name or "User",
        text=graphiti_message,
    )
    logger.info(f"Added to pending cache: {message_id[:8]}... data={graphiti_message[:50]}")

    # 2. Schedule background graph update with extracted/expanded data
    background_tasks.add_task(
        _add_to_graph_background,
        message_id=message_id,
        message=graphiti_message,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
    )

    # 3. Search graph for existing context
    search_result = await kg.search(request.message, project_id)
    success = search_result["success"]
    edges = search_result.get("edges", []) if success else []
    nodes = search_result.get("nodes", []) if success else []
    communities = search_result.get("communities", []) if success else []

    # 4. Get pending messages (including the one we just added)
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    # 5. Generate response with graph + pending + history + project context
    _log_context(request.message, edges, nodes, communities)
    facts, entities, comm = _format_context(edges, nodes, communities)
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
        communities=comm,
    )
    _log_prompt_stats(prompt, "DATA")

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


async def _handle_both(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    background_tasks: BackgroundTasks,
    data_to_save: Optional[str],
    search_queries: list[str] | None = None,
    chat_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Handle BOTH message - save data AND answer question."""
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())
    queries = search_queries or [request.message]

    # 1. Save data to pending cache and schedule background processing
    if data_to_save:
        await cache.add(
            project_id=project_id,
            message_id=message_id,
            user_name=user_name or "User",
            text=data_to_save,
        )
        logger.info(f"[BOTH] Added to pending: {message_id[:8]}... data={data_to_save[:50]}")

        background_tasks.add_task(
            _add_to_graph_background,
            message_id=message_id,
            message=data_to_save,
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
        )

    # 2. Get pending messages (including what we just added)
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    # 3. Search knowledge graph (multi-query)
    search_result = await _multi_query_search(kg, queries, project_id)
    success = search_result["success"]
    edges = search_result.get("edges", []) if success else []
    nodes = search_result.get("nodes", []) if success else []
    communities = search_result.get("communities", []) if success else []

    if not success:
        logger.warning(f"[BOTH] Search failed: {search_result.get('error')}")

    _log_context(str(queries), edges, nodes, communities)

    # 4. Generate response with graph + pending + history
    facts, entities, comm = _format_context(edges, nodes, communities)
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
        communities=comm,
    )
    _log_prompt_stats(prompt, "BOTH")

    try:
        reply = await generate_text(prompt, model=settings.llm_model_pro)
        if not reply or not reply.strip():
            logger.warning("[BOTH] LLM returned empty response")
            reply = "Got it! I've recorded the information. However, I couldn't generate a full response."
    except Exception as e:
        logger.error(f"[BOTH] Failed to generate response: {e}")
        reply = "Got it! I've recorded the information, but encountered an error generating a response."

    return ChatResponse(
        reply=reply,
        sources=[e["fact"] for e in edges[:5]],
        confidence=1.0 if edges or pending else 0.7,
        entities_extracted=0,
        message_type="BOTH",
        debug_context={
            "queries_used": queries,
            "edges_count": len(edges),
            "nodes_count": len(nodes),
            "pending_count": len(pending),
            "data_saved": bool(data_to_save),
        },
    )


ITERATIVE_SEARCH_MAX = 2  # Max additional search rounds

def _get_iterative_search_prompt() -> str:
    return load_prompt("iterative_search")


async def _iterative_search(
    kg: KnowledgeGraph,
    project_id: str,
    question: str,
    initial_queries: list[str],
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    """Search with up to 2 additional rounds if first results are insufficient."""
    settings = get_settings()
    all_queries = list(initial_queries)

    # Initial search
    search_result = await _multi_query_search(kg, initial_queries, project_id)
    edges = search_result.get("edges", [])
    nodes = search_result.get("nodes", [])
    communities = search_result.get("communities", [])
    seen_facts = {e["fact"] for e in edges}

    for iteration in range(ITERATIVE_SEARCH_MAX):
        # Ask LLM if we have enough to answer
        facts_summary = "\n".join(f"- {e['fact']}" for e in edges[:20]) or "(none)"
        verdict_prompt = _get_iterative_search_prompt().format(
            question=question, facts_summary=facts_summary
        )

        try:
            verdict = await generate_text(verdict_prompt, model=settings.llm_model_pro)
        except Exception as e:
            logger.warning(f"Iterative search verdict failed: {e}")
            break

        if "ANSWER:" in verdict:
            logger.info(f"Iterative search: sufficient after {iteration} extra rounds")
            break

        if "SEARCH_MORE:" not in verdict:
            break

        # Extract new queries
        raw = verdict.split("SEARCH_MORE:", 1)[1].strip()
        new_queries = [q.strip() for q in raw.split("|") if q.strip()][:2]
        if not new_queries:
            break

        logger.info(f"Iterative search round {iteration + 1}: {new_queries}")
        all_queries.extend(new_queries)

        # Additional search
        extra_result = await _multi_query_search(kg, new_queries, project_id)
        for e in extra_result.get("edges", []):
            if e["fact"] not in seen_facts:
                edges.append(e)
                seen_facts.add(e["fact"])
        for n in extra_result.get("nodes", []):
            if not any(existing["name"] == n["name"] for existing in nodes):
                nodes.append(n)
        for c in extra_result.get("communities", []):
            if not any(existing.get("name") == c.get("name") for existing in communities):
                communities.append(c)

    return edges, nodes, communities, all_queries


async def _handle_question(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_name: Optional[str],
    search_queries: list[str] | None = None,
    chat_history: str = "",
    project_description: Optional[str] = None,
) -> ChatResponse:
    """Handle QUESTION message - search graph + pending and answer."""
    cache = get_pending_cache()
    queries = search_queries or [request.message]

    # Get pending messages FIRST (before search, to avoid race condition)
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    if pending:
        logger.info(f"Including {len(pending)} pending messages in context")

    # Iterative search — up to 2 extra rounds if first results insufficient
    edges, nodes, communities, all_queries = await _iterative_search(
        kg, project_id, request.message, queries
    )

    success = len(edges) > 0 or len(nodes) > 0
    _log_context(str(all_queries), edges, nodes, communities)

    # Generate response with graph + pending + history + project context
    facts, entities, comm = _format_context(edges, nodes, communities)
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
        communities=comm,
    )
    _log_prompt_stats(prompt, "QUESTION")

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
            "queries_used": all_queries,
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
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID is required",
        )

    # Verify user has access to this project
    project = await verify_project_membership(db, user, project_id)

    user_id = user.id
    user_name = user.name

    # Get chat history for context (user-specific)
    settings = get_settings()
    history_messages = await get_chat_history_from_db(db, project_id, user_id, settings.chat_history_limit)
    chat_history = format_history_for_prompt(history_messages)
    classifier_history = format_history_for_classifier(history_messages)

    # Check if project needs onboarding (no description set)
    needs_onboarding = not project.description

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
            chat_request, kg, background_tasks, user,
            chat_history, classifier_history, project.description
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
    db: AsyncSession = Depends(get_db),
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    user: User = Depends(get_current_user),
) -> dict:
    """Build communities for a project. Requires authentication and membership."""
    # Verify user has access to this project
    await verify_project_membership(db, user, request.project_id)

    result = await kg.build_communities(request.project_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Build failed"))
    return {"status": "communities_built", "project_id": request.project_id}


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    project_id: str = Query(..., description="Project ID to get history for"),
    limit: int = Query(default=50, le=100, description="Max messages to return"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Get chat history for a project. Requires authentication and membership."""
    # Verify user has access to this project
    await verify_project_membership(db, user, project_id)

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

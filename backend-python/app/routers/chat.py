"""Chat API Router.

Classification-based flow with background processing:
1. Classify message (DATA/QUESTION/BOTH) with data extraction
2. DATA/BOTH → save data_to_save to Graphiti (background)
3. QUESTION/BOTH → search graph + pending + history + LLM answer
"""

# Classifier gets last N messages for context resolution
CLASSIFIER_HISTORY_LIMIT = 4

import asyncio
import uuid
from datetime import datetime
from typing import Optional

import structlog

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

logger = structlog.get_logger(__name__)


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
        score = e.get("score")
        score_str = f" [score={score:.4f}]" if score is not None else ""
        logger.info(f"  [{i+1}]{score_str} {e['fact']}")

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
    trace_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Process message in onboarding mode."""
    settings = get_settings()
    prompt = format_onboarding_prompt(
        message=message,
        chat_history=chat_history,
        user_name=user_name,
    )
    return await generate_text(
        prompt,
        model=settings.llm_model_pro,
        prompt_name="onboarding",
        step="onboarding",
        trace_id=trace_id,
        project_id=project_id,
        user_id=user_id,
    )


async def _add_to_graph_background(
    message_id: str,
    message: str,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    trace_id: Optional[str] = None,
) -> None:
    """Background task: add to graph, then remove from pending."""
    # Restore trace_id in ContextVar so Langfuse spans inside kg.add_episode() are linked
    from ..context import current_trace_id
    if trace_id:
        current_trace_id.set(trace_id)

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
    trace_id: Optional[str] = None,
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
        trace_id=trace_id,
        project_id=project_id,
        user_id=user_id,
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
            classification.search_queries, chat_history, project_description,
            trace_id=trace_id, user_id=user_id,
        )
    elif classification.message_type == MessageType.BOTH:
        # Mixed message - save data AND answer question
        return await _handle_both(
            request, kg, project_id, user_id, user_name,
            background_tasks, classification.data_to_save,
            classification.search_queries, chat_history, project_description,
            trace_id=trace_id,
        )
    else:
        # Pure data - save and acknowledge
        return await _handle_data(
            request, project_id, user_id, user_name,
            background_tasks, classification.data_to_save,
            chat_history, project_description,
            trace_id=trace_id,
        )


async def _handle_data(
    request: ChatRequest,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    background_tasks: BackgroundTasks,
    data_to_save: Optional[str],
    chat_history: str = "",
    project_description: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> ChatResponse:
    """Handle DATA message with pending cache and background processing."""
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())

    # Use extracted data_to_save, or fall back to original message.
    # If data_to_save lost significant content (< 40% of original length), use original —
    # this prevents the classifier from summarizing structured lists into just their header.
    if data_to_save and len(data_to_save) < len(request.message) * 0.4:
        logger.warning(
            f"data_to_save too short ({len(data_to_save)} vs {len(request.message)} chars), "
            "falling back to original message"
        )
        graphiti_message = request.message
    else:
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
        trace_id=trace_id,
    )

    # 3. Get pending messages (including the one we just added)
    # NOTE: No graph search for DATA — pending_context already has the new fact,
    # and generating a simple "Got it!" acknowledgment doesn't need graph context.
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    # 4. Generate acknowledgment — no graph search for DATA
    edges, nodes, communities = [], [], []
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
        reply = await generate_text(
            prompt,
            model=settings.llm_model_pro,
            prompt_name="response",
            step="chat_response",
            trace_id=trace_id,
            project_id=project_id,
            user_id=user_id,
        )
        if not reply or not reply.strip():
            logger.warning("llm_empty_response_data", trace_id=trace_id)
            reply = "Got it! I've recorded that information."
    except Exception as e:
        logger.error("generate_response_failed", error=str(e), trace_id=trace_id)
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
    trace_id: Optional[str] = None,
) -> ChatResponse:
    """Handle BOTH message - save data AND answer question."""
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())
    queries = search_queries or [request.message]

    # 1. Save data to pending cache and schedule background processing
    if data_to_save:
        # Fall back to original if classifier lost significant content
        graphiti_data = data_to_save
        if len(data_to_save) < len(request.message) * 0.4:
            logger.warning(
                f"[BOTH] data_to_save too short ({len(data_to_save)} vs {len(request.message)} chars), "
                "falling back to original message"
            )
            graphiti_data = request.message
        await cache.add(
            project_id=project_id,
            message_id=message_id,
            user_name=user_name or "User",
            text=graphiti_data,
        )
        logger.info(f"[BOTH] Added to pending: {message_id[:8]}... data={graphiti_data[:50]}")

        background_tasks.add_task(
            _add_to_graph_background,
            message_id=message_id,
            message=graphiti_data,
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
            trace_id=trace_id,
        )

    # 2. Get pending messages (including what we just added)
    pending = await cache.get_pending(project_id)
    pending_context = cache.format_for_prompt(pending)

    # 3. Search knowledge graph (multi-query)
    search_result = await _search_multi(kg, queries, project_id, span_name="search_multi")
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
        reply = await generate_text(
            prompt,
            model=settings.llm_model_pro,
            prompt_name="response",
            step="chat_response",
            trace_id=trace_id,
            project_id=project_id,
            user_id=user_id,
        )
        if not reply or not reply.strip():
            logger.warning("llm_empty_response_both", trace_id=trace_id)
            reply = "Got it! I've recorded the information. However, I couldn't generate a full response."
    except Exception as e:
        logger.error("generate_response_failed_both", error=str(e), trace_id=trace_id)
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


ITERATIVE_SEARCH_MAX = get_settings().iterative_search_max  # Max additional search rounds
POOL_SIZE = 15  # Max facts in rolling pool (verdict + response both use this)


def _pool_top(pool: dict[str, dict], size: int) -> dict[str, dict]:
    """Trim pool to top-N facts by RRF score."""
    scored = sorted(
        pool.items(),
        key=lambda kv: kv[1].get("score") or 0.0,
        reverse=True,
    )
    return dict(scored[:size])


def _get_iterative_search_prompt() -> str:
    return load_prompt("iterative_search")


async def _search_multi(
    kg: KnowledgeGraph,
    queries: list[str],
    project_id: str,
    span_name: str = "search_multi",
) -> dict:
    """Run multi-query search, dedup by fact text keeping highest RRF score."""
    if not queries:
        return {"success": True, "edges": [], "nodes": [], "communities": []}

    if len(queries) == 1:
        return await kg.search(queries[0], project_id)

    from ..graphiti_client import _lf_span
    import time as _time
    span = _lf_span(span_name, input=queries, metadata={"query_count": len(queries)})
    t0 = _time.monotonic()

    tasks = [kg.search(q, project_id) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged_edges: dict[str, dict] = {}  # fact → edge with highest score
    merged_nodes: dict[str, dict] = {}
    merged_communities: dict[str, dict] = {}
    any_success = False

    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"Search error: {r}")
            continue
        if not r.get("success"):
            continue
        any_success = True
        for edge in r.get("edges", []):
            existing = merged_edges.get(edge["fact"])
            if existing is None or (edge.get("score") or 0) > (existing.get("score") or 0):
                merged_edges[edge["fact"]] = edge
        for node in r.get("nodes", []):
            merged_nodes.setdefault(node["name"], node)
        for comm in r.get("communities", []):
            merged_communities.setdefault(comm["name"], comm)

    merged = {
        "success": any_success,
        "edges": list(merged_edges.values()),
        "nodes": list(merged_nodes.values()),
        "communities": list(merged_communities.values()),
    }
    if span:
        span.end(output={
            "edges": len(merged["edges"]),
            "nodes": len(merged["nodes"]),
            "latency_ms": round((_time.monotonic() - t0) * 1000),
        })
    return merged


async def _iterative_search(
    kg: KnowledgeGraph,
    project_id: str,
    question: str,
    initial_queries: list[str],
    trace_id: Optional[str] = None,
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    """Search with rolling pool of top-POOL_SIZE facts by RRF score.

    Verdict sees:
    - top-POOL_SIZE edges sorted by RRF score (bounded, no bloat)
    - ALL accumulated entity names from nodes across all rounds
      so LLM can follow multi-hop connections (e.g. Cartwheel → Target)
    """
    settings = get_settings()
    all_queries = list(initial_queries)

    # Pool: fact_text → edge dict, bounded to POOL_SIZE by RRF score
    pool: dict[str, dict] = {}
    # Nodes: name → node dict — ALL accumulated, not trimmed (names are cheap)
    all_nodes: dict[str, dict] = {}
    all_communities: dict[str, dict] = {}

    def _merge_result(r: dict) -> None:
        for e in r.get("edges", []):
            existing = pool.get(e["fact"])
            if existing is None or (e.get("score") or 0) > (existing.get("score") or 0):
                pool[e["fact"]] = e
        for n in r.get("nodes", []):
            all_nodes[n["name"]] = n
        for c in r.get("communities", []):
            all_communities[c.get("name", "")] = c

    # Round 0: initial search
    result = await _search_multi(kg, initial_queries, project_id, span_name="iterative_search_round_0")
    _merge_result(result)
    trimmed_pool = _pool_top(pool, POOL_SIZE)
    logger.info(f"Round 0: {len(pool)} edges → pool={len(trimmed_pool)}, nodes={len(all_nodes)}")

    for iteration in range(ITERATIVE_SEARCH_MAX):
        pool_facts = list(trimmed_pool.values())
        facts_summary = "\n".join(
            f"- [{e.get('source_name', '?')}] → [{e.get('target_name', '?')}]: {e['fact']}"
            for e in pool_facts
        ) or "(none)"

        # Entity names from ALL accumulated edges (source/target) + top nodes by score
        # Using ALL edges (not just trimmed pool) ensures multi-hop entities stay visible
        pool_entity_names: set[str] = set()
        for e in pool.values():
            if e.get("source_name"):
                pool_entity_names.add(e["source_name"])
            if e.get("target_name"):
                pool_entity_names.add(e["target_name"])

        # Fill up to 25 with top nodes by score not already in pool entities
        top_nodes = sorted(
            all_nodes.values(),
            key=lambda n: n.get("score") or 0.0,
            reverse=True,
        )
        extra_names = [
            n["name"] for n in top_nodes
            if n["name"] not in pool_entity_names
        ][:max(0, 25 - len(pool_entity_names))]

        entity_names = ", ".join(sorted(pool_entity_names) + extra_names) if (pool_entity_names or extra_names) else "(none)"
        logger.info(f"Verdict round {iteration} entity_names: {entity_names[:300]}")

        previous_queries = ", ".join(all_queries)
        verdict_prompt = _get_iterative_search_prompt().format(
            question=question,
            facts_summary=facts_summary,
            entity_names=entity_names,
            previous_queries=previous_queries,
        )

        try:
            verdict = await generate_text(
                verdict_prompt,
                model=settings.llm_model_pro,
                prompt_name="iterative_search",
                step=f"iterative_verdict_{iteration}",
                trace_id=trace_id,
            )
        except Exception as e:
            logger.warning(f"Verdict failed: {e}")
            break

        logger.info(f"Verdict round {iteration}: {verdict[:120]}")

        if "ANSWER:" in verdict:
            logger.info(f"Iterative search: done after round {iteration} (ANSWER)")
            break

        if "SEARCH_MORE:" not in verdict:
            break

        raw = verdict.split("SEARCH_MORE:", 1)[1].strip()
        new_queries = [q.strip() for q in raw.split("|") if q.strip()][:2]
        if not new_queries:
            break

        logger.info(f"Round {iteration + 1}: searching {new_queries}")
        all_queries.extend(new_queries)

        extra = await _search_multi(kg, new_queries, project_id, span_name=f"iterative_search_round_{iteration + 1}")
        _merge_result(extra)
        trimmed_pool = _pool_top(pool, POOL_SIZE)
        logger.info(f"Round {iteration + 1}: {len(pool)} edges → pool={len(trimmed_pool)}, nodes={len(all_nodes)}")

    return list(trimmed_pool.values()), list(all_nodes.values()), list(all_communities.values()), all_queries


async def _handle_question(
    request: ChatRequest,
    kg: KnowledgeGraph,
    project_id: str,
    user_name: Optional[str],
    search_queries: list[str] | None = None,
    chat_history: str = "",
    project_description: Optional[str] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
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
        kg, project_id, request.message, queries, trace_id=trace_id
    )

    success = len(edges) > 0 or len(nodes) > 0
    _log_context(str(all_queries), edges, nodes, communities)

    # edges already bounded to POOL_SIZE and sorted by question_score
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
        reply = await generate_text(
            prompt,
            model=settings.llm_model_pro,
            prompt_name="response",
            step="chat_response",
            trace_id=trace_id,
            project_id=project_id,
            user_id=user_id,
        )
        if not reply or not reply.strip():
            logger.warning("llm_empty_response_question", trace_id=trace_id)
            reply = "Sorry, I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error("generate_response_failed_question", error=str(e), trace_id=trace_id)
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

    # Generate trace_id for this request — correlates all LLM calls in Langfuse/logs
    trace_id = str(uuid.uuid4())

    # Propagate trace_id via context var so Graphiti spans can read it without param threading
    from ..context import current_trace_id
    current_trace_id.set(trace_id)

    # Create Langfuse trace for this request (must exist before generations are added)
    from ..langfuse_client import get_langfuse
    lf = get_langfuse()
    if lf:
        try:
            lf.trace(
                id=trace_id,
                name="chat_request",
                input=chat_request.message,
                metadata={"project_id": chat_request.get_project_id()},
            )
        except Exception:
            pass

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
        logger.info("onboarding_mode", project_id=project_id, trace_id=trace_id)
        try:
            reply = await process_onboarding(
                message=chat_request.message,
                chat_history=chat_history,
                user_name=user_name,
                trace_id=trace_id,
                project_id=project_id,
                user_id=user_id,
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
            chat_history, classifier_history, project.description,
            trace_id=trace_id,
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

    # Update Langfuse trace with final output
    if lf:
        try:
            lf.trace(id=trace_id, output=response.reply)
        except Exception:
            pass

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

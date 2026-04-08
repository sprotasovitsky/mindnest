"""MCP Tools Router.

Provides REST endpoints for MCP tools that can be called by Claude Code.
Only OAuth 2.0 authentication is supported.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..classifier import extract_data
from ..config import get_settings
from ..context import current_trace_id
from ..database import get_db
from ..graphiti_client import get_knowledge_graph
from ..langfuse_client import get_langfuse
from ..mcp_auth import McpAuth, get_mcp_auth_read, get_mcp_auth_write
from ..models import Project, ProjectMember
from ..pending_cache import get_pending_cache
from ..prompts import _format_facts_grouped, _format_entities_standalone
from ..search import iterative_search, add_to_graph_background, format_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CurrentUserResponse(BaseModel):
    """Current authenticated user info."""
    id: str
    name: str
    email: str


class ProjectResponse(BaseModel):
    """Project info."""
    id: str
    name: str
    description: Optional[str] = None


class ListProjectsResponse(BaseModel):
    """List of projects."""
    projects: list[ProjectResponse]


class SearchRequest(BaseModel):
    """Search knowledge graph request."""
    query: str = Field(..., min_length=1, max_length=1000)
    project_id: str = Field(..., min_length=1)


class FactResult(BaseModel):
    """A fact from the knowledge graph."""
    fact: str
    source: Optional[str] = None
    target: Optional[str] = None
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    expired_at: Optional[str] = None


class EntityResult(BaseModel):
    """An entity from the knowledge graph."""
    name: str
    summary: Optional[str] = None
    created_at: Optional[str] = None


class TopicResult(BaseModel):
    """A topic cluster from the knowledge graph."""
    name: str
    summary: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results."""
    success: bool
    facts: str = ""
    entities: list[EntityResult] = []
    topics: list[TopicResult] = []
    pending_context: str = ""
    error: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Send message to knowledge graph."""
    message: str = Field(..., min_length=1, max_length=10000)
    project_id: str = Field(..., min_length=1)


class SendMessageResponse(BaseModel):
    """Send message response."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


async def log_mcp_action(
    db: AsyncSession,
    auth: McpAuth,
    action: str,
    project_id: Optional[str] = None,
    request_data: Optional[dict] = None,
    response_summary: Optional[str] = None,
) -> None:
    """Log an MCP action to database (without message content for privacy).

    Args:
        db: Database session
        auth: MCP authentication info
        action: Action name (list_projects, search_knowledge, send_message)
        project_id: Project ID if applicable
        request_data: Request metadata (lengths only, no content)
        response_summary: Brief result summary
    """
    from ..models import McpLog

    log = McpLog(
        user_id=auth.user.id,
        oauth_client_id=auth.oauth_client_id,
        action=action,
        project_id=project_id,
        request_data=request_data,
        response_summary=response_summary,
    )
    db.add(log)
    await db.commit()

    logger.info(
        f"MCP action: {action} by user {auth.user.id} "
        f"(client: {auth.oauth_client_id}, project: {project_id})"
    )


async def verify_project_access(
    db: AsyncSession,
    user_id: str,
    project_id: str,
) -> Project:
    """Verify user has access to project.

    Returns project if user is a member.
    Raises HTTPException if not found or not a member.
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

    is_member = any(m.user_id == user_id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    return project


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/me", response_model=CurrentUserResponse, operation_id="get_current_user")
async def get_current_user(
    auth: McpAuth = Depends(get_mcp_auth_read),
) -> CurrentUserResponse:
    """Get current authenticated user.

    Requires: read scope

    Returns the user's name and email. Use this to understand who "me/I"
    refers to when the user asks questions like:
    - "what are MY tasks?"
    - "what did I add yesterday?"

    Call this BEFORE search_knowledge when the query contains first-person pronouns.
    """
    logger.info(f"MCP get_current_user: user {auth.user.id} ({auth.user.name})")

    return CurrentUserResponse(
        id=auth.user.id,
        name=auth.user.name,
        email=auth.user.email,
    )


@router.get("/projects", response_model=ListProjectsResponse, operation_id="list_projects")
async def list_projects(
    auth: McpAuth = Depends(get_mcp_auth_read),
    db: AsyncSession = Depends(get_db),
) -> ListProjectsResponse:
    """List all projects for the authenticated user.

    Requires: read scope
    """
    # Get all projects where user is a member
    result = await db.execute(
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == auth.user.id)
    )
    projects = result.scalars().all()

    # Log action
    await log_mcp_action(
        db=db,
        auth=auth,
        action="list_projects",
        response_summary=f"Found {len(projects)} projects",
    )

    logger.info(f"MCP list_projects: {len(projects)} projects for user {auth.user.id}")

    return ListProjectsResponse(
        projects=[
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
            )
            for p in projects
        ]
    )


@router.post("/search", response_model=SearchResponse, operation_id="search_knowledge")
async def search_knowledge(
    data: SearchRequest,
    auth: McpAuth = Depends(get_mcp_auth_read),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search project knowledge using iterative multi-round search.

    Requires: read scope

    Performs LLM-guided iterative search through the knowledge graph:
    - Multiple search rounds with relevance scoring
    - BFS depth=1 for immediate neighbor discovery
    - Results grouped by entity with directional arrows

    Returns facts as entity-grouped text showing graph connections,
    plus any pending (recently added, not yet processed) data.

    IMPORTANT: For queries with first-person pronouns ("my tasks", "what did I add?"),
    call get_current_user FIRST to get the user's name, then search with that name.
    """
    # Verify project access
    await verify_project_access(db, auth.user.id, data.project_id)

    # Create Langfuse trace
    trace_id = str(uuid.uuid4())
    current_trace_id.set(trace_id)
    settings = get_settings()
    lf = get_langfuse()
    if lf:
        try:
            lf.trace(id=trace_id, name="mcp_search", input=data.query,
                     user_id=str(auth.user.id), session_id=f"{auth.user.id}:{data.project_id}",
                     version=settings.app_version,
                     tags=["mcp", "search"],
                     metadata={"project_id": data.project_id, "oauth_client_id": auth.oauth_client_id})
        except Exception:
            pass

    # Iterative search (same pipeline as chat)
    kg = await get_knowledge_graph()
    edges, nodes, communities, all_queries = await iterative_search(
        kg, data.project_id, data.query, [data.query], trace_id=trace_id,
    )

    # Format as entity-grouped text (same as chat prompt)
    facts_list, entities_list, comm_list = format_context(edges, nodes, communities)
    facts_text = _format_facts_grouped(facts_list, entities_list)

    # Get pending context (recently added, not yet in graph)
    cache = get_pending_cache()
    pending = await cache.get_pending(data.project_id)
    pending_context = cache.format_for_prompt(pending)

    # Entity results for backward compat
    entity_results = [
        EntityResult(
            name=n["name"],
            summary=n.get("summary"),
            created_at=n.get("created_at"),
        )
        for n in nodes
    ]

    topics = [
        TopicResult(
            name=c["name"],
            summary=c.get("summary"),
        )
        for c in communities
        if c.get("summary")
    ]

    # Log action
    await log_mcp_action(
        db=db,
        auth=auth,
        action="search_knowledge",
        project_id=data.project_id,
        request_data={"query_len": len(data.query), "search_rounds": len(all_queries)},
        response_summary=f"Found {len(edges)} facts, {len(nodes)} entities, {len(all_queries)} queries",
    )

    logger.info(
        f"MCP search_knowledge: query_len={len(data.query)} "
        f"found {len(edges)} facts, {len(nodes)} entities, {len(all_queries)} queries"
    )

    response = SearchResponse(
        success=True,
        facts=facts_text,
        entities=entity_results,
        topics=topics,
        pending_context=pending_context,
    )
    if lf:
        try:
            lf.trace(id=trace_id, output=f"{len(edges)} facts, {len(nodes)} entities, {len(all_queries)} queries")
        except Exception:
            pass
    return response


@router.post("/message", response_model=SendMessageResponse, operation_id="send_message")
async def send_message(
    data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    auth: McpAuth = Depends(get_mcp_auth_write),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """Add a message to the knowledge graph.

    Requires: write scope

    Store any type of information that can be searched later:
    - Facts: personal details, contact info, numbers, dates
    - Events: meetings, trips, appointments, milestones
    - Tasks: to-dos, reminders, assignments
    - Preferences: likes, dislikes, choices, opinions
    - Relationships: who knows whom, who recommended what
    - States: current activities, ongoing projects, habits

    The message is automatically processed to extract atomic facts before
    storage. Data becomes immediately searchable via search_knowledge
    (pending cache) and permanently stored after graph processing (~30s).

    IMPORTANT: Each message is processed independently. Include full context
    in the message itself — resolve pronouns, expand references.

    NOTE: This does NOT generate an AI response — it only stores data.
    """
    # Verify project access
    project = await verify_project_access(db, auth.user.id, data.project_id)

    if not project.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project onboarding not complete. Please complete onboarding in the app first.",
        )

    # Create Langfuse trace
    trace_id = str(uuid.uuid4())
    current_trace_id.set(trace_id)
    settings = get_settings()
    lf = get_langfuse()
    if lf:
        try:
            lf.trace(id=trace_id, name="mcp_send_message", input=data.message[:200],
                     user_id=str(auth.user.id), session_id=f"{auth.user.id}:{data.project_id}",
                     version=settings.app_version,
                     tags=["mcp", "write"],
                     metadata={"project_id": data.project_id, "oauth_client_id": auth.oauth_client_id})
        except Exception:
            pass

    # Extract atomic facts from message (same as chat classifier data extraction)
    extracted = await extract_data(
        message=data.message,
        user_name=auth.user.name,
        trace_id=trace_id,
        project_id=data.project_id,
        user_id=auth.user.id,
    )

    # Add to pending cache for immediate searchability
    cache = get_pending_cache()
    message_id = str(uuid.uuid4())
    await cache.add(
        project_id=data.project_id,
        message_id=message_id,
        user_name=auth.user.name,
        text=extracted,
    )

    # Background: add to graph, then remove from pending
    background_tasks.add_task(
        add_to_graph_background,
        message_id=message_id,
        message=extracted,
        project_id=data.project_id,
        user_id=auth.user.id,
        user_name=auth.user.name,
        trace_id=trace_id,
    )

    # Log action
    await log_mcp_action(
        db=db,
        auth=auth,
        action="send_message",
        project_id=data.project_id,
        request_data={"message_len": len(data.message), "extracted_len": len(extracted)},
        response_summary="Message extracted and queued",
    )

    logger.info(
        f"MCP send_message: len={len(data.message)} extracted={len(extracted)} "
        f"queued for project {data.project_id}"
    )

    if lf:
        try:
            lf.trace(id=trace_id, output=f"Extracted {len(extracted)} chars, queued for processing")
        except Exception:
            pass
    return SendMessageResponse(
        success=True,
        message="Message extracted and queued for processing. Data is immediately searchable.",
    )

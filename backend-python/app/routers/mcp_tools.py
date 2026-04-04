"""MCP Tools Router.

Provides REST endpoints for MCP tools that can be called by Claude Code.
Only OAuth 2.0 authentication is supported.
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..graphiti_client import get_knowledge_graph
from ..mcp_auth import McpAuth, get_mcp_auth_read, get_mcp_auth_write
from ..models import Project, ProjectMember

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
    facts: list[FactResult] = []
    entities: list[EntityResult] = []
    topics: list[TopicResult] = []
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
    """Search project knowledge using natural language.

    Requires: read scope
    Searches for facts and entities related to the query in the specified project.

    Use this to find any stored information:
    - Facts, events, tasks, preferences, relationships, states
    - People and contacts, purchases and expenses
    - Any information previously stored via send_message or chat

    IMPORTANT: For queries with first-person pronouns ("my tasks", "what did I add?"),
    call get_current_user FIRST to get the user's name, then search with that name.

    Returns facts (relationships between entities) and entities (people, items,
    places, concepts with aggregated summaries).

    Before each search call, reason about:
    1. What do I already know from previous results?
    2. What is still missing to answer the question?
    3. Which entity name from the results could lead me closer to the answer?

    Then search for that entity name. Short entity-name queries (1-2 words)
    find more connected facts than long natural language questions.
    """
    # Verify project access
    await verify_project_access(db, auth.user.id, data.project_id)

    # Search knowledge graph
    kg = await get_knowledge_graph()
    result = await kg.search(
        query=data.query,
        project_id=data.project_id,
    )

    # Format results
    facts = [
        FactResult(
            fact=e["fact"],
            source=e.get("source_name") or None,
            target=e.get("target_name") or None,
            created_at=e.get("created_at"),
            valid_at=e.get("valid_at"),
            expired_at=e.get("expired_at"),
        )
        for e in result.get("edges", [])
    ]

    entities = [
        EntityResult(
            name=n["name"],
            summary=n.get("summary"),
            created_at=n.get("created_at"),
        )
        for n in result.get("nodes", [])
    ]

    topics = [
        TopicResult(
            name=c["name"],
            summary=c.get("summary"),
        )
        for c in result.get("communities", [])
    ]

    # Log action (without query content for privacy)
    await log_mcp_action(
        db=db,
        auth=auth,
        action="search_knowledge",
        project_id=data.project_id,
        request_data={"query_len": len(data.query)},
        response_summary=f"Found {len(facts)} facts, {len(entities)} entities",
    )

    logger.info(
        f"MCP search_knowledge: query_len={len(data.query)} "
        f"found {len(facts)} facts, {len(entities)} entities"
    )

    return SearchResponse(
        success=result.get("success", False),
        facts=facts,
        entities=entities,
        topics=topics,
        error=result.get("error"),
    )


async def _add_to_knowledge_graph(
    message: str,
    project_id: str,
    user_id: str,
    user_name: str,
) -> None:
    """Background task to add message to knowledge graph."""
    try:
        kg = await get_knowledge_graph()
        await kg.add_episode(
            message=message,
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
        )
        logger.info(f"MCP message added to knowledge graph for project {project_id}")
    except Exception as e:
        logger.error(f"Failed to add MCP message to knowledge graph: {e}")


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

    IMPORTANT: The knowledge graph processes each message independently.
    If a message depends on previous context, include that context in the
    message itself so it is self-contained and searchable.

    Context enrichment patterns:
    - Resolve pronouns: "She completed it" → "Maria completed the design task"
    - Expand references: "Add 50 more" → "Add 50 more items to the grocery list"
    - Include location/source from conversation: if prior context establishes
      a place, service, or person — mention it in the fact explicitly

    The message will be processed by AI to extract entities (people, items,
    dates, places) and facts (relationships between entities). These become
    searchable via search_knowledge.

    NOTE: This does NOT generate an AI response — it only stores data.
    The user's name is automatically associated with the message.
    """
    # Verify project access
    project = await verify_project_access(db, auth.user.id, data.project_id)

    # Check if project has completed onboarding
    if not project.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project onboarding not complete. Please complete onboarding in the app first.",
        )

    # Add to knowledge graph in background
    background_tasks.add_task(
        _add_to_knowledge_graph,
        message=data.message,
        project_id=data.project_id,
        user_id=auth.user.id,
        user_name=auth.user.name,
    )

    # Log action (without message content for privacy)
    await log_mcp_action(
        db=db,
        auth=auth,
        action="send_message",
        project_id=data.project_id,
        request_data={"message_len": len(data.message)},
        response_summary="Message queued for processing",
    )

    logger.info(
        f"MCP send_message: len={len(data.message)} "
        f"queued for project {data.project_id}"
    )

    return SendMessageResponse(
        success=True,
        message="Message queued for processing",
    )

"""MCP Tools Router.

Provides REST endpoints for MCP tools that can be called by Claude Code.
All endpoints require API key authentication via X-API-Key header.
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
from ..mcp_auth import ApiKeyAuth, get_user_from_api_key, get_user_from_api_key_write
from ..models import McpLog, Project, ProjectMember

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ============================================================================
# Request/Response Models
# ============================================================================


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
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    expired_at: Optional[str] = None


class EntityResult(BaseModel):
    """An entity from the knowledge graph."""
    name: str
    summary: Optional[str] = None
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results."""
    success: bool
    facts: list[FactResult] = []
    entities: list[EntityResult] = []
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
    api_key_id: str,
    user_id: str,
    action: str,
    project_id: Optional[str] = None,
    request_data: Optional[dict] = None,
    response_summary: Optional[str] = None,
) -> None:
    """Log an MCP action to the database."""
    log = McpLog(
        api_key_id=api_key_id,
        user_id=user_id,
        action=action,
        project_id=project_id,
        request_data=request_data,
        response_summary=response_summary,
    )
    db.add(log)
    await db.commit()


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


@router.get("/projects", response_model=ListProjectsResponse)
async def list_projects(
    auth: ApiKeyAuth = Depends(get_user_from_api_key),
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
        api_key_id=auth.api_key.id,
        user_id=auth.user.id,
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


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    data: SearchRequest,
    auth: ApiKeyAuth = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search the knowledge graph.

    Requires: read scope
    Searches for facts and entities related to the query in the specified project.
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

    # Log action
    await log_mcp_action(
        db=db,
        api_key_id=auth.api_key.id,
        user_id=auth.user.id,
        action="search_knowledge",
        project_id=data.project_id,
        request_data={"query": data.query},
        response_summary=f"Found {len(facts)} facts, {len(entities)} entities",
    )

    logger.info(
        f"MCP search_knowledge: query='{data.query[:50]}...' "
        f"found {len(facts)} facts, {len(entities)} entities"
    )

    return SearchResponse(
        success=result.get("success", False),
        facts=facts,
        entities=entities,
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


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    auth: ApiKeyAuth = Depends(get_user_from_api_key_write),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """Add a message to the knowledge graph.

    Requires: write scope
    The message will be processed and entities/facts will be extracted.
    This does NOT generate an AI response - it only stores data.
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

    # Log action
    await log_mcp_action(
        db=db,
        api_key_id=auth.api_key.id,
        user_id=auth.user.id,
        action="send_message",
        project_id=data.project_id,
        request_data={"message": data.message[:200]},  # Truncate for log
        response_summary="Message queued for processing",
    )

    logger.info(
        f"MCP send_message: message='{data.message[:50]}...' "
        f"queued for project {data.project_id}"
    )

    return SendMessageResponse(
        success=True,
        message="Message queued for processing",
    )

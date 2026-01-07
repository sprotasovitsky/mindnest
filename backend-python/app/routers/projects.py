"""Projects API Router.

Handles project creation and member management.
Uses PostgreSQL for storage.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Project, ProjectMember
from .auth import get_user_by_email, decode_token, get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """Update project request."""
    name: Optional[str] = None
    description: Optional[str] = None


class AddMemberRequest(BaseModel):
    """Add member request."""
    email: EmailStr


class ProjectResponse(BaseModel):
    """Project response."""
    id: str
    name: str
    description: Optional[str]
    owner_id: str


class MemberResponse(BaseModel):
    """Member response."""
    user_id: str
    email: str
    role: str


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:]  # Remove "Bearer "
    token_data = decode_token(token)

    if not token_data or not token_data.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await get_user_by_id(db, token_data["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project."""
    logger.info(f"Creating project: {request.name} by user {user.id}")

    # Create project
    project = Project(
        name=request.name,
        description=request.description,
        owner_id=user.id,
    )
    db.add(project)
    await db.flush()  # Get project.id

    # Add owner as member with 'owner' role
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)

    await db.commit()
    await db.refresh(project)

    logger.info(f"Project created: {project.id}")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
    )


@router.post("/{project_id}/members", response_model=MemberResponse)
async def add_member(
    project_id: str,
    request: AddMemberRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Add a member to a project."""
    logger.info(f"Adding member {request.email} to project {project_id}")

    # Get project with members
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

    # Check if user is a member
    is_member = any(m.user_id == user.id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    # Block adding members until onboarding is complete (description exists)
    if not project.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete project onboarding before adding members",
        )

    # Get member user
    member_user = await get_user_by_email(db, request.email)
    if not member_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    existing_member = next(
        (m for m in project.members if m.user_id == member_user.id),
        None
    )
    if existing_member:
        return MemberResponse(
            user_id=member_user.id,
            email=member_user.email,
            role=existing_member.role,
        )

    # Add member
    new_member = ProjectMember(
        project_id=project.id,
        user_id=member_user.id,
        role="member",
    )
    db.add(new_member)
    await db.commit()

    logger.info(f"Member added: {member_user.id} to project {project_id}")

    return MemberResponse(
        user_id=member_user.id,
        email=member_user.email,
        role="member",
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project."""
    logger.info(f"Updating project: {project_id}")

    # Get project with members
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

    # Check if user is member
    is_member = any(m.user_id == user.id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    # Update fields
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description

    await db.commit()
    await db.refresh(project)

    logger.info(f"Project updated: {project_id}")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
    )


@router.get("/{project_id}/members", response_model=list[MemberResponse])
async def get_members(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    """Get all members of a project."""
    # Get project with members
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

    # Check if user is member
    is_member = any(m.user_id == user.id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    # Get user details for each member
    members = []
    for m in project.members:
        member_user = await get_user_by_id(db, m.user_id)
        if member_user:
            members.append(MemberResponse(
                user_id=m.user_id,
                email=member_user.email,
                role=m.role,
            ))

    return members


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Get project by ID."""
    # Get project with members
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

    # Check if user is member
    is_member = any(m.user_id == user.id for m in project.members)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """List all projects for current user."""
    # Get all projects where user is a member
    result = await db.execute(
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user.id)
    )
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            owner_id=p.owner_id,
        )
        for p in projects
    ]

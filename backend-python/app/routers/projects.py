"""Projects API Router.

Handles project creation and member management.
Uses in-memory storage for MVP.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field

from .auth import get_user_from_token, get_user_by_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])

# In-memory project storage
# Structure: {project_id: {id, name, description, owner_id, members: [{user_id, email, role}]}}
_projects_db: dict[str, dict] = {}


class CreateProjectRequest(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1)
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


def get_current_user(authorization: str = Header(...)) -> dict:
    """Get current user from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:]  # Remove "Bearer "
    user = get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    user: dict = Depends(get_current_user),
) -> ProjectResponse:
    """Create a new project."""
    logger.info(f"Creating project: {request.name} by user {user['id']}")

    project_id = str(uuid4())
    project = {
        "id": project_id,
        "name": request.name,
        "description": request.description,
        "owner_id": user["id"],
        "members": [
            {
                "user_id": user["id"],
                "email": user["email"],
                "role": "owner",
            }
        ],
        "created_at": datetime.utcnow().isoformat(),
    }

    _projects_db[project_id] = project

    logger.info(f"Project created: {project_id}")

    return ProjectResponse(
        id=project["id"],
        name=project["name"],
        description=project["description"],
        owner_id=project["owner_id"],
    )


@router.post("/{project_id}/members", response_model=MemberResponse)
async def add_member(
    project_id: str,
    request: AddMemberRequest,
    user: dict = Depends(get_current_user),
) -> MemberResponse:
    """Add a member to a project."""
    logger.info(f"Adding member {request.email} to project {project_id}")

    # Get project
    project = _projects_db.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is owner or member
    is_member = any(m["user_id"] == user["id"] for m in project["members"])
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    # Get member user
    member_user = get_user_by_email(request.email)
    if not member_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    already_member = any(m["email"] == request.email.lower() for m in project["members"])
    if already_member:
        # Return existing member info
        for m in project["members"]:
            if m["email"] == request.email.lower():
                return MemberResponse(**m)

    # Add member
    member = {
        "user_id": member_user["id"],
        "email": member_user["email"],
        "role": "member",
    }
    project["members"].append(member)

    logger.info(f"Member added: {member_user['id']} to project {project_id}")

    return MemberResponse(**member)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: dict = Depends(get_current_user),
) -> ProjectResponse:
    """Get project by ID."""
    project = _projects_db.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is member
    is_member = any(m["user_id"] == user["id"] for m in project["members"])
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )

    return ProjectResponse(
        id=project["id"],
        name=project["name"],
        description=project["description"],
        owner_id=project["owner_id"],
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: dict = Depends(get_current_user),
) -> list[ProjectResponse]:
    """List all projects for current user."""
    user_projects = []

    for project in _projects_db.values():
        is_member = any(m["user_id"] == user["id"] for m in project["members"])
        if is_member:
            user_projects.append(
                ProjectResponse(
                    id=project["id"],
                    name=project["name"],
                    description=project["description"],
                    owner_id=project["owner_id"],
                )
            )

    return user_projects

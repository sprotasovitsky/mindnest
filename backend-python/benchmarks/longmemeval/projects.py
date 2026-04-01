"""Project management helpers for LongMemEval benchmark.

Note: There is no DELETE /api/projects/{id} endpoint.
Orphaned projects are namespaced by project_id in Graphiti and are harmless.
To bulk-clean, delete the benchmark user account.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def create_project(
    api_url: str,
    token: str,
    name: str,
    description: Optional[str] = None,
) -> dict:
    """Create a project and return the ProjectResponse dict.

    Args:
        api_url: Base API URL.
        token: Bearer access token.
        name: Project name.
        description: Optional description. When set, the project skips the
            onboarding flow (description acts as the onboarding completion marker).
    """
    payload: dict = {"name": name}
    if description is not None:
        payload["description"] = description

    resp = httpx.post(
        f"{api_url}/api/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    project = resp.json()
    logger.info(f"Created project: {project['id']} name={name!r}")
    return project


def get_project(api_url: str, token: str, project_id: str) -> dict:
    """Fetch a single project by ID."""
    resp = httpx.get(
        f"{api_url}/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

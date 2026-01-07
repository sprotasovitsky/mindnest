"""Pending Cache for immediate message availability.

Stores messages temporarily until they're processed by Graphiti.
This allows other users to see new data immediately without waiting
for the 30-50s add_episode processing time.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PendingMessage:
    """A message waiting to be processed by Graphiti."""
    message_id: str
    user_name: str
    text: str
    created_at: datetime = field(default_factory=datetime.now)


class PendingCache:
    """In-memory pending message cache.

    For production with multiple workers, replace with Redis.
    """

    def __init__(self):
        self._cache: dict[str, list[PendingMessage]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, project_id: str) -> asyncio.Lock:
        """Get or create lock for project."""
        if project_id not in self._locks:
            self._locks[project_id] = asyncio.Lock()
        return self._locks[project_id]

    async def add(
        self,
        project_id: str,
        message_id: str,
        user_name: str,
        text: str,
    ) -> None:
        """Add message to pending cache."""
        async with self._get_lock(project_id):
            if project_id not in self._cache:
                self._cache[project_id] = []

            self._cache[project_id].append(PendingMessage(
                message_id=message_id,
                user_name=user_name,
                text=text,
            ))
            logger.debug(f"Added to pending cache: {message_id[:8]}...")

    async def remove(self, project_id: str, message_id: str) -> None:
        """Remove message after graph processing complete."""
        async with self._get_lock(project_id):
            if project_id in self._cache:
                before = len(self._cache[project_id])
                self._cache[project_id] = [
                    m for m in self._cache[project_id]
                    if m.message_id != message_id
                ]
                after = len(self._cache[project_id])
                if before != after:
                    logger.debug(f"Removed from pending cache: {message_id[:8]}...")

    async def get_pending(self, project_id: str) -> list[PendingMessage]:
        """Get all pending messages for project."""
        return self._cache.get(project_id, [])

    def format_for_prompt(self, messages: list[PendingMessage]) -> str:
        """Format pending messages as simple list."""
        if not messages:
            return ""

        lines = []
        for msg in messages:
            lines.append(f"[{msg.user_name}]: {msg.text}")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_messages = sum(len(msgs) for msgs in self._cache.values())
        return {
            "projects": len(self._cache),
            "total_pending_messages": total_messages,
        }


# Global instance
_pending_cache: Optional[PendingCache] = None


def get_pending_cache() -> PendingCache:
    """Get or create the global PendingCache instance."""
    global _pending_cache
    if _pending_cache is None:
        _pending_cache = PendingCache()
    return _pending_cache

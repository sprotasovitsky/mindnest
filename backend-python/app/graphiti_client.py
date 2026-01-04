"""Graphiti Knowledge Graph Client.

This module provides a wrapper around Graphiti for the MindNest application.
It handles:
- Episode ingestion (messages → knowledge graph)
- Hybrid search (semantic + BM25 + graph traversal)
- Context retrieval for response generation

Graphiti automatically:
- Extracts entities from text
- Creates and normalizes edge types (Emergent Schema)
- Handles temporal invalidation (replaces our SUPERSEDES logic)
- Maintains bi-temporal model (valid_at, expired_at, created_at)
"""

import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from graphiti_core import Graphiti
from graphiti_core.llm_client.google_genai_client import GoogleGenAIClient
from graphiti_core.embedder.google_genai import GoogleGenAIEmbedder

from .config import get_settings

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Graphiti-based knowledge graph for MindNest.

    This replaces:
    - Neo4j KnowledgeItem/KnowledgeRelation
    - Qdrant vector storage
    - VectorSearchService
    - GraphService
    - IntentDetectionEngine (entity extraction part)
    """

    def __init__(self):
        self._client: Optional[Graphiti] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Graphiti client and build indices."""
        if self._initialized:
            return

        settings = get_settings()

        logger.info(f"Initializing Graphiti with Neo4j at {settings.neo4j_uri}")

        # Configure LLM client (Google Gemini)
        llm_client = GoogleGenAIClient(
            api_key=settings.google_api_key,
            model=settings.llm_model,
        )

        # Configure embedder (Google Gemini embeddings)
        embedder = GoogleGenAIEmbedder(
            api_key=settings.google_api_key,
        )

        # Create Graphiti client
        self._client = Graphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
        )

        # Build indices (creates vector and BM25 indices in Neo4j)
        await self._client.build_indices()

        self._initialized = True
        logger.info("Graphiti initialized successfully")

    async def close(self) -> None:
        """Close Graphiti client."""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False

    @property
    def client(self) -> Graphiti:
        """Get Graphiti client, ensuring it's initialized."""
        if not self._client:
            raise RuntimeError("KnowledgeGraph not initialized. Call initialize() first.")
        return self._client

    async def add_message(
        self,
        message: str,
        project_id: str,
        user_id: str,
        user_name: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> dict:
        """Add a user message to the knowledge graph.

        Graphiti will automatically:
        - Extract entities (people, tasks, expenses, etc.)
        - Create edges between entities
        - Handle temporal metadata
        - Invalidate contradicting edges

        Args:
            message: User's message text
            project_id: Project ID for namespace isolation
            user_id: User ID who sent the message
            user_name: Optional user name for better entity extraction
            reference_time: When the message was sent (default: now)

        Returns:
            Dict with episode info and extracted entities
        """
        ref_time = reference_time or datetime.now()

        # Add context about who is speaking
        source_description = f"chat_message from user:{user_id}"
        if user_name:
            source_description += f" ({user_name})"

        logger.info(f"Adding episode for project {project_id}: {message[:50]}...")

        try:
            episode = await self.client.add_episode(
                name=f"msg_{user_id}_{ref_time.isoformat()}",
                episode_body=message,
                source_description=source_description,
                reference_time=ref_time,
                group_id=project_id,  # Isolate data by project
            )

            return {
                "success": True,
                "episode_id": episode.uuid if episode else None,
                "nodes_created": len(episode.nodes) if episode and episode.nodes else 0,
                "edges_created": len(episode.edges) if episode and episode.edges else 0,
            }
        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def search(
        self,
        query: str,
        project_id: str,
        limit: int = 10,
    ) -> dict:
        """Search the knowledge graph.

        Uses Graphiti's hybrid search:
        - Semantic similarity (embeddings)
        - BM25 keyword matching
        - Graph traversal

        Args:
            query: Search query in natural language
            project_id: Project to search in
            limit: Maximum results to return

        Returns:
            Dict with edges (facts) and nodes (entities)
        """
        logger.info(f"Searching in project {project_id}: {query[:50]}...")

        try:
            results = await self.client._search(
                query=query,
                group_ids=[project_id],
                num_results=limit,
            )

            return {
                "success": True,
                "facts": [
                    {
                        "fact": edge.fact,
                        "source": edge.source_node_uuid,
                        "target": edge.target_node_uuid,
                        "created_at": edge.created_at.isoformat() if edge.created_at else None,
                        "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
                        "expired_at": edge.expired_at.isoformat() if edge.expired_at else None,
                    }
                    for edge in (results.edges or [])
                ],
                "entities": [
                    {
                        "uuid": node.uuid,
                        "name": node.name,
                        "summary": node.summary,
                    }
                    for node in (results.nodes or [])
                ],
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "facts": [],
                "entities": [],
            }

    async def get_context_for_response(
        self,
        query: str,
        project_id: str,
        max_facts: int = 10,
        max_entities: int = 5,
    ) -> dict:
        """Get context from knowledge graph for response generation.

        This is used to build the prompt context for the LLM
        when generating a response to the user.

        Args:
            query: User's question/message
            project_id: Project to search in
            max_facts: Maximum facts to include
            max_entities: Maximum entities to include

        Returns:
            Dict with facts and entities formatted for LLM prompt
        """
        search_result = await self.search(query, project_id, limit=max_facts)

        if not search_result["success"]:
            return {
                "facts": [],
                "entities": [],
                "context_text": "No context available.",
            }

        facts = search_result["facts"][:max_facts]
        entities = search_result["entities"][:max_entities]

        # Build context text for LLM
        context_parts = []

        if facts:
            context_parts.append("Known facts:")
            for f in facts:
                fact_text = f["fact"]
                if f.get("expired_at"):
                    fact_text += " [OUTDATED]"
                context_parts.append(f"- {fact_text}")

        if entities:
            context_parts.append("\nRelevant entities:")
            for e in entities:
                context_parts.append(f"- {e['name']}: {e['summary'] or 'No summary'}")

        return {
            "facts": facts,
            "entities": entities,
            "context_text": "\n".join(context_parts) if context_parts else "No context available.",
        }


# Global instance
_knowledge_graph: Optional[KnowledgeGraph] = None


async def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create the global KnowledgeGraph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
        await _knowledge_graph.initialize()
    return _knowledge_graph


async def close_knowledge_graph() -> None:
    """Close the global KnowledgeGraph instance."""
    global _knowledge_graph
    if _knowledge_graph:
        await _knowledge_graph.close()
        _knowledge_graph = None

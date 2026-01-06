"""Graphiti Knowledge Graph Client.

Simplified wrapper around Graphiti - no special case handling.
All intelligence is delegated to LLM via prompts.
"""

import logging
from datetime import datetime
from typing import Optional

from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.search.search_config import (
    SearchConfig,
    EdgeSearchConfig,
    EdgeSearchMethod,
    EdgeReranker,
    NodeSearchConfig,
    NodeSearchMethod,
    NodeReranker,
    CommunitySearchConfig,
    CommunitySearchMethod,
    CommunityReranker,
)

from .config import get_settings
from .llm import get_gemini_client

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Graphiti-based knowledge graph for MindNest."""

    def __init__(self):
        self._client: Optional[Graphiti] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Graphiti client and build indices."""
        if self._initialized:
            return

        settings = get_settings()
        logger.info(f"Initializing Graphiti with Neo4j at {settings.neo4j_uri}")

        genai_client = get_gemini_client()

        # Use configurable model for entity extraction (default: Pro)
        graphiti_model = settings.graphiti_model or settings.llm_model_pro
        logger.info(f"Using model for Graphiti: {graphiti_model}")
        llm_config = LLMConfig(model=graphiti_model)
        llm_client = GeminiClient(config=llm_config, client=genai_client)

        embedder_config = GeminiEmbedderConfig(
            embedding_model="gemini-embedding-001",
            embedding_dim=3072,
        )
        embedder = GeminiEmbedder(config=embedder_config, client=genai_client)

        cross_encoder = GeminiRerankerClient(config=llm_config, client=genai_client)

        self._client = Graphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        await self._client.build_indices_and_constraints()

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

    async def add_episode(
        self,
        message: str,
        project_id: str,
        user_id: str,
        user_name: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> dict:
        """Add a message to the knowledge graph.

        Graphiti automatically extracts entities and creates edges.
        No preprocessing or filtering - just pass the message.
        """
        ref_time = reference_time or datetime.now()

        source_description = f"Message from {user_name or user_id}"

        # Add speaker context for better entity attribution
        episode_body = message
        if user_name:
            episode_body = f"[{user_name} says]: {message}"

        logger.info(f"Adding episode: {episode_body[:80]}...")

        try:
            result = await self.client.add_episode(
                name=f"msg_{user_id}_{ref_time.isoformat()}",
                episode_body=episode_body,
                source_description=source_description,
                reference_time=ref_time,
                group_id=project_id,
            )

            return {
                "success": True,
                "episode_id": result.episode.uuid if result and result.episode else None,
                "nodes_created": len(result.nodes) if result and result.nodes else 0,
                "edges_created": len(result.edges) if result and result.edges else 0,
            }
        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            return {"success": False, "error": str(e)}

    def _get_edge_config(self) -> EdgeSearchConfig:
        """Get standard edge search config with BFS and RRF reranking."""
        return EdgeSearchConfig(
            search_methods=[
                EdgeSearchMethod.bm25,
                EdgeSearchMethod.cosine_similarity,
                EdgeSearchMethod.bfs,
            ],
            reranker=EdgeReranker.rrf,
        )

    def _get_node_config(self) -> NodeSearchConfig:
        """Get standard node search config with BFS and RRF reranking."""
        return NodeSearchConfig(
            search_methods=[
                NodeSearchMethod.bm25,
                NodeSearchMethod.cosine_similarity,
                NodeSearchMethod.bfs,
            ],
            reranker=NodeReranker.rrf,
        )

    def _format_edges(self, edges: list) -> list[dict]:
        """Format edge results for API response."""
        return [
            {
                "fact": edge.fact,
                "created_at": edge.created_at.isoformat() if edge.created_at else None,
                "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
                "expired_at": edge.expired_at.isoformat() if edge.expired_at else None,
            }
            for edge in edges
        ]

    def _format_nodes(self, nodes: list) -> list[dict]:
        """Format node results for API response."""
        return [
            {
                "name": node.name,
                "summary": node.summary,
                "created_at": node.created_at.isoformat() if node.created_at else None,
            }
            for node in nodes
        ]

    async def search(
        self,
        query: str,
        project_id: str,
        limit: int | None = None,
    ) -> dict:
        """Search the knowledge graph."""
        settings = get_settings()
        limit = limit or settings.search_limit
        logger.info(f"Searching: {query[:80]}...")

        try:
            config = SearchConfig(
                edge_config=self._get_edge_config(),
                node_config=self._get_node_config(),
                limit=limit,
            )

            results = await self.client.search_(
                query=query,
                group_ids=[project_id],
                config=config,
            )

            edges = results.edges or []
            nodes = results.nodes or []

            logger.info(f"Found {len(edges)} edges, {len(nodes)} nodes")

            return {
                "success": True,
                "edges": self._format_edges(edges),
                "nodes": self._format_nodes(nodes),
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"success": False, "error": str(e), "edges": [], "nodes": []}

    async def build_communities(self, project_id: str) -> dict:
        """Build communities for a project.

        Uses label propagation to cluster related entities
        and generates summaries for each community.
        """
        logger.info(f"Building communities for project: {project_id}")

        try:
            await self.client.build_communities(group_ids=[project_id])
            logger.info("Communities built successfully")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to build communities: {e}")
            return {"success": False, "error": str(e)}


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

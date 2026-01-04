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

from .config import get_settings

logger = logging.getLogger(__name__)

# Lazy imports for Graphiti to handle import errors gracefully
Graphiti = None
GeminiClient = None
GeminiEmbedder = None
LLMConfig = None
GeminiEmbedderConfig = None
GeminiRerankerClient = None


def _import_graphiti():
    """Lazy import Graphiti and its dependencies."""
    global Graphiti, GeminiClient, GeminiEmbedder, LLMConfig, GeminiEmbedderConfig, GeminiRerankerClient
    if Graphiti is None:
        try:
            from graphiti_core import Graphiti as _Graphiti
            from graphiti_core.llm_client.gemini_client import GeminiClient as _GeminiClient
            from graphiti_core.llm_client.config import LLMConfig as _LLMConfig
            from graphiti_core.embedder.gemini import GeminiEmbedder as _GeminiEmbedder
            from graphiti_core.embedder.gemini import GeminiEmbedderConfig as _GeminiEmbedderConfig
            from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient as _GeminiRerankerClient
            Graphiti = _Graphiti
            GeminiClient = _GeminiClient
            GeminiEmbedder = _GeminiEmbedder
            LLMConfig = _LLMConfig
            GeminiEmbedderConfig = _GeminiEmbedderConfig
            GeminiRerankerClient = _GeminiRerankerClient
        except ImportError as e:
            logger.error(f"Failed to import Graphiti: {e}")
            logger.error("Install with: pip install graphiti-core")
            raise


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

        # Lazy import
        _import_graphiti()

        settings = get_settings()

        logger.info(f"Initializing Graphiti with Neo4j at {settings.neo4j_uri}")

        # Check if we have API key or need to use Vertex AI
        api_key = settings.google_api_key

        if not api_key:
            # Try to get API key from environment or use Vertex AI
            api_key = os.getenv("GOOGLE_API_KEY", "")

        # Create google.genai.Client for LLM and embedder
        from google import genai as google_genai

        if api_key:
            # Use API key
            logger.info("Using Google AI API key")
            genai_client = google_genai.Client(api_key=api_key)
        else:
            # Use Vertex AI with ADC
            logger.info("Using Vertex AI with service account credentials")
            if settings.google_application_credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

            genai_client = google_genai.Client(
                vertexai=True,
                project=settings.vertex_ai_project_id,
                location=settings.vertex_ai_location,
            )

        # Configure LLM client (Google Gemini)
        llm_config = LLMConfig(
            model=settings.llm_model,
        )
        llm_client = GeminiClient(config=llm_config, client=genai_client)

        # Configure embedder (Google Gemini embeddings)
        # gemini-embedding-001: 3072 dimensions, 100+ languages
        embedder_config = GeminiEmbedderConfig(
            embedding_model="gemini-embedding-001",
            embedding_dim=3072,
        )
        embedder = GeminiEmbedder(config=embedder_config, client=genai_client)

        # Configure cross-encoder/reranker (Gemini)
        cross_encoder = GeminiRerankerClient(config=llm_config, client=genai_client)

        # Create Graphiti client
        self._client = Graphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        # Build indices (creates vector and BM25 indices in Neo4j)
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
            result = await self.client.add_episode(
                name=f"msg_{user_id}_{ref_time.isoformat()}",
                episode_body=message,
                source_description=source_description,
                reference_time=ref_time,
                group_id=project_id,  # Isolate data by project
            )

            # AddEpisodeResults has: episode, nodes, edges, etc.
            return {
                "success": True,
                "episode_id": result.episode.uuid if result and result.episode else None,
                "nodes_created": len(result.nodes) if result and result.nodes else 0,
                "edges_created": len(result.edges) if result and result.edges else 0,
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
            from graphiti_core.search.search_config import (
                SearchConfig,
                EdgeSearchConfig, EdgeSearchMethod, EdgeReranker,
                NodeSearchConfig, NodeSearchMethod, NodeReranker,
            )

            # Use hybrid search with BM25 + cosine similarity
            config = SearchConfig(
                edge_config=EdgeSearchConfig(
                    search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
                    reranker=EdgeReranker.rrf,
                ),
                node_config=NodeSearchConfig(
                    search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
                    reranker=NodeReranker.rrf,
                ),
                limit=limit,
            )
            logger.info(f"Calling Graphiti search_ with query='{query}', group_ids=['{project_id}'], limit={limit}")
            try:
                results = await self.client.search_(
                    query=query,
                    group_ids=[project_id],
                    config=config,
                )
                logger.info(f"Search results: edges={len(results.edges) if results.edges else 0}, nodes={len(results.nodes) if results.nodes else 0}")
                if results.edges:
                    for e in results.edges[:3]:
                        logger.info(f"  Edge: {e.fact}")
                if results.nodes:
                    for n in results.nodes[:3]:
                        logger.info(f"  Node: {n.name} - {n.summary}")
            except Exception as search_err:
                logger.error(f"Search_ exception: {search_err}", exc_info=True)
                raise

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

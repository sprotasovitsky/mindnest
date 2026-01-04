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
)

from .config import get_settings
from .llm import get_gemini_client

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

        # Get shared Gemini client
        genai_client = get_gemini_client()

        # Configure LLM client
        llm_config = LLMConfig(model=settings.llm_model)
        llm_client = GeminiClient(config=llm_config, client=genai_client)

        # Configure embedder (gemini-embedding-001: 3072 dimensions, 100+ languages)
        embedder_config = GeminiEmbedderConfig(
            embedding_model="gemini-embedding-001",
            embedding_dim=3072,
        )
        embedder = GeminiEmbedder(config=embedder_config, client=genai_client)

        # Configure cross-encoder/reranker
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

        # Preprocess message to explicitly include user name for better entity extraction
        # This helps Graphiti attribute purchases/tasks to the correct person
        processed_message = message
        if user_name:
            # Add user context at the beginning so Graphiti knows who is speaking
            processed_message = f"[Message from {user_name}]: {message}"

        logger.info(f"Adding episode for project {project_id}: {processed_message[:50]}...")

        try:
            result = await self.client.add_episode(
                name=f"msg_{user_id}_{ref_time.isoformat()}",
                episode_body=processed_message,
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

            results = await self.client.search_(
                query=query,
                group_ids=[project_id],
                config=config,
            )

            logger.info(
                f"Search results: edges={len(results.edges) if results.edges else 0}, "
                f"nodes={len(results.nodes) if results.nodes else 0}"
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
            return {"success": False, "error": str(e), "facts": [], "entities": []}

    async def get_context_for_response(
        self,
        query: str,
        project_id: str,
        max_facts: int = 20,
        max_entities: int = 10,
    ) -> dict:
        """Get context from knowledge graph for response generation.

        Args:
            query: User's question/message
            project_id: Project to search in
            max_facts: Maximum facts to include
            max_entities: Maximum entities to include

        Returns:
            Dict with facts and entities for LLM context
        """
        # Primary search with original query
        search_result = await self.search(query, project_id, limit=max_facts)

        all_facts = search_result.get("facts", []) if search_result["success"] else []
        all_entities = search_result.get("entities", []) if search_result["success"] else []

        # For debt/money questions, also search for expense facts
        query_lower = query.lower()
        if any(word in query_lower for word in ["owe", "debt", "even", "split", "settle"]):
            logger.info("Debt-related query detected, also searching for expenses")

            # Filter out unreliable "owes money" facts from primary search
            all_facts = [
                f for f in all_facts
                if "owes money" not in f["fact"].lower()
            ]

            expense_result = await self.search(
                "expenses spent rubles total", project_id, limit=max_facts
            )
            if expense_result["success"]:
                # Add expense facts, avoiding duplicates
                existing_facts = {f["fact"] for f in all_facts}
                for fact in expense_result["facts"]:
                    # Skip "owes money" facts - they're unreliable
                    if "owes money" in fact["fact"].lower():
                        continue
                    if fact["fact"] not in existing_facts:
                        all_facts.append(fact)
                        existing_facts.add(fact["fact"])

        # For task completion questions, also search for completed tasks
        if any(word in query_lower for word in ["completed", "done", "finished", "all tasks"]):
            logger.info("Task completion query detected, also searching for task status")
            task_result = await self.search(
                "task completed done assigned", project_id, limit=max_facts
            )
            if task_result["success"]:
                existing_facts = {f["fact"] for f in all_facts}
                for fact in task_result["facts"]:
                    if fact["fact"] not in existing_facts:
                        all_facts.append(fact)
                        existing_facts.add(fact["fact"])

        # Sort facts by created_at (newest first)
        all_facts.sort(key=lambda f: f.get("created_at") or "", reverse=True)

        return {
            "facts": all_facts[:max_facts],
            "entities": all_entities[:max_entities],
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

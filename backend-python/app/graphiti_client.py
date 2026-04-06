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

import time

from .config import get_settings
from .llm import get_gemini_client

logger = logging.getLogger(__name__)


def _lf_span(name: str, **kwargs):
    """Create a Langfuse span tied to the current request trace, or return None."""
    from .langfuse_client import get_langfuse
    from .context import current_trace_id
    lf = get_langfuse()
    trace_id = current_trace_id.get()
    if not lf or not trace_id:
        return None
    try:
        return lf.span(name=name, trace_id=trace_id, **kwargs)
    except Exception:
        return None


def _apply_graphiti_patches() -> None:
    """Monkey-patch graphiti-core 0.28.1 bugs.

    TODO: Remove after upstream merges our PRs:
      - https://github.com/getzep/graphiti/pull/1254 (update_communities unpacking)
      - https://github.com/getzep/graphiti/pull/1253 (label_propagation infinite loop)
    """
    import graphiti_core.graphiti as _graphiti_mod
    import graphiti_core.utils.maintenance.community_operations as _comm_mod
    from collections import defaultdict

    # --- Patch 1: fix update_communities semaphore_gather unpacking (PR #1254) ---
    # Original code: `communities, community_edges = await semaphore_gather(...)`
    # crashes with "too many values to unpack" when episode has != 2 nodes.
    _orig_source = "communities, community_edges = await semaphore_gather"
    import inspect
    _src = inspect.getsource(_graphiti_mod.Graphiti.add_episode)
    if _orig_source in _src:
        import graphiti_core.graphiti as _gm
        from graphiti_core.helpers import semaphore_gather
        from graphiti_core.utils.maintenance.community_operations import update_community

        _original_add_episode = _gm.Graphiti.add_episode

        async def _patched_add_episode(self, *args, **kwargs):
            # Temporarily disable update_communities, we'll do it ourselves
            orig_uc = kwargs.get("update_communities", False)
            kwargs["update_communities"] = False
            result = await _original_add_episode(self, *args, **kwargs)

            if orig_uc and result and result.nodes:
                community_results = await semaphore_gather(
                    *[
                        update_community(self.driver, self.llm_client, self.embedder, node)
                        for node in result.nodes
                    ],
                    max_coroutines=self.max_coroutines,
                )
                for comm_nodes, comm_edges in community_results:
                    result.communities.extend(comm_nodes)
                    result.community_edges.extend(comm_edges)

            return result

        _gm.Graphiti.add_episode = _patched_add_episode
        logger.warning("Applied patch: update_communities semaphore_gather unpacking (PR #1254)")
    else:
        logger.warning("Patch #1254 not needed: update_communities code already fixed")

    # --- Patch 2: fix label_propagation infinite loop (PR #1253) ---
    _orig_label_prop = _comm_mod.label_propagation

    def _patched_label_propagation(projection, max_iterations=30):
        community_map = {uuid: i for i, uuid in enumerate(projection.keys())}

        for iteration in range(max_iterations):
            no_change = True
            new_community_map = {}

            for uuid, neighbors in projection.items():
                curr_community = community_map[uuid]
                community_candidates = defaultdict(int)
                for neighbor in neighbors:
                    community_candidates[community_map[neighbor.node_uuid]] += neighbor.edge_count
                community_lst = [
                    (count, community) for community, count in community_candidates.items()
                ]
                community_lst.sort(reverse=True)
                candidate_rank, community_candidate = community_lst[0] if community_lst else (0, -1)
                if community_candidate != -1 and candidate_rank > 1:
                    new_community = community_candidate
                else:
                    new_community = max(community_candidate, curr_community)
                new_community_map[uuid] = new_community
                if new_community != curr_community:
                    no_change = False

            if no_change:
                logger.debug(f"Label propagation converged after {iteration + 1} iterations")
                break
            community_map = new_community_map
        else:
            logger.warning(
                f"Label propagation did not converge after {max_iterations} iterations, "
                f"returning best approximation"
            )

        community_cluster_map = defaultdict(list)
        for uuid, community in community_map.items():
            community_cluster_map[community].append(uuid)
        return [cluster for cluster in community_cluster_map.values()]

    _comm_mod.label_propagation = _patched_label_propagation
    logger.warning("Applied patch: label_propagation max iterations cap (PR #1253)")


_apply_graphiti_patches()


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

        # Use configurable model for entity extraction
        graphiti_model = settings.graphiti_model or settings.llm_model_pro
        logger.info(f"Using model for Graphiti: {graphiti_model}")

        genai_client = get_gemini_client(model=graphiti_model)
        llm_config = LLMConfig(model=graphiti_model)

        # Enable thinking for gemini-3+ models
        # NOTE: Graphiti's GeminiClient requires thinking_budget (not thinking_level)
        thinking_config = None
        if graphiti_model.startswith("gemini-3"):
            from google.genai import types
            thinking_config = types.ThinkingConfig(thinking_budget=1024)
            logger.info(f"Graphiti thinking enabled (budget=1024)")

        llm_client = GeminiClient(
            config=llm_config,
            client=genai_client,
            thinking_config=thinking_config,
        )

        # Embedder and cross-encoder use regional client (don't need global)
        regional_client = get_gemini_client()
        embedder_config = GeminiEmbedderConfig(
            embedding_model="gemini-embedding-001",
            embedding_dim=3072,
        )
        embedder = GeminiEmbedder(config=embedder_config, client=regional_client)

        cross_encoder = GeminiRerankerClient(config=llm_config, client=regional_client)

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

    @staticmethod
    def _load_extraction_instructions() -> str:
        """Load extraction instructions from prompt file."""
        from .prompts import load_prompt
        return load_prompt("extraction")

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

        logger.info(f"Adding episode: len={len(episode_body)} for project {project_id}")

        settings = get_settings()
        span = _lf_span(
            "graphiti_add_episode",
            input=episode_body[:500],
            metadata={"project_id": project_id, "user_id": user_id},
        )
        t_start = time.monotonic()

        try:
            result = await self.client.add_episode(
                name=f"msg_{user_id}_{ref_time.isoformat()}",
                episode_body=episode_body,
                source_description=source_description,
                reference_time=ref_time,
                group_id=project_id,
                custom_extraction_instructions=self._load_extraction_instructions(),
                update_communities=settings.auto_update_communities,
            )

            nodes_created = len(result.nodes) if result and result.nodes else 0
            edges_created = len(result.edges) if result and result.edges else 0
            if span:
                span.end(output={
                    "nodes_created": nodes_created,
                    "edges_created": edges_created,
                    "latency_ms": round((time.monotonic() - t_start) * 1000),
                })
            return {
                "success": True,
                "episode_id": result.episode.uuid if result and result.episode else None,
                "nodes_created": nodes_created,
                "edges_created": edges_created,
            }
        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            if span:
                span.end(output={"error": str(e)}, level="ERROR", status_message=str(e))
            return {"success": False, "error": str(e)}

    def _get_edge_config(self) -> EdgeSearchConfig:
        """Get standard edge search config without BFS (bm25 + cosine only)."""
        return EdgeSearchConfig(
            search_methods=[
                EdgeSearchMethod.bm25,
                EdgeSearchMethod.cosine_similarity,
                EdgeSearchMethod.bfs,
            ],
            reranker=EdgeReranker.rrf,
            bfs_max_depth=1,
        )

    def _get_node_config(self) -> NodeSearchConfig:
        """Get standard node search config with BFS depth=1."""
        return NodeSearchConfig(
            search_methods=[
                NodeSearchMethod.bm25,
                NodeSearchMethod.cosine_similarity,
                NodeSearchMethod.bfs,
            ],
            reranker=NodeReranker.rrf,
            bfs_max_depth=1,
        )

    def _format_edges(
        self,
        edges: list,
        uuid_to_name: dict | None = None,
        scores: list[float] | None = None,
    ) -> list[dict]:
        """Format edge results for API response."""
        uuid_to_name = uuid_to_name or {}
        scores = scores or []
        return [
            {
                "fact": edge.fact,
                "source_name": uuid_to_name.get(edge.source_node_uuid, ""),
                "target_name": uuid_to_name.get(edge.target_node_uuid, ""),
                "score": scores[i] if i < len(scores) else None,
                "is_active": edge.expired_at is None,
                "created_at": edge.created_at.isoformat() if edge.created_at else None,
                "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
                "expired_at": edge.expired_at.isoformat() if edge.expired_at else None,
            }
            for i, edge in enumerate(edges)
        ]

    def _format_nodes(self, nodes: list, scores: list[float] | None = None) -> list[dict]:
        """Format node results for API response."""
        scores = scores or []
        return [
            {
                "name": node.name,
                "summary": node.summary,
                "score": scores[i] if i < len(scores) else None,
                "created_at": node.created_at.isoformat() if node.created_at else None,
            }
            for i, node in enumerate(nodes)
        ]

    def _get_community_config(self) -> CommunitySearchConfig:
        """Get community search config with BM25 + cosine similarity and RRF reranking."""
        return CommunitySearchConfig(
            search_methods=[
                CommunitySearchMethod.bm25,
                CommunitySearchMethod.cosine_similarity,
            ],
            reranker=CommunityReranker.rrf,
        )

    def _format_communities(self, communities: list) -> list[dict]:
        """Format community results for API response."""
        return [
            {
                "name": community.name,
                "summary": community.summary,
            }
            for community in communities
            if community.summary  # Only include communities with actual summaries
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

        span = _lf_span("graphiti_search", input=query, metadata={"project_id": project_id, "limit": limit})
        t_start = time.monotonic()

        try:
            config = SearchConfig(
                edge_config=self._get_edge_config(),
                node_config=self._get_node_config(),
                community_config=self._get_community_config(),
                limit=limit,
            )

            results = await self.client.search_(
                query=query,
                group_ids=[project_id],
                config=config,
            )

            edges = results.edges or []
            edge_scores = results.edge_reranker_scores or []
            nodes = results.nodes or []
            node_scores = results.node_reranker_scores or []
            communities = results.communities or []

            logger.info(f"Found {len(edges)} edges, {len(nodes)} nodes, {len(communities)} communities")

            # Build uuid→name map: start from search nodes, then fill gaps from Neo4j
            uuid_to_name = {node.uuid: node.name for node in nodes}

            # Find edge UUIDs missing from nodes
            edge_uuids = set()
            for edge in edges:
                edge_uuids.add(edge.source_node_uuid)
                edge_uuids.add(edge.target_node_uuid)
            missing_uuids = edge_uuids - set(uuid_to_name.keys())

            if missing_uuids:
                neo4j_span = _lf_span("neo4j_entity_lookup", metadata={"missing_uuids": len(missing_uuids)})
                t_neo4j = time.monotonic()
                try:
                    records, _, _ = await self._client.driver.execute_query(
                        "MATCH (n:Entity) WHERE n.uuid IN $uuids RETURN n.uuid AS uuid, n.name AS name",
                        uuids=list(missing_uuids),
                    )
                    for record in records:
                        uuid_to_name[record["uuid"]] = record["name"]
                    if neo4j_span:
                        neo4j_span.end(output={"resolved": len(records), "latency_ms": round((time.monotonic() - t_neo4j) * 1000)})
                except Exception as e:
                    logger.warning(f"Failed to resolve edge entity names: {e}")
                    if neo4j_span:
                        neo4j_span.end(output={"error": str(e)}, level="ERROR")

            formatted = {
                "success": True,
                "edges": self._format_edges(edges, uuid_to_name, edge_scores),
                "nodes": self._format_nodes(nodes, node_scores),
                "communities": self._format_communities(communities),
            }
            if span:
                span.end(output={
                    "edges": len(edges),
                    "nodes": len(nodes),
                    "communities": len(communities),
                    "latency_ms": round((time.monotonic() - t_start) * 1000),
                })
            return formatted
        except Exception as e:
            logger.error(f"Search failed: {e}")
            if span:
                span.end(output={"error": str(e)}, level="ERROR", status_message=str(e))
            return {"success": False, "error": str(e), "edges": [], "nodes": [], "communities": []}

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

    async def delete_project_data(self, project_id: str) -> dict:
        """Delete all data for a project from Neo4j.

        Removes all entities, episodes, edges, and communities
        associated with the given project_id (group_id).
        """
        logger.info(f"Deleting all data for project: {project_id}")

        try:
            driver = self.client.driver

            async with driver.session() as session:
                # Delete all relationships and nodes with this group_id
                # Order matters: delete relationships first, then nodes
                queries = [
                    # Delete RELATES_TO edges
                    "MATCH ()-[r:RELATES_TO {group_id: $group_id}]->() DELETE r",
                    # Delete MENTIONS edges
                    "MATCH ()-[r:MENTIONS {group_id: $group_id}]->() DELETE r",
                    # Delete HAS_MEMBER edges for communities
                    "MATCH (c:Community {group_id: $group_id})-[r:HAS_MEMBER]->() DELETE r",
                    # Delete Entity nodes
                    "MATCH (n:Entity {group_id: $group_id}) DETACH DELETE n",
                    # Delete Episodic nodes
                    "MATCH (n:Episodic {group_id: $group_id}) DETACH DELETE n",
                    # Delete Community nodes
                    "MATCH (n:Community {group_id: $group_id}) DETACH DELETE n",
                ]

                for query in queries:
                    await session.run(query, group_id=project_id)

            logger.info(f"Successfully deleted all data for project: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to delete project data: {e}")
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

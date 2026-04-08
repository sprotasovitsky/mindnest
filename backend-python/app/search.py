"""Shared search functions used by both chat and MCP pipelines.

Provides iterative search with LLM-guided multi-hop traversal,
relevance scoring, and background graph processing.
"""

import asyncio
import re
import time as _time
from typing import Optional

import structlog

from .config import get_settings
from .graphiti_client import KnowledgeGraph, get_knowledge_graph, _lf_span
from .llm import generate_text
from .pending_cache import get_pending_cache
from .prompts import load_prompt

logger = structlog.get_logger(__name__)

ITERATIVE_SEARCH_MAX = get_settings().iterative_search_max
POOL_SIZE = 15  # Max facts in rolling pool


def pool_top(pool: dict[str, dict], size: int) -> dict[str, dict]:
    """Trim pool to top-N facts by RRF score."""
    scored = sorted(
        pool.items(),
        key=lambda kv: kv[1].get("score") or 0.0,
        reverse=True,
    )
    return dict(scored[:size])


async def search_multi(
    kg: KnowledgeGraph,
    queries: list[str],
    project_id: str,
    span_name: str = "search_multi",
) -> dict:
    """Run multi-query search, dedup by fact text keeping highest RRF score."""
    if not queries:
        return {"success": True, "edges": [], "nodes": [], "communities": []}

    if len(queries) == 1:
        return await kg.search(queries[0], project_id)

    span = _lf_span(span_name, input=queries, metadata={"query_count": len(queries)})
    t0 = _time.monotonic()

    tasks = [kg.search(q, project_id) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged_edges: dict[str, dict] = {}
    merged_nodes: dict[str, dict] = {}
    merged_communities: dict[str, dict] = {}
    any_success = False

    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"Search error: {r}")
            continue
        if not r.get("success"):
            continue
        any_success = True
        for edge in r.get("edges", []):
            existing = merged_edges.get(edge["fact"])
            if existing is None or (edge.get("score") or 0) > (existing.get("score") or 0):
                merged_edges[edge["fact"]] = edge
        for node in r.get("nodes", []):
            merged_nodes.setdefault(node["name"], node)
        for comm in r.get("communities", []):
            merged_communities.setdefault(comm["name"], comm)

    merged = {
        "success": any_success,
        "edges": list(merged_edges.values()),
        "nodes": list(merged_nodes.values()),
        "communities": list(merged_communities.values()),
    }
    if span:
        span.end(output={
            "edges": len(merged["edges"]),
            "nodes": len(merged["nodes"]),
            "latency_ms": round((_time.monotonic() - t0) * 1000),
        })
    return merged


def apply_relevance_scores(verdict: str, pool: dict[str, dict]) -> None:
    """Parse RELEVANCE section from verdict and update pool scores.

    Only updates scores — does NOT delete facts from pool to preserve
    entity names for subsequent search rounds.
    """
    if "RELEVANCE:" not in verdict:
        return

    relevance_section = verdict.split("RELEVANCE:", 1)[1]
    for stop in ("SEARCH_MORE:", "ANSWER:"):
        if stop in relevance_section:
            relevance_section = relevance_section.split(stop, 1)[0]

    scored: dict[str, int] = {}
    for line in relevance_section.strip().split("\n"):
        line = line.strip().lstrip("- ")
        match = re.search(r'(?:→|->)\s*(\d+)\s*$', line)
        if match:
            score = int(match.group(1))
            fact_part = line[:match.start()].strip().strip('"').strip("'").strip()
            if fact_part:
                scored[fact_part] = score

    if not scored:
        return

    updated = 0
    for _key, fact_dict in pool.items():
        fact_text = fact_dict.get("fact", "")
        for scored_text, score in scored.items():
            shorter, longer = (scored_text, fact_text) if len(scored_text) <= len(fact_text) else (fact_text, scored_text)
            if shorter in longer and len(shorter) / max(len(longer), 1) > 0.5:
                fact_dict["score"] = score / 100.0
                updated += 1
                break

    if updated:
        logger.info(f"Relevance scores: updated {updated}/{len(pool)} facts")


async def iterative_search(
    kg: KnowledgeGraph,
    project_id: str,
    question: str,
    initial_queries: list[str],
    trace_id: Optional[str] = None,
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    """Search with rolling pool of top-POOL_SIZE facts by RRF score.

    Returns: (edges, nodes, communities, all_queries)
    """
    settings = get_settings()
    all_queries = list(initial_queries)

    pool: dict[str, dict] = {}
    all_nodes: dict[str, dict] = {}
    all_communities: dict[str, dict] = {}

    def _merge_result(r: dict) -> None:
        for e in r.get("edges", []):
            existing = pool.get(e["fact"])
            if existing is None or (e.get("score") or 0) > (existing.get("score") or 0):
                pool[e["fact"]] = e
        for n in r.get("nodes", []):
            all_nodes[n["name"]] = n
        for c in r.get("communities", []):
            all_communities[c.get("name", "")] = c

    # Round 0: initial search
    result = await search_multi(kg, initial_queries, project_id, span_name="iterative_search_round_0")
    _merge_result(result)
    trimmed_pool = pool_top(pool, POOL_SIZE)
    logger.info(f"Round 0: {len(pool)} edges → pool={len(trimmed_pool)}, nodes={len(all_nodes)}")

    for iteration in range(ITERATIVE_SEARCH_MAX):
        pool_facts = list(trimmed_pool.values())
        facts_summary = "\n".join(
            f"- [{e.get('source_name', '?')}] → [{e.get('target_name', '?')}]: {e['fact']}"
            + (f" [{e['score']:.2f}]" if e.get('score') is not None else "")
            for e in pool_facts
        ) or "(none)"

        pool_entity_names: set[str] = set()
        for e in pool.values():
            if e.get("source_name"):
                pool_entity_names.add(e["source_name"])
            if e.get("target_name"):
                pool_entity_names.add(e["target_name"])

        top_nodes = sorted(
            all_nodes.values(),
            key=lambda n: n.get("score") or 0.0,
            reverse=True,
        )
        extra_names = [
            n["name"] for n in top_nodes
            if n["name"] not in pool_entity_names
        ][:max(0, 25 - len(pool_entity_names))]

        entity_names = ", ".join(sorted(pool_entity_names) + extra_names) if (pool_entity_names or extra_names) else "(none)"
        logger.info(f"Verdict round {iteration} entity_names: {entity_names[:300]}")

        previous_queries = ", ".join(all_queries)
        verdict_prompt = load_prompt("iterative_search").format(
            question=question,
            facts_summary=facts_summary,
            entity_names=entity_names,
            previous_queries=previous_queries,
        )

        try:
            verdict = await generate_text(
                verdict_prompt,
                model=settings.llm_model_pro,
                prompt_name="iterative_search",
                step=f"iterative_verdict_{iteration}",
                trace_id=trace_id,
            )
        except Exception as e:
            logger.warning(f"Verdict failed: {e}")
            break

        logger.info(f"Verdict round {iteration}: {verdict[:120]}")

        apply_relevance_scores(verdict, pool)
        trimmed_pool = pool_top(pool, POOL_SIZE)

        if "ANSWER:" in verdict:
            logger.info(f"Iterative search: done after round {iteration} (ANSWER)")
            break

        if "SEARCH_MORE:" not in verdict:
            break

        raw = verdict.split("SEARCH_MORE:", 1)[1].strip()
        new_queries = [q.strip() for q in raw.split("|") if q.strip()][:2]
        if not new_queries:
            break

        logger.info(f"Round {iteration + 1}: searching {new_queries}")
        all_queries.extend(new_queries)

        extra = await search_multi(kg, new_queries, project_id, span_name=f"iterative_search_round_{iteration + 1}")
        _merge_result(extra)
        trimmed_pool = pool_top(pool, POOL_SIZE)
        logger.info(f"Round {iteration + 1}: {len(pool)} edges → pool={len(trimmed_pool)}, nodes={len(all_nodes)}")

    return list(trimmed_pool.values()), list(all_nodes.values()), list(all_communities.values()), all_queries


async def add_to_graph_background(
    message_id: str,
    message: str,
    project_id: str,
    user_id: str,
    user_name: Optional[str],
    trace_id: Optional[str] = None,
) -> None:
    """Background task: add to graph, then remove from pending."""
    from .context import current_trace_id
    from .langfuse_client import get_langfuse
    bg_trace_id = f"{trace_id}-bg" if trace_id else None
    if bg_trace_id:
        current_trace_id.set(bg_trace_id)
        lf = get_langfuse()
        if lf:
            try:
                lf.trace(
                    id=bg_trace_id,
                    name="background_add_episode",
                    input=message[:200],
                    user_id=str(user_id),
                    session_id=f"{user_id}:{project_id}",
                    tags=["background", "graphiti"],
                    metadata={"parent_trace_id": trace_id, "message_id": message_id},
                )
            except Exception:
                pass

    cache = get_pending_cache()
    kg = await get_knowledge_graph()

    try:
        logger.info(f"Background: adding to graph {message_id[:8]}...")
        result = await kg.add_episode(
            message=message,
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
        )
        if result["success"]:
            logger.info(f"Background: completed {message_id[:8]}, nodes={result.get('nodes_created', 0)}")
        else:
            logger.warning(f"Background: failed {message_id[:8]}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Background: error {message_id[:8]}: {e}")
    finally:
        await cache.remove(project_id, message_id)
        logger.debug(f"Background: removed from pending {message_id[:8]}")


def format_context(
    edges: list[dict], nodes: list[dict], communities: list[dict] | None = None
) -> tuple[list[dict], list[dict], list[dict]]:
    """Format search results for LLM prompts."""
    facts = [{"fact": e["fact"], **e} for e in edges]
    entities = [{"name": n["name"], "summary": n["summary"], **n} for n in nodes]
    comm = communities or []
    return facts, entities, comm

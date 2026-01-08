# Graphiti Entity Summary Fix Proposal

## Problem

Entity summaries in Graphiti accumulate stale information because they are not updated when related edges are expired/contradicted.

### Root Cause

In `_extract_entity_summary()` (node_operations.py):
- Takes node's current summary + new episode content
- LLM combines them into updated summary
- **But**: LLM doesn't know which facts (edges) have been expired/contradicted

### Example

```
Timeline:
1. Message: "Boris is assigned to buy alcohol"
   → Edge created: "Boris assigned to buy alcohol"
   → Boris summary: "assigned to buy alcohol"

2. Message: "Boris bought alcohol for 14000 rubles"
   → Old edge gets expired_at timestamp (contradicted)
   → New edge: "Boris completed purchase, spent 14000"
   → Boris summary: "assigned to buy alcohol, completed purchase for 14000"
                     ↑ STALE INFO STILL HERE!
```

### Impact

- Calculations based on entity summaries are incorrect
- LLM sees conflicting information (planning vs actual)
- Users get wrong answers for aggregation queries

## Proposed Solution

### Files to Modify

1. **`graphiti_core/utils/maintenance/node_operations.py`**
2. **`graphiti_core/prompts/extract_nodes.py`**
3. **`graphiti_core/prompts/snippets.py`**

### Implementation

#### 1. node_operations.py - Add expired edges query

```python
async def _extract_entity_summary(
    llm_client: LLMClient,
    node: EntityNode,
    episode: EpisodicNode | None,
    previous_episodes: list[EpisodicNode] | None,
    should_summarize_node: NodeSummaryFilter | None,
    driver,      # NEW: Neo4j driver
    group_id,    # NEW: for scoping
) -> None:

    # NEW: Get expired edges related to this entity
    expired_edges = await get_expired_edges_for_entity(driver, node.uuid, group_id)

    context = {
        'node': {
            'summary': node.summary[:MAX_SUMMARY_CHARS],
            'name': node.name,
            'entity_types': node.labels,
            'attributes': node.attributes,
        },
        'episode_content': episode.content if episode else '',
        'previous_episodes': [ep.content for ep in (previous_episodes or [])],
        'expired_facts': [e.fact for e in expired_edges],  # NEW
    }

    # ... rest of function
```

#### 2. New helper function for expired edges

```python
async def get_expired_edges_for_entity(
    driver,
    entity_uuid: str,
    group_id: str,
    limit: int = 50
) -> list[EntityEdge]:
    """Get recently expired edges connected to this entity."""

    query = """
    MATCH (n:Entity {uuid: $uuid})-[r:RELATES_TO]-(m:Entity)
    WHERE r.group_id = $group_id
      AND r.expired_at IS NOT NULL
    RETURN r
    ORDER BY r.expired_at DESC
    LIMIT $limit
    """

    # Execute and return edges
    ...
```

#### 3. extract_nodes.py - Update prompt

```python
def extract_summary(context: dict[str, Any]) -> list[Message]:
    expired_facts_section = ""
    if context.get('expired_facts'):
        expired_facts_section = f"""
<EXPIRED_FACTS>
The following facts are NO LONGER VALID. Remove any related information from the summary:
{chr(10).join('- ' + fact for fact in context['expired_facts'])}
</EXPIRED_FACTS>
"""

    return [
        Message(
            role='system',
            content='You are a helpful assistant that extracts entity summaries from the provided text.',
        ),
        Message(
            role='user',
            content=f"""
Given the MESSAGES and the ENTITY, update the summary that combines relevant information
about the entity from the messages and relevant information from the existing summary.

IMPORTANT: If any information in the existing summary relates to expired facts listed below,
that information should be REMOVED or REPLACED with current information.

{summary_instructions}

{expired_facts_section}

<MESSAGES>
{to_prompt_json(context['previous_episodes'])}
{to_prompt_json(context['episode_content'])}
</MESSAGES>

<ENTITY>
{context['node']}
</ENTITY>
""",
        ),
    ]
```

#### 4. snippets.py - Add instruction

```python
summary_instructions = """
## Summary Guidelines

- Output only factual content
- Keep summary under 250 characters
- State facts directly without meta-commentary
- If information contradicts expired facts, use only the current information
- Remove outdated task assignments when tasks are completed
- For numeric values, use only the most recent confirmed values
"""
```

## Questions to Consider

1. **Performance**: Additional DB query per entity - acceptable?
2. **Scope**: All expired edges or only recently expired (last N episodes)?
3. **Edge cases**: What if expired edge fact text doesn't match summary text exactly?

## Alternative Approaches

### A. Rebuild summary from scratch

Instead of updating incrementally, periodically rebuild summaries using only non-expired edges:

```python
async def rebuild_entity_summary(node: EntityNode, driver, group_id):
    # Get ALL valid (non-expired) edges for this entity
    valid_edges = await get_valid_edges_for_entity(driver, node.uuid, group_id)

    # Generate summary from scratch using only valid edges
    context = {
        'node': {'name': node.name, ...},
        'valid_facts': [e.fact for e in valid_edges],
    }
    # Use different prompt that builds from facts, not updates existing
```

### B. Mark summary as stale

Add `summary_valid_until` field to entities, invalidate when related edge expires:

```python
class EntityNode:
    summary: str
    summary_valid_until: datetime | None  # Set to None when edge expires
```

## References

- Graphiti source: https://github.com/getzep/graphiti
- extract_nodes.py: prompts/extract_nodes.py
- node_operations.py: utils/maintenance/node_operations.py
- Related paper: https://arxiv.org/html/2501.13956v1

## Status

- [ ] Create GitHub issue
- [ ] Fork repository
- [ ] Implement changes
- [ ] Add tests
- [ ] Submit PR

"""Prompt management for MindNest.

This module handles loading and formatting prompts from external files.
Prompts are loaded from Langfuse (when configured) with fallback to .txt files.
All prompts are also stored as .txt files for development and version control.

Langfuse Prompt Management (Layer 6):
- Prompts stored in Langfuse UI with version history
- Production version fetched at runtime via Langfuse SDK
- Falls back to .txt files when Langfuse is unavailable
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Directory containing prompt files
PROMPTS_DIR = Path(__file__).parent

# Day names in English for LLM context
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_current_datetime_string() -> str:
    """Get formatted current date and time string for LLM context.

    Returns:
        Formatted string like "Friday, January 17, 2025 at 14:30 UTC"
    """
    now = datetime.now(timezone.utc)
    weekday = WEEKDAYS[now.weekday()]
    return now.strftime(f"{weekday}, %B %d, %Y at %H:%M UTC")


def _load_from_file(name: str) -> str:
    """Load a prompt from a local .txt file."""
    file_path = PROMPTS_DIR / f"{name}.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


@lru_cache(maxsize=10)
def load_prompt(name: str) -> str:
    """Load a prompt by name.

    Tries Langfuse first (production version), falls back to local .txt file.

    Args:
        name: Prompt name (without .txt extension), e.g. "classifier", "response"

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt file not found and Langfuse unavailable
    """
    from ..langfuse_client import get_langfuse
    lf = get_langfuse()
    if lf:
        try:
            prompt_obj = lf.get_prompt(name)
            # TextPromptClient exposes .prompt (str); fallback for future SDK changes
            return prompt_obj.prompt if hasattr(prompt_obj, "prompt") else str(prompt_obj)
        except Exception as e:
            logger.debug(f"Langfuse prompt '{name}' not found, using file: {e}")

    return _load_from_file(name)


async def sync_prompts_to_langfuse() -> None:
    """Push local .txt prompts to Langfuse if they don't exist there yet.

    Called once at application startup to seed Langfuse with current prompts.
    Only uploads prompts that don't already exist in Langfuse.
    """
    from ..langfuse_client import get_langfuse
    lf = get_langfuse()
    if not lf:
        return

    prompt_files = list(PROMPTS_DIR.glob("*.txt"))
    synced = 0
    for file_path in prompt_files:
        name = file_path.stem
        content = file_path.read_text(encoding="utf-8")
        try:
            # Try to get existing prompt — if it exists, skip
            lf.get_prompt(name)
        except Exception:
            # Doesn't exist yet — create it
            try:
                lf.create_prompt(
                    name=name,
                    prompt=content,
                    labels=["production"],
                )
                synced += 1
                logger.info(f"Synced prompt '{name}' to Langfuse")
            except Exception as e:
                logger.warning(f"Failed to sync prompt '{name}' to Langfuse: {e}")

    if synced:
        logger.info(f"Synced {synced} prompts to Langfuse")


def get_system_prompt() -> str:
    """Get the system prompt."""
    return load_prompt("system")


def get_context_guide() -> str:
    """Get the context interpretation guide."""
    return load_prompt("context_guide")


def get_response_template() -> str:
    """Get the response generation template."""
    return load_prompt("response")


def _format_facts_grouped(facts: list[dict], entities: list[dict]) -> str:
    """Group facts by entity, showing graph connections clearly.

    Output format:
    ## EntityName
    Summary: ... (if available)
    - → TargetEntity: fact text
    - ← SourceEntity: fact text
    """
    # Build entity summary lookup
    entity_summaries = {e["name"]: e.get("summary", "") for e in entities if e.get("name")}

    # Group facts by source and target entities
    entity_facts: dict[str, list[str]] = {}
    for f in facts:
        src = f.get("source_name") or "Unknown"
        tgt = f.get("target_name") or "Unknown"
        fact_text = f.get("fact", "")
        score = f.get("score")
        score_str = f" [{score:.2f}]" if score is not None else ""

        # Add to source entity
        entity_facts.setdefault(src, []).append(f"→ {tgt}: {fact_text}{score_str}")
        # Add to target entity (reverse direction)
        if tgt != src:
            entity_facts.setdefault(tgt, []).append(f"← {src}: {fact_text}{score_str}")

    # Sort entities: most connected first
    sorted_entities = sorted(
        [(name, fact_list) for name, fact_list in entity_facts.items() if name != "Unknown"],
        key=lambda x: len(x[1]),
        reverse=True,
    )

    lines = []
    for name, fact_lines in sorted_entities:
        summary = entity_summaries.get(name, "")
        lines.append(f"## {name}")
        if summary:
            lines.append(f"Summary: {summary}")
        # Deduplicate
        seen = set()
        for fl in fact_lines:
            if fl not in seen:
                seen.add(fl)
                lines.append(f"  - {fl}")
        lines.append("")

    # Append ungrouped facts (missing source/target names)
    if "Unknown" in entity_facts:
        lines.append("## (ungrouped facts)")
        seen = set()
        for fl in entity_facts["Unknown"]:
            if fl not in seen:
                seen.add(fl)
                lines.append(f"  - {fl}")
        lines.append("")

    return "\n".join(lines) if lines else "(no facts found)"


def _format_entities_standalone(entities: list[dict], facts: list[dict]) -> str:
    """Format entities that have summaries but no facts in the current result set."""
    # Find entities not mentioned in facts
    fact_names = set()
    for f in facts:
        fact_names.add(f.get("source_name", ""))
        fact_names.add(f.get("target_name", ""))

    orphan_entities = [e for e in entities if e.get("name") and e["name"] not in fact_names and e.get("summary")]
    if not orphan_entities:
        return "(all entities included in facts above)"

    lines = []
    for e in orphan_entities:
        lines.append(f"- {e['name']}: {e['summary']}")
    return "\n".join(lines)


def _format_communities_text(communities: list[dict] | None) -> str:
    """Format community summaries as text."""
    if not communities:
        return "(none)"
    lines = []
    for c in communities:
        if c.get("summary"):
            lines.append(f"- {c['name']}: {c['summary']}")
    return "\n".join(lines) if lines else "(none)"


def format_response_prompt(
    message: str,
    facts: list[dict],
    entities: list[dict],
    user_name: Optional[str] = None,
    project_id: Optional[str] = None,
    pending_context: str = "",
    chat_history: str = "",
    project_description: Optional[str] = None,
    communities: Optional[list[dict]] = None,
) -> str:
    """Format the full response prompt with context.

    Args:
        message: User's message
        facts: List of facts from knowledge graph
        entities: List of entities from knowledge graph
        user_name: Current user's name
        project_id: Current project ID
        pending_context: Recent messages not yet in graph
        chat_history: Formatted previous conversation history
        project_description: Project description for context
        communities: List of community summaries from knowledge graph

    Returns:
        Formatted prompt ready for LLM
    """
    # Separate facts into active (current) and superseded (expired) groups
    active_facts = [f for f in facts if f.get("is_active", True)]
    expired_facts = [f for f in facts if not f.get("is_active", True)]

    active_facts_text = _format_facts_grouped(active_facts, entities) if active_facts else "(no facts found)"
    expired_facts_text = _format_facts_grouped(expired_facts, []) if expired_facts else "(none)"
    entities_text = _format_entities_standalone(entities, active_facts) if entities else "(no entities found)"
    communities_text = _format_communities_text(communities) if communities else "(none)"

    # Load and format template
    template = get_response_template()

    return template.format(
        system_prompt=get_system_prompt(),
        context_guide=get_context_guide(),
        current_datetime=get_current_datetime_string(),
        active_facts_text=active_facts_text,
        expired_facts_text=expired_facts_text,
        entities_text=entities_text,
        communities_text=communities_text,
        user_name=user_name or "Anonymous",
        project_id=project_id or "Unknown",
        message=message,
        pending_context=pending_context,
        chat_history=chat_history if chat_history else "No previous messages in this session.",
        project_description=project_description or "No description provided yet.",
    )


def get_onboarding_template() -> str:
    """Get the onboarding prompt template."""
    return load_prompt("onboarding")


def format_onboarding_prompt(
    message: str,
    chat_history: str = "",
    user_name: Optional[str] = None,
) -> str:
    """Format the onboarding prompt.

    Args:
        message: User's current message
        chat_history: Formatted previous conversation history
        user_name: Current user's name

    Returns:
        Formatted prompt for onboarding flow
    """
    template = get_onboarding_template()

    return template.format(
        message=message,
        chat_history=chat_history if chat_history else "No previous messages.",
        user_name=user_name or "User",
    )


def clear_prompt_cache():
    """Clear the prompt cache (useful for development/testing)."""
    load_prompt.cache_clear()

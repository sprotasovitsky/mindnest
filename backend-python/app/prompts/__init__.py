"""Prompt management for MindNest.

This module handles loading and formatting prompts from external files.
All prompts are stored as .txt files for easy editing and version control.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache
from typing import Optional

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


@lru_cache(maxsize=10)
def load_prompt(name: str) -> str:
    """Load a prompt from a file.

    Args:
        name: Prompt name (without .txt extension)

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    file_path = PROMPTS_DIR / f"{name}.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    return file_path.read_text(encoding="utf-8")


def get_system_prompt() -> str:
    """Get the system prompt."""
    return load_prompt("system")


def get_context_guide() -> str:
    """Get the context interpretation guide."""
    return load_prompt("context_guide")


def get_response_template() -> str:
    """Get the response generation template."""
    return load_prompt("response")


def format_response_prompt(
    message: str,
    facts: list[dict],
    entities: list[dict],
    user_name: Optional[str] = None,
    project_id: Optional[str] = None,
    pending_context: str = "",
    chat_history: str = "",
    project_description: Optional[str] = None,
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

    Returns:
        Formatted prompt ready for LLM
    """
    # Pass raw data as JSON - let LLM interpret with full metadata
    facts_text = json.dumps(facts, indent=2, ensure_ascii=False) if facts else "[]"
    entities_text = json.dumps(entities, indent=2, ensure_ascii=False) if entities else "[]"

    # Load and format template
    template = get_response_template()

    return template.format(
        system_prompt=get_system_prompt(),
        context_guide=get_context_guide(),
        current_datetime=get_current_datetime_string(),
        facts_text=facts_text,
        entities_text=entities_text,
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

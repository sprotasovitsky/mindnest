"""Gemini-based answer synthesis for the MCP test.

Takes raw facts and entities from mcp/search and generates a concise answer
to the benchmark question using Vertex AI Gemini.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _build_synthesis_prompt(question: str, facts: list[dict], entities: list[dict]) -> str:
    """Build the synthesis prompt from search results."""
    parts = [
        "You are a helpful assistant. Answer the question using ONLY the facts provided below.",
        "If the facts do not contain enough information, say so briefly.",
        "",
        "Facts:",
    ]
    if facts:
        for f in facts:
            fact_text = f.get("fact", "")
            valid_at = f.get("valid_at")
            if valid_at:
                parts.append(f"  - {fact_text} (at {valid_at})")
            else:
                parts.append(f"  - {fact_text}")
    else:
        parts.append("  (none)")

    parts.append("")
    parts.append("Entities:")
    if entities:
        for e in entities:
            name = e.get("name", "")
            summary = e.get("summary", "")
            parts.append(f"  - {name}: {summary}" if summary else f"  - {name}")
    else:
        parts.append("  (none)")

    parts += [
        "",
        f"Question: {question}",
        "",
        "Answer concisely in one or two sentences:",
    ]
    return "\n".join(parts)


def synthesize_answer(
    question: str,
    facts: list[dict],
    entities: list[dict],
    model: str,
    vertex_project: str = "",
    vertex_location: str = "us-central1",
) -> str:
    """Call Gemini via Vertex AI and return the synthesized answer string."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
    except ImportError:
        raise RuntimeError(
            "vertexai package not installed. Run: pip install google-cloud-aiplatform"
        )

    project = vertex_project or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    location = vertex_location or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        raise RuntimeError(
            "Vertex AI project not set. Pass vertex_project in config or set "
            "GOOGLE_CLOUD_PROJECT environment variable."
        )

    vertexai.init(project=project, location=location)
    gemini = GenerativeModel(model)

    prompt = _build_synthesis_prompt(question, facts, entities)
    logger.debug(f"Synthesis prompt ({len(prompt)} chars) for question: {question[:80]}")

    response = gemini.generate_content(prompt)
    answer = response.text.strip()
    logger.debug(f"Synthesized answer: {answer[:120]}")
    return answer

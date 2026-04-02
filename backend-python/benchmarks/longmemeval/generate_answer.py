"""Gemini-based answer synthesis for the MCP test.

Takes raw facts and entities from mcp/search and generates a concise answer
to the benchmark question using google-genai (same client as the backend).

Reads Vertex AI credentials from the same env vars the backend uses:
  VERTEX_AI_PROJECT_ID, VERTEX_AI_LOCATION,
  GCP_SERVICE_ACCOUNT_EMAIL, GCP_PRIVATE_KEY
"""

import logging
import os
from typing import Optional

from google import genai
from google.genai import types
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None


def _get_client(vertex_project: str = "", vertex_location: str = "global") -> genai.Client:
    """Lazily create a Vertex AI Gemini client, reusing the backend's env vars."""
    global _client
    if _client is not None:
        return _client

    project = vertex_project or os.environ.get("VERTEX_AI_PROJECT_ID", "")
    location = vertex_location or os.environ.get("VERTEX_AI_LOCATION", "us-central1")
    sa_email = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL", "")
    private_key = os.environ.get("GCP_PRIVATE_KEY", "").replace("\\n", "\n")

    if not project or not sa_email or not private_key:
        raise RuntimeError(
            "Vertex AI credentials not set. Required env vars: "
            "VERTEX_AI_PROJECT_ID, GCP_SERVICE_ACCOUNT_EMAIL, GCP_PRIVATE_KEY"
        )

    credentials = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": project,
            "private_key": private_key,
            "client_email": sa_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    _client = genai.Client(
        vertexai=True,
        project=project,
        location=location,
        credentials=credentials,
    )
    logger.info(f"Gemini client initialised (project={project}, location={location})")
    return _client


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
    """Call Gemini via google-genai and return the synthesized answer string."""
    client = _get_client(vertex_project, vertex_location)

    prompt = _build_synthesis_prompt(question, facts, entities)
    logger.debug(f"Synthesis prompt ({len(prompt)} chars) for question: {question[:80]}")

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    answer = response.text.strip()
    logger.debug(f"Synthesized answer: {answer[:120]}")
    return answer

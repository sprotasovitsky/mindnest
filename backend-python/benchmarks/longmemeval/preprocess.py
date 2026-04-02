"""Preprocess LongMemEval sessions for MCP ingestion.

An LLM-client calling MCP is expected to decompose complex messages into
atomic facts before sending them via /mcp/message.  This module replicates
that step: for each user turn it asks Gemini to extract standalone facts,
then writes a new dataset JSON where each session turn is replaced with
the extracted facts.

Usage:
    source .env
    python -m benchmarks.longmemeval.preprocess \
        --input  data/longmemeval_s_cleaned.json \
        --output data/longmemeval_s_mcp.json \
        --limit 1          # process only the first instance
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """\
You are preparing messages for a knowledge graph that processes each message independently.

The graph extracts entities (people, items, dates, places) and facts
(relationships between entities). These become searchable later.

Extract all facts from the current message: personal details, events, tasks,
preferences, relationships, states — anything concrete.

IMPORTANT: Each fact must be self-contained. Use the conversation history to:
- Resolve pronouns: "She completed it" → "Maria completed the design task"
- Expand references: "Add 50 more" → "Add 50 more items to the grocery list"
- Include location/source/person from prior context when relevant

Write each fact in third person (use "User" as the subject).
Only include facts — not questions or advice requests.
If there are no facts, return exactly: NONE

Conversation history:
{history}

Current message:
{message}

Facts (one per line):"""

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    project = os.environ.get("VERTEX_AI_PROJECT_ID", "")
    location = "global"  # gemini-3 models require global endpoint
    sa_email = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL", "")
    private_key = os.environ.get("GCP_PRIVATE_KEY", "").replace("\\n", "\n")

    if not project or not sa_email or not private_key:
        raise RuntimeError("Vertex AI credentials not set")

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
    _client = genai.Client(vertexai=True, project=project, location=location, credentials=credentials)
    return _client


def extract_facts(message: str, history: str = "", model: str = "gemini-3.1-flash-lite-preview") -> list[str]:
    """Ask Gemini to extract atomic facts from a user message with conversation context."""
    client = _get_client()
    prompt = EXTRACT_PROMPT.format(message=message, history=history or "(no history)")

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
    )

    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            text = resp.text.strip()
            if text == "NONE" or not text:
                return []
            return [line.strip().lstrip("- ").lstrip("• ") for line in text.splitlines() if line.strip()]
        except Exception as e:
            if attempt < 2:
                logger.warning(f"Extraction failed, retrying: {e}")
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Extraction failed after 3 attempts: {e}")
                return []


def preprocess_instance(instance: dict, model: str = "gemini-3.1-flash-lite-preview") -> dict:
    """Replace user turns with extracted atomic facts, passing session context."""
    new_sessions = []
    total_original = 0
    total_facts = 0

    for s_idx, session in enumerate(instance["haystack_sessions"]):
        new_turns = []
        session_history: list[str] = []
        for turn in session:
            role = turn["role"]
            content = turn["content"]
            if role != "user":
                session_history.append(f"[assistant]: {content[:200]}")
                continue
            total_original += 1
            # Build history from previous turns in this session
            history = "\n".join(session_history[-10:])  # last 10 turns
            facts = extract_facts(content, history, model)
            for fact in facts:
                new_turns.append({"role": "user", "content": fact})
                total_facts += 1
            session_history.append(f"[user]: {content[:200]}")

        if new_turns:
            new_sessions.append(new_turns)

    logger.info(f"  Instance {instance.get('question_id', '?')}: "
                f"{total_original} user turns → {total_facts} atomic facts")

    result = dict(instance)
    result["haystack_sessions"] = new_sessions
    return result


def main():
    parser = argparse.ArgumentParser(description="Preprocess LongMemEval for MCP test")
    parser.add_argument("--input", required=True, help="Input dataset JSON")
    parser.add_argument("--output", required=True, help="Output dataset JSON")
    parser.add_argument("--model", default="gemini-3.1-flash-lite-preview")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    if args.limit:
        data = data[:args.limit]

    logger.info(f"Processing {len(data)} instances with {args.model}")

    results = []
    for i, inst in enumerate(data):
        logger.info(f"[{i+1}/{len(data)}] Instance {inst.get('question_id', '?')}")
        results.append(preprocess_instance(inst, args.model))

    with open(args.output, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"Done. Written to {args.output}")


if __name__ == "__main__":
    main()

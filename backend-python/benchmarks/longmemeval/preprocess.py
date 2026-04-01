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
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """\
Extract all personal facts about the user from the message below.
Return each fact as a separate line, written as a standalone statement in third person
(use "User" as the subject).
Only include facts the user explicitly states about themselves, their life,
preferences, plans, possessions, or experiences.
Do NOT include questions, advice requests, or assistant responses.
If there are no personal facts, return exactly: NONE

Message:
{message}

Facts (one per line):"""

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    project = os.environ.get("VERTEX_AI_PROJECT_ID", "")
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
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


def extract_facts(message: str, model: str = "gemini-2.5-flash") -> list[str]:
    """Ask Gemini to extract atomic facts from a user message."""
    client = _get_client()
    prompt = EXTRACT_PROMPT.format(message=message)

    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
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


def preprocess_instance(instance: dict, model: str = "gemini-2.5-flash") -> dict:
    """Replace user turns with extracted atomic facts."""
    new_sessions = []
    total_original = 0
    total_facts = 0

    for s_idx, session in enumerate(instance["haystack_sessions"]):
        new_turns = []
        for turn in session:
            if turn["role"] != "user":
                continue
            total_original += 1
            facts = extract_facts(turn["content"], model)
            for fact in facts:
                new_turns.append({"role": "user", "content": fact})
                total_facts += 1

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
    parser.add_argument("--model", default="gemini-2.5-flash")
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

"""MCP test — direct Graphiti path benchmark.

Data flow: POST /api/mcp/message → Graphiti (no classifier, no pending cache).
Question answered via: POST /api/mcp/search → raw facts → Gemini synthesis.
Tests retrieval quality in isolation.

Usage:
    python -m benchmarks.longmemeval.run_mcp_test \
        --email benchmark@example.com \
        --password secret \
        --vertex-project my-gcp-project \
        --limit 3          # smoke test

Output:
    results/mcp_hypothesis.jsonl  — one JSON line per instance:
    {"id": "...", "answer": "...", "question": "..."}
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx

from .auth import login_oauth_pkce, login_jwt
from .config import BenchmarkConfig
from .generate_answer import synthesize_answer
from .projects import create_project

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Description pre-set on project creation to bypass onboarding check in /mcp/message
MCP_PROJECT_DESCRIPTION = "Benchmark project for LongMemEval MCP test"


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> list[dict]:
    """Load LongMemEval dataset from a JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Dataset not found at {p}. "
            "Clone the LongMemEval submodule with: "
            "git submodule update --init --recursive"
        )
    with open(p) as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} instances from {p}")
    return data


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def mcp_send_message(
    api_url: str,
    token: str,
    project_id: str,
    message: str,
    retries: int = 3,
) -> dict:
    """POST /api/mcp/message. Returns response JSON."""
    url = f"{api_url}/api/mcp/message"
    payload = {"message": message, "project_id": project_id}
    backoff = 60
    for attempt in range(retries):
        try:
            resp = httpx.post(url, json=payload, headers=_headers(token), timeout=120)
            if resp.status_code == 429:
                wait = backoff * (attempt + 1)
                logger.warning(f"Rate limited — waiting {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if attempt < retries - 1:
                logger.warning(f"HTTP error {e.response.status_code}, retrying...")
                time.sleep(5)
            else:
                raise
    raise RuntimeError(f"mcp_send_message failed after {retries} attempts")


def mcp_search(
    api_url: str,
    token: str,
    project_id: str,
    query: str,
    retries: int = 3,
) -> dict:
    """POST /api/mcp/search. Returns dict with facts[] and entities[]."""
    url = f"{api_url}/api/mcp/search"
    payload = {"query": query, "project_id": project_id}
    backoff = 60
    for attempt in range(retries):
        try:
            resp = httpx.post(url, json=payload, headers=_headers(token), timeout=120)
            if resp.status_code == 429:
                wait = backoff * (attempt + 1)
                logger.warning(f"Rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if attempt < retries - 1:
                logger.warning(f"HTTP error {e.response.status_code}, retrying...")
                time.sleep(5)
            else:
                raise
    raise RuntimeError(f"mcp_search failed after {retries} attempts")


# ---------------------------------------------------------------------------
# Session ingestion
# ---------------------------------------------------------------------------

def _normalize_sessions(raw_sessions: list) -> list[list[dict]]:
    """Normalize session format (same as run_chat_test)."""
    out: list[list[dict]] = []
    for s in raw_sessions:
        if isinstance(s, dict) and "turns" in s:
            out.append(s["turns"])
        elif isinstance(s, list):
            out.append(s)
        else:
            out.append([s])
    return out


def ingest_sessions(
    api_url: str,
    token: str,
    project_id: str,
    sessions: list,
    inter_message_delay: float,
    inter_session_delay: float,
    short_turn_threshold: int,
) -> int:
    """Send all user-role turns to /api/mcp/message. Returns total messages sent."""
    normalized = _normalize_sessions(sessions)
    total_sent = 0
    for s_idx, turns in enumerate(normalized):
        prev_user_text = ""
        for t_idx, turn in enumerate(turns):
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role != "user":
                continue

            # Prepend context to bare short replies
            if prev_user_text and len(content.strip()) <= short_turn_threshold:
                message = f"[Context: {prev_user_text[:80]}] {content}"
            else:
                message = content

            mcp_send_message(api_url, token, project_id, message)
            total_sent += 1
            prev_user_text = content

            if t_idx < len(turns) - 1:
                time.sleep(inter_message_delay)

        if s_idx < len(normalized) - 1:
            time.sleep(inter_session_delay)

    return total_sent


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def _get_instance_id(instance: dict) -> str:
    return instance.get("question_id") or instance.get("id", "")


def run(config: BenchmarkConfig) -> None:
    dataset = load_dataset(config.dataset_path)
    if config.limit:
        dataset = dataset[:config.limit]

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "mcp_hypothesis.jsonl"

    # Resume support
    done_ids: set[str] = set()
    if output_path.exists():
        with open(output_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done_ids.add(json.loads(line)["id"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        logger.info(f"Resuming — {len(done_ids)} instances already done")

    # MCP requires OAuth token; JWT token is used for project creation
    jwt_token = login_jwt(config)
    mcp_token = login_oauth_pkce(config, scope="read write")

    with open(output_path, "a") as out_f:
        for idx, instance in enumerate(dataset):
            instance_id = _get_instance_id(instance) or str(idx)
            if instance_id in done_ids:
                logger.info(f"[{idx+1}/{len(dataset)}] Skipping {instance_id}")
                continue

            question = instance.get("question", "")
            sessions = instance.get("haystack_sessions") or instance.get("sessions", [])

            logger.info(
                f"[{idx+1}/{len(dataset)}] Instance {instance_id} — "
                f"{len(sessions)} sessions, question: {question[:80]}"
            )

            # Create project with description pre-set → bypasses onboarding check in /mcp/message
            project = create_project(
                api_url=config.api_url,
                token=jwt_token,
                name=f"bench-mcp-{instance_id}",
                description=MCP_PROJECT_DESCRIPTION,
            )
            project_id = project["id"]

            # Ingest all user-role turns via MCP
            total_msgs = ingest_sessions(
                api_url=config.api_url,
                token=mcp_token,
                project_id=project_id,
                sessions=sessions,
                inter_message_delay=config.inter_message_delay_seconds,
                inter_session_delay=config.inter_session_delay_seconds,
                short_turn_threshold=config.short_turn_threshold,
            )

            # Wait for Graphiti async processing
            wait_secs = min(
                config.graphiti_wait_base_seconds + config.graphiti_wait_per_message * total_msgs,
                config.graphiti_wait_max_seconds,
            )
            logger.info(f"Waiting {wait_secs:.0f}s for Graphiti to process {total_msgs} messages")
            time.sleep(wait_secs)

            # Search for relevant facts
            search_result = mcp_search(config.api_url, mcp_token, project_id, question)
            facts = search_result.get("facts", [])
            entities = search_result.get("entities", [])
            logger.info(f"  Search: {len(facts)} facts, {len(entities)} entities")

            # Synthesize answer via Gemini
            answer = synthesize_answer(
                question=question,
                facts=facts,
                entities=entities,
                model=config.gemini_model_for_synthesis,
                vertex_project=config.vertex_project,
                vertex_location=config.vertex_location,
            )

            record = {"id": instance_id, "answer": answer, "question": question}
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            logger.info(f"  → Answer: {answer[:120]}")

    logger.info(f"Done. Results written to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval MCP Test")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--email", required=True, help="Benchmark user email")
    parser.add_argument("--password", required=True, help="Benchmark user password")
    parser.add_argument("--mcp-client-id", default="mcp-benchmark-client")
    parser.add_argument("--vertex-project", default="", help="GCP project for Vertex AI")
    parser.add_argument("--dataset", help="Path to dataset JSON")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Max instances to process")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg = BenchmarkConfig(
        api_url=args.api_url,
        email=args.email,
        password=args.password,
        mcp_client_id=args.mcp_client_id,
        vertex_project=args.vertex_project,
        limit=args.limit,
    )
    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.output_dir:
        cfg.output_dir = args.output_dir
    run(cfg)

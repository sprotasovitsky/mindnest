"""Chat test — full production pipeline benchmark.

Data flow: POST /api/chat → classifier → pending cache → Graphiti → LLM response.
Tests the real end-user experience.

Usage:
    python -m benchmarks.longmemeval.run_chat_test \
        --email benchmark@example.com \
        --password secret \
        --limit 3          # smoke test with 3 instances

Output:
    results/chat_hypothesis.jsonl  — one JSON line per instance:
    {"id": "...", "answer": "...", "question": "..."}
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx

from .auth import login_jwt
from .config import BenchmarkConfig
from .projects import create_project, get_project

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


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


def send_chat(api_url: str, token: str, project_id: str, message: str, retries: int = 3) -> dict:
    """POST /api/chat and return the response JSON. Handles 429 with backoff."""
    url = f"{api_url}/api/chat"
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
    raise RuntimeError(f"Failed after {retries} attempts")


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

def wait_for_onboarding(
    api_url: str, token: str, project_id: str, seed_message: str, max_attempts: int = 10
) -> None:
    """Send seed message and poll until project has a description (onboarding done)."""
    logger.info(f"Starting onboarding for project {project_id}")
    for attempt in range(max_attempts):
        resp = send_chat(api_url, token, project_id, seed_message)
        message_type = resp.get("message_type", "")
        if message_type != "ONBOARDING":
            logger.info(f"Onboarding complete (message_type={message_type!r})")
            return
        # Confirm by checking project description
        project = get_project(api_url, token, project_id)
        if project.get("description"):
            logger.info("Onboarding complete — project has description")
            return
        logger.info(f"Still onboarding (attempt {attempt + 1}/{max_attempts}), continuing...")
    raise RuntimeError(f"Onboarding did not complete after {max_attempts} attempts")


# ---------------------------------------------------------------------------
# Session ingestion
# ---------------------------------------------------------------------------

def _build_context_prepend(prev_turn: str, threshold: int = 30) -> str:
    """Return a prepend string for short turns to provide context."""
    stripped = prev_turn.strip()
    if len(stripped) <= threshold:
        return stripped
    return ""


def ingest_sessions(
    api_url: str,
    token: str,
    project_id: str,
    sessions: list[dict],
    inter_message_delay: float,
    inter_session_delay: float,
    short_turn_threshold: int,
) -> int:
    """Send all user-role turns to /api/chat. Returns total messages sent."""
    total_sent = 0
    for s_idx, session in enumerate(sessions):
        turns = session.get("turns", [])
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

            send_chat(api_url, token, project_id, message)
            total_sent += 1
            prev_user_text = content

            if t_idx < len(turns) - 1:
                time.sleep(inter_message_delay)

        if s_idx < len(sessions) - 1:
            time.sleep(inter_session_delay)

    return total_sent


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def run(config: BenchmarkConfig) -> None:
    dataset = load_dataset(config.dataset_path)
    if config.limit:
        dataset = dataset[:config.limit]

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chat_hypothesis.jsonl"

    # Determine which instances are already done (for resuming interrupted runs)
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

    token = login_jwt(config)

    with open(output_path, "a") as out_f:
        for idx, instance in enumerate(dataset):
            instance_id = instance.get("id", str(idx))
            if instance_id in done_ids:
                logger.info(f"[{idx+1}/{len(dataset)}] Skipping already-done instance {instance_id}")
                continue

            question = instance.get("question", "")
            sessions = instance.get("sessions", [])

            logger.info(
                f"[{idx+1}/{len(dataset)}] Instance {instance_id} — "
                f"{len(sessions)} sessions, question: {question[:80]}"
            )

            # Create a fresh project per instance
            project = create_project(
                api_url=config.api_url,
                token=token,
                name=f"bench-chat-{instance_id}",
            )
            project_id = project["id"]

            # Complete onboarding before any data messages
            wait_for_onboarding(
                config.api_url, token, project_id, config.onboarding_seed_message
            )

            # Ingest all user-role turns
            total_msgs = ingest_sessions(
                api_url=config.api_url,
                token=token,
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

            # Ask the benchmark question
            chat_resp = send_chat(config.api_url, token, project_id, question)
            answer = chat_resp.get("reply", "")

            record = {"id": instance_id, "answer": answer, "question": question}
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            logger.info(f"  → Answer: {answer[:120]}")

    logger.info(f"Done. Results written to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval Chat Test")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--email", required=True, help="Benchmark user email")
    parser.add_argument("--password", required=True, help="Benchmark user password")
    parser.add_argument("--dataset", help="Path to dataset JSON (default: config)")
    parser.add_argument("--output-dir", help="Output directory (default: results/)")
    parser.add_argument("--limit", type=int, default=None, help="Max instances to process")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg = BenchmarkConfig(
        api_url=args.api_url,
        email=args.email,
        password=args.password,
        limit=args.limit,
    )
    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.output_dir:
        cfg.output_dir = args.output_dir
    run(cfg)

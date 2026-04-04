"""Quick single-question test against an existing project.

Usage:
    source .env
    python -m benchmarks.longmemeval.test_single \
        --project-id b8c2597c-36df-4743-bb45-6f16da3bfdce \
        --question "Where did I redeem a $5 coupon on coffee creamer?"

What it does:
    1. Clears chat history for the project (so previous answers don't contaminate)
    2. Sends the question via /api/chat
    3. Prints the answer + debug context
    4. Saves timestamped log to benchmarks/longmemeval/logs/single_<timestamp>.log
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import asyncpg
import httpx

from .auth import login_jwt
from .config import BenchmarkConfig

LOGS_DIR = Path(__file__).parent / "logs"
EMAIL = "benchmark2@mindnest.one"
PASSWORD = "BenchmarkPass123!"
DB_DSN = "postgresql://mindnest:mindnest@localhost:5432/mindnest"


async def clear_chat_history_async(project_id: str) -> int:
    """Delete chat_messages for this project via asyncpg."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        result = await conn.execute(
            "DELETE FROM chat_messages WHERE project_id = $1", project_id
        )
        # result is like "DELETE 3"
        count = int(result.split()[-1])
        return count
    finally:
        await conn.close()


def clear_chat_history(project_id: str) -> int:
    return asyncio.run(clear_chat_history_async(project_id))


def ask_question(api_url: str, token: str, project_id: str, question: str) -> dict:
    resp = httpx.post(
        f"{api_url}/api/chat",
        json={"message": question, "project_id": project_id},
        headers={"Authorization": f"Bearer {token}"},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def run(project_id: str, question: str, api_url: str = "http://localhost:8000") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"single_{ts}.log"

    # Find latest backend log to tail
    backend_logs = sorted(LOGS_DIR.glob("backend_pool_*.log"), key=lambda p: p.stat().st_mtime)
    backend_log = backend_logs[-1] if backend_logs else None

    lines = []
    def log(msg: str) -> None:
        print(msg)
        lines.append(msg)

    log(f"=== SINGLE QUESTION TEST {ts} ===")
    log(f"Project: {project_id}")
    log(f"Question: {question}")
    log("")

    # 1. Clear history
    log("--- Step 1: Clear chat history ---")
    deleted = clear_chat_history(project_id)
    log(f"Deleted {deleted} messages")
    log("")

    # 2. Login
    cfg = BenchmarkConfig(api_url=api_url, email=EMAIL, password=PASSWORD)
    token = login_jwt(cfg)

    # 3. Snapshot backend log position before request
    backend_start_pos = 0
    if backend_log and backend_log.exists():
        backend_start_pos = backend_log.stat().st_size

    # 4. Ask question
    log("--- Step 2: Ask question ---")
    t0 = time.time()
    result = ask_question(api_url, token, project_id, question)
    elapsed = time.time() - t0

    reply = result.get("reply", "")
    debug = result.get("debug_context", {})

    log(f"REPLY: {reply}")
    log(f"Elapsed: {elapsed:.1f}s")
    log("")
    log("--- Debug context ---")
    log(json.dumps(debug, indent=2))
    log("")

    # 5. Capture backend logs since request started
    if backend_log and backend_log.exists():
        with open(backend_log) as f:
            f.seek(backend_start_pos)
            backend_lines = f.read()
        log("--- Backend log (this request) ---")
        log(backend_lines)

    # 6. Save to log file
    with open(log_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n[LOG] Saved to {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Single question test")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()
    run(args.project_id, args.question, args.api_url)


if __name__ == "__main__":
    main()

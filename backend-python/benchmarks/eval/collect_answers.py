"""Collect answers from the running MindNest backend for evaluation.

Reads LongMemEval questions, queries /api/chat, and collects:
- input (question)
- actual_output (model answer)
- expected_output (ground truth from dataset)
- retrieval_context (facts returned — approximated from response debug_context)

Usage:
    python -m benchmarks.eval.collect_answers \
        --email benchmark@example.com \
        --password BenchmarkPass123! \
        --project-id <project_id> \
        --output benchmarks/eval/results/answers.json
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

from .config import API_BASE_URL, DATASET_PATH, REGRESSION_QUESTION_IDS


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    """Login and return JWT token."""
    resp = await client.post(
        f"{API_BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def ask_question(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    question: str,
) -> dict:
    """Send a question to /api/chat and return the response."""
    resp = await client.post(
        f"{API_BASE_URL}/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": question, "projectId": project_id},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()


async def collect(
    email: str,
    password: str,
    project_id: str,
    output_path: str,
    question_ids: list[str] | None = None,
) -> list[dict]:
    """Collect answers for evaluation questions from the running backend."""
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    ids_to_run = set(question_ids or REGRESSION_QUESTION_IDS)
    instances = [d for d in dataset if d["question_id"] in ids_to_run]

    if not instances:
        raise ValueError(f"No matching question IDs found in dataset. Requested: {ids_to_run}")

    async with httpx.AsyncClient() as client:
        token = await login(client, email, password)
        print(f"Logged in as {email}")

        results = []
        for inst in instances:
            qid = inst["question_id"]
            question = inst["question"]
            expected = inst.get("answer", "")

            print(f"  Asking [{qid}]: {question[:80]}...")
            try:
                t0 = time.monotonic()
                response = await ask_question(client, token, project_id, question)
                elapsed = time.monotonic() - t0

                results.append({
                    "question_id": qid,
                    "input": question,
                    "actual_output": response.get("reply", ""),
                    "expected_output": expected,
                    "latency_s": round(elapsed, 2),
                    "message_type": response.get("message_type", ""),
                    "sources": response.get("sources", []),
                })
                print(f"    Done in {elapsed:.1f}s")
            except Exception as e:
                print(f"    ERROR: {e}")
                results.append({
                    "question_id": qid,
                    "input": question,
                    "actual_output": "",
                    "expected_output": expected,
                    "error": str(e),
                })

            await asyncio.sleep(2)  # Rate limit

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} answers to {output_path}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--output", default="benchmarks/eval/results/answers.json")
    parser.add_argument("--question-ids", nargs="*")
    args = parser.parse_args()

    asyncio.run(collect(
        email=args.email,
        password=args.password,
        project_id=args.project_id,
        output_path=args.output,
        question_ids=args.question_ids,
    ))


if __name__ == "__main__":
    main()

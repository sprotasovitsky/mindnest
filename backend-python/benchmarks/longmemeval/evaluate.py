"""Evaluation wrapper for LongMemEval benchmark.

Wraps the upstream evaluate_qa.py script from the LongMemEval repository.
Expects JSONL hypothesis file with {"id": "...", "answer": "..."} per line.

Usage:
    python -m benchmarks.longmemeval.evaluate \
        --hypothesis results/chat_hypothesis.jsonl

    python -m benchmarks.longmemeval.evaluate \
        --hypothesis results/mcp_hypothesis.jsonl \
        --label "MCP test"
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Expected location of the cloned LongMemEval repository (git submodule)
LONGMEMEVAL_REPO = Path(__file__).parent / "data" / "longmemeval"
EVALUATE_SCRIPT = LONGMEMEVAL_REPO / "src" / "evaluate_qa.py"


def _check_prerequisites(hypothesis_path: Path) -> None:
    if not hypothesis_path.exists():
        raise FileNotFoundError(f"Hypothesis file not found: {hypothesis_path}")

    if not EVALUATE_SCRIPT.exists():
        raise FileNotFoundError(
            f"LongMemEval evaluate_qa.py not found at {EVALUATE_SCRIPT}.\n"
            "Run: git submodule update --init --recursive"
        )


def _validate_hypothesis_keys(hypothesis_path: Path) -> None:
    """Verify all lines have the 'answer' key expected by evaluate_qa.py."""
    issues = []
    with open(hypothesis_path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                issues.append(f"  line {i}: invalid JSON — {e}")
                continue
            if "answer" not in obj:
                issues.append(f"  line {i}: missing 'answer' key (keys: {list(obj.keys())})")
            if "id" not in obj:
                issues.append(f"  line {i}: missing 'id' key")
    if issues:
        logger.warning(f"Hypothesis file has {len(issues)} validation issue(s):\n" + "\n".join(issues))


def run_evaluation(
    hypothesis_path: Path,
    label: str = "",
    extra_args: list[str] | None = None,
) -> None:
    """Run evaluate_qa.py on the hypothesis file and print results."""
    _check_prerequisites(hypothesis_path)
    _validate_hypothesis_keys(hypothesis_path)

    cmd = [
        sys.executable,
        str(EVALUATE_SCRIPT),
        "--hypothesis", str(hypothesis_path),
    ]
    if extra_args:
        cmd.extend(extra_args)

    tag = f"[{label}] " if label else ""
    logger.info(f"{tag}Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        logger.error(f"evaluate_qa.py exited with code {result.returncode}")
        sys.exit(result.returncode)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval Evaluation Wrapper")
    parser.add_argument(
        "--hypothesis",
        required=True,
        help="Path to hypothesis JSONL file (output of run_chat_test.py or run_mcp_test.py)",
    )
    parser.add_argument("--label", default="", help="Label for logging (e.g. 'Chat test')")
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Extra arguments forwarded to evaluate_qa.py",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s — %(message)s",
    )
    args = _parse_args()
    run_evaluation(
        hypothesis_path=Path(args.hypothesis),
        label=args.label,
        extra_args=args.extra or None,
    )

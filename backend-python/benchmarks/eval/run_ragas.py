"""Ragas evaluation for MindNest RAG pipeline (Layer 7).

Metrics evaluated:
- answer_relevancy: how relevant is the answer to the question?
- faithfulness: is the answer grounded in the retrieved context?
- context_recall: how much of the ground truth is covered by retrieved context?

Reads pre-collected answers from benchmarks/eval/results/answers.json.
Run collect_answers.py first to populate that file.

Usage:
    python -m benchmarks.eval.run_ragas \
        --answers benchmarks/eval/results/answers.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import (
    MIN_ANSWER_RELEVANCY,
    MIN_CONTEXT_RECALL,
    MIN_FAITHFULNESS,
    RESULTS_DIR,
)


def run_ragas(answers_path: str) -> dict:
    """Run Ragas metrics on collected answers."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_recall, faithfulness

    with open(answers_path) as f:
        answers = json.load(f)

    # Filter out errored answers
    valid = [a for a in answers if a.get("actual_output") and not a.get("error")]
    if not valid:
        print("No valid answers to evaluate.")
        return {"error": "no_valid_answers"}

    print(f"Evaluating {len(valid)} answers with Ragas...")

    # Build Ragas dataset format
    data = {
        "question": [a["input"] for a in valid],
        "answer": [a["actual_output"] for a in valid],
        "contexts": [
            a.get("sources", [a["actual_output"]]) for a in valid
        ],
        "ground_truth": [a.get("expected_output", "") for a in valid],
    }

    dataset = Dataset.from_dict(data)

    metrics = [answer_relevancy, faithfulness, context_recall]
    result = evaluate(dataset, metrics=metrics)

    scores = {
        "answer_relevancy": round(float(result["answer_relevancy"]), 3),
        "faithfulness": round(float(result["faithfulness"]), 3),
        "context_recall": round(float(result["context_recall"]), 3),
    }

    # Check thresholds
    passed = (
        scores["answer_relevancy"] >= MIN_ANSWER_RELEVANCY
        and scores["faithfulness"] >= MIN_FAITHFULNESS
        and scores["context_recall"] >= MIN_CONTEXT_RECALL
    )

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(valid),
        "scores": scores,
        "thresholds": {
            "answer_relevancy": MIN_ANSWER_RELEVANCY,
            "faithfulness": MIN_FAITHFULNESS,
            "context_recall": MIN_CONTEXT_RECALL,
        },
        "passed": passed,
    }

    print("\n=== Ragas Results ===")
    for metric, score in scores.items():
        threshold = report["thresholds"][metric]
        status = "✓" if score >= threshold else "✗"
        print(f"  {status} {metric}: {score:.3f} (threshold: {threshold})")
    print(f"Overall: {'PASS' if passed else 'FAIL'}")

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--answers",
        default="benchmarks/eval/results/answers.json",
        help="Path to collected answers JSON file",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for report JSON",
    )
    args = parser.parse_args()

    if not Path(args.answers).exists():
        print(f"Answers file not found: {args.answers}")
        print("Run collect_answers.py first.")
        sys.exit(1)

    report = run_ragas(args.answers)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = args.output or f"{RESULTS_DIR}/ragas_{ts}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {out_path}")

    # Exit 1 if below thresholds (for CI)
    if not report.get("passed", True):
        sys.exit(1)


if __name__ == "__main__":
    main()

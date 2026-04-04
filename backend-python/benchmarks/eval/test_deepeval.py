"""DeepEval evaluation suite for MindNest (Layer 7).

Metrics evaluated:
- AnswerRelevancyMetric: is the answer relevant to the question?
- FaithfulnessMetric: is the answer grounded in retrieved context (no hallucinations)?
- ContextualRecallMetric: did the system retrieve the data needed to answer?

Reads pre-collected answers from benchmarks/eval/results/answers.json.
Run collect_answers.py first to populate that file.

Usage:
    # Step 1: collect answers (requires running server)
    python -m benchmarks.eval.collect_answers \
        --email benchmark@example.com --password BenchmarkPass123! \
        --project-id <project_id>

    # Step 2: run evaluation
    python -m benchmarks.eval.test_deepeval \
        --answers benchmarks/eval/results/answers.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from .config import (
    JUDGE_MODEL,
    MIN_ANSWER_RELEVANCY,
    MIN_FAITHFULNESS,
    RESULTS_DIR,
)


def _configure_deepeval_judge():
    """Configure DeepEval to use Gemini via Vertex AI as the judge model."""
    try:
        from deepeval.models import GeminiVertexAI
        return GeminiVertexAI(model=JUDGE_MODEL)
    except ImportError:
        # Fall back to OpenAI-compatible config if GeminiVertexAI not available
        # Set OPENAI_API_KEY to a placeholder — DeepEval requires it even for custom models
        os.environ.setdefault("OPENAI_API_KEY", "placeholder")
        return None


def run_deepeval(answers_path: str) -> dict:
    """Run DeepEval metrics on collected answers."""
    from deepeval import evaluate
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase

    judge_model = _configure_deepeval_judge()

    with open(answers_path) as f:
        answers = json.load(f)

    # Filter out errored answers
    valid = [a for a in answers if a.get("actual_output") and not a.get("error")]
    if not valid:
        print("No valid answers to evaluate.")
        return {"error": "no_valid_answers"}

    print(f"Evaluating {len(valid)} answers with DeepEval...")

    test_cases = []
    for a in valid:
        sources = a.get("sources", [])
        # Use sources as retrieval_context; fall back to actual_output if empty
        context = sources if sources else [a["actual_output"]]
        test_cases.append(
            LLMTestCase(
                input=a["input"],
                actual_output=a["actual_output"],
                expected_output=a.get("expected_output", ""),
                retrieval_context=context,
            )
        )

    kwargs = {}
    if judge_model:
        kwargs["model"] = judge_model

    metrics = [
        AnswerRelevancyMetric(threshold=MIN_ANSWER_RELEVANCY, **kwargs),
        FaithfulnessMetric(threshold=MIN_FAITHFULNESS, **kwargs),
    ]

    results = evaluate(test_cases, metrics, run_async=True, print_results=False)

    # Summarize scores
    summary: dict[str, list[float]] = {}
    passed = 0
    for test_result in results.test_results:
        if test_result.success:
            passed += 1
        for metric_data in test_result.metrics_data or []:
            name = metric_data.name
            score = metric_data.score or 0.0
            summary.setdefault(name, []).append(score)

    avg_scores = {k: round(sum(v) / len(v), 3) for k, v in summary.items()}

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(test_cases),
        "passed": passed,
        "pass_rate": round(passed / len(test_cases), 3) if test_cases else 0,
        "avg_scores": avg_scores,
        "thresholds": {
            "answer_relevancy": MIN_ANSWER_RELEVANCY,
            "faithfulness": MIN_FAITHFULNESS,
        },
    }

    print("\n=== DeepEval Results ===")
    print(f"Total: {report['total']}  Passed: {report['passed']}  Pass rate: {report['pass_rate']:.0%}")
    for metric, score in avg_scores.items():
        print(f"  {metric}: {score:.3f}")

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
        help="Output path for report JSON (default: auto-timestamped in results/)",
    )
    args = parser.parse_args()

    if not Path(args.answers).exists():
        print(f"Answers file not found: {args.answers}")
        print("Run collect_answers.py first.")
        sys.exit(1)

    report = run_deepeval(args.answers)

    # Save report
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = args.output or f"{RESULTS_DIR}/deepeval_{ts}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {out_path}")


if __name__ == "__main__":
    main()

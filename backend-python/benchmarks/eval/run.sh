#!/bin/bash
# Evaluation pipeline runner (Layer 7)
#
# Prerequisites:
#   1. Running MindNest backend (uvicorn app.main:app --port 8000)
#   2. Benchmark project created and filled with data
#   3. Python env with requirements.txt installed
#
# Usage:
#   cd backend-python
#   EMAIL=... PASSWORD=... PROJECT_ID=... bash benchmarks/eval/run.sh

set -e

EMAIL="${EMAIL:-benchmark@example.com}"
PASSWORD="${PASSWORD:-BenchmarkPass123!}"
PROJECT_ID="${PROJECT_ID:?PROJECT_ID is required}"
ANSWERS="benchmarks/eval/results/answers_$(date +%Y%m%d_%H%M%S).json"

echo "=== Step 1: Collect answers from backend ==="
python -m benchmarks.eval.collect_answers \
    --email "$EMAIL" \
    --password "$PASSWORD" \
    --project-id "$PROJECT_ID" \
    --output "$ANSWERS"

echo ""
echo "=== Step 2: DeepEval evaluation ==="
python -m benchmarks.eval.test_deepeval --answers "$ANSWERS"

echo ""
echo "=== Step 3: Ragas evaluation ==="
python -m benchmarks.eval.run_ragas --answers "$ANSWERS"

echo ""
echo "=== Done. Results saved to benchmarks/eval/results/ ==="

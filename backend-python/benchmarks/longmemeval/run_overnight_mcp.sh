#!/bin/bash
# Wait for preprocessing to finish, then run MCP test
set -a && source /Users/siarheipratasavitski/Projects/MindNest/backend-python/.env && set +a
PYTHON=/Users/siarheipratasavitski/Projects/MindNest/backend-python/venv/bin/python3

PREPROCESS_PID=$1
DATA_FILE="benchmarks/longmemeval/data/longmemeval_s_mcp_30.json"

echo "Waiting for preprocessing (PID $PREPROCESS_PID) to finish..."
while kill -0 "$PREPROCESS_PID" 2>/dev/null; do
    sleep 60
done
echo "Preprocessing done. Starting MCP test..."

if [ ! -f "$DATA_FILE" ]; then
    echo "ERROR: $DATA_FILE not found"
    exit 1
fi

rm -f benchmarks/longmemeval/results/mcp_hypothesis.jsonl

$PYTHON -m benchmarks.longmemeval.run_mcp_test \
  --email "benchmark2@mindnest.one" \
  --password "BenchmarkPass123!" \
  --dataset "$DATA_FILE" \
  --limit 30

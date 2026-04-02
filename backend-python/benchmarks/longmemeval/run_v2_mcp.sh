#!/bin/bash
set -a && source /Users/siarheipratasavitski/Projects/MindNest/backend-python/.env && set +a
PYTHON=/Users/siarheipratasavitski/Projects/MindNest/backend-python/venv/bin/python3
PREPROCESS_PID=$1
DATA_FILE="benchmarks/longmemeval/data/longmemeval_s_mcp_17_v2.json"

echo "Waiting for preprocessing (PID $PREPROCESS_PID)..."
while kill -0 "$PREPROCESS_PID" 2>/dev/null; do
    sleep 30
done
echo "Preprocessing done. Starting MCP test..."

$PYTHON -m benchmarks.longmemeval.run_mcp_test \
  --email "benchmark2@mindnest.one" \
  --password "BenchmarkPass123!" \
  --dataset "$DATA_FILE" \
  --limit 17

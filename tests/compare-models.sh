#!/bin/bash

# Compare Graphiti models across multiple test scenarios
# 3 models × 3 tests = 9 runs, all data kept in database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend-python"
RESULTS_DIR="$SCRIPT_DIR/results/model-comparison-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$RESULTS_DIR"

MODELS=("gemini-2.5-flash-lite" "gemini-2.5-flash" "gemini-2.5-pro")
MODEL_NAMES=("flash-lite" "flash" "pro")
SCENARIOS=("001-new-year-party" "002-personal-budget" "003-recipe-shopping")

echo "=== Model Comparison Test (3 models × 3 scenarios) ==="
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Function to wait for server
wait_for_server() {
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/chat/health > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "  ERROR: Server failed to start"
    return 1
}

# Function to stop server
stop_server() {
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Function to start server with specific model
start_server() {
    local model=$1
    echo "  Starting server with model: $model"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    GRAPHITI_MODEL="$model" nohup uvicorn app.main:app --port 8000 > /tmp/server-$model.log 2>&1 &
    cd "$SCRIPT_DIR"
    wait_for_server
}

# Function to run test and measure time
run_test() {
    local model_name=$1
    local scenario=$2
    local test_key="${model_name}-${scenario}"

    echo "  Running scenario: $scenario"

    local start_time=$(date +%s.%N)

    ./run-scenario.sh "scenarios/${scenario}.md" 2>&1 | tee "$RESULTS_DIR/test-output-$test_key.txt"

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)

    echo "$duration" > "$RESULTS_DIR/time-$test_key.txt"
    echo "  Completed in ${duration}s"

    # Extract project ID from output
    local project_id=$(grep "Project ID:" "$RESULTS_DIR/test-output-$test_key.txt" | tail -1 | awk '{print $3}')
    echo "$project_id" > "$RESULTS_DIR/project-id-$test_key.txt"
    echo "  Project ID: $project_id"
}

# Function to export Neo4j data for a specific project
export_neo4j_data() {
    local test_key=$1
    local project_id=$2

    echo "  Exporting data for project: $project_id"

    # Count entities and edges for this project
    local entity_count=$(docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
        "MATCH (n:Entity) WHERE n.group_id = '$project_id' RETURN count(n)" 2>/dev/null | tail -1)
    local edge_count=$(docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
        "MATCH ()-[e]->() WHERE e.group_id = '$project_id' RETURN count(e)" 2>/dev/null | tail -1)

    echo "  Entities: $entity_count, Edges: $edge_count"
    echo "project_id: $project_id" > "$RESULTS_DIR/stats-$test_key.txt"
    echo "entities: $entity_count" >> "$RESULTS_DIR/stats-$test_key.txt"
    echo "edges: $edge_count" >> "$RESULTS_DIR/stats-$test_key.txt"

    # Export key entities
    docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
        "MATCH (n:Entity) WHERE n.group_id = '$project_id' RETURN n.name, n.summary ORDER BY n.name" \
        > "$RESULTS_DIR/entities-$test_key.txt" 2>/dev/null
}

# Main loop - for each model, run all scenarios
for i in "${!MODELS[@]}"; do
    model="${MODELS[$i]}"
    model_name="${MODEL_NAMES[$i]}"

    echo ""
    echo "========================================="
    echo "Model: $model"
    echo "========================================="

    # Stop any running server
    stop_server

    # Start server with this model
    start_server "$model"

    # Run each scenario
    for scenario in "${SCENARIOS[@]}"; do
        echo ""
        echo "--- Scenario: $scenario ---"

        test_key="${model_name}-${scenario}"

        run_test "$model_name" "$scenario"

        project_id=$(cat "$RESULTS_DIR/project-id-$test_key.txt")
        export_neo4j_data "$test_key" "$project_id"
    done

    # Stop server after all scenarios for this model
    stop_server
done

# Generate comparison report
echo ""
echo "========================================="
echo "Generating comparison report..."
echo "========================================="

cat > "$RESULTS_DIR/comparison.md" << 'HEADER'
# Model Comparison Report (3 models × 3 scenarios)

## Timing Results (seconds)

HEADER

# Timing table
echo "| Scenario | flash-lite | flash | pro |" >> "$RESULTS_DIR/comparison.md"
echo "|----------|------------|-------|-----|" >> "$RESULTS_DIR/comparison.md"

for scenario in "${SCENARIOS[@]}"; do
    line="| $scenario |"
    for model_name in "${MODEL_NAMES[@]}"; do
        time=$(cat "$RESULTS_DIR/time-${model_name}-${scenario}.txt" 2>/dev/null | cut -d. -f1 || echo "N/A")
        line="$line $time |"
    done
    echo "$line" >> "$RESULTS_DIR/comparison.md"
done

echo "" >> "$RESULTS_DIR/comparison.md"
echo "## Data Statistics (Entities / Edges)" >> "$RESULTS_DIR/comparison.md"
echo "" >> "$RESULTS_DIR/comparison.md"
echo "| Scenario | flash-lite | flash | pro |" >> "$RESULTS_DIR/comparison.md"
echo "|----------|------------|-------|-----|" >> "$RESULTS_DIR/comparison.md"

for scenario in "${SCENARIOS[@]}"; do
    line="| $scenario |"
    for model_name in "${MODEL_NAMES[@]}"; do
        stats_file="$RESULTS_DIR/stats-${model_name}-${scenario}.txt"
        if [[ -f "$stats_file" ]]; then
            entities=$(grep "entities:" "$stats_file" | cut -d: -f2 | tr -d ' ')
            edges=$(grep "edges:" "$stats_file" | cut -d: -f2 | tr -d ' ')
            line="$line $entities / $edges |"
        else
            line="$line N/A |"
        fi
    done
    echo "$line" >> "$RESULTS_DIR/comparison.md"
done

echo "" >> "$RESULTS_DIR/comparison.md"
echo "## Project IDs (for database comparison)" >> "$RESULTS_DIR/comparison.md"
echo "" >> "$RESULTS_DIR/comparison.md"
echo "| Scenario | flash-lite | flash | pro |" >> "$RESULTS_DIR/comparison.md"
echo "|----------|------------|-------|-----|" >> "$RESULTS_DIR/comparison.md"

for scenario in "${SCENARIOS[@]}"; do
    line="| $scenario |"
    for model_name in "${MODEL_NAMES[@]}"; do
        pid=$(cat "$RESULTS_DIR/project-id-${model_name}-${scenario}.txt" 2>/dev/null || echo "N/A")
        # Shorten UUID for display
        short_pid=$(echo "$pid" | cut -c1-8)
        line="$line $short_pid... |"
    done
    echo "$line" >> "$RESULTS_DIR/comparison.md"
done

echo ""
echo "========================================="
echo "Comparison complete!"
echo "Results saved to: $RESULTS_DIR"
echo "========================================="
echo ""
cat "$RESULTS_DIR/comparison.md"

echo ""
echo "All 9 projects are saved in Neo4j database for comparison."

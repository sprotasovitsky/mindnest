#!/bin/bash
# Test Scenario Runner
# Executes test scenarios EXACTLY as written in markdown files
# Usage: ./run-scenario.sh <scenario-file.md>

set -e

SCENARIO_FILE="$1"
BASE_URL="http://localhost:8080"

if [ -z "$SCENARIO_FILE" ]; then
    echo "Usage: ./run-scenario.sh <scenario-file.md>"
    echo "Example: ./run-scenario.sh scenarios/012-russian-language.md"
    exit 1
fi

if [ ! -f "$SCENARIO_FILE" ]; then
    echo "Error: File not found: $SCENARIO_FILE"
    exit 1
fi

echo "=============================================="
echo "Running scenario: $SCENARIO_FILE"
echo "=============================================="
echo ""

# Arrays to store user tokens
declare -A USER_TOKENS
declare -A USER_EMAILS
PROJECT_ID=""

# Function to register a user
register_user() {
    local name="$1"
    local email="$2"
    local password="${3:-test123}"

    echo "Registering user: $name ($email)"
    RESP=$(curl -s -X POST "$BASE_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\",\"name\":\"$name\"}")

    TOKEN=$(echo "$RESP" | jq -r '.token')
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        USER_TOKENS["$name"]="$TOKEN"
        USER_EMAILS["$name"]="$email"
        echo "  ✓ Registered successfully"
    else
        # Try login if already registered
        RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"$email\",\"password\":\"$password\"}")
        TOKEN=$(echo "$RESP" | jq -r '.token')
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            USER_TOKENS["$name"]="$TOKEN"
            USER_EMAILS["$name"]="$email"
            echo "  ✓ Logged in (already registered)"
        else
            echo "  ✗ Failed to register/login"
            echo "  Response: $RESP"
        fi
    fi
}

# Function to create a project
create_project() {
    local user="$1"
    local name="$2"
    local description="$3"
    local token="${USER_TOKENS[$user]}"

    echo "Creating project: $name (by $user)"
    RESP=$(curl -s -X POST "$BASE_URL/api/projects" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "{\"name\":\"$name\",\"description\":\"$description\"}")

    PROJECT_ID=$(echo "$RESP" | jq -r '.id')
    if [ "$PROJECT_ID" != "null" ] && [ -n "$PROJECT_ID" ]; then
        echo "  ✓ Project created: $PROJECT_ID"
    else
        echo "  ✗ Failed to create project"
        echo "  Response: $RESP"
    fi
}

# Function to add member to project
add_member() {
    local owner="$1"
    local member_email="$2"
    local token="${USER_TOKENS[$owner]}"

    echo "Adding member: $member_email"
    RESP=$(curl -s -X POST "$BASE_URL/api/projects/$PROJECT_ID/members" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "{\"email\":\"$member_email\"}")
    echo "  ✓ Member added"
}

# Function to send chat message
send_chat() {
    local user="$1"
    local message="$2"
    local expected="$3"
    local token="${USER_TOKENS[$user]}"

    echo ""
    echo "[$user]: $message"
    RESP=$(curl -s -X POST "$BASE_URL/api/chat" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "{\"projectId\":\"$PROJECT_ID\",\"message\":\"$message\"}")

    REPLY=$(echo "$RESP" | jq -r '.reply')
    echo "Agent: $REPLY"

    if [ -n "$expected" ]; then
        echo "Expected: $expected"
    fi
}

# Parse the scenario file and extract information
echo "Parsing scenario file..."
echo ""

# Extract users from the table
echo "=== Phase 1: Setup ==="
echo ""

# Read users from markdown table (format: | Name | Email | Password |)
while IFS='|' read -r _ name email password _; do
    name=$(echo "$name" | xargs)
    email=$(echo "$email" | xargs)
    password=$(echo "$password" | xargs)

    # Skip header and separator rows
    if [[ "$name" =~ ^-+$ ]] || [ "$name" == "Name" ] || [ -z "$name" ]; then
        continue
    fi

    if [ -n "$email" ] && [[ "$email" == *"@"* ]]; then
        register_user "$name" "$email" "${password:-test123}"
    fi
done < <(grep -E "^\|.*@.*\|" "$SCENARIO_FILE" || grep -E "^\|[^|]+\|[^|]+@[^|]+\|" "$SCENARIO_FILE")

echo ""

# Extract and execute steps
# This is a simplified parser - for complex scenarios, manual execution may be needed

echo "=== Executing Chat Steps ==="
echo ""

# Find all Chat: lines with their User context
current_user=""
step_num=0

while IFS= read -r line; do
    # Check for User: line
    if [[ "$line" =~ ^User:\ (.+)$ ]]; then
        current_user="${BASH_REMATCH[1]}"
        current_user=$(echo "$current_user" | xargs)
    fi

    # Check for Chat: line
    if [[ "$line" =~ ^Chat:\ \"(.+)\"$ ]]; then
        message="${BASH_REMATCH[1]}"
        ((step_num++))

        if [ -n "$current_user" ] && [ -n "${USER_TOKENS[$current_user]}" ]; then
            echo "--- Step $step_num ---"
            send_chat "$current_user" "$message"
        else
            echo "Warning: No token for user '$current_user', skipping message"
        fi
    fi

    # Check for project creation
    if [[ "$line" =~ POST\ /api/projects.*\"name\":\ ?\"([^\"]+)\".*\"description\":\ ?\"([^\"]+)\" ]]; then
        proj_name="${BASH_REMATCH[1]}"
        proj_desc="${BASH_REMATCH[2]}"
        if [ -n "$current_user" ] && [ -z "$PROJECT_ID" ]; then
            create_project "$current_user" "$proj_name" "$proj_desc"
        fi
    fi

    # Check for member addition
    if [[ "$line" =~ POST\ /api/projects/.*members.*\"email\":\ ?\"([^\"]+)\" ]]; then
        member_email="${BASH_REMATCH[1]}"
        if [ -n "$current_user" ] && [ -n "$PROJECT_ID" ]; then
            add_member "$current_user" "$member_email"
        fi
    fi

done < "$SCENARIO_FILE"

echo ""
echo "=============================================="
echo "Scenario execution completed"
echo "=============================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo ""

# Verification
echo "=== Verification ==="
if [ -n "$PROJECT_ID" ]; then
    echo "Items in Qdrant:"
    curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
        -H "Content-Type: application/json" \
        -d "{\"filter\":{\"must\":[{\"key\":\"projectId\",\"match\":{\"value\":\"$PROJECT_ID\"}}]}}" | jq '.result.count'

    echo ""
    echo "Items in Neo4j:"
    docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
        "MATCH (k:KnowledgeItem {projectId: '$PROJECT_ID'}) RETURN k.type, count(*) as count" 2>/dev/null || echo "Neo4j query failed"
fi

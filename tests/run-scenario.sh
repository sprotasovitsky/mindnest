#!/bin/bash
# Test Scenario Runner
# Executes test scenarios EXACTLY as written in markdown files
# Usage: ./run-scenario.sh <scenario-file.md>
# Compatible with macOS (zsh/bash 3.x) - no associative arrays

SCENARIO_FILE="$1"
BASE_URL="${TEST_BASE_URL:-http://localhost:8000}"

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

# Store users as "name:email:token" entries in a simple array
USER_DATA=()
PROJECT_ID=""

# Function to get token for user by name
get_token() {
    local name="$1"
    for entry in "${USER_DATA[@]}"; do
        local entry_name="${entry%%:*}"
        if [ "$entry_name" = "$name" ]; then
            # Extract token (third field)
            echo "$entry" | cut -d: -f3
            return
        fi
    done
    echo ""
}

# Function to get email for user by name
get_email() {
    local name="$1"
    for entry in "${USER_DATA[@]}"; do
        local entry_name="${entry%%:*}"
        if [ "$entry_name" = "$name" ]; then
            # Extract email (second field)
            echo "$entry" | cut -d: -f2
            return
        fi
    done
    echo ""
}

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
        USER_DATA+=("$name:$email:$TOKEN")
        echo "  ✓ Registered successfully"
    else
        # Try login if already registered
        RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"$email\",\"password\":\"$password\"}")
        TOKEN=$(echo "$RESP" | jq -r '.token')
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            USER_DATA+=("$name:$email:$TOKEN")
            echo "  ✓ Logged in (already registered)"
        else
            echo "  ✗ Failed to register/login"
            echo "  Response: $RESP"
        fi
    fi
}

# Function to create a project and auto-add all registered users as members
create_project() {
    local user="$1"
    local name="$2"
    local description="$3"
    local token=$(get_token "$user")
    local owner_email=$(get_email "$user")

    echo "Creating project: $name (by $user)"
    RESP=$(curl -s -X POST "$BASE_URL/api/projects" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "{\"name\":\"$name\",\"description\":\"$description\"}")

    PROJECT_ID=$(echo "$RESP" | jq -r '.id')
    if [ "$PROJECT_ID" != "null" ] && [ -n "$PROJECT_ID" ]; then
        echo "  ✓ Project created: $PROJECT_ID"

        # Auto-add all other registered users as members
        for entry in "${USER_DATA[@]}"; do
            local member_name="${entry%%:*}"
            local member_email=$(echo "$entry" | cut -d: -f2)

            # Skip the owner
            if [ "$member_email" != "$owner_email" ]; then
                echo "  Adding member: $member_email"
                curl -s -X POST "$BASE_URL/api/projects/$PROJECT_ID/members" \
                    -H "Content-Type: application/json" \
                    -H "Authorization: Bearer $token" \
                    -d "{\"email\":\"$member_email\"}" > /dev/null
            fi
        done
        echo "  ✓ All members added"
    else
        echo "  ✗ Failed to create project"
        echo "  Response: $RESP"
    fi
}

# Function to add member to project
add_member() {
    local owner="$1"
    local member_email="$2"
    local token=$(get_token "$owner")

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
    local token=$(get_token "$user")

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

# Read users from markdown table
# Supports both formats:
# | Name | Email | Password |          (3 columns)
# | Name | Role | Email | Password |   (4 columns)
while IFS='|' read -r line; do
    # Skip empty lines and separators
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*-+[[:space:]]*$ ]] && continue

    # Split by | and clean up
    IFS='|' read -ra cols <<< "$line"

    # Find email column (contains @)
    email=""
    email_idx=-1
    for i in "${!cols[@]}"; do
        col=$(echo "${cols[$i]}" | xargs 2>/dev/null || echo "${cols[$i]}" | tr -d ' ')
        if [[ "$col" == *"@"* ]]; then
            email="$col"
            email_idx=$i
            break
        fi
    done

    # Skip if no email found
    [[ -z "$email" ]] && continue

    # Name is always first non-empty column
    name=$(echo "${cols[1]}" | xargs 2>/dev/null || echo "${cols[1]}" | tr -d ' ')

    # Skip header row
    [[ "$name" == "Name" ]] && continue
    [[ -z "$name" ]] && continue

    # Password is column after email, or default
    password_idx=$((email_idx + 1))
    if [ $password_idx -lt ${#cols[@]} ]; then
        password=$(echo "${cols[$password_idx]}" | xargs 2>/dev/null || echo "${cols[$password_idx]}" | tr -d ' ')
    fi
    password="${password:-test123}"

    register_user "$name" "$email" "$password"
done < <(grep -E "^\|.*@.*\|" "$SCENARIO_FILE" 2>/dev/null || true)

echo ""

# Extract and execute steps
echo "=== Executing Chat Steps ==="
echo ""

# Find all Chat: lines with their User context
current_user=""
step_num=0
in_chat=false
chat_message=""

while IFS= read -r line; do
    # Check for User: line
    if [[ "$line" =~ ^User:\ (.+)$ ]]; then
        current_user="${BASH_REMATCH[1]}"
        current_user=$(echo "$current_user" | xargs 2>/dev/null || echo "$current_user" | tr -d ' ')
    fi

    # Check for Chat: line start (may be single or multi-line)
    if [[ "$line" =~ ^Chat:\ \"(.*)$ ]]; then
        chat_content="${BASH_REMATCH[1]}"
        # Check if message ends on same line
        if [[ "$chat_content" =~ ^(.*)\"$ ]]; then
            # Single line message
            message="${BASH_REMATCH[1]}"
            step_num=$((step_num + 1))

            token=$(get_token "$current_user")
            if [ -n "$current_user" ] && [ -n "$token" ]; then
                echo "--- Step $step_num ---"
                send_chat "$current_user" "$message"
            else
                echo "Warning: No token for user '$current_user', skipping message"
            fi
        else
            # Multi-line message starts
            in_chat=true
            chat_message="$chat_content"
        fi
    elif [ "$in_chat" = true ]; then
        # Continue collecting multi-line message
        if [[ "$line" =~ ^(.*)\"$ ]]; then
            # Message ends
            chat_message="$chat_message ${BASH_REMATCH[1]}"
            in_chat=false
            step_num=$((step_num + 1))

            # Truncate long messages for display but send full to API
            display_msg="${chat_message:0:100}"
            [ ${#chat_message} -gt 100 ] && display_msg="${display_msg}..."

            token=$(get_token "$current_user")
            if [ -n "$current_user" ] && [ -n "$token" ]; then
                echo "--- Step $step_num ---"
                send_chat "$current_user" "$chat_message"
            else
                echo "Warning: No token for user '$current_user', skipping message"
            fi
            chat_message=""
        else
            chat_message="$chat_message $line"
        fi
    fi

    # Check for project creation (simplified pattern)
    if [[ "$line" == *"POST /api/projects"* ]] && [[ "$line" == *'"name"'* ]]; then
        # Extract project name and description using grep/sed
        proj_name=$(echo "$line" | grep -o '"name"[^"]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
        proj_desc=$(echo "$line" | grep -o '"description"[^"]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

        if [ -n "$current_user" ] && [ -z "$PROJECT_ID" ] && [ -n "$proj_name" ]; then
            create_project "$current_user" "$proj_name" "${proj_desc:-Test project}"
        fi
    fi

    # Check for member addition
    if [[ "$line" == *"POST /api/projects"*"members"* ]] && [[ "$line" == *'"email"'* ]]; then
        member_email=$(echo "$line" | grep -o '"email"[^"]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

        if [ -n "$current_user" ] && [ -n "$PROJECT_ID" ] && [ -n "$member_email" ]; then
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
    echo "Checking Neo4j for entities (Graphiti):"
    docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
        "MATCH (n:Entity) WHERE n.group_id = '$PROJECT_ID' RETURN count(n) as entity_count" 2>/dev/null || echo "Neo4j query failed (container may have different name)"

    echo ""
    echo "Edges in Neo4j:"
    docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
        "MATCH ()-[r]->() WHERE r.group_id = '$PROJECT_ID' RETURN count(r) as edge_count" 2>/dev/null || echo "Neo4j query failed"
fi

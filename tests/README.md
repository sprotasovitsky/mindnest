# MindNest Integration Tests

End-to-end test scenarios for testing MindNest functionality through the API.

## Structure

```
tests/
├── README.md              # This file
├── run-scenario.sh        # Test runner script (macOS compatible)
├── scenarios/             # Test scenario definitions
│   ├── 001-new-year-party.md
│   ├── 002-work-project.md
│   ├── ...
│   ├── 012-russian-language.md
│   └── 015-cross-language.md
├── prompts/               # Saved system prompts by version
│   └── prompt-v8.txt
└── results/               # Test execution results (committed)
    ├── model-upgrade-v8.md
    └── 012-015-test-run.md
```

## How to Run Tests

### Complete Test Workflow

#### Step 1: BEFORE running test - Save the prompt

```bash
# Extract current system prompt from AgentService.java and save it
# Increment version number (v8 → v9, etc.)
cp prompts/prompt-v8.txt prompts/prompt-v9.txt
# Edit to reflect current SYSTEM_PROMPT and INTENT_DETECTION_PROMPT from AgentService.java
```

#### Step 2: Run the test

```bash
cd /Users/siarheipratasavitski/Projects/MindNest/tests
./run-scenario.sh scenarios/012-russian-language.md
```

The runner will:
1. Parse users from markdown table
2. Register/login users
3. Create project and add members
4. Execute all Chat: steps in order
5. Show verification (Qdrant/Neo4j counts)

#### Step 3: AFTER test - Save results

Create a results file `results/XXX-description.md`:

```markdown
# Test Scenario XXX - Description
Date: YYYY-MM-DD
Prompt Version: N (see prompts/prompt-vN.txt)

## Results
| Step | Expected | Actual | Status |
|------|----------|--------|--------|
| 2.1  | SAVE     | SAVE   | ✅     |
| 3.3  | SEARCH   | SEARCH | ✅     |
...

## Summary
- Total: X/Y passed (Z%)
- Issues found: ...
- Fixes applied: ...
```

### Prerequisites

1. Start databases:
   ```bash
   cd docker && docker-compose up -d
   ```

2. Start backend:
   ```bash
   cd backend
   export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
   export GOOGLE_APPLICATION_CREDENTIALS=../.secrets/mindnest-481413-d59e7e99bbfb.json
   export VERTEX_AI_PROJECT_ID=mindnest-481413
   ./gradlew bootRun
   ```

3. Verify backend is running:
   ```bash
   curl http://localhost:8080/actuator/health
   ```

## Test Scenario Format

Each scenario file contains:

```markdown
# Test Scenario NNN: Name

## Overview
What the test covers

## Users
| Name | Email | Password |
|------|-------|----------|
| User1 | user1@test.com | test123 |

## Test Execution

### Phase N: Description

#### Step N.N: Step name
User: User1
Chat: "Message to send"
Expected: What should happen
Intent: SAVE/SEARCH/UPDATE/DELETE/TASK/COMPLETE
```

## Available Test Scenarios

| # | Name | Description |
|---|------|-------------|
| 001 | New Year Party | Multi-user party planning |
| 002 | Work Project | Project management basics |
| 003-011 | Various | Different use cases |
| **012** | Russian Language | Russian language support (17 steps) |
| **015** | Cross-Language | EN↔RU search with gemini-embedding-001 |

## Test Results

Results are saved in `results/` folder and **committed to repo**.

Format: `results/NNN-description.md` or `results/scenario-iteration-X.md`

Each result file should contain:
- Date and prompt version
- Pass/fail counts
- Detailed step results
- Issues found and fixes applied

## Post-Test Analysis

After each test run, verify:

### Database Checks

```bash
# Neo4j: Check items
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>'})
   RETURN k.type, count(*) as count"

# Neo4j: Check tasks
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>', type: 'TASK'})
   RETURN k.content, k.status, k.deadline"

# Qdrant: Count vectors
curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<PROJECT_ID>"}}]}}'
```

### Completion Criteria

A test is **PASSED** only when:
- [ ] All agent responses are correct for the intent
- [ ] No empty or error responses
- [ ] Data exists in databases as expected
- [ ] Task statuses are correct (TODO/DONE)
- [ ] No unexpected duplicates
- [ ] Delete operations remove data

## Cleanup

```bash
# PostgreSQL
docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
  "DELETE FROM users WHERE email LIKE '%@test.com';"

# Neo4j
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem) WHERE k.projectId IS NOT NULL DETACH DELETE k;"
```

## Issue Priority

| Priority | Description | Examples |
|----------|-------------|----------|
| P0 | Core broken | Empty responses, data loss |
| P1 | Feature broken | Delete not working |
| P2 | Data issues | Duplicates, wrong dates |
| P3 | UX issues | Verbose output |

Fix P0 first, then P1, etc. Re-run entire test after each fix.

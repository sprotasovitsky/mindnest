# MindNest Integration Tests

This folder contains end-to-end test scenarios for testing MindNest functionality through the API.

## Structure

```
tests/
├── README.md           # This file
├── scenarios/          # Test scenario definitions
│   └── 001-new-year-party.md
└── results/            # Test execution results (gitignored)
```

## How to Run Tests

Tests are executed manually through Claude Code by:

1. Starting the backend and databases:
   ```bash
   cd docker && docker-compose up -d
   cd backend && ./gradlew bootRun
   ```

2. Opening a test scenario file (e.g., `scenarios/001-new-year-party.md`)

3. Asking Claude to execute the test:
   ```
   Run test scenario 001-new-year-party
   ```

4. Claude will:
   - Create necessary users via API
   - Execute all scenario steps
   - Verify data in databases
   - Report results

5. **Post-Test Analysis** (MANDATORY after each scenario):
   - Analyze ALL agent responses for correctness
   - Check database state matches expected outcomes
   - Document any issues found
   - Fix issues and re-run until test passes completely

## Test Format

Each scenario file contains:

1. **Overview** - What the test covers
2. **Prerequisites** - What must be running/available
3. **Users** - User accounts to create
4. **Steps** - Numbered steps with:
   - Who performs the action (user)
   - What they say/do (chat message)
   - Expected outcome
5. **Verification** - Database checks to perform
6. **Cleanup** - How to reset after test

## Adding New Tests

1. Create a new file in `scenarios/` with format `NNN-test-name.md`
2. Follow the template structure
3. Include verification steps for all key operations

## Test Categories

- **001-099**: Core functionality (knowledge, tasks, projects)
- **100-199**: Multi-user collaboration
- **200-299**: Edge cases and error handling
- **300-399**: Performance and stress tests

---

## Post-Test Analysis Process

After executing each test scenario, perform the following analysis before considering the test complete:

### Step 1: Collect All Agent Responses

Review every response from the agent during the test:
- Was the response relevant to the user's request?
- Did the agent perform the expected action?
- Were there any empty or error responses?

### Step 2: Database Verification

Run these queries to verify database state:

```bash
# PostgreSQL: Check users and project members
docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
  "SELECT u.name, u.email, pm.role FROM users u
   LEFT JOIN project_members pm ON u.id = pm.user_id
   WHERE email LIKE '%@test.com';"

# Neo4j: Check all knowledge items
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>'})
   RETURN k.type, k.status, k.content ORDER BY k.createdAt;"

# Neo4j: Check task statuses specifically
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>', type: 'TASK'})
   RETURN k.content, k.status, k.deadline;"

# Qdrant: Check vector count
curl -s "http://localhost:6333/collections/knowledge_vectors" | grep points_count
```

### Step 3: Issue Classification

Categorize found issues by severity:

| Priority | Description | Examples |
|----------|-------------|----------|
| **P0 - Critical** | Core functionality broken | Tasks not completing, empty responses, data loss |
| **P1 - High** | Feature not working correctly | Delete not working, wrong calculations |
| **P2 - Medium** | Data quality issues | Duplicates, wrong dates, missing fields |
| **P3 - Low** | UX issues | Irrelevant responses, verbose output |

### Step 4: Document Issues

Create an issue report with:
```markdown
## Issue: [Brief description]
- **Priority**: P0/P1/P2/P3
- **Step**: Which test step revealed the issue
- **Expected**: What should have happened
- **Actual**: What actually happened
- **Evidence**: Database query results, API responses
- **File**: Suspected source file to fix
```

### Step 5: Fix and Re-run

1. Fix issues starting from P0 (highest priority)
2. Commit fixes with descriptive messages
3. Clean test data:
   ```bash
   # Clean PostgreSQL
   docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
     "DELETE FROM project_members WHERE project_id IN (SELECT id FROM projects WHERE name LIKE '%test%');"
   docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
     "DELETE FROM projects WHERE name LIKE '%test%';"
   docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
     "DELETE FROM users WHERE email LIKE '%@test.com';"

   # Clean Neo4j
   docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
     "MATCH (k:KnowledgeItem) WHERE k.projectId IS NOT NULL DETACH DELETE k;"
   ```
4. Re-run the ENTIRE test scenario
5. Repeat until all checks pass

### Step 6: Test Completion Criteria

A test is considered **PASSED** only when:

- [ ] All agent responses are relevant and correct
- [ ] No empty or error responses
- [ ] All expected data exists in databases
- [ ] All task statuses are correct (TODO/DONE)
- [ ] No duplicate entries (unless expected)
- [ ] Calculations are accurate
- [ ] Delete operations actually remove data
- [ ] Dates and other fields have correct values

### Example Analysis Report

```markdown
# Test Run: 001-new-year-party
Date: 2024-12-16
Status: FAILED (5 issues found)

## Issues Found:

### 1. [P0] Tasks not marked as completed
- Step: 4.1-4.4 (all users completing tasks)
- Expected: Task status = DONE
- Actual: Task status = TODO
- File: TaskTools.java

### 2. [P0] Empty response
- Step: 4.2 (Vika completes shopping)
- Expected: Confirmation message
- Actual: {"reply":"","sources":[...]}
- File: AgentService.java

### 3. [P1] Delete not working
- Step: 2.9 (Remove Christmas tree)
- Expected: Item removed from DB
- Actual: Item still present (3 copies)
- File: KnowledgeTools.java

### 4. [P2] Wrong year in deadline
- Step: 3.1 (Create tasks)
- Expected: 2024-12-30
- Actual: 2023-12-30
- File: TaskTools.java

### 5. [P2] Data duplication
- Step: Multiple
- Expected: Single entry per item
- Actual: Multiple duplicates
- File: KnowledgeTools.java

## Next Steps:
1. Fix P0 issues first
2. Re-run test
3. Continue until all pass
```

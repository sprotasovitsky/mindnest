# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindNest is an AI-first platform for knowledge and task management through a chat interface. Users interact with a personal AI agent (like a secretary) that manages knowledge items, tasks, and projects.

## Tech Stack

- **Backend**: Java 21 + Spring Boot 3.2 with Virtual Threads
- **Mobile/Web**: Flutter + Dart (iOS, Android, Web from single codebase)
- **AI**: Google Vertex AI (Gemini 2.5 Flash-Lite for LLM, gemini-embedding-001 for embeddings)
- **Databases**: Neo4j (knowledge graph), Qdrant (vector search), PostgreSQL (users/auth)
- **Infrastructure**: Docker Compose for local dev

## Common Commands

### Backend (from `backend/` directory)

**IMPORTANT**: Backend requires Java 21. On macOS with Homebrew:
```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
```

```bash
./gradlew build              # Build the project
./gradlew bootRun            # Run the Spring Boot application
./gradlew test               # Run all tests
./gradlew test --tests "ClassName.methodName"  # Run single test
```

### Mobile (from `mobile/` directory)
```bash
flutter pub get              # Install dependencies
flutter run                  # Run on connected device/emulator
flutter run -d chrome        # Run in web browser
flutter build apk            # Build Android APK
flutter build ios            # Build iOS app
dart run build_runner build  # Generate code (freezed, json_serializable, riverpod)
```

### Docker (from `docker/` directory)
```bash
docker-compose up -d         # Start all databases (PostgreSQL, Neo4j, Qdrant)
docker-compose down          # Stop all services
docker-compose logs -f       # View logs
```

### Local Development Ports
- Backend API: `http://localhost:8080`
- PostgreSQL: `localhost:5432`
- Neo4j Browser: `http://localhost:7474` (Bolt: `localhost:7687`)
- Qdrant REST: `http://localhost:6333` (gRPC: `localhost:6334`)

## Architecture

### Backend Structure (`backend/src/main/java/com/mindnest/`)
```
├── agent/                    # AI agent layer
│   ├── AgentService.java         # Main orchestrator (145 lines)
│   ├── IntentDetectionEngine.java # Message decomposition & intent detection
│   ├── IntentExecutor.java        # Routes intents to handlers
│   ├── ResponseGenerator.java     # LLM response generation
│   ├── UserContextBuilder.java    # User/project context building
│   ├── ToolDeclarationFactory.java # Tool/function declarations
│   ├── ToolExecutor.java          # Routes tool calls to implementations
│   ├── ChunkResult.java           # Result of chunk processing
│   ├── ChunkIntent.java           # Detected intent record
│   ├── RelationIntent.java        # Relation intent record
│   ├── handler/                   # Intent handlers
│   │   ├── IntentHandler.java         # Handler interface
│   │   ├── SaveIntentHandler.java     # SAVE intent
│   │   ├── TaskIntentHandler.java     # TASK intent + clarification
│   │   ├── SearchIntentHandler.java   # SEARCH intent
│   │   └── ChatIntentHandler.java     # CHAT intent
│   └── tools/                     # Tool implementations
│       ├── KnowledgeTools.java        # create, search knowledge
│       ├── TaskTools.java             # create, complete tasks
│       ├── ProjectTools.java          # project/member management
│       └── TimeTools.java             # date parsing
├── config/               # Configuration classes
├── controller/           # REST endpoints
├── model/
│   ├── dto/              # Request/Response DTOs
│   └── entity/           # Database entities
├── repository/           # Data access
└── service/              # Business logic
```

### Mobile Structure (`mobile/lib/`)
```
├── core/
│   ├── api/        # HTTP client (Dio-based)
│   ├── router/     # Navigation (go_router)
│   └── theme/      # UI theming
└── features/
    └── chat/
        └── presentation/
            ├── screens/   # ChatScreen
            └── widgets/   # MessageBubble, ChatInput
```

### Data Model
- **KnowledgeItem** (Neo4j): Central entity with types `FACT`, `TASK`, `NOTE`, `DECISION`
- **KnowledgeRelation** (Neo4j): Relations between items (SUPERSEDES, CONTRADICTS, BELONGS_TO, etc.)
- **User/Project** (PostgreSQL): Auth and project management
- **Vectors** (Qdrant): Embeddings for semantic search (items are NEVER deleted from Qdrant)

### AI Agent Flow
```
User Message → ChatController → AgentService
                                      │
                                      ▼
                         IntentDetectionEngine.decompose()
                         Splits message into logical chunks
                                      │
                                      ▼ (for each chunk)
                         IntentDetectionEngine.detectChunkIntent()
                         Returns: intent, type, content, properties, relations
                                      │
                                      ▼
                              IntentExecutor.processChunk()
                              Routes to appropriate handler:
                              ├─ SaveIntentHandler   → create_knowledge
                              ├─ TaskIntentHandler   → create_task / complete_task
                              ├─ SearchIntentHandler → search + graph expansion
                              └─ ChatIntentHandler   → no tools
                                      │
                                      ▼
                         ResponseGenerator.generateCombinedResponse()
                         LLM generates natural language response
                                      │
                                      ▼
                         ChatResponse (reply, sources, confidence)
```

## Immutable Architecture

**CRITICAL PRINCIPLE**: The system is fully immutable. There are NO UPDATE or DELETE operations at the database level. All changes create NEW items with relations.

### How Operations Work

| User Action | What Happens in DB |
|-------------|-------------------|
| Create item | CREATE new KnowledgeItem |
| Update item | CREATE new item + SUPERSEDES relation to old |
| Delete item | CREATE `[DELETED] description` marker + SUPERSEDES relation to original |
| Complete task | CREATE `task [DONE]` node + SUPERSEDES relation to original |
| Refund purchase | CREATE refund item + CONTRADICTS relation to original purchase |

### Relation Types

| Relation | Meaning | Graph Depth |
|----------|---------|-------------|
| `SUPERSEDES` | New item replaces old (update, delete, complete) | ∞ (follow chain to end) |
| `CONTRADICTS` | Items cancel out (refund cancels purchase) | ∞ (follow chain to end) |
| `DEPENDS_ON` | Item depends on another | ∞ (follow chain to end) |
| `BLOCKS` | Item blocks another | ∞ (follow chain to end) |
| `BELONGS_TO` | Item belongs to category | 1 level |
| `ASSIGNED_TO` | Task assigned to person | 1 level |
| `RELATES_TO` | General relation | 1 level |

### Graph Expansion (GraphService)

When searching, the system:
1. Finds seed nodes via semantic search (Qdrant)
2. Expands graph from seed nodes following relations
3. **Chain relations** (SUPERSEDES, CONTRADICTS, etc.): Follow to the end of chain
4. **Single-level relations** (BELONGS_TO, ASSIGNED_TO): Only 1 hop
5. Serializes expanded graph for LLM to understand context

### LLM Understanding of Relations

The search response prompt teaches LLM to:
- **SUPERSEDES**: Item A → SUPERSEDES → B means A is NEWER, B is OUTDATED. Ignore B.
- **[DELETED] markers**: If `[DELETED] X` → SUPERSEDES → `original X`, then X was deleted
- **[DONE] markers**: If `task [DONE]` → SUPERSEDES → `task`, then task is completed
- **CONTRADICTS**: Subtract from totals (refunds cancel purchases)

### User Context in Search

Search responses include:
- **Current user**: Who is asking the question
- **Project members**: All people in the project with roles

This allows LLM to filter appropriately:
- "My tasks" → Shows only current user's tasks
- "Boris's tasks" → Shows only Boris's tasks
- "All tasks" → Shows all tasks

## AI Models Configuration

Current models in `application.yml`:
```yaml
models:
  chat: gemini-2.5-flash-lite      # Main chat model
  chat-pro: gemini-2.5-pro         # For complex queries
  flash: gemini-2.5-flash-lite     # Intent detection
  embedding: gemini-embedding-001  # 3072 dimensions, 100+ languages
```

Key features:
- **Cross-language search**: EN query finds RU content and vice versa
- **Recency boost**: Recent items get up to 5% score boost (decays over 30 days)
- **Semantic similarity only**: All matching uses embeddings, no keyword matching
- **Similarity thresholds**: Search 0.5, Relation matching 0.6
- **Immutable storage**: Items are NEVER deleted from Qdrant, only marked via relations

## Environment Variables

### Google Cloud / Vertex AI
- `VERTEX_AI_PROJECT_ID`: Google Cloud project ID (`mindnest-481413`)
- `VERTEX_AI_LOCATION`: Region (default: `us-central1`)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON file

Service account key is stored in `.secrets/` (gitignored). To run backend with Vertex AI:
```bash
# Full command to run backend (from backend/ directory):
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/../.secrets/mindnest-481413-d59e7e99bbfb.json
export VERTEX_AI_PROJECT_ID=mindnest-481413
./gradlew bootRun
```

### Database (defaults work with docker-compose)
- `POSTGRES_HOST/PORT/DB/USER/PASSWORD`
- `NEO4J_HOST/PORT/USER/PASSWORD`
- `QDRANT_HOST/PORT`

## Database Access & Credentials

### PostgreSQL (users, projects, members)
- **Credentials**: `mindnest:mindnest` (user:password)
- **Database**: `mindnest`
```bash
docker exec mindnest-postgres psql -U mindnest -d mindnest -c "SELECT * FROM users"
docker exec mindnest-postgres psql -U mindnest -d mindnest -c "SELECT * FROM projects"
docker exec mindnest-postgres psql -U mindnest -d mindnest -c "SELECT u.name, pm.role FROM project_members pm JOIN users u ON pm.user_id = u.id WHERE pm.project_id = '<PROJECT_ID>'"
```

### Neo4j (knowledge graph)
- **Credentials**: `neo4j:mindnest` (user:password)
- **NOT `password` or `mindnest123`**
```bash
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>'}) RETURN k.type, count(*)"
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>', type: 'TASK'}) RETURN k.content, k.status, k.deadline"
```

### Qdrant (vector search)
- **Collection name**: `knowledge_vectors` (NOT `knowledge`)
- **Vector dimensions**: 3072 (gemini-embedding-001)
- **No authentication**
```bash
# Count all vectors
curl -s "http://localhost:6333/collections/knowledge_vectors" | jq '.result.points_count'

# Get vectors for project
curl -s "http://localhost:6333/collections/knowledge_vectors/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<PROJECT_ID>"}}]},"limit":10,"with_payload":true}' | jq
```

## Testing

### Test Scenarios

```
tests/
├── run-scenario.sh        # Test runner (macOS compatible)
├── scenarios/             # Test scenario files
│   ├── 012-russian-language.md
│   └── 015-cross-language.md
├── prompts/               # Saved prompts (ONE file per version)
│   └── prompt-vN.md       # All prompts + config for version N
└── results/               # Test results (committed)
    └── NNN-vN-description.md
```

### Prompt Version File Format

Each version is stored in a single file `prompt-vN.md` containing:

```markdown
# Prompt Version N
Date: YYYY-MM-DD
Time: HH:MM

## Changes from vN-1
- What changed and why

## Configuration (application.yml)
- Models, thresholds, etc.

## Prompts
### 1. System Prompt
### 2. Decomposition Prompt
### 3. Intent Detection Prompt
### 4. Search Response Prompt
### 5. Action Response Prompt
```

### Prompt Files in Backend

All prompts are stored in `backend/src/main/resources/prompts/`:
- `system-prompt.txt`
- `decomposition-prompt.txt`
- `intent-detection-prompt.txt`
- `search-response-prompt.txt`
- `action-response-prompt.txt`

Loaded via `PromptConfig.java` at startup.

### Prompt Version History

| Version | Changes |
|---------|---------|
| v17 | Immutable architecture: no UPDATE/DELETE, only CREATE + relations |
| v18 | Added SUPERSEDES semantics to search response (LLM ignores outdated items) |
| v19 | Added user context (current user + project members) for task filtering |
| v20 | Extracted all prompts to external files, unified version format |
| v21 | Improved intent detection examples |
| v22 | Added task completion clarification flow (needs_clarification, selected_indices) |
| v23 | English-only prompts (language-agnostic via embeddings) |

### Running Tests

```bash
cd tests
./run-scenario.sh scenarios/012-russian-language.md
./run-scenario.sh scenarios/015-cross-language.md
```

The runner parses the markdown file and executes all steps automatically.

### Post-Test Analysis Checklist
After each test scenario, verify:
- [ ] All tasks have correct status (TODO or `[DONE]` marker with SUPERSEDES)
- [ ] Dates/deadlines have correct year (not 2023!)
- [ ] No duplicate data in Neo4j (85% similarity check should prevent)
- [ ] Vector count in Qdrant >= Neo4j count (items never deleted from Qdrant)
- [ ] Deleted items have `[DELETED]` markers with SUPERSEDES relations
- [ ] LLM correctly ignores superseded items in responses

### Database Verification Commands

```bash
# Neo4j: Check items by type
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>'}) RETURN k.type, count(*)"

# Neo4j: Check tasks
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem {projectId: '<PROJECT_ID>', type: 'TASK'}) RETURN k.content, k.status"

# Neo4j: Check relations
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (a)-[r]->(b) WHERE a.projectId = '<PROJECT_ID>' RETURN type(r), count(*)"

# Qdrant: Count vectors for project
curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<PROJECT_ID>"}}]}}'
```

### Test Cleanup Commands

```bash
# PostgreSQL: Remove test users
docker exec mindnest-postgres psql -U mindnest -d mindnest -c \
  "DELETE FROM project_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com');
   DELETE FROM projects WHERE owner_id IN (SELECT id FROM users WHERE email LIKE '%@test.com');
   DELETE FROM users WHERE email LIKE '%@test.com';"

# Neo4j: Remove all knowledge items (CAREFUL!)
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest \
  "MATCH (k:KnowledgeItem) DETACH DELETE k;"

# Qdrant: Delete all points (CAREFUL!)
curl -X POST "http://localhost:6333/collections/knowledge_vectors/points/delete" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"any":["*"]}}]}}'
```

### CRITICAL: Testing Rules

**🛑 PRE-TEST CHECKLIST - STOP AND VERIFY BEFORE ANY TEST:**

```
┌────────────────────────────────────────────────────────────────┐
│  BEFORE running ./run-scenario.sh, VERIFY:                     │
│                                                                │
│  □ Saved intent-detection-prompt.txt to tests/prompts/         │
│  □ Saved system-prompt.txt to tests/prompts/                   │
│  □ Version number incremented (check last file in prompts/)    │
│  □ Created prompt-vN.txt with ALL current prompts              │
│                                                                │
│  IF ANY BOX IS UNCHECKED → DO NOT RUN TEST                     │
└────────────────────────────────────────────────────────────────┘
```

**⚠️ MANDATORY 3-STEP WORKFLOW - NO EXCEPTIONS:**

Every test run MUST follow ALL THREE steps. Skipping any step is a violation of testing rules.

```
┌─────────────────────────────────────────────────────────────┐
│  1. BEFORE TEST → Save prompt to tests/prompts/prompt-vN.txt │
│  2. RUN TEST    → ./run-scenario.sh scenarios/XXX.md         │
│  3. AFTER TEST  → Create tests/results/XXX-vN.md             │
└─────────────────────────────────────────────────────────────┘
```

**Step 3 is NOT optional.** After running ANY test:
- Analyze EACH step: Expected vs Actual
- Create results file with detailed table
- Document all issues found (even minor ones)
- Include database verification counts

**🔴 MANDATORY RESPONSE ANALYSIS - TESTS ALWAYS PASS:**

Tests will always "pass" (run without errors). This does NOT mean they are successful!
You MUST analyze the actual responses:

```
┌────────────────────────────────────────────────────────────────┐
│  FOR EVERY TEST RUN, YOU MUST:                                 │
│                                                                │
│  1. Read the FULL test output (not just tail/metrics)          │
│  2. Check EACH response for correctness:                       │
│     - Did agent detect correct intent? (SAVE/SEARCH/TASK/etc)  │
│     - Did agent save correct content?                          │
│     - Did search return relevant results?                      │
│     - Did SUPERSEDES relations get created for updates?        │
│     - Did [DELETED] markers get created for deletes?           │
│  3. Verify immutable architecture is working:                  │
│     - Neo4j: Check for SUPERSEDES/CONTRADICTS relations        │
│     - No direct updates to existing nodes                      │
│  4. Document ANY incorrect response (even partially wrong)     │
│                                                                │
│  "All tests passed" means NOTHING without this analysis!       │
└────────────────────────────────────────────────────────────────┘
```

**ABSOLUTE RULE - EXACT TEST EXECUTION:**
- Tests MUST be executed EXACTLY as written in `tests/scenarios/*.md` files
- NEVER create ad-hoc test scripts that deviate from scenarios
- NEVER simplify or modify test steps
- Use the EXACT users, messages, and sequence from scenario files
- If a scenario has 2 users (e.g., Алексей and Мария), use BOTH users
- If a scenario has specific messages, use those EXACT messages

**ABSOLUTE RULE - NO /tmp SCRIPTS:**
- NEVER create test scripts in `/tmp/` folder
- ALWAYS use `tests/run-scenario.sh` to execute tests
- If the runner needs fixes, fix it in the repo - not create a new script in /tmp

**Step 1 - BEFORE test:**
- Save prompts from `backend/src/main/resources/prompts/*.txt`
- Include config values from `application.yml` (thresholds)
- Increment version: `prompt-v8.txt` → `prompt-v9.txt`

**Step 2 - RUN test:**
```bash
cd tests
./run-scenario.sh scenarios/012-russian-language.md
```

**Step 3 - AFTER test:**
- Create `tests/results/XXX-description.md` with pass/fail counts
- Include prompt version used
- Document any issues found

**During test execution:**
- If issues are found, STOP and fix them BEFORE moving to next test
- After ANY code change, rebuild backend and re-run test
- Do NOT skip tests - a fix might break something else

**Test Results Format** (`tests/results/NNN-iteration-X.md`):
```
# Scenario NNN - Iteration X
Date: YYYY-MM-DD

## Prompt Version: N (see tests/prompts/prompt-vN.txt)

## Results
- Items to save: X, saved: Y (Z%)
- Search works: Y/N
- Update works: Y/N
- Delete works: Y/N

## Issues Found
...

## What Changed from Previous Iteration
...
```

## Agent Architecture

### Key Principle: Tools, Not Agents
When adding new AI capabilities, **add new tools to existing agent** rather than creating new agents. The single `AgentService` handles all interactions.

### CRITICAL: No Keyword Matching in Code

**NEVER use keyword/pattern matching in Java code for language processing.** This is a strict architectural rule.

Why:
- We must support **many languages simultaneously** without language-specific code
- Keyword matching breaks on morphology (e.g., Russian word endings: "пятёрочку" ≠ "пятёрочке")
- It creates maintenance burden for each new language

What to use instead:
1. **Semantic similarity (embeddings)** - `gemini-embedding-001` handles 100+ languages and morphology
2. **LLM intent detection** - Let the model extract queries, entities, intents from natural language
3. **User confirmation** - If uncertain, ask the user to confirm before destructive operations

Examples of **FORBIDDEN** patterns:
```java
// ❌ WRONG - Language-specific keyword matching
if (content.toLowerCase().contains("удали")) { ... }
if (message.startsWith("что") || message.endsWith("?")) { ... }
String[] keywords = query.split("\\s+");
for (String keyword : keywords) { if (content.contains(keyword)) ... }

// ❌ WRONG - Hardcoded patterns for parsing
if (lower.contains(" was ")) { return content.substring(0, idx); }
if (lower.contains("измени ") || lower.contains("поменяй ")) { ... }
```

Correct approach:
```java
// ✅ CORRECT - Semantic similarity only
List<SearchResult> results = vectorSearchService.search(query, limit, projectId);
for (SearchResult r : results) {
    if (r.score() > threshold) { /* process */ }
}

// ✅ CORRECT - LLM extracts structured data
IntentResult intent = detectIntent(message);  // LLM returns intent, entities
String updateQuery = intent.updateQuery();    // LLM extracted this, not regex
```

### Agent Architecture (Refactored)

```
┌─────────────────────────────────────────────────────────────────┐
│  AgentService.java (145 lines) - Main orchestrator              │
│  • Manages conversation context                                 │
│  • Coordinates the processing pipeline                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          ▼               ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│IntentDetection  │ │IntentExecutor│ │ResponseGen  │ │UserContext  │
│Engine           │ │              │ │erator       │ │Builder      │
│                 │ │Routes to     │ │             │ │             │
│• decompose()    │ │handlers:     │ │• search     │ │• buildUser  │
│• detectIntent() │ │• Save        │ │• action     │ │  Context()  │
│                 │ │• Task        │ │• chat       │ │• getPending │
│                 │ │• Search      │ │• combined   │ │  TaskIds()  │
│                 │ │• Chat        │ │             │ │             │
└─────────────────┘ └──────┬──────┘ └─────────────┘ └─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ToolExecutor.java - Routes tool calls to implementations       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          ▼               ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│KnowledgeTools   │ │TaskTools    │ │ProjectTools │ │TimeTools    │
│• create         │ │• create     │ │• create     │ │• getCurrentDate│
│• search         │ │• complete   │ │• getMembers │ │• parseDate   │
│• createRelation │ │• getActive  │ │             │ │              │
└─────────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Key Services
```
GraphService.java          # Graph expansion with depth per relation type
VectorSearchService.java   # Qdrant semantic search with recency boost
EmbeddingService.java      # Generate embeddings via Gemini
ToolDeclarationFactory.java # Creates all 17 tool declarations for Gemini
```

### Available Tools (17 total)
| Tool | Description |
|------|-------------|
| `create_knowledge` | Save facts, decisions, notes |
| `search_knowledge` | Find information (supports cross-language) |
| `create_task` | Create tasks with assignee and deadline |
| `complete_task_by_title` | Mark task as done (creates [DONE] marker + SUPERSEDES) |
| `complete_tasks_by_ids` | Complete multiple tasks by their IDs |
| `complete_all_tasks_by_assignee` | Complete all tasks for a person |
| `get_active_tasks` | List active tasks |
| `get_tasks_for_today` | Get tasks due today |
| `get_my_items` | Get items created by current user |
| `search_tasks` | Find tasks |
| `decompose_task` | Break task into subtasks |
| `create_relation` | Link two knowledge items by search query |
| `get_related` | Find related items |
| `find_path` | Find connection path between items |
| `create_project` | Create a new project |
| `list_projects` | List user's projects |
| `get_current_date` | Get current date/time |

**Note**: There are NO `update_knowledge`, `delete_knowledge`, or `confirm_delete` tools. All modifications happen through the immutable architecture (new items + relations).

### Adding New Tool
1. Add method to appropriate `*Tools.java` class
2. Add function declaration in `ToolDeclarationFactory.java`
3. Add executor case in `ToolExecutor.java`
4. Update system prompt in `prompts/system-prompt.txt` if needed

### Adding New Intent Handler
1. Create new handler class implementing `IntentHandler` interface in `agent/handler/`
2. Implement `getIntentType()` and `execute()` methods
3. Handler is auto-registered via Spring DI (no manual wiring needed)
4. Update `intent-detection-prompt.txt` to recognize new intent

### Intent Detection (Chunk-Based)

Agent uses chunk-based processing for complex messages:

1. **Decomposition** (Gemini Flash): Splits message into independent logical chunks
   - "Budget 50000 and buy milk" → ["Budget 50000", "buy milk"]
2. **Intent Detection** (Gemini Flash): For each chunk, determines intent and extracts structured data
3. **Execution**: Each chunk processed through appropriate handler
4. **Response Generation** (Gemini Flash): Combines results into natural response

Supported intents:
- `SAVE` - Save new information (creates KnowledgeItem)
  - Delete requests → SAVE with `[DELETED]` marker + SUPERSEDES relation
  - Updates → SAVE new item + SUPERSEDES relation to old
- `SEARCH` - Find existing information (expands graph, returns to LLM)
- `TASK` - Create or complete task
  - status=TODO: Creates new task
  - status=DONE: Completes task with clarification flow (see below)
- `CHAT` - General conversation (no tools)

**Note**: There is no UPDATE or DELETE intent. All modifications handled via SAVE with relations.

### Task Completion Clarification Flow

When user says "Done!" without specifying which task:

```
User: "Done!"
         │
         ▼
IntentDetectionEngine: detects TASK intent with needs_clarification=true
         │
         ▼
TaskIntentHandler: gets user's active tasks
         │
         ├─ 0 tasks → "You have no active tasks"
         ├─ 1 task  → Complete immediately (no question)
         └─ N tasks → Show numbered list, ask which ones
                     │
                     ▼
            "You have 3 active tasks:
             [1] Buy wine
             [2] Rent karaoke
             [3] Buy games
             Which ones are complete? (enter numbers like '1 and 3', or 'all')"
                     │
                     ▼
User: "1 and 3" or "all" or "the wine one"
         │
         ▼
TaskIntentHandler: completes selected tasks
```

Clarification state is stored in message metadata (`pendingTaskIds`) and extracted on next turn.

### Common Issues Fixed
- **Ambiguous task completion**: Clarification flow asks which tasks to complete when multiple exist
- **Tasks not completing**: Use `complete_task_by_title` which creates `[DONE]` marker + SUPERSEDES
- **Empty responses**: Fallback returns function call results if LLM returns empty text
- **Wrong year in dates**: TimeTools uses current/next year for dates without year
- **Data duplication**: 85% similarity check before creating new items
- **Cross-language search**: Works with gemini-embedding-001 (100+ languages)
- **Deleted items showing**: LLM taught to ignore items with SUPERSEDES from `[DELETED]` markers
- **User task filtering**: User context (current user + members) passed to LLM for filtering
- **God class refactoring**: AgentService split from 1727 lines to 145 lines + specialized services

## State Management (Mobile)

Uses Riverpod with code generation. After modifying providers or data classes:
```bash
dart run build_runner build
```

## Code Style

- **All documentation and comments must be in English** — this includes code comments, commit messages, markdown files, and inline documentation
- Follow standard Java/Dart naming conventions
- **Important distinction**: The repository (code, docs, comments) is English-only, but the MindNest application itself must support multiple languages for end users (UI strings, chat responses, pattern matching for user queries, etc.)

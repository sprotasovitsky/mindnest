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
├── agent/          # AI agent orchestration (AgentService)
├── config/         # Configuration classes (VertexAiConfig)
├── controller/     # REST endpoints (ChatController)
├── model/
│   ├── dto/        # Request/Response DTOs
│   └── entity/     # Database entities (User, Project, KnowledgeItem)
├── repository/     # Data access (JPA for PostgreSQL, Neo4j repos)
└── service/        # Business logic (LlmService, EmbeddingService, ModelRouter)
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
- **KnowledgeItem** (Neo4j): Central entity with types `fact`, `task`, `decision`, `note`, `question`
- **User/Project** (PostgreSQL): Auth and project management
- **Vectors** (Qdrant): Embeddings for semantic search

### AI Agent Flow
1. User message → `ChatController`
2. `AgentService` → `ModelRouter` (selects appropriate Gemini model)
3. `LlmService` calls Vertex AI
4. Response includes confidence score and sources

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
- **Similarity thresholds**: Search 0.5, Update 0.6, Delete 0.55

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

**Full documentation: [`tests/README.md`](tests/README.md)**

```
tests/
├── README.md              # Full test documentation
├── run-scenario.sh        # Test runner (macOS compatible)
├── scenarios/             # Test scenario files
│   ├── 012-russian-language.md
│   └── 015-cross-language.md
├── prompts/               # Saved system prompts
└── results/               # Test results (committed)
```

### Running Tests

```bash
cd tests
./run-scenario.sh scenarios/012-russian-language.md
./run-scenario.sh scenarios/015-cross-language.md
```

The runner parses the markdown file and executes all steps automatically.

### Post-Test Analysis Checklist
After each test scenario, verify:
- [ ] All tasks have correct status (DONE/TODO)
- [ ] Dates/deadlines have correct year (not 2023!)
- [ ] No duplicate data in Neo4j
- [ ] Vector count in Qdrant matches Neo4j count
- [ ] Deleted items are actually removed

### CRITICAL: Testing Rules

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

### Tool Structure
```
AgentService.java          # Orchestrates LLM calls, defines function declarations
    ↓
ToolExecutor.java          # Routes function calls to appropriate tool class
    ↓
*Tools.java                # Actual implementations
├── KnowledgeTools.java    # create, search, update, delete knowledge + graph relations
├── TaskTools.java         # create, complete, search tasks
├── ProjectTools.java      # project/member management
└── TimeTools.java         # date parsing
```

### Available Tools (14 total)
| Tool | Description |
|------|-------------|
| `create_knowledge` | Save facts, decisions, notes |
| `search_knowledge` | Find information (supports cross-language) |
| `update_knowledge` | Correct existing info |
| `delete_knowledge` | Remove items |
| `preview_delete` | Preview items before deletion |
| `confirm_delete` | Confirm deletion by IDs |
| `create_task` | Create tasks with assignee and deadline |
| `complete_task_by_title` | Mark task as done by title |
| `get_active_tasks` | List active tasks |
| `search_tasks` | Find tasks |
| `create_relation` | Link two knowledge items |
| `get_related` | Find related items |
| `find_path` | Find connection path between items |
| `get_current_date` | Get current date/time |

### Adding New Tool
1. Add method to appropriate `*Tools.java` class
2. Add function declaration in `AgentService.java` (TOOL_DECLARATIONS)
3. Add executor method in `ToolExecutor.java`
4. Update system prompt in `AgentService.java` if needed

### Intent Detection
Agent uses two-step processing:
1. **Intent Detection** (Gemini Flash): Classifies user message into SAVE, SEARCH, UPDATE, DELETE, TASK, COMPLETE, RELATION, or CHAT
2. **Response Generation** (Gemini Flash-Lite): Executes tools and generates response

Supported intents:
- `SAVE` - Save new information
- `SEARCH` - Find existing information
- `UPDATE` - Correct/modify existing info
- `DELETE` - Remove items
- `TASK` - Create new task
- `COMPLETE` - Mark task as done
- `RELATION` - Create link between items
- `CHAT` - General conversation

### Common Issues Fixed
- **Tasks not completing**: Use `complete_task_by_title` (searches by name, not ID)
- **Empty responses**: Fallback returns function call results if LLM returns empty text
- **Delete not working**: Use `delete_knowledge` tool with query-based search
- **Wrong year in dates**: TimeTools uses current/next year for dates without year
- **Data duplication**: 85% similarity check before creating new items
- **Cross-language search**: Now works with gemini-embedding-001 (100+ languages)

## State Management (Mobile)

Uses Riverpod with code generation. After modifying providers or data classes:
```bash
dart run build_runner build
```

## Code Style

- **All documentation and comments must be in English** — this includes code comments, commit messages, markdown files, and inline documentation
- Follow standard Java/Dart naming conventions
- **Important distinction**: The repository (code, docs, comments) is English-only, but the MindNest application itself must support multiple languages for end users (UI strings, chat responses, pattern matching for user queries, etc.)

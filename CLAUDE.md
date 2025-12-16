# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindNest is an AI-first platform for knowledge and task management through a chat interface. Users interact with a personal AI agent (like a secretary) that manages knowledge items, tasks, and projects.

## Tech Stack

- **Backend**: Java 21 + Spring Boot 3.2 with Virtual Threads
- **Mobile/Web**: Flutter + Dart (iOS, Android, Web from single codebase)
- **AI**: Google Vertex AI (Gemini for LLM, text-embedding-004 for embeddings)
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
Test scenarios are in `tests/scenarios/`. Each scenario is a markdown file with steps to execute.

```bash
# Location
tests/
├── README.md           # Test process documentation
└── scenarios/
    └── 001-new-year-party.md
```

### Running Tests
1. Start infrastructure: `cd docker && docker-compose up -d`
2. Start backend with proper Java/credentials (see Environment Variables)
3. Execute scenario steps via curl or test scripts
4. Run post-test analysis (see tests/README.md)

### Post-Test Analysis Checklist
After each test scenario, verify:
- [ ] All tasks have correct status (DONE/TODO)
- [ ] Dates/deadlines have correct year (not 2023!)
- [ ] No duplicate data in Neo4j
- [ ] Vector count in Qdrant matches Neo4j count
- [ ] Deleted items are actually removed

## Agent Architecture

### Key Principle: Tools, Not Agents
When adding new AI capabilities, **add new tools to existing agent** rather than creating new agents. The single `AgentService` handles all interactions.

### Tool Structure
```
AgentService.java          # Orchestrates LLM calls, defines function declarations
    ↓
ToolExecutor.java          # Routes function calls to appropriate tool class
    ↓
*Tools.java                # Actual implementations
├── KnowledgeTools.java    # create, search, delete knowledge
├── TaskTools.java         # create, complete, search tasks
├── ProjectTools.java      # project/member management
└── TimeTools.java         # date parsing
```

### Adding New Tool
1. Add method to appropriate `*Tools.java` class
2. Add function declaration in `AgentService.java` (TOOL_DECLARATIONS)
3. Add executor method in `ToolExecutor.java`
4. Update system prompt in `AgentService.java` if needed

### Common Issues Fixed
- **Tasks not completing**: Use `complete_task_by_title` (searches by name, not ID)
- **Empty responses**: Fallback returns function call results if LLM returns empty text
- **Delete not working**: Use `delete_knowledge` tool with query-based search
- **Wrong year in dates**: TimeTools uses current/next year for dates without year
- **Data duplication**: 85% similarity check before creating new items

## State Management (Mobile)

Uses Riverpod with code generation. After modifying providers or data classes:
```bash
dart run build_runner build
```

## Code Style

- **All documentation and comments must be in English** — this includes code comments, commit messages, markdown files, and inline documentation
- Follow standard Java/Dart naming conventions
- **Important distinction**: The repository (code, docs, comments) is English-only, but the MindNest application itself must support multiple languages for end users (UI strings, chat responses, pattern matching for user queries, etc.)

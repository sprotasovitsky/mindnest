# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindNest is an AI-first platform for knowledge and task management through a chat interface. Users interact with a personal AI agent that manages knowledge items, tasks, and projects.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + Graphiti
- **Mobile/Web**: Flutter + Dart (iOS, Android, Web from single codebase)
- **AI**: Google Gemini (gemini-2.5-flash-lite for LLM, gemini-embedding-001 for embeddings)
- **Knowledge Graph**: Graphiti (built on Neo4j) - handles entity extraction, temporal relations, hybrid search
- **Databases**: Neo4j (knowledge graph via Graphiti), PostgreSQL (users, projects, members)
- **Infrastructure**: Docker Compose for local dev

## Common Commands

### Backend (from `backend-python/` directory)

```bash
# Create virtual environment (first time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Or with environment variables
GOOGLE_API_KEY=your-key uvicorn app.main:app --reload --port 8000
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

### Docker (from `backend-python/` directory)
```bash
docker-compose up -d         # Start databases (PostgreSQL, Neo4j)
docker-compose down          # Stop all services
docker-compose logs -f       # View logs
```

### Local Development Ports
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Neo4j Browser: `http://localhost:7474` (Bolt: `localhost:7687`)

## Architecture

### Backend Structure (`backend-python/app/`)
```
├── main.py                   # FastAPI app entry point, lifespan handler
├── config.py                 # Settings from environment variables
├── database.py               # PostgreSQL connection (SQLAlchemy async)
├── models.py                 # SQLAlchemy models (User, Project, ProjectMember)
├── graphiti_client.py        # Graphiti wrapper (KnowledgeGraph class)
├── prompts/                  # External prompt templates
│   ├── __init__.py               # Prompt loading and formatting
│   ├── system.txt                # System prompt for LLM
│   ├── context_guide.txt         # How to interpret graph data
│   └── response.txt              # Response generation template
├── routers/
│   ├── auth.py                   # User registration/login
│   ├── projects.py               # Project management
│   └── chat.py                   # Chat API - main endpoint
└── init-scripts/
    └── postgres/
        └── 01-init.sql           # PostgreSQL schema init
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

### Data Model (Graphiti)

Graphiti automatically manages:
- **Entities (Nodes)**: People, tasks, items, concepts extracted from messages
- **Edges (Facts)**: Relationships between entities with temporal metadata
- **Bi-temporal model**: `valid_at`, `expired_at`, `created_at` for each fact

Key fields:
- `expired_at = null` → fact is CURRENT and valid
- `expired_at = <timestamp>` → fact was SUPERSEDED by newer information

### Chat Processing Flow

```
User Message → POST /api/chat
                    │
                    ▼
           KnowledgeGraph.add_message()
           ┌────────────────────────────────────┐
           │  Graphiti automatically:            │
           │  • Extracts entities from text      │
           │  • Creates/updates edges (facts)    │
           │  • Handles temporal invalidation    │
           │  • Normalizes edge types            │
           └────────────────────────────────────┘
                    │
                    ▼
           KnowledgeGraph.get_context_for_response()
           ┌────────────────────────────────────┐
           │  Hybrid search:                     │
           │  • Semantic similarity (embeddings) │
           │  • BM25 keyword matching            │
           │  • Graph traversal                  │
           └────────────────────────────────────┘
                    │
                    ▼
           generate_response()
           ┌────────────────────────────────────┐
           │  LLM (Gemini) generates response:   │
           │  • Uses system prompt               │
           │  • Uses context guide               │
           │  • Facts + entities as context      │
           └────────────────────────────────────┘
                    │
                    ▼
           ChatResponse (reply, sources, confidence)
```

## Graphiti Knowledge Graph

Graphiti replaces the previous custom implementation:
- **Neo4j KnowledgeItem/KnowledgeRelation** → Graphiti entities/edges
- **Qdrant vector storage** → Graphiti embeddings (stored in Neo4j)
- **VectorSearchService** → Graphiti hybrid search
- **GraphService** → Graphiti graph traversal
- **IntentDetectionEngine** → Graphiti entity extraction

### Key Graphiti Features

1. **Automatic Entity Extraction**: Graphiti LLM extracts entities from text
2. **Emergent Schema**: Edge types are created and normalized automatically
3. **Temporal Invalidation**: Old facts get `expired_at` when superseded
4. **Hybrid Search**: Combines BM25 + semantic similarity + graph traversal
5. **Cross-encoder Reranking**: Results are reranked for relevance

### Temporal Model

| Field | Meaning |
|-------|---------|
| `created_at` | When the fact was recorded |
| `valid_at` | When the fact became true |
| `expired_at` | When the fact was superseded (null = still valid) |

Example timeline:
1. "Boris is tasked with buying alcohol" → `expired_at: null` (active task)
2. "Boris bought alcohol for 14000" → task fact gets `expired_at` set (completed)

## AI Models Configuration

Settings in `backend-python/app/config.py`:
```python
llm_model: str = "gemini-2.5-flash-lite"      # Main chat model
llm_model_pro: str = "gemini-2.5-pro"         # For complex queries
# Embeddings: gemini-embedding-001 (3072 dimensions, 100+ languages)
```

Key features:
- **Cross-language search**: EN query finds RU content and vice versa
- **Automatic entity extraction**: No manual intent detection needed
- **Temporal awareness**: Facts have validity periods

## Environment Variables

### Required for Google AI
```bash
# Option 1: API Key (recommended for development)
GOOGLE_API_KEY=your-api-key

# Option 2: Vertex AI with service account
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
```

### Database
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mindnest123
DATABASE_URL=postgresql+asyncpg://mindnest:mindnest@localhost:5432/mindnest
```

### Full startup command
```bash
cd backend-python
source venv/bin/activate
GOOGLE_API_KEY=your-key uvicorn app.main:app --reload --port 8000
```

## Database Access

### Neo4j (knowledge graph via Graphiti)
- **Credentials**: `neo4j:mindnest123` (user:password)
- **Browser**: http://localhost:7474

```bash
# View entities
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 10"

# View edges (facts)
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH ()-[e:RELATES_TO]->() RETURN e.fact, e.created_at LIMIT 10"

# View Graphiti indices
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "SHOW INDEXES"
```

### PostgreSQL (users/auth)
- **Credentials**: `mindnest:mindnest` (user:password)
- **Database**: `mindnest`

Tables are created by `init-scripts/postgres/01-init.sql` on first container start.

## Prompts

All prompts are stored in `backend-python/app/prompts/`:

| File | Purpose |
|------|---------|
| `system.txt` | System prompt defining assistant role |
| `context_guide.txt` | How LLM should interpret graph data (expired_at, etc.) |
| `response.txt` | Template combining system prompt + context + user message |

### Prompt Loading

Prompts are loaded via `prompts/__init__.py`:
- `get_system_prompt()` → loads `system.txt`
- `get_context_guide()` → loads `context_guide.txt`
- `format_response_prompt()` → combines all prompts with context

### Modifying Prompts

1. Edit the `.txt` file in `backend-python/app/prompts/`
2. Restart the server (prompts are cached with `@lru_cache`)
3. Or call `clear_prompt_cache()` to reload

## API Endpoints

### Chat
- `POST /api/chat` - Send message (legacy endpoint for compatibility)
- `POST /api/chat/message` - Send message (new endpoint)
- `POST /api/chat/search` - Search knowledge graph
- `GET /api/chat/health` - Health check

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project
- `POST /api/projects/{id}/members` - Add member

### Request/Response Examples

```bash
# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Boris needs to buy wine", "projectId": "proj-123"}'

# Search
curl -X POST http://localhost:8000/api/chat/search \
  -H "Content-Type: application/json" \
  -d '{"query": "what tasks does Boris have?", "project_id": "proj-123"}'
```

## Development Notes

### Key Principles

1. **Graphiti handles complexity**: Entity extraction, graph management, and search are delegated to Graphiti
2. **Simple processing flow**: Message → Graphiti → Search → LLM → Response
3. **Temporal awareness**: Facts have validity periods, LLM interprets expired_at
4. **No keyword matching**: All search uses semantic similarity via embeddings

### Common Issues

| Issue | Solution |
|-------|----------|
| "Graphiti not initialized" | Check Neo4j is running, credentials are correct |
| "No results from search" | Check project_id matches, add some messages first |
| "Empty response" | Check GOOGLE_API_KEY is set |
| Import errors | Run `pip install -r requirements.txt` |

### Adding New Functionality

Since Graphiti handles entity extraction and graph management, most new features involve:

1. **New prompt instructions**: Edit `prompts/system.txt` or `context_guide.txt`
2. **New API endpoints**: Add to `routers/chat.py`
3. **New search configurations**: Modify `KnowledgeGraph.search()` in `graphiti_client.py`

## Testing

### Test Scenarios

```
tests/
├── run-scenario.sh        # Test runner (macOS compatible)
├── scenarios/             # Test scenario files
│   ├── 001-new-year-party.md      # Multi-user shopping/tasks
│   ├── 002-personal-budget.md     # Budget tracking with corrections
│   ├── 003-recipe-shopping.md     # Recipe management
│   ├── ...
│   ├── 013-edge-cases.md          # Edge cases (long text, unicode)
│   └── 014-enterprise-sprint.md   # High volume stress test
├── prompts/               # Saved prompts (for version tracking)
│   └── prompt-vN.md       # Prompts snapshot for version N
└── results/               # Test results
    └── NNN-vN-description.md
```

### Running Tests

```bash
cd tests
./run-scenario.sh scenarios/001-new-year-party.md
./run-scenario.sh scenarios/002-personal-budget.md
```

The runner:
1. Parses the markdown scenario file
2. Registers users from the table
3. Creates project and adds members
4. Executes all Chat: messages in sequence
5. Prints responses from the agent
6. Verifies entities/edges in Neo4j (Graphiti)

### Environment Variables for Tests

```bash
TEST_BASE_URL=http://localhost:8000  # Default, can override
```

### Post-Test Verification

```bash
# Check entities created by Graphiti
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 20"

# Check edges (facts)
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH ()-[e]->() RETURN type(e), e.fact LIMIT 20"
```

### Analyzing Test Results

Since Graphiti handles entity extraction automatically:
1. Check if entities were created for key concepts (people, items, tasks)
2. Check if edges capture the relationships correctly
3. Verify `expired_at` is set when facts are superseded
4. Check LLM responses are contextually accurate

## State Management (Mobile)

Uses Riverpod with code generation. After modifying providers or data classes:
```bash
dart run build_runner build
```

## Code Style

- **All documentation and comments must be in English**
- Follow PEP 8 for Python code
- Follow Dart style guide for Flutter code
- The application supports multiple languages for end users via multilingual embeddings

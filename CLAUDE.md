# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindNest is an AI-first platform for knowledge and task management through a chat interface. Users interact with a personal AI agent that manages knowledge items, tasks, and projects.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + Graphiti
- **Mobile/Web**: Flutter + Dart (iOS, Android, Web from single codebase)
- **AI**: Google Gemini (gemini-3-flash-preview for chat, gemini-2.5-flash for Graphiti, gemini-embedding-001 for embeddings)
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
uvicorn app.main:app --reload --port 8000
```

### Mobile (from `mobile/` directory)
```bash
# Initial setup (after clone)
make setup                   # flutter pub get + xcodegen + pod install

# Run with different environments (uses flavors)
make run-dev                 # Local backend (flavor: dev)
make run-staging             # Staging backend (flavor: staging)
make run-prod                # Production backend (flavor: prod)

# Build iOS
make build-dev-ios
make build-staging-ios
make build-prod-ios

# Build Android APK
make build-dev-apk           # Dev APK
make build-staging-apk       # Staging APK
make build-prod-apk          # Production APK (signed)

# Build Android AAB (for Play Store)
make build-staging-aab       # Staging bundle
make build-prod-aab          # Production bundle (signed)

# Utilities
make regen                   # Regenerate Xcode project (xcodegen + pod install)
make clean                   # Clean all build artifacts
dart run build_runner build  # Generate code (freezed, json_serializable, riverpod)
```

### iOS Project Structure
```
mobile/ios/
├── project.yml              # XcodeGen config (generates .xcodeproj)
├── Podfile                  # CocoaPods dependencies
├── Configurations/
│   ├── Dev.xcconfig         # → com.mindnest.app.dev
│   ├── Staging.xcconfig     # → com.mindnest.app.staging
│   └── Prod.xcconfig        # → com.mindnest.app
├── MindNest/                # App source files
│   ├── AppDelegate.swift
│   ├── Assets.xcassets/
│   ├── Info.plist
│   └── MindNest-Bridging-Header.h
├── MindNestTests/           # Unit tests
└── ci_scripts/
    └── ci_post_clone.sh     # Xcode Cloud script
```

**Xcode Cloud Schemes:**
- `dev` - Development build
- `staging` - TestFlight builds
- `prod` - App Store builds

**Note:** `.xcodeproj`, `.xcworkspace`, and `Pods/` are gitignored. Run `make setup` after clone.

### Android Project Structure
```
mobile/android/
├── app/
│   ├── build.gradle.kts     # App config with flavors and signing
│   ├── proguard-rules.pro   # ProGuard/R8 rules for release builds
│   └── src/main/
│       └── AndroidManifest.xml
├── build.gradle.kts         # Root Gradle config
├── key.properties           # Signing credentials (gitignored)
└── mindnest-release.jks     # Release keystore (gitignored)
```

**Product Flavors:**

| Flavor | Application ID | App Name |
|--------|----------------|----------|
| dev | `com.mindnest.app.dev` | MindNest Dev |
| staging | `com.mindnest.app.staging` | MindNest Staging |
| prod | `com.mindnest.app` | MindNest |

**Release Signing:**
- Keystore and credentials stored in `key.properties` (gitignored)
- Release builds are signed automatically when `key.properties` exists
- ProGuard/R8 minification enabled for release builds

**Note:** `key.properties` and `*.jks` are gitignored. Store keystore securely outside repo.

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

### Backend Structure (`backend-python/`)
```
├── alembic/                  # Database migrations
│   ├── env.py                    # Alembic async config
│   └── versions/                 # Migration files
├── app/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings from environment (Pydantic V2)
│   ├── database.py               # PostgreSQL connection (SQLAlchemy async)
│   ├── models.py                 # SQLAlchemy models (User, Project, ChatMessage)
│   ├── graphiti_client.py        # Graphiti wrapper
│   ├── llm.py                    # Shared Gemini client (singleton)
│   ├── classifier.py             # Message classifier (DATA/QUESTION)
│   ├── pending_cache.py          # In-memory cache for instant message availability
│   ├── prompts/                  # LLM prompt templates
│   │   ├── __init__.py               # Prompt loading/formatting
│   │   ├── system.txt
│   │   ├── context_guide.txt
│   │   ├── classifier.txt            # Classification prompt
│   │   ├── response.txt
│   │   └── onboarding.txt            # Project onboarding flow
│   └── routers/
│       ├── auth.py               # User registration/login
│       ├── projects.py           # Project management
│       └── chat.py               # Chat API with history support
├── alembic.ini               # Alembic configuration
├── docker-compose.yml        # Neo4j + PostgreSQL
└── requirements.txt          # Python dependencies
```

### Mobile Structure (`mobile/lib/`)

The mobile app follows **Clean Architecture** with Repository pattern:

```
├── core/
│   ├── api/              # HTTP client (Dio-based ApiClient)
│   ├── auth/             # Auth service (token storage)
│   ├── constants/        # AppConfig (API URL, timeouts, storage keys)
│   ├── error/            # AppError sealed classes (NetworkError, AuthError, ValidationError)
│   ├── models/           # @freezed data classes (User, Project, Member, ChatMessage)
│   ├── providers/        # @riverpod state management (auth, projects, members, chat)
│   ├── repositories/     # Repository pattern (abstract + impl for each domain)
│   ├── router/           # Navigation (go_router)
│   └── theme/            # UI theming
├── shared/
│   └── widgets/          # Reusable widgets (LoadingOverlay, ErrorView, EmptyState)
└── features/
    ├── auth/
    │   └── presentation/screens/    # LoginScreen
    ├── chat/
    │   └── presentation/
    │       ├── screens/             # ChatScreen
    │       └── widgets/             # MessageBubble, ChatInput
    ├── members/
    │   └── presentation/
    │       ├── screens/             # MembersScreen
    │       └── widgets/             # AddMemberModal
    ├── profile/
    │   └── presentation/screens/    # ProfileScreen
    └── projects/
        └── presentation/
            ├── screens/             # ProjectsListScreen
            └── widgets/             # CreateProjectModal, ProjectSettingsSheet
```

### Mobile Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (features/*/presentation/)              │
│  - Screens (ConsumerWidget/ConsumerStatefulWidget)          │
│  - Widgets (stateless UI components)                        │
│  - Uses: ref.watch(provider), ref.read(provider.notifier)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  State Layer (core/providers/)                              │
│  - @riverpod annotated Notifier classes                     │
│  - @freezed State classes with copyWith                     │
│  - Handles: loading, error, data states                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Repository Layer (core/repositories/)                      │
│  - Abstract interfaces (AuthRepository, ProjectRepository)  │
│  - Implementations (*RepositoryImpl)                        │
│  - Maps API responses to domain models                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer (core/api/, core/models/)                       │
│  - ApiClient (Dio HTTP client)                              │
│  - @freezed models with @JsonSerializable                   │
│  - AuthService (token storage)                              │
└─────────────────────────────────────────────────────────────┘
```

### Code Generation

The mobile app uses code generation for boilerplate:

```bash
# Run after modifying @freezed, @riverpod, or @JsonSerializable classes
cd mobile
dart run build_runner build

# Watch mode for development
dart run build_runner watch
```

Generated files:
- `*.freezed.dart` - copyWith, == operator, toString
- `*.g.dart` - JSON serialization, Riverpod providers

### Data Model (Graphiti)

Graphiti automatically manages:
- **Entities (Nodes)**: People, tasks, items, concepts extracted from messages
- **Edges (Facts)**: Relationships between entities with temporal metadata
- **Bi-temporal model**: `valid_at`, `expired_at`, `created_at` for each fact

Key fields:
- `expired_at = null` → fact is CURRENT and valid
- `expired_at = <timestamp>` → fact was SUPERSEDED by newer information

### Chat Processing Flow

The chat uses a **classification-based flow** with background processing:

```
User Message → POST /api/chat
                    │
                    ▼
           ┌─────────────────────────────────────┐
           │  1. Load Chat History (last 10 msgs) │
           │  2. Check if project needs onboarding│
           │     (no description → onboarding)    │
           │  3. Classify Message (DATA/QUESTION) │
           └─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   [DATA message]          [QUESTION message]
        │                       │
        ▼                       ▼
   Add to Pending Cache    Get Pending Messages
   (instant availability)  (before graph search)
        │                       │
        ▼                       ▼
   Background Task:        Search Knowledge Graph
   Add to Graphiti         (BM25 + semantic + BFS)
        │                       │
        └───────────┬───────────┘
                    ▼
           ┌────────────────────────────────────┐
           │  Generate Response (Gemini Pro):    │
           │  • System prompt + context guide    │
           │  • Project description (context)    │
           │  • Graph facts + entities           │
           │  • Pending messages (HIGHEST PRIO)  │
           │  • Chat history (for consistency)   │
           └────────────────────────────────────┘
                    │
                    ▼
           Save to Chat History (PostgreSQL)
                    │
                    ▼
           ChatResponse (reply, sources, message_type)
```

### Message Classification

Messages are classified using `gemini-2.5-flash-lite`:
- **DATA**: New information to store (expenses, tasks, items, updates)
- **QUESTION**: Queries requiring search and response (summaries, calculations)

For QUESTION messages, the classifier also generates an optimized `search_query`.

### Pending Cache

The pending cache (`pending_cache.py`) provides **instant message availability**:
- DATA messages are added to cache immediately (before graph processing)
- QUESTION messages include pending cache in context
- Background task processes message into Graphiti graph
- Message removed from cache after successful graph insertion

This ensures new information is immediately available for queries, even while Graphiti is processing.

### Chat History

Conversation history is stored in PostgreSQL (`chat_messages` table):
- Each message exchange (user + assistant) is saved
- Last N messages (configurable via `chat_history_limit`) included in LLM context
- Helps LLM maintain consistency across related questions (e.g., budget calculations)

Config setting:
```python
chat_history_limit: int = 10  # Number of recent messages in context
```

### Project Onboarding

When a project has no description set, the system enters **onboarding mode**:

1. **Detection**: Check if `project.description` is empty/null
2. **Onboarding Flow**: Uses `onboarding.txt` prompt instead of normal processing
3. **Conversation**: LLM asks user to describe the project, asks 3 clarifying questions
4. **Confirmation**: User confirms the final description
5. **Save**: LLM outputs `DESCRIPTION_CONFIRMED: <description>` marker, backend saves to DB

The onboarding uses chat history as a state machine - no explicit state tracking needed.

After onboarding completes, the project description is passed to all subsequent LLM calls via `format_response_prompt()`, providing context about the project's purpose.

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
4. **Hybrid Search**: Combines BM25 + semantic similarity + BFS graph traversal
5. **RRF Reranking**: Reciprocal Rank Fusion combines results from multiple search methods

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
llm_model: str = "gemini-2.5-flash-lite"       # Message classifier (fast)
llm_model_balanced: str = "gemini-2.5-flash"   # Reserved for future use
llm_model_pro: str = "gemini-3-flash-preview"  # Chat responses (requires Vertex AI)
graphiti_model: str = "gemini-2.5-flash"       # Entity extraction (best balance)
# Embeddings: gemini-embedding-001 (3072 dimensions, 100+ languages)

# Other settings
search_limit: int = 40                          # Max edges/nodes from search
chat_history_limit: int = 10                    # Messages in LLM context
```

**Currently used:**
- **Message classifier**: `llm_model` (gemini-2.5-flash-lite) - classifies DATA vs QUESTION
- **Chat responses**: `llm_model_pro` (gemini-3-flash-preview) - generates user-facing responses (**requires Vertex AI, not API key**)
- **Graphiti entity extraction**: `graphiti_model` (gemini-2.5-flash) - extracts entities/edges

**Model selection rationale** (based on comparative testing):
- `gemini-2.5-flash` chosen for Graphiti after testing flash-lite, flash, pro, and gemini-3 models
- gemini-3 models showed data loss issues (missing transactions in calculations)
- flash-lite was fastest but had more refusals on valid requests
- flash provides best balance of speed (~20% faster than pro) and accuracy

Key features:
- **Cross-language search**: EN query finds RU content and vice versa
- **Automatic entity extraction**: No manual intent detection needed
- **Temporal awareness**: Facts have validity periods

### Shared LLM Client (`llm.py`)

The `llm.py` module provides a singleton Gemini client shared between:
- `graphiti_client.py` - for entity extraction and embeddings
- `chat.py` - for response generation

```python
from .llm import get_gemini_client, generate_text

# Get raw client for Graphiti
client = get_gemini_client()

# Generate text directly
response = await generate_text("Your prompt here")
```

All models use Vertex AI with service account credentials.

## Environment Variables

### Vertex AI (required)

```bash
VERTEX_AI_PROJECT_ID=your-project-id
GCP_SERVICE_ACCOUNT_EMAIL=your-sa@project.iam.gserviceaccount.com
GCP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

### Setting up Vertex AI

1. Create service account in GCP Console with "Vertex AI User" role
2. Create key (JSON) and extract:
   - `project_id` → `VERTEX_AI_PROJECT_ID`
   - `client_email` → `GCP_SERVICE_ACCOUNT_EMAIL`
   - `private_key` → `GCP_PRIVATE_KEY`
3. Add to `.env` file

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
uvicorn app.main:app --reload --port 8000
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

### Database Migrations (Alembic)

```bash
cd backend-python

# Run migrations (creates/updates tables)
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Rollback last migration
alembic downgrade -1

# Show current revision
alembic current
```

Migrations are stored in `backend-python/alembic/versions/`.

## Prompts

All prompts are stored in `backend-python/app/prompts/`:

| File | Purpose |
|------|---------|
| `system.txt` | System prompt defining assistant role |
| `context_guide.txt` | How LLM should interpret graph data (expired_at, etc.) |
| `classifier.txt` | Message classification prompt (DATA vs QUESTION) |
| `response.txt` | Template combining system prompt + context + user message |
| `onboarding.txt` | Project onboarding flow (gathering project description) |

### Data Source Priority (in response.txt)

The LLM receives data from multiple sources with this priority:
1. **Pending Messages** (HIGHEST) - Just received, not yet in graph
2. **Knowledge Graph** - Facts and entity summaries from Graphiti
3. **Chat History** - Previous conversation for consistency
4. **Project Description** - Context about the project's purpose

### Prompt Loading

Prompts are loaded via `prompts/__init__.py`:
- `get_system_prompt()` → loads `system.txt`
- `get_context_guide()` → loads `context_guide.txt`
- `format_response_prompt()` → combines all prompts with context (including project description)
- `format_onboarding_prompt()` → loads `onboarding.txt` for new projects

### Modifying Prompts

1. Edit the `.txt` file in `backend-python/app/prompts/`
2. Restart the server (prompts are cached with `@lru_cache`)
3. Or call `clear_prompt_cache()` to reload

## API Endpoints

### Auth
- `POST /api/auth/register` - Register new user (rate limit: 3/min)
- `POST /api/auth/login` - Login user (rate limit: 5/min)
- `POST /api/auth/refresh` - Refresh access token using refresh token

### Chat (all require authentication)
- `POST /api/chat` - Send message, process through knowledge graph (rate limit: 30/min)
- `GET /api/chat/history` - Get chat history for a project
- `POST /api/chat/build-communities` - Build graph communities for a project
- `GET /api/chat/health` - Health check with pending cache stats

### Projects (all require authentication)
- `POST /api/projects` - Create project
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project
- `POST /api/projects/{id}/members` - Add member

### Request/Response Examples

```bash
# Login (returns access_token + refresh_token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'

# Send message (requires Bearer token)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"message": "Boris needs to buy wine", "projectId": "proj-123"}'

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
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
| "Empty response" | Check Vertex AI credentials are set |
| Import errors | Run `pip install -r requirements.txt` |
| Inconsistent calculations | Check `chat_history_limit` is adequate (default: 10) |
| Missing recent data | Pending cache may have cleared; check background task logs |

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
├── compare-models.sh      # Model comparison across scenarios
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
    ├── model-comparison-*/        # Model comparison results
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

### Model Comparison Testing

Compare different LLM models for Graphiti entity extraction:

```bash
cd tests
./compare-models.sh
```

This script:
1. Runs 3 scenarios with each configured model
2. Measures timing for each run
3. Exports entity/edge counts from Neo4j
4. Generates comparison report in `results/model-comparison-*/comparison.md`

Override model via environment variable:
```bash
GRAPHITI_MODEL="gemini-2.5-pro" uvicorn app.main:app --port 8000
```

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

## E2E Testing with Maestro

End-to-end tests use [Maestro](https://maestro.mobile.dev/) for multi-device mobile testing.

### Prerequisites

1. **Java 17+** required for Maestro 2.0
   ```bash
   # Check Java version
   java -version

   # If needed, use Homebrew Java
   export JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home
   ```

2. **Install Maestro**
   ```bash
   curl -Ls "https://get.maestro.mobile.dev" | bash
   ```

3. **Android emulators** configured and running

### Running E2E Tests

```bash
cd tests/e2e

# Run scenario on multiple emulators
python3 run_e2e_scenario.py ../scenarios/001-new-year-party.md

# Skip chat messages (only setup - useful for debugging)
python3 run_e2e_scenario.py ../scenarios/001-new-year-party.md --skip-chat
```

### E2E Test Structure

```
tests/e2e/
├── README.md              # Setup and usage guide
├── config.yaml            # Test configuration
├── run_e2e_scenario.py    # Multi-device test runner
└── flows/common/          # Reusable Maestro flows
    ├── login.yaml
    ├── create_project.yaml
    ├── join_project.yaml
    ├── add_member.yaml
    ├── complete_onboarding.yaml
    └── send_message.yaml
```

### Flutter Element Selection in Maestro

**IMPORTANT**: For Flutter widgets, use `Semantics` label instead of `tooltip` for element selection.

```dart
// In Flutter widget code
Semantics(
  label: 'Send message',  // ← Maestro finds this
  button: true,
  child: IconButton.filled(
    tooltip: 'Send',      // ← Maestro does NOT find this reliably
    ...
  ),
)
```

```yaml
# In Maestro test
- tapOn: "Send message"   # ✓ Works - uses Semantics label
- tapOn: "Send"           # ✗ May fail - tooltip not always accessible
```

### Key Widgets with Semantics

| Widget | Semantics Label | File |
|--------|-----------------|------|
| Send button | `Send message` | `chat_input.dart` |

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

## Critical Rules

### DO NOT change AI models without explicit user request

The following models are intentionally chosen and must NOT be changed:
```python
llm_model = "gemini-2.5-flash-lite"       # Classifier - fast, cost-effective
llm_model_pro = "gemini-3-flash-preview"  # Chat responses - requires Vertex AI auth
graphiti_model = "gemini-2.5-flash"       # Entity extraction - NOT gemini-3, NOT flash-lite
embedding_model = "gemini-embedding-001"  # NOT text-embedding-004
embedding_dim = 3072                      # NOT 768
```

**Important:** `gemini-3-flash-preview` does NOT support API keys. It requires Vertex AI authentication (OAuth2 or service account).

**Why gemini-2.5-flash for Graphiti:**
- Tested against flash-lite, pro, and gemini-3 models
- gemini-3 models showed data loss (missing transactions in budget calculations)
- flash-lite had more refusals on valid update/correction requests
- flash provides best balance: ~20% faster than pro with similar accuracy

### ALWAYS use --dart-define when running Flutter manually

When running `flutter run` directly (not via Makefile), you MUST pass `--dart-define` flags:

```bash
# Without --dart-define, app uses DEFAULT values:
# - API_URL = http://10.0.2.2:8000/api (Android emulator localhost)
# - ENVIRONMENT = dev
# This will NOT work on real devices!

# Correct way to run on real device:
flutter run --flavor staging --release -d <device_id> \
  --dart-define=ENVIRONMENT=staging \
  --dart-define=API_URL=https://dev-api.mindnest.one/api

# Or use Makefile which handles this automatically:
make run-staging
```

**API URLs by environment:**
- `dev`: `http://localhost:8000/api` (local backend)
- `staging`: `https://dev-api.mindnest.one/api`
- `prod`: `https://api.mindnest.one/api`

## Security

### Authentication

- **Password hashing**: bcrypt with 12 rounds (not SHA-256)
- **Tokens**: JWT with access token (15 min) + refresh token (7 days)
- **Password requirements**: Min 8 characters, at least 1 letter and 1 digit

### Rate Limiting

Rate limits are enforced via slowapi and vary by environment:

| Endpoint | Production | DEBUG mode |
|----------|------------|------------|
| Login | 5/minute | 100/minute |
| Register | 3/minute | 100/minute |
| Chat | 30/minute | 200/minute |

To enable DEBUG mode locally:
```bash
DEBUG=true uvicorn app.main:app --port 8000
```

### CORS

Allowed origins are configured via `ALLOWED_ORIGINS` env variable:
- Default: `http://localhost:3000,http://localhost:8080,https://mindnest.one,https://*.mindnest.one`

### Security Configuration

```python
# Required in production
SECRET_KEY=<min 32 chars>      # For JWT signing

# Optional
ALLOWED_ORIGINS=<comma-separated list>
DEBUG=false                     # Never true in production
```

### Mobile Token Handling

The mobile app (`ApiClient`) automatically:
1. Adds `Authorization: Bearer <token>` to all requests
2. Intercepts 401 responses
3. Calls `/api/auth/refresh` with the refresh token
4. Retries the original request with the new access token
5. Logs out the user if refresh fails

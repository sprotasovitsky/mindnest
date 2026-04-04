# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindNest is an AI-first platform for knowledge and task management through a chat interface. Users interact with a personal AI agent that manages knowledge items, tasks, and projects via a Graphiti knowledge graph.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + Graphiti (knowledge graph engine)
- **Mobile/Web**: Flutter + Dart (iOS, Android, Web from single codebase)
- **AI**: Google Gemini via Vertex AI (see Critical Rules for model names)
- **Knowledge Graph**: Graphiti on Neo4j — entity extraction, temporal relations, hybrid search
- **Databases**: Neo4j (knowledge graph), PostgreSQL (users, projects, chat history)
- **Infrastructure**: Docker Compose for local dev

## Project Structure

```
backend-python/         # FastAPI backend
├── app/
│   ├── main.py         # Entry point
│   ├── config.py       # All settings (Pydantic V2)
│   ├── graphiti_client.py  # Graphiti wrapper
│   ├── classifier.py   # DATA vs QUESTION message classifier
│   ├── pending_cache.py    # In-memory cache for instant message availability
│   ├── prompts/        # LLM prompt templates (.txt files)
│   └── routers/        # auth.py, chat.py, projects.py, oauth.py, mcp_tools.py
└── alembic/            # Database migrations

mobile/lib/
├── core/
│   ├── api/            # Dio-based ApiClient (auto token refresh on 401)
│   ├── models/         # @freezed data classes
│   ├── providers/      # @riverpod state management
│   └── repositories/   # Abstract interfaces + implementations
└── features/           # auth/, chat/, members/, profile/, projects/
    └── */presentation/ # screens/ + widgets/
```

## Essential Commands

### Backend (from `backend-python/`)
```bash
source venv/bin/activate && uvicorn app.main:app --reload --port 8000
docker-compose up -d          # Start Neo4j + PostgreSQL
alembic upgrade head          # Run migrations
```

### Mobile (from `mobile/`)
```bash
make setup                    # First-time: flutter pub get + xcodegen + pod install
make run-dev                  # Run against local backend
make run-staging              # Run against staging backend
dart run build_runner build   # Regenerate after @freezed/@riverpod/@JsonSerializable changes
```

## Architecture Principles

### Mobile — Clean Architecture layers
```
Presentation (ConsumerWidget/ConsumerStatefulWidget)
    └─► State (core/providers/ — @riverpod Notifier + @freezed State)
            └─► Repository (abstract interface + *RepositoryImpl)
                    └─► Data (ApiClient + @freezed models)
```

### Backend — Classification-based chat flow
1. Classify message: DATA (store) or QUESTION (search + answer)
2. DATA → add to pending cache immediately, background-process into Graphiti
3. QUESTION → search Graphiti graph + pending cache → generate response via Gemini
4. Pending cache ensures new info is instantly queryable before graph processing completes

## MCP Knowledge Base

MindNest has an MCP server connected to this workspace. Before answering questions about MindNest functionality, architecture, decisions, or status — **query the knowledge graph first** using `mcp__mindnest__search_knowledge`. The knowledge graph contains project vision, architecture details, backlog, security review, model comparison reports, and other project knowledge that may be more up-to-date than this file.

## Critical Rules

### DO NOT change AI models without explicit user request

```python
llm_model = "gemini-2.5-flash-lite"              # Classifier — fast, cost-effective, always-on CoT
llm_model_pro = "gemini-3.1-flash-lite-preview"  # Chat responses + iterative retrieval
graphiti_model = "gemini-3.1-flash-lite-preview"  # Entity extraction — thinking_budget=1024
embedding_model = "gemini-embedding-001"          # NOT text-embedding-004
embedding_dim = 3072                              # NOT 768
llm_thinking_level = "MEDIUM"                    # Default thinking level for gemini-3+ (NONE/MINIMAL/LOW/MEDIUM/HIGH)
```

`gemini-3.1-flash-lite-preview` requires global Vertex AI endpoint. Chat responses use `thinking_level=MEDIUM` (configurable via `LLM_THINKING_LEVEL` env var). Graphiti uses `thinking_budget=1024` (separate param, Graphiti's internal client doesn't support `thinking_level`).

**Important:** `max_output_tokens` on gemini-3+ counts thinking + text combined. With thinking enabled, it starves text output → empty response with `MAX_TOKENS`. Only set `max_output_tokens` when `LLM_THINKING_LEVEL=NONE`.

Classifier stays on `gemini-2.5-flash-lite` (regional, no thinking API) — CoT is handled via prompt suffix instead.

### Prompt and MCP description synchronization

Four places describe how data is stored and searched. They MUST use the same terminology and categories:

| File | Role | Audience |
|------|------|----------|
| `app/prompts/classifier.txt` | Decide what to extract from user message | Internal LLM (classifier) |
| `app/routers/mcp_tools.py` send_message docstring | Explain how to prepare data for storage | External LLM clients |
| `app/prompts/iterative_search.txt` | Decide if more search is needed | Internal LLM (retrieval) |
| `app/routers/mcp_tools.py` search_knowledge docstring | Explain how to search effectively | External LLM clients |

**Shared terminology for data types:** facts, events, tasks, preferences, relationships, states.

**Rules when editing any of these:**
1. Change one → review the other three for consistency
2. Examples must be **generic patterns**, never specific enough to hint at benchmark answers
3. Classifier extraction rules and MCP message guidance must describe the same principles — what counts as a "fact worth saving"
4. Iterative search logic and MCP search guidance must align — when and how to follow entity connections

### ALWAYS use --dart-define when running Flutter manually

```bash
# Without --dart-define, defaults are Android-emulator values — won't work on real devices
flutter run --flavor staging --release -d <device_id> \
  --dart-define=ENVIRONMENT=staging \
  --dart-define=API_URL=https://dev-api.mindnest.one/api

# Or just use the Makefile (handles this automatically)
make run-staging
```

### Use Semantics labels (not tooltips) for Maestro E2E tests

```dart
Semantics(
  label: 'Send message',  // Maestro finds this
  button: true,
  child: IconButton.filled(tooltip: 'Send', ...),  // Maestro does NOT reliably find tooltip
)
```

### Two-phase benchmark testing rule

Always use `/api/chat` for all benchmark testing including fill phase — never use MCP endpoints.

When running chat benchmark tests with `run_chat_test.py`, always use a two-phase approach to save cost:

**Phase 1 — Fill (fast settings):**
```bash
# Start server with no iterative search for ingestion
ITERATIVE_SEARCH_MAX=0 LLM_THINKING_LEVEL=NONE LLM_MAX_OUTPUT_TOKENS=200 uvicorn app.main:app --port 8000

# Fill projects (creates projects, ingests sessions, saves projects_map.json)
python -m benchmarks.longmemeval.run_chat_test \
    --email benchmark@example.com --password BenchmarkPass123! \
    --dataset benchmarks/longmemeval/data/test_5_new.json \
    --output-dir benchmarks/longmemeval/results/my_run \
    --fill-only
```

**Phase 2 — Ask (normal settings):**
```bash
# Restart server with normal settings
uvicorn app.main:app --port 8000

# Ask questions only (reads projects_map.json)
python -m benchmarks.longmemeval.run_chat_test \
    --email benchmark@example.com --password BenchmarkPass123! \
    --dataset benchmarks/longmemeval/data/test_5_new.json \
    --output-dir benchmarks/longmemeval/results/my_run \
    --ask-only
```

Why: the filling phase makes hundreds of API calls for onboarding + ingestion. `ITERATIVE_SEARCH_MAX=0` removes iterative search rounds. `LLM_THINKING_LEVEL=NONE` disables thinking for chat responses (not Graphiti). `LLM_MAX_OUTPUT_TOKENS=200` caps response length — safe to use only when thinking is NONE. Quality doesn't matter during fill, only data ingestion into Graphiti does.

### "termly" references in deployment configs are intentional

MindNest staging shares infrastructure with the Termly project: `termly-postgres`, `termly-nginx`, `termly-network`, `/opt/termly/` on EC2. This is not a naming error — see `backend-python/README.md` for details.

## Code Style

- All documentation and comments must be in **English**
- Python: PEP 8
- Dart: official Dart style guide
- App supports multiple end-user languages via multilingual embeddings (EN/RU search works cross-language)

## Common Gotchas

| Issue | Fix |
|-------|-----|
| "Graphiti not initialized" | Check Neo4j is running (`docker-compose up -d`) |
| "Empty response" | Check Vertex AI credentials in `.env` |
| Import errors (Python) | `pip install -r requirements.txt` |
| Build errors after model changes | `dart run build_runner build` |
| Flutter web: secure storage fails | Use `localhost`, not IP address |
| Inconsistent AI calculations | Increase `chat_history_limit` in `config.py` (default: 10) |
| `.xcodeproj` missing | Run `make setup` (gitignored, generated by XcodeGen) |

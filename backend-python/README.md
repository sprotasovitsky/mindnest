# MindNest Backend

AI-first knowledge and task management platform powered by [Graphiti](https://github.com/getzep/graphiti).

## Quick Start

```bash
cd backend-python

# Create virtual environment (first time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start databases
docker-compose up -d

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000

# Debug mode (relaxed rate limits, auto OAuth config)
DEBUG=true uvicorn app.main:app --reload --port 8000
```

### Local Ports
- Backend API: `http://localhost:8000`
- Neo4j Browser: `http://localhost:7474` (Bolt: `localhost:7687`)
- PostgreSQL: `localhost:5432`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                            │
│  ├── classifier.py — DATA vs QUESTION routing               │
│  ├── pending_cache.py — instant availability before graph   │
│  ├── graphiti_client.py — Graphiti wrapper                  │
│  └── llm.py — singleton Gemini client (shared)             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Graphiti (knowledge graph engine)                          │
│  - Entity/Edge extraction via LLM                           │
│  - Temporal invalidation (expired_at)                       │
│  - Hybrid search: BM25 + semantic + BFS                     │
└─────────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
           Neo4j                PostgreSQL
     (graph + vectors)      (users, auth, chat history)
```

### Chat Processing Flow

```
User Message → classify (DATA or QUESTION)
    │
    ├── DATA: add to pending cache → background Graphiti ingest
    │
    └── QUESTION: search Graphiti + pending cache → generate response
                  → save to chat history → return ChatResponse
```

### Temporal Model (Graphiti)

| Field | Meaning |
|-------|---------|
| `created_at` | When the fact was recorded |
| `valid_at` | When the fact became true |
| `expired_at` | When superseded (`null` = still valid) |

Example:
1. "Boris is buying alcohol" → `expired_at: null`
2. "Boris bought alcohol for 14000" → first fact gets `expired_at` set

## Project Structure

```
backend-python/
├── alembic/               # Migrations
│   └── versions/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Settings (Pydantic V2)
│   ├── database.py        # PostgreSQL async (SQLAlchemy)
│   ├── models.py          # SQLAlchemy models (User, Project, ChatMessage, OAuth*)
│   ├── graphiti_client.py # Graphiti wrapper
│   ├── llm.py             # Shared Gemini singleton
│   ├── classifier.py      # Message classifier (DATA/QUESTION)
│   ├── pending_cache.py   # In-memory cache
│   ├── mcp_server.py      # MCP server setup (fastapi-mcp)
│   ├── mcp_auth.py        # MCP OAuth token validation
│   ├── oauth_service.py   # OAuth 2.0 business logic
│   ├── prompts/           # LLM prompt templates
│   │   ├── system.txt
│   │   ├── context_guide.txt
│   │   ├── classifier.txt
│   │   ├── response.txt
│   │   └── onboarding.txt
│   └── routers/
│       ├── auth.py
│       ├── chat.py
│       ├── projects.py
│       ├── oauth.py
│       └── mcp_tools.py
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Environment Variables

```bash
# Vertex AI (required)
VERTEX_AI_PROJECT_ID=your-project-id
GCP_SERVICE_ACCOUNT_EMAIL=your-sa@project.iam.gserviceaccount.com
GCP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Databases
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mindnest123
DATABASE_URL=postgresql+asyncpg://mindnest:mindnest@localhost:5432/mindnest

# App
SECRET_KEY=<min 32 chars>    # JWT signing key
DEBUG=false                   # true → relaxed rate limits

# Optional
RESEND_API_KEY=               # Email sending
GOOGLE_CLIENT_ID=             # Google OAuth
APPLE_CLIENT_ID=              # Apple Sign-In
ALLOWED_ORIGINS=              # CORS origins (comma-separated)

# OAuth/MCP (production only; auto-configured in DEBUG mode)
OAUTH_ISSUER=https://api.mindnest.one
OAUTH_RESOURCE_URI=https://api.mindnest.one
```

### Setting up Vertex AI

1. Create service account in GCP Console with "Vertex AI User" role
2. Create JSON key and extract:
   - `project_id` → `VERTEX_AI_PROJECT_ID`
   - `client_email` → `GCP_SERVICE_ACCOUNT_EMAIL`
   - `private_key` → `GCP_PRIVATE_KEY`
3. Add to `.env`

## AI Models

See `app/config.py` for settings. **Do not change these without explicit request** — see CLAUDE.md Critical Rules.

```python
llm_model = "gemini-2.5-flash-lite"       # Classifier
llm_model_pro = "gemini-3-flash-preview"  # Chat responses (Vertex AI only)
graphiti_model = "gemini-2.5-flash"       # Entity extraction
embedding_model = "gemini-embedding-001"  # 3072 dimensions
```

### Shared LLM Client

```python
from .llm import get_gemini_client, generate_text

client = get_gemini_client()                     # Raw client for Graphiti
response = await generate_text("Your prompt")    # Direct text generation
```

## API Endpoints

### Auth

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Register (3/min) |
| `POST /api/auth/login` | Login (5/min) |
| `POST /api/auth/refresh` | Refresh access token |
| `GET /api/auth/me` | Get current user |
| `PATCH /api/auth/me` | Update profile |
| `POST /api/auth/verify-email` | Verify email token |
| `POST /api/auth/resend-verification` | Resend verification |
| `POST /api/auth/request-password-reset` | Request reset |
| `POST /api/auth/verify-reset-code` | Verify reset code |
| `POST /api/auth/reset-password` | Reset password |
| `POST /api/auth/change-password` | Change password |
| `DELETE /api/auth/account` | Delete account |
| `POST /api/auth/social/google` | Google OAuth |
| `POST /api/auth/social/apple` | Apple Sign-In |

### Chat

| Endpoint | Description |
|----------|-------------|
| `POST /api/chat` | Send message (30/min) |
| `GET /api/chat/history` | Get chat history |
| `POST /api/chat/build-communities` | Build graph communities |
| `GET /api/chat/health` | Health + cache stats |

### Projects

| Endpoint | Description |
|----------|-------------|
| `POST /api/projects` | Create project |
| `GET /api/projects` | List projects |
| `GET /api/projects/{id}` | Get project |
| `POST /api/projects/{id}/members` | Add member |

### Quick curl examples

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'

# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Boris needs to buy wine", "projectId": "proj-123"}'
```

## Database

### Migrations (Alembic)

```bash
alembic upgrade head                              # Apply all migrations
alembic revision --autogenerate -m "description"  # Create migration after model changes
alembic downgrade -1                              # Rollback one step
alembic current                                   # Show current revision
```

### Datetime Handling

All columns use timezone-aware UTC:
- Database: `TIMESTAMP WITH TIME ZONE`
- Models: `DateTime(timezone=True)` with `utc_now()` default
- Python: `datetime.now(timezone.utc)` — not `datetime.utcnow()` (deprecated)

### Neo4j Access

Credentials: `neo4j:mindnest123` — Browser: http://localhost:7474

```bash
# View entities
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 10"

# View edges (facts)
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH ()-[e:RELATES_TO]->() RETURN e.fact, e.created_at LIMIT 10"

# View expired facts
docker exec mindnest-neo4j cypher-shell -u neo4j -p mindnest123 \
  "MATCH ()-[e]->() WHERE e.expired_at IS NOT NULL RETURN e.fact LIMIT 10"
```

### PostgreSQL Access

Credentials: `mindnest:mindnest` — Database: `mindnest`

## Prompts

All prompts are in `app/prompts/` and cached with `@lru_cache`:

| File | Purpose |
|------|---------|
| `system.txt` | Assistant role definition |
| `context_guide.txt` | How LLM interprets `expired_at` and graph data |
| `classifier.txt` | DATA vs QUESTION classification |
| `response.txt` | Main response template (combines all context) |
| `onboarding.txt` | New project onboarding flow |

Data priority in `response.txt` (highest → lowest):
1. **Pending Messages** — just received, not yet in graph
2. **Knowledge Graph** — Graphiti facts + entity summaries
3. **Chat History** — recent conversation (default: last 10 messages)
4. **Project Description** — project context

To reload prompts without restart: call `clear_prompt_cache()`.

## MCP Integration (Claude Code)

MindNest exposes an MCP server at `/mcp` for Claude Code integration.

### OAuth 2.0 Flow (PKCE — RFC 6749, 7636)

```
1. Claude Code → GET /mcp
2. Server → 401 + WWW-Authenticate: Bearer resource_metadata="..."
3. Claude Code discovers OAuth metadata → registers dynamic client
4. Browser opens: /oauth/authorize?client_id=...&code_challenge=...
5. User logs in and grants consent
6. Code exchanged for tokens via POST /oauth/token
7. Claude Code uses Bearer token for all /mcp requests
```

### OAuth Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/.well-known/oauth-protected-resource` | Resource metadata |
| `/.well-known/oauth-authorization-server` | Auth server metadata |
| `/oauth/register` | Dynamic client registration |
| `/oauth/authorize` | Authorization (login + consent) |
| `/oauth/token` | Token exchange |
| `/oauth/revoke` | Token revocation |

### MCP Tools

| Tool | Scope | Description |
|------|-------|-------------|
| `list_projects` | read | List user's projects |
| `search_knowledge` | read | Search knowledge graph |
| `send_message` | write | Send message to project chat |

### Testing MCP Locally

Create `.mcp.json` in project root:
```json
{
  "mcpServers": {
    "mindnest": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Start with `DEBUG=true` (auto-configures OAuth for localhost). Open Claude Code in the project directory — first request triggers OAuth browser flow.

**Note:** Claude Code generates a new `client_id` each session, so the consent page appears every time.

### Security Features

- PKCE (S256 only)
- Refresh token rotation with replay attack detection
- SSRF protection on client metadata URLs
- XSS protection on all HTML pages

## Deployment

### Environments

| Environment | Backend API | Web (Flutter) |
|-------------|-------------|---------------|
| Local | `localhost:8000/api` | `localhost:8080` |
| Staging | `dev-api.mindnest.one/api` | `dev.mindnest.one` |
| Production | `api.mindnest.one/api` | `mindnest.one` |

### Shared Infrastructure with Termly

MindNest staging shares EC2 infrastructure with the Termly project. The "termly" references in deployment configs are **intentional**:

- `termly-postgres` — shared PostgreSQL container (MindNest uses database `mindnest_staging`)
- `termly-nginx` — shared Nginx reverse proxy
- `termly-network` — shared Docker network
- `/opt/termly/` — shared deployment directory on EC2

Nginx configs on EC2:
- `/opt/termly/nginx/conf.d/dev-api.mindnest.one.conf`
- `/opt/termly/nginx/conf.d/dev.mindnest.one.conf`

### CI/CD

Staging deploys automatically on push to `main` via `.github/workflows/staging-deploy.yml`:
1. Python backend tests
2. Flutter web build (staging config)
3. Docker image build + deploy to EC2

## Testing

```bash
cd tests
./run-scenario.sh scenarios/001-new-year-party.md
./compare-models.sh    # Compare LLM models for Graphiti extraction

# Override Graphiti model for testing
GRAPHITI_MODEL="gemini-2.5-pro" uvicorn app.main:app --port 8000
```

See `tests/e2e/README.md` for E2E testing with Maestro.

## Resources

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Graphiti Documentation](https://help.getzep.com/graphiti)

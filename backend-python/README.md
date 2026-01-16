# MindNest Backend (Graphiti)

AI-first knowledge and task management platform powered by [Graphiti](https://github.com/getzep/graphiti).

## Architecture

```
┌─────────────────────────────────────────────┐
│              Flutter App                     │
└─────────────────────┬───────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────┐
│         FastAPI Backend (Python)             │
│  ┌───────────────────────────────────────┐  │
│  │         Graphiti Core                 │  │
│  │  - Episode ingestion                  │  │
│  │  - Entity/Edge extraction (LLM)       │  │
│  │  - Hybrid search                      │  │
│  │  - Temporal invalidation              │  │
│  │  - Emergent Schema                    │  │
│  └───────────────────────────────────────┘  │
└─────────────────────┬───────────────────────┘
                      │ Bolt
┌─────────────────────▼───────────────────────┐
│              Neo4j Database                  │
│  - Graph storage                             │
│  - Vector indices (embeddings)               │
│  - BM25 indices (keyword search)             │
└─────────────────────────────────────────────┘
```

## What Graphiti Replaces

| Old (Java) | New (Graphiti) |
|------------|----------------|
| KnowledgeItem entity | Graphiti EntityNode |
| KnowledgeRelation (21 types) | Emergent edge types |
| SUPERSEDES relation | `expired_at` + edge invalidation |
| IntentDetectionEngine | Graphiti LLM extraction |
| VectorSearchService + Qdrant | Graphiti hybrid search |
| GraphService | Graphiti graph traversal |
| ~6000 LOC Java | ~300 LOC Python |

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker
- GCP Service Account with Vertex AI access

### 2. Setup

```bash
cd backend-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your Vertex AI credentials
```

### 3. Start Neo4j

```bash
docker-compose up -d
```

Wait for Neo4j to be ready:
```bash
docker-compose logs -f neo4j
# Look for "Started."
```

### 4. Test Graphiti

```bash
python scripts/test_graphiti.py
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234"}'

# Send a message (requires Bearer token)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Buy milk tomorrow", "projectId": "project-uuid"}'
```

## API Endpoints

### Auth

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Register new user |
| `POST /api/auth/login` | Login user |
| `POST /api/auth/refresh` | Refresh access token |
| `GET /api/auth/me` | Get current user info |
| `POST /api/auth/verify-email` | Verify email with token |
| `POST /api/auth/resend-verification` | Resend verification email |
| `POST /api/auth/request-password-reset` | Request password reset |
| `POST /api/auth/verify-reset-code` | Verify reset code |
| `POST /api/auth/reset-password` | Reset password |
| `POST /api/auth/change-password` | Change password |
| `DELETE /api/auth/account` | Delete account |
| `POST /api/auth/social/google` | Google OAuth login |
| `POST /api/auth/social/apple` | Apple Sign-In |

### Chat

| Endpoint | Description |
|----------|-------------|
| `POST /api/chat` | Send message, get AI response |
| `GET /api/chat/history` | Get chat history for project |
| `GET /api/chat/health` | Health check with stats |

### Projects

| Endpoint | Description |
|----------|-------------|
| `POST /api/projects` | Create project |
| `GET /api/projects` | List user's projects |
| `GET /api/projects/{id}` | Get project details |
| `PUT /api/projects/{id}` | Update project |
| `POST /api/projects/{id}/members` | Add member |
| `GET /api/projects/{id}/members` | List members |

### POST /api/chat

Send a message to the AI assistant.

**Request:**
```json
{
  "message": "Buy milk tomorrow, assigned to Petya",
  "projectId": "project-uuid"
}
```

**Response:**
```json
{
  "reply": "I've noted that you need to buy milk...",
  "sources": ["Petya is assigned to buy milk"],
  "message_type": "DATA"
}
```

## How It Works

### 1. Episode Ingestion

When a message is sent:
1. Graphiti receives the message as an "episode"
2. LLM extracts entities (people, tasks, expenses, etc.)
3. LLM creates edges between entities
4. Edges are normalized (Emergent Schema)
5. Temporal metadata is extracted (deadlines, etc.)

### 2. Edge Invalidation

When information is updated:
1. Graphiti detects conflicting edges
2. Old edges get `expired_at` timestamp
3. New edges are created
4. History is preserved (bi-temporal model)

Example:
```
Message 1: "Buy milk tomorrow, assigned to Petya"
  → Creates: Petya --[assigned_to]--> Task:BuyMilk

Message 2: "Petya bought the milk"
  → Invalidates: Petya --[assigned_to]--> Task:BuyMilk (expired_at = now)
  → Creates: Petya --[completed]--> Task:BuyMilk
```

### 3. Hybrid Search

Search combines:
- **Semantic**: Embedding similarity
- **BM25**: Keyword matching
- **Graph**: Traversal from matching nodes

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL async connection URL | Yes (prod) |
| `NEO4J_URI` | Neo4j Bolt URI | No (default: localhost:7687) |
| `NEO4J_USER` | Neo4j username | No (default: neo4j) |
| `NEO4J_PASSWORD` | Neo4j password | Yes (prod) |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Yes |
| `VERTEX_AI_PROJECT_ID` | GCP Project ID | Yes |
| `GCP_SERVICE_ACCOUNT_EMAIL` | Service account email | Yes |
| `GCP_PRIVATE_KEY` | Service account private key | Yes |
| `RESEND_API_KEY` | Resend.com API key for emails | No |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | No |
| `APPLE_CLIENT_ID` | Apple Sign-In service ID | No |
| `DEBUG` | Enable debug mode | No (default: false) |

See `.env.example` for full list with descriptions.

## Development

### Project Structure

```
backend-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── graphiti_client.py   # Graphiti wrapper
│   └── routers/
│       └── chat.py          # Chat endpoints
├── scripts/
│   └── test_graphiti.py     # Test script
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

### Running Tests

```bash
# Test Graphiti integration
python scripts/test_graphiti.py

# Test API (with server running)
curl http://localhost:8000/api/chat/health
```

## Neo4j Browser

Access Neo4j browser at http://localhost:7474

Useful queries:
```cypher
// See all nodes
MATCH (n) RETURN n LIMIT 50

// See all edges
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 50

// Find tasks
MATCH (n:Entity) WHERE n.name CONTAINS 'task' RETURN n

// Find expired edges
MATCH (a)-[r]->(b) WHERE r.expired_at IS NOT NULL RETURN a, r, b
```

## Resources

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [Zep Paper (arXiv)](https://arxiv.org/abs/2501.13956)

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
- Google API Key (for Gemini)

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
# Edit .env and add your GOOGLE_API_KEY
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

# Send a message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Buy milk tomorrow, assigned to Petya",
    "project_id": "test_project",
    "user_id": "user_123"
  }'

# Search
curl -X POST http://localhost:8000/api/chat/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What tasks does Petya have?",
    "project_id": "test_project"
  }'
```

## API Endpoints

### POST /api/chat/message

Send a message to the knowledge graph.

**Request:**
```json
{
  "message": "Buy milk tomorrow, assigned to Petya",
  "project_id": "project_123",
  "user_id": "user_456",
  "user_name": "Ivan"  // optional
}
```

**Response:**
```json
{
  "reply": "I've created a task to buy milk...",
  "sources": ["Petya is assigned to buy milk"],
  "confidence": 1.0,
  "entities_extracted": 2
}
```

### POST /api/chat/search

Search the knowledge graph.

**Request:**
```json
{
  "query": "What tasks does Petya have?",
  "project_id": "project_123",
  "limit": 10
}
```

**Response:**
```json
{
  "facts": [
    {
      "fact": "Petya is assigned to buy milk",
      "valid_at": "2025-01-04T10:00:00",
      "expired_at": null
    }
  ],
  "entities": [
    {
      "uuid": "...",
      "name": "Petya",
      "summary": "Team member"
    }
  ]
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

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `mindnest123` |
| `GOOGLE_API_KEY` | Google AI API key | required |
| `DEBUG` | Enable debug mode | `true` |

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

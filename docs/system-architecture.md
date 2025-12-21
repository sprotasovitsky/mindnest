# MindNest - System Architecture

## 1. Overview

MindNest is a knowledge and task management platform with chat interface. Users interact with an AI agent that:
- Saves information (facts, expenses, decisions, notes)
- Creates and tracks tasks
- Answers questions about saved data
- Supports multiple users in one project

## 2. Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Java 21 + Spring Boot 3.2 |
| AI/LLM | Google Vertex AI (Gemini 2.5 Flash-Lite) |
| Embeddings | gemini-embedding-001 (3072 dimensions) |
| Graph DB | Neo4j (knowledge + relations) |
| Vector DB | Qdrant (semantic search) |
| Auth DB | PostgreSQL (users, projects) |
| Mobile | Flutter + Dart |

## 3. Core Principle: IMMUTABLE Architecture

**No UPDATE. No DELETE at database level.**

All changes create NEW nodes with relations:

| User Action | Database Operation |
|-------------|-------------------|
| Create | CREATE new KnowledgeItem |
| Update | CREATE new item + SUPERSEDES → old |
| Delete | CREATE `[DELETED] description` + SUPERSEDES → original |
| Refund | CREATE `Refund X` + CONTRADICTS → purchase |
| Complete task | UPDATE task.status = DONE (exception: status can be changed) |

### Relation Types

| Relation | Meaning | Graph Depth |
|----------|---------|-------------|
| SUPERSEDES | Replaces/updates | ∞ (follow chain) |
| CONTRADICTS | Cancels (refund) | ∞ |
| DEPENDS_ON | Depends on | ∞ |
| BLOCKS | Blocks | ∞ |
| BELONGS_TO | Belongs to category | 1 level |
| ASSIGNED_TO | Task assigned to | 1 level |
| RELATES_TO | General relation | 1 level |

## 4. Message Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User Message                                                │
│  "Bought wine 8500 and beer 1200. Task for Boris done."      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: DECOMPOSITION (LLM Call #1)                         │
│                                                              │
│  Input: Full message                                         │
│  Output: [                                                   │
│    "Bought wine 8500",                                       │
│    "Bought beer 1200",                                       │
│    "Task for Boris done"                                     │
│  ]                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ (for each chunk)
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: INTENT DETECTION (LLM Call #2, #3, ...)             │
│                                                              │
│  Input: chunk + conversation context                         │
│  Output: {                                                   │
│    "intent": "SAVE",                                         │
│    "type": "EXPENSE",                                        │
│    "content": "Bought wine 8500",                            │
│    "properties": {"amount": 8500, "item": "wine"},           │
│    "relations": []                                           │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: EXECUTION                                           │
│                                                              │
│  SAVE → create_knowledge → Neo4j + Qdrant                    │
│  TASK (TODO) → create_task                                   │
│  TASK (DONE) → complete_task_by_title                        │
│  SEARCH → search + graph expansion + LLM answer              │
│  CHAT → no tool                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: RESPONSE GENERATION (LLM Call #N)                   │
│                                                              │
│  Generates natural language response in English              │
└─────────────────────────────────────────────────────────────┘
```

**LLM Calls per message: N + 2** (where N = number of chunks)

## 5. Intent Types

| Intent | When | Tool |
|--------|------|------|
| SAVE | Expenses, facts, deletions | create_knowledge |
| TASK | Create/complete task | create_task / complete_task_by_title |
| SEARCH | Questions, "show", "how much" | search_knowledge + graph expansion |
| CHAT | Greetings | none |

### Priority: SEARCH > TASK > SAVE > CHAT

## 6. Prompts

All prompts in `backend/src/main/resources/prompts/`:

| File | Purpose |
|------|---------|
| decomposition-prompt.txt | Split message into chunks |
| intent-detection-prompt.txt | Classify chunk, extract data (30 examples) |
| search-response-prompt.txt | Teach LLM to read graph |
| action-response-prompt.txt | Confirm SAVE/TASK actions |
| system-prompt.txt | General agent rules |

### Key Decomposition Rules

- Each expense = separate chunk
- Each task for DIFFERENT people = separate chunks
- Task for ONE person with MULTIPLE items = ONE chunk (don't split!)
- Questions = never split

### Key Intent Detection Rules

- "?" at end → always SEARCH
- "delete X" → SAVE with `[DELETED] X` + SUPERSEDES
- "returned X" → SAVE with CONTRADICTS to original

## 7. Data Model

### 7.1 KnowledgeItem (Neo4j)

```
(:KnowledgeItem {
  id: UUID,
  content: String,
  type: KnowledgeType,       // FACT, TASK, NOTE, DECISION
  status: TaskStatus,        // TODO, IN_PROGRESS, DONE, BLOCKED, CANCELLED
  assignee: String,          // Person name (may be null)
  deadline: LocalDate,
  amount: BigDecimal,        // For expenses
  ownerId: UUID,             // Who created this
  projectId: UUID,
  createdAt: Instant,
  updatedAt: Instant,
  deletedAt: Instant
})
```

### 7.2 Vector Payload (Qdrant)

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "type": "TASK",
  "content": "truncated (1000 chars)",
  "ownerId": "uuid",
  "status": "TODO",
  "createdAt": epoch_millis
}
```

## 8. Key Classes

```
backend/src/main/java/com/mindnest/
├── agent/
│   ├── AgentService.java      # Main orchestrator (~1500 lines)
│   ├── ToolExecutor.java      # Routes tool calls
│   └── tools/
│       ├── KnowledgeTools.java
│       ├── TaskTools.java
│       ├── ProjectTools.java
│       └── TimeTools.java
├── service/
│   ├── GraphService.java      # Graph expansion
│   ├── VectorSearchService.java
│   └── EmbeddingService.java
└── repository/
    └── KnowledgeRepository.java
```

### AgentService Methods

| Method | Purpose |
|--------|---------|
| processMessage() | Main entry point |
| decompose() | Split message (LLM) |
| detectChunkIntent() | Classify chunk (LLM) |
| executeSave() | Create knowledge item |
| executeTask() | Create/complete task |
| executeSearch() | Search + graph expansion |
| generateCombinedResponse() | Final response (LLM) |

### Tools

| Tool | Description |
|------|-------------|
| create_knowledge | Save fact/note/decision |
| search_knowledge | Semantic search |
| create_task | Create task with deadline/assignee |
| complete_task_by_title | Find and mark task DONE |
| search_tasks | Search tasks |
| get_active_tasks | List active tasks |
| create_relation | Link two items |
| get_related | Find related items |
| find_path | Find path between items |
| get_current_date | Current date |

## 9. Known Issues (Test v23)

### 9.1 Task Completion Only First Match

**Problem**: User has 4 tasks, says "Done!" → only 1 marked DONE

**Cause**: `completeTaskByTitle()` uses semantic search, returns after first match:
```java
for (SearchResult result : results) {
    if (result.score() > threshold) {
        task.setStatus(TaskStatus.DONE);
        return Optional.of(updated);  // ← Returns immediately!
    }
}
```

### 9.2 Expense Search Incomplete

**Problem**: Sum shows 6000 instead of 35850

**Cause**: Semantic search doesn't find all expense items

### 9.3 "My items" Shows Wrong Items

**Problem**: Vika asks "my items" → shows other users' items

**Cause**: Semantic search for "my items" doesn't filter by ownerId

### 9.4 Assignee Field Often Null

**Problem**: Assignee stored in content text `[assigned to: Boris]` instead of field

## 10. Open Questions

### 10.1 Task Completion Strategy

When user says "my task done", should we:
- A) Complete most semantically similar task (current, unreliable)
- B) Complete all tasks for that user (too aggressive?)
- C) Ask for clarification if multiple tasks
- D) Use assignee field + filter by current user

### 10.2 Expense Aggregation

How to handle "total expenses" queries:
- A) Semantic search (current, incomplete)
- B) Direct query by type + amount field
- C) Create separate EXPENSE type

### 10.3 "My items" Query

How to handle:
- A) Semantic search (current, wrong results)
- B) Filter by ownerId only
- C) Combine: ownerId filter + semantic

## 11. Proposed Fixes Priority

### High Priority

1. Fix task completion - use assignee context in matching
2. Fix expense aggregation - query by amount field
3. Fix "my items" - filter by ownerId

### Medium Priority

4. Store assignee in field, not content text
5. Increase search limits for aggregations

### Low Priority

6. Add EXPENSE type separate from FACT
7. Configurable graph expansion limits

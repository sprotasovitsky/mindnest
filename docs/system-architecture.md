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
│   ├── AgentService.java           # Main orchestrator (145 lines)
│   ├── IntentDetectionEngine.java  # Message decomposition & intent detection
│   ├── IntentExecutor.java         # Routes intents to handlers
│   ├── ResponseGenerator.java      # LLM response generation
│   ├── UserContextBuilder.java     # User/project context building
│   ├── ToolDeclarationFactory.java # Tool/function declarations
│   ├── ToolExecutor.java           # Routes tool calls
│   ├── ChunkResult.java            # Result of chunk processing
│   ├── ChunkIntent.java            # Detected intent record
│   ├── RelationIntent.java         # Relation intent record
│   ├── handler/
│   │   ├── IntentHandler.java      # Handler interface
│   │   ├── SaveIntentHandler.java  # SAVE intent
│   │   ├── TaskIntentHandler.java  # TASK intent + clarification
│   │   ├── SearchIntentHandler.java # SEARCH intent
│   │   └── ChatIntentHandler.java  # CHAT intent
│   └── tools/
│       ├── KnowledgeTools.java
│       ├── TaskTools.java
│       ├── ProjectTools.java
│       └── TimeTools.java
├── service/
│   ├── GraphService.java           # Graph expansion
│   ├── VectorSearchService.java    # Qdrant semantic search
│   └── EmbeddingService.java       # Embeddings via Gemini
└── repository/
    └── KnowledgeRepository.java
```

### Agent Service Architecture

| Service | Purpose |
|---------|---------|
| AgentService | Main orchestrator, coordinates pipeline |
| IntentDetectionEngine | decompose(), detectChunkIntent() |
| IntentExecutor | Routes to Save/Task/Search/Chat handlers |
| ResponseGenerator | generateSearchResponse(), generateActionResponse() |
| UserContextBuilder | buildUserContext(), getPendingTaskIds() |
| ToolDeclarationFactory | Creates 17 tool declarations for Gemini |

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

## 9. Known Issues and Fixes

### 9.1 Task Completion ✅ FIXED

**Problem**: User has 4 tasks, says "Done!" → only 1 marked DONE

**Solution**: Implemented clarification flow in TaskIntentHandler:
- If 0 tasks → "You have no active tasks"
- If 1 task → Complete immediately
- If N tasks → Show numbered list, ask which ones to complete
- User can respond with "all", "1 and 3", or task name

```java
// TaskIntentHandler.java
if (needsClarification) {
    return requestTaskClarification(projectId, userId);  // Shows numbered list
}
if (completeAll) {
    return completeAllTasks(projectId, userId);
}
if (selectedIndices != null) {
    return completeSelectedTasks(selectedIndices, pendingTaskIds);
}
```

### 9.2 Expense Search Incomplete (Open)

**Problem**: Sum shows 6000 instead of 35850

**Cause**: Semantic search doesn't find all expense items

**Potential fix**: Use type filter + amount field aggregation

### 9.3 "My items" Shows Wrong Items (Open)

**Problem**: Vika asks "my items" → shows other users' items

**Cause**: Semantic search for "my items" doesn't filter by ownerId

**Potential fix**: Combine ownerId filter with semantic search

### 9.4 Assignee Field Often Null (Open)

**Problem**: Assignee stored in content text instead of field

**Potential fix**: Intent detection should extract assignee to field

## 10. Remaining Tasks

### High Priority
1. ~~Fix task completion~~ ✅ Done - clarification flow implemented
2. Fix expense aggregation - query by amount field
3. Fix "my items" - filter by ownerId

### Medium Priority
4. Store assignee in field, not content text
5. Increase search limits for aggregations

### Low Priority
6. Add EXPENSE type separate from FACT
7. Configurable graph expansion limits

## 11. Architecture Improvements (Completed)

### AgentService Refactoring ✅

**Before**: AgentService was 1,727 lines (god class)

**After**: Split into focused services:
| Service | Lines | Responsibility |
|---------|-------|----------------|
| AgentService | 145 | Orchestration only |
| IntentDetectionEngine | 180 | Decompose + detect intent |
| IntentExecutor | 65 | Route to handlers |
| ResponseGenerator | 120 | LLM responses |
| UserContextBuilder | 130 | User context |
| ToolDeclarationFactory | 280 | Tool declarations |
| Intent handlers | 390 | Save/Task/Search/Chat |

**Benefits**:
- 92% reduction in main class size
- Single responsibility per class
- Easier testing and maintenance
- New handlers added without modifying existing code

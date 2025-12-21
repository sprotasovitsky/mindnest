# Current Issues and Roadmap

Last updated: 2025-12-21

## Recently Fixed

### Task Completion Clarification ✅
**Issue**: When user said "Done!" with multiple active tasks, system only completed the first matching task.

**Solution**: Implemented clarification flow in `TaskIntentHandler`:
- 0 tasks → "You have no active tasks"
- 1 task → Complete immediately (no question)
- N tasks → Show numbered list, ask which ones
- User can respond with "all", "1 and 3", or task name

**Files changed**:
- `TaskIntentHandler.java` - Main clarification logic
- `TaskTools.java` - Added `getActiveTasksForUser()`, `completeTasksByIds()`
- `KnowledgeRepository.java` - Added `findActiveTasksForUser()` query
- `intent-detection-prompt.txt` - Added clarification examples

### AgentService Refactoring ✅
**Issue**: AgentService was 1,727 lines (god class anti-pattern).

**Solution**: Split into focused services:
| Service | Lines | Responsibility |
|---------|-------|----------------|
| AgentService | 145 | Orchestration only |
| IntentDetectionEngine | 180 | Decompose + detect intent |
| IntentExecutor | 65 | Route to handlers |
| ResponseGenerator | 120 | LLM responses |
| UserContextBuilder | 130 | User context |
| ToolDeclarationFactory | 280 | Tool declarations |
| SaveIntentHandler | 110 | SAVE intent |
| TaskIntentHandler | 210 | TASK intent + clarification |
| SearchIntentHandler | 55 | SEARCH intent |
| ChatIntentHandler | 15 | CHAT intent |

**Benefits**: 92% reduction in main class, single responsibility, easier testing.

---

## Open Issues

### High Priority

#### 1. Expense Search Incomplete
**Symptom**: "How much did we spend?" shows 6000 instead of 35850

**Cause**: Semantic search doesn't find all expense items

**Potential solutions**:
- A) Use type=EXPENSE filter + amount field aggregation
- B) Increase search limit for aggregation queries
- C) Create dedicated expense query in repository

**Files to modify**:
- `SearchIntentHandler.java`
- `KnowledgeRepository.java`

#### 2. "My items" Shows Wrong Items
**Symptom**: User asks "my items" → shows other users' items

**Cause**: Semantic search for "my items" matches any item, doesn't filter by ownerId

**Potential solutions**:
- A) Add ownerId filter to vector search
- B) Combine ownerId filter with semantic search
- C) Special handling in SearchIntentHandler for "my" queries

**Files to modify**:
- `SearchIntentHandler.java`
- `VectorSearchService.java`

#### 3. Assignee Field Often Null
**Symptom**: Task assignee stored as `[assigned to: Boris]` in content text instead of `assignee` field

**Cause**: Intent detection extracts assignee but it's not being saved to the field

**Potential solutions**:
- A) Fix intent detection to populate properties.assignee
- B) Parse assignee from content in TaskTools
- C) Update create_task tool to use assignee from properties

**Files to modify**:
- `intent-detection-prompt.txt`
- `TaskTools.java`

---

### Medium Priority

#### 4. Improve Search Result Limits
**Issue**: Default limit of 10 may miss relevant items for aggregation queries

**Solution**: Dynamic limit based on query type (aggregation → 50, normal → 10)

#### 5. Better Date Parsing
**Issue**: Dates without year sometimes get wrong year

**Solution**: Improve TimeTools logic for year inference

---

### Low Priority

#### 6. Separate EXPENSE Type
**Issue**: Expenses stored as FACT type, hard to query separately

**Solution**: Add EXPENSE as separate KnowledgeType

#### 7. Configurable Graph Expansion
**Issue**: Graph expansion limits hardcoded

**Solution**: Move limits to application.yml

---

## Architecture Notes

### Current Pipeline
```
User Message
    │
    ▼
IntentDetectionEngine.decompose()      # Split into chunks
    │
    ▼ (for each chunk)
IntentDetectionEngine.detectChunkIntent()  # Get intent + properties
    │
    ▼
IntentExecutor.processChunk()          # Route to handler
    │
    ├─► SaveIntentHandler              # create_knowledge
    ├─► TaskIntentHandler              # create_task / complete
    ├─► SearchIntentHandler            # search + graph expansion
    └─► ChatIntentHandler              # no tools
    │
    ▼
ResponseGenerator.generateCombinedResponse()  # LLM response
```

### Immutable Architecture
- No UPDATE/DELETE at database level
- Changes create NEW nodes with relations:
  - Update → SUPERSEDES relation
  - Delete → `[DELETED]` marker + SUPERSEDES
  - Refund → CONTRADICTS relation
  - Complete task → `[DONE]` marker + SUPERSEDES

### Key Principles
1. **No keyword matching in code** - Use semantic search only
2. **Language-agnostic** - Embeddings handle 100+ languages
3. **LLM for intent detection** - Let model extract structure
4. **Clarification over assumption** - Ask user when ambiguous

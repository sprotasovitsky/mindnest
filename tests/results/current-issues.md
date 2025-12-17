# Current Issues and Improvements Needed
Date: 2025-12-17 (Updated after v7)

## Critical Issues
None at this time - all core functionality working.

## Recently Fixed (v7)

### [FIXED] Graph Relationships Not Used
**Status**: FIXED in v7
**Solution implemented**: Added explicit tools to AgentService:
- `create_relation` - Link two items with relation type
- `get_related` - Find connected items (with depth)
- `find_path` - Discover connection path between items
- Relation types: RELATES_TO, DEPENDS_ON, SUPPORTS, CONTRADICTS, REFERENCES, DERIVED_FROM, SIMILAR_TO

### [FIXED] No Explicit Delete Confirmation
**Status**: FIXED in v6
**Solution implemented**: Added `preview_delete` and `confirm_delete` tools.

### [FIXED] Search Result Ordering (Recency)
**Status**: FIXED in v7
**Solution implemented**: Added recency boost to search:
- Items < 30 days get up to 5% score boost
- Most recent items prioritized when scores are close
- createdAt stored in vector metadata

### [FIXED] Multi-Language Support (Russian)
**Status**: FIXED in v6/v7
**Solution implemented**:
- Added Russian keywords to intent detection
- TASK: "создай задачу", "добавь задачу", "задача для", "назначь"
- COMPLETE: "выполнена", "сделана", "готово", "завершена"
- DELETE: "удали", "убери", "отмени", "верни"
- SEARCH: "сколько", "что", "когда", "где", "какой", "покажи", "найди"
- SAVE: "Потратил", "Купил", "Бюджет", "Решили"
- RELATION: "связь", "связать", "связано с", "зависит от"

### [FIXED] Delete Too Aggressive
**Status**: FIXED in v7
**Problem**: Delete with semantic search deleted related but unintended items
**Solution**: Combined similarity + keyword matching:
- Delete if: score > 0.8 (very high match) OR (score > 0.6 AND keyword match)
- Keywords must be >= 4 characters

## Known Limitations

### 1. UPDATE Intent - Cross-Language Limitation
**Severity**: Low (was Medium, now mostly fixed)
**Status**: Improved in v7
**What works now**:
- Russian: "На самом деле X, а не Y" ✓
- Russian: "Измени X на Y" ✓
- Russian: "Поменяй X на Y" ✓
- English: "Actually it was X, not Y" ✓
- English: "Change X to Y" ✓

**Known limitation**: Cross-language UPDATE doesn't work
- Example: "Change grocery budget" won't find "бюджет на продукты"
- Reason: text-embedding-004 similarity is only 0.40 for cross-language
- **Workaround**: Use same language for query as stored data

### 2. Duplicate Detection Threshold
**Severity**: Low
**Description**: 85% similarity threshold for duplicate detection may be too strict or too loose depending on content type.
**Impact**: Some near-duplicates may slip through, or legitimate similar items may be blocked.
**Solution**: Consider content-type-specific thresholds or user confirmation for borderline cases.

### 3. Task Assignee Search
**Severity**: Low
**Description**: Assignee is included in task content as `[assigned to: Name]` for searchability.
**Limitation**: Works via semantic search, not exact match. May find wrong task if multiple similar tasks exist.

## Potential Improvements

### 1. Task Status Tracking
- Add "IN_PROGRESS" status between "TODO" and "DONE"
- Track who completed the task and when
- Add task priority levels

### 2. Knowledge Item Versioning
- Keep history of changes to items
- Allow viewing previous versions
- Track who made changes

### 3. Better Date Understanding
- Parse relative dates like "next Monday", "in 2 weeks"
- Handle time zones
- Support recurring tasks/events

### 4. Automatic Relation Creation
- Automatically create SIMILAR_TO relations for high similarity items
- Suggest relations based on content analysis
- Create SUBTASK_OF relations when decomposing tasks

## Test Coverage Gaps

### Not Tested:
1. Concurrent multi-user editing
2. Very long messages (>1000 words)
3. Special characters in content (emoji, unicode)
4. Large projects (100+ items)
5. Cross-project search
6. Item deletion and re-creation
7. Error recovery (database down, API timeout)
8. Graph traversal with many relations

## Performance Concerns

### Observed:
- Intent detection adds ~500ms latency (separate LLM call)
- Vector search is fast (<100ms)
- Neo4j queries are fast (<50ms)
- Recency boost adds negligible overhead

### To Monitor:
- Scaling with large number of items per project
- Concurrent user load
- Memory usage with many active projects
- Graph query performance with deep relation traversal

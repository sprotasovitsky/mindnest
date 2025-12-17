# Scenario 001 - Iteration 3 (Regression Test)
Date: 2025-12-17

## Prompt Version: 2 (tests/prompts/prompt-v2.txt)

## Purpose
Verify no regression after implementing two-step intent detection for test 002.

## Results

### Save Operations
| Step | User | Content | Status |
|------|------|---------|--------|
| 2.1 | Andrey | Party planning | SAVED |
| 2.2 | Boris | Alcohol list | SAVED |
| 2.3 | Vika | Food list | SAVED |
| 2.4 | Galya | Decorations list | SAVED |
| 3.1 | Andrey | Tasks for Boris/Vika/Galya | SAVED |
| 3.2 | Andrey | Clean apartment task | SAVED |
| 4.1 | Boris | Alcohol expenses 12700 | SAVED |
| 4.3 | Vika | Food expenses 6800 | SAVED |
| 4.5 | Galya | Decorations expenses 2000 | SAVED |

**Save rate: 9/9 = 100%**

### Task Completion
| Step | User | Task | Status |
|------|------|------|--------|
| 4.2 | Boris | Alcohol task | NOT FOUND |
| 4.4 | Vika | Food task | NOT FOUND |

**Issue**: complete_task_by_title cannot find tasks. Tasks saved as single message, not individual items.

### Delete Operations
| Step | User | Action | Status |
|------|------|--------|--------|
| 5.1 | Galya | Remove Christmas tree | NOT FOUND |

**Note**: Christmas tree was mentioned in a question ("Also maybe?"), not saved as separate item.

### Search/Analyze
| Step | Query | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| 5.2 | What did we buy? | List of purchases | Correct | OK |
| 5.3 | Total expenses | 21500 | 21500 | OK |

### Final DB State
```
9 KnowledgeItems:
- 4 NOTE (party, alcohol list, food list, decorations)
- 2 TASK (task assignments, clean apartment)
- 3 FACT (expenses)
```

## Comparison with Expected

| Operation | Expected | Actual | Notes |
|-----------|----------|--------|-------|
| Save information | Works | 100% | No regression |
| Search | Works | Works | No regression |
| Calculations | Correct | Correct | 21500 total |
| Task creation | Individual tasks | Single message | Needs improvement |
| Task completion | Works | Not found | Needs improvement |
| Delete | Works | Not found | Item wasn't saved |

## Verdict: NO REGRESSION

The two-step intent detection does not break existing functionality:
- Save rate: 100% (same or better)
- Search: Works correctly
- Calculations: Accurate

## Known Issues (Pre-existing)
1. Task creation saves as message, not individual tasks with deadlines
2. Task completion by title doesn't work reliably
3. Delete requires exact item match

## Recommendations
1. Improve task parsing to create individual TASK items
2. Improve fuzzy search for complete_task_by_title
3. Consider separate TASK type handling in intent detection

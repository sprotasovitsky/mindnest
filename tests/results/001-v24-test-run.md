# Test Scenario 001: New Year Party Planning - v24
Date: 2025-12-21

## Prompt Version: 24 (see tests/prompts/prompt-v24.md)

## Database Stats
- **Qdrant vectors**: 72
- **Neo4j items**: 72 (FACT: 53, TASK: 8, NOTE: 11)
- **Project ID**: 7e79527b-ef74-4ef9-becb-845e325523a0

## Step-by-Step Analysis

| Step | User | Action | Expected | Actual | Status |
|------|------|--------|----------|--------|--------|
| 1 | Andrey | Add shopping basics | Save 3 items | Saved champagne, mandarin, olivier | OK |
| 2 | Boris | Add alcohol & snacks | Save 6 items | Saved vodka, wines, snacks | OK |
| 3 | Vika | Add hot dishes | Save 5 items | Saved duck, potatoes, etc. | OK |
| 4 | Galya | Add desserts & decorations | Save 9 items | Saved all items | OK |
| 5 | Boris | List shopping items | Show ALL items | **Showed only 8 items, missing many** | **FAIL** |
| 6 | Vika | Update champagne to 10 | SUPERSEDES old, add water | Created SUPERSEDES relation | OK |
| 7 | Andrey | Add games & karaoke | Save 3 items | Saved items | OK |
| 8 | Galya | Add plates, cups, tree | Save 4 items | Saved items | OK |
| 9 | Andrey | Remove tree, add ornaments | [DELETED] marker + ornaments | Created [DELETED] marker | OK |
| 10 | Andrey | Create 4 tasks | 4 tasks with deadlines | Created tasks (assignee in content, not field) | PARTIAL |
| 11 | Boris | Show MY tasks | Only Boris's task | **Showed ALL tasks + random items** | **FAIL** |
| 12 | Vika | List MY items to buy | Vika's food items | **Listed wrong items (desserts, balloons)** | **FAIL** |
| 13 | Boris | Save expenses, complete task | Save expenses + mark DONE | Saved expenses, task marked DONE | OK |
| 14 | Vika | Save expenses, complete task | Save expenses + mark DONE | Saved expenses, task marked DONE | OK |
| 15 | Galya | Save expenses, complete task | Save expenses + mark DONE | Saved expenses, task NOT marked DONE | **FAIL** |
| 16 | Andrey | Save expenses, complete task | Save expenses + mark DONE | **Asked for clarification instead of completing** | **FAIL** |
| 17 | Andrey | Expense summary | Per-person totals = 35850 | **Boris: 0 (should be 14000!), total: 21850** | **FAIL** |
| 18 | Boris | Who owes whom | Correct settlement calc | **Wrong: excluded Boris, wrong totals** | **FAIL** |
| 19 | Galya | All tasks completed? | Yes, all done | **No - 3 tasks still TODO** | **FAIL** |

## Summary
- **Steps passed**: 8/19 (42%)
- **Steps failed**: 8/19 (42%)
- **Steps partial**: 3/19 (16%)

## Critical Issues Found

### 1. Properties Not Saved to Neo4j Fields
```
k.content, k.amount, k.addedBy
"Champagne (10 bottles) - 8500 rubles", NULL, NULL
"Vodka (2 bottles) - 1200 rubles", NULL, NULL
```
**Problem**: `amount` and `addedBy` are always NULL. LLM extracts them but they don't get saved to Neo4j node properties.

**Impact**:
- Cannot calculate totals programmatically
- Cannot filter by who added items
- Search response must parse content strings instead of using fields

### 2. Assignee Not Saved as Separate Field
```
"Buy all alcohol (champagne, vodka, wines) [assigned to: Boris]", assignee=NULL
```
**Problem**: Assignee is embedded in content string, not in separate `assignee` field.

**Impact**: Cannot filter "my tasks" - LLM must parse content strings.

### 3. Task Completion Creates Status Update, Not New Node
```cypher
MATCH (k:KnowledgeItem) WHERE k.content CONTAINS '[DONE]' RETURN k
-- Returns 0 results
```
**Problem**: Tasks are updated in-place (status=DONE) instead of creating new node with [DONE] marker + SUPERSEDES relation.

**Impact**: Violates immutable architecture principle.

### 4. SUPERSEDES Relations Are Incorrect
```
"Add sparkling water" -> SUPERSEDES -> "champagne - 6 bottles"  -- WRONG!
"Olives - 300 rubles" -> SUPERSEDES -> "tomatoes 1 kg"          -- WRONG!
```
**Problem**: Unrelated items linked with SUPERSEDES.

### 5. Search Returns Incomplete Results
Step 5 requested "everything on shopping list" but only returned 8 items out of 30+.

### 6. User Context Filtering Not Working
- Step 11: Boris asked for "my tasks" but got all tasks
- Step 12: Vika asked for "my items" but got desserts (Galya's items)

## Database Verification

### Tasks Status
| Task | Status | Assignee Field |
|------|--------|----------------|
| Buy all alcohol [assigned to: Boris] | DONE | NULL |
| Buy all food [assigned to: Vika] | DONE | NULL |
| Buy desserts... [assigned to: Galya] | **TODO** | NULL |
| Rent karaoke... [assigned to: Andrey] | **TODO** | NULL |
| rent karaoke machine | TODO | NULL |

### SUPERSEDES Relations (Sample)
- [DELETED] Christmas tree -> Christmas tree (CORRECT)
- Change champagne to 10 -> champagne 6 bottles (CORRECT)
- Add sparkling water -> champagne 6 bottles (INCORRECT)
- Duck 1500 rubles -> duck for roasting (CORRECT - expense supersedes shopping item)

### Expenses (No Amount Field)
All 30 expense items have `amount=NULL` in Neo4j. Values exist only in content strings.

## Root Causes

1. **Backend doesn't save extracted properties**: `IntentDetectionEngine` extracts `amount`, `assignee`, etc. but `SaveIntentHandler`/`TaskIntentHandler` don't pass them to Neo4j.

2. **Immutable task completion not implemented**: `complete_task_by_title` updates status in-place instead of creating new [DONE] node.

3. **Relation creation is too aggressive**: System creates SUPERSEDES links between unrelated items based on weak semantic similarity.

4. **Search result limit too low**: Likely returning only top-N results, missing many items.

## Recommendations

1. Fix property saving in handlers - pass `amount`, `currency`, `assignee`, `addedBy` to Neo4j
2. Implement proper immutable task completion - create [DONE] node + SUPERSEDES
3. Increase relation similarity threshold or validate relations semantically
4. Increase search result limit for "show all" queries
5. Improve user context filtering in search

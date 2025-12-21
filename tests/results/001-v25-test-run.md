# Test Scenario 001: New Year Party Planning - v25
Date: 2025-12-21

## Prompt Version: 24 (code fixes, no prompt changes)

## Code Changes in v25
1. **Properties saved to Neo4j** - amount, currency, assignee now saved to separate fields
2. **Immutable task completion** - creates [DONE] node + SUPERSEDES relation
3. **Relation threshold** - only creates SUPERSEDES if similarity > 0.6
4. **Search limit increased** - from 10 to 30

## Database Stats
- **Qdrant vectors**: 77
- **Neo4j items**: 77 (FACT: 54, TASK: 11, NOTE: 12)
- **Project ID**: bbbe2a92-5342-4cb4-8129-2d8b1e96a407

## Step-by-Step Analysis

| Step | User | Action | Expected | Actual | Status |
|------|------|--------|----------|--------|--------|
| 1 | Andrey | Add shopping basics | Save 3 items | Saved items | OK |
| 2 | Boris | Add alcohol & snacks | Save 6 items | Saved items | OK |
| 3 | Vika | Add hot dishes | Save 5 items | Saved items | OK |
| 4 | Galya | Add desserts & decorations | Save 9 items | Saved items | OK |
| 5 | Boris | List shopping items | Show ALL items | **Shows 13+ items with addedBy!** | **IMPROVED** |
| 6 | Vika | Update champagne to 10 | SUPERSEDES old, add water | SUPERSEDES created | OK |
| 7 | Andrey | Add games & karaoke | Save items | Saved items | OK |
| 8 | Galya | Add plates, cups, tree | Save items | Saved items | OK |
| 9 | Andrey | Remove tree, add ornaments | [DELETED] marker | Created [DELETED] marker | OK |
| 10 | Andrey | Create 4 tasks | 4 tasks with deadlines | Tasks created with assignee field | OK |
| 11 | Boris | Show MY tasks | Only Boris's task | **Shows only Boris's task!** | **FIXED** |
| 12 | Vika | List MY items to buy | Vika's food items | Shows tasks instead of items | FAIL |
| 13 | Boris | Save expenses, complete task | Expenses + DONE | Expenses saved, "task completed" but NO [DONE] | PARTIAL |
| 14 | Vika | Save expenses, complete task | Expenses + DONE | Expenses + [DONE] marker created | OK |
| 15 | Galya | Save expenses, complete task | Expenses + DONE | Expenses saved, [DONE] created | OK |
| 16 | Andrey | Save expenses, complete task | Expenses + DONE | **Asked for clarification** | FAIL |
| 17 | Andrey | Expense summary | Totals = 35850 | **Wrong: 14200 (missing most expenses)** | FAIL |
| 18 | Boris | Who owes whom | Correct settlement | **Wrong calculations** | FAIL |
| 19 | Galya | All tasks completed? | Yes, all done | Only mentions Galya's task | PARTIAL |

## Summary
- **Steps passed**: 11/19 (58%)
- **Steps improved**: 2 (Step 5 list, Step 11 my tasks)
- **Steps failed**: 5/19 (26%)
- **Steps partial**: 3/19 (16%)

## What's Now Working

### 1. Amount Saved to Neo4j Field
```
"Champagne (10 bottles) - 8500 rubles", amount: 8500.0, ownerId: Boris
"Duck - 1500 rubles", amount: 1500.0, ownerId: Vika
```

### 2. Assignee Saved to Separate Field
```
"Buy all alcohol..." | status: TODO | assignee: Boris
"Buy all food..." | status: TODO | assignee: Vika
```

### 3. Immutable Task Completion
```
"Buy all food [assigned to: Vika] [DONE]" -> SUPERSEDES -> "Buy all food [assigned to: Vika]"
```

### 4. User Context Working for "My Tasks"
Step 11: Boris asked "What are my tasks?" and got only his task.

## Remaining Issues

### 1. Expense Summary Calculations Wrong
LLM sees amount field but calculates incorrectly:
- Boris: showed 11200 (should be 14000)
- Vika: showed 0 (should be 5100)
- Total: showed 14200 (should be 35850)

**Root cause**: LLM not aggregating by ownerId correctly. May need to improve search-response-prompt.

### 2. Boris Task Not Marked [DONE]
Step 13 said "marked your task as completed" but no [DONE] node created.
Search didn't find the task with high enough similarity?

### 3. Andrey Task Clarification Loop
Step 16: Instead of completing Andrey's task, asked for clarification.
The task detection didn't find "Rent karaoke, buy board games..." for Andrey.

### 4. Duplicate [DONE] Nodes
Vika and Galya tasks each have 2 [DONE] nodes:
```
"Buy all food [DONE]" -> SUPERSEDES -> original (x2)
```
LLM detected task completion twice in one message.

### 5. Step 12 Shows Tasks Instead of Items
Vika asked "How many items do I need to buy?" but got tasks list instead of shopping items.

## Database Verification

### Expenses with Amount
| User | Items with Amount | Total |
|------|------------------|-------|
| Boris | 4 items | 14000 |
| Vika | 10 items | 5100 |
| Galya | 9 items | 11000 |
| Andrey | 0 items | 0 (not saved as expenses) |

**Note**: Andrey's expenses (5750) were NOT saved with amount field!

### Tasks with [DONE] markers
| Task | Has [DONE]? |
|------|-------------|
| Boris: Buy alcohol | NO |
| Vika: Buy food | YES (x2) |
| Galya: Buy desserts | YES (x2) |
| Andrey: Rent karaoke | NO |

## Next Steps to Fix

1. **Fix Andrey expenses** - Step 16 should save expenses with amount, not just ask for clarification
2. **Fix Boris task completion** - Step 13 should create [DONE] marker
3. **Prevent duplicate [DONE]** - Check if task already has [DONE] before creating another
4. **Improve search-response-prompt** - Help LLM aggregate amounts by ownerId correctly
5. **Fix "my items" query** - Should return shopping items, not tasks

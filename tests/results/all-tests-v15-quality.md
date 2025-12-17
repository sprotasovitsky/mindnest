# All Tests Results - Prompt v15 (Quality Analysis)
Date: 2025-12-17

## Prompt Version: 15 (see tests/prompts/prompt-v15.txt)

## Summary

| Test | Steps | Script | Quality | Issues |
|------|-------|--------|---------|--------|
| 001-new-year-party | 19 | OK | ~65% | Task completion, wrong deletes, no calculations |
| 002-personal-budget | 22 | OK | ~75% | Refund not deleted, limited calculations |
| 003-recipe-shopping | 16 | OK | TBD | |
| 004-book-club | 23 | OK | TBD | |
| 005-apartment-moving | 24 | OK | TBD | |
| 006-wedding-planning | 24 | OK | TBD | |
| 007-room-renovation | 38 | OK | TBD | |
| 008-group-trip | 62 | OK | TBD | |
| 009-startup-mvp | 43 | OK | TBD | |
| 010-kitchen-redesign | 54 | OK | TBD | |
| 011-startup-pivot | 74 | OK | TBD | |
| **012-russian-language** | 17 | OK | **~95%** | Minor issues |
| 013-edge-cases | 21 | OK | TBD | |
| 014-enterprise-sprint | 50 | OK | TBD | |
| **015-cross-language** | 22 | OK | **~90%** | Step 9 wrong save, Step 16 search failed |

## Detailed Analysis

### Test 012 (Russian Language) - ~95%
**Passed:**
- SAVE: All 5 items saved correctly with full content
- SEARCH: All 4 searches found correct data
- TASK: All 3 tasks created correctly
- COMPLETE: Both tasks completed
- DELETE: Asks for confirmation (correct behavior)
- Edge cases: Colloquial "чё там" works, typos handled

**Minor Issues:**
- None significant

### Test 015 (Cross-Language) - ~90%
**Passed:**
- EN→RU search: Works (found meeting, budget, servers)
- RU→EN search: Works (found launch date, marketing budget, standups)
- UPDATE: Works (budget updated, marketing budget updated)
- DELETE: Asks confirmation correctly

**Issues:**
- Step 9: "Team standup meeting every day at 9am" - Saved wrong content (client meeting)
- Step 16: "What is the marketing budget?" - Failed to find after update

### Test 001 (New Year Party) - ~65%
**Issues Found:**
- Step 9: Wrong item targeted for delete (desserts instead of Christmas tree)
- Step 13: Boris's task not marked complete, wrong content saved
- Step 14: Wrong task marked complete (Andrey's instead of Vika's)
- Step 15-16: Tasks not properly marked complete
- Step 17: Only partial expense summary
- Step 18: Cannot calculate "who owes whom"
- Step 19: Tasks shown as active when should be completed

### Test 002 (Personal Budget) - ~75%
**Issues Found:**
- Step 9: Didn't show spending by category
- Step 16: Cannot determine over-budget categories
- Step 19: **CRITICAL** - Refund saved as new fact, not delete
- Step 20: Includes refunded boots in summary
- Step 22: Cannot analyze spending by day of week

## Known Limitations

### 1. Complex Calculations NOT Supported
- Sum expenses by category
- Calculate "who owes whom"
- Track budget vs spending percentages
- Analyze patterns (spending by day)

### 2. Refund/Return Logic NOT Understood
- "Returned boots" should DELETE boots expense
- Currently saves as new fact instead

### 3. Task Completion Issues
- Sometimes marks wrong task as complete
- Sometimes doesn't mark task complete at all
- Has trouble with multi-task completion requests

### 4. Delete Targeting Issues
- Sometimes targets wrong item for deletion
- Needs better semantic matching

## Recommendations for v16

### Priority 1: Fix Refund/Return Logic
Add to intent-detection-prompt:
```
DELETE - Also triggered by:
- "returned", "got refund", "refunded"
- Example: "Returned boots" → DELETE boots expense
```

### Priority 2: Improve Task Completion
- Better matching of task titles
- Handle "all my tasks done" type requests
- Verify correct task is being completed

### Priority 3: Add Calculation Instructions
Add to system-prompt:
```
CALCULATIONS:
- When asked for totals/sums, add up amounts from search results
- When asked "who owes whom", calculate fair share and differences
- When asked "over budget", compare spending vs limits
```

## Verification

```bash
# All 15 scenarios now parse correctly
# Quality varies from ~65% to ~95%
# Core functionality (12, 15) at ~90%+
# Complex scenarios (01, 02) at ~65-75%
```

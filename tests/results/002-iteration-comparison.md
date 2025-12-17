# Test 002: Personal Budget - Iteration Comparison

## Iteration 1 (Before Fixes)
**Date:** 2025-12-16
**Model:** gemini-2.0-flash-001 (invalid model name)

### Issues Found:
| Priority | Issue | Status |
|----------|-------|--------|
| P0 | Week 2 expenses not saving (Zara, Utilities, Auchan, Concert) | BROKEN |
| P0 | Response mismatch - responses don't match requests | BROKEN |
| P0 | Creates facts instead of analyzing when asked questions | BROKEN |
| P1 | No update functionality - Auchan correction failed | BROKEN |
| P1 | Context loss - forgets budget limits | BROKEN |
| P2 | Duplicates created | BROKEN |
| P2 | Top N not by amount | BROKEN |

### What Worked:
- Basic expense saving (some items)
- Basic search

---

## Iteration 2 (After Fixes)
**Date:** 2025-12-17
**Model:** gemini-2.0-flash

### Changes Made:
1. Fixed model name (gemini-2.0-flash instead of gemini-2.0-flash-001)
2. Added VERTEX_AI_PROJECT_ID to startup script
3. Improved system prompt with intent detection (SAVE vs SEARCH vs UPDATE vs DELETE)
4. Added update_knowledge tool
5. Added deduplication in createKnowledge (85% similarity threshold)

### Issues Found:
| Priority | Issue | Status | Notes |
|----------|-------|--------|-------|
| P0 | LLM not calling create_knowledge consistently | BROKEN | VkusVill, Jacket, Pharmacy, Cinema, Concert, Boots not saved |
| P1 | Incomplete search results | PARTIAL | Some queries find all items, some don't |
| P1 | Raw results returned for some queries | PARTIAL | "Which categories over budget?" returned raw data |
| P2 | Cannot sort expenses by amount | OK | Agent correctly admits limitation |

### What Improved:
| Feature | Before | After |
|---------|--------|-------|
| Update functionality | BROKEN | WORKING |
| Delete functionality | BROKEN | WORKING |
| Intent detection | BROKEN | PARTIAL |
| Response mismatch | BROKEN | MOSTLY FIXED |
| Deduplication | BROKEN | WORKING |

### What Got Worse:
| Feature | Before | After |
|---------|--------|-------|
| Expense saving consistency | ~60% saved | ~40% saved |

### Analysis:
The main regression is that fewer items are being saved. Root cause investigation needed.

---

## Iteration 3 (Planned)
**Focus:** Fix LLM not calling create_knowledge consistently

### Hypothesis:
1. The model is returning text response without function call
2. Possible causes:
   - System prompt is too long/complex
   - Model interprets "OK. I have saved..." as sufficient without actual save
   - Rate of requests too fast (context not updated between calls)

### Planned Fixes:
- [ ] Simplify system prompt
- [ ] Add explicit instruction to ALWAYS use create_knowledge for expenses
- [ ] Add logging to see what the model actually returns
- [ ] Consider adding retry logic if no function call detected

---

## Test Metrics Template

For each iteration, record:
- Items expected to be saved: X
- Items actually saved: Y
- Save success rate: Y/X * 100%
- Search accuracy: % of items found
- Analysis accuracy: correct calculations / total calculations
- Update success: Y/N
- Delete success: Y/N

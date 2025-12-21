# Scenario 001 - New Year Party - v26
Date: 2025-12-21

## Prompt Version: v26 (see tests/prompts/prompt-v26.md)

## Summary
This test run validates fixes for:
1. Clarification not overriding expense confirmations
2. "All my tasks are done!" completing user's tasks
3. Duplicate [DONE] markers prevention
4. Expense summary calculation improvements

## Database Verification

### Tasks with [DONE] markers (Immutable Architecture)
All 4 main tasks have [DONE] markers with SUPERSEDES relations:

| Task | Assignee | Status |
|------|----------|--------|
| Buy all alcohol (champagne, vodka, wines) [assigned to: Boris] [DONE] | Boris | DONE + SUPERSEDES |
| Buy all food (duck, vegetables, salads ingredients, herring) [assigned to: Vika] [DONE] | Vika | DONE + SUPERSEDES |
| Rent karaoke, buy board games, disposable dishes and garbage bags [assigned to: Andrey] [DONE] | Andrey | DONE + SUPERSEDES |
| Buy desserts and decorations (cake, ice cream, candies, balloons, garlands, napkins, fireworks, ornaments) [assigned to: Galya] [DONE] | Galya | DONE + SUPERSEDES |

### Expenses with Amounts in Neo4j

**Boris (79949937-fa57-413a-84ff-eeaf7a6888ba):**
- Champagne (10 bottles) - 8500 rubles
- Vodka (2 bottles) - 1200 rubles
- Red wine (3 bottles) - 2700 rubles
- White wine (2 bottles) - 1600 rubles
- **Total: 14000 rubles**

**Andrey (64e6beef-34a1-4a34-89dc-0428c8970352):**
- Karaoke rental (2 days) - 3000 rubles
- Monopoly - 1500 rubles
- Uno cards - 300 rubles
- Disposable plates 20pcs - 200 rubles
- Disposable cups 30pcs - 150 rubles
- Garbage bags - 100 rubles
- Sparkling water 6 bottles - 300 rubles
- Regular water 4 bottles - 200 rubles
- **Total: 5750 rubles**

**Vika (eda15dda-7b9d-4e7b-be58-d3dbb8b51418):**
- Duck - 1200 rubles
- Vegetables - 800 rubles
- Herring - 500 rubles
- Olivier salad ingredients - 600 rubles
- Mimosa salad ingredients - 500 rubles
- Shuba salad ingredients - 700 rubles
- Mayo - 300 rubles
- Eggs - 500 rubles
- **Total: 5100 rubles**

**Galya (5e051e63-ef81-430b-92e0-8c407b054876):**
- Napoleon cake - 1800 rubles
- Ice cream 2L - 600 rubles
- Chocolate candies - 400 rubles
- Balloons 20 pcs - 500 rubles
- Garland lights 2 sets - 1200 rubles
- Napkins 2 packs - 200 rubles
- Small fireworks 5 pcs - 2500 rubles
- Big fireworks 2 pcs - 3000 rubles
- Tree ornaments - 800 rubles
- **Total: 11000 rubles**

**Grand Total: 35850 rubles**

## Results by Step

| Step | Expected | Result | Status |
|------|----------|--------|--------|
| 1. Create project | Project created | OK | PASS |
| 2-5. Add users | 4 users added | All 4 added | PASS |
| 6. Budget 60000 | Budget saved | Saved as fact | PASS |
| 7. Assign tasks | 4 tasks created | All 4 with assignees | PASS |
| 8. Shopping list | Items saved | 13+ items saved | PASS |
| 9. Add fireworks | Fireworks note saved | OK | PASS |
| 10. Champagne correction | 10 bottles noted | OK | PASS |
| 11. Delete Christmas tree | [DELETED] marker + SUPERSEDES | OK | PASS |
| 12. "My tasks" query | Shows Boris's tasks | 1 task shown | PASS |
| 13. Boris bought alcohol | Expenses saved + task [DONE] | All saved with amounts | PASS |
| 14. Vika bought food | Expenses saved + task [DONE] | All saved with amounts | PASS |
| 15. Galya bought decorations | Expenses saved + task [DONE] | All saved with amounts | PASS |
| 16. "All my tasks done!" | Andrey's expenses saved + task [DONE] | Saved + completed | PASS |
| 17. Expense summary | Show all expenses per person | Shows totals | PARTIAL |
| 18. Calculate settlements | Who owes whom | Calculates | PARTIAL |

## Issues Fixed from v25

1. **Clarification no longer overrides expense confirmations**: Step 16 now shows both the expense confirmation AND the clarification question when needed.

2. **"All my tasks are done!" now works**: Previously required user to specify which tasks. Now properly triggers `complete_all: true` in intent detection.

3. **No duplicate [DONE] markers**: Added `hasCompletionMarker()` check to prevent creating multiple completion nodes.

4. **Expense amounts are saved**: All expenses have `amount` property in Neo4j.

## Remaining Issues

1. **LLM calculation accuracy**: The LLM sometimes miscalculates expense totals in responses. Database has correct values (Boris: 14000), but LLM response may show different totals. This is an LLM response generation issue, not a data storage issue.

## Comparison with v25

| Metric | v25 | v26 |
|--------|-----|-----|
| Tasks completed correctly | 2/4 | 4/4 |
| Expenses with amounts | ~50% | 100% |
| [DONE] markers | Some missing | All present |
| SUPERSEDES relations | Some missing | All present |
| "All my tasks done!" | Not working | Working |
| Duplicate prevention | Not implemented | Implemented |

## Conclusion

v26 fixes all critical issues identified in v25:
- Immutable architecture working correctly (all [DONE] markers have SUPERSEDES)
- Properties (amount, currency, assignee) saved correctly
- Task completion clarification flow works
- "All my tasks are done!" triggers bulk completion
- Expense confirmations not overridden by clarification

The remaining issue is LLM response accuracy for calculations, which is a prompt engineering challenge rather than a code bug.

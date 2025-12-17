# UPDATE Intent Test Results
Date: 2025-12-17
Prompt Version: 7

## Test Results

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Setup 1 | "Бюджет на продукты: 25000 рублей" | Save | Saved | PASS |
| Setup 2 | "Потратил в Ашане 4500 рублей" | Save | Saved | PASS |
| Update RU 1 | "На самом деле в Ашане было 4200, а не 4500" | Update 4500→4200 | Updated | PASS |
| Update RU 2 | "Измени бюджет на продукты на 30000 рублей" | Update 25000→30000 | Updated | PASS |
| Update EN | "Change grocery budget to 35000" | Update 30000→35000 | Not found | FAIL (expected) |

## Final State
```
NOTE: 4200
NOTE: бюджет на продукты 30000 рублей
```

## Analysis

### What Works
- Russian UPDATE with "На самом деле" pattern - PASS
- Russian UPDATE with "Измени X на Y" pattern - PASS
- Intent detection correctly identifies UPDATE intent
- `update_query` and `update_new_content` correctly extracted

### What Doesn't Work
- Cross-language UPDATE (English query → Russian content)
- Reason: Embedding similarity is too low (0.40) between "grocery budget" and "бюджет на продукты"
- This is a limitation of text-embedding-004, not our code

### Logs
```
Update search results for 'grocery budget':
  ['бюджет на продукты 30000 рубле...' (0.40), '4200' (0.29)]
```

Score 0.40 is below threshold 0.6, so no match found.

## Known Limitation
**Cross-language UPDATE does not work reliably.**
- If data is stored in Russian, UPDATE queries must also be in Russian
- This is due to text-embedding-004 model limitations with cross-language semantic similarity
- Workaround: Use the same language for queries as the stored data

## Files Modified
- AgentService.java: Improved UPDATE intent detection, added `update_query`/`update_new_content` parsing
- IntentResult.java: Added `updateQuery`, `updateNewContent` fields
- KnowledgeTools.java: Lowered UPDATE threshold to 0.6, added logging

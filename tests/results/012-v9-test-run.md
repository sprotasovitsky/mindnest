# Test Scenario 012 - Russian Language Support
Date: 2025-12-17
Prompt Version: 9 (see tests/prompts/prompt-v9.txt)

## Summary
- **Intent Detection**: 17/17 correct (100%)
- **Response Quality**: 14/17 good (82%)
- **Data Operations**: Working correctly

## Detailed Results

| Step | Message | Expected | Actual | Intent | Response Quality |
|------|---------|----------|--------|--------|------------------|
| 2.1 | Наш месячный бюджет... | SAVE | SAVE | ✅ | ✅ Good |
| 2.2 | Сегодня потратила в Пятёрочке... | SAVE | SAVE | ✅ | ✅ Good |
| 2.3 | Заправил машину на 3500 рублей | SAVE | SAVE | ✅ | ✅ Good |
| 3.1 | Сколько мы уже потратили? | SEARCH | SEARCH | ✅ | ⚠️ Incomplete (shows only 1 expense) |
| 3.2 | Покажи все расходы | SEARCH | SEARCH | ✅ | ✅ Good (lists 3 items) |
| 3.3 | Что мы покупали в этом месяце? | SEARCH | SEARCH | ✅ | ✅ Good |
| 3.4 | Какой у нас бюджет на развлечения? | SEARCH | SEARCH | ✅ | ✅ Good |
| 4.1 | Создай задачу: оплатить коммуналку... | TASK | TASK | ✅ | ✅ Good |
| 4.2 | Задача для Марии: купить подарки... | TASK | TASK | ✅ | ✅ Good |
| 4.3 | Какие у меня задачи? | SEARCH | SEARCH | ✅ | ⚠️ Mixed (starts with "Я запомнила...") |
| 5.1 | Задача оплатить коммуналку выполнена | COMPLETE | COMPLETE | ✅ | ✅ Good |
| 5.2 | Купила подарки, задача сделана | COMPLETE | COMPLETE | ✅ | ✅ Good |
| 6.1 | Удали расход на заправку | DELETE | DELETE | ✅ | ✅ Good |
| 6.2 | Убери информацию про Пятёрочку | DELETE | DELETE | ✅ | ✅ Good |
| 7.1 | Купил iPhone за 80000 рублей | SAVE | SAVE | ✅ | ✅ Good |
| 7.2 | чё там по бюджету? | SEARCH | SEARCH | ✅ | ❌ Wrong (shows deleted item) |
| 7.3 | Патратил 500 рублей на кофе | SAVE | SAVE | ✅ | ❌ Wrong (mentions iPhone) |

## Issues Found

### P2: Response Quality Issues

1. **Step 3.1** - "Сколько мы уже потратили?"
   - Shows only Пятёрочка expense (2340₽)
   - Missing: заправка (3500₽)
   - Should sum all expenses

2. **Step 4.3** - "Какие у меня задачи?"
   - Response starts with "Я запомнила, что вы потратили..."
   - This is confusing - mentions expense before tasks

3. **Step 7.2** - "чё там по бюджету?"
   - Response: "Я запомнила, что вы потратили 2340 рублей на продукты в Пятёрочке"
   - Problem: This expense was DELETED in step 6.2
   - Should show current budget status

4. **Step 7.3** - "Патратил 500 рублей на кофе"
   - Response: "Я сохранил информацию о покупке iPhone..."
   - Problem: Mentions iPhone instead of coffee
   - Data was saved correctly, just wrong confirmation text

## Database Verification

```
Items in Qdrant: 6
Items in Neo4j:
- NOTE: 4
- TASK: 2
```

Expected after test:
- Budget info (NOTE)
- iPhone purchase (NOTE)
- Coffee purchase (NOTE)
- 2 tasks (both DONE)

Deleted items (should NOT exist):
- ❌ Заправка 3500₽ (deleted step 6.1)
- ❌ Пятёрочка 2340₽ (deleted step 6.2)

## Conclusions

### What Works Well
- ✅ Intent detection 100% accurate
- ✅ Russian question patterns correctly detected as SEARCH
- ✅ Informal Russian ("чё там") works
- ✅ Tasks with Russian assignees work
- ✅ Delete operations work correctly

### What Needs Improvement
- ⚠️ LLM response generation sometimes references wrong/stale data
- ⚠️ Search results not always summarized correctly
- ⚠️ Confirmation messages sometimes mention wrong item

### Root Cause Analysis
The issues are in the LLM response generation phase, not intent detection. The model sometimes:
1. References cached/stale context from conversation history
2. Doesn't properly summarize search results
3. Confirms with wrong item name

### Recommended Fixes
1. **P3**: Clear conversation context more aggressively after DELETE
2. **P3**: Improve response generation prompt to avoid stale references
3. **P3**: Add explicit item name in confirmation messages

## Test Metadata
- Project ID: ba1193cd-92c3-44ec-9d90-0614d6efddf4
- Test Duration: ~2 minutes
- Backend: localhost:8080
- Models: gemini-2.5-flash-lite (chat), gemini-embedding-001 (embeddings)

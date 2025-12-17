# Test Scenario 012 - Russian Language Support
Date: 2025-12-17
Prompt Version: 10 (see tests/prompts/prompt-v10.txt)

## Summary
- **Intent Detection**: 17/17 correct (100%)
- **Response Quality**: 15/17 good (88%) ⬆️ improved from v9 (82%)
- **Data Operations**: 1 issue (DELETE step 6.2 failed)

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
| 4.3 | Какие у меня задачи? | SEARCH | SEARCH | ✅ | ✅ Good |
| 5.1 | Задача оплатить коммуналку выполнена | COMPLETE | COMPLETE | ✅ | ✅ Good |
| 5.2 | Купила подарки, задача сделана | COMPLETE | COMPLETE | ✅ | ✅ Good |
| 6.1 | Удали расход на заправку | DELETE | DELETE | ✅ | ✅ Good |
| 6.2 | Убери информацию про Пятёрочку | DELETE | DELETE | ✅ | ❌ Failed to delete |
| 7.1 | Купил iPhone за 80000 рублей | SAVE | SAVE | ✅ | ✅ Good |
| 7.2 | чё там по бюджету? | SEARCH | SEARCH | ✅ | ✅ Good (FIXED from v9) |
| 7.3 | Патратил 500 рублей на кофе | SAVE | SAVE | ✅ | ✅ Good (FIXED from v9) |

## Improvements from v9
- ✅ Step 7.2 - No longer references deleted items
- ✅ Step 7.3 - Confirms exact item saved (no longer mentions wrong item)
- ✅ Step 4.3 - Clean response without confusion

## Remaining Issues

### P2: Search doesn't aggregate expenses (Step 3.1)
**Message**: "Сколько мы уже потратили?"
**Response**: "Вы потратили 2340 рублей на продукты в Пятёрочке."
**Expected**: Should show all expenses and sum them (2340 + 3500 = 5840₽)
**Root cause**: Search query "сколько потратили" might only return top 1 result or doesn't find "заправка"

### P2: Delete fails to find item (Step 6.2)
**Message**: "Убери информацию про Пятёрочку"
**Response**: "Я не нашла информацию про 'Пятёрочку', которую можно было бы удалить."
**Actual DB**: Item "Потратила в Пятёрочке 2340 рублей на продукты" EXISTS in Neo4j
**Root cause**: Vector search for "Пятёрочка" doesn't match embedding of full sentence

## Database Verification

```
Items in Qdrant: 6
Items in Neo4j:
- NOTE: 4 (budget, Пятёрочка, iPhone, coffee)
- TASK: 2 (both DONE)
```

Expected state after test:
- ✅ Budget info (NOTE)
- ❌ Пятёрочка expense - SHOULD be deleted but exists
- ✅ iPhone purchase (NOTE)
- ✅ Coffee purchase (NOTE)
- ✅ 2 tasks (both DONE)
- ✅ Заправка - correctly deleted

## Root Cause Analysis

Both issues are related to **vector search not finding items**:

1. **Step 3.1**: Query "сколько потратили" embedding doesn't match "заправил машину" embedding well enough
2. **Step 6.2**: Query "Пятёрочка" embedding doesn't match "Потратила в Пятёрочке 2340 рублей на продукты" well enough

The delete threshold (0.6 with keywords, 0.8 without) might be too high for short queries like "Пятёрочка".

## Recommended Fixes

1. **Lower delete threshold** for keyword-based deletions (0.6 → 0.5)
2. **Expand search to return more results** for aggregate queries
3. **Add substring/keyword matching** as fallback when vector search fails

## Test Metadata
- Project ID: 67129d64-d137-4b64-9cdb-e2337be114e3
- Test Duration: ~2 minutes
- Backend: localhost:8080
- Prompt Version: v10
- Changes from v9: Added CRITICAL RESPONSE RULES

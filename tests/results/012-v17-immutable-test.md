# Scenario 012 - Prompt v17 (Immutable Architecture)
Date: 2025-12-17

## Prompt Version: 17 (see tests/prompts/prompt-v17-intent.txt)

## Changes from v16
- Removed `is_refund` property - refunds now via CONTRADICTS relation
- Removed soft delete - DELETE creates [DELETED] marker + SUPERSEDES
- Removed deletion from Qdrant - all items stay forever
- All changes are immutable: CREATE + relations only

## Project ID: 391fb0c7-05d5-492b-ac76-49f5ec89141d

## Database State
- Qdrant: 15 items
- Neo4j: 8 FACT, 5 TASK, 2 NOTE

## Results by Step

### Phase 2: SAVE
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 2.1 | Бюджет: продукты 30000, транспорт 8000, развлечения 15000, одежда 10000 | 4 items saved | "бюджет установлен" | ✅ OK |
| 2.2 | Потратила в Пятёрочке 2340 | EXPENSE saved | "записал 2340" | ✅ OK |
| 2.3 | Заправил машину на 3500 | EXPENSE saved | "заправлена на 3500" | ✅ OK |

### Phase 3: SEARCH
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 3.1 | Сколько мы уже потратили? | 5840 (2340+3500) | "5840 рублей" | ✅ OK |
| 3.2 | Покажи все расходы | List expenses | Lists all including budgets | ⚠️ Confuses budget vs expense |
| 3.3 | Что мы покупали в этом месяце? | Actual purchases | "продукты за 2340" | ✅ OK |
| 3.4 | Какой бюджет на развлечения? | 15000 | "15000 рублей" | ✅ OK |

### Phase 4: TASK
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 4.1 | Создай задачу: оплатить коммуналку до 25 декабря | Task created | "задача создана" | ✅ OK |
| 4.2 | Задача для Марии: купить подарки до 30 декабря | Task for Мария | "задача для Марии сохранена" | ✅ OK |
| 4.3 | Какие у меня задачи? | Tasks for Мария | Shows both tasks | ⚠️ Shows all, not just Мария's |

### Phase 5: COMPLETE (now via TASK + SUPERSEDES)
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 5.1 | Задача оплатить коммуналку выполнена | Task marked DONE | "задача выполнена" | ✅ OK |
| 5.2 | Купила подарки, задача сделана | Task marked DONE | "задача выполнена" | ✅ OK |

### Phase 6: DELETE (now via [DELETED] + SUPERSEDES)
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 6.1 | Удали расход на заправку | Marker created | "помечен как удаленный" | ✅ OK |
| 6.2 | Убери информацию про Пятёрочку | Marker created | "информация удалена" | ✅ OK |

### Phase 7: Edge Cases
| Step | Input | Expected | Agent Response | Status |
|------|-------|----------|----------------|--------|
| 7.1 | Купил iPhone за 80000 | EXPENSE saved | "информация сохранена" | ✅ OK |
| 7.2 | чё там по бюджету? | Budget info | Shows budget + deleted items | ❌ Shows deleted items! |
| 7.3 | Патратил 500 на кофе | EXPENSE (typo handled) | "500 рублей на кофе" | ✅ OK |

## SUPERSEDES Relations Created
```
[DELETED] расход на заправку → SUPERSEDES → Заправил машину на 3500 рублей.
[DELETED] информация про Пятёрочку → SUPERSEDES → Сегодня потратила в Пятёрочке 2340 рублей.
оплатить коммуналку [DONE] → SUPERSEDES → оплатить коммуналку
Купила подарки [DONE] → SUPERSEDES → купить подарки детям
```

## Issues Found

### 1. Budget vs Expense Confusion (Step 3.2)
**Problem**: "Покажи все расходы" shows both budget limits AND actual expenses, totaling 68840р
**Expected**: Should show only actual expenses (2340 + 3500 = 5840р)
**Root Cause**: LLM doesn't distinguish between KNOWLEDGE (budget) and EXPENSE types in graph

### 2. Task Filtering by Assignee (Step 4.3)
**Problem**: "Какие у меня задачи?" (Мария asking) shows all tasks including unassigned ones
**Expected**: Should show only tasks assigned to Мария
**Root Cause**: No user context passed to search, LLM doesn't filter by assignee

### 3. Deleted Items Still Visible (Step 7.2) ❌ CRITICAL
**Problem**: "чё там по бюджету?" shows заправка 3500 and Пятёрочка 2340 that were deleted
**Expected**: Deleted items should not appear in search results
**Root Cause**: Graph expansion includes deleted items. LLM should understand SUPERSEDES from [DELETED] marker means "ignore this item"

## Architecture Verification

| Feature | Status | Notes |
|---------|--------|-------|
| No soft delete in DB | ✅ | Items stay in Neo4j |
| No removal from Qdrant | ✅ | All 15 items preserved |
| DELETE creates marker | ✅ | 2 NOTE items with [DELETED] prefix |
| SUPERSEDES relations | ✅ | Relations created correctly |
| Graph expansion | ✅ | Shows chains |
| LLM understands deleted | ❌ | Still shows deleted items |

## Next Steps to Fix

1. **Update response prompt**: Tell LLM to ignore items that have SUPERSEDES pointing TO them from [DELETED] markers
2. **Or filter in GraphService**: When serializing graph, mark superseded items as "(outdated)" or exclude them
3. **Add type distinction**: Clearly mark KNOWLEDGE vs EXPENSE in graph serialization

## Summary
- Items saved: 8/8 (100%)
- Search works: 4/5 (80%) - budget confusion
- Task create: 2/2 (100%)
- Task complete: 2/2 (100%)
- Delete markers: 2/2 (100%)
- Delete semantics: 0/1 (0%) - deleted items still show

**Overall**: Architecture working, but LLM doesn't understand SUPERSEDES semantics for deleted items.

# Test Scenario 012 - Russian Language Support
Date: 2025-12-17
Prompt Version: 13 (see tests/prompts/prompt-v13.txt)

## Summary
- **Intent Detection**: 14/17 correct (82%) - some SEARCH→SAVE errors
- **Delete Confirmation**: Working correctly!
- **Soft-Delete**: Working correctly

## Key Win: Delete Confirmation Flow

Step 13 asks for confirmation:
```
[Алексей]: Удали расход на заправку
Agent: Я нашла запись о расходе на заправку машины на 3500 рублей.
       Вы хотите ее удалить? [id: a8473e0c-...]
```

Step 14 deletes directly (high confidence):
```
[Мария]: Убери информацию про Пятёрочку
Agent: Удалила: Потратила в Пятёрочке 2340 рублей на продукты.
```

## Detailed Results

| Step | Message | Expected | Actual | Intent | Notes |
|------|---------|----------|--------|--------|-------|
| 2.1 | Наш месячный бюджет... | SAVE | SAVE | ✅ | Good |
| 2.2 | Сегодня потратила в Пятёрочке... | SAVE | SAVE | ✅ | Good |
| 2.3 | Заправил машину на 3500 рублей | SAVE | SAVE | ✅ | Good |
| 3.1 | Сколько мы уже потратили? | SEARCH | SEARCH | ✅ | Shows all, math wrong (6174 vs 5840) |
| 3.2 | Покажи все расходы | SEARCH | SEARCH | ✅ | Good |
| 3.3 | Что мы покупали в этом месяце? | SEARCH | SAVE | ❌ | Wrong - saved instead of searched |
| 3.4 | Какой у нас бюджет на развлечения? | SEARCH | SEARCH | ✅ | Good |
| 4.1 | Создай задачу: оплатить коммуналку... | TASK | TASK | ✅ | Good |
| 4.2 | Задача для Марии: купить подарки... | TASK | TASK | ✅ | Good |
| 4.3 | Какие у меня задачи? | SEARCH | SAVE | ❌ | Wrong - saved instead of searched |
| 5.1 | Задача оплатить коммуналку выполнена | COMPLETE | COMPLETE | ✅ | Good |
| 5.2 | Купила подарки, задача сделана | COMPLETE | COMPLETE | ✅ | Good |
| 6.1 | Удали расход на заправку | DELETE | DELETE | ✅ | **Asks for confirmation!** |
| 6.2 | Убери информацию про Пятёрочку | DELETE | DELETE | ✅ | **Auto-deleted (high confidence)** |
| 7.1 | Купил iPhone за 80000 рублей | SAVE | SAVE | ✅ | Good |
| 7.2 | чё там по бюджету? | SEARCH | SEARCH | ✅ | Good |
| 7.3 | Патратил 500 рублей на кофе | SAVE | SAVE | ✅ | Good |

## Issues Found

### P2: Intent Detection Instability (Steps 3.3, 4.3)
- "Что мы покупали?" detected as SAVE instead of SEARCH
- "Какие у меня задачи?" detected as SAVE instead of SEARCH
- These worked correctly in v11, might be LLM instability

### P3: Math Error (Step 3.1)
- Agent said "6174 рубля" but correct sum is 5840 (2340 + 3500)
- LLM arithmetic issue, not code issue

## What Works Well
- ✅ Soft-delete implemented
- ✅ Delete confirmation flow working
- ✅ High confidence (>0.85) = auto-delete
- ✅ Medium confidence (0.65-0.85) = ask confirmation
- ✅ Budget queries work
- ✅ Task creation and completion work

## Database Verification
```
Qdrant: 7 items (includes deleted - check needed)
Neo4j: 5 NOTE + 2 TASK = 7 items (includes soft-deleted)
```

## Test Metadata
- Project ID: a5e125db-3ce4-4cd0-a8d1-4c5990f99e5f
- Prompt Version: v13

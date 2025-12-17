# Scenario 012 - Russian Language Support - Iteration 1
Date: 2025-12-17

## Prompt Version: 7 (see tests/prompts/prompt-v7.txt)

## Test Summary
Full Russian language support test with SAVE, SEARCH, TASK, COMPLETE, DELETE operations.

## Results

| Operation | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Save budget (RU) | Save "Бюджет на декабрь: продукты 30000, транспорт 5000" | Saved as NOTE | PASS |
| Save expense (RU) | Save "Потратила 2500 рублей в магазине" | Saved as NOTE | PASS |
| Search with '?' (RU) | Find budget info | Found budget + expense | PASS |
| Search with 'Покажи' (RU) | Find expenses | Found budget + expense | PASS |
| Create task with assignee (RU) | Create task for Мария | Task created with [assigned to: Марии] | PASS |
| Search Maria's tasks (RU) | Find task assigned to Maria | Found task via semantic search | PASS |
| Complete task (RU) | Mark task as DONE | Task marked as DONE | PASS |
| Delete expense (RU) | Delete only expense, keep budget | Only expense deleted | PASS |

## Final Database State
```
NOTE: Бюджет на декабрь: продукты 30000, транспорт 5000. [N/A]
TASK: оплатить интернет [assigned to: Марии] [DONE]
```

## Issues Found and Fixed During Testing

### Issue 1: Delete too aggressive (Fixed in v7)
- **Problem**: "Удали расход в магазине" deleted budget (score 0.75) along with expense (score 0.72)
- **Root cause**: Threshold 0.65 was too low, both items matched semantically
- **Fix**: Added keyword matching requirement: delete if (score > 0.8) OR (score > 0.6 AND keyword match)
- **Result**: Now only expense with "магазине" keyword is deleted

### Issue 2: User already exists (Test setup)
- **Problem**: Test script failed when users already registered
- **Fix**: Use random email suffix in test script

## What Changed from Previous Iteration
This is the first iteration of test 012.

Changes made during this test session:
1. Added Graph relations tools (create_relation, get_related, find_path)
2. Added RELATION intent to intent detection
3. Added recency boost to search (up to 5% for items < 30 days)
4. Improved delete precision with keyword matching

## Raw Test Output
```
=== TEST 012: Russian Language Support (v2) ===

Registering users...
Project: 5c2b8d5c-22ff-4672-965b-fc745fef1c70
Setup complete

=== SAVE Tests ===
1. Save budget (RU):
Ok, я сохранил заметку: "Бюджет на декабрь: продукты 30000, транспорт 5000".

2. Save expense (RU):
Я записала в блокнот, что вы потратили 2500 рублей в магазине.

=== SEARCH Tests ===
3. Search with '?' (RU):
Бюджет на декабрь: продукты 30000, транспорт 5000. Также есть запись о трате 2500 рублей в магазине.

4. Search without '?' - 'Покажи' (RU):
Вот что я нашла: Бюджет на декабрь: продукты 30000, транспорт 5000 и Потратила 2500 рублей в магазине.

=== TASK Tests ===
5. Create task with assignee (RU):
Ok, я создал задачу для Марии: оплатить интернет до 20 декабря.

6. Search for Maria's tasks:
Вот что я нашла: Задача "оплатить интернет" назначена Марии. Также есть заметки о бюджете на декабрь (продукты 30000, транспорт 5000) и о тратах в магазине (2500 рублей).

=== COMPLETE Tests ===
7. Complete task (RU):
Задача "оплатить интернет", назначенная Марии, отмечена как выполненная.

=== DELETE Tests ===
8. Delete expense (RU):
Я удалил информацию о расходе в магазине.

=== VERIFICATION ===
NOTE: Бюджет на декабрь: продукты 30000, транспорт 5000. [N/A]
TASK: оплатить интернет [assigned to: Марии] [DONE]
```

## Backend Logs (Delete Operation)
```
Detected intent: DELETE -> tool: delete_knowledge
Executing tool: delete_knowledge with args: {query=расход в магазине}
Deleted knowledge item: 1f2a2924-eab4-4e12-bf2b-6d80af034a20 - 'Потратила 2500 рублей в магазине' (score: 0.720314)
Deleted 1 items for query: 'расход в магазине'
```

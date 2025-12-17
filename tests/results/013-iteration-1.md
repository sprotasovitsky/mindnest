# Scenario 013 - Edge Cases - Iteration 1
Date: 2025-12-17

## Prompt Version: 7 (see tests/prompts/prompt-v7.txt)

## Summary
Testing edge cases: long messages, special characters, delete/re-create, graph relations.

## Results

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Long message save | Saved | Saved | PASS |
| Long message search | Found | Not found | FAIL |
| Emoji save | Preserved | Preserved (as tasks) | PASS |
| Unicode save (₽, →, ✓) | Preserved | Preserved | PASS |
| Chinese/Japanese save | Preserved | Preserved | PASS |
| Search emoji content | Found | Found | PASS |
| Delete item | Deleted | Deleted | PASS |
| Re-create with new value | 150000 | 150000 | PASS |
| Create graph items | 3 items | 2 items + task | PARTIAL |
| Create relations | 2 relations | 1 relation | FAIL |
| Query relations | Related items | General search | PARTIAL |
| Find path | Path found | Path not found | FAIL |

## Detailed Results

### TEST 1: Very Long Message (1000+ words)
- **Save**: SUCCESS - 1921 words saved as meeting protocol
- **Search**: FAIL - "Я не нашел протокол совещания"
- Issue: Content was saved but search doesn't find it

### TEST 2: Special Characters
- **Emoji (🎉🎂🎁)**: PASS - Saved correctly, created tasks for birthday
- **Unicode (₽, →, ✓)**: PASS - "Цена: 1500₽ • Скидка: 10% → Итого: 1350₽" saved
- **Chinese/Japanese (日本, 北京)**: PASS - Saved as note with mixed scripts

### TEST 3: Delete and Re-create
- **Create budget 100000**: SUCCESS
- **Delete budget**: SUCCESS
- **Re-create budget 150000**: SUCCESS
- **Verify new value**: SUCCESS - Returns 150000, not old 100000

### TEST 4: Graph Relations
- **Create items**: PARTIAL - "API документация" wasn't saved as separate item
- **Create relation Backend → Project**: SUCCESS
- **Create relation APIDocs → Backend**: FAIL - API docs item not found
- **Query relations**: PARTIAL - Returns general search instead of related items
- **Find path**: FAIL - "не смог найти путь"

## Verification

Items in Qdrant: 7
- NOTE: Проект Alpha: разработка мобильного приложения
- TASK: Бэкенд для Alpha [assigned to: Node.js + PostgreSQL]
- FACT: Цена: 1500₽ • Скидка: 10% → Итого: 1350₽
- TASK: Купить торт [assigned to: Маша]
- TASK: Купить подарок [assigned to: Маша]
- NOTE: Встреча с партнёрами из 日本 (Япония) в 北京 (Пекин)
- NOTE: Бюджет на отпуск: 150000 рублей

Neo4j relations: 1 (expected 2)

## Issues Found

1. **Long text search fails**: Content is saved but search doesn't find it
   - Possible cause: Embedding of long text may not match search query well
   - Or: Long text stored but not vectorized properly

2. **Graph relations partially broken**:
   - Second relation not created (API docs item missing)
   - find_path returns no results
   - get_related seems to return general search instead of actual relations

3. **Item type interpretation**: "Бэкенд для Alpha: Node.js + PostgreSQL" saved as TASK instead of NOTE
   - LLM interpreted "Бэкенд" as task assignment

## Missing Long Text

The meeting protocol (1921 words) doesn't appear in final Qdrant count (7 items).
Either it was merged/deduplicated, or wasn't saved to Qdrant vector store.

## Next Steps

1. Investigate why long text isn't searchable
2. Fix graph relations - ensure items exist before creating relations
3. Verify find_path implementation
4. Consider improving get_related to use actual graph queries vs semantic search

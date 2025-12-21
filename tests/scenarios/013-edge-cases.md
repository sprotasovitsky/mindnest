# Test Scenario 013: Edge Cases

## Overview

Test edge cases and robustness:
1. Very long messages (1000+ words)
2. Special characters (emoji, unicode, non-Latin scripts)
3. Item deletion and re-creation
4. Graph relations traversal

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email              | Password |
|--------|--------------------|----------|
| Тестер | tester@test.com    | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register user
```
POST /api/auth/register
{ "email": "tester@test.com", "password": "test123", "name": "Тестер" }
```

#### Step 1.2: Create project
```
User: Тестер
POST /api/projects { "name": "Edge Cases Test", "description": "Testing edge cases" }
```

---

### Phase 2: Very Long Messages

#### Step 2.1: Save very long meeting notes (1000+ words)
```
User: Тестер
Chat: "Протокол совещания по проекту разработки нового продукта. Присутствовали: Иван Петров (руководитель проекта), Мария Сидорова (дизайнер), Алексей Козлов (разработчик), Елена Новикова (маркетолог). Пункт 1: обсуждение текущего статуса разработки. Было отмечено что работа идёт по плану. Дедлайн установлен на конец декабря. Пункт 2: обсуждение дизайна. Мария представила три варианта интерфейса. Команда выбрала второй вариант с минимальными доработками. Пункт 3: технические вопросы. Алексей сообщил о необходимости обновления серверной инфраструктуры. Бюджет на это составит около 50000 рублей. Пункт 4: маркетинг. Елена предложила стратегию продвижения через социальные сети. Бюджет на рекламу: 100000 рублей в месяц. Пункт 5: следующие шаги. Все участники получили задачи на следующую неделю. Следующее совещание назначено на понедельник в 10:00."
Expected: Agent saves the full text
Intent: SAVE
```

#### Step 2.2: Search in long content
```
User: Тестер
Chat: "Найди протокол совещания"
Expected: Agent finds the meeting notes
Intent: SEARCH
```

#### Step 2.3: Search specific detail from long text
```
User: Тестер
Chat: "Какой бюджет на рекламу?"
Expected: Agent finds "100000 рублей в месяц"
Intent: SEARCH
```

---

### Phase 3: Special Characters

#### Step 3.1: Save with emojis
```
User: Тестер
Chat: "🎉 День рождения Маши 15 декабря! 🎂 Нужно купить торт и 🎁 подарок"
Expected: Agent saves with emojis intact
Intent: SAVE
```

#### Step 3.2: Save with currency and math symbols
```
User: Тестер
Chat: "Цена товара: 1500₽ • Скидка: 10% → Итого: 1350₽ ✓"
Expected: Agent saves with all special characters
Intent: SAVE
```

#### Step 3.3: Save with Chinese/Japanese text
```
User: Тестер
Chat: "Встреча с партнёрами из 日本 (Япония) в 北京 (Пекин) 20 декабря"
Expected: Agent saves mixed script text
Intent: SAVE
```

#### Step 3.4: Search for emoji content
```
User: Тестер
Chat: "Когда день рождения Маши?"
Expected: Agent finds the birthday note
Intent: SEARCH
```

#### Step 3.5: Search for unicode content
```
User: Тестер
Chat: "Какая итоговая цена?"
Expected: Agent finds "1350₽"
Intent: SEARCH
```

---

### Phase 4: Delete and Re-create (Immutable Architecture)

#### Step 4.1: Create item
```
User: Тестер
Chat: "Бюджет на отпуск: 100000 рублей"
Expected: Agent saves budget
Intent: SAVE
```

#### Step 4.2: Verify item exists
```
User: Тестер
Chat: "Какой бюджет на отпуск?"
Expected: Agent returns "100000 рублей"
Intent: SEARCH
```

#### Step 4.3: Delete item (creates [DELETED] marker)
```
User: Тестер
Chat: "Удали бюджет на отпуск"
Expected: Agent creates [DELETED] marker with SUPERSEDES relation to original
Intent: SAVE (with [DELETED] marker)
Note: In immutable architecture, delete = create deletion marker + SUPERSEDES relation
```

#### Step 4.4: Verify item "deleted" (superseded)
```
User: Тестер
Chat: "Какой бюджет на отпуск?"
Expected: Agent says nothing found (LLM ignores superseded items)
Intent: SEARCH
Note: Original item still exists in DB but is superseded by [DELETED] marker
```

#### Step 4.5: Re-create with new value
```
User: Тестер
Chat: "Бюджет на отпуск: 150000 рублей"
Expected: Agent creates new item (duplicate check should allow - old was "deleted")
Intent: SAVE
```

#### Step 4.6: Verify new value
```
User: Тестер
Chat: "Какой бюджет на отпуск?"
Expected: Agent returns "150000 рублей" (ignores both old value AND deletion marker)
Intent: SEARCH
```

---

### Phase 5: Graph Relations

#### Step 5.1: Create base items
```
User: Тестер
Chat: "Проект Alpha: разработка мобильного приложения"
Expected: Agent saves project info
Intent: SAVE
```

```
User: Тестер
Chat: "Бэкенд Alpha: Node.js с PostgreSQL"
Expected: Agent saves backend info
Intent: SAVE
```

```
User: Тестер
Chat: "API документация для бэкенда Alpha"
Expected: Agent saves docs info
Intent: SAVE
```

#### Step 5.2: Create relations chain
```
User: Тестер
Chat: "Свяжи бэкенд Alpha с проектом Alpha - бэкенд относится к проекту"
Expected: Agent creates RELATES_TO relation (uses create_relation tool)
Intent: SAVE
```

```
User: Тестер
Chat: "API документация относится к бэкенду Alpha"
Expected: Agent creates second relation (uses create_relation tool)
Intent: SAVE
```

#### Step 5.3: Query single level relations
```
User: Тестер
Chat: "Что связано с проектом Alpha?"
Expected: Agent returns related items (бэкенд)
Intent: SEARCH (uses get_related)
```

#### Step 5.4: Query path between items
```
User: Тестер
Chat: "Как связаны API документация и проект Alpha?"
Expected: Agent finds path: Docs -> Backend -> Project
Intent: SEARCH (uses find_path)
```

---

## Verification Queries

### Neo4j - Check items
```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
RETURN k.type, substring(k.content, 0, 50) as content
ORDER BY k.createdAt;
```

### Neo4j - Check relations
```cypher
MATCH (a:KnowledgeItem {projectId: '<project_id>'})-[r]->(b:KnowledgeItem)
RETURN substring(a.content, 0, 30) as from, type(r) as relation, substring(b.content, 0, 30) as to;
```

### Qdrant - Check special characters preserved
```bash
curl -s "http://localhost:6333/collections/knowledge_vectors/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<project_id>"}}]},"limit":20,"with_payload":true}' \
  | jq '.result.points[].payload.content'
```

---

## Expected Results

| Step | Test | Expected |
|------|------|----------|
| 2.1 | Long message save | Full text saved |
| 2.2-2.3 | Search in long text | Content found |
| 3.1-3.3 | Special chars save | All chars preserved |
| 3.4-3.5 | Search special chars | Content found |
| 4.1-4.6 | Delete/re-create (immutable) | [DELETED] marker + SUPERSEDES, new value found |
| 5.1-5.4 | Graph relations | Relations created & queryable |

---

## Key Edge Cases

### Long messages:
- Content truncation limit: 1000 chars in vector metadata
- Full content stored in Neo4j
- Search should still work via embeddings

### Special characters:
- Emoji: 🎉 🎂 🎁
- Currency: ₽ € $ ¥
- Math: → × ÷ ± √
- Check marks: ✓ ✗ ☑
- Non-Latin: 日本語 中文 العربية

### Delete/re-create (Immutable Architecture):
- "Delete" creates [DELETED] marker + SUPERSEDES relation
- Original item still exists in DB (never physically deleted)
- LLM ignores superseded items in search responses
- Duplicate detection should allow re-creation after "delete"
- New value found correctly (ignores deletion marker chain)

### Graph relations:
- Chain: A -> B -> C
- get_related should return direct relations
- find_path should traverse multiple levels
- SUPERSEDES chains followed to end (for finding current version)

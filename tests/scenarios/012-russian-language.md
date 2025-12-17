# Test Scenario 012: Russian Language Support

## Overview

Test that the agent correctly handles messages in Russian language:
1. Search queries (questions)
2. Saving facts and notes
3. Creating tasks
4. Completing tasks
5. Deleting items

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email              | Password |
|--------|--------------------|----------|
| Алексей | alexey@test.com   | test123  |
| Мария   | maria@test.com    | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "alexey@test.com", "password": "test123", "name": "Алексей" }
{ "email": "maria@test.com", "password": "test123", "name": "Мария" }
```

#### Step 1.2: Алексей creates project
```
User: Алексей
POST /api/projects { "name": "Семейный бюджет", "description": "Учёт расходов семьи" }
```

#### Step 1.3: Add Мария to project
```
User: Алексей
POST /api/projects/{projectId}/members { "email": "maria@test.com" }
```

---

### Phase 2: SAVE Intent (Facts in Russian)

#### Step 2.1: Save budget limits (Russian)
```
User: Алексей
Chat: "Наш месячный бюджет: продукты 30000 рублей, транспорт 8000, развлечения 15000, одежда 10000."
Expected: Agent saves this as FACT
Intent: SAVE
```

#### Step 2.2: Save expense (Russian)
```
User: Мария
Chat: "Сегодня потратила в Пятёрочке 2340 рублей на продукты."
Expected: Agent saves expense
Intent: SAVE
```

#### Step 2.3: Save another expense
```
User: Алексей
Chat: "Заправил машину на 3500 рублей."
Expected: Agent saves expense
Intent: SAVE
```

---

### Phase 3: SEARCH Intent (Questions in Russian)

#### Step 3.1: Question with "?" (should be SEARCH)
```
User: Мария
Chat: "Сколько мы уже потратили?"
Expected: Agent searches and returns expenses
Intent: SEARCH
```

#### Step 3.2: Question without "?" (edge case)
```
User: Алексей
Chat: "Покажи все расходы"
Expected: Agent searches (not saves!)
Intent: SEARCH
```

#### Step 3.3: "Что" question
```
User: Мария
Chat: "Что мы покупали в этом месяце?"
Expected: Agent searches
Intent: SEARCH
```

#### Step 3.4: "Какой" question
```
User: Алексей
Chat: "Какой у нас бюджет на развлечения?"
Expected: Agent returns budget info
Intent: SEARCH
```

---

### Phase 4: TASK Intent (Russian)

#### Step 4.1: Create task (Russian)
```
User: Алексей
Chat: "Создай задачу: оплатить коммуналку до 25 декабря"
Expected: Agent creates task with deadline
Intent: TASK
```

#### Step 4.2: Create task for someone (Russian)
```
User: Алексей
Chat: "Задача для Марии: купить подарки детям до 30 декабря"
Expected: Agent creates task assigned to Мария
Intent: TASK
```

#### Step 4.3: Check tasks (Russian)
```
User: Мария
Chat: "Какие у меня задачи?"
Expected: Agent shows tasks
Intent: SEARCH
```

---

### Phase 5: COMPLETE Intent (Russian)

#### Step 5.1: Complete task (Russian)
```
User: Алексей
Chat: "Задача оплатить коммуналку выполнена"
Expected: Agent marks task as DONE
Intent: COMPLETE
```

#### Step 5.2: Alternative complete phrase
```
User: Мария
Chat: "Купила подарки, задача сделана"
Expected: Agent marks task as DONE
Intent: COMPLETE
```

---

### Phase 6: DELETE Intent (Russian)

#### Step 6.1: Delete item (Russian)
```
User: Алексей
Chat: "Удали расход на заправку"
Expected: Agent deletes the expense
Intent: DELETE
```

#### Step 6.2: Alternative delete phrase
```
User: Мария
Chat: "Убери информацию про Пятёрочку"
Expected: Agent deletes the expense
Intent: DELETE
```

---

### Phase 7: Edge Cases

#### Step 7.1: Mixed language
```
User: Алексей
Chat: "Купил iPhone за 80000 рублей"
Expected: Agent saves as expense
Intent: SAVE
```

#### Step 7.2: Informal Russian
```
User: Мария
Chat: "чё там по бюджету?"
Expected: Agent searches (informal question)
Intent: SEARCH
```

#### Step 7.3: Russian with typos
```
User: Алексей
Chat: "Патратил 500 рублей на кофе"
Expected: Agent saves expense (handles typo "патратил")
Intent: SAVE
```

---

## Verification Queries

### Neo4j Checks
```cypher
// Check all items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
RETURN k.type, k.content, k.status
ORDER BY k.createdAt;

// Check tasks
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'TASK'})
RETURN k.content, k.status, k.deadline;
```

---

## Expected Results

| Step | Message | Expected Intent |
|------|---------|-----------------|
| 2.1 | Наш месячный бюджет... | SAVE |
| 2.2 | Сегодня потратила... | SAVE |
| 2.3 | Заправил машину... | SAVE |
| 3.1 | Сколько мы уже потратили? | SEARCH |
| 3.2 | Покажи все расходы | SEARCH |
| 3.3 | Что мы покупали...? | SEARCH |
| 3.4 | Какой у нас бюджет...? | SEARCH |
| 4.1 | Создай задачу... | TASK |
| 4.2 | Задача для Марии... | TASK |
| 4.3 | Какие у меня задачи? | SEARCH |
| 5.1 | ...задача выполнена | COMPLETE |
| 5.2 | ...задача сделана | COMPLETE |
| 6.1 | Удали расход... | DELETE |
| 6.2 | Убери информацию... | DELETE |
| 7.1 | Купил iPhone... | SAVE |
| 7.2 | чё там по бюджету? | SEARCH |
| 7.3 | Патратил 500... | SAVE |

---

## Key Russian Keywords to Test

### SEARCH triggers:
- Question mark "?"
- "сколько", "что", "какой", "когда", "где", "кто", "почему", "как"
- "покажи", "найди", "выведи", "подскажи"

### TASK triggers:
- "создай задачу", "добавь задачу", "задача для"
- "назначь", "нужно сделать"

### COMPLETE triggers:
- "выполнена", "сделана", "готово", "завершена"
- "закончил", "сделал"

### DELETE triggers:
- "удали", "убери", "отмени", "верни"

### SAVE triggers (default if none of above):
- "потратил", "купил", "заплатил"
- Facts without question words

# Test Scenario 015: Cross-Language Search

## Overview

Test that the agent correctly handles cross-language scenarios:
1. Save information in Russian, search in English
2. Save information in English, search in Russian
3. Cross-language UPDATE operations
4. Mixed language content

This tests the multilingual capabilities of gemini-embedding-001.

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)
- **IMPORTANT**: Requires gemini-embedding-001 model (supports 100+ languages)

## Users

| Name   | Email              | Password |
|--------|--------------------|----------|
| Ivan   | ivan@test.com      | test123  |
| John   | john@test.com      | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "ivan@test.com", "password": "test123", "name": "Ivan" }
{ "email": "john@test.com", "password": "test123", "name": "John" }
```

#### Step 1.2: Ivan creates project
```
User: Ivan
POST /api/projects { "name": "International Project", "description": "Cross-language testing" }
```

#### Step 1.3: Add John to project
```
User: Ivan
POST /api/projects/{projectId}/members { "email": "john@test.com" }
```

---

### Phase 2: Save in Russian, Search in English

#### Step 2.1: Save Russian content (Ivan)
```
User: Ivan
Chat: "Встреча с клиентом запланирована на понедельник в 10 утра"
Expected: Agent saves meeting info
Intent: SAVE
```

#### Step 2.2: Save another Russian item (Ivan)
```
User: Ivan
Chat: "Бюджет проекта составляет 500000 рублей"
Expected: Agent saves budget info
Intent: SAVE
```

#### Step 2.3: Save Russian expense (Ivan)
```
User: Ivan
Chat: "Расходы на серверы: 50000 рублей в месяц"
Expected: Agent saves expense
Intent: SAVE
```

#### Step 2.4: English search for Russian content (John)
```
User: John
Chat: "When is the client meeting?"
Expected: Agent finds "Встреча с клиентом... понедельник в 10 утра"
Intent: SEARCH
```

#### Step 2.5: Another English search (John)
```
User: John
Chat: "What is the project budget?"
Expected: Agent finds "Бюджет проекта... 500000 рублей"
Intent: SEARCH
```

#### Step 2.6: English search for expense (John)
```
User: John
Chat: "How much do we spend on servers?"
Expected: Agent finds "Расходы на серверы: 50000 рублей"
Intent: SEARCH
```

---

### Phase 3: Save in English, Search in Russian

#### Step 3.1: Save English content (John)
```
User: John
Chat: "Product launch date is March 15, 2025"
Expected: Agent saves launch date
Intent: SAVE
```

#### Step 3.2: Save another English item (John)
```
User: John
Chat: "Marketing budget is 100000 dollars for Q1"
Expected: Agent saves marketing budget
Intent: SAVE
```

#### Step 3.3: Save English task-like info (John)
```
User: John
Chat: "Team standup meeting every day at 9am"
Expected: Agent saves meeting schedule
Intent: SAVE
```

#### Step 3.4: Russian search for English content (Ivan)
```
User: Ivan
Chat: "Когда запуск продукта?"
Expected: Agent finds "Product launch date is March 15"
Intent: SEARCH
```

#### Step 3.5: Another Russian search (Ivan)
```
User: Ivan
Chat: "Какой бюджет на маркетинг?"
Expected: Agent finds "Marketing budget is 100000 dollars"
Intent: SEARCH
```

#### Step 3.6: Russian search for standup (Ivan)
```
User: Ivan
Chat: "Когда ежедневные встречи команды?"
Expected: Agent finds "Team standup meeting every day at 9am"
Intent: SEARCH
```

---

### Phase 4: Cross-Language UPDATE

#### Step 4.1: Update Russian content with English query (John)
```
User: John
Chat: "Actually the project budget is 600000 rubles, not 500000"
Expected: Agent updates Russian budget content
Intent: UPDATE
```

#### Step 4.2: Verify update in Russian (Ivan)
```
User: Ivan
Chat: "Какой бюджет проекта?"
Expected: Agent returns updated value "600000"
Intent: SEARCH
```

#### Step 4.3: Update English content with Russian query (Ivan)
```
User: Ivan
Chat: "На самом деле маркетинговый бюджет 120000 долларов, не 100000"
Expected: Agent updates English marketing budget
Intent: UPDATE
```

#### Step 4.4: Verify update in English (John)
```
User: John
Chat: "What is the marketing budget?"
Expected: Agent returns updated value "120000"
Intent: SEARCH
```

---

### Phase 5: Mixed Language Content

#### Step 5.1: Save mixed content (Ivan)
```
User: Ivan
Chat: "Купил MacBook Pro за 250000 рублей для разработки"
Expected: Agent saves mixed RU/EN content
Intent: SAVE
```

#### Step 5.2: Search mixed content in English (John)
```
User: John
Chat: "How much was the MacBook?"
Expected: Agent finds MacBook purchase info
Intent: SEARCH
```

#### Step 5.3: Save technical terms mixed (John)
```
User: John
Chat: "Setup Docker и Kubernetes кластер на production серверах"
Expected: Agent saves mixed technical content
Intent: SAVE
```

#### Step 5.4: Search technical in Russian (Ivan)
```
User: Ivan
Chat: "Что настроили на серверах?"
Expected: Agent finds Docker/Kubernetes setup info
Intent: SEARCH
```

---

### Phase 6: Cross-Language DELETE

#### Step 6.1: Delete Russian content with English (John)
```
User: John
Chat: "Delete the server expenses information"
Expected: Agent deletes "Расходы на серверы"
Intent: DELETE
```

#### Step 6.2: Verify deletion in Russian (Ivan)
```
User: Ivan
Chat: "Какие расходы на серверы?"
Expected: Agent says nothing found
Intent: SEARCH
```

---

## Verification Queries

### Neo4j Checks
```cypher
// Check all items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
RETURN k.type, substring(k.content, 0, 50) as content
ORDER BY k.createdAt;
```

### Qdrant Checks
```bash
curl -s "http://localhost:6333/collections/knowledge_vectors/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<project_id>"}}]},"limit":20,"with_payload":true}' | jq '.result.points[] | .payload.content'
```

---

## Expected Results

| Step | Query Language | Content Language | Expected Result |
|------|----------------|------------------|-----------------|
| 2.4 | English | Russian | FOUND |
| 2.5 | English | Russian | FOUND |
| 2.6 | English | Russian | FOUND |
| 3.4 | Russian | English | FOUND |
| 3.5 | Russian | English | FOUND |
| 3.6 | Russian | English | FOUND |
| 4.1 | English | Russian | UPDATED |
| 4.3 | Russian | English | UPDATED |
| 5.2 | English | Mixed | FOUND |
| 5.4 | Russian | Mixed | FOUND |
| 6.1 | English | Russian | DELETED |

---

## Key Test Points

1. **EN→RU Search**: English query finds Russian content
2. **RU→EN Search**: Russian query finds English content
3. **Cross-language UPDATE**: Update content in different language than original
4. **Mixed content**: Handle technical terms in any language
5. **Cross-language DELETE**: Delete content using different language

---

## Notes

- This test requires gemini-embedding-001 model which supports 100+ languages
- Previous model (text-embedding-004) had ~0.40 cross-language similarity (below threshold)
- New model should have much higher cross-language similarity
- If tests fail, check that embedding model is correctly configured

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('ivan@test.com', 'john@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```

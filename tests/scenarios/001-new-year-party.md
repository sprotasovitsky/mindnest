# Test Scenario 001: New Year Party Planning

## Overview

Four friends (Andrey, Boris, Vika, Galya) collaborate to plan a New Year's Eve party at Andrey's dacha (countryside house). They:
1. Create a shared shopping list
2. Discuss and modify items
3. Assign tasks to each person
4. Complete tasks and record expenses
5. Calculate total expenses and who owes whom

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email                | Password   | Role   |
|--------|---------------------|------------|--------|
| Andrey | andrey@test.com     | test123    | owner  |
| Boris  | boris@test.com      | test123    | member |
| Vika   | vika@test.com       | test123    | member |
| Galya  | galya@test.com      | test123    | member |

## Project

| Field       | Value                                                    |
|-------------|----------------------------------------------------------|
| Name        | New Year Party 2025                                      |
| Description | Planning our NYE celebration at the dacha                |

## Onboarding

```
Description: "We're planning a New Year's Eve party at my dacha. Four friends will collaborate on shopping list, task assignments, and expense tracking."
Answers: "1. Shopping list management, task assignments, and expense splitting. 2. Four friends - Andrey (host), Boris, Vika, and Galya. 3. Successfully plan the party with clear task ownership and fair expense distribution."
Confirm: "Yes, that's perfect. Please save it."
```

## Test Execution

### Phase 1: Setup (User Registration & Project Creation)

#### Step 1.1: Register all users
```
POST /api/auth/register
For each user: { "email": "...", "password": "test123", "name": "..." }
```

#### Step 1.2: Andrey creates the project
```
User: Andrey
Action: Login, then create project
POST /api/projects { "name": "New Year Party 2025", "description": "Planning our NYE celebration at the dacha" }
```

#### Step 1.3: Andrey adds friends to project
```
User: Andrey
POST /api/projects/{projectId}/members { "email": "boris@test.com" }
POST /api/projects/{projectId}/members { "email": "vika@test.com" }
POST /api/projects/{projectId}/members { "email": "galya@test.com" }
```

---

### Phase 2: Shopping List Creation (Chat-based)

#### Step 2.1: Andrey starts the planning
```
User: Andrey
Chat: "Let's start planning our New Year party! I'm hosting at my dacha. We need to make a shopping list. First, I'll add some basics: we need champagne - 6 bottles, olivier salad ingredients for 8 people, and mandarin oranges - 3 kg."
Expected: Agent creates knowledge items for shopping list
```

#### Step 2.2: Boris adds his items
```
User: Boris
Chat: "I think we need more alcohol. Let me add: vodka - 2 bottles, wine (red) - 3 bottles, wine (white) - 2 bottles. Also, we should get some snacks: cheese platter, crackers, and olives."
Expected: Agent adds items to shopping list
```

#### Step 2.3: Vika adds food items
```
User: Vika
Chat: "For hot dishes, let's add: duck for roasting - 1 piece (about 2.5 kg), potatoes - 3 kg for baking, vegetables for salad - tomatoes 1 kg, cucumbers 0.5 kg. Also herring for shuba salad - 500g."
Expected: Agent adds items
```

#### Step 2.4: Galya adds desserts and decorations
```
User: Galya
Chat: "Don't forget desserts! Adding: Napoleon cake from the bakery - 1, ice cream - 2 liters, chocolate candies - 500g. For decorations: balloons - 20 pieces, garland lights - 2 sets, New Year napkins - 2 packs. And fireworks - 5 small and 2 big ones!"
Expected: Agent adds items
```

#### Step 2.5: Boris checks the list
```
User: Boris
Chat: "What do we have on our shopping list so far? Can you show me everything?"
Expected: Agent returns full shopping list
```

#### Step 2.6: Vika modifies quantity
```
User: Vika
Chat: "6 bottles of champagne is not enough for 4 people over the whole night. Change it to 10 bottles. Also add sparkling water - 6 bottles and regular water - 4 bottles."
Expected: Agent updates champagne quantity and adds water
```

#### Step 2.7: Andrey adds entertainment
```
User: Andrey
Chat: "Almost forgot - we need board games! Add Monopoly and Uno cards. Also, I'll rent a karaoke machine - adding that to the list."
Expected: Agent adds items
```

#### Step 2.8: Galya adds last items
```
User: Galya
Chat: "We need disposable plates - 20 pieces and cups - 30 pieces. Also garbage bags - 1 roll. And don't forget the Christmas tree - artificial, 180cm! Who has one?"
Expected: Agent adds items
```

#### Step 2.9: Andrey responds about tree
```
User: Andrey
Chat: "I have a Christmas tree, no need to buy. Remove it from the shopping list. But we need tree decorations - a box of ornaments."
Expected: Agent creates [DELETED] marker for tree (with SUPERSEDES relation), adds ornaments
Note: In immutable architecture, "remove" creates a deletion marker, not actual delete
```

---

### Phase 3: Task Assignment (Deadline: December 30)

#### Step 3.1: Andrey creates tasks
```
User: Andrey
Chat: "Let's assign who buys what. Create tasks with deadline December 30:
- Task for Boris: Buy all alcohol (champagne, vodka, wines)
- Task for Vika: Buy all food (duck, vegetables, salads ingredients, herring)
- Task for Galya: Buy desserts and decorations (cake, ice cream, candies, balloons, garlands, napkins, fireworks, ornaments)
- Task for me (Andrey): Rent karaoke, buy board games, disposable dishes and garbage bags"
Expected: Agent creates multiple tasks with deadline December 30
Note: System may decompose into individual tasks per item. Expected ~7+ tasks total.
```

#### Step 3.2: Boris checks his task
```
User: Boris
Chat: "What are my tasks for the New Year party?"
Expected: Agent shows Boris's task
```

#### Step 3.3: Vika asks about total items
```
User: Vika
Chat: "How many items do I need to buy in total? List them please."
Expected: Agent lists Vika's shopping items
```

---

### Phase 4: Task Completion & Expense Recording

#### Step 4.1: Boris completes his shopping
```
User: Boris
Chat: "I've bought everything! Here are the expenses:
- Champagne (10 bottles) - 8500 rubles
- Vodka (2 bottles) - 1200 rubles
- Red wine (3 bottles) - 2700 rubles
- White wine (2 bottles) - 1600 rubles
Total: 14000 rubles
Mark my task as completed."
Expected: Agent records expenses as knowledge, marks task done
```

#### Step 4.2: Vika completes her shopping
```
User: Vika
Chat: "Done with shopping! Expenses:
- Duck - 1500 rubles
- Potatoes 3kg - 150 rubles
- Tomatoes 1kg - 300 rubles
- Cucumbers 0.5kg - 150 rubles
- Herring 500g - 350 rubles
- Olivier ingredients - 800 rubles
- Mandarin oranges 3kg - 450 rubles
- Cheese platter - 900 rubles
- Crackers - 200 rubles
- Olives - 300 rubles
Total: 5100 rubles
My task is done!"
Expected: Agent records expenses, marks task done
```

#### Step 4.3: Galya completes her shopping
```
User: Galya
Chat: "All bought! My expenses:
- Napoleon cake - 1800 rubles
- Ice cream 2L - 600 rubles
- Chocolate candies - 400 rubles
- Balloons 20 pcs - 500 rubles
- Garland lights 2 sets - 1200 rubles
- Napkins 2 packs - 200 rubles
- Small fireworks 5 pcs - 2500 rubles
- Big fireworks 2 pcs - 3000 rubles
- Tree ornaments - 800 rubles
Total: 11000 rubles
Task completed!"
Expected: Agent records expenses, marks task done
```

#### Step 4.4: Andrey completes his shopping
```
User: Andrey
Chat: "I'm done too:
- Karaoke rental (2 days) - 3000 rubles
- Monopoly - 1500 rubles
- Uno cards - 300 rubles
- Disposable plates 20pcs - 200 rubles
- Disposable cups 30pcs - 150 rubles
- Garbage bags - 100 rubles
- Sparkling water 6 bottles - 300 rubles
- Regular water 4 bottles - 200 rubles
Total: 5750 rubles
All my tasks are done!"
Expected: Agent records expenses, marks ALL Andrey's tasks as done
Note: If Andrey has multiple tasks, agent should complete all of them
```

---

### Phase 5: Expense Summary & Settlement

#### Step 5.1: Andrey asks for summary
```
User: Andrey
Chat: "Can you give me a summary of all expenses? How much did each person spend and what's the total?"
Expected: Agent calculates from stored knowledge:
- Boris: 14000 rubles
- Vika: 5100 rubles
- Galya: 11000 rubles
- Andrey: 5750 rubles
- Total: 35850 rubles
- Per person: 8962.50 rubles
```

#### Step 5.2: Boris asks who owes whom
```
User: Boris
Chat: "Calculate who owes whom money so we're all even."
Expected: Agent calculates:
- Fair share per person: 8962.50 rubles
- Boris overpaid: 14000 - 8962.50 = 5037.50 rubles (should receive)
- Vika underpaid: 8962.50 - 5100 = 3862.50 rubles (should pay)
- Galya overpaid: 11000 - 8962.50 = 2037.50 rubles (should receive)
- Andrey underpaid: 8962.50 - 5750 = 3212.50 rubles (should pay)

Settlement:
- Vika pays Boris: 3862.50 rubles
- Andrey pays Boris: 1175 rubles
- Andrey pays Galya: 2037.50 rubles
```

#### Step 5.3: Verify all tasks completed
```
User: Galya
Chat: "Are all tasks for the party completed?"
Expected: Agent confirms all 4 tasks are done
```

---

## Verification Queries

After test execution, verify in databases:

### PostgreSQL Checks
```sql
-- Check users created
SELECT id, email, name FROM users WHERE email LIKE '%@test.com';

-- Check project created
SELECT * FROM projects WHERE name = 'New Year Party 2025';

-- Check project members
SELECT pm.*, u.email FROM project_members pm
JOIN users u ON pm.user_id = u.id
WHERE pm.project_id = '<project_id>';
```

### Neo4j Checks
```cypher
// Check all knowledge items for the project
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
RETURN k.type, k.content, k.status
ORDER BY k.createdAt;

// Check shopping list items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'shopping' OR k.type = 'note'
RETURN k.content;

// Check tasks
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'task'})
RETURN k.content, k.status, k.deadline;

// Check expense records
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rubles' OR k.content CONTAINS 'expense'
RETURN k.content;
```

### Qdrant Checks
```bash
# Check vectors exist for project
curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<project_id>"}}]}}'
```

### Immutable Architecture Checks
```cypher
// Check SUPERSEDES relations (for deleted/updated items)
MATCH (a:KnowledgeItem)-[r:SUPERSEDES]->(b:KnowledgeItem)
WHERE a.projectId = '<project_id>'
RETURN a.content, b.content;

// Check [DELETED] markers
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content STARTS WITH '[DELETED]'
RETURN k.content;

// Check [DONE] task markers
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS '[DONE]'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 4 users registered
- 1 shared project with 4 members
- ~30+ knowledge items (shopping list + expenses + deletion markers)
- 4 expense records (one per person)
- 7+ tasks created (system decomposes into individual tasks)
- All tasks completed (each has [DONE] marker + SUPERSEDES relation)
- 1 [DELETED] marker for Christmas tree
- Agent can calculate totals from stored data

Note: In immutable architecture, completed tasks and deleted items create NEW nodes with SUPERSEDES relations, so total node count will be higher than just "items saved".

---

## Cleanup

To reset for re-running:
```sql
-- Delete test users and cascade
DELETE FROM users WHERE email LIKE '%@test.com';

-- Or delete just the project
DELETE FROM projects WHERE name = 'New Year Party 2025';
```

```cypher
// Delete all knowledge for project
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```

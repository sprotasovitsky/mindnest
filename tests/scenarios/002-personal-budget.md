# Test Scenario 002: Personal Budget Tracking

## Overview

Single user (Marina) tracks her monthly expenses through chat. She:
1. Records daily expenses with categories
2. Asks analytical questions about spending
3. Sets budget limits
4. Gets alerts when approaching limits
5. Generates monthly summary

## Complexity: Simple (1 user)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email              | Password |
|--------|-------------------|----------|
| Marina | marina@test.com   | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register user
```
POST /api/auth/register
{ "email": "marina@test.com", "password": "test123", "name": "Marina" }
```

#### Step 1.2: Create project
```
User: Marina
POST /api/projects { "name": "My Budget December 2025", "description": "Personal expense tracking" }
```

---

### Phase 2: Setting Up Budget Categories

#### Step 2.1: Marina sets budget limits
```
User: Marina
Chat: "I want to track my December budget. My monthly limits are:
- Food & groceries: 25000 rubles
- Transport: 5000 rubles
- Entertainment: 10000 rubles
- Clothing: 15000 rubles
- Utilities: 8000 rubles
- Health: 5000 rubles
Total budget: 68000 rubles"
Expected: Agent saves budget limits as facts/notes
```

---

### Phase 3: Recording Expenses (Week 1)

#### Step 3.1: December 1 - Groceries
```
User: Marina
Chat: "Today I spent 2340 rubles at Perekrestok supermarket on groceries"
Expected: Agent records expense with date, amount, category
```

#### Step 3.2: December 2 - Transport
```
User: Marina
Chat: "Metro card refill - 800 rubles"
Expected: Agent records transport expense
```

#### Step 3.3: December 3 - Multiple expenses
```
User: Marina
Chat: "Today's expenses:
- Lunch at cafe: 650 rubles (food)
- Taxi home: 450 rubles (transport)
- Netflix subscription: 799 rubles (entertainment)"
Expected: Agent records all three expenses with correct categories
```

#### Step 3.4: December 4 - Groceries
```
User: Marina
Chat: "Bought products at VkusVill for 1890 rubles"
Expected: Agent records food expense
```

#### Step 3.5: December 5 - Clothing
```
User: Marina
Chat: "Bought a winter jacket at Zara - 8990 rubles"
Expected: Agent records clothing expense
```

#### Step 3.6: December 6 - Health
```
User: Marina
Chat: "Pharmacy - vitamins and cold medicine: 1200 rubles"
Expected: Agent records health expense
```

#### Step 3.7: December 7 - Entertainment
```
User: Marina
Chat: "Cinema tickets for two: 1400 rubles, popcorn and drinks: 600 rubles"
Expected: Agent records entertainment expenses
```

---

### Phase 4: First Week Analysis

#### Step 4.1: Week summary
```
User: Marina
Chat: "How much did I spend this week? Show me by category"
Expected: Agent calculates:
- Food: 2340 + 650 + 1890 = 4880 rubles
- Transport: 800 + 450 = 1250 rubles
- Entertainment: 799 + 1400 + 600 = 2799 rubles
- Clothing: 8990 rubles
- Health: 1200 rubles
Total: 19119 rubles
```

#### Step 4.2: Budget status
```
User: Marina
Chat: "How am I doing against my budget limits?"
Expected: Agent shows remaining budget per category:
- Food: 25000 - 4880 = 20120 left (80%)
- Transport: 5000 - 1250 = 3750 left (75%)
- Entertainment: 10000 - 2799 = 7201 left (72%)
- Clothing: 15000 - 8990 = 6010 left (40%)
- Health: 5000 - 1200 = 3800 left (76%)
- Utilities: 8000 - 0 = 8000 left (100%)
```

---

### Phase 5: Recording Expenses (Week 2)

#### Step 5.1: December 8 - Utilities
```
User: Marina
Chat: "Paid utilities: electricity 2100, internet 800, mobile 600"
Expected: Agent records utilities expense: 3500 rubles
```

#### Step 5.2: December 10 - Food
```
User: Marina
Chat: "Big grocery shopping at Auchan: 4500 rubles"
Expected: Agent records food expense
```

#### Step 5.3: December 12 - Entertainment
```
User: Marina
Chat: "Concert tickets for December 20: 5500 rubles"
Expected: Agent records entertainment expense
```

#### Step 5.4: December 14 - Clothing alert
```
User: Marina
Chat: "Bought boots for 7500 rubles"
Expected: Agent records expense AND alerts that clothing budget exceeded (8990 + 7500 = 16490 > 15000)
```

---

### Phase 6: Mid-Month Analysis

#### Step 6.1: Specific category query
```
User: Marina
Chat: "How much did I spend on food so far?"
Expected: Agent calculates: 2340 + 650 + 1890 + 4500 = 9380 rubles
```

#### Step 6.2: Over-budget categories
```
User: Marina
Chat: "Which categories am I over budget?"
Expected: Agent identifies Clothing is over by 1490 rubles
```

#### Step 6.3: Largest expenses
```
User: Marina
Chat: "What were my top 5 biggest expenses?"
Expected: Agent lists:
1. Winter jacket: 8990 rubles
2. Boots: 7500 rubles
3. Concert tickets: 5500 rubles
4. Auchan groceries: 4500 rubles
5. Utilities: 3500 rubles
```

---

### Phase 7: Expense Corrections (Immutable Architecture)

#### Step 7.1: Correction
```
User: Marina
Chat: "I made a mistake - the Auchan shopping was actually 4200 rubles, not 4500. Please correct it."
Expected: Agent creates NEW expense record (4200 rubles) with SUPERSEDES relation to old one
Note: In immutable architecture, corrections create new items, not update existing
```

#### Step 7.2: Refund
```
User: Marina
Chat: "I returned the boots and got a refund of 7500 rubles"
Expected: Agent creates refund record with CONTRADICTS relation to original boots expense
Note: CONTRADICTS relation means these items cancel out in calculations
```

---

### Phase 8: Final Analysis

#### Step 8.1: Monthly summary request
```
User: Marina
Chat: "Give me a complete summary of my December spending so far"
Expected: Agent provides detailed breakdown by category with totals and budget comparison
```

#### Step 8.2: Remaining budget
```
User: Marina
Chat: "How much can I still spend this month in each category?"
Expected: Agent calculates remaining amounts
```

#### Step 8.3: Spending pattern
```
User: Marina
Chat: "What day of the week do I usually spend the most?"
Expected: Agent analyzes patterns (if enough data)
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All expenses
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rubles'
RETURN k.content, k.createdAt
ORDER BY k.createdAt;

// Budget limits
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'budget' OR k.content CONTAINS 'limit'
RETURN k.content;

// Check SUPERSEDES relations (corrections)
MATCH (new:KnowledgeItem)-[r:SUPERSEDES]->(old:KnowledgeItem)
WHERE new.projectId = '<project_id>'
RETURN new.content as corrected, old.content as original;

// Check CONTRADICTS relations (refunds)
MATCH (refund:KnowledgeItem)-[r:CONTRADICTS]->(original:KnowledgeItem)
WHERE refund.projectId = '<project_id>'
RETURN refund.content, original.content;
```

### Qdrant Checks
```bash
curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<project_id>"}}]}}'
```

---

## Expected Data Summary

After successful test:
- 1 user registered
- 1 personal project
- 6 budget limit records
- ~17+ expense records (including correction and refund markers)
- 1 SUPERSEDES relation (Auchan correction: 4200 supersedes 4500)
- 1 CONTRADICTS relation (boots refund contradicts boots purchase)
- Agent can calculate totals by category (accounting for SUPERSEDES/CONTRADICTS)
- Agent can identify over-budget categories
- Agent can handle corrections and refunds via immutable architecture

---

## Key Test Points

1. **Categorization**: Agent correctly categorizes expenses
2. **Date handling**: Agent associates expenses with correct dates
3. **Calculations**: Accurate sum/remaining calculations (respecting SUPERSEDES/CONTRADICTS)
4. **Alerts**: Warning when budget exceeded
5. **Corrections**: Creates new item + SUPERSEDES relation (not update)
6. **Refunds**: Creates refund item + CONTRADICTS relation
7. **Analysis**: Pattern recognition and summaries

---

## Cleanup

```sql
DELETE FROM users WHERE email = 'marina@test.com';
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```

# Test Scenario 003: Recipe and Shopping List

## Overview

Single user (Dmitry) plans a dinner party. He:
1. Saves a complex recipe
2. Agent automatically extracts shopping list
3. Adjusts portions for guest count
4. Marks items as bought
5. Asks about cooking steps

## Complexity: Simple (1 user)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email            | Password |
|--------|-----------------|----------|
| Dmitry | dmitry@test.com | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register user
```
POST /api/auth/register
{ "email": "dmitry@test.com", "password": "test123", "name": "Dmitry" }
```

#### Step 1.2: Create project
```
User: Dmitry
POST /api/projects { "name": "Dinner Party Menu", "description": "Recipes and shopping for Saturday dinner" }
```

---

### Phase 2: Saving Recipe

#### Step 2.1: Main dish recipe
```
User: Dmitry
Chat: "Save this recipe for Beef Stroganoff (serves 4):

Ingredients:
- Beef tenderloin: 600g
- Onion: 2 medium
- Mushrooms: 300g
- Sour cream: 200ml
- Beef broth: 200ml
- Flour: 2 tbsp
- Butter: 50g
- Vegetable oil: 2 tbsp
- Salt, pepper to taste
- Fresh parsley: 1 bunch

Instructions:
1. Cut beef into thin strips
2. Season with salt and pepper
3. Slice onions and mushrooms
4. Heat oil in pan, brown beef in batches (2-3 min per batch)
5. Remove beef, add butter, sauté onions until golden (5 min)
6. Add mushrooms, cook 5 more minutes
7. Sprinkle flour, stir 1 minute
8. Add broth, stir until thickened
9. Add sour cream, mix well
10. Return beef, simmer 5 minutes
11. Garnish with parsley
Serve with rice or mashed potatoes."

Expected: Agent saves recipe with all ingredients and steps
```

#### Step 2.2: Side dish recipe
```
User: Dmitry
Chat: "Also save this recipe for Mashed Potatoes (serves 4):

Ingredients:
- Potatoes: 1 kg
- Butter: 80g
- Milk: 150ml
- Salt: 1 tsp
- Nutmeg: pinch

Instructions:
1. Peel and cut potatoes into chunks
2. Boil in salted water until tender (20 min)
3. Drain, return to pot
4. Add butter, mash
5. Heat milk, add gradually while mashing
6. Season with salt and nutmeg
7. Serve hot"

Expected: Agent saves recipe
```

#### Step 2.3: Salad recipe
```
User: Dmitry
Chat: "And a Caesar Salad (serves 4):

Ingredients:
- Romaine lettuce: 1 large head
- Chicken breast: 300g
- Parmesan cheese: 80g
- Croutons: 100g
- Caesar dressing: 150ml
- Cherry tomatoes: 200g
- Olive oil: 2 tbsp

Instructions:
1. Grill chicken breast, slice
2. Wash and tear lettuce
3. Halve cherry tomatoes
4. Combine lettuce, tomatoes in bowl
5. Top with chicken and croutons
6. Drizzle dressing
7. Shave parmesan on top"

Expected: Agent saves recipe
```

---

### Phase 3: Shopping List Generation

#### Step 3.1: Request shopping list
```
User: Dmitry
Chat: "Create a shopping list from all my recipes"
Expected: Agent compiles ingredients from all recipes:
- Beef tenderloin: 600g
- Onion: 2 medium
- Mushrooms: 300g
- Sour cream: 200ml
- Beef broth: 200ml
- Flour: 2 tbsp
- Butter: 130g (50g + 80g combined)
- Vegetable oil: 2 tbsp
- Parsley: 1 bunch
- Potatoes: 1 kg
- Milk: 150ml
- Nutmeg
- Romaine lettuce: 1 head
- Chicken breast: 300g
- Parmesan: 80g
- Croutons: 100g
- Caesar dressing: 150ml
- Cherry tomatoes: 200g
- Olive oil: 2 tbsp
- Salt, pepper (pantry items)
```

---

### Phase 4: Adjusting Portions

#### Step 4.1: More guests
```
User: Dmitry
Chat: "Actually, I'll have 8 guests instead of 4. Can you adjust all recipes and the shopping list?"
Expected: Agent creates NEW versions of recipes for 8 people (with SUPERSEDES relations to originals):
- Beef: 1200g
- Potatoes: 2 kg
- Chicken: 600g
- etc.
Note: In immutable architecture, adjustments create new items, not modify existing
```

#### Step 4.2: Verify adjustment
```
User: Dmitry
Chat: "How much beef do I need now?"
Expected: Agent returns 1200g (from the new superseding recipe, ignoring outdated 600g version)
```

---

### Phase 5: Shopping Process

#### Step 5.1: Mark items bought
```
User: Dmitry
Chat: "I bought at the butcher: beef tenderloin 1.2kg for 1800 rubles and chicken breast 600g for 540 rubles"
Expected: Agent marks items as bought, records prices
```

#### Step 5.2: More shopping
```
User: Dmitry
Chat: "Got from supermarket:
- Potatoes 2kg - 120 rub
- Onions 4pcs - 60 rub
- Mushrooms 600g - 320 rub
- Sour cream 400ml - 180 rub
- Milk 200ml - 80 rub
- Butter 200g - 240 rub
- Parmesan 100g - 450 rub
- Caesar dressing - 280 rub
All bought!"
Expected: Agent marks items, records prices
```

#### Step 5.3: Check remaining
```
User: Dmitry
Chat: "What do I still need to buy?"
Expected: Agent lists remaining items:
- Romaine lettuce
- Cherry tomatoes
- Croutons
- Parsley
- Beef broth
- Flour (or check pantry)
- Oils
```

#### Step 5.4: Final shopping
```
User: Dmitry
Chat: "Bought the rest: lettuce 180 rub, cherry tomatoes 200 rub, croutons 150 rub, parsley 50 rub, beef broth 2 packs 160 rub. I have flour and oils at home."
Expected: Agent marks everything complete
```

---

### Phase 6: Cooking Assistance

#### Step 6.1: Recipe recall
```
User: Dmitry
Chat: "Remind me how to make the beef stroganoff"
Expected: Agent provides the saved recipe with adjusted quantities
```

#### Step 6.2: Specific question
```
User: Dmitry
Chat: "How long do I boil the potatoes?"
Expected: Agent answers: 20 minutes until tender
```

#### Step 6.3: Cooking order
```
User: Dmitry
Chat: "In what order should I cook everything to have all dishes ready at the same time?"
Expected: Agent suggests timeline:
1. Start potatoes boiling (20 min)
2. While potatoes cook, prep beef and vegetables
3. Start mashing potatoes
4. Cook beef stroganoff (15-20 min)
5. Assemble Caesar salad last (5 min)
Total time: ~45 minutes
```

---

### Phase 7: Post-Dinner

#### Step 7.1: Total cost
```
User: Dmitry
Chat: "How much did I spend on ingredients in total?"
Expected: Agent calculates: 1800 + 540 + 120 + 60 + 320 + 180 + 80 + 240 + 450 + 280 + 180 + 200 + 150 + 50 + 160 = 4810 rubles
```

#### Step 7.2: Cost per person
```
User: Dmitry
Chat: "How much is that per person for 8 guests?"
Expected: Agent calculates: 4810 / 8 = 601.25 rubles per person
```

#### Step 7.3: Recipe rating
```
User: Dmitry
Chat: "The dinner was great! Rate the beef stroganoff recipe 5 stars and add note: guests loved it, next time add more mushrooms"
Expected: Agent creates NEW version of recipe with rating and note (SUPERSEDES original)
Note: In immutable architecture, adding rating creates new item with relation to old
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All recipes (including superseded versions)
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'recipe' OR k.content CONTAINS 'Ingredients'
RETURN k.content;

// Shopping list items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.type = 'NOTE' OR k.type = 'TASK'
RETURN k.content, k.status;

// Expenses
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rub'
RETURN k.content;

// SUPERSEDES relations (recipe adjustments and rating)
MATCH (new:KnowledgeItem)-[r:SUPERSEDES]->(old:KnowledgeItem)
WHERE new.projectId = '<project_id>'
RETURN new.content as current, old.content as outdated;
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
- 1 project
- 6+ recipe items (3 original + 3 adjusted for 8 people with SUPERSEDES)
- Shopping list with ~20 items
- All items marked as bought with prices
- Recipe rated with 5 stars (new version SUPERSEDES adjusted version)
- Multiple SUPERSEDES relations tracking recipe evolution

---

## Key Test Points

1. **Recipe parsing**: Agent extracts structured data from recipe text
2. **List aggregation**: Combines ingredients from multiple recipes
3. **Math operations**: Doubles quantities correctly via new recipe versions
4. **State tracking**: Tracks bought vs needed items
5. **Information retrieval**: Returns current (non-superseded) recipe data
6. **Immutable updates**: Rating creates new item + SUPERSEDES relation

---

## Cleanup

```sql
DELETE FROM users WHERE email = 'dmitry@test.com';
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```

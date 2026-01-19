# Test Scenario 015: Mixed Messages and Context References

## Overview

Tests the classifier's ability to:
1. Handle mixed messages (data + question = BOTH type)
2. Extract and save data even when primary intent is a question
3. Resolve references to LLM responses (e.g., "save this recipe" after LLM suggests one)
4. Verify that referenced data from chat history is properly expanded and saved

## Users

| Name | Email          | Password | Role  |
|------|----------------|----------|-------|
| Alex | alex@test.com  | test123  | owner |

## Project

| Field | Value                   |
|-------|-------------------------|
| Name  | Family Planning Project |

## Onboarding

```
Description: "A shared space for family tasks, shopping lists, recipes, and planning."
Answers: "1. Shopping lists, recipes, task management. 2. Family members. 3. Keep everything organized."
Confirm: "Yes, save it."
```

## Test Execution

### Phase 0: Setup

#### Step 0.1: Create project
```
User: Alex
POST /api/projects { "name": "Family Planning Project", "description": "A shared space for family tasks, shopping lists, recipes, and planning." }
```

### Phase 1: Mixed Messages (BOTH type)

#### Step 1.1: Shopping list + question
```
User: Alex
Chat: "We need to buy: milk, eggs, bread, cheese. What else should we add for breakfast?"
Expected: Data saved (milk, eggs, bread, cheese) AND question answered
```

#### Step 1.2: Task + question
```
User: Alex
Chat: "Mom should pick up the kids at 3pm. What time does the school usually end?"
Expected: Task saved (Mom pick up kids 3pm) AND question answered
```

#### Step 1.3: Expense + question
```
User: Alex
Chat: "I spent $120 on groceries today. How much have we spent this week?"
Expected: Expense saved ($120 groceries) AND calculates weekly total
```

---

### Phase 2: LLM Response References

#### Step 2.1: Ask for recipe suggestion
```
User: Alex
Chat: "Suggest a simple pasta recipe for dinner"
Expected: LLM provides a pasta recipe with ingredients
```

#### Step 2.2: Save the suggested recipe
```
User: Alex
Chat: "Save this recipe to our collection"
Expected: Recipe from previous LLM response saved to database
```

#### Step 2.3: Create shopping list from recipe
```
User: Alex
Chat: "Create a shopping list for that pasta recipe"
Expected: Shopping list created with recipe ingredients from history
```

#### Step 2.4: Verify recipe was saved
```
User: Alex
Chat: "What recipes do we have saved?"
Expected: Returns the pasta recipe that was saved in step 2.2
```

---

### Phase 3: Complex Reference Chains

#### Step 3.1: Ask for breakfast ideas
```
User: Alex
Chat: "Give me 3 quick breakfast ideas with ingredients"
Expected: LLM provides 3 numbered breakfast options with ingredient lists
```

#### Step 3.2: Select option by reference
```
User: Alex
Chat: "Let's go with option 2. Add those ingredients to our shopping list."
Expected: Ingredients from option 2 extracted and added to shopping list
```

#### Step 3.3: Verify all shopping items
```
User: Alex
Chat: "Show me everything on our shopping list"
Expected: Returns all items: breakfast basics, pasta ingredients, option 2 ingredients
```

---

### Phase 4: Multiple Data Points in One Message

#### Step 4.1: Multiple facts + question
```
User: Alex
Chat: "Dad bought milk for $4 and bread for $2 at the store. Mom needs to call the doctor tomorrow. What appointments do we have scheduled?"
Expected: All 3 facts saved (2 expenses + 1 task) AND question answered
```

#### Step 4.2: Correction + question
```
User: Alex
Chat: "Actually the milk was $5, not $4. What's our total grocery spending so far?"
Expected: Correction saved AND total calculated
```

---

### Phase 5: Edge Cases

#### Step 5.1: Very short reference
```
User: Alex
Chat: "Add that too"
Expected: Classifier attempts to resolve "that" from recent history
```

#### Step 5.2: Numbered list reference
```
User: Alex
Chat: "Save items 1 and 3 from the breakfast list"
Expected: Specific items extracted from numbered list in history
```

#### Step 5.3: Final verification
```
User: Alex
Chat: "Give me a summary of everything we've saved today"
Expected: Returns comprehensive list of all saved items, tasks, expenses, recipes
```

---

## Verification Queries

### Neo4j Checks
```cypher
// Check shopping list items from step 1.1
MATCH (e:Entity)
WHERE e.group_id = '<project_id>'
AND (e.name =~ '(?i).*milk.*' OR e.name =~ '(?i).*eggs.*' OR e.name =~ '(?i).*bread.*')
RETURN e.name, e.summary;

// Check task from step 1.2
MATCH ()-[r:RELATES_TO]->()
WHERE r.group_id = '<project_id>'
AND r.fact =~ '(?i).*mom.*pick.*kids.*'
RETURN r.fact;

// Check expenses
MATCH ()-[r:RELATES_TO]->()
WHERE r.group_id = '<project_id>'
AND (r.fact CONTAINS '$' OR r.fact =~ '(?i).*spent.*' OR r.fact =~ '(?i).*bought.*')
RETURN r.fact;

// Check recipe was saved (from LLM response reference)
MATCH (e:Entity)
WHERE e.group_id = '<project_id>'
AND (e.name =~ '(?i).*pasta.*' OR e.summary =~ '(?i).*recipe.*')
RETURN e.name, e.summary;

// Count total entities (should have significant data)
MATCH (e:Entity)
WHERE e.group_id = '<project_id>'
RETURN count(e) as entity_count;
```

---

## Key Test Points

1. **BOTH Classification**: Messages with data AND questions correctly classified
2. **Data Extraction**: Data saved even when question is present
3. **Reference Resolution**: "this recipe", "option 2", "that" expanded from history
4. **LLM Response Capture**: User references to LLM suggestions properly saved
5. **Multiple Data Points**: Single message with multiple facts all extracted
6. **Corrections**: Updates handled correctly

---

## Success Criteria

- [ ] Step 1.1: milk, eggs, bread, cheese appear in Neo4j
- [ ] Step 1.2: Task about Mom picking up kids saved
- [ ] Step 1.3: $120 expense recorded
- [ ] Step 2.2-2.4: Pasta recipe from LLM response saved and retrievable
- [ ] Step 3.2: Option 2 ingredients added to list
- [ ] Step 4.1: All 3 facts saved (2 expenses + 1 task)
- [ ] Step 5.3: Summary includes all previously saved data

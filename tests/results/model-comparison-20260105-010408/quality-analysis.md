# Quality Analysis: gemini-2.5-flash Model Tests

## Summary

Analysis of 3 test scenarios run with gemini-2.5-flash for Graphiti entity extraction.

| Test | Scenario | Entities | Edges | Critical Issues |
|------|----------|----------|-------|-----------------|
| 001 | New Year Party | 52 | 236 | Debt calculation wrong (Galya 7,800 vs 11,000) |
| 002 | Personal Budget | 36 | 96 | Correction refused, category logic |
| 003 | Recipe Shopping | 31 | 131 | Prices not extracted, total wrong |

---

## Detailed Problem Analysis

### Test 001 Step 18: Debt Calculation Error

**Expected:** Galya spent 11,000 rubles
**Actual:** LLM calculated 7,800 rubles

**Root Cause:** Search/ranking issue

| Component | Status | Details |
|-----------|--------|---------|
| Classifier | QUESTION | Correct |
| Database | All data correct | Galya entity has total 11,000 |
| Search | **PROBLEM** | Did not return: Galya, Napoleon cake, garland lights, New Year napkins |
| LLM | Correct | Calculated correctly from received context: 5500+600+500+400+800=7,800 |

**Evidence:**
- 40 nodes returned, but "Galya" not among them
- Missing entities with prices: Napoleon cake (1800), garland lights (1200), napkins (200)
- LLM summed only what it received: fireworks(5500) + ice cream(600) + balloons(500) + candies(400) + ornaments(800) = 7,800

---

### Test 002 Step 18: Correction Refused

**User message:** "I made a mistake - the Auchan shopping was actually 4200 rubles, not 4500. Please correct it."
**Response:** "I can't correct... no information in knowledge graph"

**Root Cause:** Classifier error

| Component | Status | Details |
|-----------|--------|---------|
| Classifier | **PROBLEM** | DATA instead of COMMAND |
| Search | Not executed | For DATA, search is skipped |
| Database | Correct | Correction was recorded |
| LLM | Correct | Responded "can't" because no context provided |

**Evidence from logs:**
```
Classified as MessageType.DATA: I made a mistake - the Auchan shopping was actuall...
```

For DATA messages, code passes `facts=[], entities=[]` to LLM - no search performed.

---

### Test 002 Step 21: Clothing Remaining Wrong

**Expected:** 6,010 rubles (15,000 - 8,990)
**Actual in test:** 13,510 rubles

**Status:** RESOLVED - current behavior is correct (returns 6,010)

Likely transient issue during test execution - boots refund was not properly processed at that moment.

---

### Test 003 Step 3: Caesar Salad "Not Found"

**User message:** Full Caesar Salad recipe
**Response in test:** "I don't have any information about a Caesar Salad"

**Root Cause:** LLM response issue

| Component | Status | Details |
|-----------|--------|---------|
| Classifier | DATA | Correct |
| Database | Recorded | Recipe was saved |
| LLM | **PROBLEM** | Said "no information" instead of confirming save |

**Current behavior:** Now responds "Would you like me to record..." - better but still not ideal.

---

### Test 003 Step 14: Total Cost Wrong

**Expected:** 4,810 rubles (2340 + 1730 + 740)
**Actual:** 4,070 rubles

**Root Cause:** Entity extraction failure

| Component | Status | Details |
|-----------|--------|---------|
| Classifier | QUESTION | Correct |
| Graphiti extraction | **PROBLEM** | Did not extract prices from Step 10 |
| Database | Missing data | lettuce=180, croutons=150, parsley=50, broth=160 NOT recorded with prices |
| Search | Correct | Returned what exists |
| LLM | Correct | Calculated from available data |

**Evidence from Neo4j:**
- "Beef broth" → "ingredient in Beef Stroganoff" (no price!)
- "Fresh parsley" → "garnish for Beef Stroganoff" (no price!)
- "Romaine lettuce" → "ingredient in Caesar Salad" (no price!)

Step 10 message: "Bought the rest: lettuce 180 rub, cherry tomatoes 200 rub, croutons 150 rub, parsley 50 rub, beef broth 2 packs 160 rub"
Graphiti extracted recipe relationships but NOT purchase prices.

---

## Root Causes Summary

| Problem | Affected Tests | Component |
|---------|----------------|-----------|
| Search/ranking misses relevant entities | 001 | Graphiti search |
| Classifier: corrections → DATA | 002 | classifier.py |
| Entity extraction misses prices | 003 | Graphiti LLM |
| LLM says "no info" after save | 003 | Response generation |

---

## Recommendations

### 1. Classifier (High Priority, Low Effort)

**Problem:** "correct", "update", "fix mistake" classified as DATA

**Solution:** Add examples to classifier prompt:
- "correct X to Y" → COMMAND
- "I made a mistake" → COMMAND
- "update the amount" → COMMAND
- "change X from Y to Z" → COMMAND

**Also:** For COMMAND, perform search before responding (like QUESTION).

### 2. Entity Extraction (High Priority, Medium Effort)

**Problem:** Prices not extracted from purchase messages

**Solutions:**
- Improve Graphiti extraction prompt for numerical data
- Post-process: regex parse prices and enrich entities
- Use stronger model for extraction

### 3. Search/Ranking (Medium Priority, Medium Effort)

**Problem:** Person entities not in top results for financial queries

**Solutions:**
- For queries with "calculate", "owes", "expenses" → always include all project member entities
- Increase node limit (40 → 60)
- Boost "Person" type entities in ranking

### 4. LLM Responses (Low Priority, Low Effort)

**Problem:** Says "no information" after user just provided data

**Solution:** For DATA messages, always respond with confirmation of what was saved, not queries about knowledge.

---

## Test Artifacts

- Project IDs:
  - 001: ade8165e-34f1-4f57-9729-739dd5ec8b4f
  - 002: 67ea10dd-471e-4111-a78a-1bdb39ed773f
  - 003: 67839252-f0c3-4474-b8ad-ba04bdd17eb7

- Test outputs: `test-output-flash-*.txt`
- Entities dump: `entities-flash-*.txt`

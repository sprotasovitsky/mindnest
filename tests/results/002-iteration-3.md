# Scenario 002 - Iteration 3
Date: 2025-12-17

## Prompt Version: 2 (see tests/prompts/prompt-v2.txt)

## Architecture Change
- Two-step intent detection with structured output
- Step 1: Fast model (gemini-2.0-flash) detects intent
- Step 2: Tool executed BEFORE response generation
- Step 3: Main model generates confirmation

## Results

### Save Operations
| Step | Message | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| 2.1 | Budget limits | SAVE | SAVED | OK |
| 3.1 | Perekrestok 2340 | SAVE | SAVED | OK |
| 3.2 | Metro 800 | SAVE | SAVED | OK |
| 3.3 | Lunch+Taxi+Netflix | SAVE | SAVED | OK |
| 3.4 | VkusVill 1890 | SAVE | SAVED | OK |
| 3.5 | Jacket 8990 | SAVE | SAVED | OK |
| 3.6 | Pharmacy 1200 | SAVE | SAVED | OK |
| 3.7 | Cinema 1400+600 | SAVE | SAVED | OK |
| 5.1 | Utilities | SAVE | SAVED | OK |
| 5.2 | Auchan 4500 | SAVE | SAVED | OK |
| 5.3 | Concert 5500 | SAVE | SAVED | OK |
| 5.4 | Boots 7500 | SAVE | SAVED | OK |
| 8.1 | NY food | SAVE | SAVED | OK |
| 8.2 | Gift 4500 | SAVE | SAVED | OK |
| 8.3 | Restaurant 6500 | SAVE | SAVED | OK |
| 8.4 | Taxi 1200 | SAVE | SAVED | OK |

**Save rate: 16/16 = 100%**

### Update Operations
| Step | Message | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| 7.1 | Auchan 4500→4200 | UPDATE | UPDATED | OK |

### Delete Operations
| Step | Message | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| 7.2 | Boots refund | DELETE | DELETED | OK |

### Search/Analyze Operations
| Step | Message | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| 4.1 | Week summary | SEARCH | Correct breakdown | OK |
| 4.2 | Budget status | SEARCH | Correct analysis | OK |
| 6.1 | Food spending | SEARCH | 9380 (correct) | OK |
| 6.2 | Over budget | SEARCH | Clothing +1490 | OK |
| 6.3 | Top 5 expenses | SEARCH | Correct list | OK |
| 9.1 | Total spending | SEARCH | ~51219 | OK |

### Final DB State
```
15 KnowledgeItems in Neo4j
- Budget limits (1)
- Expenses (13)
- Updated Auchan (corrected value)
- Boots deleted (refund)
```

## Issues Found
1. **Response text sometimes inaccurate** - LLM confirmation doesn't always match saved data
   - Step 5.1: Responded with budget limits instead of utilities confirmation
   - Step 5.3: Responded with "Metro card refill" instead of "Concert tickets"
   - Step 8.2: Responded with "concert tickets" instead of "gift"
   - Root cause: Response generation uses stale context

2. **Minor**: Intent detection sometimes includes search results in response when it should just confirm

## What Changed from Previous Iteration
1. Added two-step intent detection with fast model
2. Tools are now executed BEFORE response generation based on detected intent
3. Low temperature (0.1) for intent classification ensures consistent detection
4. Main model receives context about already-executed tools

## Comparison with Iteration 2
| Metric | Iteration 2 | Iteration 3 |
|--------|-------------|-------------|
| Save rate | ~40% (7/16) | **100% (16/16)** |
| Update works | No | **Yes** |
| Delete works | No | **Yes** |
| Analysis accuracy | Partial | **Good** |

## Next Steps
1. Run test 001 to verify no regression
2. Consider improving response generation to match saved data
3. Fix response text accuracy issues

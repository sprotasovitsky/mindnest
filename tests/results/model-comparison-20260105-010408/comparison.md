# Model Comparison Report (2 models × 3 scenarios)

## Timing Results (seconds)

| Scenario | flash | pro |
|----------|-------|-----|
| 001-new-year-party | 672 | 702 |
| 002-personal-budget | 440 | 538 |
| 003-recipe-shopping | 369 | 529 |

## Data Statistics (Entities / Edges)

| Scenario | flash | pro |
|----------|-------|-----|
| 001-new-year-party | 52 / 236 | 50 / 193 |
| 002-personal-budget | 36 / 96 | 30 / 84 |
| 003-recipe-shopping | 31 / 131 | 32 / 127 |

## Project IDs (for database comparison)

| Scenario | flash | pro |
|----------|-------|-----|
| 001-new-year-party | ade8165e... | 7f058235... |
| 002-personal-budget | 67ea10dd... | 9a3134d6... |
| 003-recipe-shopping | 67839252... | 0b62ad43... |

## Conclusion

**gemini-2.5-flash** is chosen as default for Graphiti entity extraction:
- ~20% faster than pro
- Similar entity/edge counts
- Best balance of speed and quality

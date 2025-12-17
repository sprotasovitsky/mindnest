# Model Upgrade Test Results - Version 8
Date: 2025-12-17

## Prompt Version: 8 (see tests/prompts/prompt-v8.txt)

## Model Changes

| Component | Old | New |
|-----------|-----|-----|
| Chat | gemini-2.0-flash | gemini-2.5-flash-lite |
| Chat Pro | gemini-2.5-pro | gemini-2.5-pro (unchanged) |
| Flash | gemini-2.0-flash | gemini-2.5-flash-lite |
| Embedding | text-embedding-004 | gemini-embedding-001 |
| Vector Dimensions | 768 | 3072 |

## Test Results

### Basic Russian Operations (Test 012)
| Operation | Expected | Result | Status |
|-----------|----------|--------|--------|
| Save fact | Saved | Saved | PASS |
| Save budget | Saved | Saved | PASS |
| Save decision | Saved | Saved | PASS |
| Create task | Created | Created | PASS |
| Save expense | Saved | Saved | PASS |
| Search birthday | Found | Found | PASS |
| Search budget | Found | Found | PASS |
| Search destination | Found | Found | PASS |
| Search tasks | Found | Found | PASS |
| Update budget | 200k→250k | Updated | PASS |
| Delete expense | Deleted | Deleted | PASS |
| Complete task | Completed | Completed | PASS |

**Russian Language: 12/12 PASS (100%)**

### Cross-Language Search (NEW!)
| Test | Query | Content | Result | Status |
|------|-------|---------|--------|--------|
| EN→RU | "client meeting" | "Встреча с клиентом" | Found | PASS |
| EN→RU | "project budget" | "Бюджет проекта" | Found | PASS |
| EN→RU | "release deadline" | "Дедлайн релиза" | Found | PASS |
| RU→EN | "стэндап команды" | "Team standup" | Found | PASS |
| RU→EN | "бюджет на маркетинг" | "Marketing budget" | Found | PASS |
| RU→EN | "запуск продукта" | "Product launch" | Found | PASS |
| Cross-lang UPDATE | EN query updates RU content | Updated | PASS |

**Cross-Language: 7/7 PASS (100%)**

## Performance Observations

- Response time: Similar to previous models
- Quality: Responses are coherent and accurate
- Cross-language: Major improvement from text-embedding-004

## Key Improvement

**Before (text-embedding-004):**
- Cross-language similarity: ~0.40 (below 0.5 threshold)
- EN query could NOT find RU content
- Documented as "known limitation"

**After (gemini-embedding-001):**
- Cross-language similarity: HIGH (above threshold)
- EN query FINDS RU content perfectly
- RU query FINDS EN content perfectly
- Cross-language UPDATE works

## Migration Checklist

- [x] Update application.yml with new model names
- [x] Update VectorRepository.java (768 → 3072)
- [x] Delete old Qdrant collection
- [x] Restart backend (auto-creates new collection)
- [x] Verify new collection has 3072 dimensions
- [x] Run basic tests
- [x] Run cross-language tests
- [x] Document results

## Notes

- text-embedding-004 is deprecated August 2025
- gemini-embedding-001 is #1 on MTEB Multilingual leaderboard
- 100+ language support vs limited languages before
- No code changes needed in EmbeddingService (same API)

## Conclusion

Model upgrade successful. Cross-language search is now a working feature instead of a known limitation. All previous functionality preserved.

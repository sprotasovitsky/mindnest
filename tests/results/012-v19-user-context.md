# Scenario 012 - Prompt v19 (User Context)
Date: 2025-12-17

## Prompt Version: 19 (see tests/prompts/prompt-v19-user-context.txt)

## Changes from v18
- Added user context to search response: current user + project members
- LLM now receives info about who is asking and who is in the project
- Updated prompt to handle "my tasks" vs "Boris's tasks" vs "all tasks"

## Project ID: 5d3d99fd-4965-4439-aa89-132f0aaac3f0

## Test Setup
- User 1: Мария (owner)
- User 2: Борис (member)
- Task 1: "купить хлеб" [assigned to: Мария]
- Task 2: "отправить отчёт" [assigned to: Борис]
- Task 3: "позвонить в офис" [no assignee]

## User Context Feature Test

### Test 1: "Какие у меня задачи?" (Мария спрашивает)
| Expected | Actual | Status |
|----------|--------|--------|
| Only Maria's task | "У вас есть задача 'купить хлеб'" | ✅ PASSED |

### Test 2: "Какие задачи у Бориса?"
| Expected | Actual | Status |
|----------|--------|--------|
| Only Boris's task | "У Бориса есть задача: 'отправить отчёт'" | ✅ PASSED |

### Test 3: "Покажи все задачи"
| Expected | Actual | Status |
|----------|--------|--------|
| All 3 tasks | Lists all with assignees | ✅ PASSED |

## Code Changes

### AgentService.java
1. Added `buildUserContext()` method:
   - Gets current user name from `userRepository`
   - Gets project members from `projectTools.getMembers()`
   - Returns string: "Current user: Мария\nProject members: Мария (owner), Борис (member)"

2. Updated `executeSearch()`:
   - Now accepts `userId` parameter
   - Calls `buildUserContext(userId, projectId)`
   - Appends user context to graph text for LLM

3. Updated search response prompt (v19):
   - Added "CRITICAL - User Context" section
   - Instructions for filtering by current user / other users
   - Examples: "my tasks" → filter by current user

## Summary

| Feature | v17 | v18 | v19 |
|---------|-----|-----|-----|
| SAVE | 100% | 100% | 100% |
| SEARCH | 80% | 100% | 100% |
| TASK | 100% | 100% | 100% |
| COMPLETE | 100% | 100% | 100% |
| DELETE markers | 100% | 100% | 100% |
| DELETE semantics | 0% | 100% | 100% |
| User filtering | 0% | 0% | 100% |

## Architecture Status
- ✅ Immutable system working
- ✅ DELETE via markers + SUPERSEDES
- ✅ COMPLETE via [DONE] + SUPERSEDES
- ✅ Graph expansion shows full chains
- ✅ LLM understands SUPERSEDES semantics
- ✅ Deleted items correctly ignored in responses
- ✅ User context passed to LLM
- ✅ LLM filters by user appropriately

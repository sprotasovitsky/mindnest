# Prompt Version 23
Date: 2025-12-18

## Changes from v22
1. **All prompts translated to English** - examples now in English
2. **Content stored in English** - intent-detection translates user input to English
3. **Person names kept original** - assignee field preserves original name
4. **addedBy field in graph** - serializeForLLM now shows who created each item
5. **Task completion fixed** - uses complete_task_by_title instead of creating new task
6. **search-response-prompt updated** - explains addedBy field for expense tracking

## Key Design Decisions

### Language Handling
- All content stored in English (translated at intent-detection)
- Person names preserved in original form
- Response language detected from user message and appended to prompt

### Expense Tracking
- Items have `addedBy:UserName` property showing who created them
- LLM instructed to group expenses by addedBy for per-person summaries

### Task Completion
- Uses `complete_task_by_title` tool to find and mark existing task as DONE
- Semantic search matches task by title/content

---

## Known Issues in v23

### Task Completion Partial
- When user has multiple tasks, only first matching task is completed
- Example: Andrey had 4 tasks, only 1 was marked DONE
- Root cause: `complete_task_by_title` finds first match only

### Expense Search Incomplete
- Search doesn't always find all expense items
- Total calculations are partial (6000 instead of 35850)

---

## Prompt Files

### 1. intent-detection-prompt.txt
- All examples in English
- CRITICAL LANGUAGE RULE: translate to English
- Person names kept original
- 15 examples covering SAVE, SEARCH, TASK, CHAT

### 2. decomposition-prompt.txt
- English examples
- Preserves original language during split (translation happens in intent-detection)

### 3. search-response-prompt.txt
- Explains addedBy field for expense tracking
- Instructions for grouping by addedBy
- Status interpretation (DONE/TODO)

### 4. action-response-prompt.txt
- Simplified, relies on language detection in code

### 5. system-prompt.txt
- Tool usage rules
- Response rules

---

## Code Changes

### GraphService.java
```java
// Added overloaded method with user name mapping
public String serializeForLLM(GraphContext context, Map<String, String> userIdToName) {
    // ... outputs addedBy:UserName for each item
}
```

### AgentService.java
```java
// Added helper method
private Map<String, String> buildUserIdToNameMap(String projectId) {
    // Returns map of userId -> userName for all project members
}

// Task completion now uses complete_task_by_title
if ("DONE".equalsIgnoreCase(status)) {
    Map<String, Object> args = new HashMap<>();
    args.put("title", targetQuery);
    toolExecutor.execute("complete_task_by_title", args, projectId, userId);
}
```

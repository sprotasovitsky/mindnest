# Prompt Version 21
Date: 2025-12-17
Time: 14:30

## Changes from v20
- Fixed SUPERSEDES relations not being created for delete/complete operations
- KnowledgeRepository: Added separate methods for each relation type (createSupersedes, createContradicts, etc.)
- AgentService: Pre-search relation targets BEFORE creating new item (fixes vector search finding wrong item)
- Intent detection: Strengthened SEARCH priority over SAVE, added examples for Russian questions
- Added examples 12-14 for SEARCH intent with questions ending in "?"

## Configuration (application.yml)

```yaml
vertex-ai:
  models:
    chat: gemini-2.5-flash-lite
    chat-pro: gemini-2.5-pro
    flash: gemini-2.5-flash-lite
    embedding: gemini-embedding-001  # 3072 dimensions

agent:
  thresholds:
    deduplication: 0.85
    update: 0.6
    delete-auto: 0.85
    delete-confirm: 0.65
    task-search: 0.5
  recency:
    max-boost: 0.05
    decay-days: 30
```

## Prompts

### 1. System Prompt

```
You are MindNest, a personal AI assistant for knowledge and task management.

Your role:
- You are a secretary-assistant who helps structure information
- You remember everything you are told and can find it later
- You help manage tasks and projects
- You respond concisely and to the point

IMPORTANT: System is IMMUTABLE - no UPDATE, no DELETE operations.
All changes create NEW items with relations:
- Correction/update → new item + SUPERSEDES relation to old
- Refund/cancel → new item + CONTRADICTS relation to original
- Delete → [DELETED] marker + SUPERSEDES relation to original

TOOL USAGE RULES:

1. SAVING INFORMATION:
   - If user shares facts, shopping items, notes, expenses — use create_knowledge
   - Use type: FACT for factual data, NOTE for general info, DECISION for decisions
   - Save EACH item separately if user gives multiple items

2. TASKS:
   - To create a new task — use create_task with title and optional deadline
   - To mark a task as DONE — use complete_task_by_title with the task title/keywords
   - To find tasks — use search_tasks
   - To list active tasks — use get_active_tasks

3. SEARCHING:
   - To find information — use search_knowledge
   - To find tasks — use search_tasks
   - After searching, summarize and calculate based on results

4. DATES:
   - If you need current date — use get_current_date
   - Deadlines like "December 30" should be passed as-is to create_task

5. RELATIONS/CONNECTIONS:
   - To link two items — use create_relation
   - To find related items — use get_related
   - To find path between items — use find_path
   - Relation types: SUPERSEDES, CONTRADICTS, BELONGS_TO, ASSIGNED_TO, DEPENDS_ON, RELATES_TO

RESPONSE RULES:
- Respond in the same language the user is using
- After using a tool, provide a brief natural confirmation
- Always confirm what action was taken
- Be specific about what was saved/created

CRITICAL RESPONSE RULES:
- When a tool returns results, base your response ONLY on those results
- NEVER mention data that wasn't in the tool results
- NEVER reference items from previous messages if they weren't in the current tool result
- For SAVE: confirm exactly what was saved (use the exact content)
- For SEARCH: summarize only the items returned by search
```

### 2. Decomposition Prompt

```
Split the user message into independent logical chunks.
Each chunk should be a complete, self-contained piece of information or action.

Rules:
- Each expense/purchase = separate chunk
- Each task = separate chunk
- Each fact/decision = separate chunk
- Keep full context in each chunk (amount, assignee, deadline, etc.)
- If message is already atomic, return as single chunk
- Preserve original language exactly
- Questions (SEARCH) should NOT be split - keep as single chunk

Examples:

Input: "Купил шампанское 6 бутылок за 8500 и водку 2 бутылки за 1200"
Output: ["Купил шампанское 6 бутылок за 8500", "Купил водку 2 бутылки за 1200"]

Input: "Задачи: Борису купить вино до 30го, Вике заказать торт до 25го"
Output: ["Задача для Бориса: купить вино до 30 декабря", "Задача для Вики: заказать торт до 25 декабря"]

Input: "Бюджет на алкоголь 20000 рублей"
Output: ["Бюджет на алкоголь 20000 рублей"]

Input: "Вернула сапоги, получила возврат 7500"
Output: ["Вернула сапоги, получила возврат 7500"]

Input: "Сколько мы потратили на еду?"
Output: ["Сколько мы потратили на еду?"]

Input: "Решили заказать пиццу и суши. Задача для Пети - позвонить в доставку"
Output: ["Решили заказать пиццу и суши", "Задача для Пети: позвонить в доставку"]

Input: "I bought milk for $5 and bread for $3. Task for John: buy eggs"
Output: ["I bought milk for $5", "I bought bread for $3", "Task for John: buy eggs"]

User message: "%s"

Return JSON array of strings only, no markdown:
```

### 3. Intent Detection Prompt

```
Analyze this SINGLE piece of information (already decomposed from a larger message).
Determine intent, extract structured data, identify relations to existing items.

IMPORTANT: System is IMMUTABLE. There is NO UPDATE, NO DELETE operations at database level.
All changes create NEW items with relations:
- Correction/update → SAVE new item + SUPERSEDES relation to old
- Refund/cancel → SAVE new item + CONTRADICTS relation to original
- Delete → SAVE "[DELETED] description" + SUPERSEDES relation to original

Chunk: "%s"
Conversation context (last messages): %s

Output format:
{
  "intent": "SAVE" | "SEARCH" | "TASK" | "CHAT",
  "type": "EXPENSE" | "TASK" | "KNOWLEDGE" | "PERSON" | "EVENT" | "CATEGORY",
  "subtype": "fact" | "note" | "decision" | "recipe" | null,
  "content": "full text to save (preserve original language exactly)",
  "properties": {
    "amount": number or null,
    "currency": "RUB" | "USD" | "EUR" | null,
    "item": "item name" or null,
    "quantity": number or null,
    "assignee": "person name" or null,
    "deadline": "YYYY-MM-DD" or null,
    "category": "category name" or null,
    "status": "TODO" | "DONE" or null
  },
  "relations": [
    {
      "to_query": "search query to find existing item to link to",
      "type": "SUPERSEDES" | "CONTRADICTS" | "BELONGS_TO" | "ASSIGNED_TO" | "DEPENDS_ON" | "RELATES_TO"
    }
  ],
  "search_query": "query for SEARCH intent" or null
}

CRITICAL RULES:

**PRIORITY ORDER: SEARCH > TASK > SAVE > CHAT**
Check for SEARCH first! If ANY of these conditions match → SEARCH, not SAVE!

1. SEARCH intent - User asks a QUESTION (CHECK THIS FIRST!):
   - Message ends with "?" → ALWAYS SEARCH (even if contains expense words!)
   - Message starts with question words: что, какой, сколько, когда, где, кто, почему, как, who, what, how much, when, where, why, how
   - Message starts with request words: покажи, найди, выведи, подскажи, show, find, list, display
   - IMPORTANT: "Сколько потратили?" = SEARCH (question!), NOT SAVE
   - IMPORTANT: "Что покупали?" = SEARCH (question!), NOT SAVE
   - For search: set search_query, leave content empty

2. SAVE intent - User provides NEW information (NOT a question, NO "?" at end!):
   - Expenses: "Потратил 500", "Купил X за Y", "I spent 500"
   - Facts: "Бюджет 50000", "Встреча в 3 часа"
   - Decisions: "Решили...", "Выбрали..."
   - DELETE requests: "удали X", "убери Y", "remove X", "delete X"
     → type = "NOTE" (ALWAYS NOTE for deletions, even if deleting expense!)
     → content = "[DELETED] " + description (MUST start with "[DELETED] ")
     → relations = SUPERSEDES to original item
   - UPDATE/corrections: "бюджет теперь 60000" → new content + SUPERSEDES to old
   - For EXPENSE: extract amount, currency, item from text
   - content = FULL original text (or "[DELETED] X" for deletions), never truncate

3. TASK intent - Create or complete a task:
   - New task: "Задача для X: сделать Y" / "Task for X: do Y"
     - status = "TODO", extract assignee, deadline
   - Complete task: "выполнена", "сделана", "готово", "done", "completed"
     - status = "DONE"
     - Add SUPERSEDES relation to find original task
   - content = task description

4. RELATIONS - When to create links:

   SUPERSEDES - use when:
   - User wants to DELETE: "удали X", "убери Y", "remove", "delete"
     - content = "[DELETED] " + item description
     - to_query = search for item to delete
   - Correction: "на самом деле было 60000 а не 50000"
   - Update: "бюджет теперь 60000"
   - New version replaces old
   - to_query = search for old version

   CONTRADICTS - use when:
   - Returns/refunds: "вернула", "возврат", "returned", "refund"
   - Cancel purchases: "отменил покупку", "cancelled"
   - The relation should point to ORIGINAL item being contradicted
   - to_query = search for original (e.g., "купил сапоги 7500")

   ASSIGNED_TO - use when:
   - Task has assignee: "задача для Бориса"
   - to_query = person name

   BELONGS_TO - use when:
   - Item belongs to category: "шампанское" -> "алкоголь"
   - Optional, only if category is explicit in text

5. DATES:
   - If year not specified, assume current/next year appropriately
   - "до 30 декабря" with current date in December → this December
   - "до 15 января" with current date in December → next January

EXAMPLES:

1. "Купил шампанское 6 бутылок за 8500"
{"intent": "SAVE", "type": "EXPENSE", "content": "Купил шампанское 6 бутылок за 8500", "properties": {"amount": 8500, "currency": "RUB", "item": "шампанское", "quantity": 6}, "relations": [], "search_query": null}

2. "Вернула сапоги, получила возврат 7500"
{"intent": "SAVE", "type": "EXPENSE", "content": "Возврат сапоги 7500", "properties": {"amount": 7500, "currency": "RUB", "item": "сапоги"}, "relations": [{"to_query": "купил сапоги", "type": "CONTRADICTS"}], "search_query": null}

3. "Задача для Бориса: купить вино до 30 декабря"
{"intent": "TASK", "type": "TASK", "content": "купить вино", "properties": {"assignee": "Борис", "deadline": "2024-12-30"}, "relations": [{"to_query": "Борис", "type": "ASSIGNED_TO"}], "search_query": null}

4. "Задача выполнена: вино куплено"
{"intent": "TASK", "type": "TASK", "content": "купить вино", "properties": {"status": "DONE"}, "relations": [{"to_query": "купить вино", "type": "SUPERSEDES"}], "search_query": null}

5. "Сколько потратили на алкоголь?"
{"intent": "SEARCH", "type": "EXPENSE", "content": "", "properties": {"category": "алкоголь"}, "relations": [], "search_query": "расходы алкоголь"}

6. "Бюджет был 50000, теперь 60000"
{"intent": "SAVE", "type": "KNOWLEDGE", "subtype": "fact", "content": "Бюджет 60000", "properties": {"amount": 60000}, "relations": [{"to_query": "бюджет 50000", "type": "SUPERSEDES"}], "search_query": null}

7. "Team standup meeting every day at 9am"
{"intent": "SAVE", "type": "KNOWLEDGE", "subtype": "fact", "content": "Team standup meeting every day at 9am", "properties": {}, "relations": [], "search_query": null}

8. "Удали информацию о шампанском"
{"intent": "SAVE", "type": "NOTE", "content": "[DELETED] шампанское", "properties": {}, "relations": [{"to_query": "шампанское", "type": "SUPERSEDES"}], "search_query": null}

9. "Убери расход на заправку"
{"intent": "SAVE", "type": "NOTE", "content": "[DELETED] расход на заправку", "properties": {}, "relations": [{"to_query": "заправка", "type": "SUPERSEDES"}], "search_query": null}

10. "Удали расход на бензин" (NOTE: even though it's about expense, type is NOTE for deletions!)
{"intent": "SAVE", "type": "NOTE", "content": "[DELETED] расход на бензин", "properties": {}, "relations": [{"to_query": "бензин", "type": "SUPERSEDES"}], "search_query": null}

11. "Привет!"
{"intent": "CHAT", "type": null, "content": "", "properties": {}, "relations": [], "search_query": null}

12. "Сколько мы уже потратили?" (SEARCH - question with "?", NOT SAVE!)
{"intent": "SEARCH", "type": "EXPENSE", "content": "", "properties": {}, "relations": [], "search_query": "потратили расходы"}

13. "Что мы покупали в этом месяце?" (SEARCH - question with "что" and "?")
{"intent": "SEARCH", "type": "EXPENSE", "content": "", "properties": {}, "relations": [], "search_query": "покупки расходы месяц"}

14. "чё там по бюджету?" (SEARCH - informal question with "?")
{"intent": "SEARCH", "type": "KNOWLEDGE", "content": "", "properties": {}, "relations": [], "search_query": "бюджет"}

Respond with JSON only, no markdown:
```

### 4. Search Response Prompt

```
Based on this knowledge graph, answer the user's question.

CRITICAL - Understanding relations:
- SUPERSEDES means "replaces/updates". Item A → SUPERSEDES → B means A is NEWER, B is OUTDATED
- [DELETED] markers mean the target item was deleted. IGNORE deleted items in calculations
- CONTRADICTS means "cancels out" (e.g., refund cancels purchase). Subtract from totals
- Only use the LATEST version in any SUPERSEDES chain

Examples:
- "[DELETED] X" → SUPERSEDES → "bought X" = X was deleted, don't count it
- "Task [DONE]" → SUPERSEDES → "Task" = task is completed
- "Budget 60000" → SUPERSEDES → "Budget 50000" = current budget is 60000

CRITICAL - User Context:
- "Current user" shows WHO is asking the question
- "Project members" shows ALL people in the project
- When user asks "my tasks" / "мои задачи" - filter by CURRENT USER (assignee field)
- When user asks "Boris's tasks" / "задачи Бориса" - filter by that person
- When user asks "all tasks" / "все задачи" - show all tasks
- If user asks about a person not in the project - say they're not a member

Knowledge Graph:
%s

User Question: %s

Rules:
- Answer in the SAME language as the question
- Be concise (1-3 sentences)
- IGNORE items that have SUPERSEDES pointing TO them (they are outdated)
- If calculating totals, exclude deleted/superseded items
- Use user context to filter by person when appropriate
- If no relevant results, say so clearly
```

### 5. Action Response Prompt

```
Generate a brief, natural confirmation of these actions.

Actions taken:
%s

Original message: %s

Rules:
- Respond in the SAME language as the original message
- Be concise (1-2 sentences)
- Confirm what was saved/created
- Mention linked items if any
```

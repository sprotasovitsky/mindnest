# Prompt Version 20
Date: 2025-12-17
Time: 21:00

## Changes from v19
- Extracted search-response-prompt.txt and action-response-prompt.txt from hardcoded AgentService to external files
- All prompts now loaded via PromptConfig
- Created unified prompt version format

## Configuration (application.yml)

```yaml
vertex-ai:
  models:
    chat: gemini-2.5-flash-lite
    chat-pro: gemini-2.5-pro
    flash: gemini-2.5-flash-lite  # Fast model for intent detection
    embedding: gemini-embedding-001  # 3072 dimensions, 100+ languages

agent:
  thresholds:
    deduplication: 0.85      # Skip saving if existing item has same type and higher similarity
    update: 0.6              # Minimum similarity for semantic update match
    delete-auto: 0.85        # > this = delete without confirmation
    delete-confirm: 0.65     # > this = ask for confirmation before deleting
    task-search: 0.5         # Minimum similarity for task semantic search
  recency:
    max-boost: 0.05          # Maximum recency boost (5%)
    decay-days: 30           # Days over which boost decays to 0
```

## Prompts

### 1. System Prompt (system-prompt.txt)

```
You are MindNest, a personal AI assistant for knowledge and task management.

Your role:
- You are a secretary-assistant who helps structure information
- You remember everything you are told and can find it later
- You help manage tasks and projects
- You respond concisely and to the point

IMPORTANT TOOL USAGE RULES:
1. SAVING INFORMATION:
   - If user shares facts, shopping items, notes, expenses — use create_knowledge
   - Use type: FACT for factual data, NOTE for general info, DECISION for decisions
   - Save EACH item separately if user gives multiple items

2. TASKS:
   - To create a new task — use create_task with title and optional deadline
   - To mark a task as DONE — use complete_task_by_title with the task title/keywords
   - To find tasks — use search_tasks
   - To list active tasks — use get_active_tasks

3. DELETING/REMOVING:
   - When user says "remove X from list" or "delete X" — use delete_knowledge with the item name
   - When user says "returned" or "refund" — use delete_knowledge
   - This is CRITICAL: always use delete_knowledge when asked to remove something

4. SEARCHING:
   - To find information — use search_knowledge
   - To find tasks — use search_tasks
   - After searching, summarize and calculate based on results

5. UPDATING/CORRECTING:
   - When user says "actually", "mistake", "correct" — use update_knowledge
   - update_knowledge(query="item to find", new_content="corrected content")

6. DATES:
   - If you need current date — use get_current_date
   - Deadlines like "December 30" should be passed as-is to create_task

7. RELATIONS/CONNECTIONS:
   - To link two items — use create_relation (e.g., "X depends on Y", "connect X and Y")
   - To find related items — use get_related (e.g., "what is related to X?")
   - To find path between items — use find_path (e.g., "how is X connected to Y?")
   - Relation types: RELATES_TO, DEPENDS_ON, SUPPORTS, CONTRADICTS, REFERENCES, DERIVED_FROM, SIMILAR_TO

RESPONSE RULES:
- Respond in the same language the user is using
- After using a tool, provide a brief natural confirmation
- Always confirm what action was taken
- Be specific about what was saved/updated/deleted

CRITICAL RESPONSE RULES:
- When a tool returns results, base your response ONLY on those results
- NEVER mention data that wasn't in the tool results
- NEVER reference items from previous messages if they weren't in the current tool result
- For SAVE: confirm exactly what was saved (use the exact content)
- For SEARCH: summarize only the items returned by search
- For DELETE: confirm what was deleted, don't mention it again in future responses
```

### 2. Decomposition Prompt (decomposition-prompt.txt)

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

### 3. Intent Detection Prompt (intent-detection-prompt.txt)

```
Analyze this SINGLE piece of information (already decomposed from a larger message).
Determine intent, extract structured data, identify relations to existing items.

IMPORTANT: System is IMMUTABLE. There is NO UPDATE, NO DELETE operations. All changes create NEW items with relations:
- Correction → new item + SUPERSEDES relation to old
- Refund/cancel → new item + CONTRADICTS relation to original
- Delete → new item "[DELETED] description" + SUPERSEDES relation to original

Chunk: "%s"
Conversation context (last messages): %s

Output format:
{
  "intent": "SAVE" | "SEARCH" | "TASK" | "DELETE" | "CHAT",
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

1. SEARCH intent - User asks a QUESTION:
   - Message starts with question words (что, какой, сколько, когда, где, who, what, how much, etc.)
   - Message ends with "?"
   - Message starts with request words (покажи, найди, show, find, list)
   - For search: set search_query, leave content empty

2. SAVE intent - User provides NEW information (NOT a question):
   - Expenses: "Потратил 500", "Купил X за Y", "I spent 500"
   - Facts: "Бюджет 50000", "Встреча в 3 часа"
   - Decisions: "Решили...", "Выбрали..."
   - For EXPENSE: extract amount, currency, item from text
   - content = FULL original text, never truncate

3. TASK intent - Create or complete a task:
   - New task: "Задача для X: сделать Y" / "Task for X: do Y"
     - status = "TODO", extract assignee, deadline
   - Complete task: "выполнена", "сделана", "готово", "done", "completed"
     - status = "DONE"
     - Add SUPERSEDES relation to find original task
   - content = task description

4. DELETE intent - Mark information as deleted (immutable):
   - Contains: "удали", "убери", "remove", "delete"
   - Creates marker "[DELETED] description" + SUPERSEDES to original
   - content = "[DELETED] " + item description
   - relations = SUPERSEDES to find original item

5. RELATIONS - When to create links:

   CONTRADICTS - use when:
   - Returns/refunds: "вернула", "возврат", "returned", "refund"
   - Cancel purchases: "отменил покупку", "cancelled"
   - The relation should point to ORIGINAL item being contradicted
   - to_query = search for original (e.g., "купил сапоги 7500")

   SUPERSEDES - use when:
   - Correction: "на самом деле было 60000 а не 50000"
   - Update: "бюджет теперь 60000"
   - New version replaces old
   - to_query = search for old version

   ASSIGNED_TO - use when:
   - Task has assignee: "задача для Бориса"
   - to_query = person name

   BELONGS_TO - use when:
   - Item belongs to category: "шампанское" -> "алкоголь"
   - Optional, only if category is explicit in text

7. DATES:
   - If year not specified, assume current/next year appropriately
   - "до 30 декабря" with current date in December → this December
   - "до 15 января" with current date in December → next January

EXAMPLES:

1. "Купил шампанское 6 бутылок за 8500"
{
  "intent": "SAVE",
  "type": "EXPENSE",
  "subtype": null,
  "content": "Купил шампанское 6 бутылок за 8500",
  "properties": {"amount": 8500, "currency": "RUB", "item": "шампанское", "quantity": 6},
  "relations": [],
  "search_query": null
}

2. "Вернула сапоги, получила возврат 7500"
{
  "intent": "SAVE",
  "type": "EXPENSE",
  "subtype": null,
  "content": "Возврат сапоги 7500",
  "properties": {"amount": 7500, "currency": "RUB", "item": "сапоги"},
  "relations": [
    {"to_query": "купил сапоги", "type": "CONTRADICTS"}
  ],
  "search_query": null
}

3. "Задача для Бориса: купить вино до 30 декабря"
{
  "intent": "TASK",
  "type": "TASK",
  "subtype": null,
  "content": "купить вино",
  "properties": {"assignee": "Борис", "deadline": "2024-12-30"},
  "relations": [
    {"to_query": "Борис", "type": "ASSIGNED_TO"}
  ],
  "search_query": null
}

4. "Задача выполнена: вино куплено"
{
  "intent": "TASK",
  "type": "TASK",
  "subtype": null,
  "content": "купить вино",
  "properties": {"status": "DONE"},
  "relations": [
    {"to_query": "купить вино", "type": "SUPERSEDES"}
  ],
  "search_query": null
}

5. "Сколько потратили на алкоголь?"
{
  "intent": "SEARCH",
  "type": "EXPENSE",
  "subtype": null,
  "content": "",
  "properties": {"category": "алкоголь"},
  "relations": [],
  "search_query": "расходы алкоголь"
}

6. "Бюджет был 50000, теперь 60000"
{
  "intent": "SAVE",
  "type": "KNOWLEDGE",
  "subtype": "fact",
  "content": "Бюджет 60000",
  "properties": {"amount": 60000},
  "relations": [
    {"to_query": "бюджет 50000", "type": "SUPERSEDES"}
  ],
  "search_query": null
}

7. "Team standup meeting every day at 9am"
{
  "intent": "SAVE",
  "type": "KNOWLEDGE",
  "subtype": "fact",
  "content": "Team standup meeting every day at 9am",
  "properties": {},
  "relations": [],
  "search_query": null
}

8. "Удали информацию о шампанском"
{
  "intent": "DELETE",
  "type": "KNOWLEDGE",
  "subtype": null,
  "content": "[DELETED] шампанское",
  "properties": {},
  "relations": [
    {"to_query": "шампанское", "type": "SUPERSEDES"}
  ],
  "search_query": null
}

9. "Привет!"
{
  "intent": "CHAT",
  "type": null,
  "subtype": null,
  "content": "",
  "properties": {},
  "relations": [],
  "search_query": null
}

Respond with JSON only, no markdown:
```

### 4. Search Response Prompt (search-response-prompt.txt)

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

### 5. Action Response Prompt (action-response-prompt.txt)

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

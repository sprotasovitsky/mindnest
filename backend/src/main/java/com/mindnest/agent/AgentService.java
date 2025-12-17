package com.mindnest.agent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.*;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import com.mindnest.agent.IntentResult.Intent;
import com.mindnest.model.dto.ChatResponse;
import com.mindnest.model.entity.Conversation;
import com.mindnest.model.entity.Message;
import com.mindnest.service.ConversationService;
import com.mindnest.service.ModelRouter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class AgentService {

    private final VertexAI vertexAI;
    private final ModelRouter modelRouter;
    private final ToolExecutor toolExecutor;
    private final ConversationService conversationService;
    private final ObjectMapper objectMapper;

    @Value("${vertex-ai.models.chat}")
    private String chatModel;

    @Value("${vertex-ai.models.flash}")
    private String flashModel;

    private static final String SYSTEM_PROMPT = """
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
            """;

    // Prompt for intent detection (Step 1)
    // Supports both English and Russian keywords
    private static final String INTENT_DETECTION_PROMPT = """
            Analyze the user's message and determine their intent. Return JSON with:
            - intent: one of SAVE, SEARCH, UPDATE, DELETE, TASK, COMPLETE, CHAT
            - tool: which tool to call (or null for CHAT)
            - content: the main content to save/search/update/delete (extracted from message)
            - knowledgeType: for SAVE intent, one of FACT, NOTE, DECISION
            - tasks: for TASK intent, array of task objects with {title, deadline, assignee}

            INTENT RULES (check in this EXACT order - first match wins):

            1. TASK - User explicitly creates task(s):
            - Keywords EN: "create task", "task for", "add task", "assign task"
            - Keywords RU: "создай задачу", "добавь задачу", "задача для", "назначь"
            - Pattern: "Create task for X: do Y" / "Задача для X: сделать Y"
            Tool: create_task
            Extract each task with title, assignee, deadline

            2. COMPLETE - User marks a task as done:
            - Keywords EN: "mark as done", "completed task", "task is done", "task complete"
            - Keywords RU: "выполнена", "сделана", "готово", "завершена", "закончил", "сделал"
            - Pattern: "X task is done" / "Задача X выполнена"
            Tool: complete_task_by_title

            3. DELETE - User wants to remove information:
            - Keywords EN: "remove", "delete", "cancel", "returned", "refund"
            - Keywords RU: "удали", "убери", "отмени", "верни", "удалить"
            - Example: "Remove boots from the list" / "Удали информацию про заправку"
            Tool: delete_knowledge
            IMPORTANT: Extract the search query for what to delete in "content" field

            4. UPDATE - User corrects/changes existing information:
            - Keywords EN: "actually", "mistake", "correct", "change", "update", "was wrong", "not X but Y", "instead of"
            - Keywords RU: "на самом деле", "ошибка", "исправь", "измени", "обнови", "не X а Y", "вместо", "было неправильно", "поменяй"
            - Patterns:
              * "Actually it was 4200, not 4500" → query: "4500", new: "4200"
              * "Change budget to 50000" → query: "budget", new: "budget 50000"
              * "На самом деле потратили 3000, а не 2500" → query: "2500", new: "3000"
              * "Измени бюджет на 40000" → query: "бюджет", new: "бюджет 40000"
            Tool: update_knowledge
            IMPORTANT: Extract update_query (what to find) and update_new_content (replacement) separately!

            5. SEARCH - User asks a QUESTION or wants to find/retrieve info:
            *** CRITICAL RULE - CHECK THIS FIRST: ***
            If message STARTS with any of these words (case insensitive), it is ALWAYS SEARCH:
            - "что " (what) - e.g. "Что мы покупали?" = SEARCH
            - "какой" / "какие" / "какая" (which) - e.g. "Какие задачи?" = SEARCH
            - "сколько" (how much/many) - e.g. "Сколько потратили?" = SEARCH
            - "когда" (when) - e.g. "Когда встреча?" = SEARCH
            - "где" (where) - e.g. "Где информация?" = SEARCH
            - "кто" (who) - e.g. "Кто назначен?" = SEARCH
            - "почему" / "зачем" (why) - e.g. "Почему так?" = SEARCH
            - "как" (how) - e.g. "Как сделать?" = SEARCH
            - "чё" / "че" (informal what) - e.g. "чё там?" = SEARCH
            - "what" / "when" / "where" / "which" / "who" / "why" / "how"

            If message ENDS with "?" it is SEARCH (even if it contains action words like "покупали", "купили").

            *** EXAMPLES - ALWAYS SEARCH (even if they mention purchases/expenses): ***
            - "Что мы покупали в этом месяце?" → SEARCH (starts with "что", ends with "?")
            - "Что купили?" → SEARCH (starts with "что")
            - "Какие у меня задачи?" → SEARCH (starts with "какие")
            - "чё там по бюджету?" → SEARCH (starts with "чё")
            - "Сколько потратили?" → SEARCH (starts with "сколько")
            - "How much did we spend?" → SEARCH (starts with "how")

            Additional search triggers:
            - Requests EN: "show me", "list all", "find", "search", "tell me about"
            - Requests RU: "покажи", "найди", "выведи", "подскажи", "расскажи"
            Tool: search_knowledge

            6. SAVE - User provides NEW factual information to store (NOT questions!):
            - ONLY if NOT a question (no "?" at end, no question words at start)
            - NEVER save if message starts with: что, какой, какие, сколько, когда, где, кто, как, чё, че
            - NEVER save if message ends with "?"
            - Expenses: "I spent 500" / "Потратил 500", "Купил X за Y"
            - Facts: "Budget is..." / "Бюджет...", "Встреча в..."
            - Decisions: "We decided..." / "Решили...", "Выбрали..."
            Tool: create_knowledge

            7. RELATION - User wants to link/connect items:
            - Keywords EN: "connect", "link", "relates to", "depends on", "related to"
            - Keywords RU: "связь", "связать", "связано с", "зависит от", "относится к"
            - Pattern: "X depends on Y" / "Задача X зависит от Y"
            Tool: create_relation

            8. CHAT - General conversation:
            - "Hello", "Thanks" / "Привет", "Спасибо", "Что ты умеешь?"
            Tool: null

            User message: "%s"

            Respond with JSON only, no markdown:
            {"intent":"...", "tool":"...", "content":"...", "knowledgeType":"...", "tasks":[{"title":"...","deadline":"...","assignee":"..."}], "update_query":"...", "update_new_content":"..."}
            """;

    public ChatResponse processMessage(String message, String projectId, String userId) {
        log.info("Processing message for project: {}, user: {}", projectId, userId);

        try {
            // Get or create conversation
            UUID userUuid = UUID.fromString(userId);
            UUID projectUuid = UUID.fromString(projectId);
            Conversation conversation = conversationService.getOrCreateConversation(userUuid, projectUuid);

            // Save user message
            conversationService.addMessage(conversation.getId(), Message.Role.user, message, null);

            // Clear sources before processing
            toolExecutor.clearSources();

            // STEP 1: Detect intent using fast model
            IntentResult intentResult = detectIntent(message);
            log.info("Detected intent: {} -> tool: {}", intentResult.intent(), intentResult.toolToCall());

            // STEP 2: Force tool execution based on detected intent
            String toolResult = null;
            if (intentResult.requiresToolCall() && intentResult.toolToCall() != null) {
                toolResult = executeIntentBasedTool(intentResult, message, projectId, userId);
                log.info("Tool execution result: {}", toolResult);
            }

            // STEP 3: Generate response using main model
            GenerativeModel model = buildModelWithTools();
            List<Content> contents = buildConversationContents(conversation.getId(), message);

            // If tool was executed, add context about what was done
            String enhancedMessage = message;
            if (toolResult != null) {
                enhancedMessage = message + "\n\n[System: Tool '" + intentResult.toolToCall() +
                    "' was already executed with result: " + toolResult +
                    ". Confirm this action to the user in a natural way.]";
                // Replace last content with enhanced message
                contents.set(contents.size() - 1, Content.newBuilder()
                    .setRole("user")
                    .addParts(Part.newBuilder().setText(
                        SYSTEM_PROMPT + "\n\nUser request: " + enhancedMessage).build())
                    .build());
            }

            // Generate response (may include additional function calls)
            GenerateContentResponse response = model.generateContent(contents);

            // Process response - handle any additional function calls
            String finalResponse = processResponse(response, projectId, userId, model, contents);

            // Get sources collected during tool execution
            List<String> sources = toolExecutor.getSources();

            // Calculate confidence
            double confidence = calculateConfidence(finalResponse);

            // Save assistant response
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("confidence", confidence);
            if (!sources.isEmpty()) {
                metadata.put("sources", sources);
            }
            conversationService.addMessage(conversation.getId(), Message.Role.assistant, finalResponse, metadata);

            return ChatResponse.builder()
                    .reply(finalResponse)
                    .sources(sources)
                    .confidence(confidence)
                    .conversationId(conversation.getId().toString())
                    .build();

        } catch (Exception e) {
            log.error("Error processing message: ", e);
            return ChatResponse.builder()
                    .reply("Sorry, an error occurred while processing your request. Please try again.")
                    .sources(List.of())
                    .confidence(0.0)
                    .build();
        }
    }

    private List<Content> buildConversationContents(UUID conversationId, String currentMessage) {
        List<Content> contents = new ArrayList<>();

        // Get recent messages for context (excluding the one we just added)
        List<Message> history = conversationService.getContextMessages(conversationId);

        // Add system prompt as first user message
        boolean isFirstUserMessage = true;

        for (Message msg : history) {
            // Skip the current message as it's already being processed
            if (msg.getContent().equals(currentMessage) && msg.getRole() == Message.Role.user) {
                continue;
            }

            String role = msg.getRole() == Message.Role.user ? "user" : "model";
            String content = msg.getContent();

            // Embed system prompt in first user message
            if (isFirstUserMessage && msg.getRole() == Message.Role.user) {
                content = SYSTEM_PROMPT + "\n\nUser request: " + content;
                isFirstUserMessage = false;
            }

            contents.add(Content.newBuilder()
                    .setRole(role)
                    .addParts(Part.newBuilder().setText(content).build())
                    .build());
        }

        // Add current message with system prompt if no history
        String currentContent = currentMessage;
        if (isFirstUserMessage || contents.isEmpty()) {
            currentContent = SYSTEM_PROMPT + "\n\nUser request: " + currentMessage;
        }

        contents.add(Content.newBuilder()
                .setRole("user")
                .addParts(Part.newBuilder().setText(currentContent).build())
                .build());

        return contents;
    }

    private GenerativeModel buildModelWithTools() throws IOException {
        // Define available tools
        Tool tools = Tool.newBuilder()
                .addFunctionDeclarations(buildCreateKnowledgeFunction())
                .addFunctionDeclarations(buildSearchKnowledgeFunction())
                .addFunctionDeclarations(buildUpdateKnowledgeFunction())
                .addFunctionDeclarations(buildDeleteKnowledgeFunction())
                .addFunctionDeclarations(buildPreviewDeleteFunction())
                .addFunctionDeclarations(buildConfirmDeleteFunction())
                .addFunctionDeclarations(buildCreateTaskFunction())
                .addFunctionDeclarations(buildGetTasksForTodayFunction())
                .addFunctionDeclarations(buildGetActiveTasksFunction())
                .addFunctionDeclarations(buildUpdateTaskStatusFunction())
                .addFunctionDeclarations(buildCompleteTaskByTitleFunction())
                .addFunctionDeclarations(buildSearchTasksFunction())
                .addFunctionDeclarations(buildDecomposeTaskFunction())
                .addFunctionDeclarations(buildCreateProjectFunction())
                .addFunctionDeclarations(buildListProjectsFunction())
                .addFunctionDeclarations(buildGetCurrentDateFunction())
                .addFunctionDeclarations(buildCreateRelationFunction())
                .addFunctionDeclarations(buildGetRelatedFunction())
                .addFunctionDeclarations(buildFindPathFunction())
                .build();

        return new GenerativeModel.Builder()
                .setModelName(chatModel)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(2048)
                        .setTemperature(0.7f)
                        .build())
                .setTools(List.of(tools))
                .build();
    }

    private String processResponse(GenerateContentResponse response, String projectId, String userId,
                                   GenerativeModel model, List<Content> contents) throws IOException {
        Content responseContent = response.getCandidates(0).getContent();

        // Check if there are function calls
        List<FunctionCall> functionCalls = new ArrayList<>();
        StringBuilder textResponse = new StringBuilder();

        for (Part part : responseContent.getPartsList()) {
            if (part.hasFunctionCall()) {
                functionCalls.add(part.getFunctionCall());
            }
            if (part.hasText()) {
                textResponse.append(part.getText());
            }
        }

        // Log what the model returned
        log.info("Model response: functionCalls={}, textLength={}",
                functionCalls.size(), textResponse.length());
        if (functionCalls.isEmpty() && textResponse.length() > 0) {
            log.warn("NO FUNCTION CALL - Model returned text only: {}",
                    textResponse.substring(0, Math.min(200, textResponse.length())));
        }

        // If there are function calls, execute them
        if (!functionCalls.isEmpty()) {
            List<Part> functionResponses = new ArrayList<>();

            for (FunctionCall functionCall : functionCalls) {
                String functionName = functionCall.getName();
                Map<String, Object> args = protoToMap(functionCall.getArgs());

                log.info("Executing function: {} with args: {}", functionName, args);

                // Execute the tool
                String result = toolExecutor.execute(functionName, args, projectId, userId);

                log.info("Function {} result: {}", functionName, result);

                // Build function response
                functionResponses.add(Part.newBuilder()
                        .setFunctionResponse(FunctionResponse.newBuilder()
                                .setName(functionName)
                                .setResponse(com.google.protobuf.Struct.newBuilder()
                                        .putFields("result", com.google.protobuf.Value.newBuilder()
                                                .setStringValue(result)
                                                .build())
                                        .build())
                                .build())
                        .build());
            }

            // Add model response and function results to conversation
            contents.add(responseContent);
            contents.add(Content.newBuilder()
                    .setRole("function")
                    .addAllParts(functionResponses)
                    .build());

            // Get final response after function execution
            GenerateContentResponse finalResponse = model.generateContent(contents);
            String finalText = ResponseHandler.getText(finalResponse);

            // Fallback if response is empty
            if (finalText == null || finalText.isBlank()) {
                // Build response from function results
                StringBuilder fallbackResponse = new StringBuilder();
                for (Part part : functionResponses) {
                    if (part.hasFunctionResponse()) {
                        String result = part.getFunctionResponse().getResponse()
                                .getFieldsMap().get("result").getStringValue();
                        if (result != null && !result.isBlank()) {
                            fallbackResponse.append(result).append("\n");
                        }
                    }
                }
                return fallbackResponse.length() > 0
                        ? fallbackResponse.toString().trim()
                        : "Done.";
            }
            return finalText;
        }

        return textResponse.toString().isBlank() ? "I understand." : textResponse.toString();
    }

    private Map<String, Object> protoToMap(com.google.protobuf.Struct struct) {
        Map<String, Object> result = new HashMap<>();
        struct.getFieldsMap().forEach((key, value) -> {
            result.put(key, protoValueToObject(value));
        });
        return result;
    }

    private Object protoValueToObject(com.google.protobuf.Value value) {
        return switch (value.getKindCase()) {
            case STRING_VALUE -> value.getStringValue();
            case NUMBER_VALUE -> value.getNumberValue();
            case BOOL_VALUE -> value.getBoolValue();
            case NULL_VALUE -> null;
            case STRUCT_VALUE -> protoToMap(value.getStructValue());
            case LIST_VALUE -> value.getListValue().getValuesList().stream()
                    .map(this::protoValueToObject)
                    .toList();
            default -> value.toString();
        };
    }

    // Function declarations

    private FunctionDeclaration buildCreateKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_knowledge")
                .setDescription("Save a piece of information, fact, decision, or note to the knowledge base")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("content", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("The content to save")
                                .build())
                        .putProperties("type", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Type of knowledge: FACT, DECISION, NOTE, or QUESTION")
                                .build())
                        .addRequired("content")
                        .build())
                .build();
    }

    private FunctionDeclaration buildSearchKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("search_knowledge")
                .setDescription("Search the knowledge base for relevant information")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query")
                                .build())
                        .putProperties("limit", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("Maximum number of results (default 5)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildUpdateKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("update_knowledge")
                .setDescription("Update/correct an existing item in the knowledge base. Use when user says 'actually it was X not Y' or 'correct the amount'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the item to update (e.g. 'Auchan', 'groceries')")
                                .build())
                        .putProperties("new_content", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("The corrected/updated content")
                                .build())
                        .addRequired("query")
                        .addRequired("new_content")
                        .build())
                .build();
    }

    private FunctionDeclaration buildDeleteKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("delete_knowledge")
                .setDescription("Delete/remove an item from the knowledge base by searching for it. Use when user says 'remove X from the list' or 'delete X'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the item to delete (e.g. 'Christmas tree', 'champagne')")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildPreviewDeleteFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("preview_delete")
                .setDescription("Preview items that would be deleted without actually deleting them. Shows matching items and their IDs for confirmation. Use this FIRST when user wants to delete something, then use confirm_delete.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find items to delete")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildConfirmDeleteFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("confirm_delete")
                .setDescription("Confirm deletion of items by their IDs. Use after preview_delete when user confirms they want to delete the shown items.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("ids", Schema.newBuilder()
                                .setType(Type.ARRAY)
                                .setItems(Schema.newBuilder().setType(Type.STRING).build())
                                .setDescription("List of item IDs to delete")
                                .build())
                        .addRequired("ids")
                        .build())
                .build();
    }

    private FunctionDeclaration buildCreateTaskFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_task")
                .setDescription("Create a new task with optional deadline and assignee")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("title", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task title")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task description (optional)")
                                .build())
                        .putProperties("deadline", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Deadline: 'today', 'tomorrow', 'friday', or date like '2024-12-20'")
                                .build())
                        .putProperties("assignee", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Person assigned to the task (name)")
                                .build())
                        .addRequired("title")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetTasksForTodayFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_tasks_for_today")
                .setDescription("Get all tasks due today")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetActiveTasksFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_active_tasks")
                .setDescription("Get all active (TODO or IN_PROGRESS) tasks")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildUpdateTaskStatusFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("update_task_status")
                .setDescription("Update the status of a task")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("task_id", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("ID of the task to update")
                                .build())
                        .putProperties("status", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("New status: TODO, IN_PROGRESS, DONE, BLOCKED, or CANCELLED")
                                .build())
                        .addRequired("task_id")
                        .addRequired("status")
                        .build())
                .build();
    }

    private FunctionDeclaration buildCompleteTaskByTitleFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("complete_task_by_title")
                .setDescription("Mark a task as completed by searching for it by title or description. Use this when user says 'mark task X as done' or 'completed task X'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("title", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task title or keywords to find the task (e.g. 'buy alcohol', 'shopping')")
                                .build())
                        .addRequired("title")
                        .build())
                .build();
    }

    private FunctionDeclaration buildSearchTasksFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("search_tasks")
                .setDescription("Search tasks by content")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query")
                                .build())
                        .putProperties("limit", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("Maximum results (default 5)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildDecomposeTaskFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("decompose_task")
                .setDescription("Break down a task into smaller subtasks")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("task_id", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("ID of the parent task to decompose")
                                .build())
                        .putProperties("subtasks", Schema.newBuilder()
                                .setType(Type.ARRAY)
                                .setItems(Schema.newBuilder()
                                        .setType(Type.STRING)
                                        .build())
                                .setDescription("List of subtask titles")
                                .build())
                        .addRequired("task_id")
                        .addRequired("subtasks")
                        .build())
                .build();
    }

    private FunctionDeclaration buildCreateProjectFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_project")
                .setDescription("Create a new project")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("name", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Project name")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Project description (optional)")
                                .build())
                        .addRequired("name")
                        .build())
                .build();
    }

    private FunctionDeclaration buildListProjectsFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("list_projects")
                .setDescription("List all user's projects")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetCurrentDateFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_current_date")
                .setDescription("Get the current date")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildCreateRelationFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_relation")
                .setDescription("Create a relation/link between two knowledge items. Use when user says 'X is related to Y', 'X depends on Y', 'connect X and Y'. Relation types: RELATES_TO (general), DEPENDS_ON (dependency), SUPPORTS (evidence), CONTRADICTS (conflict), REFERENCES, DERIVED_FROM, SIMILAR_TO")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("source_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the SOURCE item (the item that has the relation)")
                                .build())
                        .putProperties("target_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the TARGET item (the item being related to)")
                                .build())
                        .putProperties("relation_type", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Type of relation: RELATES_TO, DEPENDS_ON, SUPPORTS, CONTRADICTS, REFERENCES, DERIVED_FROM, SIMILAR_TO")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Optional description of the relation")
                                .build())
                        .addRequired("source_query")
                        .addRequired("target_query")
                        .addRequired("relation_type")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetRelatedFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_related")
                .setDescription("Get all items related to a knowledge item. Use when user asks 'what is related to X', 'show connections for X', 'what depends on X'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the item")
                                .build())
                        .putProperties("depth", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("How many levels of relations to traverse (default 1, max 3)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildFindPathFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("find_path")
                .setDescription("Find the path/connection between two knowledge items. Use when user asks 'how is X connected to Y', 'what's the relation between X and Y'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("source_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the first item")
                                .build())
                        .putProperties("target_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the second item")
                                .build())
                        .addRequired("source_query")
                        .addRequired("target_query")
                        .build())
                .build();
    }

    private double calculateConfidence(String response) {
        double base = 0.85;

        if (response.contains("not sure") || response.contains("maybe") ||
                response.contains("perhaps") || response.contains("possibly")) {
            base -= 0.1;
        }

        if (response.contains("don't know") || response.contains("I'm not certain") ||
                response.contains("cannot answer") || response.contains("no results")) {
            base -= 0.2;
        }

        return Math.max(0.1, Math.min(1.0, base));
    }

    /**
     * Pre-check for question patterns that MUST be SEARCH intent.
     * This is a failsafe to ensure questions are never misclassified as SAVE.
     * Returns IntentResult for SEARCH if pattern matches, null otherwise.
     */
    private IntentResult checkForceSearchPattern(String message) {
        if (message == null || message.isBlank()) {
            return null;
        }

        String lowerMessage = message.toLowerCase().trim();

        // Skip task-related questions - let LLM handle them to use correct tool
        if (lowerMessage.contains("задач") || lowerMessage.contains("task")) {
            log.debug("Task-related question, letting LLM decide tool");
            return null;
        }

        // Determine which tool to use based on context
        String tool = "search_knowledge";

        // Russian question word prefixes (with space to avoid matching word parts)
        String[] russianQuestionStarts = {
            "что ", "какой ", "какие ", "какая ", "каков ", "какое ",
            "сколько ", "когда ", "где ", "кто ", "почему ", "зачем ",
            "как ", "чё ", "че ", "чего "
        };

        // English question word prefixes
        String[] englishQuestionStarts = {
            "what ", "which ", "when ", "where ", "who ", "why ", "how "
        };

        // Check Russian question starts
        for (String prefix : russianQuestionStarts) {
            if (lowerMessage.startsWith(prefix)) {
                log.debug("Matched Russian question pattern: '{}'", prefix);
                return new IntentResult(
                    Intent.SEARCH,
                    tool,
                    List.of(),
                    message,  // Use the message as search query
                    List.of(),
                    null,
                    null
                );
            }
        }

        // Check English question starts
        for (String prefix : englishQuestionStarts) {
            if (lowerMessage.startsWith(prefix)) {
                log.debug("Matched English question pattern: '{}'", prefix);
                return new IntentResult(
                    Intent.SEARCH,
                    tool,
                    List.of(),
                    message,
                    List.of(),
                    null,
                    null
                );
            }
        }

        // Check if message ends with "?" (question mark)
        if (message.trim().endsWith("?")) {
            log.debug("Matched question mark pattern");
            return new IntentResult(
                Intent.SEARCH,
                tool,
                List.of(),
                message,
                List.of(),
                null,
                null
            );
        }

        // Russian request words (also should be SEARCH)
        String[] russianRequestStarts = {
            "покажи ", "найди ", "выведи ", "подскажи ", "расскажи "
        };
        for (String prefix : russianRequestStarts) {
            if (lowerMessage.startsWith(prefix)) {
                log.debug("Matched Russian request pattern: '{}'", prefix);
                return new IntentResult(
                    Intent.SEARCH,
                    tool,
                    List.of(),
                    message,
                    List.of(),
                    null,
                    null
                );
            }
        }

        return null;  // No forced pattern matched, let LLM decide
    }

    /**
     * Step 1: Detect user intent using fast model with structured output
     */
    private IntentResult detectIntent(String message) {
        // FAILSAFE: Pre-check for Russian question patterns that must ALWAYS be SEARCH
        // This ensures questions are never misclassified as SAVE
        IntentResult forcedSearch = checkForceSearchPattern(message);
        if (forcedSearch != null) {
            log.info("Force-detected SEARCH pattern: {}", message);
            return forcedSearch;
        }

        try {
            GenerativeModel intentModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)  // Increased for multi-task JSON responses
                            .setTemperature(0.1f)  // Low temperature for consistent classification
                            .build())
                    .build();

            String prompt = INTENT_DETECTION_PROMPT.formatted(message);
            GenerateContentResponse response = intentModel.generateContent(prompt);
            String jsonResponse = ResponseHandler.getText(response);

            log.debug("Intent detection raw response: {}", jsonResponse);

            // Parse JSON response
            return parseIntentResponse(jsonResponse, message);

        } catch (Exception e) {
            log.error("Intent detection failed, defaulting to CHAT: {}", e.getMessage());
            return IntentResult.chat();
        }
    }

    /**
     * Parse the JSON response from intent detection
     */
    private IntentResult parseIntentResponse(String jsonResponse, String originalMessage) {
        try {
            // Clean up response (remove markdown if present)
            String cleaned = jsonResponse.trim();
            if (cleaned.startsWith("```json")) {
                cleaned = cleaned.substring(7);
            }
            if (cleaned.startsWith("```")) {
                cleaned = cleaned.substring(3);
            }
            if (cleaned.endsWith("```")) {
                cleaned = cleaned.substring(0, cleaned.length() - 3);
            }
            cleaned = cleaned.trim();

            JsonNode json = objectMapper.readTree(cleaned);

            String intentStr = json.has("intent") ? json.get("intent").asText("CHAT") : "CHAT";
            String tool = json.has("tool") && !json.get("tool").isNull() ? json.get("tool").asText() : null;
            String content = json.has("content") && !json.get("content").isNull()
                    ? json.get("content").asText()
                    : originalMessage;
            String knowledgeType = json.has("knowledgeType") && !json.get("knowledgeType").isNull()
                    ? json.get("knowledgeType").asText()
                    : "NOTE";

            Intent intent;
            try {
                intent = Intent.valueOf(intentStr.toUpperCase());
            } catch (IllegalArgumentException e) {
                log.warn("Unknown intent: {}, defaulting to CHAT", intentStr);
                intent = Intent.CHAT;
            }

            // Parse tasks if present
            List<IntentResult.TaskInfo> tasks = new ArrayList<>();
            if (json.has("tasks") && json.get("tasks").isArray()) {
                for (JsonNode taskNode : json.get("tasks")) {
                    String title = taskNode.has("title") ? taskNode.get("title").asText() : null;
                    String deadline = taskNode.has("deadline") && !taskNode.get("deadline").isNull()
                            ? taskNode.get("deadline").asText() : null;
                    String assignee = taskNode.has("assignee") && !taskNode.get("assignee").isNull()
                            ? taskNode.get("assignee").asText() : null;
                    if (title != null && !title.isBlank()) {
                        tasks.add(new IntentResult.TaskInfo(title, deadline, assignee));
                    }
                }
            }

            // Build content to save based on knowledge type
            String contentToSave = content;
            if (intent == Intent.SAVE && knowledgeType != null) {
                contentToSave = content; // Could enhance with type prefix if needed
            }

            // Parse update fields for UPDATE intent
            String updateQuery = json.has("update_query") && !json.get("update_query").isNull()
                    ? json.get("update_query").asText() : null;
            String updateNewContent = json.has("update_new_content") && !json.get("update_new_content").isNull()
                    ? json.get("update_new_content").asText() : null;

            return new IntentResult(intent, tool, List.of(), contentToSave, tasks, updateQuery, updateNewContent);

        } catch (Exception e) {
            log.error("Failed to parse intent JSON: {}, response was: {}", e.getMessage(), jsonResponse);
            return IntentResult.chat();
        }
    }

    /**
     * Step 2: Execute tool based on detected intent
     */
    private String executeIntentBasedTool(IntentResult intent, String originalMessage,
                                          String projectId, String userId) {
        String tool = intent.toolToCall();
        String content = intent.contentToSave() != null ? intent.contentToSave() : originalMessage;

        log.info("Executing intent-based tool: {} with content: {}", tool, truncate(content, 100));

        return switch (tool) {
            case "create_knowledge" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("content", content);
                args.put("type", determineKnowledgeType(content));
                yield toolExecutor.execute("create_knowledge", args, projectId, userId);
            }
            case "search_knowledge" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("query", content);
                args.put("limit", 10);
                yield toolExecutor.execute("search_knowledge", args, projectId, userId);
            }
            case "update_knowledge" -> {
                // For update, use parsed update_query and update_new_content if available
                Map<String, Object> args = new HashMap<>();
                String query = intent.updateQuery() != null ? intent.updateQuery() : extractUpdateQuery(content);
                String newContent = intent.updateNewContent() != null ? intent.updateNewContent() : content;
                args.put("query", query);
                args.put("new_content", newContent);
                log.info("UPDATE: query='{}', new_content='{}'", query, truncate(newContent, 50));
                yield toolExecutor.execute("update_knowledge", args, projectId, userId);
            }
            case "delete_knowledge" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("query", content);
                yield toolExecutor.execute("delete_knowledge", args, projectId, userId);
            }
            case "create_task" -> {
                // Handle multiple tasks
                List<IntentResult.TaskInfo> tasks = intent.tasks();
                if (tasks != null && !tasks.isEmpty()) {
                    StringBuilder results = new StringBuilder();
                    for (IntentResult.TaskInfo task : tasks) {
                        Map<String, Object> args = new HashMap<>();
                        args.put("title", task.title());
                        if (task.deadline() != null) {
                            args.put("deadline", task.deadline());
                        }
                        if (task.assignee() != null) {
                            args.put("assignee", task.assignee());
                        }
                        String result = toolExecutor.execute("create_task", args, projectId, userId);
                        results.append(result).append("\n");
                    }
                    yield results.toString().trim();
                } else {
                    // Single task from content
                    Map<String, Object> args = new HashMap<>();
                    args.put("title", content);
                    yield toolExecutor.execute("create_task", args, projectId, userId);
                }
            }
            case "complete_task_by_title" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("title", content);
                yield toolExecutor.execute("complete_task_by_title", args, projectId, userId);
            }
            case "create_relation" -> {
                // For relations, we let the main model handle it since it needs to parse source/target
                // The model will call create_relation with proper arguments
                yield null;
            }
            default -> {
                log.warn("Unknown tool for intent: {}", tool);
                yield null;
            }
        };
    }

    /**
     * Determine knowledge type based on content
     */
    private String determineKnowledgeType(String content) {
        String lower = content.toLowerCase();

        // Check for expense/money patterns
        if (lower.contains("rubles") || lower.contains("rub") || lower.contains("₽") ||
            lower.contains("spent") || lower.contains("bought") || lower.contains("paid") ||
            lower.contains("cost") || lower.contains("price")) {
            return "FACT";
        }

        // Check for decision patterns
        if (lower.contains("decided") || lower.contains("decision") || lower.contains("choose") ||
            lower.contains("go with") || lower.contains("let's")) {
            return "DECISION";
        }

        // Default to NOTE for general information
        return "NOTE";
    }

    /**
     * Extract query for update operation (find the thing being updated)
     */
    private String extractUpdateQuery(String content) {
        // Simple heuristic: look for keywords and extract the subject
        String lower = content.toLowerCase();

        // English patterns
        if (lower.contains(" was ")) {
            int idx = lower.indexOf(" was ");
            return content.substring(0, idx).trim();
        }
        if (lower.contains("change ")) {
            int start = lower.indexOf("change ") + 7;
            int end = lower.indexOf(" to ", start);
            if (end > start) {
                return content.substring(start, end).trim();
            }
        }
        if (lower.contains("update ")) {
            int start = lower.indexOf("update ") + 7;
            int end = lower.indexOf(" to ", start);
            if (end > start) {
                return content.substring(start, end).trim();
            }
        }

        // Russian patterns
        // "измени X на Y" / "поменяй X на Y"
        if (lower.contains("измени ") || lower.contains("поменяй ")) {
            int start = Math.max(lower.indexOf("измени "), lower.indexOf("поменяй "));
            start = start + (lower.charAt(start) == 'и' ? 7 : 8); // "измени " or "поменяй "
            int end = lower.indexOf(" на ", start);
            if (end > start) {
                return content.substring(start, end).trim();
            }
        }
        // "не X а Y" / "не X, а Y"
        if (lower.contains(" не ") && (lower.contains(" а ") || lower.contains(", а "))) {
            int start = lower.indexOf(" не ") + 4;
            int end = lower.indexOf(" а ", start);
            if (end < 0) end = lower.indexOf(", а ", start);
            if (end > start) {
                return content.substring(start, end).trim();
            }
        }
        // "вместо X теперь Y"
        if (lower.contains("вместо ")) {
            int start = lower.indexOf("вместо ") + 7;
            int end = lower.indexOf(" теперь", start);
            if (end < 0) end = lower.indexOf(" сейчас", start);
            if (end > start) {
                return content.substring(start, end).trim();
            }
        }

        // Fallback: return first few words as query
        String[] words = content.split("\\s+");
        return String.join(" ", Arrays.copyOf(words, Math.min(3, words.length)));
    }

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }
}

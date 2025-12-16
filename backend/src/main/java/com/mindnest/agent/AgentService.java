package com.mindnest.agent;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.*;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
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

    @Value("${vertex-ai.models.chat}")
    private String chatModel;

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

            2. TASKS:
               - To create a new task — use create_task with title and optional deadline
               - To mark a task as DONE — use complete_task_by_title with the task title/keywords
               - To find tasks — use search_tasks
               - To list active tasks — use get_active_tasks

            3. DELETING/REMOVING:
               - When user says "remove X from list" or "delete X" — use delete_knowledge with the item name
               - This is CRITICAL: always use delete_knowledge when asked to remove something

            4. SEARCHING:
               - To find information — use search_knowledge
               - To find tasks — use search_tasks

            5. DATES:
               - If you need current date — use get_current_date
               - Deadlines like "December 30" should be passed as-is to create_task

            RESPONSE RULES:
            - Respond in the same language the user is using
            - After using a tool, provide a brief natural confirmation
            - Always confirm what action was taken
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

            // Build the model with tools
            GenerativeModel model = buildModelWithTools();

            // Build conversation history for context
            List<Content> contents = buildConversationContents(conversation.getId(), message);

            // Generate response (may include function calls)
            GenerateContentResponse response = model.generateContent(contents);

            // Process response - handle function calls if present
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
                .addFunctionDeclarations(buildDeleteKnowledgeFunction())
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

    private FunctionDeclaration buildCreateTaskFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_task")
                .setDescription("Create a new task with optional deadline")
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
}

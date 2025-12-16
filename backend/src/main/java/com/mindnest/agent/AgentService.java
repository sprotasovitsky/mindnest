package com.mindnest.agent;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.*;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import com.mindnest.model.dto.ChatResponse;
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

    @Value("${vertex-ai.models.chat}")
    private String chatModel;

    private static final String SYSTEM_PROMPT = """
            You are MindNest, a personal AI assistant for knowledge and task management.

            Your role:
            - You are a secretary-assistant who helps structure information
            - You remember everything you are told and can find it later
            - You help manage tasks and projects
            - You respond concisely and to the point

            Rules:
            - If user shares a fact or information — use create_knowledge to save it
            - If user asks to create a task — use create_task
            - If user asks about their tasks — use get_tasks_for_today or get_active_tasks
            - If user asks to find something — use search_knowledge or search_tasks
            - If you need the current date — use get_current_date
            - Always use the appropriate tool for the user's request
            - Respond in the same language the user is using
            - After using a tool, summarize the result naturally for the user
            """;

    public ChatResponse processMessage(String message, String projectId, String userId) {
        log.info("Processing message for project: {}, user: {}", projectId, userId);

        try {
            // Build the model with tools
            GenerativeModel model = buildModelWithTools();

            // Create content with system instruction embedded in first message
            List<Content> contents = new ArrayList<>();
            String promptWithSystem = SYSTEM_PROMPT + "\n\nUser request: " + message;
            contents.add(Content.newBuilder()
                    .setRole("user")
                    .addParts(Part.newBuilder().setText(promptWithSystem).build())
                    .build());

            // Generate response (may include function calls)
            GenerateContentResponse response = model.generateContent(contents);

            // Process response - handle function calls if present
            String finalResponse = processResponse(response, projectId, userId, model, contents);

            // Calculate confidence
            double confidence = calculateConfidence(finalResponse);

            return ChatResponse.builder()
                    .reply(finalResponse)
                    .sources(List.of())
                    .confidence(confidence)
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

    private GenerativeModel buildModelWithTools() throws IOException {
        // Define available tools
        Tool tools = Tool.newBuilder()
                .addFunctionDeclarations(buildCreateKnowledgeFunction())
                .addFunctionDeclarations(buildSearchKnowledgeFunction())
                .addFunctionDeclarations(buildCreateTaskFunction())
                .addFunctionDeclarations(buildGetTasksForTodayFunction())
                .addFunctionDeclarations(buildGetActiveTasksFunction())
                .addFunctionDeclarations(buildUpdateTaskStatusFunction())
                .addFunctionDeclarations(buildSearchTasksFunction())
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
            return ResponseHandler.getText(finalResponse);
        }

        return textResponse.toString();
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

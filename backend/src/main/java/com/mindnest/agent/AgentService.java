package com.mindnest.agent;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.*;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import com.mindnest.agent.IntentResult.Intent;
import com.mindnest.agent.tools.KnowledgeTools;
import com.mindnest.config.PromptConfig;
import com.mindnest.model.dto.ChatResponse;
import com.mindnest.model.entity.KnowledgeRelation;
import com.mindnest.model.entity.Conversation;
import com.mindnest.model.entity.Message;
import com.mindnest.model.entity.ProjectMember;
import com.mindnest.service.ConversationService;
import com.mindnest.service.GraphService;
import com.mindnest.service.ModelRouter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class AgentService {

    private final VertexAI vertexAI;
    private final ModelRouter modelRouter;
    private final ToolExecutor toolExecutor;
    private final ConversationService conversationService;
    private final GraphService graphService;
    private final ObjectMapper objectMapper;
    private final PromptConfig promptConfig;
    private final com.mindnest.repository.UserRepository userRepository;
    private final com.mindnest.agent.tools.ProjectTools projectTools;
    private final KnowledgeTools knowledgeTools;

    @Value("${vertex-ai.models.chat}")
    private String chatModel;

    @Value("${vertex-ai.models.flash}")
    private String flashModel;

    // Records for the new chunk-based architecture
    record ChunkIntent(
        String intent,           // SAVE, SEARCH, TASK, DELETE, CHAT
        String type,             // EXPENSE, TASK, KNOWLEDGE, PERSON, EVENT, CATEGORY
        String subtype,          // fact, note, decision, recipe, etc.
        String content,          // Full text to save
        Map<String, Object> properties,  // Extracted structured data
        List<RelationIntent> relations,  // Links to create
        String searchQuery       // For SEARCH intent
    ) {}

    record RelationIntent(
        String toQuery,          // Search query to find target
        String type              // SUPERSEDES, CONTRADICTS, BELONGS_TO, etc.
    ) {}

    record ChunkResult(
        boolean success,
        String itemId,
        String description,
        List<String> linkedTo,
        String searchResults     // For SEARCH intent
    ) {
        static ChunkResult chat() {
            return new ChunkResult(true, null, "chat", List.of(), null);
        }

        static ChunkResult saved(String id, String desc) {
            return new ChunkResult(true, id, desc, List.of(), null);
        }

        static ChunkResult search(String results) {
            return new ChunkResult(true, null, "search", List.of(), results);
        }
    }

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

            // Get conversation context for intent detection
            List<Message> context = conversationService.getContextMessages(conversation.getId());
            String contextSummary = buildContextSummary(context);

            // === NEW ARCHITECTURE: Chunk-based processing ===

            // STEP 1: Decompose message into chunks
            List<String> chunks = decompose(message);
            log.info("Decomposed message into {} chunks: {}", chunks.size(), chunks);

            // STEP 2: Process each chunk through full flow
            List<ChunkResult> results = new ArrayList<>();
            for (String chunk : chunks) {
                ChunkResult result = processChunk(chunk, contextSummary, projectId, userId);
                results.add(result);
                log.info("Chunk '{}' -> result: {}", truncate(chunk, 50), result);
            }

            // STEP 3: Generate combined response
            String finalResponse = generateCombinedResponse(results, message, contextSummary);

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

    /**
     * STEP 1: Decompose message into independent logical chunks using LLM
     */
    private List<String> decompose(String message) {
        try {
            GenerativeModel decomposeModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.0f)
                            .build())
                    .build();

            String prompt = promptConfig.getDecompositionPrompt().formatted(message);
            GenerateContentResponse response = decomposeModel.generateContent(prompt);
            String jsonResponse = ResponseHandler.getText(response);

            log.debug("Decomposition raw response: {}", jsonResponse);

            // Parse JSON array of strings
            return parseChunkArray(jsonResponse);

        } catch (Exception e) {
            log.error("Decomposition failed, treating as single chunk: {}", e.getMessage());
            return List.of(message);
        }
    }

    /**
     * Parse JSON array of strings from decomposition response
     */
    private List<String> parseChunkArray(String jsonResponse) {
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

            return objectMapper.readValue(cleaned, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.error("Failed to parse chunk array: {}", e.getMessage());
            return List.of(jsonResponse);
        }
    }

    /**
     * Build summary of conversation context for intent detection
     */
    private String buildContextSummary(List<Message> context) {
        if (context.isEmpty()) {
            return "No previous context";
        }

        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (Message msg : context) {
            if (count >= 5) break;  // Last 5 messages max
            String role = msg.getRole() == Message.Role.user ? "User" : "Assistant";
            sb.append(role).append(": ").append(truncate(msg.getContent(), 100)).append("\n");
            count++;
        }
        return sb.toString();
    }

    /**
     * STEP 2: Process a single chunk through full agent flow
     */
    private ChunkResult processChunk(String chunk, String contextSummary, String projectId, String userId) {
        // 2.1 Intent detection for this chunk
        ChunkIntent intent = detectChunkIntent(chunk, contextSummary);
        log.info("Chunk intent: {} -> type: {}", intent.intent(), intent.type());

        // 2.2 Execute based on intent
        // NOTE: System is IMMUTABLE - no DELETE/UPDATE intents
        // - "Delete" returns SAVE with [DELETED] content + SUPERSEDES relation
        // - "Update" returns SAVE with new content + SUPERSEDES relation
        // - "Complete task" returns TASK with status=DONE + SUPERSEDES relation
        return switch (intent.intent().toUpperCase()) {
            case "SAVE" -> executeSave(intent, projectId, userId);
            case "TASK" -> executeTask(intent, projectId, userId);
            case "SEARCH" -> executeSearch(intent, projectId, userId);
            case "CHAT" -> ChunkResult.chat();
            default -> {
                log.warn("Unknown intent: {}", intent.intent());
                yield ChunkResult.chat();
            }
        };
    }

    /**
     * Detect intent for a single chunk using LLM
     */
    private ChunkIntent detectChunkIntent(String chunk, String contextSummary) {
        try {
            GenerativeModel intentModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.0f)
                            .build())
                    .build();

            String prompt = promptConfig.getIntentDetectionPrompt().formatted(chunk, contextSummary);
            GenerateContentResponse response = intentModel.generateContent(prompt);
            String jsonResponse = ResponseHandler.getText(response);

            log.debug("Chunk intent raw response: {}", jsonResponse);

            return parseChunkIntent(jsonResponse);

        } catch (Exception e) {
            log.error("Chunk intent detection failed: {}", e.getMessage());
            return new ChunkIntent("CHAT", null, null, chunk, Map.of(), List.of(), null);
        }
    }

    /**
     * Parse chunk intent JSON response
     */
    private ChunkIntent parseChunkIntent(String jsonResponse) {
        try {
            // Clean up response
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

            String intent = json.has("intent") ? json.get("intent").asText("CHAT") : "CHAT";
            String type = json.has("type") && !json.get("type").isNull() ? json.get("type").asText() : null;
            String subtype = json.has("subtype") && !json.get("subtype").isNull() ? json.get("subtype").asText() : null;
            String content = json.has("content") && !json.get("content").isNull() ? json.get("content").asText() : "";
            String searchQuery = json.has("search_query") && !json.get("search_query").isNull()
                    ? json.get("search_query").asText() : null;

            // Parse properties
            Map<String, Object> properties = new HashMap<>();
            if (json.has("properties") && json.get("properties").isObject()) {
                JsonNode props = json.get("properties");
                props.fieldNames().forEachRemaining(field -> {
                    JsonNode value = props.get(field);
                    if (!value.isNull()) {
                        if (value.isNumber()) {
                            properties.put(field, value.numberValue());
                        } else if (value.isBoolean()) {
                            properties.put(field, value.booleanValue());
                        } else {
                            properties.put(field, value.asText());
                        }
                    }
                });
            }

            // Parse relations
            List<RelationIntent> relations = new ArrayList<>();
            if (json.has("relations") && json.get("relations").isArray()) {
                for (JsonNode relNode : json.get("relations")) {
                    String toQuery = relNode.has("to_query") ? relNode.get("to_query").asText() : null;
                    String relType = relNode.has("type") ? relNode.get("type").asText() : null;
                    if (toQuery != null && relType != null) {
                        relations.add(new RelationIntent(toQuery, relType));
                    }
                }
            }

            return new ChunkIntent(intent, type, subtype, content, properties, relations, searchQuery);

        } catch (Exception e) {
            log.error("Failed to parse chunk intent JSON: {}", e.getMessage());
            return new ChunkIntent("CHAT", null, null, "", Map.of(), List.of(), null);
        }
    }

    /**
     * Execute SAVE intent - create knowledge/expense item with relations
     */
    private ChunkResult executeSave(ChunkIntent intent, String projectId, String userId) {
        // IMPORTANT: Find relation targets BEFORE creating new item
        // Otherwise vector search will find the newly created item instead of the original
        Map<String, String> preFoundTargets = new HashMap<>();
        for (RelationIntent rel : intent.relations()) {
            try {
                // Search for target item BEFORE creating new item
                var searchResults = knowledgeTools.searchKnowledge(rel.toQuery(), projectId, 1);
                if (!searchResults.isEmpty()) {
                    preFoundTargets.put(rel.toQuery(), searchResults.get(0).id());
                    log.debug("Pre-found target for '{}': {}", rel.toQuery(), searchResults.get(0).id());
                }
            } catch (Exception e) {
                log.warn("Failed to pre-find target '{}': {}", rel.toQuery(), e.getMessage());
            }
        }

        Map<String, Object> args = new HashMap<>();
        args.put("content", intent.content());

        // Determine type based on intent type
        String knowledgeType = switch (intent.type() != null ? intent.type().toUpperCase() : "KNOWLEDGE") {
            case "EXPENSE" -> "FACT";  // Expenses stored as FACT for now (until we add EXPENSE type to tools)
            case "KNOWLEDGE" -> intent.subtype() != null ? intent.subtype().toUpperCase() : "NOTE";
            case "TASK" -> "TASK";
            default -> "NOTE";
        };
        args.put("type", knowledgeType);

        // Add structured properties
        if (intent.properties() != null && !intent.properties().isEmpty()) {
            // For now, append properties to content for searchability
            // Future: store in separate fields
        }

        String result = toolExecutor.execute("create_knowledge", args, projectId, userId);

        // Extract created item ID from result
        String createdItemId = extractIdFromResult(result);

        // Create relations using pre-found target IDs
        List<String> linkedTo = new ArrayList<>();
        for (RelationIntent rel : intent.relations()) {
            try {
                String targetId = preFoundTargets.get(rel.toQuery());
                if (targetId != null && createdItemId != null) {
                    // Use direct ID-based relation creation
                    var relResult = knowledgeTools.createRelation(
                            createdItemId,
                            targetId,
                            KnowledgeRelation.RelationType.valueOf(rel.type()),
                            null
                    );
                    if (relResult.isPresent()) {
                        linkedTo.add(rel.toQuery() + " (" + rel.type() + ")");
                        log.info("Created {} relation: {} -> {}", rel.type(), createdItemId, targetId);
                    }
                } else {
                    log.warn("Could not create relation: targetId={}, createdItemId={}", targetId, createdItemId);
                }
            } catch (Exception e) {
                log.warn("Failed to create relation to '{}': {}", rel.toQuery(), e.getMessage());
            }
        }

        return new ChunkResult(true, null, intent.content(), linkedTo, null);
    }

    /**
     * Extract item ID from tool execution result.
     * Result format: "Created note: '...' (id: UUID)"
     */
    private String extractIdFromResult(String result) {
        if (result == null) return null;
        int idStart = result.indexOf("(id: ");
        if (idStart < 0) return null;
        int idEnd = result.indexOf(")", idStart);
        if (idEnd < 0) return null;
        return result.substring(idStart + 5, idEnd);
    }

    /**
     * Execute TASK intent - create task or complete existing task.
     * status=TODO: create new task
     * status=DONE: create completed task node + SUPERSEDES relation to original
     */
    private ChunkResult executeTask(ChunkIntent intent, String projectId, String userId) {
        String status = intent.properties() != null
                ? (String) intent.properties().get("status")
                : "TODO";

        // If completing a task (status=DONE), use complete_task_by_title
        if ("DONE".equalsIgnoreCase(status)) {
            // Find target query from relations or use content as fallback
            String targetQuery = intent.content();
            for (RelationIntent rel : intent.relations()) {
                if ("SUPERSEDES".equals(rel.type()) && rel.toQuery() != null) {
                    targetQuery = rel.toQuery();
                    break;
                }
            }

            // Use complete_task_by_title to mark existing task as DONE
            Map<String, Object> args = new HashMap<>();
            args.put("title", targetQuery);
            String result = toolExecutor.execute("complete_task_by_title", args, projectId, userId);

            log.info("Task completion result for '{}': {}", targetQuery, result);

            List<String> linkedTo = new ArrayList<>();
            if (result != null && result.contains("Completed task")) {
                linkedTo.add("completed: " + targetQuery);
            }
            return new ChunkResult(true, null, "Completed: " + targetQuery, linkedTo, null);
        }

        // Create new task
        Map<String, Object> args = new HashMap<>();
        args.put("title", intent.content());

        if (intent.properties() != null) {
            if (intent.properties().containsKey("deadline")) {
                args.put("deadline", intent.properties().get("deadline").toString());
            }
            if (intent.properties().containsKey("assignee")) {
                args.put("assignee", intent.properties().get("assignee").toString());
            }
        }

        String result = toolExecutor.execute("create_task", args, projectId, userId);

        // Create relation to assignee if specified
        List<String> linkedTo = new ArrayList<>();
        for (RelationIntent rel : intent.relations()) {
            if ("ASSIGNED_TO".equals(rel.type())) {
                try {
                    String linkResult = createRelation(intent.content(), rel.toQuery(), rel.type(), projectId, userId);
                    if (linkResult != null) {
                        linkedTo.add(rel.toQuery());
                    }
                } catch (Exception e) {
                    log.warn("Failed to link task to assignee: {}", e.getMessage());
                }
            }
        }

        return new ChunkResult(true, null, "Task: " + intent.content(), linkedTo, null);
    }

    /**
     * Execute SEARCH intent - search knowledge base with graph expansion
     */
    private ChunkResult executeSearch(ChunkIntent intent, String projectId, String userId) {
        String query = intent.searchQuery() != null ? intent.searchQuery() : intent.content();

        // Step 1: Semantic search to find seed nodes
        Map<String, Object> args = new HashMap<>();
        args.put("query", query);
        args.put("limit", 10);

        String tool = "TASK".equals(intent.type()) ? "search_tasks" : "search_knowledge";
        String searchResult = toolExecutor.execute(tool, args, projectId, null);

        // Step 2: Extract IDs from search results and expand graph
        List<String> seedIds = toolExecutor.getLastSearchIds();
        if (seedIds != null && !seedIds.isEmpty()) {
            // Expand graph with proper depth per relation type
            GraphService.GraphContext graphContext = graphService.expandGraph(seedIds, 50);

            // Build userId -> userName map for showing who added each item
            Map<String, String> userIdToName = buildUserIdToNameMap(projectId);

            // Serialize graph for LLM with user names
            String graphText = graphService.serializeForLLM(graphContext, userIdToName);
            log.debug("Expanded graph for search:\n{}", graphText);

            // Build user context for LLM
            String userContext = buildUserContext(userId, projectId);

            return ChunkResult.search(graphText + "\n\n" + userContext);
        }

        return ChunkResult.search(searchResult);
    }

    /**
     * Build user context string for LLM: current user + all project members
     */
    private String buildUserContext(String userId, String projectId) {
        StringBuilder context = new StringBuilder();

        try {
            // Get current user name
            String currentUserName = "Unknown";
            if (userId != null) {
                var userOpt = userRepository.findById(UUID.fromString(userId));
                if (userOpt.isPresent()) {
                    currentUserName = userOpt.get().getName();
                }
            }
            context.append("Current user: ").append(currentUserName).append("\n");

            // Get all project members with their names
            if (projectId != null) {
                List<ProjectMember> members = projectTools.getMembers(UUID.fromString(projectId));
                if (!members.isEmpty()) {
                    context.append("Project members: ");
                    List<String> memberNames = new ArrayList<>();
                    for (ProjectMember member : members) {
                        var memberUser = userRepository.findById(member.getUserId());
                        if (memberUser.isPresent()) {
                            String name = memberUser.get().getName();
                            String role = member.getRole().name().toLowerCase();
                            memberNames.add(name + " (" + role + ")");
                        }
                    }
                    context.append(String.join(", ", memberNames));
                }
            }
        } catch (Exception e) {
            log.warn("Failed to build user context: {}", e.getMessage());
        }

        return context.toString();
    }

    /**
     * Build a map of userId -> userName for all project members.
     * Used to show who added each item in the knowledge graph.
     */
    private Map<String, String> buildUserIdToNameMap(String projectId) {
        Map<String, String> userIdToName = new HashMap<>();
        try {
            if (projectId != null) {
                List<ProjectMember> members = projectTools.getMembers(UUID.fromString(projectId));
                for (ProjectMember member : members) {
                    var memberUser = userRepository.findById(member.getUserId());
                    if (memberUser.isPresent()) {
                        userIdToName.put(member.getUserId().toString(), memberUser.get().getName());
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Failed to build userId to name map: {}", e.getMessage());
        }
        return userIdToName;
    }

    // NOTE: No executeDelete method - system is IMMUTABLE
    // DELETE is handled via SAVE intent with [DELETED] content + SUPERSEDES relation
    // The LLM returns SAVE intent when user wants to delete something

    /**
     * Create a relation between items using semantic search
     */
    private String createRelation(String sourceContent, String targetQuery, String relationType,
                                   String projectId, String userId) {
        Map<String, Object> args = new HashMap<>();
        args.put("source_query", sourceContent);
        args.put("target_query", targetQuery);
        args.put("relation_type", relationType);
        return toolExecutor.execute("create_relation", args, projectId, userId);
    }

    /**
     * STEP 3: Generate combined response from all chunk results
     */
    private String generateCombinedResponse(List<ChunkResult> results, String originalMessage, String context) {
        try {
            // Build summary of what was done
            StringBuilder actionSummary = new StringBuilder();
            StringBuilder searchResults = new StringBuilder();

            for (ChunkResult result : results) {
                if (result.searchResults() != null) {
                    searchResults.append(result.searchResults()).append("\n");
                } else if (result.description() != null && !"chat".equals(result.description())) {
                    actionSummary.append("- ").append(result.description());
                    if (!result.linkedTo().isEmpty()) {
                        actionSummary.append(" (linked to: ").append(String.join(", ", result.linkedTo())).append(")");
                    }
                    actionSummary.append("\n");
                }
            }

            // If there are search results, use LLM to generate response with calculations
            if (searchResults.length() > 0) {
                return generateSearchResponse(searchResults.toString(), originalMessage);
            }

            // If there are actions, use LLM to generate natural response
            if (actionSummary.length() > 0) {
                return generateActionResponse(actionSummary.toString(), originalMessage);
            }

            // Chat response
            return generateChatResponse(originalMessage, context);

        } catch (Exception e) {
            log.error("Failed to generate combined response: {}", e.getMessage());
            return "Done.";
        }
    }


    /**
     * Generate response for search results, including calculations if needed
     */
    private String generateSearchResponse(String searchResults, String originalQuestion) {
        try {
            GenerativeModel responseModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.3f)
                            .build())
                    .build();

            String prompt = promptConfig.getSearchResponsePrompt()
                    .formatted(searchResults, originalQuestion);

            GenerateContentResponse response = responseModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate search response: {}", e.getMessage());
            return searchResults;
        }
    }

    /**
     * Generate natural response for actions taken
     */
    private String generateActionResponse(String actionSummary, String originalMessage) {
        try {
            GenerativeModel responseModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(512)
                            .setTemperature(0.3f)
                            .build())
                    .build();

            String prompt = promptConfig.getActionResponsePrompt()
                    .formatted(actionSummary, originalMessage);

            GenerateContentResponse response = responseModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate action response: {}", e.getMessage());
            return "Saved.";
        }
    }

    /**
     * Generate chat response (no tools needed)
     */
    private String generateChatResponse(String message, String context) {
        try {
            GenerativeModel chatModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(512)
                            .setTemperature(0.7f)
                            .build())
                    .build();

            String prompt = promptConfig.getSystemPrompt() + "\n\nContext:\n" + context +
                    "\n\nUser message: " + message + "\n\nRespond briefly:";

            GenerateContentResponse response = chatModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate chat response: {}", e.getMessage());
            return "I understand.";
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
                content = promptConfig.getSystemPrompt() + "\n\nUser request: " + content;
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
            currentContent = promptConfig.getSystemPrompt() + "\n\nUser request: " + currentMessage;
        }

        contents.add(Content.newBuilder()
                .setRole("user")
                .addParts(Part.newBuilder().setText(currentContent).build())
                .build());

        return contents;
    }

    private GenerativeModel buildModelWithTools() throws IOException {
        // Define available tools
        // NOTE: No update/delete functions - system is immutable
        // All changes create NEW items with relations (SUPERSEDES, CONTRADICTS)
        Tool tools = Tool.newBuilder()
                .addFunctionDeclarations(buildCreateKnowledgeFunction())
                .addFunctionDeclarations(buildSearchKnowledgeFunction())
                .addFunctionDeclarations(buildCreateTaskFunction())
                .addFunctionDeclarations(buildGetTasksForTodayFunction())
                .addFunctionDeclarations(buildGetActiveTasksFunction())
                .addFunctionDeclarations(buildUpdateTaskStatusFunction())
                .addFunctionDeclarations(buildCompleteTaskByTitleFunction())
                .addFunctionDeclarations(buildCompleteAllTasksByAssigneeFunction())
                .addFunctionDeclarations(buildGetMyItemsFunction())
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

    /**
     * Build model WITHOUT tools - used when tool was already executed by intent detection.
     * This prevents the model from making conflicting function calls.
     */
    private GenerativeModel buildModelWithoutTools() {
        return new GenerativeModel.Builder()
                .setModelName(chatModel)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(2048)
                        .setTemperature(0.7f)
                        .build())
                // No tools - model can only generate text
                .build();
    }

    /**
     * Build model for response generation after tool execution.
     * Uses very low temperature for consistent, deterministic responses.
     */
    private GenerativeModel buildModelForResponse() {
        return new GenerativeModel.Builder()
                .setModelName(chatModel)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(512)   // Short responses only
                        .setTemperature(0.1f)      // Very low for consistency
                        .build())
                // No tools - only text generation
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

    // NOTE: No update/delete function declarations - system is immutable
    // All changes create NEW items with relations (SUPERSEDES, CONTRADICTS)

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
                .setDescription("Mark a SINGLE task as completed by searching for it by title. Use this when user mentions a SPECIFIC task name.")
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

    private FunctionDeclaration buildCompleteAllTasksByAssigneeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("complete_all_tasks_by_assignee")
                .setDescription("Mark ALL tasks assigned to a person as completed. Use this when user says 'my tasks are done', 'I finished all my tasks', 'done with my tasks'. This completes ALL tasks for the person, not just one.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("assignee", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Name of the person whose ALL tasks should be marked as done (e.g. 'Boris', 'Andrey')")
                                .build())
                        .addRequired("assignee")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetMyItemsFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_my_items")
                .setDescription("Get all items created/added by the current user. Use when user asks 'my items', 'what did I add', 'show my contributions', 'list what I saved'.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
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
     * Step 1: Detect user intent using fast model with structured output
     *
     * NOTE: All intent detection is done by LLM. We do NOT use keyword matching
     * because we need to support 100+ languages through embeddings only.
     * The LLM handles morphology and language variations.
     */
    private IntentResult detectIntent(String message) {
        try {
            GenerativeModel intentModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)  // Increased for multi-task JSON responses
                            .setTemperature(0.0f)  // Zero temperature for deterministic classification
                            .build())
                    .build();

            String prompt = promptConfig.getIntentDetectionPrompt().formatted(message);
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
            case "search_tasks" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("query", content);  // Empty content = return all tasks
                args.put("limit", 10);
                yield toolExecutor.execute("search_tasks", args, projectId, userId);
            }
            // NOTE: No update_knowledge/delete_knowledge cases - system is immutable
            // All changes create NEW items with SUPERSEDES/CONTRADICTS relations
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
            case "complete_all_tasks_by_assignee" -> {
                Map<String, Object> args = new HashMap<>();
                args.put("assignee", content);
                yield toolExecutor.execute("complete_all_tasks_by_assignee", args, projectId, userId);
            }
            case "get_my_items" -> {
                Map<String, Object> args = new HashMap<>();
                yield toolExecutor.execute("get_my_items", args, projectId, userId);
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

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }
}

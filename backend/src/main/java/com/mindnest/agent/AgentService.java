package com.mindnest.agent;

import com.mindnest.model.dto.ChatResponse;
import com.mindnest.model.entity.Conversation;
import com.mindnest.model.entity.Message;
import com.mindnest.service.ConversationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Main AI agent service that orchestrates message processing.
 * Delegates to specialized services for specific functionality.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AgentService {

    private final ConversationService conversationService;
    private final ToolExecutor toolExecutor;
    private final IntentDetectionEngine intentDetectionEngine;
    private final IntentExecutor intentExecutor;
    private final ResponseGenerator responseGenerator;
    private final UserContextBuilder userContextBuilder;

    /**
     * Process a user message through the full agent pipeline.
     *
     * Pipeline:
     * 1. Decompose message into chunks
     * 2. Detect intent for each chunk
     * 3. Execute intents via handlers
     * 4. Generate combined response
     *
     * @param message User's message
     * @param projectId Project context
     * @param userId User context
     * @return Chat response with reply and metadata
     */
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

            // Get conversation context
            List<Message> context = conversationService.getContextMessages(conversation.getId());
            String contextSummary = intentDetectionEngine.buildContextSummary(context);

            // Extract pending task IDs from last clarification (if any)
            List<String> pendingTaskIds = userContextBuilder.getPendingTaskIdsFromContext(context);

            // STEP 1: Decompose message into chunks
            List<String> chunks = intentDetectionEngine.decompose(message);
            log.info("Decomposed message into {} chunks: {}", chunks.size(), chunks);

            // STEP 2: Process each chunk through full flow
            List<ChunkResult> results = new ArrayList<>();
            for (String chunk : chunks) {
                ChunkResult result = processChunk(chunk, contextSummary, projectId, userId, pendingTaskIds);
                results.add(result);
                log.info("Chunk '{}' -> result: {}", truncate(chunk, 50), result.description());
            }

            // STEP 3: Generate combined response
            String finalResponse = responseGenerator.generateCombinedResponse(results, message, contextSummary);

            // Get sources collected during tool execution
            List<String> sources = toolExecutor.getSources();

            // Calculate confidence
            double confidence = responseGenerator.calculateConfidence(finalResponse);

            // Save assistant response with metadata
            Map<String, Object> metadata = buildResponseMetadata(confidence, sources, results);
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
     * Process a single chunk through intent detection and execution.
     */
    private ChunkResult processChunk(String chunk, String contextSummary, String projectId, String userId,
                                      List<String> pendingTaskIds) {
        // Detect intent for this chunk
        ChunkIntent intent = intentDetectionEngine.detectChunkIntent(chunk, contextSummary);
        log.info("Chunk intent: {} -> type: {}", intent.intent(), intent.type());

        // Execute based on intent
        return intentExecutor.processChunk(intent, projectId, userId, pendingTaskIds);
    }

    /**
     * Build metadata for assistant response.
     */
    private Map<String, Object> buildResponseMetadata(double confidence, List<String> sources,
                                                       List<ChunkResult> results) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("confidence", confidence);

        if (!sources.isEmpty()) {
            metadata.put("sources", sources);
        }

        // Extract pending task IDs from clarification results for next turn
        List<String> newPendingTaskIds = userContextBuilder.extractPendingTaskIds(results);
        if (!newPendingTaskIds.isEmpty()) {
            metadata.put("pendingTaskIds", newPendingTaskIds);
            metadata.put("clarificationType", "task_completion");
        }

        return metadata;
    }

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }
}

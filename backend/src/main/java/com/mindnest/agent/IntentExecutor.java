package com.mindnest.agent;

import com.mindnest.agent.handler.IntentHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Routes intent execution to appropriate handlers.
 * Central orchestrator for processing detected intents.
 */
@Service
@Slf4j
public class IntentExecutor {

    private final Map<String, IntentHandler> handlers = new HashMap<>();
    private final IntentHandler defaultHandler;

    public IntentExecutor(List<IntentHandler> handlerList) {
        for (IntentHandler handler : handlerList) {
            handlers.put(handler.getIntentType().toUpperCase(), handler);
        }
        // Use CHAT handler as default
        this.defaultHandler = handlers.getOrDefault("CHAT", handlerList.get(0));
        log.info("Registered {} intent handlers: {}", handlers.size(), handlers.keySet());
    }

    /**
     * Process a chunk through the appropriate intent handler.
     *
     * @param intent The detected intent with structured data
     * @param projectId The project context
     * @param userId The user context
     * @param pendingTaskIds Task IDs from previous clarification (if any)
     * @return Result of processing the chunk
     */
    public ChunkResult processChunk(ChunkIntent intent, String projectId, String userId,
                                     List<String> pendingTaskIds) {
        // If there are pending task IDs from clarification, add them to intent properties
        ChunkIntent intentWithPending = addPendingTaskIds(intent, pendingTaskIds);

        log.info("Processing intent: {} -> type: {}", intentWithPending.intent(), intentWithPending.type());

        String intentType = intentWithPending.intent().toUpperCase();
        IntentHandler handler = handlers.getOrDefault(intentType, defaultHandler);

        if (handler == defaultHandler && !intentType.equals("CHAT")) {
            log.warn("Unknown intent '{}', using default CHAT handler", intentType);
        }

        return handler.execute(intentWithPending, projectId, userId);
    }

    /**
     * Add pending task IDs to intent properties for task completion flow.
     */
    private ChunkIntent addPendingTaskIds(ChunkIntent intent, List<String> pendingTaskIds) {
        if (pendingTaskIds.isEmpty() || !"TASK".equalsIgnoreCase(intent.intent())) {
            return intent;
        }

        Map<String, Object> newProps = new HashMap<>(intent.properties() != null ? intent.properties() : Map.of());
        newProps.put("pending_task_ids", pendingTaskIds);

        return new ChunkIntent(
                intent.intent(),
                intent.type(),
                intent.subtype(),
                intent.content(),
                newProps,
                intent.relations(),
                intent.searchQuery()
        );
    }
}

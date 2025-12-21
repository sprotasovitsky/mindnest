package com.mindnest.agent;

import java.util.List;

/**
 * Result of processing a single chunk through the agent pipeline.
 * Contains information about what was done and any pending clarifications.
 */
public record ChunkResult(
        boolean success,
        String itemId,
        String description,
        List<String> linkedTo,
        String searchResults,       // For SEARCH intent
        boolean needsClarification, // For task completion clarification
        List<String> pendingTaskIds // Task IDs pending user selection
) {
    public static ChunkResult chat() {
        return new ChunkResult(true, null, "chat", List.of(), null, false, List.of());
    }

    public static ChunkResult saved(String id, String desc) {
        return new ChunkResult(true, id, desc, List.of(), null, false, List.of());
    }

    public static ChunkResult search(String results) {
        return new ChunkResult(true, null, "search", List.of(), results, false, List.of());
    }

    public static ChunkResult clarification(String message, List<String> taskIds) {
        return new ChunkResult(true, null, message, List.of(), null, true, taskIds);
    }
}

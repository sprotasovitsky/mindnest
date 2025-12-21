package com.mindnest.agent.handler;

import com.mindnest.agent.ChunkIntent;
import com.mindnest.agent.ChunkResult;

/**
 * Base interface for intent handlers.
 * Each handler processes a specific type of user intent.
 */
public interface IntentHandler {

    /**
     * Get the intent type this handler processes.
     */
    String getIntentType();

    /**
     * Execute the intent and return the result.
     *
     * @param intent The detected intent with structured data
     * @param projectId The project context
     * @param userId The user context
     * @return Result of executing the intent
     */
    ChunkResult execute(ChunkIntent intent, String projectId, String userId);
}

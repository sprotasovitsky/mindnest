package com.mindnest.agent;

import java.util.List;
import java.util.Map;

/**
 * Detected intent for a single chunk of user message.
 * Contains structured data extracted by LLM during intent detection.
 */
public record ChunkIntent(
        String intent,           // SAVE, SEARCH, TASK, DELETE, CHAT
        String type,             // EXPENSE, TASK, KNOWLEDGE, PERSON, EVENT, CATEGORY
        String subtype,          // fact, note, decision, recipe, etc.
        String content,          // Full text to save
        Map<String, Object> properties,  // Extracted structured data
        List<RelationIntent> relations,  // Links to create
        String searchQuery       // For SEARCH intent
) {}
